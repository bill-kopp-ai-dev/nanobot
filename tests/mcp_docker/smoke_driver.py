"""Run inside the disposable gateway container in the F2 Docker smoke."""

from __future__ import annotations

import asyncio
import json
import os
import shutil
import sys
from pathlib import Path

from nanobot.agent.tools.mcp import MCPProvider
from nanobot.agent.tools.registry import ToolRegistry
from nanobot.config.loader import load_config
from nanobot.mcp_docker.client import BrokerClient, BrokerUnavailableError
from nanobot.mcp_docker.service import DockerMcpService, DomainError
from nanobot.webui.settings_services import WebUISettingsConfig

ROOT = Path.home() / ".nanobot"
BROKER = BrokerClient(ROOT / "mcp-docker" / "broker-token")
DOMAIN = DockerMcpService(WebUISettingsConfig(ROOT / "config.json"), BROKER)


def mutate(operation: str, server_id: str, **kwargs: object) -> dict:
    state = load_config(ROOT / "config.json").tools.mcp_docker
    current = state.servers.get(server_id)
    body = {"server_id": server_id, "expected_revision": state.revision,
            **({"expected_server_revision": current.revision} if current else {}), **kwargs}
    result = DOMAIN.act(operation, body)
    print(f"{server_id} {operation}: {result['state']}", flush=True)
    return result


async def call_and_gate(server_id: str, tool: str, arguments: dict) -> None:
    registry = ToolRegistry()
    provider = MCPProvider.from_config(load_config(ROOT / "config.json"), registry)
    await provider.connect()
    name = f"mcp_percival_docker_{server_id}_{tool}"
    wrapper = registry.get(name)
    assert wrapper is not None, (name, registry.tool_names, provider.runtime_status())
    result = await wrapper.execute(**arguments)
    assert not getattr(result, "is_error", False), result
    mutate("disable-tool", server_id, tool=tool)
    denied = await wrapper.execute(**arguments)  # previously cached wrapper
    assert getattr(denied, "is_error", False), denied
    mutate("enable-tool", server_id, tool=tool)
    restored = await wrapper.execute(**arguments)
    assert not getattr(restored, "is_error", False), restored
    mutate("deactivate", server_id)
    denied = await wrapper.execute(**arguments)
    assert getattr(denied, "is_error", False), denied
    mutate("activate", server_id)
    await provider.aclose()


def main() -> None:
    assert shutil.which("docker") is None
    assert not Path("/var/run/docker.sock").exists()
    weather, osm = sys.argv[1:3]
    weather_backup: Path | None = None
    for server_id, image, update, config, tool, args in (
        ("f2weather", os.environ["F2_WEATHER_ID"], os.environ["F2_WEATHER_OLD_ID"],
         {"persistent": True}, "weather_convert_time",
         {"datetime_str": "2026-10-07T12:00:00Z", "from_timezone": "UTC", "to_timezone": "America/Sao_Paulo"}),
        ("f2osm", os.environ["F2_OSM_ID"], os.environ["F2_OSM_OLD_ID"],
         {"env": {"USER_AGENT": {"kind": "plain", "value": "Percival-F2-test (local)"},
                  "FROM_HEADER": {"kind": "plain", "value": "local@example.invalid"}}},
         "osm_get_health", {}),
    ):
        assert (weather if server_id == "f2weather" else osm) == image
        mutate("install", server_id, source={"type": "local-image", "reference": image}, configuration=config)
        state = DOMAIN.list()["servers"][server_id]
        assert len(state["tools"]) >= (9 if server_id == "f2weather" else 30)
        asyncio.run(call_and_gate(server_id, tool, args))
        mutate("configure", server_id, configuration={**config, "mounts": ["/etc"]})
        mutate("configure", server_id, configuration=config)
        mutate("restart", server_id)
        mutate("update-image", server_id, source={"type": "local-image", "reference": update})
        assert DOMAIN.list()["servers"][server_id]["tools"]
        previous = load_config(ROOT / "config.json").tools.mcp_docker.servers[server_id].source.reference
        try:
            mutate("update-image", server_id, source={"type": "local-image", "reference": os.environ["F2_FAIL_IMAGE_ID"]})
        except BrokerUnavailableError:
            pass
        else:
            raise AssertionError("non-MCP image update unexpectedly succeeded")
        assert load_config(ROOT / "config.json").tools.mcp_docker.servers[server_id].source.reference == previous
        assert DOMAIN.list()["servers"][server_id]["tools"]
        for blocked in ("/run", "/var/run", "/var/lib/docker", os.environ["F2_STATE_HOST_PATH"]):
            before = load_config(ROOT / "config.json").tools.mcp_docker.servers[server_id].revision
            state_revision = load_config(ROOT / "config.json").tools.mcp_docker.revision
            try:
                mutate("configure", server_id, configuration={**config, "mounts": [blocked]})
            except BrokerUnavailableError:
                pass
            else:
                raise AssertionError(f"protected mount was accepted: {blocked}")
            current = load_config(ROOT / "config.json").tools.mcp_docker
            assert current.revision == state_revision and current.servers[server_id].revision == before
        if server_id == "f2weather":
            mutate("stop", server_id)
            assert DOMAIN.list()["servers"][server_id]["state"] == "stopped-persistent"
            mutate("start", server_id)
        else:
            try:
                mutate("stop", server_id)
            except DomainError as exc:
                assert exc.status == 409
            else:
                raise AssertionError("nonpersistent stop accepted")
        try:
            mutate("exclude", server_id, expected_confirmation="wrong")
        except DomainError as exc:
            assert exc.status == 400
        else:
            raise AssertionError("wrong exclusion confirmation accepted")
        excluded = mutate("exclude", server_id, expected_confirmation=server_id)
        if server_id == "f2weather":
            weather_backup = Path(excluded["backup"])
        assert server_id not in DOMAIN.list()["servers"]
    assert weather_backup is not None
    section = load_config(ROOT / "config.json").tools.mcp_docker
    DOMAIN.restore_backup(weather_backup, section.revision, "f2weather")
    section = load_config(ROOT / "config.json").tools.mcp_docker
    restored = section.servers["f2weather"]
    DOMAIN._write_transition("f2weather", {
        "schemaVersion": 1,
        "server_id": "f2weather",
        "action": "restart",
        "state": "preparing",
        "base_revision": section.revision,
        "correlation_id": "d" * 32,
        "before": {
            "server": restored.model_dump(mode="json", by_alias=True),
            "configuration": section.configurations["f2weather"].model_dump(mode="json", by_alias=True),
        },
    })
    DOMAIN.list()
    transition = json.loads((ROOT / "mcp-docker/transitions/f2weather.json").read_text())
    assert transition["state"] == "committed" and transition["recovery"] == "rolled-back-to-config"
    assert DOMAIN.list()["servers"]["f2weather"]["dockerObservation"] == "running"
    mutate("exclude", "f2weather", expected_confirmation="f2weather")
    assert len(list((ROOT / "mcp-docker/backups").iterdir())) == 7
    assert "secret" not in (ROOT / "mcp-docker/audit.jsonl").read_text()
    print("F5 smoke: two real MCP fixtures, eight families, backup restore, interrupted-transition recovery and socket separation", flush=True)


if __name__ == "__main__":
    main()
