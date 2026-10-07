"""Read-only negative control executed as root inside each F1 MCP container."""

import json
import os
import socket
import sys
import urllib.error
import urllib.request
from pathlib import Path

STATE_DIR = os.environ.get("F1_STATE_DIR", "")
assert STATE_DIR != "", "F1_STATE_DIR must be set when invoking the probe"
PROBE_HOST_PATHS = (
    "/host/run/docker.sock", "/host/var/run/docker.sock",
    "/host/proc/1/root/run/docker.sock", "/host/var/lib/docker/containers",
    "/var/run/docker.sock", "/run/docker.sock",
)
PROTECTED_COVERS = (
    f"{STATE_DIR}/config.json",
    "/host/home/bill/.nanobot/config.json",
    "/host/home/bill/.docker/config.json",
)
visible = {path: os.path.exists(path) for path in PROBE_HOST_PATHS}
for candidate in ("/host/run/docker.sock", "/host/var/run/docker.sock"):
    if visible[candidate]:
        sock = socket.socket(socket.AF_UNIX)
        sock.settimeout(2)
        try:
            sock.connect(candidate)
            visible[candidate] = "CONNECTED (FAIL)"
        except OSError:
            pass
        finally:
            sock.close()
try:
    urllib.request.urlopen("http://127.0.0.1:18081/v1/list", timeout=2)
    tcp = "reachable (FAIL)"
except (OSError, urllib.error.URLError):
    tcp = "unreachable"
cover_leak = {path: os.path.exists(path) for path in PROTECTED_COVERS}
home_mounted = os.path.ismount("/host/home")
home_checkout_visible = (
    os.getuid() == 1000 and os.path.exists("/host/home/bill/Projects/nanobot")
)
report = {
    "uid": os.getuid(),
    "paths": visible,
    "broker_tcp": tcp,
    "host_home_checkout_visible": home_checkout_visible,
    "covered_paths_leak": cover_leak,
    "home_mounted": home_mounted,
}
print(json.dumps(report))
assert not any(visible.values()), visible
assert tcp == "unreachable", tcp
assert not any(cover_leak.values()), cover_leak
assert home_mounted
if os.getuid() == 1000:
    assert home_checkout_visible
mode = sys.argv[1] if len(sys.argv) > 1 else "read"
if mode == "rw":
    marker = Path(os.environ["F1_PROOF_PATH"])
    assert marker.read_text() == "host-to-container\n"
    marker.write_text("container-to-host\n")
    print("host-to-container-to-host marker updated")
elif mode == "ro":
    marker = Path(os.environ["F1_PROOF_PATH"])
    assert marker.read_text() == "host-to-container\n"
    try:
        marker.write_text("unexpected-write\n")
    except OSError:
        pass
    else:
        raise AssertionError("read-only host mount allowed a write")
    print("host read-only reduction blocked the write")
