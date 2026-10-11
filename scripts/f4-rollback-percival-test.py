#!/usr/bin/env python3
"""F4 Percival rollback test: A→B→A for Notes and Khan (item 3).

Uses the Percival broker via the WebSocket helper (deploy_mcp.py).
Authenticates with the operator-password file at ~/.nanobot/mcp-docker/operator-password
and the WS/API tokens.
"""
import json
import os
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

VAULT = Path("/home/bill/.local/share/percival-f4-fixture/notes-vault")
KHAN = Path("/home/bill/.local/share/percival-f4-fixture/khan-calendar")
NOTES_A = "sha256:ef4082ef13905cdaa0da23830bcc6c5b88ca3beb30074e11d56593d11a097460"
NOTES_B = "sha256:661589846048f3dfde8aebf1e354fd8cec80233e14bd274da1fe0caf5a946b34"
KHAN_A = "sha256:55cd5a038d22e253693d1d0681e108f57b41f060ecbeb231dad3e2f7edd51914"
KHAN_B = "sha256:72ec8625bbce335d4b8f6ce4f1eb80add241116f700141a442246be6805c4c08"

SECRET_FILE = Path("/home/bill/.nanobot/mcp-docker/webui-token-issue-secret")
BROKER_TOKEN_FILE = Path("/home/bill/.nanobot/mcp-docker/broker-token")
OPERATOR_PASSWORD_FILE = Path("/home/bill/.nanobot/mcp-docker/operator-password")
GATEWAY_HOST = "127.0.0.1"
GATEWAY_PORT = 8765
PERCIVAL_MCP_DIR = Path("/home/bill/.nanobot/mcp-docker")


def check(cond, msg):
    if not cond:
        print(f"FAIL: {msg}")
        sys.exit(1)
    print(f"OK: {msg}")


def get_config_revision():
    """Read tools.mcpDocker.revision from the runtime config."""
    with open("/home/bill/.nanobot/config.json") as f:
        d = json.load(f)
    return d.get("tools", {}).get("mcpDocker", {}).get("revision", 0)


def get_token():
    """Get a fresh WS + API tokens via /webui/bootstrap."""
    secret = SECRET_FILE.read_text().strip()
    req = urllib.request.Request(
        f"http://{GATEWAY_HOST}:{GATEWAY_PORT}/webui/bootstrap",
        headers={
            "Host": f"{GATEWAY_HOST}:{GATEWAY_PORT}",
            "X-Nanobot-Auth": secret,
        },
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        d = json.loads(resp.read())
        return d["token"], d["api_token"]


def call_broker(action, server_id=None, extra_chunks=None):
    """Read-only action (no server_id needed)."""
    return _call_helper(action, server_id, extra_chunks)


def call_broker_ws(action, server_id=None, extra_chunks=None):
    """Mutating action via WS."""
    return _call_helper(action, server_id, extra_chunks)


def _call_helper(action, server_id=None, extra_chunks=None):
    ws_token, api_token = get_token()
    operator_pw = OPERATOR_PASSWORD_FILE.read_text().strip()
    env = os.environ.copy()
    env["PYTHONPATH"] = "/home/bill/Projects/nanobot/.venv/lib/python3.12/site-packages"
    cmd = [
        "python3", str(Path("/home/bill/Projects/nanobot/helpers/deploy_mcp.py")),
        "--ws-token", ws_token,
        "--api-token", api_token,
        "--operator-password", operator_pw,
        action,
    ]
    if server_id is not None:
        cmd.append(server_id)
    if extra_chunks:
        for chunk in extra_chunks:
            cmd.append(chunk)
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120, env=env)
    if proc.returncode != 0:
        print(f"  STDERR: {proc.stderr[:2000]}")
        print(f"  STDOUT: {proc.stdout[:2000]}")
        raise RuntimeError(f"call_broker {action} failed")
    out = proc.stdout.strip()
    if not out:
        raise RuntimeError(f"call_broker {action} returned empty")
    return json.loads(out)


def init_fixture_data():
    if VAULT.exists():
        shutil.rmtree(VAULT)
    VAULT.mkdir(parents=True, mode=0o777)
    os.chmod(VAULT, 0o777)
    note_dir = VAULT / "rollback-test"
    note_dir.mkdir(mode=0o777)
    os.chmod(note_dir, 0o777)
    note_path = note_dir / "seed.md"
    note_path.write_bytes(b"---\ntype: note\ntags: [percival-rollback]\n---\n\n# Rollback F4 seed (Percival)\n")
    os.chmod(note_path, 0o666)


def test_notes_rollback_percival():
    print("=" * 70)
    print("TEST: Notes Percival rollback A→B→A (item 3)")
    print("=" * 70)

    init_fixture_data()
    config_rev = get_config_revision()
    print(f"  config revision = {config_rev}")

    # List current servers
    listing = call_broker("list")
    servers = listing.get("servers", {})
    notes_server = servers.get("notes")
    if not notes_server:
        print("  broker list payload:", json.dumps(listing, indent=2)[:600])
        check(False, "notes server in Percival broker listing")
    initial_src = notes_server["source"]
    initial_img = initial_src.get("imageId") or initial_src.get("reference")
    initial_rev = notes_server["revision"]
    print(f"  initial rev={initial_rev} imageId={initial_img[:14]}")
    if initial_img != NOTES_A:
        # We need to reset to A via update-image
        print(f"  resetting Percival notes pin to A from {initial_img[:14]}")
        cr = get_config_revision()
        call_broker_ws("update-image", server_id="notes", extra_chunks=[
            json.dumps({"source": {"type": "local-image", "reference": NOTES_A}, "expected_revision": cr, "expected_server_revision": initial_rev}),
        ])
        listing = call_broker("list")
        servers = listing.get("servers", {})
        notes_server = servers.get("notes")
        initial_img = notes_server["source"].get("imageId") or notes_server["source"].get("reference")
        initial_rev = notes_server["revision"]
    check(initial_img == NOTES_A, f"Percival notes starts on A ({initial_img[:14]})")

    # A→B
    cr = get_config_revision()
    r = call_broker_ws("update-image", server_id="notes", extra_chunks=[
        json.dumps({"source": {"type": "local-image", "reference": NOTES_B}, "expected_revision": cr, "expected_server_revision": initial_rev}),
    ])
    print(f"  A→B response: {json.dumps(r)[:200]}")
    # Verify via list
    listing = call_broker("list")
    servers = listing.get("servers", {})
    s = servers.get("notes")
    new_img = s["source"].get("imageId") or s["source"].get("reference")
    check(new_img == NOTES_B, f"image is B ({new_img[:14]})")
    b_rev = s["revision"]
    print(f"  A→B rev={b_rev}")

    # B→A
    cr = get_config_revision()
    r = call_broker_ws("update-image", server_id="notes", extra_chunks=[
        json.dumps({"source": {"type": "local-image", "reference": NOTES_A}, "expected_revision": cr, "expected_server_revision": b_rev}),
    ])
    print(f"  B→A response: {json.dumps(r)[:200]}")
    listing = call_broker("list")
    servers = listing.get("servers", {})
    s = servers.get("notes")
    new_img = s["source"].get("imageId") or s["source"].get("reference")
    check(new_img == NOTES_A, f"image back to A ({new_img[:14]})")
    final_rev = s["revision"]
    print(f"  B→A rev={final_rev}")

    # Verify data still readable
    check((VAULT / "rollback-test" / "seed.md").exists(), "Percival notes seed preserved across A→B→A")

    print(f"PASS: notes Percival rollback A→B→A (revs {initial_rev}→{b_rev}→{final_rev})")


def test_khan_rollback_percival():
    print("=" * 70)
    print("TEST: Khan Percival rollback A→B→A (item 3)")
    print("=" * 70)

    if KHAN.exists():
        shutil.rmtree(KHAN)
    KHAN.mkdir(parents=True, mode=0o777)
    os.chmod(KHAN, 0o777)
    (KHAN / "khal.conf").write_text(
        "[calendars]\n  [[percival_rollback_f4]]\n    type = local\n    path = /data/percival_rollback_f4/**\n"
        "[locale]\n  timeformat = %H:%M\n  dateformat = %Y-%m-%d\n  longdateformat = %Y-%m-%d\n"
    )
    os.chmod(KHAN / "khal.conf", 0o666)
    (KHAN / "percival_rollback_f4").mkdir(mode=0o777)
    os.chmod(KHAN / "percival_rollback_f4", 0o777)

    listing = call_broker("list")
    servers = listing.get("servers", {})
    khan_server = servers.get("khan-calendar")
    initial_img = khan_server["source"].get("imageId") or khan_server["source"].get("reference")
    initial_rev = khan_server["revision"]
    print(f"  initial rev={initial_rev} imageId={initial_img[:14]}")
    if initial_img != KHAN_A:
        print(f"  resetting Percival khan pin to A from {initial_img[:14]}")
        cr = get_config_revision()
        call_broker_ws("update-image", server_id="khan-calendar", extra_chunks=[
            json.dumps({"source": {"type": "local-image", "reference": KHAN_A}, "expected_revision": cr, "expected_server_revision": initial_rev}),
        ])
        listing = call_broker("list")
        servers = listing.get("servers", {})
        khan_server = servers.get("khan-calendar")
        initial_img = khan_server["source"].get("imageId") or khan_server["source"].get("reference")
        initial_rev = khan_server["revision"]
    check(initial_img == KHAN_A, f"Percival khan starts on A ({initial_img[:14]})")

    # A→B
    cr = get_config_revision()
    call_broker_ws("update-image", server_id="khan-calendar", extra_chunks=[
        json.dumps({"source": {"type": "local-image", "reference": KHAN_B}, "expected_revision": cr, "expected_server_revision": initial_rev}),
    ])
    listing = call_broker("list")
    servers = listing.get("servers", {})
    s = servers.get("khan-calendar")
    new_img = s["source"].get("imageId") or s["source"].get("reference")
    check(new_img == KHAN_B, f"khan image is B ({new_img[:14]})")
    b_rev = s["revision"]
    print(f"  A→B rev={b_rev}")

    # B→A
    cr = get_config_revision()
    call_broker_ws("update-image", server_id="khan-calendar", extra_chunks=[
        json.dumps({"source": {"type": "local-image", "reference": KHAN_A}, "expected_revision": cr, "expected_server_revision": b_rev}),
    ])
    listing = call_broker("list")
    servers = listing.get("servers", {})
    s = servers.get("khan-calendar")
    new_img = s["source"].get("imageId") or s["source"].get("reference")
    check(new_img == KHAN_A, f"khan image back to A ({new_img[:14]})")
    final_rev = s["revision"]
    print(f"  B→A rev={final_rev}")

    check(KHAN.joinpath("khal.conf").exists(), "Percival khan khal.conf preserved across A→B→A")
    print(f"PASS: khan Percival rollback A→B→A (revs {initial_rev}→{b_rev}→{final_rev})")


if __name__ == "__main__":
    test_notes_rollback_percival()
    print()
    test_khan_rollback_percival()
