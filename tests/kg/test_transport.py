"""The KG HTTP seam and existing WebUI mutation channel share gateway auth."""

from __future__ import annotations

import asyncio
import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

import httpx
import pytest
from websockets.asyncio.client import connect
from websockets.asyncio.server import ServerConnection, serve
from websockets.exceptions import InvalidStatus

from nanobot.channels.websocket.runtime import WebSocketConfig
from nanobot.webui.gateway_services import build_gateway_services
from nanobot.webui.inbound_commands import WebUICommandRouter


class _Transport:
    async def webui_send_event(
        self, connection: ServerConnection, event: str, **fields: Any,
    ) -> None:
        await connection.send(json.dumps({"event": event, **fields}))


@pytest.mark.asyncio
async def test_get_bearer_and_authenticated_ws_mutation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    webui_dist = tmp_path / "webui-dist"
    webui_dist.mkdir()
    (webui_dist / "index.html").write_text("<!doctype html><title>WebUI</title>")
    kg_dist = tmp_path / "kg-dist"
    kg_dist.mkdir()
    (kg_dist / "index.html").write_text("<!doctype html><title>KG</title>")
    monkeypatch.setattr("nanobot.webui.ws_http.kg_static_root", lambda: kg_dist)
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps({"agents": {"defaults": {"workspace": str(workspace)}}}))
    config = WebSocketConfig(host="127.0.0.1", token_issue_secret="fixture-secret")
    services = build_gateway_services(
        config=config, bus=None, session_manager=None, static_dist_path=webui_dist,
        workspace_path=workspace, config_path=config_path,
        default_restrict_to_workspace=True, runtime_model_name=None,
        runtime_surface="browser", runtime_capabilities_overrides=None,
    )
    router = WebUICommandRouter(_Transport(), services)

    async def process(connection: ServerConnection, request: Any) -> Any:
        return await services.endpoint.process_request(connection, request, is_allowed=lambda _: True)

    async def messages(connection: ServerConnection) -> None:
        async for message in connection:
            await router.dispatch(connection, "kg-browser", json.loads(message))

    async with serve(messages, "127.0.0.1", 0, process_request=process) as server:
        port = server.sockets[0].getsockname()[1]
        origin = f"http://127.0.0.1:{port}"
        try:
            async with httpx.AsyncClient(trust_env=False) as client:
                health_path = "/kg-interface/api/memory/healthz"
                assert (await client.get(origin + health_path)).status_code == 401
                bootstrap = (await client.get(origin + "/webui/bootstrap", headers={
                    "X-Nanobot-Auth": "fixture-secret",
                })).json()
                assert (await client.get(
                    origin + health_path, params={"token": bootstrap["api_token"]},
                )).status_code == 401
                assert (await client.get(
                    origin + health_path, params={"token": bootstrap["api_token"]},
                    headers={"Authorization": "Bearer invalid"},
                )).status_code == 401
                assert (await client.get(
                    origin + health_path, params={"token": "do-not-log"},
                    headers={"Authorization": f'Bearer {bootstrap["api_token"]}'},
                )).status_code == 401
                response = await client.get(origin + health_path, headers={
                    "Authorization": f'Bearer {bootstrap["api_token"]}',
                })
                assert response.status_code == 503
                assert response.json()["ok"] is False
                unknown = await client.get(origin + "/kg-interface/api/memory/missing", headers={
                    "Authorization": f'Bearer {bootstrap["api_token"]}',
                })
                assert unknown.status_code == 404
                assert unknown.headers["content-type"].startswith("application/json")
                assert (await client.get(origin + "/")).text.startswith("<!doctype html>")
                assert "<title>KG</title>" in (await client.get(origin + "/kg-interface/")).text
                assert (await client.get(origin + "/kg-interface/assets/missing.js")).status_code == 404
                with pytest.raises(InvalidStatus) as denied:
                    async with connect(f'ws://127.0.0.1:{port}{bootstrap["ws_path"]}?client_id=anon'):
                        pass
                assert denied.value.response.status_code == 401

                # Same bootstrap supplies a WebUI-audience WS credential; a
                # real settings mutation exercises the gateway's existing
                # allowlist and typed webui_response, not a fake KG write.
                async with connect(
                    f'ws://127.0.0.1:{port}{bootstrap["ws_path"]}'
                    f'?token={bootstrap["token"]}&client_id=kg-browser',
                ) as ws:
                    await ws.send(json.dumps({
                        "type": "webui_request", "request_id": "kg-transport-probe",
                        "action": "settings.runtime_config.update",
                        "payload": {"values": {"agents.defaults.max_tool_iterations": 3}},
                    }))
                    for _ in range(5):
                        event = json.loads(await asyncio.wait_for(ws.recv(), timeout=5))
                        if event.get("event") == "webui_response":
                            assert event["ok"] is True, event
                            break
                    else:
                        pytest.fail("gateway did not return the mutation result")
                assert json.loads(config_path.read_text())["agents"]["defaults"][
                    "maxToolIterations"
                ] == 3
        finally:
            await router.close()


@pytest.mark.asyncio
async def test_spa_transport_in_real_browser_against_gateway(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Opt-in cross-repo smoke: browser JS, real listener, authenticated GET and WS."""
    source = os.environ.get("PERCIVAL_KG_SPA_SOURCE")
    bun, chromium = shutil.which("bun"), shutil.which("chromium")
    if not source or not bun or not chromium:
        pytest.skip("browser smoke needs PERCIVAL_KG_SPA_SOURCE, bun and Chromium")
    probe = Path(source) / "src/tests/gateway-browser-probe.ts"
    if not probe.is_file():
        pytest.skip("SPA browser probe source not available")

    dist = tmp_path / "kg-dist"
    assets = dist / "assets"
    assets.mkdir(parents=True)
    build = await asyncio.to_thread(
        subprocess.run,
        [bun, "build", str(probe), "--target", "browser", "--define", "import.meta.env.DEV=false",
         "--outfile", str(assets / "browser-probe.js")],
        capture_output=True, text=True, timeout=60, check=False,
    )
    assert build.returncode == 0, build.stderr
    (dist / "index.html").write_text(
        '<!doctype html><html><body><input id="kg-secret" value="fixture-secret">'
        '<script type="module" src="/kg-interface/assets/browser-probe.js"></script>'
        '</body></html>'
    )
    monkeypatch.setattr("nanobot.webui.ws_http.kg_static_root", lambda: dist)
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps({"agents": {"defaults": {"workspace": str(workspace)}}}))
    webui_dist = tmp_path / "webui-dist"
    webui_dist.mkdir()
    (webui_dist / "index.html").write_text("<!doctype html><title>WebUI</title>")
    services = build_gateway_services(
        config=WebSocketConfig(host="127.0.0.1", token_issue_secret="fixture-secret"),
        bus=None, session_manager=None, static_dist_path=webui_dist,
        workspace_path=workspace, config_path=config_path,
        default_restrict_to_workspace=True, runtime_model_name=None,
        runtime_surface="browser", runtime_capabilities_overrides=None,
    )
    router = WebUICommandRouter(_Transport(), services)

    async def process(connection: ServerConnection, request: Any) -> Any:
        return await services.endpoint.process_request(connection, request, is_allowed=lambda _: True)

    async def messages(connection: ServerConnection) -> None:
        async for message in connection:
            await router.dispatch(connection, "kg-browser", json.loads(message))

    try:
        async with serve(messages, "127.0.0.1", 0, process_request=process) as server:
            port = server.sockets[0].getsockname()[1]
            profile = tmp_path / "chrome"
            chrome = subprocess.Popen(
                [chromium, "--headless=new", "--no-sandbox", "--disable-gpu",
                 "--disable-dev-shm-usage", "--no-first-run", "--disable-background-networking",
                 "--remote-debugging-port=0", "--remote-allow-origins=*",
                 f"--user-data-dir={profile}", f"http://127.0.0.1:{port}/kg-interface/"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            try:
                deadline = asyncio.get_running_loop().time() + 20
                debug_port = profile / "DevToolsActivePort"
                while not debug_port.is_file() and asyncio.get_running_loop().time() < deadline:
                    await asyncio.sleep(0.1)
                assert debug_port.is_file(), "Chromium DevTools did not start"
                cdp_port = int(debug_port.read_text().splitlines()[0])
                async with httpx.AsyncClient(trust_env=False) as client:
                    pages = (await client.get(f"http://127.0.0.1:{cdp_port}/json/list")).json()
                page = next(item for item in pages if item.get("type") == "page")
                status: str | None = None
                async with connect(page["webSocketDebuggerUrl"]) as devtools:
                    while asyncio.get_running_loop().time() < deadline:
                        await devtools.send(json.dumps({
                            "id": 1, "method": "Runtime.evaluate",
                            "params": {"expression": "document.documentElement.dataset.probe"},
                        }))
                        while True:
                            event = json.loads(await asyncio.wait_for(devtools.recv(), timeout=5))
                            if event.get("id") == 1:
                                break
                        status = event.get("result", {}).get("result", {}).get("value")
                        if status:
                            break
                        await asyncio.sleep(0.1)
                assert status == "passed", f"browser KG transport: {status or 'timed out'}"
            finally:
                chrome.terminate()
                try:
                    await asyncio.to_thread(chrome.wait, 5)
                except subprocess.TimeoutExpired:
                    chrome.kill()
                    await asyncio.to_thread(chrome.wait, 5)
            assert json.loads(config_path.read_text())["agents"]["defaults"]["maxToolIterations"] == 3
    finally:
        await router.close()
