"""Reachable F2 configuration, authorization and domain contracts."""

from __future__ import annotations

import asyncio
import json
import stat
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from pydantic import ValidationError

from nanobot.agent.tools.mcp import MCPToolWrapper, _configured_servers
from nanobot.config.loader import load_config, resolve_config_env_vars, save_config
from nanobot.config.mcp_docker import (
    REDACTED_SECRET,
    DockerImageSource,
    DockerServer,
    McpDockerConfig,
)
from nanobot.config.schema import Config, MCPServerConfig
from nanobot.mcp_docker.client import BrokerUnavailableError
from nanobot.mcp_docker.operator import OperatorCredential
from nanobot.mcp_docker.service import DockerMcpService, DomainError
from nanobot.webui.settings_services import WebUISettingsConfig

IMAGE = "sha256:" + "a" * 64
NEXT_IMAGE = "sha256:" + "b" * 64


class FakeBroker:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, dict]] = []
        self.fail = False

    def action(self, operation: str, server_id: str, data: dict) -> dict:
        self.calls.append((operation, server_id, data))
        if self.fail:
            raise BrokerUnavailableError("offline")
        if operation == "observe":
            return {"dockerObservation": "running", "mcpConnectivity": "connected", "tools": ["second"]}
        return {"running": operation not in {"stop", "deactivate", "exclude"}, "tools": ["second"]}


def payload(server_id: str, revision: int, **extra: object) -> dict:
    return {"server_id": server_id, "expected_revision": revision, **extra}


def test_config_schema_rejects_unsupported_image_version_and_missing_configuration(tmp_path: Path) -> None:
    with pytest.raises(ValidationError):
        DockerImageSource(type="local-image", reference="ubuntu:latest")
    with pytest.raises(ValidationError):
        DockerImageSource(type="pinned-image", reference=IMAGE)
    with pytest.raises(ValidationError):
        McpDockerConfig(schema_version=2)
    with pytest.raises(ValidationError):
        McpDockerConfig(servers={"alpha": {"server_id": "alpha", "source": {"type": "local-image", "reference": IMAGE}}})
    config = load_config(tmp_path / "config.json")
    save_config(config, tmp_path / "config.json")
    assert stat.S_IMODE((tmp_path / "config.json").stat().st_mode) == 0o600


def test_secret_roundtrip_reference_and_rollback(tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    broker = FakeBroker()
    domain = DockerMcpService(WebUISettingsConfig(path), broker)
    host = {"env": {"TOKEN": {"kind": "secret", "value": "abcdefghijklm"},
                    "FROM_BROKER": {"kind": "reference", "value": "${BROKER_ENV}"}}}
    result = domain.act("install", payload("alpha", 0, source={"type": "local-image", "reference": IMAGE}, configuration=host))
    assert result["revision"] == 1
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    read = domain.list()
    assert read["servers"]["alpha"]["configuration"]["env"]["TOKEN"]["value"] == REDACTED_SECRET
    assert read["servers"]["alpha"]["configuration"]["env"]["TOKEN"]["maskHint"] == "abcd••••jklm"
    assert "abcdefghijklm" not in json.dumps(read)
    assert read["servers"]["alpha"]["dockerObservation"] == "running"
    assert read["servers"]["alpha"]["mcpConnectivity"] == "connected"
    assert read["servers"]["alpha"]["tools"] == ["second"]
    assert load_config(path).tools.mcp_docker.configurations["alpha"].env["TOKEN"].value == "abcdefghijklm"
    resolve_config_env_vars(load_config(path))  # broker reference is not resolved in the gateway
    with pytest.raises(DomainError) as invalid:
        domain.act("configure", payload("alpha", 1, expected_server_revision=0,
                                        configuration={"env": {"NEW": {"kind": "secret", "value": REDACTED_SECRET}}}))
    assert invalid.value.status == 400
    host["env"]["TOKEN"]["value"] = REDACTED_SECRET
    domain.act("configure", payload("alpha", 1, expected_server_revision=0, configuration=host))
    assert load_config(path).tools.mcp_docker.configurations["alpha"].env["TOKEN"].value == "abcdefghijklm"
    with pytest.raises(DomainError) as conflict:
        domain.act("disable-tool", payload("alpha", 1, expected_server_revision=0, tool="first"))
    assert conflict.value.status == 409
    broker.fail = True
    with pytest.raises(BrokerUnavailableError):
        domain.act("update-image", payload("alpha", 2, expected_server_revision=1,
                                           source={"type": "local-image", "reference": NEXT_IMAGE}))
    assert load_config(path).tools.mcp_docker.revision == 2
    assert load_config(path).tools.mcp_docker.servers["alpha"].source.reference == IMAGE
    audit = (tmp_path / "mcp-docker" / "audit.jsonl").read_text()
    assert "abcdefghijklm" not in audit
    assert '"phase": "failed"' in audit
    assert stat.S_IMODE((tmp_path / "mcp-docker" / "audit.jsonl").stat().st_mode) == 0o600


def test_eight_families_and_cas(tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    broker = FakeBroker()
    domain = DockerMcpService(WebUISettingsConfig(path), broker)
    revision = 0
    server_revision = None

    def act(name: str, **extra: object) -> dict:
        nonlocal revision, server_revision
        value = domain.act(name, payload("weather", revision, **(
            {"expected_server_revision": server_revision} if server_revision is not None else {}
        ), **extra))
        revision = value["revision"]
        if name != "exclude":
            server_revision = domain.config.load().tools.mcp_docker.servers["weather"].revision
        return value

    act("install", source={"type": "local-image", "reference": IMAGE}, configuration={"persistent": True})
    act("disable-tool", tool="first")
    assert domain.config.load().tools.mcp_docker.servers["weather"].tools_disabled == ["first"]
    act("update-image", source={"type": "local-image", "reference": NEXT_IMAGE})
    assert domain.config.load().tools.mcp_docker.servers["weather"].tools_disabled == []
    act("enable-tool", tool="first")
    act("configure", configuration={"persistent": True, "mounts": ["/srv/data"]})
    act("restart")
    act("stop")
    assert domain.list()["servers"]["weather"]["state"] == "stopped-persistent"
    act("start")
    act("deactivate")
    with pytest.raises(DomainError):
        act("start")
    act("activate")
    with pytest.raises(DomainError):
        act("exclude", expected_confirmation="not-weather")
    backup_dir = act("exclude", expected_confirmation="weather")["backup"]
    assert domain.list()["servers"] == {}
    assert len(list((tmp_path / "mcp-docker" / "backups").iterdir())) == 2
    restored = domain.restore_backup(Path(str(backup_dir)), revision)
    assert restored["state"] == "running"
    assert domain.list()["servers"]["weather"]["source"]["reference"] == NEXT_IMAGE
    with pytest.raises(DomainError) as overwrite:
        domain.restore_backup(Path(str(backup_dir)), revision + 1)
    assert overwrite.value.status == 409
    with pytest.raises(DomainError) as stale:
        domain.act("install", payload("weather", 0, source={"type": "local-image", "reference": IMAGE}, configuration={}))
    assert stale.value.status == 409


def test_competing_writers_and_separate_operator_password(tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    stale = load_config(path)
    domain = DockerMcpService(WebUISettingsConfig(path), FakeBroker())
    request = payload("alpha", 0, source={"type": "local-image", "reference": IMAGE}, configuration={})
    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda _: _outcome(domain, request), range(2)))
    assert sorted(results) == ["committed", "conflict"]
    with pytest.raises(ValueError, match="CAS conflict"):
        save_config(stale, path)
    assert "alpha" in load_config(path).tools.mcp_docker.servers
    credential = OperatorCredential(tmp_path)
    credential.set_password("first password")
    assert credential.verify("first password")
    with pytest.raises(PermissionError):
        credential.set_password("unauthorized")
    credential.set_password("second password", current_password="first password")
    assert credential.verify("second password") and not credential.verify("first password")
    assert stat.S_IMODE(credential.path.stat().st_mode) == 0o600
    assert "password" not in credential.path.read_text()


def test_managed_server_mapping_and_wrapper_rechecks_gate(tmp_path: Path) -> None:
    config = Config()
    path = tmp_path / "config.json"
    config.bind_source_path(path)
    server_id = "weather"
    config.tools.mcp_docker.servers[server_id] = DockerServer(
        server_id=server_id,
        source={"type": "local-image", "reference": IMAGE},
        state="running", tools=["forecast", "time"], tools_disabled=["time"],
    )
    config.tools.mcp_docker.configurations[server_id] = {}
    config.tools.mcp_servers["generic"] = MCPServerConfig(type="stdio", command="generic")
    token_path = tmp_path / "mcp-docker" / "broker-token"
    token_path.parent.mkdir(mode=0o700)
    token_path.write_text("t" * 64)
    token_path.chmod(0o600)
    servers = _configured_servers(config)
    managed_name = "percival_docker_weather"
    assert managed_name in servers and "generic" in servers
    assert servers[managed_name].enabled_tools == ["forecast"]
    assert servers[managed_name].headers["Authorization"] == "Bearer " + "t" * 64

    allowed = True

    class Session:
        calls = 0

        async def call_tool(self, _name: str, *, arguments: dict) -> object:
            self.calls += 1
            from mcp.types import TextContent
            return type("Result", (), {"content": [TextContent(type="text", text="ok")], "isError": False})()

    session = Session()
    wrapper = MCPToolWrapper(session, managed_name, type("ToolDef", (), {
        "name": "forecast", "description": "", "inputSchema": {"type": "object", "properties": {}}
    })())
    wrapper.set_managed_gate(lambda: allowed)
    assert "ok" in asyncio.run(wrapper.execute())
    allowed = False
    denied = asyncio.run(wrapper.execute())
    assert getattr(denied, "is_error", False)
    assert session.calls == 1


def test_managed_wrapper_gate_rejects_disabled_tool_after_runtime_change(tmp_path: Path) -> None:
    """The per-call gate reads config on each invocation, so a disable-tool
    issued after wrapper registration takes effect without a reconnect."""
    config = Config()
    path = tmp_path / "config.json"
    config.bind_source_path(path)
    server_id = "weather"
    config.tools.mcp_docker.servers[server_id] = DockerServer(
        server_id=server_id,
        source={"type": "local-image", "reference": IMAGE},
        state="running", tools=["forecast", "time"], tools_disabled=[],
    )
    config.tools.mcp_docker.configurations[server_id] = {}
    token_path = tmp_path / "mcp-docker" / "broker-token"
    token_path.parent.mkdir(mode=0o700)
    token_path.write_text("t" * 64)
    token_path.chmod(0o600)
    save_config(config, path)

    expected_source = config.tools.mcp_docker.servers[server_id].source.reference
    config_path = path

    def permitted(raw_name: str = "forecast", source: str = expected_source) -> bool:
        section = load_config(config_path).tools.mcp_docker
        current = section.servers.get(server_id)
        return bool(
            current is not None
            and current.active
            and current.state == "running"
            and current.source.reference == source
            and raw_name in current.tools
            and raw_name not in current.tools_disabled
        )

    class Session:
        calls = 0

        async def call_tool(self, _name: str, *, arguments: dict) -> object:
            self.calls += 1
            from mcp.types import TextContent
            return type("Result", (), {"content": [TextContent(type="text", text="ok")], "isError": False})()

    wrapper = MCPToolWrapper(session=Session(), server_name="percival_docker_weather", tool_def=type(
        "ToolDef", (), {"name": "forecast", "description": "", "inputSchema": {"type": "object", "properties": {}}}
    )())
    wrapper.set_managed_gate(permitted)
    assert "ok" in asyncio.run(wrapper.execute())

    # Disable the tool in config; the next call must be rejected without
    # re-registering the wrapper, proving the gate reads the live config.
    updated = load_config(path)
    updated.tools.mcp_docker.servers[server_id].tools_disabled = ["forecast"]
    updated.tools.mcp_docker.revision += 1
    save_config(updated, path)
    denied = asyncio.run(wrapper.execute())
    assert getattr(denied, "is_error", False)


def _outcome(domain: DockerMcpService, request: dict) -> str:
    try:
        domain.act("install", request)
        return "committed"
    except DomainError as exc:
        assert exc.status == 409
        return "conflict"


def test_cas_refuses_save_when_disk_revision_is_ahead(tmp_path: Path) -> None:
    """A config object whose revision is behind the disk must not be allowed
    to overwrite the Docker MCP section."""
    path = tmp_path / "config.json"
    domain = DockerMcpService(WebUISettingsConfig(path), FakeBroker())
    domain.act("install", payload("alpha", 0, source={"type": "local-image", "reference": IMAGE}, configuration={}))
    disk = load_config(path)
    stale = load_config(path)
    stale.tools.mcp_docker.revision = disk.tools.mcp_docker.revision - 1
    assert stale.tools.mcp_docker.revision != disk.tools.mcp_docker.revision
    with pytest.raises(ValueError, match="CAS conflict"):
        save_config(stale, path)
    assert load_config(path).tools.mcp_docker.revision == disk.tools.mcp_docker.revision
    assert "alpha" in load_config(path).tools.mcp_docker.servers
