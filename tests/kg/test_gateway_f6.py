"""F6: native bundle payloads, bearer reads and authenticated WS writes."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

import httpx
import pytest
from websockets.asyncio.client import connect
from websockets.asyncio.server import ServerConnection, serve
from websockets.exceptions import InvalidStatus

from nanobot.agent.kg.ak.core import write_source_note
from nanobot.agent.kg.cm.core import notes_read, notes_write
from nanobot.channels.websocket.runtime import WebSocketConfig
from nanobot.webui.gateway_services import build_gateway_services
from nanobot.webui.inbound_commands import WebUICommandRouter

CM_ID = "20261006-120000"
AK_ID = "20261006-120001"
SOURCE_ID = "20261006-120002"


class _Transport:
    async def webui_send_event(self, connection: ServerConnection, event: str,
                                **fields: Any) -> None:
        await connection.send(json.dumps({"event": event, **fields}))


@pytest.mark.asyncio
async def test_native_kg_listener_contract(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    cm = workspace / ".collective-memory"
    ak = workspace / ".acquired-knowledge"
    created = notes_write(cm, note_id=CM_ID, body="original needle", frontmatter_patch={"title": "CM"})
    ak.mkdir()
    for note_id, note_type in ((AK_ID, "ExtractedNote"), (SOURCE_ID, "Source")):
        write_source_note(
            ak, source_id=note_id, title=note_type, body="## Conteúdo extraído\n\nsource needle\n",
            note_type=note_type, source_kind="document", file_path="", content_sha256="a" * 64,
            media_type="text/plain", size_bytes=13, chunks_total=1, parsed_chars=13,
            page_count=None, tags=["kg"],
        )
    for root, note_id in ((cm, CM_ID), (ak, AK_ID)):
        graph_dir = root / "graphify-out"
        graph_dir.mkdir()
        (graph_dir / "graph.json").write_text(json.dumps({
            "directed": True, "multigraph": False, "graph": {},
            "nodes": [{"id": note_id, "label": "fixture"}], "links": [],
        }))
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps({"agents": {"defaults": {"workspace": str(workspace)}}}))
    services = build_gateway_services(
        config=WebSocketConfig(host="127.0.0.1", token_issue_secret="fixture-secret"),
        bus=None, session_manager=None, static_dist_path=None,
        workspace_path=workspace, config_path=config_path,
        default_restrict_to_workspace=True, runtime_model_name=None,
        runtime_surface="browser", runtime_capabilities_overrides=None,
    )
    router = WebUICommandRouter(_Transport(), services)

    async def process(connection: ServerConnection, request: Any) -> Any:
        return await services.endpoint.process_request(connection, request, is_allowed=lambda _: True)

    async def messages(connection: ServerConnection) -> None:
        async for raw in connection:
            await router.dispatch(connection, "kg-browser", json.loads(raw))

    try:
        async with serve(messages, "127.0.0.1", 0, process_request=process) as server:
            port = server.sockets[0].getsockname()[1]
            origin = f"http://127.0.0.1:{port}"
            async with httpx.AsyncClient(trust_env=False) as client:
                prefix = "/kg-interface/api/"
                assert (await client.get(origin + prefix + "memory/notes")).status_code == 401
                bootstrap = (await client.get(origin + "/webui/bootstrap", headers={
                    "X-Nanobot-Auth": "fixture-secret",
                })).json()
                headers = {"Authorization": "Bearer " + bootstrap["api_token"]}

                async def get(path: str) -> dict[str, Any]:
                    response = await client.get(origin + prefix + path, headers=headers)
                    assert response.status_code == 200, (path, response.text)
                    return response.json()

                assert (await get("memory/healthz"))["ok"]
                assert (await get("acquire/healthz"))["ok"]
                assert (await get("memory/notes?limit=1"))["results"][0]["title"] == "CM"
                assert (await get(f"memory/notes/{CM_ID}"))["body_hash"] == created["body_hash"]
                assert (await get(f"memory/notes/{CM_ID}/history?limit=1"))["history"]
                assert (await get("memory/notes?q=needle"))["count"] == 1
                assert (await get("memory/search?q=needle"))["count"] == 1
                assert (await get("memory/stats"))["notes_total"] == 1
                assert "total_bytes" in await get("memory/storage/stats")
                assert (await get("memory/graph"))["exists"]
                assert (await get("memory/graph/data"))["nodes"][0]["id"] == CM_ID
                assert (await get("acquire/notes"))["results"][0]["id"] == AK_ID
                assert (await get(f"acquire/notes/{AK_ID}"))["body_hash"]
                assert (await get("acquire/search?q=needle"))["count"] == 2
                assert (await get("acquire/stats"))["sources_total"] == 1
                assert (await get("acquire/graph"))["exists"]
                assert (await get("acquire/graph/data"))["nodes"][0]["id"] == AK_ID
                assert (await get("acquire/sources"))["results"][0]["id"] == SOURCE_ID
                assert (await get(f"acquire/sources/{SOURCE_ID}"))["first_chunk"]["text"]
                assert (await get(f"acquire/sources/{SOURCE_ID}/chunks/0"))["source_id"] == SOURCE_ID
                cm_alias = cm / "notes" / f"{CM_ID}-alias.md"
                cm_alias.symlink_to(cm / "notes" / f"{CM_ID}-cm.md")
                assert (await client.get(origin + prefix + "memory/notes", headers=headers)).status_code == 403
                cm_alias.unlink()
                ak_alias = ak / "notes" / f"{AK_ID}-alias.md"
                ak_alias.symlink_to(ak / "notes" / f"{AK_ID}-ExtractedNote.md")
                assert (await client.get(origin + prefix + "acquire/notes", headers=headers)).status_code == 403
                ak_alias.unlink()
                assert (await client.get(origin + prefix + "memory/notes/invalid", headers=headers)).status_code == 400
                bad = await client.get(origin + prefix + "memory/missing", headers=headers)
                assert bad.status_code == 404 and bad.headers["content-type"].startswith("application/json")
                assert (await client.get(origin + prefix + "memory/graph/data")).status_code == 401
                assert (await client.get(origin + prefix + f"acquire/notes/{CM_ID}",
                                         headers=headers)).status_code == 404

                with pytest.raises(InvalidStatus) as denied:
                    async with connect(f"ws://127.0.0.1:{port}/?client_id=anon"):
                        pass
                assert denied.value.response.status_code == 401

                async with connect(
                    f"ws://127.0.0.1:{port}{bootstrap['ws_path']}"
                    f"?token={bootstrap['token']}&client_id=kg-browser",
                ) as ws:
                    serial = 0

                    async def mutate(action: str, payload: dict[str, Any]) -> dict[str, Any]:
                        nonlocal serial
                        serial += 1
                        await ws.send(json.dumps({"type": "webui_request", "request_id": f"kg-{serial}",
                                                  "action": action, "payload": payload}))
                        for _ in range(5):
                            event = json.loads(await asyncio.wait_for(ws.recv(), timeout=5))
                            if event.get("event") == "webui_response":
                                return event
                        pytest.fail("missing mutation response")

                    body = {"note_id": CM_ID, "body": "updated", "base_body_hash": created["body_hash"]}
                    result = await mutate("kg.memory.notes.body", body)
                    assert result["ok"] and result["result"]["body_hash"] != created["body_hash"]
                    assert notes_read(cm, CM_ID)["body"] == "updated"
                    stale = await mutate("kg.memory.notes.body", {**body, "body": "stale"})
                    assert stale["error"]["status"] == 409
                    conflict = json.loads(stale["error"]["message"])
                    assert conflict == {
                        "status": "conflict", "base_body_hash": created["body_hash"],
                        "current_body_hash": notes_read(cm, CM_ID)["body_hash"],
                        "server_body": "updated",
                    }
                    assert (await mutate("kg.memory.notes.protected", {"note_id": CM_ID,
                                     "protected": True}))["result"]["protected"]
                    assert (await mutate("kg.memory.notes.lifecycle", {"note_id": CM_ID,
                                     "lifecycle": "cold", "force": True}))["result"]["lifecycle"] == "cold"
                    assert (await mutate("kg.memory.notes.flag", {"note_id": CM_ID, "kind": "stale_after_expired",
                                     "confidence": "low", "reason": "review"}))["ok"]
                    assert (await mutate("kg.memory.notes.resolve", {"note_id": CM_ID,
                                     "kind": "stale_after_expired", "resolution": "acknowledge"}))["ok"]
                    assert (await mutate("kg.memory.storage.maintenance", {"dry_run": True}))["ok"]
                    ak_read = await get(f"acquire/notes/{AK_ID}")
                    assert (await mutate("kg.acquire.notes.body", {"note_id": AK_ID, "body": "AK edited",
                                     "base_body_hash": ak_read["body_hash"]}))["ok"]
                    assert (await mutate("kg.acquire.notes.forget", {"note_id": AK_ID}))["error"]["status"] == 404
                    (cm / "_archive").symlink_to(cm / "notes", target_is_directory=True)
                    refused = await mutate("kg.memory.notes.forget", {"note_id": CM_ID,
                                                                          "reason": "archived"})
                    assert refused["error"]["status"] == 403
                    assert notes_read(cm, CM_ID)["body"] == "updated"
                    (cm / "_archive").unlink()
                    assert (await mutate("kg.memory.notes.forget", {"note_id": CM_ID,
                                     "reason": "archived"}))["result"]["archived"]
                    assert (await client.get(origin + prefix + f"memory/notes/{CM_ID}",
                                             headers=headers)).status_code == 404
                graph_path = ak / "graphify-out" / "graph.json"
                graph_path.unlink()
                missing = await client.get(origin + prefix + "acquire/graph/data", headers=headers)
                assert missing.status_code == 404 and missing.json()["error"] == "bundle_or_note_not_found"
                assert (await get("acquire/graph")) == {"exists": False}
                outside = tmp_path / "outside.json"
                outside.write_text('{"nodes":[],"links":[]}')
                graph_path.symlink_to(outside)
                assert (await client.get(origin + prefix + "acquire/graph/data",
                                         headers=headers)).status_code == 403
                graph_path.unlink()
                graph_path.write_bytes(b" " * (8 * 1024 * 1024 + 1))
                large = await client.get(origin + prefix + "acquire/graph/data", headers=headers)
                assert large.status_code == 413 and large.json()["error"] == "graph_too_large"
                config_path.write_text(json.dumps({"kg": {"cmRoot": str(tmp_path)},
                                                    "agents": {"defaults": {"workspace": str(workspace)}}}))
                assert (await client.get(origin + prefix + "memory/graph/data",
                                         headers=headers)).status_code == 403
    finally:
        await router.close()
