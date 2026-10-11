#!/usr/bin/env python3
"""F4 fixture test for Percival: backup, recreate, restore using docker stdio MCP calls.

Identical to the Positronic F4 test, but uses /home/bill/.local/share/percival-f4-fixture/
as the data path. The broker mounts /host/<src> for /host/... in the container, so
the docker run invocation uses the same path; the broker-level behavior is already
covered by the F7 reports and the Percival smoke checks.
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

VAULT = Path("/home/bill/.local/share/percival-f4-fixture/notes-vault")
KHAN = Path("/home/bill/.local/share/percival-f4-fixture/khan-calendar")
NOTES_IMAGE = "sha256:ef4082ef13905cdaa0da23830bcc6c5b88ca3beb30074e11d56593d11a097460"
KHAN_IMAGE = "sha256:55cd5a038d22e253693d1d0681e108f57b41f060ecbeb231dad3e2f7edd51914"


def mcp_call(image, mounts, env, network, requests, timeout=300):
    cmd = ["docker", "run", "--rm", "-i", "--network", network]
    for k, v in env.items():
        cmd.extend(["-e", f"{k}={v}"])
    for src, tgt, mode in mounts:
        cmd.extend(["-v", f"{src}:{tgt}:{mode}"])
    cmd.append(image)
    payload = "\n".join(json.dumps(r) for r in requests) + "\n"
    proc = subprocess.run(cmd, input=payload, capture_output=True, text=True, timeout=timeout)
    responses = []
    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            responses.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    return responses, proc


def init_seq():
    return [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "percival-f4", "version": "1.0"}}},
        {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}},
    ]


def call_tool(req_id, name, args):
    return {"jsonrpc": "2.0", "id": req_id, "method": "tools/call", "params": {"name": name, "arguments": args}}


def check(cond, msg):
    if not cond:
        print(f"FAIL: {msg}")
        sys.exit(1)
    print(f"OK: {msg}")


def hash_dir(p):
    h = hashlib.sha256()
    for fp in sorted(p.rglob("*")):
        if fp.is_file():
            rel = fp.relative_to(p).as_posix().encode()
            h.update(rel + b"\0")
            h.update(hashlib.sha256(fp.read_bytes()).digest())
    return h.hexdigest()


def reset_dir(p):
    if p.exists():
        shutil.rmtree(p)
    p.mkdir(parents=True, mode=0o777)
    os.chmod(p, 0o777)


def test_notes_backup_restore_recreate():
    print("=" * 70)
    print("TEST: Notes (Percival) — backup, recreate, restore (item 2)")
    print("=" * 70)

    reset_dir(VAULT)

    note_dir = VAULT / "percival-f4-test"
    note_dir.mkdir(mode=0o777)
    os.chmod(note_dir, 0o777)
    note_path = note_dir / "seed.md"
    note_bytes = b"---\ntype: note\ntags: [percival-f4]\n---\n\n# F4 seed (Percival)\n\nFixture: baseline before backup.\n"
    note_path.write_bytes(note_bytes)
    os.chmod(note_path, 0o666)
    pre_hash = hash_dir(VAULT)
    print(f"  pre-hash: {pre_hash[:16]}…")

    # 2. Snapshot
    backup = VAULT.with_suffix(".vault.bak")
    if backup.exists():
        shutil.rmtree(backup)
    shutil.copytree(VAULT, backup)

    # 3. Recreate: fresh container process, get_stats
    responses, _ = mcp_call(
        NOTES_IMAGE,
        [(str(VAULT), "/vault", "rw")],
        {},
        "none",
        init_seq() + [call_tool(2, "notes_get_stats", {})],
        timeout=180,
    )
    stats_resp = next((r for r in responses if r.get("id") == 2), None)
    if not stats_resp:
        check(False, "Percival notes get_stats after recreate (no response)")
    check("error" not in stats_resp, "Percival notes get_stats after recreate")
    text = json.dumps(stats_resp["result"])
    check("percival-f4-test/seed.md" in text, "Percival stats show the seed note")

    # 4. Delete the note
    responses, _ = mcp_call(
        NOTES_IMAGE,
        [(str(VAULT), "/vault", "rw")],
        {},
        "none",
        init_seq() + [call_tool(2, "notes_rm", {"path": "percival-f4-test/seed.md"})],
        timeout=180,
    )
    rm_resp = next((r for r in responses if r.get("id") == 2), None)
    check(rm_resp and "error" not in rm_resp, "Percival notes rm seed.md")
    check(not (VAULT / "percival-f4-test/seed.md").exists(), "Percival file removed from vault")

    # 5. Restore
    shutil.rmtree(VAULT)
    shutil.copytree(backup, VAULT)
    shutil.rmtree(backup)
    os.chmod(VAULT, 0o777)
    for root, dirs, files in os.walk(VAULT):
        for d in dirs:
            os.chmod(os.path.join(root, d), 0o777)
        for f in files:
            os.chmod(os.path.join(root, f), 0o666)
    post_hash = hash_dir(VAULT)
    check(post_hash == pre_hash, "Percival backup hash matches post-restore hash")

    # 6. Verify
    responses, _ = mcp_call(
        NOTES_IMAGE,
        [(str(VAULT), "/vault", "rw")],
        {},
        "none",
        init_seq() + [call_tool(2, "notes_get_stats", {})],
        timeout=180,
    )
    stats_resp = next((r for r in responses if r.get("id") == 2), None)
    check(stats_resp and "error" not in stats_resp, "Percival notes get_stats after restore")
    text = json.dumps(stats_resp["result"])
    check("percival-f4-test/seed.md" in text, "Percival stats after restore show the seed note")

    shutil.rmtree(VAULT)
    print("PASS: percival notes backup/recreate/restore")


def test_khan_backup_restore_recreate():
    print("=" * 70)
    print("TEST: Khan (Percival) — backup, recreate, restore (item 2)")
    print("=" * 70)

    reset_dir(KHAN)
    (KHAN / "khal.conf").write_text(
        "[calendars]\n"
        "  [[percival_f4fixture]]\n"
        "    type = local\n"
        "    path = /data/percival_f4fixture/**\n"
        "[locale]\n"
        "  timeformat = %H:%M\n"
        "  dateformat = %Y-%m-%d\n"
        "  longdateformat = %Y-%m-%d\n"
    )
    os.chmod(KHAN / "khal.conf", 0o666)
    (KHAN / "percival_f4fixture").mkdir(mode=0o777)
    os.chmod(KHAN / "percival_f4fixture", 0o777)

    # 1. Trigger khan auto-heal via khan_list_calendars
    proc = subprocess.run(
        ["docker", "run", "--rm", "-i", "--network", "none",
         "-e", "KHAN_WORKSPACE_DIR=/data", "-e", "KHAL_CONFIG=/data/khal.conf",
         "-v", f"{KHAN}:/data:rw",
         KHAN_IMAGE],
        input="\n".join(json.dumps(r) for r in init_seq() + [call_tool(2, "khan_list_calendars", {})]) + "\n",
        capture_output=True, text=True, timeout=180,
    )
    check(KHAN.joinpath("khal.db").exists(), "Percival khan auto-heal wrote khal.db")
    check(KHAN.joinpath("khal.conf").exists(), "Percival khan auto-heal preserved khal.conf")
    khal_conf_text = (KHAN / "khal.conf").read_text()
    check("[[" in khal_conf_text and "type = calendar" in khal_conf_text, "Percival khan auto-heal rewrote calendars")
    pre_hash = hash_dir(KHAN)
    print(f"  pre-hash (after auto-heal): {pre_hash[:16]}…")

    # 2. Backup
    backup = KHAN.with_suffix(".calendar.bak")
    if backup.exists():
        shutil.rmtree(backup)
    shutil.copytree(KHAN, backup)
    backup_hash = hash_dir(backup)
    print(f"  backup hash: {backup_hash[:16]}…")

    # 3. Recreate
    proc = subprocess.run(
        ["docker", "run", "--rm", "-i", "--network", "none",
         "-e", "KHAN_WORKSPACE_DIR=/data", "-e", "KHAL_CONFIG=/data/khal.conf",
         "-v", f"{KHAN}:/data:rw",
         KHAN_IMAGE],
        input="\n".join(json.dumps(r) for r in init_seq() + [call_tool(2, "khan_list_calendars", {})]) + "\n",
        capture_output=True, text=True, timeout=180,
    )
    check("khal.call" in proc.stderr, "Percival khan recreate executed khal CLI")
    check("returncode\": 0" in proc.stderr, "Percival khal returned 0 after recreate")

    # 4. Wipe
    shutil.rmtree(KHAN)
    KHAN.mkdir(mode=0o777)
    check(not KHAN.joinpath("khal.db").exists(), "Percival khan data wiped")

    # 5. Restore
    shutil.copytree(backup, KHAN, dirs_exist_ok=True)
    shutil.rmtree(backup)
    post_hash = hash_dir(KHAN)
    check(post_hash == pre_hash, "Percival khan backup hash matches post-restore hash")

    # 6. Verify
    proc = subprocess.run(
        ["docker", "run", "--rm", "-i", "--network", "none",
         "-e", "KHAN_WORKSPACE_DIR=/data", "-e", "KHAL_CONFIG=/data/khal.conf",
         "-v", f"{KHAN}:/data:rw",
         KHAN_IMAGE],
        input="\n".join(json.dumps(r) for r in init_seq() + [call_tool(2, "khan_list_calendars", {})]) + "\n",
        capture_output=True, text=True, timeout=180,
    )
    check("khal.call" in proc.stderr, "Percival khan post-restore executed khal CLI")
    check("returncode\": 0" in proc.stderr, "Percival khal post-restore returned 0")

    shutil.rmtree(KHAN)
    print("PASS: percival khan backup/recreate/restore (filesystem + khal CLI)")


if __name__ == "__main__":
    test_notes_backup_restore_recreate()
    print()
    test_khan_backup_restore_recreate()
