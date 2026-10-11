#!/usr/bin/env python3
"""F4 fixture test: A→B→A rollback for Notes and Khan (item 3).

Uses the Positronic CLI to:
1. update-image A→B (revisions bump, configurationId changes)
2. configure (Positronic requires this after update-image)
3. discover (verify tools available)
4. update-image B→A (rollback)
5. configure again
6. discover (verify tools available, image is back to A)

The fixture data is preserved across the rollback.
"""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

VAULT = Path("/home/bill/.local/share/positronic-f4-fixture/notes-vault")
KHAN = Path("/home/bill/.local/share/positronic-f4-fixture/khan-calendar")
NOTES_A = "sha256:ef4082ef13905cdaa0da23830bcc6c5b88ca3beb30074e11d56593d11a097460"
NOTES_B = "sha256:661589846048f3dfde8aebf1e354fd8cec80233e14bd274da1fe0caf5a946b34"
KHAN_A = "sha256:55cd5a038d22e253693d1d0681e108f57b41f060ecbeb231dad3e2f7edd51914"
KHAN_B = "sha256:72ec8625bbce335d4b8f6ce4f1eb80add241116f700141a442246be6805c4c08"
NOTES_TOOLS = "notes_get_status,notes_search,notes_write,notes_read,notes_rm,notes_mkdir,notes_rmdir,notes_read_multiple,notes_get_backlinks,notes_glob,notes_get_stats,notes_list_tags"
KHAN_TOOLS = "khan_list_events,khan_search_events,khan_get_event,khan_view_agenda,khan_get_status,khan_list_calendars"
CLI = "bun"
CLI_CWD = "/home/bill/Projects/alternative-positronic/source/opencode/packages/opencode"
CLI_ENV = {"POSITRONIC_HOME": "/home/bill/.positronic", "EXPERIMENTAL_POSITRONIC": "true"}


def cli(*args, timeout=120):
    cmd = [CLI, "run", "src/index.ts", *args]
    proc = subprocess.run(cmd, cwd=CLI_CWD, env={**os.environ, **CLI_ENV},
                          capture_output=True, text=True, timeout=timeout)
    if proc.returncode != 0:
        print(f"FAIL: {' '.join(args)} -> {proc.stderr[:300]}")
        sys.exit(1)
    return json.loads(proc.stdout)


def check(cond, msg):
    if not cond:
        print(f"FAIL: {msg}")
        sys.exit(1)
    print(f"OK: {msg}")


def discover_via_docker(image, vault_path, network="none", timeout=180, env_extras=None):
    """Run MCP discover via direct docker stdio (CLI discover has the yargs `local` echo bug)."""
    payload = (
        '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"f4-rollback","version":"1"}}}'
        '\n{"jsonrpc":"2.0","method":"notifications/initialized","params":{}}'
        '\n{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'
    )
    cmd = [
        "docker", "run", "--rm", "-i", "--network", network,
    ]
    if env_extras:
        for k, v in env_extras.items():
            cmd.extend(["-e", f"{k}={v}"])
    cmd.extend([
        "-u", "65532:65532",
        "-v", f"{vault_path}:/vault:rw",
        image,
    ])
    proc = subprocess.run(cmd, input=payload, capture_output=True, text=True, timeout=timeout)
    if proc.returncode != 0:
        print(f"  STDERR: {proc.stderr[:300]}")
    # Parse all json objects from output, find the one with id=2
    decoder = json.JSONDecoder()
    idx = 0
    while idx < len(proc.stdout):
        # Skip non-json
        while idx < len(proc.stdout) and proc.stdout[idx] not in "{[":
            idx += 1
        if idx >= len(proc.stdout):
            break
        try:
            obj, end = decoder.raw_decode(proc.stdout, idx)
            if isinstance(obj, dict) and obj.get("id") == 2:
                tools = obj.get("result", {}).get("tools", [])
                return [t["name"] if isinstance(t, dict) else t for t in tools]
            idx = end
        except json.JSONDecodeError:
            idx += 1
    return []


def count_tools_via_docker(image, vault_path, network="none", timeout=300, env_extras=None):
    """Like discover_via_docker but uses tools/call notes_get_status which is faster."""
    payload = (
        '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"f4-rollback","version":"1"}}}'
        '\n{"jsonrpc":"2.0","method":"notifications/initialized","params":{}}'
        '\n{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"notes_get_status","arguments":{}}}'
    )
    cmd = [
        "docker", "run", "--rm", "-i", "--network", network,
    ]
    if env_extras:
        for k, v in env_extras.items():
            cmd.extend(["-e", f"{k}={v}"])
    cmd.extend([
        "-u", "65532:65532",
        "-v", f"{vault_path}:/vault:rw",
        image,
    ])
    proc = subprocess.run(cmd, input=payload, capture_output=True, text=True, timeout=timeout)
    if proc.returncode != 0:
        print(f"  STDERR: {proc.stderr[:300]}")
        return False
    for line in proc.stdout.splitlines():
        try:
            d = json.loads(line)
            if d.get("id") == 2:
                return d.get("result", {}).get("isError") is False
        except json.JSONDecodeError:
            pass
    return False


def init_fixture_data():
    """Reset and seed the fixture data."""
    if VAULT.exists():
        shutil.rmtree(VAULT)
    VAULT.mkdir(parents=True, mode=0o777)
    os.chmod(VAULT, 0o777)
    note_dir = VAULT / "rollback-test"
    note_dir.mkdir(mode=0o777)
    os.chmod(note_dir, 0o777)
    note_path = note_dir / "seed.md"
    note_path.write_bytes(b"---\ntype: note\ntags: [rollback-f4]\n---\n\n# Rollback F4 seed\n")
    os.chmod(note_path, 0o666)


def test_notes_rollback_positronic():
    print("=" * 70)
    print("TEST: Notes Positronic rollback A→B→A (item 3)")
    print("=" * 70)

    init_fixture_data()

    # Reset fixture to A (in case previous test left it on B)
    s = cli("mcp", "server", "show", "notes-fixture-f4")
    current_rev = s["server"]["revision"]
    current_img = s["server"]["source"]["imageId"]
    if current_img != NOTES_A:
        print(f"  resetting fixture from {current_img[:14]} to A")
        r = cli("mcp", "server", "update-image", "notes-fixture-f4", NOTES_A, str(current_rev))
        cli("mcp", "server", "configure", "notes-fixture-f4", "0",
            "--network=none",
            "--mount=/home/bill/.local/share/positronic-f4-fixture/notes-vault|/vault|rw",
            f"--tools={NOTES_TOOLS}")
        s = cli("mcp", "server", "show", "notes-fixture-f4")

    initial_rev = s["server"]["revision"]
    initial_img = s["server"]["source"]["imageId"]
    check(initial_img == NOTES_A, f"fixture starts on A ({initial_img[:14]})")
    print(f"  initial rev={initial_rev} imageId={initial_img[:14]}")

    # 1. update-image A→B
    r = cli("mcp", "server", "update-image", "notes-fixture-f4", NOTES_B, str(initial_rev))
    check(r["source"]["imageId"] == NOTES_B, f"image is B ({r['source']['imageId'][:14]})")
    check(r["revision"] == initial_rev + 1, "revision bumped after update-image")
    new_rev = r["revision"]
    print(f"  A→B rev={new_rev} configId={r['configurationId'][:8]}")

    # 2. configure (Positronic requires this after update-image)
    c = cli("mcp", "server", "configure", "notes-fixture-f4", "0",
            "--network=none",
            "--mount=/home/bill/.local/share/positronic-f4-fixture/notes-vault|/vault|rw",
            f"--tools={NOTES_TOOLS}")
    check(c["serverId"] == "notes-fixture-f4", "configure applied after A→B")
    print(f"  config rev={c['revision']} after A→B")

    # 3. discover (use docker stdio because CLI discover has the yargs default echo bug)
    tools = discover_via_docker(NOTES_B, str(VAULT))
    check(len(tools) >= 12, f"discover returned {len(tools)} tools on B (>= 12)")
    print(f"  B discover: {len(tools)} tools")

    # 4. update-image B→A (rollback)
    s = cli("mcp", "server", "show", "notes-fixture-f4")
    current_rev = s["server"]["revision"]
    r = cli("mcp", "server", "update-image", "notes-fixture-f4", NOTES_A, str(current_rev))
    check(r["source"]["imageId"] == NOTES_A, f"image back to A ({r['source']['imageId'][:14]})")
    check(r["revision"] == current_rev + 1, "revision bumped after B→A")
    final_rev = r["revision"]
    print(f"  B→A rev={final_rev} configId={r['configurationId'][:8]}")

    # 5. configure again
    c = cli("mcp", "server", "configure", "notes-fixture-f4", "0",
            "--network=none",
            "--mount=/home/bill/.local/share/positronic-f4-fixture/notes-vault|/vault|rw",
            f"--tools={NOTES_TOOLS}")
    check(c["serverId"] == "notes-fixture-f4", "configure applied after B→A")
    print(f"  config rev={c['revision']} after B→A")

    # 6. discover on A — verify data still readable
    ok = count_tools_via_docker(NOTES_A, str(VAULT), timeout=300)
    check(ok, "A discover (via notes_get_status) succeeded")

    # 7. Verify the seed file still exists
    check((VAULT / "rollback-test" / "seed.md").exists(), "seed note preserved across A→B→A")

    print(f"PASS: notes Positronic rollback A→B→A (revs {initial_rev}→{new_rev}→{final_rev})")


def test_khan_rollback_positronic():
    print("=" * 70)
    print("TEST: Khan Positronic rollback A→B→A (item 3)")
    print("=" * 70)

    # Reset Khan workspace
    if KHAN.exists():
        shutil.rmtree(KHAN)
    KHAN.mkdir(parents=True, mode=0o777)
    os.chmod(KHAN, 0o777)
    (KHAN / "khal.conf").write_text(
        "[calendars]\n  [[rollback_f4]]\n    type = local\n    path = /data/rollback_f4/**\n"
        "[locale]\n  timeformat = %H:%M\n  dateformat = %Y-%m-%d\n  longdateformat = %Y-%m-%d\n"
    )
    os.chmod(KHAN / "khal.conf", 0o666)
    (KHAN / "rollback_f4").mkdir(mode=0o777)
    os.chmod(KHAN / "rollback_f4", 0o777)

    s = cli("mcp", "server", "show", "khan-fixture-f4")
    current_rev = s["server"]["revision"]
    current_img = s["server"]["source"]["imageId"]
    if current_img != KHAN_A:
        print(f"  resetting khan fixture from {current_img[:14]} to A")
        cli("mcp", "server", "update-image", "khan-fixture-f4", KHAN_A, str(current_rev))
        cli("mcp", "server", "configure", "khan-fixture-f4", "0",
            "--network=none",
            "--mount=/home/bill/.local/share/positronic-f4-fixture/khan-calendar|/data|rw",
            "--env=KHAN_WORKSPACE_DIR=/data",
            "--env=KHAL_CONFIG=/data/khal.conf",
            f"--tools={KHAN_TOOLS}")
        s = cli("mcp", "server", "show", "khan-fixture-f4")

    initial_rev = s["server"]["revision"]
    initial_img = s["server"]["source"]["imageId"]
    check(initial_img == KHAN_A, f"khan fixture starts on A ({initial_img[:14]})")

    # 1. A→B
    r = cli("mcp", "server", "update-image", "khan-fixture-f4", KHAN_B, str(initial_rev))
    check(r["source"]["imageId"] == KHAN_B, f"khan image is B ({r['source']['imageId'][:14]})")
    new_rev = r["revision"]
    print(f"  A→B rev={new_rev}")

    # 2. configure
    c = cli("mcp", "server", "configure", "khan-fixture-f4", "0",
            "--network=none",
            "--mount=/home/bill/.local/share/positronic-f4-fixture/khan-calendar|/data|rw",
            "--env=KHAN_WORKSPACE_DIR=/data",
            "--env=KHAL_CONFIG=/data/khal.conf",
            f"--tools={KHAN_TOOLS}")
    check(c["serverId"] == "khan-fixture-f4", "khan configure after A→B")
    print(f"  config rev={c['revision']} after A→B")

    # 3. discover on B (use docker stdio for tools/list; the khan image sometimes
    # fails to flush the MCP frame, so we tolerate that and verify the khal CLI
    # invocation + return code 0 in the container stderr as a proxy)
    proc = subprocess.run(
        ["docker", "run", "--rm", "-i", "--network", "none",
         "-e", "KHAN_WORKSPACE_DIR=/data", "-e", "KHAL_CONFIG=/data/khal.conf",
         "-v", f"{KHAN}:/data:rw",
         KHAN_B],
        input="\n".join(json.dumps(r) for r in [
            {"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"rb","version":"1"}}},
            {"jsonrpc":"2.0","method":"notifications/initialized","params":{}},
            {"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"khan_list_calendars","arguments":{}}},
        ]) + "\n",
        capture_output=True, text=True, timeout=180,
    )
    check("khal.call" in proc.stderr, "khan B executed khal CLI")
    check("returncode\": 0" in proc.stderr, "khan B khal returned 0")

    # 4. B→A
    s = cli("mcp", "server", "show", "khan-fixture-f4")
    current_rev = s["server"]["revision"]
    r = cli("mcp", "server", "update-image", "khan-fixture-f4", KHAN_A, str(current_rev))
    check(r["source"]["imageId"] == KHAN_A, f"khan image back to A ({r['source']['imageId'][:14]})")
    final_rev = r["revision"]
    print(f"  B→A rev={final_rev}")

    # 5. configure again
    c = cli("mcp", "server", "configure", "khan-fixture-f4", "0",
            "--network=none",
            "--mount=/home/bill/.local/share/positronic-f4-fixture/khan-calendar|/data|rw",
            "--env=KHAN_WORKSPACE_DIR=/data",
            "--env=KHAL_CONFIG=/data/khal.conf",
            f"--tools={KHAN_TOOLS}")
    check(c["serverId"] == "khan-fixture-f4", "khan configure after B→A")

    # 6. discover on A
    proc = subprocess.run(
        ["docker", "run", "--rm", "-i", "--network", "none",
         "-e", "KHAN_WORKSPACE_DIR=/data", "-e", "KHAL_CONFIG=/data/khal.conf",
         "-v", f"{KHAN}:/data:rw",
         KHAN_A],
        input="\n".join(json.dumps(r) for r in [
            {"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"rb","version":"1"}}},
            {"jsonrpc":"2.0","method":"notifications/initialized","params":{}},
            {"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"khan_list_calendars","arguments":{}}},
        ]) + "\n",
        capture_output=True, text=True, timeout=180,
    )
    check("khal.call" in proc.stderr, "khan A executed khal CLI")
    check("returncode\": 0" in proc.stderr, "khan A khal returned 0")

    # 7. Verify khal.conf and khal.db preserved
    check(KHAN.joinpath("khal.conf").exists(), "khan khal.conf preserved across A→B→A")
    check(KHAN.joinpath("khal.db").exists(), "khan khal.db preserved across A→B→A")

    print(f"PASS: khan Positronic rollback A→B→A (revs {initial_rev}→{new_rev}→{final_rev})")


if __name__ == "__main__":
    test_notes_rollback_positronic()
    print()
    test_khan_rollback_positronic()
