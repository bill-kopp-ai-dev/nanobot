from __future__ import annotations

import json
from pathlib import Path

from nanobot.mcp_docker import inventory


def test_docker_inspect_templates_never_request_environment_values() -> None:
    assert ".Config.Env" not in inventory.IMAGE_TEMPLATE
    assert ".Config.Env" not in inventory.CONTAINER_TEMPLATE


def test_container_report_selects_standard_labels_and_redacts_secret_mount_paths() -> None:
    fields = [
        "c" * 64,
        "/random_name",
        "percival-weather:0.9.0-1234567",
        "sha256:" + "a" * 64,
        "2026-10-09T00:00:00Z",
        "running",
        "none",
        json.dumps({
            "percival.mcp-docker.owner": "percival",
            "percival.mcp-docker.managed-by": "percival-broker",
            "percival.mcp-docker.server-id": "weather",
            "percival.mcp-docker.instance-id": "instance-1",
            "unrelated.secret": "must-not-appear",
        }),
        "null",
        "{}",
        json.dumps([
            {"Type": "bind", "Source": "/home/user/.nanobot/secrets/token", "Destination": "/run/secrets/token", "RW": False},
            {"Type": "bind", "Source": "/home/user/calendar", "Destination": "/data", "RW": True},
        ]),
        "false",
        "false",
        "false",
        "true",
    ]
    parsed = inventory._parse_container(inventory.SEPARATOR.join(fields))
    assert parsed is not None
    assert parsed["name"] == "random_name"
    assert parsed["labels"] == {
        "percival.mcp-docker.owner": "percival",
        "percival.mcp-docker.managed-by": "percival-broker",
        "percival.mcp-docker.server-id": "weather",
        "percival.mcp-docker.instance-id": "instance-1",
    }
    assert parsed["mounts"][0]["source"] == "[REDACTED]"
    assert parsed["mounts"][0]["destination"] == "[REDACTED]"
    assert parsed["mounts"][1]["source"] == "/home/user/calendar"


def test_config_reference_extractor_emits_image_pins_not_secret_values(tmp_path: Path) -> None:
    config = tmp_path / "config.json"
    digest = "sha256:" + "b" * 64
    config.write_text(json.dumps({
        "tools": {"mcpDocker": {"servers": {
            "weather": {"server_id": "weather", "source": {"type": "local-image", "reference": digest}},
        }}},
        "providers": {"api_key": "secret-value-that-must-not-be-emitted"},
    }), encoding="utf-8")

    result = inventory._config_references(config)
    assert result == [{
        "kind": "config-image-reference",
        "path": str(config),
        "pointer": "/tools/mcpDocker/servers/weather/source/reference",
        "serverId": "weather",
        "reference": digest,
    }]
    assert "secret-value-that-must-not-be-emitted" not in json.dumps(result)


def test_compose_reference_reader_lists_declared_image_without_expanding_env(tmp_path: Path) -> None:
    project = tmp_path / "percival-example"
    project.mkdir()
    compose = project / "docker-compose.yml"
    compose.write_text("services:\n  server:\n    image: ${IMAGE:-percival-example:dev}\n", encoding="utf-8")
    assert inventory._project_references(tmp_path) == [{
        "kind": "compose-image",
        "path": str(compose),
        "line": "3",
        "reference": "${IMAGE:-percival-example:dev}",
    }]


def test_config_reference_extractor_propagates_server_id_into_list_items(tmp_path: Path) -> None:
    """A reference nested inside a list must inherit the surrounding server id,
    not lose it by falling back to the empty string. This protects the
    Positronic registry shape, which stores servers as a list under ``servers``."""
    digest = "sha256:" + "c" * 64
    config = tmp_path / "registry.json"
    config.write_text(json.dumps({
        "servers": [
            {"id": "agentmail", "source": {"imageId": digest}},
            {"id": "weather", "source": {"imageId": "sha256:" + "d" * 64}},
        ],
    }), encoding="utf-8")
    references = inventory._config_references(config)
    assert references == [
        {"kind": "config-image-reference", "path": str(config),
         "pointer": "/servers/0/source/imageId", "serverId": "agentmail", "reference": digest},
        {"kind": "config-image-reference", "path": str(config),
         "pointer": "/servers/1/source/imageId", "serverId": "weather",
         "reference": "sha256:" + "d" * 64},
    ]


def test_config_reference_extractor_does_not_match_unrelated_env_config(tmp_path: Path) -> None:
    config = tmp_path / "config.json"
    config.write_text(json.dumps({
        "tools": {"mcpDocker": {"servers": {
            "agentmail": {"server_id": "agentmail", "source": {"type": "local-image",
                                                                "reference": "sha256:" + "e" * 64}},
        }}},
        "providers": {"openai": {"api_key": "sk-fake-secret-value", "model": "gpt-4o"}},
    }), encoding="utf-8")
    references = inventory._config_references(config)
    assert len(references) == 1
    assert references[0]["serverId"] == "agentmail"
    assert "sk-fake-secret-value" not in json.dumps(references)
