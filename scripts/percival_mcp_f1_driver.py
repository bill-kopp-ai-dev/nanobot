#!/usr/bin/env python3
"""Gateway-side F1 experiment driver; keeps intent/audit outside the broker.

This is deliberately a disposable prototype, not the Percival config schema or
CLI. It runs *inside* a Docker gateway test container without Docker access.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path("/home/nanobot/.nanobot")
CONFIG = ROOT / "config.json"
AUDIT = ROOT / "mcp-docker" / "audit.jsonl"
BACKUPS = ROOT / "mcp-docker" / "backups"
URL = "http://127.0.0.1:18081"
TOKEN = os.environ["F1_BROKER_TOKEN"]
IMAGE_WEATHER = os.environ["F1_WEATHER_ID"]
IMAGE_OSM = os.environ["F1_OSM_ID"]
IMAGE_WEATHER_OLD = os.environ["F1_WEATHER_OLD_ID"]
IMAGE_OSM_OLD = os.environ["F1_OSM_OLD_ID"]
IMAGE_ALPINE = os.environ["F1_ALPINE_ID"]
IMAGE_WEATHER_PINNED = os.environ["F1_WEATHER_PINNED"]
CONFIG_WRITE_LOCK = threading.RLock()


def request(route: str, body: dict, token: str = TOKEN) -> tuple[int, dict]:
    start = time.monotonic()
    req = urllib.request.Request(URL + route, json.dumps(body).encode(), {
        "Content-Type": "application/json", "Authorization": "Bearer " + token,
    })
    try:
        with urllib.request.urlopen(req, timeout=35) as response:
            code, data = response.status, json.load(response)
    except urllib.error.HTTPError as exc:
        code, data = exc.code, json.load(exc)
    print(f"{route} HTTP {code} elapsed_ms={round((time.monotonic() - start) * 1000)}", flush=True)
    if code != 200:
        print(f"  error={data.get('error', '')[:200]}", flush=True)
    return code, data


def ok(route: str, body: dict) -> dict:
    code, result = request(route, body)
    assert code == 200, (route, code, result)
    return result


def rejected(route: str, body: dict, status: int = 409) -> None:
    code, result = request(route, body)
    assert code == status, (route, code, result)


def persist(config: dict) -> None:
    temp = CONFIG.with_suffix(".new")
    temp.write_text(json.dumps(config, indent=2) + "\n")
    os.chmod(temp, 0o600)
    temp.replace(CONFIG)


def audit(action: str, server_id: str, status: str) -> None:
    AUDIT.parent.mkdir(mode=0o700, exist_ok=True)
    with AUDIT.open("a") as f:
        f.write(json.dumps({"action": action, "server_id": server_id, "status": status}) + "\n")
    os.chmod(AUDIT, 0o600)


def mutate(config: dict, op: str, server_id: str, *, expected_revision: int | None = None, **kwargs: object) -> dict:
    with CONFIG_WRITE_LOCK:
        section = config["tools"]["mcpDocker"]
        revision = section["revision"]
        disk_revision = json.loads(CONFIG.read_text())["tools"]["mcpDocker"]["revision"]
        if disk_revision != revision or (expected_revision is not None and expected_revision != revision):
            raise ValueError("CAS conflict: stale gateway revision")
        result = ok("/v1/" + op, {"server_id": server_id, **kwargs})
        section["revision"] += 1
        state = section["servers"].setdefault(server_id, {})
        if op == "install":
            state.update({"image": result["image"], "source": kwargs["image"],
                          "active": True, "persistent": kwargs.get("persistent", False),
                          "host_access": True, "toolsDisabled": [], "env": kwargs.get("env", {})})
        elif op == "update-image":
            state["image"] = result["image"]
            state["source"] = kwargs["image"]
        elif op == "configure":
            state["host_access"] = kwargs["host_access"]
        elif op in {"disable-tool", "enable-tool"}:
            state["toolsDisabled"] = result["toolsDisabled"]
        elif op in {"activate", "deactivate"}:
            state["active"] = result["active"]
        elif op == "exclude":
            del section["servers"][server_id]
        persist(config)
        audit(op, server_id, "committed")
        return result


def mcp(server_id: str, method: str, params: dict | None = None) -> dict:
    result = ok("/mcp", {"jsonrpc": "2.0", "server_id": server_id,
                          "id": 21, "method": method, "params": params or {}})
    assert "result" in result, result
    return result["result"]


def backup(config: dict, server_id: str) -> Path:
    BACKUPS.mkdir(parents=True, mode=0o700, exist_ok=True)
    target = BACKUPS / f"{server_id}-{config['tools']['mcpDocker']['revision']}"
    target.mkdir(mode=0o700, exist_ok=False)
    manifest = {"schemaVersion": 1, "server_id": server_id,
                "source_revision": config["tools"]["mcpDocker"]["revision"],
                "server": config["tools"]["mcpDocker"]["servers"][server_id]}
    canonical = json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()
    manifest["sha256"] = hashlib.sha256(canonical).hexdigest()
    (target / "manifest.json").write_text(json.dumps(manifest))
    os.chmod(target / "manifest.json", 0o600)
    return target


def run() -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    config = {"tools": {"mcpDocker": {"schemaVersion": 1, "revision": 0, "servers": {}}}}
    persist(config)
    for server_id, image, env in (
        ("weather", IMAGE_WEATHER_PINNED, {}),
        ("osm", IMAGE_OSM, {"USER_AGENT": "Percival-F1-test (local)",
                                "FROM_HEADER": "local@example.invalid"}),
    ):
        started = time.monotonic()
        mutate(config, "install", server_id, image=image, env=env, persistent=server_id == "weather")
        assert mcp(server_id, "initialize")["serverInfo"]["name"]
        tools = mcp(server_id, "tools/list")["tools"]
        print(f"{server_id}: tool_count={len(tools)} cold_start_ms={round((time.monotonic()-started)*1000)}")
        assert len(tools) >= (9 if server_id == "weather" else 30)
        call = ("weather_convert_time", {"datetime_str": "2026-10-07T12:00:00Z",
                                         "from_timezone": "UTC", "to_timezone": "America/Sao_Paulo"}) if server_id == "weather" else ("osm_get_health", {})
        response = mcp(server_id, "tools/call", {"name": call[0], "arguments": call[1]})
        assert not response.get("isError"), response
        print(f"{server_id}: real call {call[0]} ok")
        mutate(config, "disable-tool", server_id, tool=call[0])
        assert call[0] not in {t["name"] for t in mcp(server_id, "tools/list")["tools"]}
        rejected("/mcp", {"jsonrpc": "2.0", "id": 99, "server_id": server_id,
                          "method": "tools/call", "params": {"name": call[0], "arguments": call[1]}})
        mutate(config, "enable-tool", server_id, tool=call[0])
        mutate(config, "deactivate", server_id)
        rejected("/mcp", {"jsonrpc": "2.0", "id": 99, "server_id": server_id, "method": "tools/list"})
        mutate(config, "activate", server_id)
        mutate(config, "configure", server_id, host_access=False)
        assert ok("/v1/list", {"server_id": server_id})["state"]["host_access"] is False
        mutate(config, "configure", server_id, host_access=True)
        mutate(config, "restart", server_id)
        previous = backup(config, server_id)
        next_image = IMAGE_WEATHER_OLD if server_id == "weather" else IMAGE_OSM_OLD
        mutate(config, "update-image", server_id, image=next_image)
        assert ok("/v1/list", {"server_id": server_id})["state"]["image"] == next_image
        # A different *real, locally installed* image fails after the old
        # container is stopped; the broker must recreate the previous one.
        failing_image = IMAGE_OSM if server_id == "weather" else IMAGE_ALPINE
        rejected("/v1/update-image", {"server_id": server_id, "image": failing_image})
        assert ok("/v1/list", {"server_id": server_id})["state"]["image"] == next_image
        assert mcp(server_id, "tools/list")["tools"]
        audit("update-image", server_id, "failed")
        print(f"{server_id}: updated to {next_image}; failed-update backup={previous.name} compensated")
        if server_id == "weather":
            mutate(config, "stop", server_id)
            rejected("/mcp", {"jsonrpc": "2.0", "id": 99, "server_id": server_id, "method": "tools/list"})
            mutate(config, "start", server_id)
        else:
            rejected("/v1/stop", {"server_id": server_id})
        assert mcp(server_id, "tools/list")["tools"]
    rejected("/v1/exclude", {"server_id": "osm", "expected_confirmation": "wrong"})
    for server_id in ("weather", "osm"):
        for alias in ("/run", "/var/run", "/host/proc/1/root/run", "/home/bill/.docker"):
            rejected("/v1/configure", {"server_id": server_id, "host_access": True,
                                       "mounts": [f"type=bind,src={alias},dst=/host/run"]})
        rejected("/v1/configure", {"server_id": server_id, "host_access": True, "network": "host"})
        rejected("/v1/restart", {"server_id": server_id, "docker_flags": ["--privileged"]})
        assert mcp(server_id, "tools/list")["tools"]
    rejected("/v1/install", {"server_id": "../run/docker.sock", "image": IMAGE_WEATHER})
    rejected("/v1/install", {"server_id": "injection", "image": "--privileged"})
    config["agents"] = {"defaults": {"botName": "F1-preserve-through-CAS"}}
    persist(config)
    revision = config["tools"]["mcpDocker"]["revision"]
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(mutate, config, "disable-tool", server, expected_revision=revision, tool=tool)
                   for server, tool in (("weather", "weather_convert_time"), ("osm", "osm_get_health"))]
        outcomes = []
        for future in futures:
            try:
                future.result()
                outcomes.append("committed")
            except ValueError as exc:
                assert "CAS conflict" in str(exc)
                outcomes.append("conflict")
    assert sorted(outcomes) == ["committed", "conflict"], outcomes
    assert json.loads(CONFIG.read_text())["agents"]["defaults"]["botName"] == "F1-preserve-through-CAS"
    for server, tool in (("weather", "weather_convert_time"), ("osm", "osm_get_health")):
        if tool not in config["tools"]["mcpDocker"]["servers"][server]["toolsDisabled"]:
            mutate(config, "disable-tool", server, tool=tool)
        assert tool not in {t["name"] for t in mcp(server, "tools/list")["tools"]}
        mutate(config, "enable-tool", server, tool=tool)
    mutate(config, "install", "weather-copy", image=IMAGE_WEATHER, env={}, persistent=False)
    assert {t["name"] for t in mcp("weather-copy", "tools/list")["tools"]} == {
        t["name"] for t in mcp("weather", "tools/list")["tools"]
    }
    mutate(config, "disable-tool", "weather-copy", tool="weather_convert_time")
    assert "weather_convert_time" in {t["name"] for t in mcp("weather", "tools/list")["tools"]}
    backup(config, "weather-copy")
    mutate(config, "exclude", "weather-copy", expected_confirmation="weather-copy")
    print("two-writer CAS conflict, unrelated config and server_id tool collision isolated")
    assert request("/v1/list", {"server_id": "osm"}, token="wrong")[0] == 401
    print("F1 first pass complete; leave records and containers for recreate scenario")


def reconcile() -> None:
    config = json.loads(CONFIG.read_text())
    for server_id, state in config["tools"]["mcpDocker"]["servers"].items():
        # The broker lost in-memory state on recreation; containers from the
        # previous sidecar still exist. The driver re-installs after cleanup.
        result = ok("/v1/install", {"server_id": server_id, "image": state["source"],
                                     "persistent": state["persistent"], "env": state["env"]})
        assert result["running"]
        assert mcp(server_id, "tools/list")["tools"]
        audit("reconcile", server_id, "committed")
        print(f"reconciled {server_id} revision={config['tools']['mcpDocker']['revision']}")
    assert CONFIG.is_file() and AUDIT.is_file()
    print(f"persisted config_bytes={CONFIG.stat().st_size} audit_entries={len(AUDIT.read_text().splitlines())}")


def finish() -> None:
    config = json.loads(CONFIG.read_text())
    for server_id in ("weather", "osm"):
        backup(config, server_id)
        mutate(config, "exclude", server_id, expected_confirmation=server_id)
    print("excluded both registrations; source images retained")


def restore_checks() -> None:
    config = json.loads(CONFIG.read_text())
    backups = {}
    for server_id in ("weather", "osm", "weather-copy"):
        candidates = [path for path in BACKUPS.iterdir()
                      if path.is_dir() and path.name.startswith(server_id + "-")]
        backups[server_id] = max(candidates, key=lambda path: int(path.name.rsplit("-", 1)[1]))

    def cli(backup_dir: Path, revision: int, *, apply: bool = False, success: bool = True) -> None:
        args = ["nanobot", "mcp-docker", "restore", str(backup_dir),
                "--config", str(CONFIG), "--expected-revision", str(revision)]
        if apply:
            args.append("--apply")
        completed = subprocess.run(args, text=True, capture_output=True, timeout=40,
                                   env={**os.environ, "PERCIVAL_F1_DISPOSABLE": "1"}, check=False)
        assert (completed.returncode == 0) == success, (args, completed.stdout, completed.stderr)
        print(f"CLI restore {backup_dir.name}: {'apply' if apply else 'preview'} "
              f"{'ok' if success else 'rejected'}")

    revision = config["tools"]["mcpDocker"]["revision"]
    cli(backups["weather"], revision)
    rejected("/v1/list", {"server_id": "weather"})
    tampered = BACKUPS / "tampered"
    shutil.copytree(backups["weather"], tampered)
    manifest_path = tampered / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["server"]["active"] = False
    manifest_path.write_text(json.dumps(manifest))
    cli(tampered, revision, success=False)
    shutil.rmtree(tampered)
    for server_id in ("weather", "osm", "weather-copy"):
        cli(backups[server_id], revision, apply=True)
        cli(backups[server_id], revision, apply=True, success=False)
        config = json.loads(CONFIG.read_text())
        revision = config["tools"]["mcpDocker"]["revision"]
        cli(backups[server_id], revision, apply=True, success=False)
        assert mcp(server_id, "tools/list")["tools"]
    assert "weather_convert_time" not in {t["name"] for t in mcp("weather-copy", "tools/list")["tools"]}
    assert "weather_convert_time" in {t["name"] for t in mcp("weather", "tools/list")["tools"]}
    cli(backups["osm"], revision - 1, apply=True, success=False)
    assert json.loads(CONFIG.read_text())["agents"]["defaults"]["botName"] == "F1-preserve-through-CAS"
    for server_id in ("weather", "osm", "weather-copy"):
        mutate(config, "exclude", server_id, expected_confirmation=server_id)
    print("CLI preview/integrity/CAS/conflict/restore and cleanup verified")


def set_host_access(enabled: bool) -> None:
    config = json.loads(CONFIG.read_text())
    for server_id in ("weather", "osm"):
        mutate(config, "configure", server_id, host_access=enabled)
    print(f"effective host mount configured {'RW' if enabled else 'RO'} for both fixtures")


def probe() -> None:
    import shutil

    assert not Path("/var/run/docker.sock").exists()
    assert shutil.which("docker") is None
    assert request("/v1/list", {"server_id": "weather"}, token="incorrect")[0] == 401
    # An exec process in this gateway can read the gateway's broker token.
    # Record this as an indirect capability, not as isolation.
    assert TOKEN and len(TOKEN) >= 32
    print("gateway: no socket/CLI; exec can read token from environment (indirect risk)")


def sdk() -> None:
    import asyncio

    from mcp import ClientSession
    from mcp.client.streamable_http import streamablehttp_client

    async def check() -> None:
        for server_id, minimum in (("weather", 9), ("osm", 30)):
            async with streamablehttp_client(URL + "/mcp/" + server_id,
                                             headers={"Authorization": "Bearer " + TOKEN}) as (read, write, _):
                async with ClientSession(read, write) as session:
                    initialized = await session.initialize()
                    tools = await session.list_tools()
                    assert len(tools.tools) >= minimum
                    print(f"SDK streamablehttp_client {server_id}: "
                          f"{initialized.serverInfo.name} tools={len(tools.tools)}")

    asyncio.run(check())


if __name__ == "__main__":
    {"run": run, "probe": probe, "sdk": sdk, "reconcile": reconcile,
     "finish": finish, "restore-checks": restore_checks,
     "reduce-host": lambda: set_host_access(False),
     "restore-host": lambda: set_host_access(True)}[sys.argv[1]]()
