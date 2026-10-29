"""Gateway-side driver copied into a disposable DinD gateway for A-012."""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

from nanobot.agent.tools.mcp import MCPProvider
from nanobot.agent.tools.registry import ToolRegistry
from nanobot.config.loader import load_config
from nanobot.mcp_docker.client import BrokerClient
from nanobot.mcp_docker.service import DockerMcpService
from nanobot.webui.settings_services import WebUISettingsConfig

ROOT = Path.home() / ".nanobot"
SERVER_ID = "a012fixture"


async def run_call(*, seconds: float, marker: bool) -> None:
    config_path = ROOT / "config.json"
    registry = ToolRegistry()
    provider = MCPProvider.from_config(load_config(config_path), registry)
    try:
        await provider.connect()
        wrapper = registry.get(f"mcp_percival_docker_{SERVER_ID}_delay")
        assert wrapper is not None, (registry.tool_names, provider.runtime_status())
        if marker:
            print("A012_CALL_STARTED", flush=True)
        result = await wrapper.execute(seconds=seconds)
        assert not getattr(result, "is_error", False), result
        print("A012_CALL_COMPLETED", flush=True)
    finally:
        await provider.aclose()


def install() -> None:
    state = load_config(ROOT / "config.json").tools.mcp_docker
    image_id = os.environ["A012_FIXTURE_IMAGE_ID"]
    host_marker_dir = os.environ["A012_HOST_MARKER_DIR"]
    marker_path = f"/host{host_marker_dir}/call-started"
    service = DockerMcpService(
        WebUISettingsConfig(ROOT / "config.json"),
        BrokerClient(ROOT / "mcp-docker" / "broker-token"),
    )
    service.act("install", {
        "server_id": SERVER_ID,
        "expected_revision": state.revision,
        "source": {"type": "local-image", "reference": image_id},
        "configuration": {
            "mounts": [host_marker_dir],
            "network": "none",
            "env": {"A012_MARKER": {"kind": "plain", "value": marker_path}},
        },
    })
    print("A012_FIXTURE_INSTALLED", flush=True)


def cleanup() -> None:
    config = load_config(ROOT / "config.json")
    server = config.tools.mcp_docker.servers.get(SERVER_ID)
    if server is None:
        return
    service = DockerMcpService(
        WebUISettingsConfig(ROOT / "config.json"),
        BrokerClient(ROOT / "mcp-docker" / "broker-token"),
    )
    service.act("exclude", {
        "server_id": SERVER_ID,
        "expected_revision": config.tools.mcp_docker.revision,
        "expected_server_revision": server.revision,
        "expected_confirmation": SERVER_ID,
    })
    print("A012_FIXTURE_CLEANED", flush=True)


def main() -> None:
    if sys.argv[1] == "install":
        install()
        asyncio.run(run_call(seconds=4, marker=True))
    elif sys.argv[1] == "recover":
        asyncio.run(run_call(seconds=0.1, marker=False))
    elif sys.argv[1] == "cleanup":
        cleanup()
    else:
        raise SystemExit("expected install or recover")


if __name__ == "__main__":
    main()
