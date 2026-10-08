"""WebSocket authorization boundary for Docker MCP settings."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from websockets.datastructures import Headers

from nanobot.config.loader import load_config, save_config
from nanobot.config.mcp_docker import DockerServer
from nanobot.mcp_docker.client import BrokerRejectedError
from nanobot.webui.http_utils import http_json_response
from nanobot.webui.settings_routes import WebUISettingsRouter
from nanobot.webui.settings_services import WebUISettingsServices


def router(path: Path, *, authorized: bool = True) -> WebUISettingsRouter:
    return WebUISettingsRouter(
        settings=WebUISettingsServices.create(path), bus=SimpleNamespace(),
        logger=SimpleNamespace(exception=lambda *_args: None),
        check_api_token=lambda _request: authorized,
        parse_query=lambda _path: {}, json_response=http_json_response,
        error_response=lambda code, message: http_json_response({"error": message}, status=code),
        runtime_surface="browser", runtime_capabilities={},
    )


def request(action: str, values: dict | None = None, *, host: str = "127.0.0.1:8765", forwarded: str = "") -> SimpleNamespace:
    headers = Headers([("Host", host), *( [("X-Forwarded-For", forwarded)] if forwarded else [])])
    result = SimpleNamespace(path=f"/api/settings/mcp-docker/{action}", headers=headers)
    if values is not None:
        result._nanobot_webui_mutation_request = True
        result._nanobot_webui_mutation_payload = values
    return result


@pytest.mark.asyncio
async def test_operator_bootstrap_is_loopback_only_and_returns_status(tmp_path: Path) -> None:
    settings = router(tmp_path / "config.json")
    local = SimpleNamespace(remote_address=("127.0.0.1", 4567))
    remote = SimpleNamespace(remote_address=("198.51.100.2", 4567))
    path = "/api/settings/mcp-docker/operator-bootstrap"
    assert (await settings.dispatch(remote, request("operator-bootstrap"), path)).status_code == 403
    assert (await settings.dispatch(local, request("operator-bootstrap", forwarded="198.51.100.2"), path)).status_code == 403
    response = await settings.dispatch(local, request("operator-bootstrap"), path)
    assert json.loads(response.body) == {"configured": False}


@pytest.mark.asyncio
async def test_mutations_require_webui_and_operator_auth_for_each_call(tmp_path: Path) -> None:
    settings = router(tmp_path / "config.json")
    local = SimpleNamespace(remote_address=("127.0.0.1", 4567))
    remote = SimpleNamespace(remote_address=("198.51.100.2", 4567))
    install = "/api/settings/mcp-docker/install"
    assert (await settings.dispatch(local, request("install"), install)).status_code == 405
    assert (await router(tmp_path / "config.json", authorized=False).dispatch(
        local, request("operator-setup", {"operator_admin": "correct"}), "/api/settings/mcp-docker/operator-setup"
    )).status_code == 401
    setup = await settings.dispatch(local, request("operator-setup", {"operator_admin": "correct"}),
                                    "/api/settings/mcp-docker/operator-setup")
    assert setup.status_code == 200
    assert (await settings.dispatch(local, request("operator-setup", {"operator_admin": "again"}),
                                    "/api/settings/mcp-docker/operator-setup")).status_code == 409
    assert (await settings.dispatch(local, request("install", {"server_id": "a"}), install)).status_code == 401
    assert (await settings.dispatch(local, request("install", {"operator_admin": "wrong"}), install)).status_code == 401
    assert (await settings.dispatch(remote, request("install", {"operator_admin": "correct"}), install)).status_code == 403
    assert (await settings.dispatch(local, request("install", {"operator_admin": "correct", "server_id": "a",
                                                               "expected_revision": 0}), install)).status_code == 400
    valid = {"operator_admin": "correct", "server_id": "a", "expected_revision": 0,
             "source": {"type": "local-image", "reference": "sha256:" + "a" * 64},
             "configuration": {}}
    assert (await settings.dispatch(local, request("install", valid), install)).status_code == 503
    assert not (tmp_path / "config.json").exists()  # no publication after broker failure
    assert (await settings.dispatch(local, request("operator-rotate", {"operator_admin": "correct",
                                                                    "new_password": "new-password"}),
                                    "/api/settings/mcp-docker/operator-rotate")).status_code == 200
    assert (await settings.dispatch(local, request("install", {"operator_admin": "correct"}), install)).status_code == 401
    config = load_config(tmp_path / "config.json")
    config.tools.mcp_docker.allow_remote_admin = True
    save_config(config, tmp_path / "config.json")
    # Remote auth now passes; malformed request is rejected at the domain boundary.
    assert (await settings.dispatch(remote, request("install", {"operator_admin": "new-password"}), install)).status_code == 400


@pytest.mark.asyncio
async def test_restore_requires_server_confirmation_and_maps_broker_rejection(tmp_path: Path) -> None:
    settings = router(tmp_path / "config.json")
    local = SimpleNamespace(remote_address=("127.0.0.1", 4567))
    setup_path = "/api/settings/mcp-docker/operator-setup"
    setup = await settings.dispatch(local, request("operator-setup", {"operator_admin": "correct"}), setup_path)
    assert setup.status_code == 200

    restore_path = "/api/settings/mcp-docker/restore"
    missing_confirmation = await settings.dispatch(local, request("restore", {
        "operator_admin": "correct",
        "backup_id": "2026-10-08T12-00-00-weather-abc123",
        "expected_revision": 0,
    }), restore_path)
    assert missing_confirmation.status_code == 400

    def reject_restore(_backup_dir: Path, _revision: int, _confirmation: str) -> dict:
        raise BrokerRejectedError(400, "broker rejected reconcile")

    settings._mcp_docker.restore_backup = reject_restore
    rejected = await settings.dispatch(local, request("restore", {
        "operator_admin": "correct",
        "backup_id": "2026-10-08T12-00-00-weather-abc123",
        "expected_revision": 0,
        "expected_confirmation": "weather",
    }), restore_path)
    assert rejected.status_code == 502
    assert json.loads(rejected.body) == {"error": "Docker MCP broker rejected the restore operation"}

    settings._mcp_docker.restore_backup = lambda _backup_dir, _revision, _confirmation: {
        "server": "weather",
        "state": "running",
    }
    restored = await settings.dispatch(local, request("restore", {
        "operator_admin": "correct",
        "backup_id": "2026-10-08T12-00-00-weather-abc123",
        "expected_revision": 0,
        "expected_confirmation": "weather",
    }), restore_path)
    assert restored.status_code == 200
    assert json.loads(restored.body)["mcp_runtime"]["requires_restart"] is True


@pytest.mark.asyncio
async def test_observational_list_is_webui_authenticated_and_fails_closed_when_broker_is_offline(tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    config = load_config(path)
    config.tools.mcp_docker.servers["weather"] = DockerServer(
        server_id="weather",
        source={"type": "local-image", "reference": "sha256:" + "a" * 64},
    )
    config.tools.mcp_docker.configurations["weather"] = {
        "env": {"API_TOKEN": {"kind": "secret", "value": "not-for-the-response"}},
    }
    save_config(config, path)
    local = SimpleNamespace(remote_address=("127.0.0.1", 4567))
    route = "/api/settings/mcp-docker/list"
    settings = router(path)

    response = await settings.dispatch(local, request("list"), route)
    payload = json.loads(response.body)

    assert response.status_code == 200
    observed = payload["servers"]["weather"]
    assert observed["dockerObservation"] == "unknown"
    assert observed["mcpConnectivity"] == "unknown"
    assert payload["brokerStatus"] == {
        "status": "unavailable", "reason": "token-missing",
        "message": "Broker token is missing from this gateway instance.",
    }
    assert "observationError" not in observed
    assert "not-for-the-response" not in response.body.decode()
    assert (await router(path, authorized=False).dispatch(local, request("list"), route)).status_code == 401
