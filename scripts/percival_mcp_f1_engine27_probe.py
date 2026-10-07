#!/usr/bin/env python3
"""Exercise both pinned F1 fixture sources through a disposable 27.x daemon."""

from __future__ import annotations

import json
import select
import subprocess

DAEMON = "percival-f1-engine27"
MOUNTS = ["--mount", "type=bind,src=/,dst=/host,bind-recursive=disabled",
          "--tmpfs", "/host/run:rw,noexec,nosuid,nodev,mode=0700",
          "--tmpfs", "/host/var/lib/docker:rw,noexec,nosuid,nodev,mode=0700"]


def test_fixture(image: str, tool: str, args: dict, expected_count: int, env: list[str]) -> None:
    command = ["docker", "exec", "-i", DAEMON, "docker", "run", "--rm", "-i",
               "--pull=never", "--network=none", "--cap-drop=ALL",
               "--security-opt=no-new-privileges", *MOUNTS, *env, image]
    proc = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, text=True, bufsize=1)

    def rpc(method: str, parameters: dict, identifier: int) -> dict:
        if proc.stdin is None or proc.stdout is None:
            raise AssertionError("stdio not connected")
        try:
            proc.stdin.write(json.dumps({"jsonrpc": "2.0", "id": identifier,
                                         "method": method, "params": parameters}) + "\n")
            proc.stdin.flush()
        except OSError as exc:
            raise AssertionError(f"{image} MCP {method} write failed: {exc}") from exc
        readable, _, _ = select.select([proc.stdout], [], [], 20)
        if not readable:
            raise AssertionError(f"{image} MCP {method} timeout")
        raw = proc.stdout.readline()
        if not raw:
            raise AssertionError(f"{image} MCP {method} closed")
        response = json.loads(raw)
        assert response.get("id") == identifier and "result" in response, response
        return response["result"]

    try:
        result = rpc("initialize", {"protocolVersion": "2025-03-26", "capabilities": {},
                                     "clientInfo": {"name": "percival-f1-engine27", "version": "0.1"}}, 1)
        assert result["serverInfo"]["name"]
        if proc.stdin is None:
            raise AssertionError("stdio disconnected during handshake")
        try:
            proc.stdin.write('{"jsonrpc":"2.0","method":"notifications/initialized"}\n')
            proc.stdin.flush()
        except OSError as exc:
            raise AssertionError(f"notifications/initialized write failed: {exc}") from exc
        tools = rpc("tools/list", {}, 2)["tools"]
        assert len(tools) >= expected_count and tool in {item["name"] for item in tools}
        called = rpc("tools/call", {"name": tool, "arguments": args}, 3)
        assert not called.get("isError"), called
        print(f"Engine 27.5.1 {image}: {len(tools)} tools, {tool} ok")
    finally:
        try:
            if proc.stdin and not proc.stdin.closed:
                proc.stdin.close()
        except OSError:
            pass
        try:
            proc.kill()
        finally:
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                pass


if __name__ == "__main__":
    test_fixture("percival-f1-weather:source-b5032f4", "weather_convert_time",
                 {"datetime_str": "2026-10-07T12:00:00Z", "from_timezone": "UTC",
                  "to_timezone": "America/Sao_Paulo"}, 9, [])
    test_fixture("percival-f1-osm:source-ca3c397", "osm_get_health", {}, 30,
                 ["-e", "USER_AGENT=Percival-F1-test (local)",
                  "-e", "FROM_HEADER=local@example.invalid"])
