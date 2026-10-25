from __future__ import annotations

import json
from pathlib import Path

import pytest

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


def test_compose_reference_reader_includes_runtime_override(tmp_path: Path) -> None:
    project = tmp_path / "nanobot"
    project.mkdir()
    override = project / "docker-compose.engine29-override.yml"
    override.write_text("services:\n  broker:\n    image: percival-mcp-broker:local\n", encoding="utf-8")
    assert inventory._project_references(tmp_path) == [{
        "kind": "compose-image", "path": str(override), "line": "3",
        "reference": "percival-mcp-broker:local",
    }]


def test_inventory_distinguishes_managers_sharing_an_image_without_name_inference(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    image_id = "sha256:" + "a" * 64
    container_ids = ["b" * 64, "c" * 64]
    label_sets = [
        {"percival.mcp-docker.owner": "percival",
         "percival.mcp-docker.managed-by": "percival-broker",
         "percival.mcp-docker.server-id": "osm",
         "percival.mcp-docker.instance-id": "broker-instance"},
        {"io.positronic.managed": "mcp", "io.positronic.run": "positronic-run",
         "io.positronic.server": "positronic-server", "io.positronic.server-name": "osm",
         "unrelated.secret": "do-not-emit"},
    ]
    containers = {
        cid: inventory.SEPARATOR.join([
            cid, f"/random_{index}", image_id, image_id, "2026-10-24T00:00:00Z",
            "running", "none", json.dumps(labels),
            json.dumps(["CMD-SHELL", "test -f /ready || exit 1"]), "{}", "[]",
            "true", "false", "false", "true",
        ])
        for index, (cid, labels) in enumerate(zip(container_ids, label_sets, strict=True))
    }
    image = inventory.SEPARATOR.join([
        image_id, "[]", "[]", "2026-10-24T00:00:00Z", "linux", "amd64",
        json.dumps({"io.percival.build.worktree": "dirty",
                    "io.percival.build.source-diff-sha256": "d" * 64,
                    "unrelated.secret": "do-not-emit"}), "null", "{}",
    ])

    def docker(args: list[str], *, docker_bin: str = "docker") -> str:
        if args[:2] == ["container", "ls"]:
            return "\n".join(container_ids)
        if args[:2] == ["image", "ls"]:
            return image_id
        assert args[:3] in (["container", "inspect", "--format"], ["image", "inspect", "--format"])
        return containers[args[-1]] if args[0] == "container" else image

    monkeypatch.setattr(inventory, "_docker", docker)
    result = inventory.collect_inventory(home=tmp_path, projects_root=tmp_path)
    assert len(result["images"]) == 1
    assert len(result["containers"]) == 2
    assert result["containers"][1]["labels"]["io.positronic.run"] == "positronic-run"
    assert result["images"][0]["labels"]["io.percival.build.worktree"] == "dirty"
    assert "do-not-emit" not in json.dumps(result)
    monkeypatch.setattr(inventory, "collect_inventory", lambda **kwargs: result)
    monkeypatch.setattr("sys.argv", ["inventory", "--format", "markdown"])
    assert inventory.main() == 0
    markdown = capsys.readouterr().out
    assert "| positronic | positronic | positronic-server | positronic-run |" in markdown
    assert "| percival | percival-broker | osm | broker-instance |" in markdown
    assert "| True/False/True |" in markdown
    assert "test -f /ready \\|\\| exit 1" in markdown
    rows = [line for line in markdown.splitlines() if line.startswith("| random_")]
    assert len(rows) == 2 and all(row.replace("\\|", "").count("|") == 15 for row in rows)


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
