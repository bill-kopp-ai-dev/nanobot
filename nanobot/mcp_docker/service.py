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
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol, cast

from pydantic import ValidationError

from nanobot.config.mcp_docker import (
    REDACTED_SECRET,
    SERVER_ID,
    DockerHostConfig,
    DockerImageSource,
    DockerServer,
)
from nanobot.config.schema import Config
from nanobot.mcp_docker.client import BrokerUnavailableError
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


class DockerMcpService:
    def __init__(self, config: WebUISettingsConfig, broker: Broker) -> None:
        self.config = config
        self.broker = broker
        self.root = config.path.parent / "mcp-docker"

    def list(self) -> dict[str, Any]:
        section = self.config.load().tools.mcp_docker
        servers: dict[str, Any] = {}
        for key, server in section.servers.items():
            observation: dict[str, Any]
            try:
                observation = self.broker.action("observe", key, {
                    "source": server.source.model_dump(mode="json"),
                })
            except BrokerUnavailableError:
                observation = {
                    "dockerObservation": "unknown",
                    "mcpConnectivity": "unknown",
                    "observationError": "Docker MCP broker unavailable",
                }
            docker_state = observation.get("dockerObservation")
            mcp_state = observation.get("mcpConnectivity")
            observed_tools = observation.get("tools")
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
                **({"observationError": "Docker MCP broker unavailable"}
                   if observation.get("observationError") else {}),
            }
        return {
            "schemaVersion": section.schema_version,
            "revision": section.revision,
            "allowRemoteAdmin": section.allow_remote_admin,
            "servers": servers,
            "history": self._history(),
        }

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
            "install", "configure", "disable-tool", "enable-tool", "activate",
            "deactivate", "update-image", "restart", "start", "stop", "exclude", "restore",
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
            events.append({"at": at, "action": action, "server_id": server_id,
                           "phase": phase, "revision": revision,
                           "correlation_id": correlation_id})
        return list(reversed(events))

    def _backup(self, config: Config, server_id: str) -> Path:
        section = config.tools.mcp_docker
        stamp = datetime.now(UTC).strftime("%Y-%m-%dT%H-%M-%S")
        folder = self.root / "backups" / f"{stamp}-{server_id}-{uuid.uuid4().hex}"
        folder.mkdir(parents=True, mode=0o700)
        manifest = {
            "schemaVersion": 1,
            "server_id": server_id,
            "source_revision": section.revision,
            "server": section.servers[server_id].model_dump(mode="json", by_alias=True),
            "configuration": section.configurations[server_id].model_dump(mode="json", by_alias=True),
        }
        import hashlib
        manifest["sha256"] = hashlib.sha256(json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        path = folder / "manifest.json"
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(manifest, handle, ensure_ascii=False)
            handle.flush()
            os.fsync(handle.fileno())
        return folder

    def _audit(self, action: str, server_id: str, phase: str, revision: int, correlation_id: str) -> None:
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        path = self.root / "audit.jsonl"
        fd = os.open(path, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)
        with os.fdopen(fd, "a", encoding="utf-8") as handle:
            handle.write(json.dumps({"at": datetime.now(UTC).isoformat(), "action": action,
                                     "server_id": server_id, "phase": phase,
                                     "revision": revision, "correlation_id": correlation_id}) + "\n")
            handle.flush()
            os.fsync(handle.fileno())

    def act(self, action: str, payload: dict[str, Any]) -> dict[str, Any]:
        allowed: dict[str, set[str]] = {
            "install": {"source", "configuration"},
            "configure": {"configuration"},
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
        correlation_id = uuid.uuid4().hex

        def transaction(path: Path) -> dict[str, Any]:
            from nanobot.config.loader import load_config, save_config

            config = load_config(path)
            section = config.tools.mcp_docker
            if section.revision != expected:
                raise DomainError(409, "Docker MCP revision conflict")
            current = section.servers.get(server_id)
            if (current is None) == (action != "install"):
                raise DomainError(409, "server already exists" if current else "unknown server_id")
            if current is not None and payload.get("expected_server_revision") != current.revision:
                raise DomainError(409, "server revision conflict")
            if action == "exclude" and payload.get("expected_confirmation") != server_id:
                raise DomainError(400, "confirmation must equal server_id")
            if action in {"start", "stop"} and (not section.configurations[server_id].persistent or not current or not current.active):
                raise DomainError(409, "start/stop requires an active persistent server")
            if action in {"restart", "activate"} and current and action == "restart" and not current.active:
                raise DomainError(409, "server is inactive")

            try:
                source = DockerImageSource.model_validate(payload["source"]) if action in {"install", "update-image"} else None
                host = self._host(payload["configuration"], section.configurations.get(server_id)) if action in {"install", "configure"} else None
            except (ValidationError, KeyError, ValueError) as exc:
                raise DomainError(400, "invalid image or host configuration") from exc
            tool = payload.get("tool")
            if action in {"disable-tool", "enable-tool"} and (not isinstance(tool, str) or not tool):
                raise DomainError(400, "tool must be a nonempty raw name")
            backup = self._backup(config, server_id) if action in {"update-image", "exclude"} else None
            self._audit(action, server_id, "started", section.revision, correlation_id)
            old_source = current.source.model_dump(mode="json") if current else None
            broker_succeeded = False
            try:
                # The broker receives only typed actions and host configuration;
                # it validates the effective Docker access before starting.
                result = self.broker.action(action, server_id, {
                    **({"source": source.model_dump(mode="json")} if source else {}),
                    **({"configuration": host.model_dump(mode="json")} if host else {}),
                    **({"tool": tool} if action in {"disable-tool", "enable-tool"} else {}),
                    **({"expected_confirmation": server_id} if action == "exclude" else {}),
                })
                broker_succeeded = True
                if action == "install":
                    assert source is not None and host is not None
                    section.servers[server_id] = DockerServer(server_id=server_id, source=source,
                                                                tools=result.get("tools", []),
                                                                state="running" if result.get("running") else "pending-broker")
                    section.configurations[server_id] = host
                elif action == "exclude":
                    del section.servers[server_id]
                    del section.configurations[server_id]
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
                        self._audit(action, server_id, "compensation-failed", section.revision, correlation_id)
                if action == "install" and broker_succeeded:
                    try:
                        self.broker.action("exclude", server_id, {"expected_confirmation": server_id})
                    except Exception:
                        self._audit(action, server_id, "compensation-failed", section.revision, correlation_id)
                self._audit(action, server_id, "failed", section.revision, correlation_id)
                raise
            self._audit(action, server_id, "committed", section.revision, correlation_id)
            return {"revision": section.revision, "server": server_id,
                    "state": section.servers[server_id].state if server_id in section.servers else "excluded",
                    "backup": str(backup) if backup else None}

        return self.config.run_serialized(transaction)

    def restore_backup(self, backup_dir: Path, expected_revision: int) -> dict[str, Any]:
        """Restore one excluded server through the single-writer transaction."""
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
            if not isinstance(server_id, str) or server.server_id != server_id:
                raise ValueError("server ID mismatch")
        except (OSError, ValueError, TypeError, ValidationError) as exc:
            raise DomainError(400, "invalid or tampered MCP Docker backup") from exc
        correlation_id = uuid.uuid4().hex

        def transaction(path: Path) -> dict[str, Any]:
            from nanobot.config.loader import load_config, save_config

            config = load_config(path)
            section = config.tools.mcp_docker
            if type(expected_revision) is not int or expected_revision < 0:
                raise DomainError(400, "expected revision must be a nonnegative integer")
            if section.revision != expected_revision:
                raise DomainError(409, "Docker MCP revision conflict")
            if server_id in section.servers:
                raise DomainError(409, "restore refuses to overwrite an existing server")
            self._audit("restore", server_id, "started", section.revision, correlation_id)
            server.revision += 1
            server.state = "installed" if not server.active else "starting"
            try:
                result = self.broker.action("reconcile", server_id, {
                    "source": server.source.model_dump(mode="json"),
                    "configuration": host.model_dump(mode="json"),
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
                section.revision += 1
                save_config(config, path)
            except Exception:
                try:
                    self.broker.action("exclude", server_id, {"expected_confirmation": server_id})
                except Exception:
                    self._audit("restore", server_id, "compensation-failed", section.revision, correlation_id)
                self._audit("restore", server_id, "failed", section.revision, correlation_id)
                raise
            self._audit("restore", server_id, "committed", section.revision, correlation_id)
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
