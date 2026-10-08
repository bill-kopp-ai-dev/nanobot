"""WebSocket helper to drive the WebUI's settings.mcp_docker.* mutations.

Mutating actions go over the authenticated WebSocket using the WS token.
Read-only actions (`list`, `operator-bootstrap`) use the HTTP endpoint
with the api_token (bearer).

Usage:
    uv run --no-sync --frozen python helpers/deploy_mcp.py \\
        --ws-token <ws_token> \\
        --api-token <api_token> \\
        --operator-password <password> \\
        install agentmail '{"type":"local-image","reference":"sha256:..."}'
        configure agentmail '{...}'
        activate agentmail
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import urllib.error
import urllib.request
import uuid
from typing import Any

import websockets

READ_ONLY = {"list", "operator-bootstrap"}


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
        # Skip chat events, progress, etc.


def call_read_only(http_base: str, api_token: str, action: str) -> dict[str, Any]:
    url = f"{http_base}/api/settings/mcp-docker/{action}"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {api_token}"})
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
    parser.add_argument("--ws-token", required=True, help="bootstrap-issued WebUI WS token")
    parser.add_argument("--api-token", required=True, help="bootstrap-issued API bearer token")
    parser.add_argument("--operator-password", required=True, help="operator credential for mutating actions")
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("action")
    parser.add_argument("args", nargs="*", help="server_id, then optional JSON payload string(s)")
    args = parser.parse_args()

    if args.action in READ_ONLY:
        result = call_read_only(args.http, args.api_token, args.action)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0

    payload: dict[str, Any] = {"operator_admin": args.operator_password}
    if not args.args:
        raise SystemExit(f"action {args.action} requires at least a server_id")
    payload["server_id"] = args.args[0]
    for chunk in args.args[1:]:
        payload.update(json.loads(chunk))

    action = f"settings.mcp_docker.{args.action.replace('-', '_')}"
    url = f"{args.ws}?token={args.ws_token}"
    async with websockets.connect(url, open_timeout=args.timeout, close_timeout=args.timeout) as ws:
        result = await call_mutation(ws, action, payload)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
