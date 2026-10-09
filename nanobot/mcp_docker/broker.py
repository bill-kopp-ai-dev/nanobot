"""Socket-owning Docker MCP sidecar; no gateway config or shell execution.

Only typed endpoints are exposed on loopback. All Docker access occurs here;
the gateway container must not mount a socket or the Docker CLI.
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
import threading
from pathlib import Path
from typing import Any, cast

from pydantic import ValidationError

from nanobot.mcp_docker.contracts import SERVER_ID, DockerHostConfig, DockerImageSource
from nanobot.mcp_docker.mount_policy import MountPolicy

DOCKER = "/usr/bin/docker"
PROTOCOL = "2025-03-26"
ADMIN = frozenset({"install", "configure", "disable-tool", "enable-tool", "activate",
                   "deactivate", "update-image", "restart", "start", "stop", "exclude", "reconcile", "recover",
                   "hydrate", "status", "observe", "health"})
MCP = frozenset({"initialize", "notifications/initialized", "tools/list", "tools/call"})
_STORE: dict[str, ManagedServer] = {}
_LOCK = threading.RLock()


class BrokerError(Exception):
    def __init__(self, message: str, status: int = 409):
        self.status = status
        super().__init__(message)


class ImageMissingError(BrokerError):
    """The referenced image is not present in the local Docker image cache."""

    def __init__(self) -> None:
        super().__init__("image missing locally", 409)


def docker(*args: str, timeout: int = 35) -> str:
    try:
        result = subprocess.run([DOCKER, *args], text=True, capture_output=True,
                                timeout=timeout, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise BrokerError("Docker CLI or daemon unavailable", 503) from exc
    if result.returncode:
        # Docker stderr may contain env or host paths. Never echo it to HTTP.
        diagnostic = result.stderr.lower()
        if any(marker in diagnostic for marker in ("no such object", "no such container", "no such image")):
            raise BrokerError("Docker object not found", 404)
        raise BrokerError(f"Docker operation failed ({result.returncode})", 503)
    return result.stdout.strip()


def ready() -> MountPolicy:
    if os.environ.get("DOCKER_HOST", "unix:///var/run/docker.sock") not in {
        "unix:///var/run/docker.sock", "unix:///run/docker.sock",
    } or os.environ.get("DOCKER_BIN", DOCKER) != DOCKER:
        raise BrokerError("only the local Docker socket and /usr/bin/docker are supported", 503)
    versions = docker("version", "--format", "{{.Client.Version}}|{{.Server.Version}}")
    parts = versions.split("|")
    if len(parts) != 2 or any(re.fullmatch(r"27\.[0-9]+\.[0-9]+", version) is None for version in parts):
        # Disposable F2 smoke on a different local Engine is never a deploy
        # compatibility claim; real deployment and CI require Engine 27.x.
        if os.environ.get("PERCIVAL_DISPOSABLE_ENGINE29") != "1" or len(parts) != 2 or not (
            re.fullmatch(r"(?:27|29)\.[0-9]+\.[0-9]+", parts[0])
            and re.fullmatch(r"29\.[0-9]+\.[0-9]+", parts[1])
        ):
            raise BrokerError("Docker Client and Server 27.x required", 503)
    root = docker("info", "--format", "{{.DockerRootDir}}")
    options = docker("info", "--format", "{{json .SecurityOptions}}")
    try:
        security_options = json.loads(options)
    except ValueError as exc:
        raise BrokerError("invalid Docker info response", 503) from exc
    if not isinstance(security_options, list) or any("rootless" in str(option) for option in cast(list[object], security_options)):
        raise BrokerError("rootful Docker Engine required", 503)
    try:
        mountinfo = Path(os.environ["PERCIVAL_HOST_MOUNTINFO"]).read_text(encoding="utf-8")
        state_root = os.environ["PERCIVAL_STATE_HOST_PATH"]
        token_host = os.environ["PERCIVAL_TOKEN_HOST_PATH"]
        host_root = Path(os.environ["PERCIVAL_HOST_INVENTORY"])
        gateway_name = os.environ.get("PERCIVAL_GATEWAY_CONTAINER_NAME", "nanobot-gateway")
        gateway_data: object = json.loads(docker("inspect", gateway_name))
        if not isinstance(gateway_data, list) or len(cast(list[object], gateway_data)) != 1 or not isinstance(gateway_data[0], dict):
            raise ValueError("gateway container inspection unavailable")
        mounts: object = cast(dict[str, object], gateway_data[0]).get("Mounts")
        if not isinstance(mounts, list):
            raise ValueError("gateway state mount unavailable")
        sources = [cast(dict[str, object], m).get("Source") for m in cast(list[object], mounts)
                   if isinstance(m, dict) and cast(dict[str, object], m).get("Destination") == "/home/nanobot/.nanobot"
                   and cast(dict[str, object], m).get("Type") == "bind"]
        if len(sources) != 1 or sources[0] != state_root:
            raise ValueError("gateway state mount does not match host inventory")
        return MountPolicy(mountinfo=mountinfo, host_root=host_root, docker_root=root,
                           state_root=state_root, token_path=token_host,
                           verified_state_path=state_root)
    except (KeyError, OSError, ValueError) as exc:
        raise BrokerError("host inventory or mandatory cover unavailable", 503) from exc


def image_reference(source: DockerImageSource) -> str:
    reference = source.reference
    try:
        raw = docker("image", "inspect", "--format",
                     "{{.Id}}|{{range .RepoDigests}}{{.}}|{{end}}", reference)
    except BrokerError as exc:
        if exc.status == 404:
            raise ImageMissingError() from exc
        raise
    parts = raw.split("|")
    if (not parts or (source.type == "local-image" and parts[0] != reference) or
        (source.type == "pinned-image" and reference not in parts[1:])):
        raise BrokerError("local image identity mismatch")
    return reference


def _name(server_id: str) -> str:
    return "percival-mcp-" + server_id


def _inspect(server_id: str) -> dict[str, Any] | None:
    try:
        data: object = json.loads(docker("inspect", _name(server_id)))
    except BrokerError as exc:
        if exc.status == 404:
            return None
        raise
    if not isinstance(data, list) or len(cast(list[object], data)) != 1 or not isinstance(data[0], dict):
        raise BrokerError("invalid container inspection")
    container = cast(dict[str, Any], data[0])
    config = container.get("Config")
    labels: object = cast(dict[str, object], config).get("Labels", {}) if isinstance(config, dict) else {}
    if not isinstance(labels, dict) or cast(dict[str, object], labels).get("percival.mcp-docker.server-id") != server_id:
        raise BrokerError("container name owned by another application")
    return container


def _running(server_id: str) -> bool:
    container = _inspect(server_id)
    state = container.get("State") if container else None
    return bool(isinstance(state, dict) and cast(dict[str, object], state).get("Running") is True)


def _remove(server_id: str) -> None:
    if _inspect(server_id) is not None:
        docker("rm", "-f", _name(server_id))  # never -v


def _spawn(server: ManagedServer) -> None:
    policy = ready()  # re-read host mounts/data-root before every new container
    reference = image_reference(server.source)
    args = ["run", "-d", "-i", "--pull=never", "--name", _name(server.server_id),
            "--label", f"percival.mcp-docker.server-id={server.server_id}",
            f"--network={server.host.network}", "--cap-drop=ALL",
            "--security-opt=no-new-privileges",
            *policy.docker_args(server.host.mounts)]
    for key, entry in sorted(server.host.env.items()):
        value = entry.value
        if entry.kind == "reference":
            value = os.environ.get(value[2:-1], "")
            if not value:
                raise BrokerError("broker environment reference missing")
        args += ["-e", f"{key}={value}"]
    docker(*args, reference)
    if not _running(server.server_id):
        raise BrokerError("MCP container exited during startup")
    # Verify the daemon honored the network, the zero-bind mode and required covers.
    container = _inspect(server.server_id)
    if container is None:
        raise BrokerError("container unavailable after spawn")
    host_config = container.get("HostConfig")
    expected_network = server.host.network
    actual_network = cast(dict[str, object], host_config).get("NetworkMode") if isinstance(host_config, dict) else None
    if actual_network != expected_network:
        raise BrokerError("container network policy mismatch")
    if server.host.mounts == []:
        actual_mounts = container.get("Mounts")
        if not isinstance(actual_mounts, list) or any(
            isinstance(item, dict) and cast(dict[str, object], item).get("Type") == "bind"
            for item in cast(list[object], actual_mounts)
        ):
            raise BrokerError("minimum host access has unexpected binds")
    tmpfs = cast(dict[str, object], host_config).get("Tmpfs")
    plan = policy.docker_args(server.host.mounts)
    required_covers = [plan[i + 1].split(":", 1)[0]
                       for i, token in enumerate(plan[:-1]) if token == "--tmpfs"]
    if required_covers and (not isinstance(tmpfs, dict) or not all(
        cover in cast(dict[str, object], tmpfs) for cover in required_covers
    )):
        raise BrokerError("mandatory Docker covers not present")


def _exchange(server_id: str, request: dict[str, Any]) -> dict[str, Any]:
    if not _running(server_id):
        raise BrokerError("server not running")
    proc = subprocess.Popen([DOCKER, "attach", "--sig-proxy=false", _name(server_id)],
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.DEVNULL, text=True, bufsize=1)

    def send(message: dict[str, Any]) -> dict[str, Any]:
        if proc.stdin is None or proc.stdout is None:
            raise BrokerError("MCP transport unavailable")
        proc.stdin.write(json.dumps(message, separators=(",", ":")) + "\n")
        proc.stdin.flush()
        readable, _, _ = select.select([proc.stdout], [], [], 18)
        if not readable:
            raise BrokerError("MCP response timed out", 503)
        raw = proc.stdout.readline()
        if not raw:
            raise BrokerError("MCP server closed transport", 503)
        data: object = json.loads(raw)
        if not isinstance(data, dict):
            raise BrokerError("MCP response malformed")
        return cast(dict[str, Any], data)

    try:
        handshake = send({"jsonrpc": "2.0", "id": -1, "method": "initialize", "params": {
            "protocolVersion": PROTOCOL, "capabilities": {},
            "clientInfo": {"name": "percival-broker", "version": "0.1"},
        }})
        if "result" not in handshake:
            raise BrokerError("MCP initialize failed")
        assert proc.stdin is not None
        proc.stdin.write('{"jsonrpc":"2.0","method":"notifications/initialized"}\n')
        proc.stdin.flush()
        if request["method"] == "initialize":
            return {"jsonrpc": "2.0", "id": request.get("id"), "result": handshake["result"]}
        return send(request)
    except (OSError, ValueError) as exc:
        raise BrokerError("MCP transport failed", 503) from exc
    finally:
        if proc.stdin and not proc.stdin.closed:
            proc.stdin.close()
        proc.kill()
        proc.wait(timeout=5)


def _discover(server_id: str) -> list[str]:
    response = _exchange(server_id, {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
    result = response.get("result")
    tools: object = cast(dict[str, object], result).get("tools") if isinstance(result, dict) else None
    if not isinstance(tools, list) or not tools or any(not isinstance(item, dict) or not isinstance(cast(dict[str, object], item).get("name"), str) for item in cast(list[object], tools)):
        raise BrokerError("MCP tools/list returned no valid tools")
    return [str(cast(dict[str, object], item)["name"]) for item in cast(list[object], tools)]


def _observe(server_id: str, data: dict[str, Any]) -> dict[str, Any]:
    """Read Docker and MCP state without changing the container or broker registry."""
    try:
        source = DockerImageSource.model_validate(data["source"])
    except (KeyError, ValidationError) as exc:
        raise BrokerError("invalid observation source", 400) from exc
    try:
        image_reference(source)
    except ImageMissingError:
        return {"dockerObservation": "image-missing", "mcpConnectivity": "unknown", "tools": []}
    container = _inspect(server_id)
    if container is None:
        return {"dockerObservation": "container-missing", "mcpConnectivity": "unknown", "tools": []}
    host_config: object = container.get("HostConfig")
    raw_mounts: object = container.get("Mounts")
    network_mode: object = (
        cast(dict[str, object], host_config).get("NetworkMode")
        if isinstance(host_config, dict) else None
    )
    effective_mounts: list[dict[str, object]] = []
    if isinstance(raw_mounts, list):
        for raw_mount in cast(list[object], raw_mounts):
            if not isinstance(raw_mount, dict):
                continue
            mount = cast(dict[str, object], raw_mount)
            mount_type = mount.get("Type")
            destination = mount.get("Destination")
            if isinstance(mount_type, str) and isinstance(destination, str):
                effective_mounts.append({
                    "type": mount_type,
                    "destination": destination,
                    "readWrite": mount.get("RW") is True,
                })
    effective: dict[str, object] = {
        "network": network_mode if isinstance(network_mode, str) else "unknown",
        "mounts": effective_mounts,
    }
    state = container.get("State")
    running = isinstance(state, dict) and cast(dict[str, object], state).get("Running") is True
    if not running:
        return {"dockerObservation": "stopped", "mcpConnectivity": "disconnected", "tools": [],
                "effectiveConfiguration": effective}
    try:
        tools = _discover(server_id)
    except BrokerError:
        return {"dockerObservation": "running", "mcpConnectivity": "disconnected", "tools": [],
                "effectiveConfiguration": effective}
    return {"dockerObservation": "running", "mcpConnectivity": "connected", "tools": tools,
            "effectiveConfiguration": effective}


class ManagedServer:
    def __init__(self, server_id: str, source: DockerImageSource, host: DockerHostConfig) -> None:
        self.server_id = server_id
        self.source = source
        self.host = host
        self.active = True
        self.disabled: set[str] = set()
        self.tools: list[str] = []
        self.lock = threading.RLock()


def _managed_server_from_state(server_id: str, state: object) -> ManagedServer:
    if not isinstance(state, dict):
        raise BrokerError("invalid managed state", 400)
    values = cast(dict[str, Any], state)
    if set(values) != {"source", "configuration", "active", "tools_disabled", "tools"}:
        raise BrokerError("invalid managed state", 400)
    try:
        source = DockerImageSource.model_validate(values["source"])
        host = DockerHostConfig.model_validate(values["configuration"])
        active = values["active"]
        disabled = values["tools_disabled"]
        tools = values["tools"]
        if (type(active) is not bool or not isinstance(disabled, list) or
            not all(isinstance(name, str) for name in cast(list[object], disabled)) or
            not isinstance(tools, list) or
            not all(isinstance(name, str) for name in cast(list[object], tools))):
            raise ValueError("invalid managed state")
        disabled_names = cast(list[str], disabled)
        tool_names = cast(list[str], tools)
        if not set(disabled_names).issubset(tool_names):
            raise ValueError("disabled tools must be discovered tools")
    except (KeyError, ValidationError, ValueError) as exc:
        raise BrokerError("invalid managed state", 400) from exc
    server = ManagedServer(server_id, source, host)
    server.active = active
    server.disabled = set(disabled_names)
    server.tools = tool_names
    return server


def action(op: str, server_id: str, data: dict[str, Any]) -> dict[str, Any]:
    if op not in ADMIN or not SERVER_ID.fullmatch(server_id):
        raise BrokerError("unsupported broker action", 400)
    if op == "status":
        if data:
            raise BrokerError("unsupported broker status fields", 400)
        with _LOCK:
            return {"registered": server_id in _STORE}
    ready()
    if op == "health":
        if data:
            raise BrokerError("unsupported broker health fields", 400)
        return {"ready": True, "minimumMountsSupported": True, "supportedNetworks": ["none", "bridge"]}
    if op == "observe":
        if set(data) != {"source"}:
            raise BrokerError("unsupported observation fields", 400)
        return _observe(server_id, data)
    fields = {"install": {"source", "configuration"}, "configure": {"configuration"},
              "update-image": {"source"}, "disable-tool": {"tool"}, "enable-tool": {"tool"},
              "reconcile": {"source", "configuration", "active", "tools_disabled"},
              "recover": {"source", "configuration", "active", "tools_disabled", "running"},
              "hydrate": {"source", "configuration", "active", "tools_disabled", "tools"},
              "exclude": {"expected_confirmation"}}
    if set(data) - fields.get(op, set()):
        raise BrokerError("unsupported broker action fields", 400)
    if op == "exclude" and data.get("expected_confirmation") != server_id:
        raise BrokerError("confirmation must equal server_id", 400)
    with _LOCK:
        server = _STORE.get(server_id)
        if op == "install":
            if server is not None or _inspect(server_id) is not None:
                raise BrokerError("server already installed")
            try:
                source = DockerImageSource.model_validate(data["source"])
                host = DockerHostConfig.model_validate(data["configuration"])
            except (KeyError, ValidationError) as exc:
                raise BrokerError("invalid image or configuration", 400) from exc
            server = ManagedServer(server_id, source, host)
            _STORE[server_id] = server
        elif op == "hydrate":
            hydrated = _managed_server_from_state(server_id, data)
            if server is None:
                server = hydrated
                _STORE[server_id] = server
            return {"registered": True}
        elif op in {"reconcile", "recover"}:
            try:
                source = DockerImageSource.model_validate(data["source"])
                host = DockerHostConfig.model_validate(data["configuration"])
                active = data["active"]
                disabled = data["tools_disabled"]
                desired_running = data.get("running", active)
                if (type(active) is not bool or type(desired_running) is not bool or
                    not isinstance(disabled, list) or not all(isinstance(t, str) for t in cast(list[object], disabled))):
                    raise ValueError("invalid reconcile state")
            except (KeyError, ValidationError, ValueError) as exc:
                raise BrokerError("invalid reconcile state", 400) from exc
            if server is None:
                server = ManagedServer(server_id, source, host)
                _STORE[server_id] = server
            else:
                server.source, server.host = source, host
            server.active, server.disabled = active, set(cast(list[str], disabled))
            if op == "recover":
                _remove(server_id)
                server.tools = []
                if server.active and desired_running:
                    _spawn(server)
                    server.tools = _discover(server_id)
                return {"running": _running(server_id), "tools": server.tools}
        elif server is None:
            if op == "exclude":
                if _inspect(server_id) is not None:
                    _remove(server_id)
                return {"running": False, "tools": []}
            raise BrokerError("unknown server_id", 404)
    assert server is not None
    with server.lock:
        if op in {"install", "reconcile"}:
            try:
                if server.active:
                    if _inspect(server_id) is None:
                        _spawn(server)
                    if _running(server_id):
                        server.tools = _discover(server_id)
                return {"running": _running(server_id), "tools": server.tools}
            except Exception:
                if op == "install":
                    _remove(server_id)
                    with _LOCK:
                        _STORE.pop(server_id, None)
                raise
        if op == "configure":
            try:
                new_host = DockerHostConfig.model_validate(data["configuration"])
            except (KeyError, ValidationError) as exc:
                raise BrokerError("invalid configuration", 400) from exc
            old = server.host
            _remove(server_id)
            server.host = new_host
            try:
                if server.active:
                    _spawn(server)
                    server.tools = _discover(server_id)
            except Exception:
                _remove(server_id)
                server.host = old
                if server.active:
                    _spawn(server)
                    server.tools = _discover(server_id)
                raise
        elif op == "update-image":
            try:
                next_source = DockerImageSource.model_validate(data["source"])
            except (KeyError, ValidationError) as exc:
                raise BrokerError("invalid image", 400) from exc
            if next_source == server.source:
                raise BrokerError("image identity is unchanged", 409)
            image_reference(next_source)
            old = server.source
            _remove(server_id)
            server.source = next_source
            try:
                if server.active:
                    _spawn(server)
                    server.tools = _discover(server_id)
            except Exception:
                _remove(server_id)
                server.source = old
                if server.active:
                    _spawn(server)
                    server.tools = _discover(server_id)
                raise
            server.disabled.intersection_update(server.tools)
        elif op == "restart":
            if not server.active:
                raise BrokerError("server inactive")
            _remove(server_id)
            _spawn(server)
            server.tools = _discover(server_id)
        elif op in {"disable-tool", "enable-tool"}:
            tool = data.get("tool")
            if not isinstance(tool, str) or tool not in server.tools:
                raise BrokerError("unknown raw tool name", 400)
            (server.disabled.add if op == "disable-tool" else server.disabled.discard)(tool)
        elif op == "deactivate":
            server.active = False
            _remove(server_id)
        elif op == "activate":
            server.active = True
            if _inspect(server_id) is None:
                _spawn(server)
            server.tools = _discover(server_id)
        elif op == "stop":
            if not server.host.persistent or not server.active:
                raise BrokerError("persistent active server required")
            if _running(server_id):
                docker("stop", _name(server_id))
        elif op == "start":
            if not server.host.persistent or not server.active:
                raise BrokerError("persistent active server required")
            if _inspect(server_id) is None:
                _spawn(server)
            elif not _running(server_id):
                docker("start", _name(server_id))
            server.tools = _discover(server_id)
        elif op == "exclude":
            container = _inspect(server_id)
            mounts: object = container.get("Mounts") if container else []
            volume_names = [str(cast(dict[str, object], item).get("Name"))
                            for item in cast(list[object], mounts) if isinstance(item, dict)
                            and cast(dict[str, object], item).get("Type") == "volume"] if isinstance(mounts, list) else []
            server.active = False
            _remove(server_id)
            with _LOCK:
                _STORE.pop(server_id, None)
            return {"running": False, "volume_names": volume_names}
        return {"running": _running(server_id), "tools": server.tools}


class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
        pass  # Never log headers, tool arguments, env or paths.

    def send_json(self, code: int, data: dict[str, Any]) -> None:
        body = json.dumps(data).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def authorized(self) -> bool:
        token_file = Path(os.environ["PERCIVAL_BROKER_TOKEN_FILE"])
        try:
            if token_file.stat().st_mode & 0o037:
                return False
            token = token_file.read_text(encoding="utf-8").strip()
        except OSError:
            return False
        return len(token) >= 32 and hmac.compare_digest(
            self.headers.get("Authorization", "").encode(), ("Bearer " + token).encode()
        )

    def do_POST(self) -> None:  # noqa: N802
        if not self.authorized():
            self.send_json(401, {"error": "unauthorized"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > 65536:
                raise BrokerError("invalid payload size", 400)
            body: object = json.loads(self.rfile.read(length))
            if not isinstance(body, dict):
                raise BrokerError("payload must be an object", 400)
            payload = cast(dict[str, Any], body)
            if self.path.startswith("/v1/"):
                op = self.path.removeprefix("/v1/")
                server_id = payload.get("server_id")
                if not isinstance(server_id, str) or not SERVER_ID.fullmatch(server_id):
                    raise BrokerError("invalid server_id", 400)
                result = action(op, server_id, {k: v for k, v in payload.items() if k != "server_id"})
            elif self.path.startswith("/mcp/"):
                server_id = self.path.removeprefix("/mcp/")
                if not SERVER_ID.fullmatch(server_id):
                    raise BrokerError("server not found", 404)
                method = payload.get("method")
                if method not in MCP:
                    raise BrokerError("unsupported MCP method", 400)
                with _LOCK:
                    server = _STORE.get(server_id)
                if server is None:
                    raise BrokerError("server not found", 404)
                with server.lock:
                    if not server.active or not _running(server_id):
                        raise BrokerError("server unavailable")
                    if method == "notifications/initialized":
                        self.send_response(202)
                        self.send_header("Content-Length", "0")
                        self.end_headers()
                        return
                    if method == "tools/call":
                        params = payload.get("params")
                        name = cast(dict[str, object], params).get("name") if isinstance(params, dict) else None
                        if not isinstance(name, str) or name in server.disabled or name not in server.tools:
                            raise BrokerError("tool unavailable")
                    result = _exchange(server_id, payload)
                    if method == "tools/list" and isinstance(result.get("result"), dict):
                        listed = result["result"].get("tools", [])
                        result["result"]["tools"] = [t for t in listed if isinstance(t, dict) and cast(dict[str, object], t).get("name") not in server.disabled]
            else:
                raise BrokerError("not found", 404)
            self.send_json(200, result)
        except (BrokerError, ValueError, TypeError, KeyError, OSError) as exc:
            error = exc if isinstance(exc, BrokerError) else BrokerError("invalid broker request", 400)
            self.send_json(error.status, {"error": str(error)})


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=18081)
    args = parser.parse_args()
    if args.port < 1 or args.port > 65535:
        raise SystemExit("invalid broker port")
    if not Path(os.environ["PERCIVAL_BROKER_TOKEN_FILE"]).is_file():
        raise SystemExit("broker token unavailable")
    ready()
    service = http.server.ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print("percival mcp broker ready", flush=True)
    service.serve_forever()


if __name__ == "__main__":
    main()
