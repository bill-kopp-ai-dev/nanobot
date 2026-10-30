"""WebSocket authorization boundary for Docker MCP settings."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from websockets.datastructures import Headers

from nanobot.access.sessions import SESSION_COOKIE_NAME
from nanobot.config.loader import load_config, save_config
from nanobot.config.mcp_docker import DockerServer
from nanobot.mcp_docker.client import BrokerRejectedError
from nanobot.webui.gateway_auth import AccessController
from nanobot.webui.http_utils import http_json_response
from nanobot.webui.settings_routes import WebUISettingsRouter
from nanobot.webui.settings_services import WebUISettingsServices

_OPERATOR_PASSWORD = "crimson forest river lantern 2026"
_OPERATOR_NEW_PASSWORD = "cobalt garden orbit lantern 2026"


def _controller(tmp_path: Path) -> AccessController:
    return AccessController.from_data_dir(tmp_path)


def router(
    path: Path,
    *,
    authorized: bool = True,
    controller: AccessController | None = None,
) -> WebUISettingsRouter:
    return WebUISettingsRouter(
        settings=WebUISettingsServices.create(path), bus=SimpleNamespace(),
        logger=SimpleNamespace(exception=lambda *_args: None),
        check_api_token=lambda _request: authorized,
        parse_query=lambda _path: {}, json_response=http_json_response,
        error_response=lambda code, message: http_json_response({"error": message}, status=code),
        runtime_surface="browser", runtime_capabilities={},
        access=controller or _controller(path.parent),
    )


def request(
    action: str,
    values: dict | None = None,
    *,
    host: str = "127.0.0.1:8765",
    forwarded: str = "",
    session_id: str | None = None,
) -> SimpleNamespace:
    cookie_parts = [f"{SESSION_COOKIE_NAME}={session_id}"] if session_id else []
    headers = Headers([
        ("Host", host),
        *( [("X-Forwarded-For", forwarded)] if forwarded else []),
        *([("Cookie", "; ".join(cookie_parts))] if cookie_parts else []),
    ])
    result = SimpleNamespace(path=f"/api/settings/mcp-docker/{action}", headers=headers)
    if values is not None:
        result._nanobot_webui_mutation_request = True
        result._nanobot_webui_mutation_payload = values
    return result


def _install_session(controller: AccessController, password: str = _OPERATOR_PASSWORD) -> str:
    if not controller.has_password():
        controller.setup(password)
    session = controller.login(password, source="local")
    controller.elevate(password=password, session_id=session.session_id, source="local")
    return session.session_id


@pytest.mark.asyncio
async def test_mutations_require_webui_and_session_elevation(tmp_path: Path) -> None:
    controller = _controller(tmp_path)
    settings = router(tmp_path / "config.json", controller=controller)
    local = SimpleNamespace(remote_address=("127.0.0.1", 4567))
    remote = SimpleNamespace(remote_address=("198.51.100.2", 4567))
    install = "/api/settings/mcp-docker/install"
    assert (await settings.dispatch(local, request("install"), install)).status_code == 405
    # Unauthenticated mutation: the WebUI token gate is the legacy API check;
    # the new contract routes MCP Docker writes through session+elevation.
    assert (await router(tmp_path / "config.json", authorized=False).dispatch(
        local, request("install", {}), install
    )).status_code == 401
    session_id = _install_session(controller)
    assert (await settings.dispatch(
        local, request("install", {"server_id": "a"}, session_id=session_id), install
    )).status_code == 400
    assert (await settings.dispatch(
        remote, request("install", {"server_id": "a"}, session_id=session_id), install
    )).status_code == 403
    assert (await settings.dispatch(local, request("install", {
        "server_id": "a", "expected_revision": 0
    }, session_id=session_id), install)).status_code == 400
    valid = {"server_id": "a", "expected_revision": 0,
             "source": {"type": "local-image", "reference": "sha256:" + "a" * 64},
             "configuration": {}}
    assert (await settings.dispatch(
        local, request("install", valid, session_id=session_id), install
    )).status_code == 503
    assert not (tmp_path / "config.json").exists()  # no publication after broker failure
    # Rotating the password revokes the previous session and elevation; the next
    # mutation with the old cookie must fail before reaching the broker.
    controller.change_password(
        current_password=_OPERATOR_PASSWORD,
        new_password=_OPERATOR_NEW_PASSWORD,
    )
    assert (await settings.dispatch(
        local, request("install", {"server_id": "a"}, session_id=session_id), install
    )).status_code == 401
    config = load_config(tmp_path / "config.json")
    config.tools.mcp_docker.allow_remote_admin = True
    save_config(config, tmp_path / "config.json")
    new_session = controller.login(_OPERATOR_NEW_PASSWORD, source="local")
    controller.elevate(
        password=_OPERATOR_NEW_PASSWORD,
        session_id=new_session.session_id,
        source="local",
    )
    # Remote auth now passes; malformed request is rejected at the domain boundary.
    assert (await settings.dispatch(
        remote,
        request("install", {"server_id": "a"}, session_id=new_session.session_id),
        install,
    )).status_code == 400


@pytest.mark.asyncio
async def test_catalog_and_schema_mutations_always_require_local_operator_consent(tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    config = load_config(path)
    config.tools.mcp_docker.allow_remote_admin = True
    save_config(config, path)
    controller = _controller(tmp_path)
    session_id = _install_session(controller)
    settings = router(path, controller=controller)
    remote = SimpleNamespace(remote_address=("198.51.100.2", 4567))

    for action in ("migrate-schema", "restore-schema-v1", "register-catalog", "install-catalog"):
        response = await settings.dispatch(
            remote,
            request(action, {}, session_id=session_id),
            f"/api/settings/mcp-docker/{action}",
        )
        assert response.status_code == 403
        assert json.loads(response.body)["error"].startswith("This catalog or schema operation")


@pytest.mark.asyncio
async def test_restore_requires_server_confirmation_and_maps_broker_rejection(tmp_path: Path) -> None:
    controller = _controller(tmp_path)
    settings = router(tmp_path / "config.json", controller=controller)
    local = SimpleNamespace(remote_address=("127.0.0.1", 4567))
    session_id = _install_session(controller)

    restore_path = "/api/settings/mcp-docker/restore"
    missing_confirmation = await settings.dispatch(local, request("restore", {
        "backup_id": "2026-10-08T12-00-00-weather-abc123",
        "expected_revision": 0,
    }, session_id=session_id), restore_path)
    assert missing_confirmation.status_code == 400

    def reject_restore(_backup_dir: Path, _revision: int, _confirmation: str) -> dict:
        raise BrokerRejectedError(400, "broker rejected reconcile")

    settings._mcp_docker.restore_backup = reject_restore
    rejected = await settings.dispatch(local, request("restore", {
        "backup_id": "2026-10-08T12-00-00-weather-abc123",
        "expected_revision": 0,
        "expected_confirmation": "weather",
    }, session_id=session_id), restore_path)
    assert rejected.status_code == 502
    assert json.loads(rejected.body) == {"error": "Docker MCP broker rejected the restore operation"}

    settings._mcp_docker.restore_backup = lambda _backup_dir, _revision, _confirmation: {
        "server": "weather",
        "state": "running",
    }
    restored = await settings.dispatch(local, request("restore", {
        "backup_id": "2026-10-08T12-00-00-weather-abc123",
        "expected_revision": 0,
        "expected_confirmation": "weather",
    }, session_id=session_id), restore_path)
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
