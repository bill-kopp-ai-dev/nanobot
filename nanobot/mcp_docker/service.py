"""Gateway-owned intent and contract for Docker MCP operations.

The broker never writes config.json. A gateway process serializes config writes
through WebUISettingsConfig; revisions reject stale browser/CLI mutations.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import tempfile
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol, cast

from jsonschema import Draft202012Validator
from pydantic import ValidationError

from nanobot.config.mcp_docker import (
    REDACTED_SECRET,
    SERVER_ID,
    DockerEnvValue,
    DockerHostConfig,
    DockerImageSource,
    DockerServer,
    ManagedAppReference,
    McpDockerConfig,
    TrustedCatalogConfig,
)
from nanobot.config.schema import Config
from nanobot.mcp_docker.broker import BrokerError
from nanobot.mcp_docker.catalog import CatalogError, load_catalog_snapshot, resolve_app_profile
from nanobot.mcp_docker.client import BrokerRejectedError, BrokerUnavailableError
from nanobot.webui.settings_services import WebUISettingsConfig


class Broker(Protocol):
    def action(self, operation: str, server_id: str, data: dict[str, Any]) -> dict[str, Any]: ...


class DomainError(Exception):
    def __init__(self, status: int, message: str):
        self.status = status
        super().__init__(message)


def _mask(value: str) -> str:
    return f"{value[:4]}••••{value[-4:]}" if len(value) >= 8 else "••••"


def _redact(host: DockerHostConfig) -> dict[str, Any]:
    result = host.model_dump(mode="json", by_alias=True)
    for name, entry in host.env.items():
        if entry.kind == "secret":
            result["env"][name]["value"] = REDACTED_SECRET
            result["env"][name]["maskHint"] = _mask(entry.value)
    return result


def broker_problem(exc: BrokerUnavailableError | BrokerRejectedError | BrokerError) -> dict[str, str]:
    """Bounded, non-sensitive diagnostics shared by list and operator preflight."""
    if isinstance(exc, BrokerUnavailableError):
        messages = {
            "token-missing": "Broker token is missing from this gateway instance.",
            "token-invalid": "Broker token is invalid.",
            "token-permissions": "Broker token owner, group or mode does not match this gateway.",
            "token-unreadable": "Broker token cannot be read by this gateway.",
            "transport": "Docker MCP broker is not reachable from this gateway.",
            "broker-error": "Docker MCP broker is not ready; inspect its health and Docker access.",
            "invalid-response": "Docker MCP broker returned an invalid response.",
        }
        return {"reason": exc.reason if exc.reason in messages else "unavailable",
                "message": messages.get(exc.reason, "Docker MCP broker unavailable.")}
    if isinstance(exc, BrokerRejectedError) and exc.status_code == 401:
        return {"reason": "authentication", "message": "Docker MCP broker rejected this gateway's token."}
    return {"reason": "rejected", "message": "Docker MCP broker rejected the observation request."}


class DockerMcpService:
    def __init__(self, config: WebUISettingsConfig, broker: Broker) -> None:
        self.config = config
        self.broker = broker
        self.root = config.path.parent / "mcp-docker"

    def list(self) -> dict[str, Any]:
        pending_transitions = self.recover_pending()
        section = self.config.load().tools.mcp_docker
        broker_capabilities: dict[str, Any] = {}
        try:
            health = self.broker.action("health", "broker", {})
            if health.get("ready") is not True:
                raise BrokerUnavailableError("broker health response invalid", reason="invalid-response")
            broker_status: dict[str, str] = {"status": "ready"}
            broker_capabilities = {
                "minimumMountsSupported": health.get("minimumMountsSupported") is True,
                "supportedNetworks": ["none", "bridge"] if health.get("supportedNetworks") == ["none", "bridge"] else ["none"],
                "appMountsSupported": health.get("appMountsSupported") is True,
                "catalogAcquisitionSupported": health.get("catalogAcquisitionSupported") is True,
            }
        except (BrokerUnavailableError, BrokerRejectedError, BrokerError) as exc:
            broker_status = {"status": "unavailable", **broker_problem(exc)}
        servers: dict[str, Any] = {}
        for key, server in section.servers.items():
            observation: dict[str, Any]
            if broker_status["status"] != "ready":
                observation = {
                    "dockerObservation": "unknown",
                    "mcpConnectivity": "unknown",
                }
            else:
                try:
                    observation = self.broker.action("observe", key, {
                        "source": server.source.model_dump(mode="json"),
                    })
                except (BrokerUnavailableError, BrokerRejectedError, BrokerError) as exc:
                    observation = {
                        "dockerObservation": "unknown",
                        "mcpConnectivity": "unknown",
                        "observationError": broker_problem(exc)["message"],
                    }
            docker_state = observation.get("dockerObservation")
            mcp_state = observation.get("mcpConnectivity")
            observed_tools = observation.get("tools")
            raw_effective = observation.get("effectiveConfiguration")
            effective: dict[str, Any] | None = None
            if isinstance(raw_effective, dict):
                effective_data = cast(dict[str, object], raw_effective)
                raw_network = effective_data.get("network")
                raw_mounts = effective_data.get("mounts")
                mounts: list[dict[str, object]] = []
                if isinstance(raw_mounts, list):
                    for raw_mount in cast(list[object], raw_mounts):
                        if not isinstance(raw_mount, dict):
                            continue
                        mount = cast(dict[str, Any], raw_mount)
                        mount_type = mount.get("type")
                        mount_destination = mount.get("destination")
                        mount_read_write = mount.get("readWrite")
                        if (isinstance(mount_type, str) and mount_type in {"bind", "volume", "tmpfs"} and
                            isinstance(mount_destination, str) and
                            type(mount_read_write) is bool):
                            mounts.append({"type": mount_type,
                                           "destination": mount_destination,
                                           "readWrite": mount_read_write})
                effective = {
                    "network": raw_network if isinstance(raw_network, str) and
                    re.fullmatch(r"[A-Za-z0-9_.:/-]{1,128}", raw_network) else "unknown",
                    "mounts": mounts,
                }
            servers[key] = {
                **server.model_dump(mode="json", by_alias=True),
                "configuration": _redact(section.configurations[key]),
                "dockerObservation": docker_state if isinstance(docker_state, str) and docker_state in {
                    "running", "stopped", "container-missing", "image-missing", "unknown",
                } else "unknown",
                "mcpConnectivity": mcp_state if isinstance(mcp_state, str) and mcp_state in {
                    "connected", "disconnected", "unknown",
                } else "unknown",
                "tools": [name for name in cast(list[object], observed_tools) if isinstance(name, str)]
                if isinstance(observed_tools, list) else server.tools,
                "toolsSource": "observed" if isinstance(observed_tools, list) else "saved",
                "savedTools": server.tools,
                **({"effectiveConfiguration": effective} if effective is not None else {}),
                **({"observationError": observation["observationError"]}
                   if observation.get("observationError") else {}),
            }
        return {
            "schemaVersion": section.schema_version,
            "revision": section.revision,
            "allowRemoteAdmin": section.allow_remote_admin,
            **broker_capabilities,
            "brokerStatus": broker_status,
            "servers": servers,
            "history": self._history(),
            "pendingTransitions": pending_transitions,
            "backups": self._backups(),
            "catalogs": self._catalog_summaries(section),
            "localCatalogCandidate": self._local_catalog_candidate(),
            "appReleases": {
                server_id: release.model_dump(mode="json", by_alias=True)
                for server_id, release in section.app_releases.items()
            },
        }

    def _local_catalog_candidate(self) -> dict[str, Any]:
        try:
            root = self._catalog_root()
            catalog_path = root / "public" / "catalog.json"
            if catalog_path.is_symlink():
                raise CatalogError("catalog snapshot must not be a symlink")
            raw = catalog_path.read_bytes()
            snapshot_sha256 = hashlib.sha256(raw).hexdigest()
            apps = load_catalog_snapshot(root, snapshot_sha256)
            return {"status": "ready", "snapshotSha256": snapshot_sha256, "appCount": len(apps)}
        except (CatalogError, DomainError, OSError):
            return {"status": "unavailable"}

    @staticmethod
    def _catalog_root() -> Path:
        raw = os.environ.get("PERCIVAL_MCP_INDEX_ROOT")
        if not raw:
            raise DomainError(503, "local MCP index is not provisioned")
        root = Path(raw)
        if not root.is_absolute() or root.is_symlink():
            raise DomainError(503, "local MCP index path is invalid")
        try:
            resolved = root.resolve(strict=True)
        except OSError as exc:
            raise DomainError(503, "local MCP index is unavailable") from exc
        if not resolved.is_dir():
            raise DomainError(503, "local MCP index is unavailable")
        return resolved

    def _catalog_summaries(self, section: McpDockerConfig) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        for catalog_id, trusted in sorted(section.trusted_catalogs.items()):
            try:
                apps = load_catalog_snapshot(Path(trusted.root), trusted.snapshot_sha256)
                result.append({
                    "catalogId": catalog_id,
                    "snapshotSha256": trusted.snapshot_sha256,
                    "status": "ready",
                    "apps": [{
                        "id": app.app_id,
                        "name": app.mcp_name,
                        "version": app.version,
                        "sourceClass": app.source_class,
                        "platform": app.platform,
                        "repositoryDigest": app.repository_digest,
                        "needsNetwork": app.needs_network,
                        "environmentVariables": [
                            {"name": variable.name, "required": variable.required, "secret": variable.secret}
                            for variable in app.environment_variables
                        ],
                        "mounts": [
                            {"target": mount.target, "kind": mount.kind,
                             "access": mount.access, "required": mount.required}
                            for mount in app.mounts
                        ],
                    } for app in apps],
                })
            except (CatalogError, OSError):
                result.append({
                    "catalogId": catalog_id,
                    "snapshotSha256": trusted.snapshot_sha256,
                    "status": "stale",
                    "apps": [],
                })
        return result

    def migrate_schema(self, expected_revision: int, expected_confirmation: str) -> dict[str, Any]:
        """Explicitly migrate the canonical MCP config from v1 to v2 under CAS."""
        if expected_confirmation != "MCP-Docker-v1-to-v2":
            raise DomainError(400, "type MCP-Docker-v1-to-v2 to confirm the schema migration")
        if type(expected_revision) is not int or expected_revision < 0:
            raise DomainError(400, "expected_revision must be a nonnegative integer")
        if self.recover_pending():
            raise DomainError(503, "an MCP Docker transition is unresolved; inspect recovery before migration")

        def transaction(path: Path) -> dict[str, Any]:
            from nanobot.config.loader import load_config, save_config

            config = load_config(path)
            section = config.tools.mcp_docker
            if section.revision != expected_revision:
                raise DomainError(409, "Docker MCP revision conflict")
            if section.schema_version != 1:
                raise DomainError(409, "MCP Docker config is not schema version 1")
            if self._has_pending_unresolved():
                raise DomainError(503, "an MCP Docker transition is unresolved; inspect recovery before migration")
            raw = path.read_bytes() if path.exists() else b"{}\n"
            backup_id = datetime.now(UTC).strftime("schema-v1-%Y%m%dT%H%M%SZ-") + uuid.uuid4().hex[:12]
            backup_dir = self.root / "backups" / backup_id
            backup_dir.mkdir(parents=True, mode=0o700)
            os.chmod(backup_dir, 0o700)
            snapshot_path = backup_dir / "config-v1.json"
            fd = os.open(snapshot_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, "wb") as handle:
                handle.write(raw)
                handle.flush()
                os.fsync(handle.fileno())
            manifest = {
                "schemaVersion": 1,
                "action": "migrate-schema",
                "source_revision": section.revision,
                "sha256": hashlib.sha256(raw).hexdigest(),
            }
            manifest_path = backup_dir / "manifest.json"
            manifest_fd = os.open(manifest_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(manifest_fd, "w", encoding="utf-8") as handle:
                json.dump(manifest, handle, sort_keys=True)
                handle.flush()
                os.fsync(handle.fileno())
            section.schema_version = 2
            section.installation_id = str(uuid.uuid4())
            section.revision += 1
            save_config(config, path)
            correlation_id = uuid.uuid4().hex
            self._audit("migrate-schema", "catalog", "committed", section.revision,
                        correlation_id)
            return {
                "schemaVersion": section.schema_version,
                "revision": section.revision,
                "installationId": section.installation_id,
                "backupId": backup_id,
            }

        return self.config.run_serialized(transaction)

    def register_catalog(
        self, catalog_id: str, snapshot_sha256: str,
        expected_revision: int, expected_confirmation: str,
    ) -> dict[str, Any]:
        if not re.fullmatch(r"[a-z][a-z0-9-]{0,39}", catalog_id):
            raise DomainError(400, "invalid catalog_id")
        if expected_confirmation != catalog_id:
            raise DomainError(400, "catalog confirmation must equal catalog_id")
        if type(expected_revision) is not int or expected_revision < 0:
            raise DomainError(400, "expected_revision must be a nonnegative integer")
        root = self._catalog_root()
        try:
            apps = load_catalog_snapshot(root, snapshot_sha256)
        except CatalogError as exc:
            raise DomainError(400, "local index snapshot failed validation") from exc
        if self.recover_pending():
            raise DomainError(503, "an MCP Docker transition is unresolved; inspect recovery before pinning a catalog")
        registered_at = datetime.now(UTC).isoformat()

        def mutation(config: Config) -> dict[str, Any]:
            section = config.tools.mcp_docker
            if section.revision != expected_revision:
                raise DomainError(409, "Docker MCP revision conflict")
            if section.schema_version != 2:
                raise DomainError(409, "migrate MCP Docker config to schema version 2 first")
            if self._has_pending_unresolved():
                raise DomainError(503, "an MCP Docker transition is unresolved; inspect recovery before pinning a catalog")
            previous = section.trusted_catalogs.get(catalog_id)
            if previous is not None and previous.snapshot_sha256 != snapshot_sha256:
                if any(release.catalog_id == catalog_id for release in section.app_releases.values()):
                    raise DomainError(409, "catalog pin is referenced by installed apps; register a new catalog_id")
                required = f"{catalog_id}@{previous.snapshot_sha256[:12]}->{snapshot_sha256[:12]}"
                if expected_confirmation != required:
                    raise DomainError(400, f"type {required} to replace the trusted catalog pin")
            elif previous is not None:
                raise DomainError(409, "catalog snapshot is already trusted")
            section.trusted_catalogs[catalog_id] = TrustedCatalogConfig(
                catalog_id=catalog_id,
                root=str(root),
                snapshot_sha256=snapshot_sha256,
                registered_at=registered_at,
            )
            section.revision += 1
            self._audit("register-catalog", catalog_id, "committed", section.revision,
                        uuid.uuid4().hex)
            return {"catalogId": catalog_id, "snapshotSha256": snapshot_sha256,
                    "revision": section.revision, "appCount": len(apps)}

        return self.config.update(mutation)

    def restore_schema_v1(
        self, backup_id: str, expected_revision: int, expected_confirmation: str,
    ) -> dict[str, Any]:
        """Restore the v1 MCP section only when no v2 catalog data was committed."""
        if (not re.fullmatch(r"schema-v1-[A-Za-z0-9T_-]{1,96}", backup_id) or
            expected_confirmation != f"restore:{backup_id}"):
            raise DomainError(400, "schema backup ID and typed restore confirmation are required")
        backup_dir = self.root / "backups" / backup_id
        if backup_dir.is_symlink() or backup_dir.resolve().parent != (self.root / "backups").resolve():
            raise DomainError(400, "schema backup must be a direct child of the private backups directory")
        snapshot_path = backup_dir / "config-v1.json"
        manifest_path = backup_dir / "manifest.json"
        if snapshot_path.is_symlink() or manifest_path.is_symlink() or not snapshot_path.is_file() or not manifest_path.is_file():
            raise DomainError(400, "schema backup files are unavailable")
        try:
            raw = snapshot_path.read_bytes()
            manifest_value: object = json.loads(manifest_path.read_text(encoding="utf-8"))
            saved_value: object = json.loads(raw)
            if not isinstance(manifest_value, dict) or not isinstance(saved_value, dict):
                raise ValueError("invalid schema backup")
            manifest = cast(dict[str, Any], manifest_value)
            saved = cast(dict[str, Any], saved_value)
            tools_saved = saved.get("tools")
            if (manifest.get("action") != "migrate-schema" or
                not hmac.compare_digest(str(manifest.get("sha256", "")), hashlib.sha256(raw).hexdigest()) or
                not isinstance(tools_saved, dict)):
                raise ValueError("invalid schema backup")
            mcp_raw = cast(dict[str, Any], tools_saved).get("mcpDocker")
            if not isinstance(mcp_raw, dict):
                raise ValueError("invalid schema backup")
            mcp_saved = cast(dict[str, Any], mcp_raw)
        except (OSError, ValueError, TypeError, KeyError) as exc:
            raise DomainError(400, "schema backup is missing, invalid or tampered") from exc
        if mcp_saved.get("schemaVersion") != 1:
            raise DomainError(400, "backup does not contain MCP config schema version 1")
        if type(expected_revision) is not int or expected_revision < 0:
            raise DomainError(400, "expected_revision must be a nonnegative integer")

        def transaction(path: Path) -> dict[str, Any]:
            from nanobot.config.loader import load_config, save_config

            config = load_config(path)
            section = config.tools.mcp_docker
            if section.revision != expected_revision:
                raise DomainError(409, "Docker MCP revision conflict")
            if section.schema_version != 2 or section.trusted_catalogs or section.app_releases:
                raise DomainError(409, "schema rollback is unsupported after catalog trust or app install")
            saved_servers = mcp_saved.get("servers")
            saved_configs = mcp_saved.get("configurations")
            current_servers = {key: item.model_dump(mode="json", by_alias=True)
                               for key, item in section.servers.items()}
            current_configs = {}
            for key, host in section.configurations.items():
                value = host.model_dump(mode="json", by_alias=True)
                value.pop("appMounts", None)
                current_configs[key] = value
            if current_servers != saved_servers or current_configs != saved_configs:
                raise DomainError(409, "schema rollback requires the managed server state to match its v1 snapshot")
            if self._has_pending_unresolved():
                raise DomainError(503, "an MCP Docker transition is unresolved; inspect recovery before rollback")
            section.schema_version = 1
            section.installation_id = None
            section.trusted_catalogs.clear()
            section.app_releases.clear()
            section.revision += 1
            save_config(config, path)
            self._audit("restore-schema-v1", "catalog", "committed", section.revision,
                        uuid.uuid4().hex)
            return {"schemaVersion": 1, "revision": section.revision, "backupId": backup_id}

        return self.config.run_serialized(transaction)

    def export_capabilities(self) -> dict[str, Any]:
        def transaction(path: Path) -> dict[str, Any]:
            from nanobot.config.loader import load_config

            section = load_config(path).tools.mcp_docker
            if section.schema_version != 2 or section.installation_id is None:
                raise DomainError(409, "migrate MCP Docker config to schema version 2 before export")
            servers: list[dict[str, Any]] = []
            for server_id, server in sorted(section.servers.items()):
                host = section.configurations[server_id]
                entry: dict[str, Any] = {
                    "server_id": server_id,
                    "owner": "native-mcp-manager",
                    "active": server.active,
                    "state": server.state,
                    "source": server.source.model_dump(mode="json"),
                    "observed": "unknown",
                    "configuration": {
                        "network": host.network,
                        "host_mounts": "full" if host.mounts is None else "reduced",
                        "app_mounts": [
                            {"target": item.target, "kind": item.kind, "read_only": item.read_only}
                            for item in host.app_mounts
                        ],
                    },
                }
                release = section.app_releases.get(server_id)
                if release is not None:
                    entry["app_release"] = release.model_dump(mode="json", by_alias=False)
                servers.append(entry)
            snapshot = {
                "schema_version": 1,
                "installation_id": section.installation_id,
                "owner": "native-mcp-manager",
                "revision": section.revision,
                "generated_at": datetime.now(UTC).isoformat(),
                "servers": servers,
            }
            try:
                export_schema = json.loads(
                    Path(__file__).with_name("capabilities.schema.1.0.json").read_text(encoding="utf-8")
                )
                validator: Any = Draft202012Validator(export_schema)
                validator.check_schema(export_schema)
                errors = sorted(validator.iter_errors(snapshot), key=lambda error: list(map(str, error.absolute_path)))
            except (OSError, ValueError, TypeError) as exc:
                raise DomainError(500, "capabilities export schema is unavailable") from exc
            if errors:
                raise DomainError(500, "capabilities snapshot did not validate")
            raw = (json.dumps(snapshot, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode()
            self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
            os.chmod(self.root, 0o700)
            fd, temporary = tempfile.mkstemp(prefix=".capabilities.", suffix=".tmp", dir=self.root)
            try:
                os.fchmod(fd, 0o600)
                with os.fdopen(fd, "wb") as handle:
                    handle.write(raw)
                    handle.flush()
                    os.fsync(handle.fileno())
                os.replace(temporary, self.root / "capabilities.lock")
                dir_fd = os.open(self.root, os.O_RDONLY)
                try:
                    os.fsync(dir_fd)
                finally:
                    os.close(dir_fd)
            except Exception:
                try:
                    os.unlink(temporary)
                except FileNotFoundError:
                    pass
                raise
            return {
                "revision": section.revision,
                "sha256": hashlib.sha256(raw).hexdigest(),
                "capabilities": snapshot,
            }

        return self.config.run_serialized(transaction)

    def install_catalog_app(
        self,
        *,
        catalog_id: str,
        app_id: str,
        server_id: str,
        expected_revision: int,
        expected_confirmation: str,
        mount_sources: dict[str, str],
        environment: dict[str, DockerEnvValue],
        host_mounts: list[str],
        network: str | None = None,
    ) -> dict[str, Any]:
        if not SERVER_ID.fullmatch(server_id):
            raise DomainError(400, "invalid server_id")
        if self.recover_pending():
            raise DomainError(503, "an MCP Docker transition is unresolved; inspect recovery before catalog install")
        if type(expected_revision) is not int or expected_revision < 0:
            raise DomainError(400, "expected_revision must be a nonnegative integer")
        section = self.config.load().tools.mcp_docker
        if section.revision != expected_revision:
            raise DomainError(409, "Docker MCP revision conflict")
        if section.schema_version != 2:
            raise DomainError(409, "migrate MCP Docker config to schema version 2 first")
        if server_id in section.servers:
            raise DomainError(409, "server already exists")
        trusted = section.trusted_catalogs.get(catalog_id)
        if trusted is None:
            raise DomainError(404, "catalog is not trusted")
        try:
            apps = load_catalog_snapshot(Path(trusted.root), trusted.snapshot_sha256)
        except (CatalogError, OSError) as exc:
            raise DomainError(409, "trusted local catalog snapshot is stale or invalid") from exc
        app = next((item for item in apps if item.app_id == app_id), None)
        if app is None:
            raise DomainError(404, "approved app release is not present in the trusted catalog")
        confirmation = f"{server_id}/{app.app_id}@{app.version}"
        if expected_confirmation != confirmation:
            raise DomainError(400, f"type {confirmation} to confirm this local catalog install")
        try:
            host = resolve_app_profile(
                app,
                mount_sources=mount_sources,
                environment=environment,
                host_mounts=host_mounts,
                network=network,
            )
        except (CatalogError, ValidationError, ValueError) as exc:
            raise DomainError(400, "installation configuration does not satisfy the app profile") from exc
        try:
            health = self.broker.action("health", "broker", {})
        except (BrokerUnavailableError, BrokerRejectedError, BrokerError):
            raise
        if (health.get("minimumMountsSupported") is not True or health.get("appMountsSupported") is not True or
            health.get("catalogAcquisitionSupported") is not True):
            raise DomainError(409, "Docker broker does not support catalog mounts or policy-governed acquisition")
        correlation_id = uuid.uuid4().hex
        self._audit("acquire", server_id, "started", expected_revision, correlation_id)
        try:
            acquired = self.broker.action("acquire", server_id, {
                "reference": app.repository_digest,
                "platform": app.platform,
            })
        except (BrokerUnavailableError, BrokerRejectedError, BrokerError):
            self._audit("acquire", server_id, "failed", expected_revision, correlation_id)
            raise
        if acquired.get("repositoryDigest") != app.repository_digest or acquired.get("platform") != app.platform:
            self._audit("acquire", server_id, "failed", expected_revision, correlation_id)
            raise DomainError(502, "broker acquisition identity did not match the catalog pin")
        self._audit("acquire", server_id, "committed", expected_revision, correlation_id)
        app_reference = ManagedAppReference(
            catalog_id=catalog_id,
            snapshot_sha256=app.snapshot_sha256,
            app_id=app.app_id,
            mcp_name=app.mcp_name,
            version=app.version,
            source_class=app.source_class,
            repository_digest=app.repository_digest,
            platform=app.platform,
            manifest_sha256=app.manifest_sha256,
            server_json_sha256=app.server_json_sha256,
            consent_revision=expected_revision,
            consented_at=datetime.now(UTC).isoformat(),
        )
        result = self.act("install", {
            "server_id": server_id,
            "expected_revision": expected_revision,
            "expected_confirmation": confirmation,
            "source": {"type": "pinned-image", "reference": app.repository_digest},
            "configuration": host.model_dump(mode="json"),
            "app_release": app_reference.model_dump(mode="json"),
        })
        result["appId"] = app.app_id
        result["appVersion"] = app.version
        return result

    @staticmethod
    def _validate_app_host(
        section: McpDockerConfig, release: ManagedAppReference, host: DockerHostConfig,
    ) -> None:
        trusted = section.trusted_catalogs.get(release.catalog_id)
        if trusted is None or trusted.snapshot_sha256 != release.snapshot_sha256:
            raise DomainError(409, "installed app no longer matches a trusted catalog pin")
        try:
            apps = load_catalog_snapshot(Path(trusted.root), trusted.snapshot_sha256)
        except (CatalogError, OSError) as exc:
            raise DomainError(409, "installed app catalog snapshot is stale or invalid") from exc
        app = next((item for item in apps if item.app_id == release.app_id), None)
        if app is None or (
            app.mcp_name != release.mcp_name or app.version != release.version or
            app.source_class != release.source_class or app.repository_digest != release.repository_digest or
            app.platform != release.platform or app.manifest_sha256 != release.manifest_sha256 or
            app.server_json_sha256 != release.server_json_sha256
        ):
            raise DomainError(409, "installed app release does not match its trusted catalog snapshot")
        if host.mounts is None:
            raise DomainError(400, "catalog apps require an explicit reduced host access profile")
        requirements = {mount.target: mount for mount in app.mounts}
        provided = {mount.target: mount for mount in host.app_mounts}
        if set(provided) - set(requirements) or {mount.target for mount in app.mounts if mount.required} - set(provided):
            raise DomainError(400, "configured app mounts do not match the catalog profile")
        for target, configured in provided.items():
            requirement = requirements[target]
            if configured.kind != requirement.kind or configured.read_only != (requirement.access == "read-only"):
                raise DomainError(400, "configured app mount access does not match the catalog profile")
        if host.network == "bridge" and not app.needs_network:
            raise DomainError(400, "configured network access exceeds the catalog profile")
        env_requirements = {item.name: item for item in app.environment_variables}
        if set(host.env) - set(env_requirements):
            raise DomainError(400, "configured environment contains undeclared app variables")
        for name, requirement in env_requirements.items():
            configured = host.env.get(name)
            if requirement.required and configured is None:
                raise DomainError(400, "required app environment value is missing")
            if configured is not None and (
                (requirement.secret and configured.kind != "secret") or
                (not requirement.secret and configured.kind == "secret") or
                (requirement.required and not configured.value)
            ):
                raise DomainError(400, "configured app environment type does not match the catalog")

    def _backups(self) -> list[dict[str, Any]]:
        backups = self.root / "backups"
        try:
            entries = sorted(backups.iterdir(), key=lambda item: item.name, reverse=True)
        except FileNotFoundError:
            return []
        result: list[dict[str, Any]] = []
        for entry in entries[:100]:
            if entry.is_symlink() or not entry.is_dir() or not re.fullmatch(r"[A-Za-z0-9T:.Z_-]{1,128}", entry.name):
                continue
            manifest_path = entry / "manifest.json"
            if manifest_path.is_symlink():
                continue
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            except (OSError, ValueError, TypeError):
                continue
            if not isinstance(manifest, dict):
                continue
            data = cast(dict[str, Any], manifest)
            server_id = data.get("server_id")
            revision = data.get("source_revision")
            if isinstance(server_id, str) and SERVER_ID.fullmatch(server_id) and type(revision) is int and revision >= 0:
                backup = {"backupId": entry.name, "serverId": server_id, "sourceRevision": revision}
                action = data.get("action")
                if isinstance(action, str) and action in {"update-image", "exclude", "migrate-schema"}:
                    backup["action"] = action
                result.append(backup)
            elif data.get("action") == "migrate-schema" and type(revision) is int and revision >= 0:
                result.append({"backupId": entry.name, "serverId": "schema",
                               "sourceRevision": revision, "action": "migrate-schema"})
        return result

    def _transition_path(self, server_id: str) -> Path:
        return self.root / "transitions" / f"{server_id}.json"

    def _has_pending_unresolved(self) -> bool:
        """Return True if any transition journal is not in a terminal state.

        Used inside the config lock to detect a journal left ``prepare`` by a
        concurrent writer that started between the outside check and the
        lock acquisition. Recovery is intentionally not attempted here; the
        caller already had a chance to resolve prior pending journals and now
        needs a fast conflict signal before mutating config.
        """
        directory = self.root / "transitions"
        if not directory.exists():
            return False
        for path in directory.glob("*.json"):
            try:
                raw: object = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError, TypeError):
                return True
            if not isinstance(raw, dict):
                return True
            state = cast(dict[str, Any], raw).get("state")
            if not isinstance(state, str) or state not in {"committed", "failed"}:
                return True
        return False

    def _write_transition(self, server_id: str, value: dict[str, Any]) -> None:
        """Durably replace one private per-server recovery journal."""
        directory = self.root / "transitions"
        directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(directory, 0o700)
        path = self._transition_path(server_id)
        fd, temporary = tempfile.mkstemp(prefix=f".{server_id}.", suffix=".tmp", dir=directory)
        try:
            os.fchmod(fd, 0o600)
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(value, handle, ensure_ascii=False, separators=(",", ":"))
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, path)
            dir_fd = os.open(directory, os.O_RDONLY)
            try:
                os.fsync(dir_fd)
            finally:
                os.close(dir_fd)
        except Exception:
            try:
                os.unlink(temporary)
            except FileNotFoundError:
                pass
            raise

    def recover_pending(self) -> list[dict[str, Any]]:
        """Reconcile interrupted intents against persisted config and Docker.

        Config is the commit record: if its revision advanced, reconcile the
        broker to that intent; otherwise restore the pre-operation snapshot.
        Unverifiable transitions remain preparing and are surfaced to callers.
        """
        directory = self.root / "transitions"
        if not directory.exists():
            return []
        pending: list[dict[str, Any]] = []
        for path in sorted(directory.glob("*.json")):
            try:
                raw_journal: object = json.loads(path.read_text(encoding="utf-8"))
                if not isinstance(raw_journal, dict):
                    pending.append({"server_id": path.stem if SERVER_ID.fullmatch(path.stem) else "unknown", "state": "preparing"})
                    continue
                journal = cast(dict[str, Any], raw_journal)
                journal_state = journal.get("state")
                if journal_state in {"committed", "failed"}:
                    continue
                if journal_state != "preparing":
                    pending.append({"server_id": path.stem if SERVER_ID.fullmatch(path.stem) else "unknown", "state": "preparing"})
                    continue
                server_id_value = journal.get("server_id")
                if not isinstance(server_id_value, str) or not SERVER_ID.fullmatch(server_id_value):
                    pending.append({"server_id": "unknown", "state": "preparing"})
                    continue
                server_id = server_id_value
                if path != self._transition_path(server_id):
                    pending.append({"server_id": server_id, "state": "preparing"})
                    continue
                base_revision_value = journal.get("base_revision")
                if type(base_revision_value) is not int or base_revision_value < 0:
                    pending.append({"server_id": server_id, "state": "preparing"})
                    continue
                base_revision = base_revision_value
                result = self.config.run_serialized(
                    lambda _config_path: self._recover_transition(server_id, journal, base_revision)
                )
                if result is None:
                    journal_action = journal.get("action")
                    pending_entry: dict[str, Any] = {"server_id": server_id, "state": "preparing"}
                    if isinstance(journal_action, str):
                        pending_entry["action"] = journal_action
                    pending.append(pending_entry)
                else:
                    journal.update(state="committed", recovery=result, recovered_at=datetime.now(UTC).isoformat())
                    self._write_transition(server_id, journal)
                    revision = self.config.load().tools.mcp_docker.revision
                    action = journal.get("action")
                    correlation_id = journal.get("correlation_id")
                    if (isinstance(action, str) and action in {
                        "install", "configure", "disable-tool", "enable-tool", "activate",
                        "deactivate", "update-image", "restart", "start", "stop", "exclude", "restore",
                    } and isinstance(correlation_id, str) and re.fullmatch(r"[0-9a-f]{32}", correlation_id)):
                        phase = "committed" if result.startswith("committed-") else "failed"
                        self._audit(action, server_id, phase, revision, correlation_id)
            except (OSError, ValueError, TypeError, KeyError, BrokerRejectedError,
                    BrokerUnavailableError, BrokerError):
                name = path.stem
                if SERVER_ID.fullmatch(name):
                    pending.append({"server_id": name, "state": "preparing"})
        return pending

    def _recover_transition(self, server_id: str, journal: dict[str, Any], base_revision: int) -> str | None:
        """Apply persisted intent when committed, otherwise restore the snapshot."""
        config = self.config.load()
        section = config.tools.mcp_docker
        if section.revision not in {base_revision, base_revision + 1}:
            return None
        server = section.servers.get(server_id)
        if section.revision == base_revision + 1 and server is None:
            # Exclude committed in config. Broker exclude is idempotent for an
            # owned orphan container and does not remove volumes or images.
            self.broker.action("exclude", server_id, {"expected_confirmation": server_id})
            return "committed-exclude"
        if section.revision == base_revision + 1 and server is not None:
            host = section.configurations.get(server_id)
            if host is None:
                return None
            self.broker.action("recover", server_id, {
                "source": server.source.model_dump(mode="json"),
                "configuration": host.broker_payload(),
                "active": server.active,
                "tools_disabled": server.tools_disabled,
                "running": server.active and server.state != "stopped-persistent",
            })
            return "committed-config"
        previous = journal.get("before")
        if previous is None:
            self.broker.action("exclude", server_id, {"expected_confirmation": server_id})
            return "rolled-back-install"
        if not isinstance(previous, dict):
            return None
        before = cast(dict[str, Any], previous)
        old_server = DockerServer.model_validate(before.get("server"))
        old_host = DockerHostConfig.model_validate(before.get("configuration"))
        self.broker.action("recover", server_id, {
            "source": old_server.source.model_dump(mode="json"),
            "configuration": old_host.broker_payload(),
            "active": old_server.active,
            "tools_disabled": old_server.tools_disabled,
            "running": old_server.active and old_server.state != "stopped-persistent",
        })
        return "rolled-back-to-config"

    def _history(self, limit: int = 50) -> list[dict[str, Any]]:
        """Read a bounded audit tail and expose only non-sensitive event fields."""
        path = self.root / "audit.jsonl"
        try:
            with path.open("rb") as handle:
                handle.seek(0, os.SEEK_END)
                size = handle.tell()
                handle.seek(max(0, size - 256 * 1024))
                raw_tail = handle.read().decode("utf-8", errors="replace")
            lines = raw_tail.splitlines()[-limit:]
        except FileNotFoundError:
            return []
        except OSError:
            return []
        actions = {
            "install", "configure", "disable-tool", "enable-tool", "activate", "acquire",
            "deactivate", "update-image", "restart", "start", "stop", "exclude", "restore",
            "migrate-schema", "restore-schema-v1", "register-catalog",
        }
        phases = {"started", "committed", "failed", "compensation-failed"}
        events: list[dict[str, Any]] = []
        for line in lines:
            try:
                raw = json.loads(line)
            except (ValueError, TypeError):
                continue
            if not isinstance(raw, dict):
                continue
            raw_event = cast(dict[str, Any], raw)
            at = raw_event.get("at")
            action = raw_event.get("action")
            server_id = raw_event.get("server_id")
            phase = raw_event.get("phase")
            revision = raw_event.get("revision")
            correlation_id = raw_event.get("correlation_id")
            if (not isinstance(at, str) or not isinstance(action, str) or action not in actions or
                not isinstance(server_id, str) or not SERVER_ID.fullmatch(server_id) or
                not isinstance(phase, str) or phase not in phases or
                type(revision) is not int or revision < 0 or
                not isinstance(correlation_id, str) or re.fullmatch(r"[0-9a-f]{32}", correlation_id) is None):
                continue
            try:
                datetime.fromisoformat(at)
            except ValueError:
                continue
            event = {"at": at, "action": action, "server_id": server_id,
                     "phase": phase, "revision": revision,
                     "correlation_id": correlation_id}
            scope_change = raw_event.get("scope_change")
            if scope_change in {"host_mounts_to_full", "network_none_to_bridge",
                                "host_mounts_to_full+network_none_to_bridge"}:
                event["scope_change"] = scope_change
            events.append(event)
        return list(reversed(events))

    def _backup(self, config: Config, server_id: str, action: str) -> Path:
        section = config.tools.mcp_docker
        stamp = datetime.now(UTC).strftime("%Y-%m-%dT%H-%M-%S")
        backup_root = self.root / "backups"
        backup_root.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(backup_root, 0o700)
        folder = backup_root / f"{stamp}-{server_id}-{uuid.uuid4().hex}"
        folder.mkdir(mode=0o700)
        manifest = {
            "schemaVersion": 1,
            "action": action,
            "server_id": server_id,
            "source_revision": section.revision,
            "server": section.servers[server_id].model_dump(mode="json", by_alias=True),
            "configuration": section.configurations[server_id].model_dump(mode="json", by_alias=True),
            "app_release": section.app_releases[server_id].model_dump(mode="json", by_alias=True)
            if server_id in section.app_releases else None,
        }
        manifest["sha256"] = hashlib.sha256(json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        path = folder / "manifest.json"
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(manifest, handle, ensure_ascii=False)
            handle.flush()
            os.fsync(handle.fileno())
        return folder

    def _audit(
        self, action: str, server_id: str, phase: str, revision: int,
        correlation_id: str, *, scope_change: str | None = None,
    ) -> None:
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        path = self.root / "audit.jsonl"
        fd = os.open(path, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)
        with os.fdopen(fd, "a", encoding="utf-8") as handle:
            event = {"at": datetime.now(UTC).isoformat(), "action": action,
                     "server_id": server_id, "phase": phase,
                     "revision": revision, "correlation_id": correlation_id}
            if scope_change is not None:
                event["scope_change"] = scope_change
            handle.write(json.dumps(event) + "\n")
            handle.flush()
            os.fsync(handle.fileno())

    def act(self, action: str, payload: dict[str, Any]) -> dict[str, Any]:
        allowed: dict[str, set[str]] = {
            "install": {"source", "configuration", "app_release", "expected_confirmation"},
            "configure": {"configuration", "expected_confirmation"},
            "disable-tool": {"tool"}, "enable-tool": {"tool"},
            "activate": set(), "deactivate": set(),
            "update-image": {"source"}, "restart": set(),
            "start": set(), "stop": set(), "exclude": {"expected_confirmation"},
        }
        if action not in allowed or set(payload) - ({"server_id", "expected_revision", "expected_server_revision"} | allowed[action]):
            raise DomainError(400, "unsupported Docker MCP operation or fields")
        server_id = payload.get("server_id")
        from nanobot.config.mcp_docker import SERVER_ID
        if not isinstance(server_id, str) or not SERVER_ID.fullmatch(server_id):
            raise DomainError(400, "invalid server_id")
        expected = payload.get("expected_revision")
        if type(expected) is not int or expected < 0:
            raise DomainError(400, "expected_revision must be a nonnegative integer")
        pending = self.recover_pending()
        if pending:
            raise DomainError(503, "an MCP Docker transition is unresolved; inspect the pending recovery state")
        correlation_id = uuid.uuid4().hex

        def transaction(path: Path) -> dict[str, Any]:
            from nanobot.config.loader import load_config, save_config

            config = load_config(path)
            section = config.tools.mcp_docker
            if section.revision != expected:
                raise DomainError(409, "Docker MCP revision conflict")
            # Re-check pending journals inside the lock: a writer may have left
            # a fresh "preparing" journal between the outside recovery attempt
            # and this lock acquisition. We must not stack a new transition on
            # top of an in-flight one even if their targets are different.
            if self._has_pending_unresolved():
                raise DomainError(503, "an MCP Docker transition is unresolved; inspect the pending recovery state")
            current = section.servers.get(server_id)
            if (current is None) == (action != "install"):
                raise DomainError(409, "server already exists" if current else "unknown server_id")
            if current is not None:
                expected_server_revision = payload.get("expected_server_revision")
                if type(expected_server_revision) is not int or expected_server_revision < 0:
                    raise DomainError(400, "expected_server_revision must be a nonnegative integer")
                if expected_server_revision != current.revision:
                    raise DomainError(409, "server revision conflict")
            if action == "exclude" and payload.get("expected_confirmation") != server_id:
                raise DomainError(400, "confirmation must equal server_id")
            if action in {"start", "stop"} and (not section.configurations[server_id].persistent or not current or not current.active):
                raise DomainError(409, "start/stop requires an active persistent server")
            if action in {"restart", "activate"} and current and action == "restart" and not current.active:
                raise DomainError(409, "server is inactive")
            if current and current.state == "stopped-persistent" and action in {"configure", "update-image"}:
                raise DomainError(409, "start the persistent server before changing its container")
            # Reject silent privilege escalation via a missing ``mounts`` key.
            # The default for ``mounts`` is ``None`` (Full host access). ``install``
            # is allowed to omit it because Full access is the documented default,
            # but ``configure`` must receive an explicit value so a stale or
            # buggy client cannot widen an existing reduction without intent.
            if action == "configure":
                configuration_obj = payload.get("configuration")
                if not isinstance(configuration_obj, dict) or "mounts" not in cast(dict[str, Any], configuration_obj):
                    raise DomainError(400, "mounts is required for configure; pass null, [] or a list")

            try:
                source = DockerImageSource.model_validate(payload["source"]) if action in {"install", "update-image"} else None
                host = self._host(payload["configuration"], section.configurations.get(server_id)) if action in {"install", "configure"} else None
                raw_app_release = payload.get("app_release")
                app_release = ManagedAppReference.model_validate(raw_app_release) if raw_app_release is not None else None
            except (ValidationError, KeyError, ValueError) as exc:
                raise DomainError(400, "invalid image or host configuration") from exc
            if action == "install" and app_release is not None:
                if section.schema_version != 2 or source is None or host is None:
                    raise DomainError(409, "catalog apps require MCP config schema version 2")
                if (source.type != "pinned-image" or source.reference != app_release.repository_digest or
                    payload.get("expected_confirmation") != f"{server_id}/{app_release.app_id}@{app_release.version}"):
                    raise DomainError(400, "catalog install confirmation or digest does not match the approved app")
                self._validate_app_host(section, app_release, host)
            if action == "install" and section.schema_version == 1 and payload.get("app_release") is not None:
                raise DomainError(409, "migrate MCP Docker config to schema version 2 first")
            if action == "configure" and current is not None and host is not None:
                release = section.app_releases.get(server_id)
                if release is not None:
                    self._validate_app_host(section, release, host)
            if action == "update-image" and server_id in section.app_releases:
                raise DomainError(409, "catalog-managed images must be updated from a trusted catalog release")
            scope_changes: list[str] = []
            if action == "configure" and current is not None and host is not None:
                previous_host = section.configurations[server_id]
                if previous_host.mounts is not None and host.mounts is None:
                    scope_changes.append("host_mounts_to_full")
                if previous_host.network == "none" and host.network == "bridge":
                    scope_changes.append("network_none_to_bridge")
                if scope_changes and payload.get("expected_confirmation") != server_id:
                    raise DomainError(400, "confirmation must equal server_id when increasing host or network access")
            scope_change = "+".join(scope_changes) if scope_changes else None
            if action == "update-image" and current and source == current.source:
                raise DomainError(409, "image identity is unchanged")
            tool = payload.get("tool")
            if action in {"disable-tool", "enable-tool"} and (not isinstance(tool, str) or not tool):
                raise DomainError(400, "tool must be a nonempty raw name")
            backup = self._backup(config, server_id, action) if action in {"update-image", "exclude"} else None
            before = None if current is None else {
                "server": current.model_dump(mode="json", by_alias=True),
                "configuration": section.configurations[server_id].model_dump(mode="json", by_alias=True),
                "app_release": section.app_releases[server_id].model_dump(mode="json", by_alias=True)
                if server_id in section.app_releases else None,
            }
            journal: dict[str, Any] = {
                "schemaVersion": 1,
                "server_id": server_id,
                "action": action,
                "state": "preparing",
                "base_revision": section.revision,
                "correlation_id": correlation_id,
                "backup_path": str(backup) if backup else None,
                "before": before,
                "started_at": datetime.now(UTC).isoformat(),
            }
            self._write_transition(server_id, journal)
            self._audit(action, server_id, "started", section.revision, correlation_id,
                        scope_change=scope_change)
            old_source = current.source.model_dump(mode="json") if current else None
            broker_succeeded = False
            try:
                managed_state = None
                if current is not None and action != "exclude":
                    managed_host = section.configurations[server_id]
                    managed_state = {
                        "source": current.source.model_dump(mode="json"),
                        "configuration": managed_host.broker_payload(),
                        "active": current.active,
                        "tools_disabled": list(current.tools_disabled),
                        "tools": list(current.tools),
                    }
                broker_payload = {
                    **({"source": source.model_dump(mode="json")} if source else {}),
                    **({"configuration": host.broker_payload()} if host else {}),
                    **({"tool": tool} if action in {"disable-tool", "enable-tool"} else {}),
                    **({"expected_confirmation": server_id} if action == "exclude" else {}),
                }
                if managed_state is not None:
                    status = self.broker.action("status", server_id, {})
                    if status.get("registered") is not True:
                        self.broker.action("hydrate", server_id, managed_state)
                # The broker receives only typed actions and configuration when
                # its volatile registry must be rehydrated after process restart.
                try:
                    result = self.broker.action(action, server_id, broker_payload)
                except BrokerRejectedError as exc:
                    if managed_state is None or exc.status_code != 404:
                        raise
                    # The broker may restart between the status probe and action.
                    self.broker.action("hydrate", server_id, managed_state)
                    result = self.broker.action(action, server_id, broker_payload)
                broker_succeeded = True
                if action == "install":
                    assert source is not None and host is not None
                    section.servers[server_id] = DockerServer(server_id=server_id, source=source,
                                                                tools=result.get("tools", []),
                                                                state="running" if result.get("running") else "pending-broker")
                    section.configurations[server_id] = host
                    if app_release is not None:
                        section.app_releases[server_id] = app_release
                elif action == "exclude":
                    del section.servers[server_id]
                    del section.configurations[server_id]
                    section.app_releases.pop(server_id, None)
                elif current is not None:
                    current.revision += 1
                    if action == "configure" and host is not None:
                        section.configurations[server_id] = host
                    if action == "update-image" and source is not None:
                        current.source = source
                        discovered = result.get("tools")
                        if isinstance(discovered, list):
                            current.tools = discovered
                            current.tools_disabled = [name for name in current.tools_disabled if name in discovered]
                    if action in {"activate", "configure", "restart", "start"} and isinstance(result.get("tools"), list):
                        current.tools = result["tools"]
                    if action in {"disable-tool", "enable-tool"}:
                        names = set(current.tools_disabled)
                        assert isinstance(tool, str)
                        (names.add if action == "disable-tool" else names.discard)(tool)
                        current.tools_disabled = sorted(names)
                    if action in {"activate", "deactivate"}:
                        current.active = action == "activate"
                    current.state = ("configured-disabled" if not current.active else
                                     "stopped-persistent" if action == "stop" else
                                     "running" if result.get("running") else "pending-broker")
                section.revision += 1
                save_config(config, path)
            except Exception:
                # Docker and config are separate durability domains. Attempt
                # compensation while the old intent is still persisted; never
                # claim that a failed compensation restored a running server.
                if action == "update-image" and old_source is not None:
                    try:
                        self.broker.action("update-image", server_id, {
                            "source": old_source,
                        })
                    except Exception:
                        self._audit(action, server_id, "compensation-failed", section.revision,
                                    correlation_id, scope_change=scope_change)
                if action == "install" and broker_succeeded:
                    try:
                        self.broker.action("exclude", server_id, {"expected_confirmation": server_id})
                    except Exception:
                        self._audit(action, server_id, "compensation-failed", section.revision,
                                    correlation_id, scope_change=scope_change)
                self._audit(action, server_id, "failed", section.revision, correlation_id,
                            scope_change=scope_change)
                try:
                    recovered = self._recover_transition(server_id, journal, section.revision)
                except Exception:
                    recovered = None
                journal.update(
                    state="failed" if recovered is not None else "preparing",
                    recovery_error=None if recovered is not None else "compensation could not be verified",
                    finished_at=datetime.now(UTC).isoformat() if recovered is not None else None,
                )
                self._write_transition(server_id, journal)
                raise
            self._audit(action, server_id, "committed", section.revision, correlation_id,
                        scope_change=scope_change)
            journal.update(state="committed", committed_revision=section.revision,
                           finished_at=datetime.now(UTC).isoformat())
            self._write_transition(server_id, journal)
            return {"revision": section.revision, "server": server_id,
                    "state": section.servers[server_id].state if server_id in section.servers else "excluded",
                    "backup": str(backup) if backup else None}

        return self.config.run_serialized(transaction)

    def restore_backup(
        self,
        backup_dir: Path,
        expected_revision: int,
        expected_confirmation: str,
    ) -> dict[str, Any]:
        """Restore one excluded server through the single-writer transaction."""
        pending = self.recover_pending()
        if pending:
            raise DomainError(503, "an MCP Docker transition is unresolved; inspect the pending recovery state")
        base = self.root / "backups"
        if backup_dir.is_symlink() or backup_dir.resolve().parent != base.resolve():
            raise DomainError(400, "backup must be a direct child of the MCP Docker backup directory")
        manifest_path = backup_dir / "manifest.json"
        if manifest_path.is_symlink() or not manifest_path.is_file():
            raise DomainError(400, "backup manifest missing")
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            if not isinstance(manifest, dict):
                raise ValueError("manifest must be an object")
            manifest_obj = cast(dict[str, Any], manifest)
            checksum = manifest_obj.pop("sha256", None)
            canonical = json.dumps(manifest_obj, sort_keys=True, separators=(",", ":")).encode()
            if not isinstance(checksum, str) or not hmac.compare_digest(checksum, hashlib.sha256(canonical).hexdigest()):
                raise ValueError("checksum mismatch")
            if manifest_obj.get("schemaVersion") != 1:
                raise ValueError("unsupported backup schema")
            server_id = manifest_obj.get("server_id")
            server = DockerServer.model_validate(manifest_obj.get("server"))
            host = DockerHostConfig.model_validate(manifest_obj.get("configuration"))
            raw_app_release = manifest_obj.get("app_release")
            app_release = ManagedAppReference.model_validate(raw_app_release) if raw_app_release is not None else None
            if not isinstance(server_id, str) or server.server_id != server_id:
                raise ValueError("server ID mismatch")
        except (OSError, ValueError, TypeError, ValidationError) as exc:
            raise DomainError(400, "invalid or tampered MCP Docker backup") from exc
        if expected_confirmation != server_id:
            raise DomainError(400, "confirmation must equal server_id")
        correlation_id = uuid.uuid4().hex

        def transaction(path: Path) -> dict[str, Any]:
            from nanobot.config.loader import load_config, save_config

            config = load_config(path)
            section = config.tools.mcp_docker
            if type(expected_revision) is not int or expected_revision < 0:
                raise DomainError(400, "expected revision must be a nonnegative integer")
            if section.revision != expected_revision:
                raise DomainError(409, "Docker MCP revision conflict")
            # See the matching check in `act`; restore must honour the same
            # in-flight journal invariant under the lock.
            if self._has_pending_unresolved():
                raise DomainError(503, "an MCP Docker transition is unresolved; inspect the pending recovery state")
            if server_id in section.servers:
                raise DomainError(409, "restore refuses to overwrite an existing server")
            if app_release is not None:
                if section.schema_version != 2:
                    raise DomainError(409, "catalog-managed backup requires MCP config schema version 2")
                self._validate_app_host(section, app_release, host)
            journal: dict[str, Any] = {
                "schemaVersion": 1,
                "server_id": server_id,
                "action": "restore",
                "state": "preparing",
                "base_revision": section.revision,
                "correlation_id": correlation_id,
                "backup_path": str(backup_dir),
                "before": None,
                "started_at": datetime.now(UTC).isoformat(),
            }
            self._write_transition(server_id, journal)
            self._audit("restore", server_id, "started", section.revision, correlation_id)
            server.revision += 1
            server.state = "installed" if not server.active else "starting"
            try:
                result = self.broker.action("reconcile", server_id, {
                    "source": server.source.model_dump(mode="json"),
                    "configuration": host.broker_payload(),
                    "active": server.active,
                    "tools_disabled": server.tools_disabled,
                })
                if server.active and not result.get("running"):
                    raise BrokerUnavailableError("broker did not start the restored server")
                if isinstance(result.get("tools"), list):
                    server.tools = result["tools"]
                    server.tools_disabled = [name for name in server.tools_disabled if name in server.tools]
                server.state = "running" if result.get("running") else "configured-disabled"
                section.servers[server_id] = server
                section.configurations[server_id] = host
                if app_release is not None:
                    section.app_releases[server_id] = app_release
                section.revision += 1
                save_config(config, path)
            except Exception:
                try:
                    self.broker.action("exclude", server_id, {"expected_confirmation": server_id})
                except Exception:
                    self._audit("restore", server_id, "compensation-failed", section.revision, correlation_id)
                self._audit("restore", server_id, "failed", section.revision, correlation_id)
                try:
                    recovered = self._recover_transition(server_id, journal, section.revision)
                except Exception:
                    recovered = None
                journal.update(
                    state="failed" if recovered is not None else "preparing",
                    recovery_error=None if recovered is not None else "compensation could not be verified",
                    finished_at=datetime.now(UTC).isoformat() if recovered is not None else None,
                )
                self._write_transition(server_id, journal)
                raise
            self._audit("restore", server_id, "committed", section.revision, correlation_id)
            journal.update(state="committed", committed_revision=section.revision,
                           finished_at=datetime.now(UTC).isoformat())
            self._write_transition(server_id, journal)
            return {"server": server_id, "revision": section.revision,
                    "state": server.state, "running": bool(result.get("running"))}

        return self.config.run_serialized(transaction)

    @staticmethod
    def _host(value: object, previous: DockerHostConfig | None) -> DockerHostConfig:
        if not isinstance(value, dict):
            raise ValueError("configuration must be an object")
        values = dict(cast(dict[str, Any], value))
        env: object = values.get("env", {})
        if isinstance(env, dict):
            entries = cast(dict[str, Any], env)
            for name, item in entries.items():
                if isinstance(item, dict) and cast(dict[str, Any], item).get("value") == REDACTED_SECRET:
                    old = previous.env.get(name) if previous else None
                    if old is None or old.kind != "secret" or cast(dict[str, Any], item).get("kind") != "secret":
                        raise ValueError("secret sentinel requires an existing secret")
                    entries[name] = {"kind": "secret", "value": old.value}
        return DockerHostConfig.model_validate(values)
