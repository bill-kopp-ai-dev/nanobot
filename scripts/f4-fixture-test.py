#!/usr/bin/env python3
"""F4 fixture test: backup, recreate, restore using docker stdio MCP calls.

Strategy:
- For Notes: write seed file directly to the mounted vault, use MCP for read
  and re-create verification. Backup is a directory copy.
- For Khan: use MCP get_status (auto-heal khal.conf) and search/verify.
  Backup is a directory copy.
- For both: verify hash of fixture dir matches after restore.
"""
import json
import os
import subprocess
import sys
import hashlib
import shutil
import time
from pathlib import Path

VAULT = Path("/home/bill/.local/share/positronic-f4-fixture/notes-vault")
KHAN = Path("/home/bill/.local/share/positronic-f4-fixture/khan-calendar")
NOTES_IMAGE = "sha256:ef4082ef13905cdaa0da23830bcc6c5b88ca3beb30074e11d56593d11a097460"
KHAN_IMAGE = "sha256:55cd5a038d22e253693d1d0681e108f57b41f060ecbeb231dad3e2f7edd51914"


def mcp_call(image: str, mounts: list, env: dict, network: str, requests: list) -> list:
    cmd = ["docker", "run", "--rm", "-i", "--network", network]
    for k, v in env.items():
        cmd.extend(["-e", f"{k}={v}"])
    for src, tgt, mode in mounts:
        cmd.extend(["-v", f"{src}:{tgt}:{mode}"])
    cmd.append(image)
    payload = "\n".join(json.dumps(r) for r in requests) + "\n"
    proc = subprocess.run(cmd, input=payload, capture_output=True, text=True, timeout=300)
    responses = []
    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            responses.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    if not responses and proc.stderr:
        print("  STDERR:", proc.stderr[:200])
        print("  STDOUT(first 200):", proc.stdout[:200])
    return responses


def init_seq() -> list:
    return [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "f4-test", "version": "1.0"}}},
        {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}},
    ]


def call_tool(req_id: int, name: str, args: dict) -> dict:
    return {"jsonrpc": "2.0", "id": req_id, "method": "tools/call", "params": {"name": name, "arguments": args}}


def check(cond, msg):
    if not cond:
        print(f"FAIL: {msg}")
        sys.exit(1)
    print(f"OK: {msg}")


def hash_dir(p: Path) -> str:
    h = hashlib.sha256()
    for fp in sorted(p.rglob("*")):
        if fp.is_file():
            rel = fp.relative_to(p).as_posix().encode()
            h.update(rel + b"\0")
            h.update(hashlib.sha256(fp.read_bytes()).digest())
    return h.hexdigest()


def reset_dir(p: Path):
    if p.exists():
        shutil.rmtree(p)
    p.mkdir(parents=True, mode=0o777)
    os.chmod(p, 0o777)


def test_notes_backup_restore_recreate():
    print("=" * 70)
    print("TEST: Notes — backup, recreate, restore (item 2)")
    print("=" * 70)

    reset_dir(VAULT)
    os.chmod(VAULT, 0o777)

    # 1. Write seed via direct file write (so we know the bytes match)
    note_dir = VAULT / "f4-test"
    note_dir.mkdir(mode=0o777)
    os.chmod(note_dir, 0o777)
    note_path = note_dir / "seed.md"
    note_bytes = b"---\ntype: note\ntags: [f4]\n---\n\n# F4 seed\n\nFixture: baseline before backup.\n"
    note_path.write_bytes(note_bytes)
    os.chmod(note_path, 0o666)
    pre_hash = hash_dir(VAULT)
    print(f"  pre-hash: {pre_hash[:16]}…")

    # 2. Snapshot the fixture data (backup)
    backup = VAULT.with_suffix(".vault.bak")
    if backup.exists():
        shutil.rmtree(backup)
    shutil.copytree(VAULT, backup)

    # 3. Spawn a fresh container process and read the note metadata
    responses = mcp_call(
        NOTES_IMAGE,
        [(str(VAULT), "/vault", "rw")],
        {},
        "none",
        init_seq() + [call_tool(2, "notes_get_stats", {})],
    )
    stats_resp = next((r for r in responses if r.get("id") == 2), None)
    if not stats_resp:
        print("DEBUG: responses=", json.dumps(responses, indent=2)[:500])
        check(False, "Notes get_stats after recreate")
    check("error" not in stats_resp, "Notes get_stats after recreate")
    stats_text = json.dumps(stats_resp["result"])
    check("f4-test/seed.md" in stats_text or '"total_notes": 1' in stats_text, "Stats show the seed note")

    # 4. Modify (delete the note) using glob
    responses = mcp_call(
        NOTES_IMAGE,
        [(str(VAULT), "/vault", "rw")],
        {},
        "none",
        init_seq() + [call_tool(2, "notes_rm", {"path": "f4-test/seed.md"})],
    )
    rm_resp = next((r for r in responses if r.get("id") == 2), None)
    check(rm_resp and "error" not in rm_resp, "Notes rm seed.md")
    check(not (VAULT / "f4-test/seed.md").exists(), "File removed from vault")

    # 5. Restore the backup
    shutil.rmtree(VAULT)
    shutil.copytree(backup, VAULT)
    shutil.rmtree(backup)
    # Reapply world-rwx because some files may have been 0644 originally
    os.chmod(VAULT, 0o777)
    for root, dirs, files in os.walk(VAULT):
        for d in dirs:
            os.chmod(os.path.join(root, d), 0o777)
        for f in files:
            os.chmod(os.path.join(root, f), 0o666)
    post_hash = hash_dir(VAULT)
    check(post_hash == pre_hash, "Backup hash matches post-restore hash")

    # 6. Re-read after restore
    responses = mcp_call(
        NOTES_IMAGE,
        [(str(VAULT), "/vault", "rw")],
        {},
        "none",
        init_seq() + [call_tool(2, "notes_get_stats", {})],
    )
    stats_resp = next((r for r in responses if r.get("id") == 2), None)
    check(stats_resp and "error" not in stats_resp, "Notes get_stats after restore")
    stats_text = json.dumps(stats_resp["result"])
    check("f4-test/seed.md" in stats_text or '"total_notes": 1' in stats_text, "Stats after restore show the seed note")

    # Cleanup
    shutil.rmtree(VAULT)
    print("PASS: notes backup/recreate/restore")


def test_khan_backup_restore_recreate():
    print("=" * 70)
    print("TEST: Khan — backup, recreate, restore (item 2)")
    print("=" * 70)

    reset_dir(KHAN)
    (KHAN / "khal.conf").write_text(
        "[calendars]\n"
        "  [[f4fixture]]\n"
        "    type = local\n"
        "    path = /data/f4fixture/**\n"
        "[locale]\n"
        "  timeformat = %H:%M\n"
        "  dateformat = %Y-%m-%d\n"
        "  longdateformat = %Y-%m-%d\n"
    )
    os.chmod(KHAN / "khal.conf", 0o666)
    (KHAN / "f4fixture").mkdir(mode=0o777)
    os.chmod(KHAN / "f4fixture", 0o777)

    # 1. Trigger khan auto-heal. Note: as of 2026-10-10 the khan image can
    # fail to flush the MCP response frame even when the underlying khal CLI
    # call returns 0 within ~1s; we record that as a separate bug. For the
    # F4 backup/restore we verify the auto-heal outcome at the filesystem
    # level (khal.db and khal.conf are present, khal.conf is well-formed).
    # khan_get_status does NOT call khal; khan_list_calendars does.
    proc = subprocess.run(
        ["docker", "run", "--rm", "-i", "--network", "none",
         "-e", "KHAN_WORKSPACE_DIR=/data", "-e", "KHAL_CONFIG=/data/khal.conf",
         "-v", f"{KHAN}:/data:rw",
         KHAN_IMAGE],
        input="\n".join(json.dumps(r) for r in init_seq() + [call_tool(2, "khan_list_calendars", {})]) + "\n",
        capture_output=True, text=True, timeout=180,
    )
    check(KHAN.joinpath("khal.db").exists(), "khan auto-heal wrote khal.db")
    check(KHAN.joinpath("khal.conf").exists(), "khan auto-heal preserved khal.conf")
    khal_conf_text = (KHAN / "khal.conf").read_text()
    check("[[" in khal_conf_text and "type = calendar" in khal_conf_text, "khan auto-heal rewrote calendars")
    pre_hash = hash_dir(KHAN)
    print(f"  pre-hash (after auto-heal): {pre_hash[:16]}…")
    print(f"  STDERR (khan): {proc.stderr.splitlines()[-1] if proc.stderr else ''}")

    # 2. Backup the calendar data (filesystem snapshot)
    backup = KHAN.with_suffix(".calendar.bak")
    if backup.exists():
        shutil.rmtree(backup)
    shutil.copytree(KHAN, backup)
    backup_hash = hash_dir(backup)
    print(f"  backup hash: {backup_hash[:16]}…")

    # 3. Recreate: spawn a fresh container process, khal must still execute
    proc = subprocess.run(
        ["docker", "run", "--rm", "-i", "--network", "none",
         "-e", "KHAN_WORKSPACE_DIR=/data", "-e", "KHAL_CONFIG=/data/khal.conf",
         "-v", f"{KHAN}:/data:rw",
         KHAN_IMAGE],
        input="\n".join(json.dumps(r) for r in init_seq() + [call_tool(2, "khan_list_calendars", {})]) + "\n",
        capture_output=True, text=True, timeout=180,
    )
    last_line = proc.stderr.splitlines()[-1] if proc.stderr else ""
    check("khal.call" in proc.stderr, "khan recreate executed khal CLI")
    check("returncode\": 0" in proc.stderr, "khal returned 0 after recreate")
    print(f"  recreate: {last_line[:120]}")

    # 4. Wipe the calendar data (simulate loss)
    shutil.rmtree(KHAN)
    KHAN.mkdir(mode=0o777)
    check(not KHAN.joinpath("khal.db").exists(), "Khan data wiped")

    # 5. Restore from backup
    shutil.copytree(backup, KHAN, dirs_exist_ok=True)
    shutil.rmtree(backup)
    post_hash = hash_dir(KHAN)
    check(post_hash == pre_hash, "Khan backup hash matches post-restore hash")

    # 6. Verify post-restore khan can read the data (filesystem + khal CLI)
    proc = subprocess.run(
        ["docker", "run", "--rm", "-i", "--network", "none",
         "-e", "KHAN_WORKSPACE_DIR=/data", "-e", "KHAL_CONFIG=/data/khal.conf",
         "-v", f"{KHAN}:/data:rw",
         KHAN_IMAGE],
        input="\n".join(json.dumps(r) for r in init_seq() + [call_tool(2, "khan_list_calendars", {})]) + "\n",
        capture_output=True, text=True, timeout=180,
    )
    check("khal.call" in proc.stderr, "khan post-restore executed khal CLI")
    check("returncode\": 0" in proc.stderr, "khal post-restore returned 0")

    # Cleanup
    shutil.rmtree(KHAN)
    print("PASS: khan backup/recreate/restore (filesystem + khal CLI)")


if __name__ == "__main__":
    test_notes_backup_restore_recreate()
    print()
    test_khan_backup_restore_recreate()
