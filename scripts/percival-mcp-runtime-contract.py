#!/usr/bin/env python3
"""Measure the stdio runtime contract of an MCP image under each manager's flags.

The contract a stdio MCP image must satisfy, regardless of who launches it:

* stdout carries JSON-RPC only, so the container must not be given a TTY;
* stdin must stay open for the session, so the client owns the lifetime;
* no published port and no HTTP healthcheck — a stdio server has no listener
  to probe, and an HTTP probe reports a false ``unhealthy``;
* exactly one init. A ``tini`` embedded in the image and a Docker ``--init``
  stacked on top of it create a false supervision layer;
* PID 1 must react to SIGTERM. Inside a PID namespace the kernel only
  delivers a signal to the namespace's init if that process installed a
  handler; otherwise the stop is escalated to SIGKILL after the grace
  period and the container exits 137 instead of 143.

Two measurements are taken per manager, each on its own disposable container:
the **EOF** measurement closes the client's stdin, and the **SIGTERM**
measurement stops the container. Neither touches running MCP containers,
live configuration, credentials or host state.

Usage::

    python3 scripts/percival-mcp-runtime-contract.py \
        --image sha256:<id> --name notes \
        --env PERCIVAL_NOTES_VAULT_PATH=/vault \
        --mount type=tmpfs,destination=/vault,tmpfs-mode=0777

The JSON report is written to ``--output`` and a human summary to stdout.
The exit status is non-zero when any contract violation is observed.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# SIGTERM is signal 15; bit 14 of the caught-signal mask.
SIGTERM_BIT = 1 << 14

# The flags each manager actually uses when it launches an MCP.
MANAGER_FLAGS: dict[str, list[str]] = {
    # nanobot/mcp_docker/broker.py:_spawn
    "percival": ["--init", "--cap-drop=ALL", "--security-opt=no-new-privileges"],
    # alternative-positronic/packages/positronic-mcp-docker/src/managed.ts
    "positronic": ["--init"],
}


def run(args: list[str], *, timeout: int = 120) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, text=True, capture_output=True, timeout=timeout)


def docker_inspect(name: str) -> dict[str, Any]:
    result = run(["docker", "inspect", name])
    if result.returncode:
        return {}
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        return {}
    return data[0] if isinstance(data, list) and data else {}


def wait_ready(name: str, timeout: int = 45) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        probe = run(["docker", "exec", name, "sh", "-c", "echo up"], timeout=30)
        if probe.returncode == 0:
            time.sleep(2.0)
            return True
        time.sleep(0.5)
    return False


def pid1_command(name: str) -> str:
    top = run(["docker", "top", name, "-eo", "pid,args"], timeout=30)
    if top.returncode:
        return ""
    rows = [line for line in top.stdout.splitlines()[1:] if line.strip()]
    return " ".join(rows[0].split()[1:]) if rows else ""


def proc_field(name: str, field: str) -> str:
    probe = run(["docker", "exec", name, "sh", "-c",
                 f"awk '/^{field}/{{print $2}}' /proc/1/status"], timeout=30)
    return probe.stdout.strip() if probe.returncode == 0 else ""


def listening_sockets(name: str) -> int:
    probe = run(["docker", "exec", name, "sh", "-c",
                 "cat /proc/net/tcp 2>/dev/null | awk 'NR>1 && $4==\"0A\"' | wc -l"], timeout=30)
    return int(probe.stdout.strip()) if probe.returncode == 0 and probe.stdout.strip().isdigit() else -1


def embedded_init(entrypoint: list[str] | None) -> bool:
    """An image embeds an init when its ENTRYPOINT runs tini (or docker-init)."""
    if not entrypoint:
        return False
    return any("tini" in part or "docker-init" in part for part in entrypoint)


def launch_flags(manager: str, env: list[str], mounts: list[str]) -> list[str]:
    args: list[str] = []
    for spec in mounts:
        args += ["--mount", spec]
    for item in env:
        args += ["--env", item]
    return args


def observe(name: str) -> dict[str, Any]:
    """Collect the static and process facts of a running container."""
    container = docker_inspect(name)
    config = container.get("Config", {}) if container else {}
    host = container.get("HostConfig", {}) if container else {}
    caught = proc_field(name, "SigCgt:")
    return {
        "image_id": container.get("Image", ""),
        "entrypoint": config.get("Entrypoint"),
        "embedded_init": embedded_init(config.get("Entrypoint")),
        "docker_init": bool(host.get("Init")),
        "tty": bool(config.get("Tty")),
        "stdin_open": bool(config.get("OpenStdin")),
        "published_ports": host.get("PortBindings") or {},
        "healthcheck": config.get("Healthcheck"),
        "effective_uid": proc_field(name, "Uid:"),
        "no_new_privs": proc_field(name, "NoNewPrivs:"),
        "cap_eff": proc_field(name, "CapEff:"),
        "sigcgt": caught,
        "handles_sigterm": bool(int(caught or "0", 16) & SIGTERM_BIT),
        "listening_sockets": listening_sockets(name),
        "pid1": pid1_command(name),
    }


def still_running(name: str) -> bool:
    state = docker_inspect(name).get("State", {})
    return bool(state.get("Running"))


INITIALIZE = json.dumps({
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {"name": "percival-contract", "version": "1"},
    },
})


def await_initialize(proc: subprocess.Popen[str], timeout: int = 20) -> bool:
    """Send an initialize request and wait for the matching response frame."""
    try:
        if proc.stdin:
            proc.stdin.write(INITIALIZE + "\n")
            proc.stdin.flush()
    except OSError:
        return False
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        line = proc.stdout.readline() if proc.stdout else ""
        if not line:
            if proc.poll() is not None:
                return False
            time.sleep(0.2)
            continue
        try:
            frame = json.loads(line)
        except json.JSONDecodeError:
            continue
        if frame.get("id") == 1:
            return "error" not in frame
    return False


def measure_eof(image: str, manager: str, env: list[str], mounts: list[str]) -> dict[str, Any]:
    """Attach to the server's stdin and close it: the server must exit 0.

    The server must first answer an ``initialize`` request. A server that
    never answers did not reach its serving state — it failed a startup
    precondition (missing configuration, unreachable upstream), which is a
    different fact from the EOF contract.
    """
    name = f"percival-contract-{uuid.uuid4().hex[:12]}"
    row: dict[str, Any] = {"manager": manager, "mode": "eof"}
    try:
        run(["docker", "rm", "-f", name], timeout=60)
        command = ["docker", "run", "--rm", "-i", "--pull=never", "--network=none",
                   *MANAGER_FLAGS[manager], *launch_flags(manager, env, mounts),
                   "--name", name, image]
        proc = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                stderr=subprocess.DEVNULL, text=True)
        ready = False
        deadline = time.monotonic() + 45
        while time.monotonic() < deadline and proc.poll() is None:
            probe = run(["docker", "exec", name, "sh", "-c", "echo up"], timeout=30)
            if probe.returncode == 0:
                ready = True
                time.sleep(2.0)
                break
            time.sleep(0.5)
        row["ready"] = ready
        row.update(observe(name))
        row["alive_before_eof"] = still_running(name)
        row["served_initialize"] = await_initialize(proc)
        try:
            if proc.stdin:
                proc.stdin.close()
        except OSError:
            pass
        try:
            proc.wait(timeout=30)
            row["exit_code"] = proc.returncode
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
            row["exit_code"] = "TIMEOUT"
    finally:
        run(["docker", "rm", "-f", name], timeout=60)
    return row


def measure_sigterm(image: str, manager: str, env: list[str], mounts: list[str],
                    stop_timeout: int) -> dict[str, Any]:
    """Stop the server the way a manager does: SIGTERM, then escalate."""
    name = f"percival-contract-{uuid.uuid4().hex[:12]}"
    row: dict[str, Any] = {"manager": manager, "mode": "sigterm"}
    try:
        run(["docker", "rm", "-f", name], timeout=60)
        started = run(["docker", "run", "-d", "-i", "--pull=never", "--network=none",
                       *MANAGER_FLAGS[manager], *launch_flags(manager, env, mounts),
                       "--name", name, image], timeout=120)
        row["started"] = started.returncode == 0
        if not row["started"]:
            row["error"] = started.stderr.strip()[-400:]
            return row
        row["ready"] = wait_ready(name)
        row.update(observe(name))
        begin = time.monotonic()
        run(["docker", "stop", "--time", str(stop_timeout), name], timeout=stop_timeout + 60)
        row["stop_seconds"] = round(time.monotonic() - begin, 1)
        state = docker_inspect(name).get("State", {})
        row["exit_code"] = state.get("ExitCode")
    finally:
        run(["docker", "rm", "-f", name], timeout=60)
    return row


def check(row: dict[str, Any]) -> list[str]:
    """Return the contract violations observed in one measurement."""
    problems: list[str] = []
    if row.get("error"):
        problems.append(f"container did not start: {row['error']}")
        return problems
    if row.get("tty"):
        problems.append("tty allocated: stdout is the JSON-RPC stream")
    if not row.get("stdin_open"):
        problems.append("stdin not open: the client cannot drive the session")
    if row.get("published_ports"):
        problems.append("published ports: a stdio MCP must not bind or publish a port")
    health = row.get("healthcheck")
    if health and health.get("Test") != ["NONE"]:
        problems.append("HTTP healthcheck on a stdio server reports a false unhealthy")
    layers = int(row.get("docker_init", False)) + int(row.get("embedded_init", False))
    row["init_layers"] = layers
    if layers > 1:
        problems.append(f"{layers} init layers: keep one")
    if row["mode"] == "sigterm":
        # The signal only reaches the application when something forwards it.
        # An init layer (Docker's or an embedded tini) forwards SIGTERM to its
        # child; with no init, PID 1 is the application itself and must have
        # installed a SIGTERM handler of its own.
        layers = int(row.get("docker_init", False)) + int(row.get("embedded_init", False))
        if layers == 0 and not row.get("handles_sigterm"):
            problems.append("no init forwards SIGTERM and PID 1 does not handle it")
        if row.get("exit_code") == 137:
            problems.append("stop ended in SIGKILL (exit 137) instead of a clean exit")
        elif row.get("exit_code") != 143:
            problems.append(f"unexpected exit code {row.get('exit_code')} on stop")
    else:
        if not row.get("served_initialize"):
            problems.append(
                f"server did not answer initialize (exit {row.get('exit_code')}): "
                "startup precondition not met, not an EOF failure")
        elif row.get("exit_code") != 0:
            problems.append(f"unexpected exit code {row.get('exit_code')} on EOF")
    return problems


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--image", required=True, help="image reference or ID under test")
    parser.add_argument("--name", required=True, help="label for this MCP in the report")
    parser.add_argument("--env", action="append", default=[], metavar="KEY=VALUE",
                        help="environment for the container")
    parser.add_argument("--mount", action="append", default=[], metavar="SPEC",
                        help="mount specification, e.g. type=tmpfs,destination=/vault,tmpfs-mode=0777")
    parser.add_argument("--manager", action="append", choices=sorted(MANAGER_FLAGS),
                        help="manager whose launch flags to measure (default: all)")
    parser.add_argument("--stop-timeout", type=int, default=10,
                        help="grace period in seconds for the SIGTERM measurement")
    parser.add_argument("--output", type=Path, help="write the JSON report here")
    args = parser.parse_args()

    managers = args.manager or sorted(MANAGER_FLAGS)
    mounts = [spec if spec.startswith("type=") else f"type=bind,{spec}" for spec in args.mount]
    rows = []
    for manager in managers:
        for row in (measure_eof(args.image, manager, args.env, mounts),
                    measure_sigterm(args.image, manager, args.env, mounts, args.stop_timeout)):
            row["mcp"] = args.name
            row["violations"] = check(row)
            rows.append(row)
            status = "OK" if not row["violations"] else "VIOLATIONS"
            print(f"[{status}] {args.name} under {manager} ({row['mode']}): "
                  f"init_layers={row.get('init_layers')} "
                  f"exit={row.get('exit_code')} "
                  f"tty={row.get('tty')} "
                  f"ports={len(row.get('published_ports') or {})} "
                  f"healthcheck={row.get('healthcheck')}")
            for problem in row["violations"]:
                print(f"    - {problem}")

    report = {
        "schemaVersion": 1,
        "readOnly": True,
        "finishedAt": datetime.now(timezone.utc).isoformat(),
        "mcp": args.name,
        "image": args.image,
        "measurements": rows,
    }
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(f"Evidence: {args.output}")
    if any(row["violations"] for row in rows):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
