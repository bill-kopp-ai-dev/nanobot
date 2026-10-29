"""Verify the Notes consumer's explicit vault profile in disposable DinD."""

from __future__ import annotations

import asyncio
import os
from pathlib import Path

from nanobot.agent.tools.mcp import MCPProvider
from nanobot.agent.tools.registry import ToolRegistry
from nanobot.config.loader import load_config
from nanobot.mcp_docker.client import BrokerClient, BrokerRejectedError
from nanobot.mcp_docker.service import DockerMcpService
from nanobot.webui.settings_services import WebUISettingsConfig

ROOT = Path.home() / ".nanobot"
SERVER_ID = "notesmanaged"
VAULT_HOST_PATH = "/notes-profile-scratch/notes-vault"
NOTE_PATH = "stage2-notes-fixture.md"
NOTE_MARKER = "S2-NB-X01 synthetic consumer profile"


def service_for() -> DockerMcpService:
    return DockerMcpService(
        WebUISettingsConfig(ROOT / "config.json"),
        BrokerClient(ROOT / "mcp-docker" / "broker-token"),
    )


def install() -> None:
    state = load_config(ROOT / "config.json").tools.mcp_docker
    host_vault = f"/host{VAULT_HOST_PATH}"
    service_for().act("install", {
        "server_id": SERVER_ID,
        "expected_revision": state.revision,
        "source": {"type": "local-image", "reference": os.environ["NOTES_IMAGE_ID"]},
        "configuration": {
            "mounts": [VAULT_HOST_PATH],
            "network": "none",
            "env": {"PERCIVAL_NOTES_VAULT_PATH": {"kind": "plain", "value": host_vault}},
        },
    })
    saved = load_config(ROOT / "config.json").tools.mcp_docker.configurations[SERVER_ID]
    assert saved.mounts == [VAULT_HOST_PATH]
    assert saved.env["PERCIVAL_NOTES_VAULT_PATH"].value == host_vault


async def verify_consumer() -> None:
    registry = ToolRegistry()
    provider = MCPProvider.from_config(load_config(ROOT / "config.json"), registry)
    try:
        await provider.connect()
        prefix = f"mcp_percival_docker_{SERVER_ID}_"
        write = registry.get(prefix + "notes_write")
        read = registry.get(prefix + "notes_read")
        resource = registry.get(prefix + "resource_okf-v0_2-guide")
        create_prompt = registry.get(prefix + "prompt_notes_create_concept")
        research_prompt = registry.get(prefix + "prompt_notes_research_and_link")
        assert write is not None and read is not None and resource is not None
        assert create_prompt is not None and research_prompt is not None, (
            registry.tool_names, provider.runtime_status(),
        )
        server_resources, create_guide, research_guide = await asyncio.gather(
            resource.execute(),
            create_prompt.execute(topic="synthetic test"),
            research_prompt.execute(topic="synthetic test"),
        )
        assert "OKF" in server_resources
        assert "synthetic test" in create_guide
        assert "synthetic test" in research_guide
        written = await write.execute(
            path=NOTE_PATH,
            yaml_frontmatter="---\ntype: Stage2Fixture\n---",
            markdown_content=NOTE_MARKER,
        )
        assert not getattr(written, "is_error", False), written
        result = await read.execute(path=NOTE_PATH)
        assert not getattr(result, "is_error", False), result
        print("NOTES_EXPLICIT_VAULT_PROFILE_OK", flush=True)
    finally:
        await provider.aclose()


def verify_protected_path_rejected() -> None:
    config = load_config(ROOT / "config.json")
    section = config.tools.mcp_docker
    current = section.servers[SERVER_ID]
    host = section.configurations[SERVER_ID].model_dump(mode="json")
    host["mounts"] = ["/var/lib/docker"]
    try:
        service_for().act("configure", {
            "server_id": SERVER_ID,
            "expected_revision": section.revision,
            "expected_server_revision": current.revision,
            "configuration": host,
        })
    except BrokerRejectedError as exc:
        assert exc.status_code == 400
    else:
        raise AssertionError("Docker data-root mount was not rejected")
    final = load_config(ROOT / "config.json").tools.mcp_docker
    assert final.configurations[SERVER_ID].mounts == [VAULT_HOST_PATH]
    assert final.configurations[SERVER_ID].env["PERCIVAL_NOTES_VAULT_PATH"].value == f"/host{VAULT_HOST_PATH}"
    print("NOTES_PROTECTED_PATH_REJECTED_WITH_PROFILE_PRESERVED", flush=True)


def cleanup() -> None:
    config = load_config(ROOT / "config.json")
    server = config.tools.mcp_docker.servers.get(SERVER_ID)
    if server is None:
        return
    service_for().act("exclude", {
        "server_id": SERVER_ID,
        "expected_revision": config.tools.mcp_docker.revision,
        "expected_server_revision": server.revision,
        "expected_confirmation": SERVER_ID,
    })
    print("NOTES_FIXTURE_CLEANED", flush=True)


def main() -> None:
    if os.environ.get("PERCIVAL_BROKER_TOKEN_GID") not in {"1000", "65532"}:
        raise SystemExit("expected a synthetic broker-token group")
    if os.environ.get("NOTES_PROFILE_ACTION") == "cleanup":
        cleanup()
        return
    if SERVER_ID in load_config(ROOT / "config.json").tools.mcp_docker.servers:
        cleanup()
    install()
    try:
        asyncio.run(verify_consumer())
        verify_protected_path_rejected()
    finally:
        cleanup()


if __name__ == "__main__":
    main()
