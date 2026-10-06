"""Opt-in real Chromium smoke for the bundled SPA on the gateway's own origin."""

from __future__ import annotations

import asyncio
import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

import httpx
import pytest
from websockets.asyncio.client import connect
from websockets.asyncio.server import ServerConnection, serve

from nanobot.agent.kg.ak.core import write_source_note
from nanobot.agent.kg.cm.core import notes_write
from nanobot.channels.websocket.runtime import WebSocketConfig
from nanobot.webui.gateway_services import build_gateway_services
from nanobot.webui.inbound_commands import WebUICommandRouter
from nanobot.webui.kg_static import kg_static_root


class _Transport:
    async def webui_send_event(self, connection: ServerConnection, event: str,
                                **fields: Any) -> None:
        await connection.send(json.dumps({"event": event, **fields}))


@pytest.mark.asyncio
async def test_packaged_spa_graph_in_browser(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    chromium = shutil.which("chromium")
    if not chromium:
        pytest.skip("real-browser smoke requires Chromium")
    root = Path(os.environ.get("PERCIVAL_KG_SPA_DIST", str(kg_static_root())))
    if not (root / "SOURCE.json").is_file():
        pytest.skip("run the SPA snapshot build before the browser smoke")
    monkeypatch.setattr("nanobot.webui.ws_http.kg_static_root", lambda: root)

    workspace = tmp_path / "workspace"
    workspace.mkdir()
    cm = workspace / ".collective-memory"
    ak = workspace / ".acquired-knowledge"
    cm_id, ak_id = "20261006-120000", "20261006-120001"
    notes_write(cm, note_id=cm_id, body="browser fixture", frontmatter_patch={"title": "CM Graph"})
    ak.mkdir()
    write_source_note(
        ak, source_id=ak_id, title="AK Graph", body="## Conteúdo extraído\n\nBrowser fixture\n",
        note_type="ExtractedNote", source_kind="document", file_path="",
        content_sha256="a" * 64, media_type="text/plain", size_bytes=15,
        chunks_total=1, parsed_chars=15, page_count=None, tags=[],
    )
    for bundle, note_id, label in ((cm, cm_id, "CM Graph"), (ak, ak_id, "AK Graph")):
        artifact = bundle / "graphify-out" / "graph.json"
        artifact.parent.mkdir()
        artifact.write_text(json.dumps({"directed": True, "multigraph": False, "graph": {},
                                        "nodes": [{"id": note_id, "label": label}], "links": []}))
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps({"agents": {"defaults": {"workspace": str(workspace)}}}))
    webui = tmp_path / "webui"
    webui.mkdir()
    (webui / "index.html").write_text("<!doctype html><title>WebUI</title>")
    services = build_gateway_services(
        config=WebSocketConfig(host="127.0.0.1", token_issue_secret="fixture-secret"),
        bus=None, session_manager=None, static_dist_path=webui, workspace_path=workspace,
        config_path=config_path, default_restrict_to_workspace=True, runtime_model_name=None,
        runtime_surface="browser", runtime_capabilities_overrides=None,
    )
    router = WebUICommandRouter(_Transport(), services)

    async def process(connection: ServerConnection, request: Any) -> Any:
        return await services.endpoint.process_request(connection, request, is_allowed=lambda _: True)

    async def messages(connection: ServerConnection) -> None:
        async for raw in connection:
            await router.dispatch(connection, "f7-browser", json.loads(raw))

    chrome: subprocess.Popen[bytes] | None = None
    try:
        async with serve(messages, "127.0.0.1", 0, process_request=process) as server:
            port = server.sockets[0].getsockname()[1]
            origin = f"http://127.0.0.1:{port}"
            async with httpx.AsyncClient(trust_env=False) as client:
                assert (await client.get(origin + "/")).status_code == 200
                index = await client.get(origin + "/kg-interface/#/graph")
                assert index.status_code == 200
                assert (await client.get(origin + "/kg-interface/missing.js")).status_code == 404
                assert (await client.get(origin + "/kg-interface/api/memory/graph/data")).status_code == 401
                for asset in ("src", "href"):
                    for path in re.findall(rf'{asset}="(/kg-interface/[^\"]+)"', index.text):
                        response = await client.get(origin + path)
                        assert response.status_code == 200, path

            profile = tmp_path / "chromium"
            chrome = subprocess.Popen(
                [chromium, "--headless=new", "--no-sandbox", "--disable-gpu",
                 "--disable-dev-shm-usage", "--no-first-run", "--disable-background-networking",
                 "--remote-debugging-port=0", "--remote-allow-origins=*",
                 f"--user-data-dir={profile}", f"{origin}/kg-interface/#/graph"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            deadline = asyncio.get_running_loop().time() + 30
            debug_port = profile / "DevToolsActivePort"
            while not debug_port.is_file() and asyncio.get_running_loop().time() < deadline:
                await asyncio.sleep(0.1)
            assert debug_port.is_file(), "Chromium DevTools did not start"
            cdp_port = int(debug_port.read_text().splitlines()[0])
            async with httpx.AsyncClient(trust_env=False) as client:
                pages = (await client.get(f"http://127.0.0.1:{cdp_port}/json/list")).json()
            page = next(item for item in pages if item.get("type") == "page")
            async with connect(page["webSocketDebuggerUrl"]) as devtools:
                async def evaluate(expression: str) -> Any:
                    await devtools.send(json.dumps({"id": 1, "method": "Runtime.evaluate", "params": {
                        "expression": expression, "returnByValue": True,
                    }}))
                    while True:
                        event = json.loads(await asyncio.wait_for(devtools.recv(), timeout=5))
                        if event.get("id") == 1:
                            assert "exceptionDetails" not in event.get("result", {}), event
                            return event.get("result", {}).get("result", {}).get("value")

                async def until(expression: str) -> Any:
                    while asyncio.get_running_loop().time() < deadline:
                        value = await evaluate(expression)
                        if value:
                            return value
                        await asyncio.sleep(0.15)
                    pytest.fail(f"Chromium timed out: {expression}")

                await until('!!document.querySelector("#kg-gateway-secret")')
                await evaluate('''(() => {
                    const input = document.querySelector("#kg-gateway-secret");
                    Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, "value").set.call(input, "fixture-secret");
                    input.dispatchEvent(new Event("input", { bubbles: true }));
                    input.closest("form").querySelector('button[type="submit"]').click();
                })()''')
                await until('!!document.querySelector("[data-testid=graph-canvas] [aria-label=\\"CM Graph\\"]")')
                await evaluate('document.querySelector("[role=radio][aria-checked=false]").click()')
                await until('!!document.querySelector("[data-testid=graph-canvas] [aria-label=\\"AK Graph\\"]")')
                await evaluate('document.querySelector("[aria-label=\\"AK Graph\\"]").dispatchEvent(new MouseEvent("click", { bubbles: true }))')
                assert await until('location.hash === "#/extracted-notes/20261006-120001"')
                assert not await evaluate('Object.keys(localStorage).some(k => /token|secret|auth/i.test(k))')
    finally:
        if chrome is not None:
            chrome.terminate()
            try:
                await asyncio.to_thread(chrome.wait, 5)
            except subprocess.TimeoutExpired:
                chrome.kill()
                await asyncio.to_thread(chrome.wait, 5)
        await router.close()
