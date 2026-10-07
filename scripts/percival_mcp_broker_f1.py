#!/usr/bin/env python3
"""Disposable F1 broker: typed Docker actions and a stateless HTTP MCP bridge.

Not a production implementation. Requires an isolated test environment; the
broker alone has Docker access. Its state is reconstructed by the F1 driver.
"""

from __future__ import annotations

import argparse
import hmac
import http.server
import json
import os
import re
import select
import subprocess
import sys
import threading
from typing import Any

DOCKER = "/usr/bin/docker"
IMAGE_ID = re.compile(r"sha256:[0-9a-f]{64}\Z")
PINNED = re.compile(r"[a-z0-9][a-z0-9._:/-]{0,199}@sha256:[0-9a-f]{64}\Z")
SERVER_ID = re.compile(r"[a-z][a-z0-9-]{0,39}\Z")
PROTOCOL = "2025-03-26"
SERVERS: dict[str, dict[str, Any]] = {}
LOCK = threading.RLock()
ACTIONS = {"install", "list", "configure", "disable-tool", "enable-tool",
           "activate", "deactivate", "update-image", "restart",
           "start", "stop", "exclude"}
ACTION_FIELDS = {
    "install": {"image", "persistent", "env"},
    "configure": {"host_access"},
    "disable-tool": {"tool"}, "enable-tool": {"tool"},
    "update-image": {"image"}, "exclude": {"expected_confirmation"},
}
ALLOWED_ENV_KEYS = {"USER_AGENT", "FROM_HEADER"}
MCP_METHODS = {"initialize", "tools/list", "tools/call"}


def docker(*args: str, timeout: int = 25) -> str:
    result = subprocess.run([DOCKER, *args], text=True, capture_output=True, timeout=timeout, check=False)
    if result.returncode:
        raise ValueError(f"Docker operation failed ({result.returncode}): {result.stderr[-300:]}")
    return result.stdout.strip()


def inspect_image(image: str) -> str:
    if not isinstance(image, str):
        raise ValueError("image must be a local sha256: ID or pinned name@sha256: RepoDigest")
    normalized = image.lower()
    if not (IMAGE_ID.fullmatch(normalized) or PINNED.fullmatch(normalized)):
        raise ValueError("image must be a local sha256: ID or pinned name@sha256: RepoDigest")
    raw = docker("image", "inspect",
                 "--format", "{{.Id}}\t{{range .RepoDigests}}{{.}}|{{end}}",
                 normalized)
    parts = raw.split("\t", 1)
    if len(parts) != 2:
        raise ValueError("docker image inspect returned unexpected format")
    actual_id = parts[0]
    digests = [token for token in parts[1].split("|") if token]
    if "@" in normalized:
        if normalized not in digests:
            raise ValueError("pinned image reference is not in local RepoDigests")
        return normalized
    if actual_id != normalized:
        raise ValueError("image ID mismatch")
    return normalized


def container_name(server_id: str) -> str:
    if not isinstance(server_id, str) or SERVER_ID.fullmatch(server_id) is None:
        raise ValueError("invalid server_id")
    return f"percival-f1-{server_id}"


def container_running(server_id: str) -> bool:
    try:
        return docker("inspect", "--format", "{{.State.Running}}", container_name(server_id)) == "true"
    except ValueError:
        return False


def spawn(server_id: str, state: dict[str, Any]) -> None:
    image = inspect_image(state["image"])
    name = container_name(server_id)
    root_mount = "type=bind,src=/,dst=/host,bind-recursive=disabled"
    if not state.get("host_access", True):
        root_mount += ",readonly"
    args = ["run", "-d", "-i", "--pull=never", "--name", name,
            "--label", "percival-f1=1", "--network=none", "--cap-drop=ALL",
            "--security-opt=no-new-privileges", "--mount", root_mount]
    # The local host has /home on a distinct btrfs submount. Include it
    # explicitly before covering state and Docker credential paths. This is a
    # local experiment, not a generic or configurable host-mount policy.
    if os.environ["F1_HOME_SUBMOUNT"] != "/home":
        raise ValueError("F1 requires the verified /home submount")
    home_mount = "type=bind,src=/home,dst=/host/home,bind-recursive=disabled"
    if not state.get("host_access", True):
        home_mount += ",readonly"
    args += ["--mount", home_mount]
    # Fail closed when mandatory covers are absent or malformed.
    for path in (os.environ["F1_DOCKER_ROOT"], os.environ["F1_PERSIST_ROOT"],
                 "/home/bill/.docker", "/home/bill/.nanobot"):
        if not path.startswith("/") or path == "/" or os.path.normpath(path) != path:
            raise ValueError("protected host path is not a normalized absolute directory")
        args += ["--tmpfs", f"/host{path}:rw,noexec,nosuid,nodev,mode=0700"]
    for key, value in sorted(state.get("env", {}).items()):
        if key not in ALLOWED_ENV_KEYS or not isinstance(value, str):
            raise ValueError("only the two non-secret OSM fixture env fields are allowed in F1")
        args += ["-e", f"{key}={value}"]
    docker(*args, image)
    if not container_running(server_id):
        raise ValueError("MCP container exited during startup")


def discover(server_id: str) -> list[str]:
    response = mcp_roundtrip(server_id, {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
    tools = response.get("result", {}).get("tools", [])
    if not isinstance(tools, list) or not tools:
        raise ValueError("MCP discovery returned no tools")
    return [tool["name"] for tool in tools]


def remove(server_id: str) -> None:
    docker("rm", "-f", container_name(server_id))


def remove_if_present(server_id: str) -> None:
    try:
        remove(server_id)
    except ValueError as exc:
        if "No such container" not in str(exc):
            raise


def mcp_roundtrip(server_id: str, request: dict[str, Any]) -> dict[str, Any]:
    """Attach to the *running* fixture and transact JSON-RPC over its stdio.

    Each HTTP request attaches afresh and initializes the same process. This
    prototype is deliberately serialized and has no crash/session recovery.
    """
    if not container_running(server_id):
        raise ValueError("server not running")
    proc = subprocess.Popen(
        [DOCKER, "attach", "--sig-proxy=false", container_name(server_id)],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
        text=True, bufsize=1,
    )

    def exchange(msg: dict[str, Any]) -> dict[str, Any]:
        if proc.stdin is None or proc.stdout is None:
            raise ValueError("MCP stdio not connected")
        try:
            proc.stdin.write(json.dumps(msg, separators=(",", ":")) + "\n")
            proc.stdin.flush()
        except OSError as exc:
            raise ValueError(f"MCP stdio write failed: {exc}") from exc
        readable, _, _ = select.select([proc.stdout], [], [], 18)
        if not readable:
            raise TimeoutError("MCP stdio response timed out")
        raw = proc.stdout.readline()
        if not raw:
            raise ValueError("MCP stdio closed")
        return json.loads(raw)

    try:
        handshake = exchange({"jsonrpc": "2.0", "id": -1, "method": "initialize", "params": {
            "protocolVersion": PROTOCOL, "capabilities": {}, "clientInfo": {"name": "percival-f1", "version": "0.1"},
        }})
        if "result" not in handshake:
            raise ValueError("MCP initialization failed")
        try:
            proc.stdin.write('{"jsonrpc":"2.0","method":"notifications/initialized"}\n')
            proc.stdin.flush()
        except OSError as exc:
            raise ValueError(f"MCP stdio notification failed: {exc}") from exc
        if request["method"] == "initialize":
            return {"jsonrpc": "2.0", "id": request.get("id"), "result": handshake["result"]}
        return exchange(request)
    finally:
        # Killing the attach CLI does not stop the underlying container.
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


def action(op: str, payload: dict[str, Any]) -> dict[str, Any]:
    server_id = payload.get("server_id")
    if not isinstance(server_id, str) or not SERVER_ID.fullmatch(server_id):
        raise ValueError("invalid server_id")
    name = container_name(server_id)
    extra_fields = ACTION_FIELDS.get(op, set())
    if set(payload) - ({"server_id"} | extra_fields):
        raise ValueError("unsupported action fields (custom mounts/networks/flags cannot override protections)")
    state = SERVERS.get(server_id)
    if op == "install":
        if state is not None:
            raise ValueError("server already installed")
        image = inspect_image(payload.get("image"))
        new = {"image": image, "source": payload["image"], "active": True,
               "persistent": payload.get("persistent") is True,
               "toolsDisabled": [], "host_access": True, "env": payload.get("env", {})}
        try:
            spawn(server_id, new)
            discover(server_id)
        except (ValueError, TimeoutError, subprocess.TimeoutExpired):
            remove_if_present(server_id)
            raise
        SERVERS[server_id] = new
        return {"image": image, "running": True}
    if state is None:
        raise ValueError("unknown server_id")
    if op == "list":
        return {"state": state, "running": container_running(server_id)}
    if op == "configure":
        new = {**state, "host_access": payload.get("host_access") is True}
        if container_running(server_id):
            remove(server_id)
            try:
                spawn(server_id, new)
                discover(server_id)
            except (ValueError, TimeoutError, subprocess.TimeoutExpired):
                remove_if_present(server_id)
                spawn(server_id, state)
                raise
        SERVERS[server_id] = new
        return {"host_access": new["host_access"]}
    if op in {"disable-tool", "enable-tool"}:
        tool = payload.get("tool")
        if not isinstance(tool, str) or not tool:
            raise ValueError("tool must be a nonempty string")
        disabled = set(state["toolsDisabled"])
        (disabled.add if op == "disable-tool" else disabled.discard)(tool)
        state["toolsDisabled"] = sorted(disabled)
        return {"toolsDisabled": state["toolsDisabled"]}
    if op in {"activate", "deactivate"}:
        state["active"] = op == "activate"
        if not state["active"] and container_running(server_id):
            remove(server_id)
        if state["active"] and not container_running(server_id):
            spawn(server_id, state)
            discover(server_id)
        return {"active": state["active"]}
    if op == "restart":
        if not state["active"]:
            raise ValueError("server disabled")
        remove(server_id)
        spawn(server_id, state)
        discover(server_id)
        return {"running": True}
    if op == "update-image":
        next_image = inspect_image(payload.get("image"))
        old = dict(state)
        if container_running(server_id):
            remove(server_id)
        try:
            new = {**state, "image": next_image, "source": payload["image"]}
            if state["active"]:
                spawn(server_id, new)
                discovered = discover(server_id)
                new["toolsDisabled"] = sorted(set(state["toolsDisabled"]) & set(discovered))
            SERVERS[server_id] = new
        except (ValueError, TimeoutError, subprocess.TimeoutExpired):
            remove_if_present(server_id)
            if old["active"]:
                spawn(server_id, old)
                discover(server_id)
            SERVERS[server_id] = old
            raise
        return {"image": next_image}
    if op == "stop":
        if not state["persistent"]:
            raise ValueError("start/stop requires persistent=true")
        if container_running(server_id):
            remove(server_id)
        return {"running": False}
    if op == "start":
        if not state["persistent"] or not state["active"]:
            raise ValueError("start requires persistent=true and active")
        if not container_running(server_id):
            spawn(server_id, state)
            discover(server_id)
        return {"running": True}
    if op == "exclude":
        if payload.get("expected_confirmation") != server_id:
            raise ValueError("confirmation must equal server_id")
        if container_running(server_id):
            remove(server_id)
        del SERVERS[server_id]
        return {"excluded": name}
    raise ValueError("unknown action")


class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
        # Do not log request bodies, authentication headers or MCP payloads.
        # BaseHTTPRequestHandler passes client IP + path, which is fine.
        pass

    def send(self, code: int, result: dict[str, Any]) -> None:
        content = json.dumps(result).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def authorized(self) -> bool:
        auth = self.headers.get("Authorization", "")
        token = getattr(self.server, "token", "")
        return bool(token) and hmac.compare_digest(
            auth.encode("utf-8"), ("Bearer " + token).encode("utf-8")
        )

    def _parse_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0") or "0")
        if length <= 0 or length > 32768:
            raise ValueError("invalid payload size")
        try:
            data = json.loads(self.rfile.read(length).decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid json: {exc.msg}") from exc
        if not isinstance(data, dict):
            raise ValueError("payload must be an object")
        return data

    def do_POST(self) -> None:  # noqa: N802
        # Authorize before reading the body to avoid logging/shape leaks.
        if not self.authorized():
            self.send(401, {"error": "unauthorized"})
            return
        try:
            payload = self._parse_json()
        except ValueError as exc:
            self.send(400, {"error": str(exc)})
            return
        try:
            with LOCK:
                if self.path == "/mcp":
                    server_id = payload.get("server_id")
                    if not isinstance(server_id, str) or not SERVER_ID.fullmatch(server_id):
                        raise ValueError("server_id is required in payload for legacy /mcp route")
                    path = f"/mcp/{server_id}"
                elif self.path.startswith("/mcp/"):
                    server_id = self.path.removeprefix("/mcp/")
                    if not SERVER_ID.fullmatch(server_id):
                        self.send(404, {"error": "not found"})
                        return
                    path = self.path
                else:
                    path = None
                if path is not None:
                    method = payload.get("method")
                    state = SERVERS.get(server_id)
                    if not state or not state["active"] or not container_running(server_id):
                        raise ValueError("server unavailable")
                    if method == "notifications/initialized" and path != "/mcp":
                        self.send_response(202)
                        self.send_header("Content-Length", "0")
                        self.end_headers()
                        return
                    if method not in MCP_METHODS and method != "notifications/initialized":
                        raise ValueError("unsupported MCP method")
                    if method == "tools/call" and payload.get("params", {}).get("name") in state["toolsDisabled"]:
                        raise ValueError("tool disabled")
                    result = mcp_roundtrip(server_id, {k: v for k, v in payload.items() if k != "server_id"})
                    if method == "tools/list" and isinstance(result.get("result"), dict):
                        result["result"]["tools"] = [
                            t for t in result["result"]["tools"] if t["name"] not in state["toolsDisabled"]
                        ]
                elif self.path.startswith("/v1/"):
                    op = self.path.removeprefix("/v1/")
                    if op not in ACTIONS:
                        self.send(404, {"error": "not found"})
                        return
                    result = action(op, payload)
                else:
                    self.send(404, {"error": "not found"})
                    return
            self.send(200, result)
        except (ValueError, KeyError, TypeError, TimeoutError, subprocess.TimeoutExpired) as exc:
            self.send(409, {"error": str(exc)})


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=18081)
    args = parser.parse_args()
    if args.port < 1 or args.port > 65535:
        print("port must be in [1, 65535]", file=sys.stderr)
        return 2
    token = os.environ.get("F1_BROKER_TOKEN", "")
    if len(token) < 32:
        print("broker token must have at least 32 characters", file=sys.stderr)
        return 2
    # Validate actual daemon access before admitting requests.
    try:
        docker("version", "--format", "{{.Client.Version}} {{.Server.Version}}")
    except ValueError as exc:
        print(f"Docker daemon unreachable: {exc}", file=sys.stderr)
        return 1
    server = http.server.ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    server.token = token  # type: ignore[attr-defined]
    print("f1 broker ready", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
