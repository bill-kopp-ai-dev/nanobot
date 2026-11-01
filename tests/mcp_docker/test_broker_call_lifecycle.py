"""Real pipes/HTTP regression coverage for bounded MCP calls and cancellation."""

from __future__ import annotations

import json
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

from nanobot.mcp_docker import broker
from nanobot.mcp_docker.contracts import DockerHostConfig, DockerImageSource

FIXTURE = r'''
import asyncio,json,sys
tasks={}
def emit(value):
    print(json.dumps(value),flush=True)
async def call(message):
    ident=message['id']
    try:
        emit({'jsonrpc':'2.0','method':'notifications/progress','params':{'progressToken':ident,'progress':0}})
        await asyncio.sleep(message['params'].get('arguments',{}).get('seconds',0))
        emit({'jsonrpc':'2.0','id':ident,'result':{'content':[{'type':'text','text':'complete'}],'isError':False}})
    except asyncio.CancelledError:
        emit({'jsonrpc':'2.0','id':ident,'error':{'code':0,'message':'Request cancelled'}})
async def main():
    while True:
        line=await asyncio.to_thread(sys.stdin.readline)
        if not line: break
        message=json.loads(line); method=message['method']; ident=message.get('id')
        if method=='initialize':
            emit({'jsonrpc':'2.0','id':ident,'result':{'capabilities':{}}})
        elif method=='tools/call':
            tasks[ident]=asyncio.create_task(call(message))
        elif method=='notifications/cancelled':
            task=tasks.get(message['params']['requestId'])
            if task: task.cancel()
asyncio.run(main())
'''


@pytest.fixture
def pipe_fixture(monkeypatch):
    popen = subprocess.Popen
    monkeypatch.setattr(broker, "_running", lambda _: True)
    monkeypatch.setattr(broker.subprocess, "Popen", lambda *args, **kwargs: popen(
        [sys.executable, "-u", "-c", FIXTURE], **kwargs,
    ))


def test_notifications_do_not_replace_tool_response(pipe_fixture):
    response = broker._exchange("fixture", {
        "jsonrpc": "2.0", "id": 8, "method": "tools/call",
        "params": {"name": "delay", "arguments": {"seconds": 0.01}},
    })
    assert response["id"] == 8
    assert response["result"]["content"][0]["text"] == "complete"


@pytest.fixture
def http_fixture(monkeypatch, pipe_fixture):
    server = broker.ManagedServer("fixture", DockerImageSource(
        type="local-image", reference="sha256:" + "a" * 64,
    ), DockerHostConfig(mounts=[], network="none"))
    server.tools = ["delay"]
    monkeypatch.setitem(broker._STORE, "fixture", server)
    monkeypatch.setattr(broker.Handler, "authorized", lambda _: True)
    http = broker.DrainingThreadingHTTPServer(("127.0.0.1", 0), broker.Handler)
    thread = threading.Thread(target=http.serve_forever, daemon=True)
    thread.start()
    try:
        yield server, http.server_address[1]
    finally:
        http.shutdown()
        http.server_close()
        thread.join(timeout=2)


def post(port, payload, session="test-session"):
    request = Request(f"http://127.0.0.1:{port}/mcp/fixture", json.dumps(payload).encode(), {
        "Content-Type": "application/json", "Mcp-Session-Id": session,
    })
    try:
        with urlopen(request, timeout=3) as response:
            raw = response.read()
            return response.status, json.loads(raw) if raw else {}
    except HTTPError as error:
        return error.code, json.load(error)


def test_wait_for_server_lock_is_inside_deadline(http_fixture, monkeypatch):
    server, port = http_fixture
    monkeypatch.setattr(broker, "_MCP_SHORT_REQUEST_TIMEOUT_S", 0.05)
    with ThreadPoolExecutor() as executor, server.lock:
        result = executor.submit(post, port, {"jsonrpc": "2.0", "id": 3, "method": "tools/list"})
        time.sleep(0.15)
        completed_inside_deadline = result.done()
    assert completed_inside_deadline, "request waited outside the broker's total deadline"
    assert result.result()[0] == 503


def test_cancel_is_not_blocked_by_call_lock_and_next_call_works(http_fixture):
    _, port = http_fixture
    with ThreadPoolExecutor() as executor:
        call = executor.submit(post, port, {
            "jsonrpc": "2.0", "id": 5, "method": "tools/call",
            "params": {"name": "delay", "arguments": {"seconds": 1}},
        })
        time.sleep(0.15)
        # Another session must not cancel the request even if it reuses ID 5.
        assert post(port, {"jsonrpc": "2.0", "method": "notifications/cancelled",
                           "params": {"requestId": 5}}, "other-session")[0] == 202
        assert not call.done()
        started = time.monotonic()
        assert post(port, {"jsonrpc": "2.0", "method": "notifications/cancelled",
                           "params": {"requestId": 5}})[0] == 202
        status, _ = call.result(timeout=1)
        assert status in (200, 409)
        assert time.monotonic() - started < 0.8
    status, response = post(port, {"jsonrpc": "2.0", "id": 5, "method": "tools/call",
                                   "params": {"name": "delay", "arguments": {"seconds": 0}}})
    assert status == 200
    assert response["result"]["content"][0]["text"] == "complete"


def test_overlapping_observations_share_one_bounded_snapshot(monkeypatch):
    server = broker.ManagedServer(
        "fixture",
        DockerImageSource(type="local-image", reference="sha256:" + "b" * 64),
        DockerHostConfig(mounts=[], network="none"),
    )
    monkeypatch.setitem(broker._STORE, "fixture", server)
    monkeypatch.setattr(broker, "image_reference", lambda _source: "fixture")
    monkeypatch.setattr(broker, "_inspect", lambda _server_id: {
        "State": {"Running": True}, "HostConfig": {"NetworkMode": "none"}, "Mounts": [],
    })
    calls = 0

    def discover(_server_id):
        nonlocal calls
        calls += 1
        time.sleep(0.1)
        return ["fixture_tool"]

    monkeypatch.setattr(broker, "_discover", discover)
    payload = {"source": server.source.model_dump(mode="json")}
    with ThreadPoolExecutor(max_workers=4) as executor:
        results = list(executor.map(lambda _: broker._observe("fixture", payload), range(4)))

    assert calls == 1
    assert all(result["mcpConnectivity"] == "connected" for result in results)
    # Return independent snapshots; callers cannot mutate the broker's cache.
    results[0]["tools"].clear()
    assert server.observation_cache["tools"] == ["fixture_tool"]
