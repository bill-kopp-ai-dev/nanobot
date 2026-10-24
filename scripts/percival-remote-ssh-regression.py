#!/usr/bin/env python3
"""In-image regression for the Percival Remote SSH transport.

The gateway image ships the OpenSSH client that Remote SSH depends on. This
regression drives the product's own code paths inside the image against an
SSH server that lives in a separate fixture container, so the gateway image
never has to carry openssh-server.

Checks performed inside the gateway image:
  * the client version and the absence of openssh-server in the image;
  * the host-key scan (ssh-keyscan) and the credential probe (ssh with the
    pinned option set, StrictHostKeyChecking=yes) against the fixture;
  * the transport tunnel (-W forwarding) with an HTTP round trip.

The fixture is built from a pinned Debian Forky snapshot and listens on a
throwaway Docker network. Nothing outside the scratch directory is touched.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

FIXTURE_BASE = "debian:forky-slim@sha256:4cee6ff3ebc49e32d55a857e25164ef8e5f8fecff2a186c6393f7e8bd8c23b53"
FIXTURE_SNAPSHOT = "20261020T000000Z"
FIXTURE_TAG = "percival-remote-ssh-fixture:10.6p1"
FIXTURE_USER = "probe"
FIXTURE_PORT = 8765
MARKER = "percival-remote-ssh-ok"

SSHD_CONFIG = """\
Port 22
HostKey /etc/ssh/ssh_host_ed25519_key
HostKey /etc/ssh/ssh_host_rsa_key
PubkeyAuthentication yes
PasswordAuthentication no
KbdInteractiveAuthentication no
PermitRootLogin no
AuthorizedKeysFile /home/probe/.ssh/authorized_keys
StrictModes no
AllowTcpForwarding yes
PermitTunnel no
GatewayPorts no
UsePAM no
X11Forwarding no
PrintMotd no
AcceptEnv LANG LC_*
LogLevel VERBOSE
Subsystem sftp internal-sftp
"""

START_SCRIPT = f"""\
#!/bin/sh
set -eu
mkdir -p /run/sshd /home/{FIXTURE_USER}/.ssh
cp /fixture/client.pub /home/{FIXTURE_USER}/.ssh/authorized_keys
chown {FIXTURE_USER}:{FIXTURE_USER} /home/{FIXTURE_USER}/.ssh/authorized_keys
chmod 600 /home/{FIXTURE_USER}/.ssh/authorized_keys
ssh-keygen -A
/usr/sbin/sshd -D -e -f /etc/ssh/sshd_config &
exec python3 -m http.server {FIXTURE_PORT} --bind 127.0.0.1 --directory /srv
"""

FIXTURE_DOCKERFILE = f"""\
FROM {FIXTURE_BASE}
RUN printf 'deb [check-valid-until=no] http://snapshot.debian.org/archive/debian/{FIXTURE_SNAPSHOT} forky main\\n' > /etc/apt/sources.list && \\
    rm -f /etc/apt/sources.list.d/debian.sources && \\
    apt-get -o Acquire::Check-Valid-Until=false update && \\
    apt-get install -y --no-install-recommends \\
        openssh-server=1:10.6p1-1 python3=3.14.7-3 && \\
    rm -rf /var/lib/apt/lists/*
RUN useradd -m -s /bin/sh {FIXTURE_USER} && \\
    usermod -p 'x' {FIXTURE_USER} && \\
    mkdir -p /home/{FIXTURE_USER}/.nanobot/auth /srv && \\
    printf '{{"channels":{{"websocket":{{"enabled":true,"port":{FIXTURE_PORT}}}}}}}' \\
        > /home/{FIXTURE_USER}/.nanobot/config.json && \\
    : > /home/{FIXTURE_USER}/.nanobot/auth/verifier.json && \\
    printf '{MARKER}' > /srv/marker.txt
COPY sshd_config /etc/ssh/sshd_config
COPY start.sh /usr/local/bin/start.sh
RUN chmod 755 /usr/local/bin/start.sh
EXPOSE 22
ENTRYPOINT ["/usr/local/bin/start.sh"]
"""

CLIENT_SCRIPT = '''"""Runs inside the gateway image and drives the real Remote SSH code paths."""

import asyncio
import json
import os
import shutil
import tempfile
from pathlib import Path

from nanobot.webui.remote_ssh import (
    RemoteProfile,
    open_tunnel,
    probe,
    scan_host_key,
)

MARKER = "percival-remote-ssh-ok"
FIXTURE_PORT = 8765


def record(checks, name, **detail):
    checks.append({"check": name, "status": "passed", **detail})
    print(f"PASS: {name}", flush=True)


async def run(*args):
    process = await asyncio.create_subprocess_exec(
        *args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()
    return process.returncode, stdout, stderr


async def main():
    checks = []
    host = os.environ["FIXTURE_HOST"]
    port = int(os.environ["FIXTURE_PORT"])

    code, _, stderr = await run("ssh", "-V")
    version = stderr.decode(errors="replace").strip()
    if code or not version.startswith("OpenSSH_"):
        raise SystemExit(f"ssh -V failed: {code} {version}")
    numbers = version.split()[0].removeprefix("OpenSSH_")
    parts = numbers.split(".")
    major = int(parts[0])
    minor = int("".join(character for character in parts[1] if character.isdigit()))
    if (major, minor) < (10, 4):
        raise SystemExit(f"ssh client is below the CVE-2026-60002 fix: {version}")
    record(checks, "image ssh client version", version=version)

    code, stdout, _ = await run("dpkg-query", "-W", "-f=${Status}", "openssh-server")
    if code == 0 and b"install ok installed" in stdout:
        raise SystemExit("the gateway image must not carry openssh-server")
    record(checks, "image has no openssh-server", status=stdout.decode().strip() or "absent")

    workdir = Path(tempfile.mkdtemp(prefix="remote-ssh-regression-"))
    key = workdir / "id_ed25519"
    shutil.copyfile(os.environ["CLIENT_KEY"], key)
    os.chmod(key, 0o600)
    known_hosts = workdir / "known_hosts"

    profile = RemoteProfile(
        name="fixture",
        host=f"probe@{host}",
        port=port,
        identity_file=str(key),
    )

    line, fingerprint = await scan_host_key(profile)
    if not fingerprint.startswith("SHA256:"):
        raise SystemExit(f"unexpected host key fingerprint: {fingerprint}")
    known_hosts.write_text(line)
    record(checks, "host key scan", fingerprint=fingerprint)

    data = await probe(profile, known_hosts)
    if data.get("port") != FIXTURE_PORT or data.get("auth_required") is not True:
        raise SystemExit(f"unexpected probe result: {data}")
    record(checks, "credential probe", port=data["port"], hostname=data.get("hostname"))

    tunnel = await open_tunnel(profile, FIXTURE_PORT, known_hosts)
    try:
        reader, writer = await asyncio.open_connection("127.0.0.1", tunnel.port)
        writer.write(b"GET /marker.txt HTTP/1.0\\r\\n\\r\\n")
        await writer.drain()
        payload = await reader.read()
        writer.close()
        if MARKER.encode() not in payload:
            raise SystemExit(f"tunnel did not carry the fixture payload: {payload!r}")
    finally:
        await tunnel.close()
    record(checks, "transport tunnel", local_port=tunnel.port, payload=MARKER)

    shutil.rmtree(workdir, ignore_errors=True)
    print(json.dumps({"checks": checks}, indent=2))


asyncio.run(main())
'''


def run(args: list[str], *, check: bool = True, timeout: int = 600) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(args, text=True, capture_output=True, timeout=timeout)
    if check and result.returncode:
        raise RuntimeError(f"command failed ({result.returncode}): {args[0]}\n"
                           f"{result.stdout[-4000:]}\n{result.stderr[-4000:]}")
    return result


def build_fixture(context: Path) -> None:
    context.mkdir(parents=True, exist_ok=True)
    (context / "Dockerfile").write_text(FIXTURE_DOCKERFILE, encoding="utf-8")
    (context / "sshd_config").write_text(SSHD_CONFIG, encoding="utf-8")
    (context / "start.sh").write_text(START_SCRIPT, encoding="utf-8")
    run(["docker", "build", "--platform", "linux/amd64", "-t", FIXTURE_TAG, str(context)])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gateway-image", required=True, help="gateway image under test")
    parser.add_argument("--scratch-parent", default="/tmp", help="parent directory for the scratch tree")
    parser.add_argument("--output", default="", help="path for the JSON result file")
    args = parser.parse_args()

    scratch = Path(args.scratch_parent).resolve() / f"percival-remote-ssh-{uuid.uuid4().hex[:8]}"
    scratch.mkdir(parents=True)
    network = f"percival-remote-ssh-{uuid.uuid4().hex[:8]}"
    fixture = f"{network}-fixture"
    try:
        if run(["docker", "image", "inspect", FIXTURE_TAG], check=False).returncode:
            build_fixture(scratch / "fixture-context")
        run(["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-C", "percival-remote-ssh-regression",
             "-f", str(scratch / "id_ed25519")])
        (scratch / "client.py").write_text(CLIENT_SCRIPT, encoding="utf-8")

        run(["docker", "network", "create", network])
        run(["docker", "run", "-d", "--name", fixture, "--network", network,
             "--mount", f"type=bind,src={scratch / 'id_ed25519.pub'},dst=/fixture/client.pub,readonly",
             FIXTURE_TAG])

        environment = {
            "FIXTURE_HOST": fixture,
            "FIXTURE_PORT": "22",
            "CLIENT_KEY": "/regression/id_ed25519",
        }
        command = [
            "docker", "run", "--rm", "--network", network,
            "--mount", f"type=bind,src={scratch},dst=/regression,readonly",
            *[f"--env={key}={value}" for key, value in environment.items()],
            "--entrypoint", "python", args.gateway_image, "/regression/client.py",
        ]
        result = run(command, check=False, timeout=900)
        (scratch / "regression-output.txt").write_text(result.stdout + result.stderr, encoding="utf-8")
        print(result.stdout, end="")
        if result.returncode:
            print(result.stderr[-4000:], file=sys.stderr)
            raise RuntimeError("the Remote SSH regression failed inside the gateway image")

        payload = json.loads(result.stdout[result.stdout.index("{"):])
        record = {
            "check": "percival remote ssh in-image regression",
            "gatewayImage": args.gateway_image,
            "fixtureImage": FIXTURE_TAG,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "checks": payload["checks"],
        }
        destination = Path(args.output) if args.output else scratch / "results.json"
        destination.write_text(json.dumps(record, indent=2), encoding="utf-8")
        print(f"results: {destination}")
        return 0
    finally:
        run(["docker", "rm", "-f", fixture], check=False)
        run(["docker", "network", "rm", network], check=False)
        shutil.rmtree(scratch, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
