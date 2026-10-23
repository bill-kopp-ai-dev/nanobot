"""Offline stdio MCP fixture for core lifecycle tests (not MCP homologation)."""

import json
import sys

for line in sys.stdin:
    request = json.loads(line)
    if "id" not in request:
        continue
    method = request["method"]
    if method == "initialize":
        result = {
            "protocolVersion": "2025-03-26",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "percival-runtime-fixture", "version": "1"},
        }
    elif method == "tools/list":
        result = {"tools": [{"name": "ping", "description": "Offline fixture",
                             "inputSchema": {"type": "object", "properties": {}}}]}
    elif method == "tools/call":
        result = {"content": [{"type": "text", "text": "pong"}], "isError": False}
    else:
        raise ValueError("unsupported fixture method")
    print(json.dumps({"jsonrpc": "2.0", "id": request["id"], "result": result}), flush=True)
