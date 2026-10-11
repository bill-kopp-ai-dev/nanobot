"""WebSocket helper to drive the WebUI's settings.mcp_docker.* mutations.

Mutating actions go over the authenticated WebSocket using the WS token.
Read-only `list` uses the HTTP endpoint with the API token (bearer). Elevation is performed by the helper over the
``/auth/elevate`` endpoint with the same single instance password before
each mutation.

Usage:
    uv run --no-sync --frozen python helpers/deploy_mcp.py \\
        install agentmail '{"type":"local-image","reference":"sha256:..."}'
    uv run --no-sync --frozen python helpers/deploy_mcp.py \\
        list
"""

from __future__ import annotations

import argparse
import asyncio
import getpass
import json
import sys
import urllib.error
import urllib.request
import uuid
from typing import Any

import websockets

READ_ONLY = {"list"}


async def _login(http_base: str, password: str) -> tuple[str, str]:
    """Login and return (session_id, csrf_token)."""
    request = urllib.request.Request(
        f"{http_base}/auth/login",
        data=json.dumps({"password": password}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as resp:
            return _read_session_cookies(resp), json.load(resp)["csrf_token"]
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"login failed: HTTP {e.code}: {body}") from e


def _read_session_cookies(response: Any) -> str:
    sid = ""
    for raw_header in response.headers.get_all("Set-Cookie") or []:
        for segment in raw_header.split(";"):
            name_value = segment.strip()
            if name_value.startswith("percival_session="):
                sid = name_value.split("=", 1)[1]
                break
    if not sid:
        raise RuntimeError("login response missing percival_session cookie")
    return sid


async def _elevate(http_base: str, session_id: str, csrf: str, password: str) -> None:
    request = urllib.request.Request(
        f"{http_base}/auth/elevate",
        data=json.dumps({"password": password}).encode(),
        headers={
            "Content-Type": "application/json",
            "Cookie": f"percival_session={session_id}; percival_csrf={csrf}",
            "X-Percival-CSRF": csrf,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as resp:
            resp.read()
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"elevation failed: HTTP {e.code}: {body}") from e


async def _bootstrap(http_base: str, session_id: str) -> tuple[str, str]:
    request = urllib.request.Request(
        f"{http_base}/webui/bootstrap",
        headers={"Cookie": f"percival_session={session_id}"},
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as resp:
            payload = json.load(resp)
            return payload["token"], payload.get("api_token", "")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"bootstrap failed: HTTP {e.code}: {body}") from e


async def call_mutation(ws: websockets.WebSocketClientProtocol, action: str, payload: dict[str, Any]) -> dict[str, Any]:
    request_id = f"req-{uuid.uuid4().hex}"
    frame = {"type": "webui_request", "request_id": request_id, "action": action, "payload": payload}
    await ws.send(json.dumps(frame))
    while True:
        raw = await ws.recv()
        try:
            msg = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if not isinstance(msg, dict):
            continue
        if msg.get("event") == "webui_response" and msg.get("request_id") == request_id:
            ok = msg.get("ok", True)
            if not ok:
                err = msg.get("error") or {}
                raise RuntimeError(f"action {action} failed: HTTP {err.get('status', '?')}: {err.get('message', '?')}")
            return msg.get("payload", {})


def call_read_only(http_base: str, api_token: str, action: str) -> dict[str, Any]:
    url = f"{http_base}/api/settings/mcp-docker/{action}"
    req = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {api_token}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"action {action} -> HTTP {e.code}: {body}") from e


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ws", default="ws://127.0.0.1:8765/")
    parser.add_argument("--http", default="http://127.0.0.1:8765")
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("action")
    parser.add_argument("args", nargs="*", help="server_id, then optional JSON payload string(s)")
    args = parser.parse_args()

    password = getpass.getpass("Percival instance password: ")

    session_id, csrf = await _login(args.http, password)
    ws_token, api_token = await _bootstrap(args.http, session_id)

    if args.action in READ_ONLY:
        result = call_read_only(args.http, api_token, args.action)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0

    await _elevate(args.http, session_id, csrf, password)
    payload: dict[str, Any] = {}
    if not args.args:
        raise SystemExit(f"action {args.action} requires at least a server_id")
    payload["server_id"] = args.args[0]
    for chunk in args.args[1:]:
        payload.update(json.loads(chunk))

    action = f"settings.mcp_docker.{args.action.replace('-', '_')}"
    url = f"{args.ws}?token={ws_token}"
    async with websockets.connect(url, open_timeout=args.timeout, close_timeout=args.timeout) as ws:
        result = await call_mutation(ws, action, payload)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
