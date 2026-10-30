from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from pathlib import Path

import pytest
import yaml

from nanobot.config.loader import load_config, save_config
from nanobot.config.mcp_docker import DockerEnvValue, TrustedCatalogConfig
from nanobot.mcp_docker import catalog as catalog_module
from nanobot.mcp_docker.catalog import (
    APP_SCHEMA,
    CatalogApp,
    CatalogEnvironmentVariable,
    CatalogError,
    CatalogMount,
    load_catalog_snapshot,
    resolve_app_profile,
)
from nanobot.mcp_docker.service import DockerMcpService, DomainError
from nanobot.webui.settings_services import WebUISettingsConfig


def _write_snapshot(root: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, str, dict[str, str]]:
    app = {
        "schema_version": "0.2",
        "id": "pblabs.example",
        "mcp_name": "io.github.p-bean-labs/example-mcp",
        "version": "1.2.3",
        "publisher": "Positronic Bean Labs",
        "source_class": "official",
        "runtime": {"container": True, "transport": "stdio", "startup": "on-demand"},
        "compatibility": {"products": ["percival"], "platforms": ["linux/amd64"]},
        "configuration": {"required_secrets": ["API_KEY"], "writable_data": True},
        "security": {"needs_network": True},
        "mounts": [{
            "target": "/data", "kind": "data", "access": "read-write",
            "required": True, "source": "installation-configured",
        }],
        "lifecycle": {
            "owner": "native-mcp-manager",
            "init": {"required": True, "provider": "container-runtime"},
            "restart_policy": "manager-policy",
            "grace_period_seconds": None,
            "observed": {
                "readiness": "mcp-initialize", "stdin_eof_exit_code": 0,
                "sigterm_exit_code": 0, "sigterm_shutdown_hook": "not-verified",
                "sigint": "not-observed",
            },
        },
        "review": {"status": "approved", "approved_release": "1.2.3"},
    }
    server = {
        "$schema": "https://static.modelcontextprotocol.io/schemas/2025-12-11/server.schema.json",
        "name": app["mcp_name"],
        "version": app["version"],
        "description": "Fixture MCP server.",
        "packages": [{
            "registryType": "oci",
            "identifier": "docker.io/pbeanlabs/example-mcp@sha256:" + "a" * 64,
            "transport": {"type": "stdio"},
            "environmentVariables": [{"name": "API_KEY", "isRequired": True, "isSecret": True}],
        }],
    }
    app_path = root / "servers/example/pblabs.app.yaml"
    server_path = root / "servers/example/server.json"
    docs_path = root / "servers/example/README.md"
    server_schema_path = root / "schemas/server.schema.2025-12-11.json"
    for path in (app_path, server_path, docs_path):
        path.parent.mkdir(parents=True, exist_ok=True)
    server_schema_path.parent.mkdir(parents=True, exist_ok=True)
    app_bytes = yaml.safe_dump(app, sort_keys=False).encode()
    server_bytes = (json.dumps(server, sort_keys=True) + "\n").encode()
    docs_bytes = b"# Example MCP\n"
    server_schema_bytes = json.dumps({
        "$schema": "http://json-schema.org/draft-07/schema#",
        "$id": "https://static.modelcontextprotocol.io/schemas/2025-12-11/server.schema.json",
        "type": "object",
        "required": ["$schema", "name", "version", "description", "packages"],
        "properties": {
            "$schema": {"const": "https://static.modelcontextprotocol.io/schemas/2025-12-11/server.schema.json"},
            "name": {"type": "string"},
            "version": {"type": "string"},
            "description": {"type": "string"},
            "packages": {"type": "array"},
        },
    }, sort_keys=True).encode()
    app_path.write_bytes(app_bytes)
    server_path.write_bytes(server_bytes)
    docs_path.write_bytes(docs_bytes)
    server_schema_path.write_bytes(server_schema_bytes)
    entry = {
        "id": app["id"],
        "source_class": app["source_class"],
        "version": app["version"],
        "server_json": "servers/example/server.json",
        "server_json_sha256": hashlib.sha256(server_bytes).hexdigest(),
        "manifest": "servers/example/pblabs.app.yaml",
        "manifest_sha256": hashlib.sha256(app_bytes).hexdigest(),
        "documentation": "servers/example/README.md",
        "documentation_sha256": hashlib.sha256(docs_bytes).hexdigest(),
    }
    server_schema_sha256 = hashlib.sha256(server_schema_bytes).hexdigest()
    monkeypatch.setattr(catalog_module, "SERVER_SCHEMA_SHA256", server_schema_sha256)
    catalog_bytes = (json.dumps({
        "schema_version": "1.0",
        "app_schema": {"version": "0.2", "sha256": hashlib.sha256(APP_SCHEMA.read_bytes()).hexdigest()},
        "server_schema": {"path": "schemas/server.schema.2025-12-11.json", "sha256": server_schema_sha256},
        "entries": [entry],
    }, sort_keys=True) + "\n").encode()
    catalog_path = root / "public/catalog.json"
    catalog_path.parent.mkdir(parents=True)
    catalog_path.write_bytes(catalog_bytes)
    return root, hashlib.sha256(catalog_bytes).hexdigest(), entry


def test_load_catalog_snapshot_validates_0_2_profile_and_pinned_digests(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, catalog_hash, _entry = _write_snapshot(tmp_path, monkeypatch)

    apps = load_catalog_snapshot(root, catalog_hash)

    assert len(apps) == 1
    app = apps[0]
    assert app.app_id == "pblabs.example"
    assert app.repository_digest.endswith("@sha256:" + "a" * 64)
    assert app.needs_network is True
    assert app.required_secrets == ("API_KEY",)
    assert [(mount.target, mount.access) for mount in app.mounts] == [("/data", "read-write")]
    host = resolve_app_profile(
        app,
        mount_sources={"/data": "/srv/example-data"},
        environment={"API_KEY": DockerEnvValue(kind="secret", value="fixture-only-secret")},
        host_mounts=[],
    )
    assert host.mounts == []
    assert host.network == "bridge"
    assert host.app_mounts[0].source == "/srv/example-data"
    assert host.app_mounts[0].target == "/data"
    assert host.app_mounts[0].read_only is False


def test_profile_resolution_fails_closed_on_missing_mapping_secret_or_widened_network(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, catalog_hash, _entry = _write_snapshot(tmp_path, monkeypatch)
    app = load_catalog_snapshot(root, catalog_hash)[0]
    secret = DockerEnvValue(kind="secret", value="fixture-only-secret")
    with pytest.raises(CatalogError, match="mount mappings"):
        resolve_app_profile(app, mount_sources={}, environment={"API_KEY": secret}, host_mounts=[])
    with pytest.raises(CatalogError, match="typed registry declarations"):
        resolve_app_profile(
            app, mount_sources={"/data": "/srv/example-data"},
            environment={"API_KEY": DockerEnvValue(kind="plain", value="not-secret")}, host_mounts=[],
        )
    with pytest.raises(CatalogError, match="explicit host access"):
        resolve_app_profile(
            app, mount_sources={"/data": "/srv/example-data"}, environment={"API_KEY": secret},
        )
    with pytest.raises(CatalogError, match="exceed the app profile"):
        resolve_app_profile(
            replace(app, needs_network=False),
            mount_sources={"/data": "/srv/example-data"},
            environment={"API_KEY": secret},
            host_mounts=[],
            network="bridge",
        )


def test_catalog_snapshot_rejects_stale_hash_manifest_approval_or_host_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, _catalog_hash, entry = _write_snapshot(tmp_path, monkeypatch)
    with pytest.raises(CatalogError, match="trusted SHA-256"):
        load_catalog_snapshot(root, "0" * 64)

    app_path = root / entry["manifest"]
    app = yaml.safe_load(app_path.read_text())
    app["review"] = {"status": "manifest-approved"}
    app_bytes = yaml.safe_dump(app, sort_keys=False).encode()
    app_path.write_bytes(app_bytes)
    entry["manifest_sha256"] = hashlib.sha256(app_bytes).hexdigest()
    catalog = json.loads((root / "public/catalog.json").read_text())
    catalog["entries"] = [entry]
    catalog_bytes = (json.dumps(catalog, sort_keys=True) + "\n").encode()
    (root / "public/catalog.json").write_bytes(catalog_bytes)
    with pytest.raises(CatalogError, match="not an approved app release"):
        load_catalog_snapshot(root, hashlib.sha256(catalog_bytes).hexdigest())


def test_catalog_snapshot_never_accepts_host_source_metadata(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, _catalog_hash, entry = _write_snapshot(tmp_path, monkeypatch)
    app_path = root / entry["manifest"]
    app = yaml.safe_load(app_path.read_text())
    app["mounts"][0]["host_path"] = "/srv/real-data"
    app_bytes = yaml.safe_dump(app, sort_keys=False).encode()
    app_path.write_bytes(app_bytes)
    entry["manifest_sha256"] = hashlib.sha256(app_bytes).hexdigest()
    catalog = json.loads((root / "public/catalog.json").read_text())
    catalog["entries"] = [entry]
    catalog_bytes = (json.dumps(catalog, sort_keys=True) + "\n").encode()
    (root / "public/catalog.json").write_bytes(catalog_bytes)

    with pytest.raises(CatalogError, match="invalid PBLabs app manifest"):
        load_catalog_snapshot(root, hashlib.sha256(catalog_bytes).hexdigest())


def test_catalog_snapshot_rejects_embedded_environment_values(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, _catalog_hash, entry = _write_snapshot(tmp_path, monkeypatch)
    server_path = root / entry["server_json"]
    server = json.loads(server_path.read_text())
    server["packages"][0]["environmentVariables"][0]["value"] = "must-not-be-in-catalog"
    server_bytes = (json.dumps(server, sort_keys=True) + "\n").encode()
    server_path.write_bytes(server_bytes)
    entry["server_json_sha256"] = hashlib.sha256(server_bytes).hexdigest()
    catalog = json.loads((root / "public/catalog.json").read_text())
    catalog["entries"] = [entry]
    catalog_bytes = (json.dumps(catalog, sort_keys=True) + "\n").encode()
    (root / "public/catalog.json").write_bytes(catalog_bytes)

    with pytest.raises(CatalogError, match="environment variable declaration"):
        load_catalog_snapshot(root, hashlib.sha256(catalog_bytes).hexdigest())


def test_manager_catalog_install_acquires_under_policy_and_exports_without_private_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_digest = "docker.io/pbeanlabs/example-mcp@sha256:" + "a" * 64
    app = CatalogApp(
        app_id="pblabs.example",
        mcp_name="io.github.p-bean-labs/example-mcp",
        version="1.2.3",
        source_class="official",
        repository_digest=repo_digest,
        platform="linux/amd64",
        needs_network=True,
        required_secrets=("API_KEY",),
        environment_variables=(CatalogEnvironmentVariable("API_KEY", True, True),),
        mounts=(CatalogMount("/data", "data", "read-write", True),),
        manifest_sha256="b" * 64,
        server_json_sha256="c" * 64,
        snapshot_sha256="d" * 64,
    )

    class Broker:
        def __init__(self) -> None:
            self.calls: list[tuple[str, str, dict]] = []

        def action(self, operation: str, server_id: str, data: dict) -> dict:
            self.calls.append((operation, server_id, data))
            if operation == "health":
                return {
                    "ready": True,
                    "minimumMountsSupported": True,
                    "appMountsSupported": True,
                    "catalogAcquisitionSupported": True,
                }
            if operation == "acquire":
                return {"repositoryDigest": repo_digest, "imageId": "sha256:" + "e" * 64, "platform": "linux/amd64"}
            if operation == "install":
                return {"running": True, "tools": ["example"]}
            if operation == "status":
                return {"registered": True}
            return {"running": True, "tools": ["example"]}

    index_root = tmp_path / "index"
    index_root.mkdir()
    monkeypatch.setattr(catalog_module, "SERVER_SCHEMA_SHA256", "f" * 64)
    monkeypatch.setattr("nanobot.mcp_docker.service.load_catalog_snapshot", lambda *_args: (app,))
    path = tmp_path / "config.json"
    config = load_config(path)
    section = config.tools.mcp_docker
    section.schema_version = 2
    section.installation_id = "12345678-1234-4234-8234-123456789abc"
    section.trusted_catalogs["pblabs"] = TrustedCatalogConfig(
        catalog_id="pblabs", root=str(index_root), snapshot_sha256="d" * 64,
        registered_at="2026-10-30T12:00:00Z",
    )
    save_config(config, path)
    broker = Broker()
    service = DockerMcpService(WebUISettingsConfig(path), broker)

    result = service.install_catalog_app(
        catalog_id="pblabs",
        app_id="pblabs.example",
        server_id="example",
        expected_revision=0,
        expected_confirmation="example/pblabs.example@1.2.3",
        mount_sources={"/data": str(tmp_path / "private-data")},
        environment={"API_KEY": DockerEnvValue(kind="secret", value="fixture-secret-value")},
        host_mounts=[],
    )

    current = load_config(path).tools.mcp_docker
    assert result["appId"] == "pblabs.example"
    assert [call[0] for call in broker.calls] == ["health", "acquire", "install"]
    assert current.app_releases["example"].repository_digest == repo_digest
    assert current.configurations["example"].app_mounts[0].target == "/data"
    exported = service.export_capabilities()
    export_text = json.dumps(exported)
    assert "fixture-secret-value" not in export_text
    assert str(tmp_path / "private-data") not in export_text
    assert "/data" in export_text
    assert (path.parent / "mcp-docker" / "capabilities.lock").is_file()


def test_trusted_catalog_registration_is_local_path_pinned_and_cas_guarded(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    index_root = tmp_path / "index"
    index_root.mkdir()
    monkeypatch.setenv("PERCIVAL_MCP_INDEX_ROOT", str(index_root))
    monkeypatch.setattr("nanobot.mcp_docker.service.load_catalog_snapshot", lambda *_args: ())

    class Broker:
        def action(self, operation: str, _server_id: str, _data: dict) -> dict:
            assert operation == "health"
            return {"ready": True}

    path = tmp_path / "config.json"
    config = load_config(path)
    section = config.tools.mcp_docker
    section.schema_version = 2
    section.installation_id = "12345678-1234-4234-8234-123456789abc"
    save_config(config, path)
    service = DockerMcpService(WebUISettingsConfig(path), Broker())

    with pytest.raises(DomainError, match="catalog confirmation"):
        service.register_catalog("pblabs", "a" * 64, 1, "wrong")
    result = service.register_catalog("pblabs", "a" * 64, 0, "pblabs")

    assert result == {"catalogId": "pblabs", "snapshotSha256": "a" * 64, "revision": 1, "appCount": 0}
    assert load_config(path).tools.mcp_docker.trusted_catalogs["pblabs"].root == str(index_root)
