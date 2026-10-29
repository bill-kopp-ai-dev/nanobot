"""Minimal stdio MCP fixture with a controllably slow tool for A-012."""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path


def respond(message_id: object, result: object) -> None:
    sys.stdout.write(json.dumps({"jsonrpc": "2.0", "id": message_id, "result": result}) + "\n")
    sys.stdout.flush()


def main() -> None:
    for line in sys.stdin:
        try:
            request = json.loads(line)
        except ValueError:
            continue
        if not isinstance(request, dict):
            continue
        method = request.get("method")
        message_id = request.get("id")
        if method == "notifications/initialized":
            continue
        if method == "initialize":
            respond(message_id, {
                "protocolVersion": "2025-03-26",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "a012-slow-fixture", "version": "0.1.0"},
            })
        elif method == "tools/list":
            respond(message_id, {"tools": [{
                "name": "delay",
                "description": "Wait for the requested bounded number of seconds.",
                "inputSchema": {
                    "type": "object",
                    "properties": {"seconds": {"type": "number"}},
                    "required": ["seconds"],
                },
            }]})
        elif method == "tools/call":
            params = request.get("params")
            arguments = params.get("arguments") if isinstance(params, dict) else None
            seconds = arguments.get("seconds") if isinstance(arguments, dict) else None
            if not isinstance(seconds, (int, float)) or not 0 <= seconds <= 20:
                respond(message_id, {"isError": True, "content": [{"type": "text", "text": "invalid seconds"}]})
                continue
            marker = os.environ.get("A012_MARKER")
            if marker:
                Path(marker).write_text("call-started\n", encoding="utf-8")
            time.sleep(seconds)
            respond(message_id, {"content": [{"type": "text", "text": "delay complete"}], "isError": False})


if __name__ == "__main__":
    main()
