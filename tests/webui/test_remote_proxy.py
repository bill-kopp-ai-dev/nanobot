"""Real browser-side HTTP/WS, real gateway auth, and an owned SSH-pipe fixture."""

import asyncio
import base64
import json
import socket
import sys
import time
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import MagicMock
from urllib.parse import parse_qs, urlsplit

import httpx
import pytest
from aiohttp import WSMsgType as AioWSMsgType
from aiohttp import web as aiohttp_web
from websockets.asyncio.client import connect
from websockets.datastructures import Headers
from websockets.exceptions import InvalidStatus
from websockets.http11 import Request

from nanobot.access.credential import AccessCredential
from nanobot.access.errors import AuthError, AuthThrottledError, SetupRequiredError
from nanobot.channels.websocket.runtime import WebSocketConfig
from nanobot.webui import remote_ssh
from nanobot.webui.client_contract import webui_contract
from nanobot.webui.gateway_services import build_gateway_services
from nanobot.webui.http_utils import (
    build_csrf_cookie,
    build_session_cookie,
)
from nanobot.webui.local_client_assets import LocalClientAssets
from nanobot.webui.remote_proxy import RemoteProxy
from nanobot.webui.remote_ssh import RemoteProfile, open_tunnel

ROOT = "synthetic-remote-root"
MEDIA = "/api/media/AAAAAAAAAAAAAAAAAAAAAA/remoteFilePayload"


def _ws_request_from_aiohttp(req: aiohttp_web.Request) -> Request:
    """Wrap an aiohttp request as a websockets Request so service.endpoint accepts it."""
    headers = Headers(list(req.headers.items()))
    return Request(req.path_qs, headers)


def _ws_connection_from_aiohttp(req: aiohttp_web.Request) -> SimpleNamespace:
    """Minimal websockets.ServerConnection stand-in for service.endpoint dispatch.

    Returned as a frozen dataclass so it can be added to sets such as
    ``services.endpoint.webui_connections`` (which require hashable members).
    """
    from dataclasses import dataclass

    @dataclass(frozen=True)
    class _FakeConnection:
        remote_address: object

    peer = req.transport.get_extra_info("peername") if req.transport else None
    if isinstance(peer, tuple):
        remote_address = (peer[0], peer[1]) + peer[2:] if len(peer) >= 2 else peer
    else:
        remote_address = peer
    return _FakeConnection(remote_address=remote_address)


@pytest.fixture
async def remote(tmp_path, monkeypatch):
    assets = tmp_path / "local-dist"
    assets.mkdir()
    (assets / "index.html").write_text("<!doctype html><title>Local nanobot</title>", encoding="utf-8")
    (assets / "assets").mkdir()
    for name in ["index-AbcD1234.js", "index-AbcD1234.css", "index.js"]:
        (assets / "assets" / name).write_text("local client asset", encoding="utf-8")
    monkeypatch.setattr("nanobot.webui.remote_proxy.LocalClientAssets", lambda: LocalClientAssets(assets))
    config = WebSocketConfig(host="127.0.0.1", token_issue_secret=ROOT, path="/custom/ws")
    services = build_gateway_services(
        config=config, bus=MagicMock(), session_manager=None, static_dist_path=None,
        workspace_path=tmp_path, config_path=tmp_path / "config.json",
        default_restrict_to_workspace=False, runtime_model_name=None,
        runtime_surface="browser", runtime_capabilities_overrides=None,
    )
    # Persist a password verifier so /auth/login accepts the proxy password.
    AccessCredential(tmp_path).set_password(ROOT)
    seen, children = [], []
    # Frozen initial wire declaration: current client vs an independently defined host.
    state = SimpleNamespace(block=asyncio.Event(), entered=asyncio.Event(), ws_redirect=False,
                            contract={"version": "0.3.5", "min_protocol": 1, "max_protocol": 1,
                                      "capabilities": ["webui.core.v1"]})

    async def login_handler(req: aiohttp_web.Request) -> aiohttp_web.Response:
        seen.append(_ws_request_from_aiohttp(req))
        try:
            payload = await req.json()
        except (json.JSONDecodeError, ValueError):
            return aiohttp_web.json_response({"error": "invalid login payload"}, status=400)
        password = payload.get("password") if isinstance(payload, dict) else None
        if not isinstance(password, str):
            return aiohttp_web.json_response({"error": "password required"}, status=400)
        source = req.remote or "unknown"
        try:
            session = services.access.login(password, source=source)
        except SetupRequiredError:
            return aiohttp_web.json_response({"error": "setup_required"}, status=409)
        except AuthThrottledError as exc:
            return aiohttp_web.json_response({"error": str(exc)}, status=429)
        except AuthError as exc:
            return aiohttp_web.json_response({"error": str(exc)}, status=401)
        body = {
            "session_id": session.session_id,
            "csrf_token": session.csrf_token,
            "session_idle_remaining_s": max(0.0, session.idle_expiry - time.monotonic()),
            "session_absolute_remaining_s": max(0.0, session.absolute_expiry - time.monotonic()),
        }
        response = aiohttp_web.json_response(body)
        response.headers["Set-Cookie"] = ", ".join([
            build_session_cookie(session.session_id, secure=False, max_age_s=12 * 60 * 60),
            build_csrf_cookie(session.csrf_token, secure=False),
        ])
        response.headers["Cache-Control"] = "no-store"
        return response

    async def assets_handler(req: aiohttp_web.Request) -> aiohttp_web.Response:
        seen.append(_ws_request_from_aiohttp(req))
        path = req.rel_url.path
        response = aiohttp_web.Response(body=b"fixture asset", status=200)
        response.headers["Content-Type"] = "application/javascript"
        response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
        if "private" in path:
            response.headers["Cache-Control"] = "private, no-store"
        if "cookie" in path:
            response.headers["Set-Cookie"] = "session=private"
        return response

    async def redirect_handler(req: aiohttp_web.Request) -> aiohttp_web.Response:
        seen.append(_ws_request_from_aiohttp(req))
        response = aiohttp_web.Response(body=b"redirect", status=302)
        response.headers["Location"] = "http://127.0.0.1:1/?token=" + ROOT
        response.headers["Set-Cookie"] = "credential=" + ROOT
        return response

    async def api_handler(req: aiohttp_web.Request) -> aiohttp_web.Response:
        seen.append(_ws_request_from_aiohttp(req))
        path = req.rel_url.path
        ws_req = _ws_request_from_aiohttp(req)
        if not services.tokens.check_api_token(ws_req):
            return aiohttp_web.Response(body=b"Unauthorized", status=401)
        if path == "/api/block":
            state.entered.set()
            await state.block.wait()
        response = aiohttp_web.Response(
            body=json.dumps({"text": f"![image]({MEDIA})"}).encode("utf-8"), status=200,
        )
        response.headers["Content-Type"] = "application/json"
        response.headers["Set-Cookie"] = "credential=" + ROOT
        return response

    async def media_handler(req: aiohttp_web.Request) -> aiohttp_web.Response:
        seen.append(_ws_request_from_aiohttp(req))
        assert req.headers.get("Authorization") is None
        response = aiohttp_web.Response(body=b"bytes", status=206)
        response.headers["Content-Type"] = "image/png"
        response.headers["Content-Range"] = "bytes 0-4/10"
        return response

    async def bootstrap_handler(req: aiohttp_web.Request) -> aiohttp_web.StreamResponse:
        seen.append(_ws_request_from_aiohttp(req))
        connection = _ws_connection_from_aiohttp(req)
        response = await services.endpoint.process_request(
            connection, _ws_request_from_aiohttp(req), is_allowed=lambda _: True,
        )
        path = req.rel_url.path
        if path == "/webui/bootstrap" and response.status_code == 200:
            payload = json.loads(response.body)
            payload["terminal"]["webui"] = state.contract
            new_body = json.dumps(payload).encode()
            # websockets Headers.__setitem__ appends rather than replaces;
            # delete first to keep exactly one Content-Length matching the
            # rewritten body before we forward through aiohttp.
            try:
                del response.headers["Content-Length"]
            except KeyError:
                pass
            response.body = new_body
            response.headers["Content-Length"] = str(len(response.body))
        # The gateway returns websockets Response objects; lift them into aiohttp.
        from aiohttp.web import Response as AioResponse
        if isinstance(response, AioResponse):
            return response
        headers = [(key, value) for key, value in response.headers.raw_items()]
        return aiohttp_web.Response(
            body=getattr(response, "body", b""), status=response.status_code,
            headers=headers,
        )

    async def ws_handler(req: aiohttp_web.Request) -> aiohttp_web.WebSocketResponse:
        seen.append(_ws_request_from_aiohttp(req))
        ws_req = _ws_request_from_aiohttp(req)
        connection = _ws_connection_from_aiohttp(req)
        # Replicate the gateway's authorize step: accept ?token= or trusted proxy.
        from nanobot.webui.gateway_endpoint import is_websocket_upgrade
        from nanobot.webui.http_utils import parse_query, query_first
        if not is_websocket_upgrade(ws_req):
            return aiohttp_web.Response(status=400, text="WS required")
        query = parse_query(req.path_qs)
        supplied = query_first(query, "token")
        accepted = False
        if supplied:
            session_id = services.tokens.session_for_issued_token(supplied)
            if session_id and services.endpoint._consume_issued_with_session(
                connection, supplied, session_id,
            ):
                accepted = True
        if not accepted and not config.websocket_requires_token:
            accepted = True
        if not accepted:
            return aiohttp_web.Response(status=401, text="Unauthorized")
        if state.ws_redirect:
            response = aiohttp_web.Response(body=b"redirect", status=302)
            response.headers["Location"] = "http://127.0.0.1:1/?token=" + ROOT
            response.headers["Set-Cookie"] = "credential=" + ROOT
            return response
        # The legacy ``X-Nanobot-Auth`` shared-secret contract is gone; the
        # proxy now authenticates with the cached session cookie and a Bearer
        # query token. Replicating the prior fixture's negative assertion.
        assert req.headers.get("X-Nanobot-Auth") is None
        ws = aiohttp_web.WebSocketResponse(max_msg_size=64 * 1024 * 1024, heartbeat=30)
        await ws.prepare(req)
        services.endpoint.webui_connections.add(connection)
        await ws.send_json({"ready": True, "media": MEDIA,
                            "query": parse_qs(urlsplit(req.path_qs).query).get("client_id")})
        async for message in ws:
            if message.type == AioWSMsgType.TEXT:
                await ws.send_str(message.data)
            elif message.type == AioWSMsgType.BINARY:
                await ws.send_bytes(message.data)
        return ws

    app = aiohttp_web.Application(client_max_size=64 * 1024 * 1024)
    app.router.add_post("/auth/login", login_handler)
    app.router.add_get("/assets/{tail:.*}", assets_handler)
    app.router.add_get("/redirect", redirect_handler)
    app.router.add_get("/api/fixture", api_handler)
    app.router.add_get("/api/block", api_handler)
    app.router.add_get(MEDIA, media_handler)
    app.router.add_get("/webui/bootstrap", bootstrap_handler)
    app.router.add_get("/webui/terminal", bootstrap_handler)
    # The fixture accepts WS upgrades on the configured ``config.path``
    # AND on any other path, mirroring the prior ``serve()`` behaviour that
    # ran the ``messages`` handler for every WS handshake regardless of
    # path. The handler still validates the configured path internally.
    app.router.add_get(config.path, ws_handler)
    app.router.add_get("/{ws_path:.*}", ws_handler)

    real_spawn = asyncio.create_subprocess_exec
    monkeypatch.setattr(remote_ssh.shutil, "which", lambda _: "fixture-ssh")
    runner = aiohttp_web.AppRunner(app, access_log=None, handle_signals=False)
    await runner.setup()
    site = aiohttp_web.TCPSite(runner, "127.0.0.1", 0)
    await site.start()
    port = site._server.sockets[0].getsockname()[1]  # type: ignore[union-attr]
    try:
        pipe = f"""
import os, socket, threading
upstream = socket.create_connection(('127.0.0.1', {port}))
def upload():
    while data := os.read(0, 65536):
        upstream.sendall(data)
    upstream.shutdown(socket.SHUT_WR)
threading.Thread(target=upload, daemon=True).start()
while data := upstream.recv(65536):
    os.write(1, data)
"""

        async def spawn(*args, **kwargs):
            child = await real_spawn(sys.executable, "-u", "-c", pipe, **kwargs)
            children.append(child)
            return child

        monkeypatch.setattr(asyncio, "create_subprocess_exec", spawn)
        profile = RemoteProfile(name="Test", host="fixture.test")
        tunnel = await open_tunnel(profile, port)
        proxy = await RemoteProxy.open(tunnel, ROOT, services.tokens.instance_id)
        try:
            async with httpx.AsyncClient(trust_env=False) as client:
                yield SimpleNamespace(proxy=proxy, tunnel=tunnel, client=client, services=services,
                                      seen=seen, state=state, profile=profile, port=port)
        finally:
            state.block.set()
            await proxy.close()
            assert all(child.returncode is not None for child in children)
    finally:
        await runner.cleanup()


async def bootstrap(remote, headers=None):
    response = await remote.client.get(remote.proxy.origin + "/webui/bootstrap", headers=(
        headers or {"X-Nanobot-Auth": remote.proxy.secret}
    ))
    assert response.status_code == 200, response.text
    return response.json()


@pytest.mark.parametrize("path,cacheable", [
    ("/assets/index-AbcD1234.js", True), ("/assets/index-AbcD1234.css", True),
    ("/assets/index.js", False), ("/", False),
])
async def test_only_local_assets_are_served_and_versioned_files_cached(remote, path, cacheable):
    response = await remote.client.get(remote.proxy.origin + path)
    assert response.status_code == 200
    assert response.headers["cache-control"] == ("private, max-age=31536000, immutable" if cacheable else "no-cache")
    assert response.headers["x-nanobot-ui"] == "local"
    assert "set-cookie" not in response.headers
    assert remote.seen == []
    assert "local" in response.text.lower()


@pytest.mark.parametrize("path", ["/assets/remote-only-AbcD1234.js", "/auth/callback", "/missing",
    "/assets/%2e%2e/config.json", "/assets/%2e%2e/%2e%2e/config.json", "/assets/foo%5cbar.js"])
async def test_missing_local_files_never_fall_back_to_remote_html_or_code(remote, path):
    assert (await remote.client.get(remote.proxy.origin + path)).status_code == 404
    assert remote.seen == []


async def test_static_symlink_cannot_escape_local_bundle(remote, tmp_path):
    outside = tmp_path / "private.js"
    outside.write_text("not a UI asset", encoding="utf-8")
    link = remote.proxy.assets.directory / "assets" / "escape.js"
    try:
        link.symlink_to(outside)
    except OSError:
        pytest.skip("This platform does not permit unprivileged symlinks")
    assert (await remote.client.get(remote.proxy.origin + "/assets/escape.js")).status_code == 404
    assert remote.seen == []


async def test_compressed_sibling_cannot_escape_local_bundle(remote, tmp_path):
    outside = tmp_path / "private.gz"
    outside.write_bytes(b"not a UI asset")
    link = remote.proxy.assets.directory / "assets" / "index.js.gz"
    try:
        link.symlink_to(outside)
    except OSError:
        pytest.skip("This platform does not permit unprivileged symlinks")
    response = await remote.client.get(remote.proxy.origin + "/assets/index.js", headers={
        "Accept-Encoding": "gzip",
    })
    assert response.status_code == 404
    assert remote.seen == []


@pytest.mark.parametrize("contract,error", [
    (None, "webui_compatibility_unknown"),
    ({**webui_contract(), "min_protocol": 2, "max_protocol": 2}, "client_update_required"),
    ({**webui_contract(), "capabilities": []}, "host_update_required"),
])
async def test_bootstrap_rechecks_contract_before_issuing_local_credentials(remote, contract, error):
    remote.state.contract = contract
    response = await remote.client.get(remote.proxy.origin + "/webui/bootstrap",
                                       headers={"X-Nanobot-Auth": remote.proxy.secret})
    assert response.status_code == 409
    assert response.json()["error"] == error
    assert "token" not in response.json() and ROOT not in response.text
    assert not remote.proxy._api and not remote.proxy._ws


async def test_remote_credentials_never_leave_the_backend(remote):
    first, second = await asyncio.gather(bootstrap(remote), bootstrap(remote))
    assert first["token"] != second["token"]
    for issued in (first, second):
        assert ROOT not in json.dumps(issued)
        assert issued["token"] not in remote.services.tokens.issued_tokens
        assert issued["api_token"] not in remote.services.tokens.api_tokens
        assert issued["ws_url"].startswith(f"ws://127.0.0.1:{remote.proxy.port}/remote-session/")
        response = await remote.client.get(remote.proxy.origin + "/api/fixture", headers={
            "Authorization": "Bearer " + issued["api_token"], "Cookie": "injected=1",
            "X-Forwarded-User": "admin", "X-Forwarded-Host": "evil.test",
        })
        assert response.status_code == 200
        assert MEDIA not in response.text and ROOT not in response.text
        assert "set-cookie" not in response.headers
        request = remote.seen[-1]
        # The proxy replaces the browser's cookie with its own session cookie.
        # The browser-supplied ``injected=1`` value must never reach upstream,
        # and other forwarded-user/host headers must not be reflected either.
        assert request.headers.get("Cookie") == f"percival_session={remote.proxy._session_cookie}"
        assert "injected" not in request.headers.get("Cookie", "")
        assert request.headers.get("X-Forwarded-User") is None
        assert request.headers.get("X-Forwarded-Host") is None
        # The legacy shared-secret bootstrap header is no longer used; the
        # proxy must not forward its old self-issued secret (nor any other
        # proxy-side token) to the upstream gateway.
        assert request.headers.get("X-Nanobot-Auth") is None
        assert request.headers["Authorization"] != "Bearer " + issued["api_token"]


@pytest.mark.parametrize("query", ["?token={token}&token=evil", "?%74oken={token}&token=evil"])
async def test_ambiguous_auth_aliases_are_rejected(remote, query):
    issued = await bootstrap(remote)
    response = await remote.client.get(remote.proxy.origin + "/api/fixture" + query.format(token=issued["api_token"]))
    assert response.status_code == 401


async def test_encoded_query_auth_and_case_insensitive_bearer(remote):
    issued = await bootstrap(remote, {"authorization": "bearer " + remote.proxy.secret})
    response = await remote.client.get(remote.proxy.origin + "/api/fixture?%74oken=" + issued["api_token"])
    assert response.status_code == 200
    assert "token=" not in remote.seen[-1].path
    response = await remote.client.get(remote.proxy.origin + "/api/fixture?token=" + issued["api_token"],
                                       headers={"Authorization": "Bearer " + issued["api_token"]})
    assert response.status_code == 401


@pytest.mark.parametrize("headers", [
    {"Host": "evil.test"}, {"Origin": "https://evil.test"}, {"Origin": "null"},
])
async def test_foreign_browser_origin_rejected_even_with_local_secret(remote, headers):
    response = await remote.client.get(remote.proxy.origin + "/webui/bootstrap", headers={
        "X-Nanobot-Auth": remote.proxy.secret, **headers,
    })
    assert response.status_code == 403
    assert remote.seen == []


async def test_custom_ws_path_multiple_tabs_and_binary_upload(remote):
    issued = await bootstrap(remote)
    url = issued["ws_url"] + "?token=" + issued["token"] + "&client_id=original-tab"
    async with connect(url, proxy=None, origin=remote.proxy.origin, max_size=64 * 1024 * 1024) as ws:
        ready = json.loads(await ws.recv())
        assert ready["query"] == ["original-tab"]
        assert ready["media"].startswith("/api/media/local/")
        binary = bytes(range(256)) * 8192
        await ws.send(binary)
        assert await ws.recv() == binary
        await ws.send(json.dumps({"text": "normal message", "nested": [1, 2]}))
        assert json.loads(await ws.recv())["text"] == "normal message"
        with pytest.raises(InvalidStatus) as rejected:
            async with connect(url, proxy=None):
                pass
        assert rejected.value.response.status_code == 401
        second = await bootstrap(remote)
        async with connect(second["ws_url"] + "?token=" + second["token"], proxy=None) as other:
            assert json.loads(await other.recv())["ready"] is True


async def test_signed_media_wrapped_over_http_and_websocket_and_range_preserved(remote):
    issued = await bootstrap(remote)
    response = await remote.client.get(remote.proxy.origin + "/api/fixture", headers={
        "Authorization": "Bearer " + issued["api_token"],
    })
    local = response.json()["text"].split("(")[1][:-1]
    async with connect(issued["ws_url"] + "?token=" + issued["token"], proxy=None) as ws:
        assert json.loads(await ws.recv())["media"] == local
    response = await remote.client.get(remote.proxy.origin + local, headers={"Range": "bytes=0-4"})
    assert response.status_code == 206 and response.content == b"bytes"
    assert response.headers["content-range"] == "bytes 0-4/10"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["content-security-policy"].startswith("sandbox;")
    assert "allow-scripts" not in response.headers["content-security-policy"]
    assert remote.seen[-1].headers["Range"] == "bytes=0-4"
    assert (await remote.client.get(remote.proxy.origin + MEDIA)).status_code == 401


async def test_http_and_websocket_redirects_cannot_disclose_credentials(remote):
    response = await remote.client.get(remote.proxy.origin + "/redirect")
    assert response.status_code == 404
    assert ROOT not in response.text and "location" not in response.headers
    assert "set-cookie" not in response.headers
    remote.state.ws_redirect = True
    issued = await bootstrap(remote)
    with pytest.raises(InvalidStatus) as rejected:
        async with connect(issued["ws_url"] + "?token=" + issued["token"], proxy=None):
            pass
    assert rejected.value.response.status_code == 502


async def test_pause_keeps_origin_and_revokes_grants_but_allows_renewal(remote):
    issued = await bootstrap(remote)
    await remote.proxy.pause()
    with socket.socket() as competitor:
        competitor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        with pytest.raises(OSError):
            competitor.bind(("127.0.0.1", remote.proxy.port))
            competitor.listen()
    assert (await remote.client.get(remote.proxy.origin + "/")).status_code == 503
    remote.tunnel.resume(remote.profile, remote.port, None)
    remote.proxy.resume(ROOT, remote.services.tokens.instance_id)
    assert (await remote.client.get(remote.proxy.origin + "/api/fixture", headers={
        "Authorization": "Bearer " + issued["api_token"],
    })).status_code == 401
    assert (await bootstrap(remote))["ws_url"] == issued["ws_url"]


@pytest.mark.skipif(hasattr(socket, "SO_EXCLUSIVEADDRUSE"), reason="Unix immediate port takeover; Windows keeps exclusive ownership until release")
async def test_shutdown_replay_contains_only_dead_local_capabilities(remote):
    issued = await bootstrap(remote)
    origin, secret = remote.proxy.origin, remote.proxy.secret
    await remote.proxy.close()
    received = []

    async def replacement(reader, writer):
        received.append(await reader.readuntil(b"\r\n\r\n"))
        writer.write(b"HTTP/1.1 401 Unauthorized\r\nContent-Length: 0\r\nConnection: close\r\n\r\n")
        await writer.drain()
        writer.close()
        await writer.wait_closed()

    # The same browser retries after the local gateway exits. The new process
    # receives credentials that the actual remote gateway cannot authenticate.
    async with await asyncio.start_server(replacement, "127.0.0.1", remote.proxy.port):
        await remote.client.get(origin + "/webui/bootstrap", headers={"X-Nanobot-Auth": secret})
        await remote.client.get(origin + "/api/fixture", headers={"Authorization": "Bearer " + issued["api_token"]})
    wire = b"".join(received).decode()
    assert ROOT not in wire
    assert not any(token in wire for token in remote.services.tokens.api_tokens)
    assert not any(token in wire for token in remote.services.tokens.issued_tokens)
    assert not remote.services.tokens.check_api_token(Request("/api/fixture", Headers({
        "Authorization": "Bearer " + issued["api_token"],
    })))


async def test_shutdown_cancels_inflight_proxy_requests_before_closing_private_origin(remote):
    issued = await bootstrap(remote)
    pending = asyncio.create_task(remote.client.get(remote.proxy.origin + "/api/block", headers={
        "Authorization": "Bearer " + issued["api_token"],
    }))
    await asyncio.wait_for(remote.state.entered.wait(), 3)
    close = remote.tunnel.close

    async def guarded_close():
        assert not remote.proxy._tasks
        await close()

    remote.tunnel.close = guarded_close
    await asyncio.wait_for(remote.proxy.close(), 5)
    await asyncio.gather(pending, return_exceptions=True)


async def test_configured_token_issuer_cannot_be_used_through_proxy(remote):
    remote.services.http.config.token_issue_path = "/assets/token"
    remote.proxy.resume(ROOT, remote.services.tokens.instance_id, "/assets/token")
    issued = await bootstrap(remote)
    for path in ("/assets/token", "/assets/token/", "/assets/token?token=" + issued["api_token"]):
        response = await remote.client.get(remote.proxy.origin + path, headers={"X-Nanobot-Auth": remote.proxy.secret})
        assert response.status_code == 403
    remote.services.http.config.token_issue_path = "/webui/bootstrap"
    assert (await remote.client.get(remote.proxy.origin + "/webui/bootstrap", headers={
        "X-Nanobot-Auth": remote.proxy.secret,
    })).status_code == 502


async def test_expired_local_tokens_fail_and_renewal_recovers(remote):
    issued = await bootstrap(remote)
    for grants, token in ((remote.proxy._api, issued["api_token"]), (remote.proxy._ws, issued["token"])):
        grants[token] = replace(grants[token], expires=time.monotonic() - 1)
    assert (await remote.client.get(remote.proxy.origin + "/api/fixture", headers={
        "Authorization": "Bearer " + issued["api_token"],
    })).status_code == 401
    with pytest.raises(InvalidStatus) as rejected:
        async with connect(issued["ws_url"] + "?token=" + issued["token"], proxy=None):
            pass
    assert rejected.value.response.status_code == 401
    renewed = await bootstrap(remote)
    assert (await remote.client.get(remote.proxy.origin + "/api/fixture", headers={
        "Authorization": "Bearer " + renewed["api_token"],
    })).status_code == 200


async def test_local_restart_rejects_all_old_credentials_and_changes_cache_scope(remote):
    issued = await bootstrap(remote)
    secret, port = remote.proxy.secret, remote.proxy.port
    await remote.proxy.close()
    tunnel = await open_tunnel(remote.profile, remote.port)
    # A new origin also works on Windows while its old exclusive socket lingers.
    remote.proxy = await RemoteProxy.open(tunnel, ROOT, remote.services.tokens.instance_id,
                                          excluded_ports={port})
    try:
        assert (await remote.client.get(remote.proxy.origin + "/webui/bootstrap", headers={
            "X-Nanobot-Auth": secret,
        })).status_code == 401
        assert (await remote.client.get(remote.proxy.origin + "/api/fixture", headers={
            "Authorization": "Bearer " + issued["api_token"],
        })).status_code == 401
        renewed = await bootstrap(remote)
        assert urlsplit(renewed["ws_url"]).path != urlsplit(issued["ws_url"]).path
    finally:
        await remote.proxy.close()


async def test_remote_restart_invalidates_media_and_cache_scope(remote):
    issued = await bootstrap(remote)
    await remote.client.get(remote.proxy.origin + "/api/fixture", headers={
        "Authorization": "Bearer " + issued["api_token"],
    })
    assert remote.proxy._media_cache
    remote.proxy.resume(ROOT, "new-instance")
    assert not remote.proxy._media_cache
    assert remote.proxy._ws_path != issued["ws_path"]


@pytest.mark.parametrize("path", ["/", "/custom/%61pi"])
async def test_custom_websocket_literal_paths_are_preserved(remote, path):
    remote.services.http.config.path = path
    issued = await bootstrap(remote)
    async with connect(issued["ws_url"] + "?token=" + issued["token"], proxy=None) as ws:
        assert json.loads(await ws.recv())["ready"] is True
    assert any(urlsplit(request.path).path == path for request in remote.seen)


@pytest.mark.parametrize("prefix", ["https://images.example", "//cdn.example", "file:///tmp"])
async def test_external_media_like_urls_remain_unchanged(remote, prefix):
    external = prefix + MEDIA
    text = f"![external]({external}) and ![local]({MEDIA})"
    rewritten = remote.proxy._rewrite(text)
    assert external in rewritten
    assert rewritten.count("/api/media/local/") == 1
    assert len(remote.proxy._media_cache) == 1


async def test_media_cache_eviction_preserves_old_links_and_new_media(remote):
    first = remote.proxy._rewrite(MEDIA)
    for index in range(10001):
        remote.proxy._rewrite(f"/api/media/BBBBBBBBBBBBBBBBBBBBBB/{index}")
    assert len(remote.proxy._media_cache) == 10000
    assert MEDIA not in remote.proxy._media_cache
    assert (await remote.client.get(remote.proxy.origin + first)).status_code == 206
    latest = remote.proxy._rewrite(MEDIA)
    assert (await remote.client.get(remote.proxy.origin + latest)).status_code == 206
    assert MEDIA.encode() not in base64.urlsafe_b64decode(first.rsplit("/", 1)[1])
    await remote.proxy.pause()
    remote.tunnel.resume(remote.profile, remote.port, None)
    remote.proxy.resume(ROOT, remote.services.tokens.instance_id)
    assert (await remote.client.get(remote.proxy.origin + first)).status_code == 206


async def test_media_capabilities_reject_tampering_and_other_proxy_keys(remote):
    local = remote.proxy._rewrite(MEDIA)
    prefix, token = local.rsplit("/", 1)
    ciphertext = bytearray(base64.urlsafe_b64decode(token))
    ciphertext[40] ^= 1
    tampered = prefix + "/" + base64.urlsafe_b64encode(ciphertext).decode()
    assert (await remote.client.get(remote.proxy.origin + tampered)).status_code == 401
    remote.proxy.resume(ROOT, "replacement-gateway")
    assert (await remote.client.get(remote.proxy.origin + local)).status_code == 401
