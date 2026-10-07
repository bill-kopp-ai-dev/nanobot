#!/usr/bin/env python3
"""Minimal MCP-style broker for the F0 disposable validation.

Listens on 127.0.0.1, requires a static token, and exposes two narrow
endpoints used by the validation script:

  GET  /v1/ping   -> {"ok": true, "client": <cli>, "server": <srv>}
  POST /v1/run    body: {"container_image": str, "command": [str]}
                 -> executes the image with `docker run --rm --network=none`
                    and returns the truncated output.  Rejects any command
                    that mentions /host, /var/run/docker.sock, /run, /proc,
                    --privileged, --pid=host, --net=host or any mount that
                    includes /var/lib/docker or the .percival path.

This is a *prototype* broker, not the real implementation.  It exists to
prove that the loopback-shared namespace, token gating, and mount checks
work as documented.  See docs/reports/2026-10-07-mcp-docker-f0-inventory-and-feasibility.md.
"""

from __future__ import annotations

import argparse
import hmac
import http.server
import json
import os
import re
import subprocess
import sys
from typing import Any

DEFAULT_TOKEN = "percival-f0-test-token"
DOCKER_BIN = os.environ.get("DOCKER_BIN", "/usr/bin/docker")
DOCKER_GID = int(os.environ.get("DOCKER_GID", "0"))
HOST_DOCKER_SOCK = os.environ.get("HOST_DOCKER_SOCK", "/var/run/docker.sock")
DISALLOWED_COMMAND_MARKERS = (
    "--privileged",
    "--pid=host",
    "--net=host",
    "--network=host",
    "/host/run",
    "/host/var/run",
    "/host/proc",
    "/host/var/lib/docker",
    "/host/root/.percival",
    "/host/etc/docker",
    "docker.sock",
)
DISALLOWED_MOUNT_PATHS = (
    "/run",
    "/var/run",
    "/proc",
    "/sys",
    "/var/lib/docker",
    "/etc/docker",
    "/root/.percival",
    "/home/nanobot/.nanobot",
    "/var/run/docker.sock",
    "/run/docker.sock",
)
# Docker image references that the broker may pass to `docker run`.
# Phase 1 (B20) allows ``sha256:<64hex>`` (local-image) and
# ``name@sha256:<64hex>`` (pinned-image), plus the conventional
# ``[registry/][ns/]name[:tag][@digest]`` form.  The pattern rejects any
# value that starts with ``-`` (would be parsed by docker as a flag) or
# contains characters outside the Docker image reference grammar.
_IMAGE_RE = re.compile(r"\A[A-Za-z0-9][A-Za-z0-9._/\-:@]{0,255}\Z")
_SHA256_RE = re.compile(r"\Asha256:[A-Fa-f0-9]{64}\Z")
_POSSIBLE_DOCKER_FLAGS = (
    "--privileged",
    "--pid=host",
    "--net=host",
    "--network=host",
    "--cap-add",
    "--security-opt",
    "--user",
    "-u",
    "-v",
    "--volume",
    "--mount",
    "--device",
    "--add-host",
    "--label",
    "-l",
    "--hostname",
    "-h",
    "--name",
    "--label-file",
    "--log-driver",
    "--restart",
    "--runtime",
    "--init",
    "--interactive",
    "-i",
    "--tty",
    "-t",
    "--rm",
    "--detach",
    "-d",
    "--env",
    "-e",
    "--env-file",
    "--workdir",
    "-w",
    "--read-only",
    "--tmpfs",
    "--dns",
    "--dns-search",
    "--dns-opt",
    "--domainname",
    "--entrypoint",
    "--expose",
    "--publish",
    "-p",
    "--expose",
    "--pull",
    "--platform",
    "--sysctl",
    "--ulimit",
    "--userns",
    "--volume-driver",
    "--volumes-from",
    "--link",
    "--network",
    "--ipc",
    "--pid",
    "--uts",
    "--cgroup-parent",
    "--cgroupns",
    "--memory",
    "-m",
    "--cpus",
    "--cpu-shares",
    "--cpuset-cpus",
    "--cpu-period",
    "--cpu-quota",
    "--cpuset-mems",
    "--memory-reservation",
    "--memory-swap",
    "--memory-swappiness",
    "--kernel-memory",
    "--cpus",
    "--cpuset-cpus",
    "--cpu-count",
    "--cpu-percent",
    "--cpuset-mems",
    "--device-cgroup-rule",
    "--device-read-bps",
    "--device-write-bps",
    "--device-read-iops",
    "--device-write-iops",
    "--blkio-weight",
    "--blkio-weight-device",
    "--cap-drop",
    "--cap-add",
    "--gpus",
    "--group-add",
    "--init-path",
    "--ip6tables",
    "--ip-forward",
    "--ip-masq",
    "--log-opt",
    "--network-alias",
    "--link-local-ip",
    "--mount",
    "--pid",
    "--privileged",
    "--publish-all",
    "--pull",
    "--read-only",
    "--restart",
    "--rm",
    "--runtime",
    "--security-opt",
    "--shm-size",
    "--stop-signal",
    "--stop-timeout",
    "--storage-opt",
    "--sysctl",
    "--tmpfs",
    "--tty",
    "-t",
    "--ulimit",
    "--userns",
    "--uts",
    "--volume",
    "-v",
    "--volume-driver",
    "--volumes-from",
    "--workdir",
    "-w",
    "--add-host",
    "--annotation",
    "--attach",
    "--blkio-weight",
    "--cap-add",
    "--cap-drop",
    "--cgroup-parent",
    "--cgroupns",
    "--cidfile",
    "--cpu-count",
    "--cpu-percent",
    "--cpu-period",
    "--cpu-quota",
    "--cpu-rt-period",
    "--cpu-rt-runtime",
    "--cpu-shares",
    "--cpus",
    "--cpuset-cpus",
    "--cpuset-mems",
    "--detach",
    "-d",
    "--detach-keys",
    "--device",
    "--device-cgroup-rule",
    "--device-read-bps",
    "--device-read-iops",
    "--device-write-bps",
    "--device-write-iops",
    "--dns",
    "--dns-opt",
    "--dns-search",
    "--domainname",
    "--entrypoint",
    "--env",
    "-e",
    "--env-file",
    "--expose",
    "--gpus",
    "--group-add",
    "--health-cmd",
    "--health-interval",
    "--health-retries",
    "--health-start-period",
    "--health-timeout",
    "--hostname",
    "-h",
    "--init",
    "--init-path",
    "--interactive",
    "-i",
    "--io-maxbandwidth",
    "--io-maxiops",
    "--ip",
    "--ip6",
    "--ipc",
    "--isolation",
    "--kernel-memory",
    "--label",
    "-l",
    "--label-file",
    "--link",
    "--link-local-ip",
    "--log-driver",
    "--log-opt",
    "--mac-address",
    "--memory",
    "-m",
    "--memory-reservation",
    "--memory-swap",
    "--memory-swappiness",
    "--mount",
    "--name",
    "--network",
    "--network-alias",
    "--no-healthcheck",
    "--oom-kill-disable",
    "--oom-score-adj",
    "--pid",
    "--pids-limit",
    "--platform",
    "--privileged",
    "--publish",
    "-p",
    "--publish-all",
    "--pull",
    "--quiet",
    "-q",
    "--read-only",
    "--restart",
    "--rm",
    "--runtime",
    "--security-opt",
    "--shm-size",
    "--stop-signal",
    "--stop-timeout",
    "--storage-opt",
    "--sysctl",
    "--tmpfs",
    "--tty",
    "-t",
    "--ulimit",
    "--user",
    "-u",
    "--userns",
    "--uts",
    "--volume",
    "-v",
    "--volume-driver",
    "--volumes-from",
    "--workdir",
    "-w",
)


def _is_valid_image(image: str) -> bool:
    """Return True when *image* is a syntactically valid Docker reference.

    The Docker image reference grammar allows alphanumerics plus
    ``._-/:@``.  The image must not start with ``-`` (docker would
    parse it as a flag and override the broker's own hardening
    options like ``--cap-drop=ALL``).
    """
    if not isinstance(image, str) or not image or not _IMAGE_RE.fullmatch(image):
        return False
    if image in _POSSIBLE_DOCKER_FLAGS:
        return False
    # Phase 1 of B20 also accepts the bare digest form for local-image.
    if image.startswith("sha256:"):
        return bool(_SHA256_RE.fullmatch(image))
    if "@" in image:
        # Pinned image must end in a sha256 digest.
        suffix = image.rsplit("@", 1)[-1]
        digest = suffix if suffix.startswith("sha256:") else f"sha256:{suffix}"
        return bool(_SHA256_RE.fullmatch(digest))
    if ":" in image:
        # Tagged reference; the part after the last colon must be the
        # tag (no slashes inside the tag).
        name, _, tag = image.rpartition(":")
        return bool(name) and bool(tag) and "/" not in tag
    return False


def _check_payload(payload: dict[str, Any]) -> tuple[bool, str]:
    image = payload.get("container_image")
    if not isinstance(image, str) or not image:
        return False, "container_image is required"
    if not _is_valid_image(image):
        return False, f"container_image {image!r} is not a valid image reference"
    cmd = payload.get("command") or []
    entrypoint = payload.get("entrypoint") or []
    if cmd and (not isinstance(cmd, list) or not all(isinstance(part, str) for part in cmd)):
        return False, "command must be a list of strings"
    if entrypoint and (not isinstance(entrypoint, list) or not all(isinstance(part, str) for part in entrypoint)):
        return False, "entrypoint must be a list of strings"
    joined = " ".join(list(cmd) + list(entrypoint))
    for marker in DISALLOWED_COMMAND_MARKERS:
        if marker in joined:
            return False, f"rejected by command policy: {marker!r}"
    mounts = payload.get("mounts") or []
    if not isinstance(mounts, list) or not all(isinstance(m, str) for m in mounts):
        return False, "mounts must be a list of strings"
    for mount in mounts:
        for denied in DISALLOWED_MOUNT_PATHS:
            if mount == denied or mount.startswith(denied + "/") or mount.startswith(denied + ":"):
                return False, f"mount {mount!r} is in the protected set"
        # If the mount is in the long syntax ``type=bind,src=<path>,dst=<path>``,
        # parse the src and dst components and reject any path that lands in
        # the protected set.
        for key in ("src", "source", "dst", "destination", "target"):
            prefix = f"{key}="
            if prefix in mount:
                value = mount.split(prefix, 1)[1].split(",", 1)[0]
                for denied in DISALLOWED_MOUNT_PATHS:
                    if value == denied or value.startswith(denied + "/"):
                        return False, f"mount {mount!r} targets protected path {value!r}"
    return True, ""


def _run_container(image: str, command: list[str], mounts: list[str], entrypoint: list[str] | None = None) -> dict[str, Any]:
    args = [
        DOCKER_BIN,
        "run",
        "--rm",
        "--pull=never",
        "--network=none",
        "--cap-drop=ALL",
        "--security-opt=no-new-privileges",
    ]
    for mount in mounts:
        args += ["--mount", mount]
    if entrypoint:
        args += ["--entrypoint", entrypoint[0]]
        args += [image] + (entrypoint[1:] if len(entrypoint) > 1 else [])
    else:
        args += [image] + command
    try:
        completed = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"ok": False, "error": repr(exc)}
    return {
        "ok": completed.returncode == 0,
        "returncode": completed.returncode,
        "stdout": completed.stdout[-512:],
        "stderr": completed.stderr[-512:],
    }


class _Handler(http.server.BaseHTTPRequestHandler):
    server_version = "PercivalF0Broker/0.1"

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
        sys.stderr.write("[broker] " + (format % args) + "\n")

    def _send_json(self, status: int, body: dict[str, Any]) -> None:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _authorized(self) -> bool:
        header = self.headers.get("Authorization", "")
        if not header.startswith("Bearer "):
            return False
        # Use a constant-time comparison to avoid leaking the token
        # through timing.  Both sides are normalised to bytes.
        provided = header[len("Bearer ") :].encode("utf-8")
        expected = self.server.token.encode("utf-8")  # type: ignore[attr-defined]
        return hmac.compare_digest(provided, expected)

    def do_GET(self) -> None:  # noqa: N802
        if self.path != "/v1/ping":
            self._send_json(404, {"error": "not found"})
            return
        if not self._authorized():
            self._send_json(401, {"error": "unauthorized"})
            return
        client_v, server_v = _docker_versions()
        self._send_json(200, {
            "ok": True,
            "docker_client": client_v,
            "docker_server": server_v,
            "socket": HOST_DOCKER_SOCK,
            "docker_gid": DOCKER_GID,
        })

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/v1/run":
            self._send_json(404, {"error": "not found"})
            return
        if not self._authorized():
            self._send_json(401, {"error": "unauthorized"})
            return
        length = int(self.headers.get("Content-Length", "0") or "0")
        if length <= 0 or length > 16 * 1024:
            self._send_json(400, {"error": "payload too small or too large"})
            return
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
        except json.JSONDecodeError as exc:
            self._send_json(400, {"error": f"invalid json: {exc}"})
            return
        if not isinstance(payload, dict):
            self._send_json(400, {"error": "payload must be an object"})
            return
        image = payload.get("container_image")
        if not isinstance(image, str) or not image:
            self._send_json(400, {"error": "container_image is required"})
            return
        ok, reason = _check_payload(payload)
        if not ok:
            self._send_json(400, {"error": reason})
            return
        cmd_list: list[str] = payload.get("command") or []
        mounts_list: list[str] = payload.get("mounts") or []
        ep_list: list[str] | None = payload.get("entrypoint")
        result = _run_container(
            image,
            cmd_list,
            mounts_list,
            entrypoint=ep_list,
        )
        self._send_json(200, result)


def _docker_versions() -> tuple[str, str]:
    try:
        out = subprocess.run(
            [DOCKER_BIN, "version", "--format", "{{.Client.Version}} {{.Server.Version}}"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        parts = (out.stdout or "").strip().split()
        if len(parts) >= 2:
            return parts[0], parts[1]
    except (OSError, subprocess.TimeoutExpired):
        pass
    return "?", "?"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=18071)
    parser.add_argument("--token", default=os.environ.get("PERCIVAL_BROKER_TOKEN", DEFAULT_TOKEN))
    args = parser.parse_args()
    server = http.server.ThreadingHTTPServer((args.host, args.port), _Handler)
    server.token = args.token  # type: ignore[attr-defined]
    print(f"broker listening on {args.host}:{args.port}", flush=True)
    print(f"docker socket {HOST_DOCKER_SOCK} (gid {DOCKER_GID})", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
