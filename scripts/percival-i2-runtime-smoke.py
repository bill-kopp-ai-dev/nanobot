#!/usr/bin/env python3
"""I2 core conformance in an owned disposable Engine 27.5.1 daemon.

Requires Docker + Compose on Linux/amd64 and prebuilt gateway/broker images.
The outer daemon only owns the uniquely named dind container. All product
containers, sockets, host-inventory views and failure injection stay inside it.
No live Percival config, credentials, ports or containers are used.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import subprocess
import tempfile
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

DIND = "docker:27.5.1-dind@sha256:aa3df78ecf320f5fafdce71c659f1629e96e9de0968305fe1de670e0ca9176ce"
ROOT = Path(__file__).resolve().parents[1]
STATE = "/home/nanobot/.nanobot"
PASSWORD = "Runtime-fixture-2026!"


def run(args, *, env=None, input=None, ok=True, timeout=120):
    result = subprocess.run(args, env=env, input=input, text=True,
                            capture_output=True, timeout=timeout)
    if ok and result.returncode:
        raise RuntimeError(f"command failed ({result.returncode}): {args[:5]}\n"
                           f"{result.stdout[-4000:]}\n{result.stderr[-4000:]}")
    return result


class Rehearsal:
    def __init__(self, args, scratch):
        self.args, self.scratch = args, scratch
        self.name = "percival-i2-" + uuid.uuid4().hex[:12]
        self.env = dict(os.environ)
        # Host Compose environment cannot inject user state or deployment overrides.
        for key in list(self.env):
            if key.startswith(("PERCIVAL_", "NANOBOT_", "COMPOSE_", "DOCKER_")):
                del self.env[key]
        self.results = []
        self.ids = {}
        self.created = False
        self.inner_ready = False

    def record(self, name, **details):
        self.results.append({"check": name, "status": "passed", **details})
        print(f"PASS: {name}", flush=True)

    def docker(self, *args, **kwargs):
        # The fixture daemon's TCP control API is loopback-only in its own
        # network namespace. The controller enters that namespace via exec;
        # product containers cannot route to the Engine API.
        command = ["docker", "exec"]
        if kwargs.get("input") is not None:
            command.append("-i")
        return run([*command, self.name, "docker", *args], env=self.env, **kwargs)

    def compose(self, *args, **kwargs):
        compose_env = {key: value for key, value in self.env.items()
                       if key.startswith(("PERCIVAL_", "NANOBOT_"))}
        (self.scratch / "compose.env").write_text(
            "".join(f"{key}={value}\n" for key, value in sorted(compose_env.items()))
        )
        return self.docker("compose", "-p", self.name,
                           "--env-file", "/fixture/compose.env",
                           "-f", "/fixture/docker-compose.yml",
                           "-f", "/fixture/docker-compose.mcp-broker.yml",
                           "-f", "/fixture/compose.yaml", *args, **kwargs)

    def cli(self, *args, **kwargs):
        return self.compose("run", "--rm", "--no-deps", "-T", "nanobot-cli", *args, **kwargs)

    def exec(self, container, code, **kwargs):
        return run(["docker", "exec", "-i", self.name, "docker", "exec", "-i", container,
                    "python", "-"], env=self.env, input=code, **kwargs)

    def inspect(self, name):
        return json.loads(self.docker("inspect", name).stdout)[0]

    def wait(self, container, code, timeout=80):
        deadline = time.monotonic() + timeout
        result = None
        while time.monotonic() < deadline:
            result = self.exec(container, code, ok=False, timeout=40)
            if result.returncode == 0:
                return result.stdout
            time.sleep(1)
        raise AssertionError(f"readiness timeout: {container}\n{result.stderr[-2000:]}")

    def http(self, port, path, status=200):
        return f"""
import json, urllib.request, urllib.error
try:
    r = urllib.request.urlopen('http://127.0.0.1:{port}{path}', timeout=3)
    assert r.status == {status}
    print(r.read().decode())
except urllib.error.HTTPError as e:
    assert e.code == {status}, e.code
"""

    def start(self):
        run(["docker", "run", "-d", "--name", self.name, "--privileged",
             "-e", "DOCKER_TLS_CERTDIR=",
             "--mount", f"type=bind,src={self.scratch},dst=/fixture", DIND,
             "dockerd", "--host=unix:///var/run/docker.sock",
             "--host=tcp://127.0.0.1:2375"])
        self.created = True
        deadline = time.monotonic() + 60
        while self.docker("info", ok=False).returncode:
            assert time.monotonic() < deadline, "disposable daemon did not start"
            time.sleep(1)
        version = self.docker("version", "--format", "{{.Server.Version}}").stdout.strip()
        assert version == "27.5.1", version
        self.inner_ready = True
        self.record("isolated rootful Docker Server 27.5.1", server=version)
        for image in (self.args.gateway_image, self.args.broker_image):
            # Transfer exact local bytes; no registry login or rebuild in dind.
            archive = self.scratch / "image.tar"
            run(["docker", "save", "-o", str(archive), image])
            run(["docker", "cp", str(archive), f"{self.name}:/fixture/image.tar"])
            self.docker("load", "-i", "/fixture/image.tar", timeout=180)
            run(["docker", "exec", self.name, "rm", "-f", "/fixture/image.tar"])
            info = json.loads(self.docker("image", "inspect", image).stdout)[0]
            assert info["Os"] == "linux" and info["Architecture"] == "amd64"
            assert info["Config"]["Labels"]["org.opencontainers.image.version"] == "0.1.0"
            self.ids[image] = info["Id"]
        self.docker("run", "--rm", "--network", "none", "--entrypoint", "python3",
                    self.args.broker_image, "-c", "import nanobot; assert nanobot.__version__ == '0.1.0'")
        if self.args.old_broker_image:
            archive = self.scratch / "old-broker.tar"
            run(["docker", "save", "-o", str(archive), self.args.old_broker_image])
            run(["docker", "cp", str(archive), f"{self.name}:/fixture/old-broker.tar"])
            self.docker("load", "-i", "/fixture/old-broker.tar")
            run(["docker", "exec", self.name, "rm", "-f", "/fixture/old-broker.tar"])
            self.ids[self.args.old_broker_image] = json.loads(self.docker("image", "inspect", self.args.old_broker_image).stdout)[0]["Id"]
        socket_gid = run(["docker", "exec", self.name, "stat", "-c", "%g", "/var/run/docker.sock"]).stdout.strip()
        self.env.update({
            "PERCIVAL_STATE_HOST_PATH": "/fixture/state",
            "PERCIVAL_BROKER_TOKEN_HOST_PATH": "/fixture/state/mcp-docker/broker-token",
            "PERCIVAL_BROKER_TOKEN_GID": "65532",
            "PERCIVAL_DOCKER_SOCKET_GID": socket_gid,
            "PERCIVAL_GATEWAY_CONTAINER_NAME": self.name + "-nanobot-gateway-1",
            "PERCIVAL_MCP_BROKER_IMAGE": self.args.broker_image,
            "HOME": str(self.scratch / "unused-home"),
        })
        (self.scratch / "compose.yaml").write_text(f"""
services:
  nanobot-gateway:
    image: {self.args.gateway_image}
    build: !reset null
    restart: "no"
    ports: !reset []
  nanobot-api:
    image: {self.args.gateway_image}
    build: !reset null
    ports: !reset []
  nanobot-cli:
    image: {self.args.gateway_image}
    build: !reset null
  percival-mcp-broker:
    build: !reset null
    restart: "no"
""")
        for filename in ("docker-compose.yml", "docker-compose.mcp-broker.yml"):
            run(["docker", "cp", str(ROOT / filename), f"{self.name}:/fixture/{filename}"])
        config = json.loads(self.compose("--profile", "cli", "--profile", "api", "config", "--format", "json").stdout)
        for name in ("nanobot-gateway", "nanobot-api", "nanobot-cli"):
            mounts = [v for v in config["services"][name]["volumes"] if v["target"] == STATE]
            assert len(mounts) == 1 and mounts[0]["source"] == "/fixture/state"
        # Initialize the fixture bind in the daemon's own host namespace; no
        # product container gets a host-path bind to the controller scratch.
        run(["docker", "exec", self.name, "mkdir", "-p", "/fixture/state/mcp-docker"])
        run(["docker", "exec", self.name, "chown", "-R", "1000:1000", "/fixture/state"])
        self.record("Compose CLI/API/gateway share exactly one state bind")

    def permissions(self):
        image = self.args.gateway_image
        # Reproduces the old CI command under the actual non-root Compose user.
        proc = self.compose("run", "--rm", "--no-deps", "-T", "--entrypoint", "sh",
                            "nanobot-cli", "-c", 'test "$(id -u)" = 0', ok=False)
        assert proc.returncode != 0
        for uid in (1000, 1001):
            self.docker("run", "--rm", "--network", "none", "--user", f"{uid}:{uid}",
                        "--entrypoint", "python", image, "-c",
                        "import neonize,segno,nanobot; from importlib.metadata import version; "
                        f"import os; assert os.access('/app/.venv',os.W_OK) is {uid == 1000}; "
                        "assert not os.access('/app/nanobot',os.W_OK); "
                        "assert nanobot.__version__ == version('nanobot-ai') == '0.1.0'")
        self.record("inherited root assertion reproduced; installed metadata/channels offline at UID 1000/1001")
        self.docker("run", "--rm", "--user", "0:0", "--entrypoint", "sh",
                    "--mount", "type=bind,src=/fixture,dst=/fixture", image, "-c",
                    "mkdir /fixture/wrong /fixture/alternate /fixture/root-drop; "
                    "chmod 700 /fixture/wrong; chown 1001:1001 /fixture/alternate")
        denied = self.docker("run", "--rm", "--user", "1000:1000", "--network", "none",
                             "--mount", f"type=bind,src=/fixture/wrong,dst={STATE}", image, "status", ok=False)
        assert denied.returncode == 1 and "not writable" in denied.stderr
        alternate = self.docker("run", "--rm", "--user", "1001:1001", "--network", "none",
                                "--mount", f"type=bind,src=/fixture/alternate,dst={STATE}", image, "status")
        assert alternate.returncode == 0
        (self.scratch / "setpriv-fails").write_text("#!/bin/sh\nexit 1\n")
        (self.scratch / "setpriv-fails").chmod(0o755)
        failed_drop = self.docker("run", "--rm", "--user", "0:0", "--network", "none",
                                  "--mount", f"type=bind,src=/fixture/root-drop,dst={STATE}",
                                  "--mount", "type=bind,src=/fixture/setpriv-fails,dst=/usr/bin/setpriv,readonly",
                                  image, "status", ok=False)
        assert failed_drop.returncode == 1 and "refusing to run as root" in failed_drop.stderr
        self.record("ownership error and setpriv failure exit 1; alternate UID status succeeds")

    def setup(self):
        self.cli("onboard", "--refresh")
        self.cli("status")
        unset = self.cli("auth", "status").stdout
        assert "No Percival instance password" in unset
        # Config JSON is the supported provider/API input, validated by onboard refresh.
        config_path = self.scratch / "state/config.json"
        config = json.loads(config_path.read_text())
        config["agents"]["defaults"].update({"model": "openai/gpt-4o-mini", "provider": "openai",
                                               "dream": {"enabled": False}})
        config["providers"]["openai"].update({"apiKey": "fixture-provider-unused", "apiBase": "http://127.0.0.1:9/v1"})
        config["gateway"]["heartbeat"]["enabled"] = False
        config["api"]["apiKey"] = ""
        config_path.write_text(json.dumps(config))
        config_path.chmod(0o644)
        self.cli("onboard", "--refresh")
        assert stat.S_IMODE(config_path.stat().st_mode) == 0o600
        no_key = self.compose("run", "--rm", "--no-deps", "-T", "nanobot-api", ok=False)
        assert no_key.returncode == 1 and "api_key" in no_key.stdout
        # Compare the old one-off path with the canonical service lifecycle.
        one_off = self.compose("run", "-d", "--no-deps", "nanobot-gateway").stdout.strip()
        self.wait(one_off, self.http(8765, "/webui/bootstrap", 401))
        one_off_before = self.inspect(one_off)
        self.docker("stop", "--time", "60", one_off)
        one_off_after = self.inspect(one_off)
        self.results.append({
            "check": "one-off Compose gateway stop diagnostic",
            "status": "observed",
            "host_init": one_off_before["HostConfig"].get("Init"),
            "exit_code": one_off_after["State"]["ExitCode"],
        })
        print(f"OBSERVED: one-off Compose gateway: HostConfig.Init={one_off_before['HostConfig'].get('Init')}, "
              f"exit={one_off_after['State']['ExitCode']}", flush=True)
        self.docker("rm", one_off)

        # Exercise the canonical long-running service lifecycle as well.
        no_password_id = self.env["PERCIVAL_GATEWAY_CONTAINER_NAME"]
        self.compose("up", "-d", "--no-build", "--no-deps", "nanobot-gateway")
        self.wait(no_password_id, self.http(18790, "/health"))
        # The unauthenticated sign-in page may listen; protected bootstrap must refuse access.
        self.wait(no_password_id, self.http(8765, "/webui/bootstrap", 401))
        signal_state = self.exec(no_password_id, """
import json
from pathlib import Path
rows=[]
for p in Path('/proc').glob('[0-9]*/status'):
    try:
        row=dict(line.split(':',1) for line in p.read_text().splitlines() if ':' in line)
        if row.get('Pid','').strip() == '1' or row.get('PPid','').strip() == '1':
            rows.append({k: row.get(k,'').strip() for k in ('Name','Pid','PPid','SigCgt','SigIgn')})
    except OSError:
        pass
print(json.dumps(rows))
""").stdout.strip()
        self.results.append({"check": "gateway signal-handler state at health readiness", "status": "observed",
                             "processes": json.loads(signal_state)})
        print(f"OBSERVED: gateway signal state {signal_state}", flush=True)
        self.compose("stop", "nanobot-gateway")
        stopped = self.inspect(no_password_id)
        assert stopped["HostConfig"].get("Init") is True, stopped["HostConfig"].get("Init")
        assert stopped["Config"].get("StopSignal") == "SIGTERM", stopped["Config"].get("StopSignal")
        assert stopped["State"]["ExitCode"] == 0, stopped["State"]
        self.record("Compose gateway init=true; unauthenticated bootstrap denied; idle SIGTERM exits 0")
        self.cli("auth", "init", input=PASSWORD + "\n" + PASSWORD + "\n")
        assert "is configured" in self.cli("auth", "status").stdout
        # Capture all auth bytes, regardless of the verifier's private filename.
        auth_files = {str(p.relative_to(self.scratch)): hashlib.sha256(p.read_bytes()).hexdigest()
                      for p in (self.scratch / "state/auth").rglob("*") if p.is_file()}
        assert auth_files
        reinit = self.cli("auth", "init", ok=False)
        assert reinit.returncode == 1 and "already configured" in reinit.stderr
        assert auth_files == {str(p.relative_to(self.scratch)): hashlib.sha256(p.read_bytes()).hexdigest()
                              for p in (self.scratch / "state/auth").rglob("*") if p.is_file()}
        self.cli("auth", "change", input=PASSWORD + "\n" + PASSWORD + "changed\n" + PASSWORD + "changed\n")
        config = json.loads(config_path.read_text())
        config["api"]["apiKey"] = "fixture-api-key-distinct"
        config_path.write_text(json.dumps(config))
        self.cli("onboard", "--refresh")
        token = self.scratch / "state/mcp-docker/broker-token"
        token.write_text(uuid.uuid4().hex + uuid.uuid4().hex)
        self.docker("run", "--rm", "--user", "0:0", "--entrypoint", "sh",
                    "--mount", "type=bind,src=/fixture/state,dst=/state", self.args.gateway_image,
                    "-c", "chown 1000:65532 /state/mcp-docker/broker-token; chmod 640 /state/mcp-docker/broker-token")
        self.record("onboard repairs permissive config mode to 0600; status/auth init/change and missing-key/reinit guards pass")

    def process(self, container, uid):
        result = self.exec(container, """
import json
from pathlib import Path
rows = []
for p in Path('/proc').glob('[0-9]*/status'):
    try:
        row = dict(line.split(':',1) for line in p.read_text().splitlines() if ':' in line)
        if row['Pid'].strip() == '1' or row['PPid'].strip() == '1':
            rows.append({k: row[k].strip() for k in ('Name','Pid','PPid','Uid','Gid','CapEff','CapPrm','CapAmb','CapInh','NoNewPrivs')})
    except (OSError, KeyError):
        pass
print(json.dumps(rows))
""")
        rows = json.loads(result.stdout)
        init = [r for r in rows if r["Pid"] == "1"]
        assert len(init) == 1 and init[0]["Name"] == "docker-init", rows
        apps = [r for r in rows if r["PPid"] == "1"]
        assert len(apps) == 1 and set(apps[0]["Uid"].split()) == {str(uid)}, rows
        assert set(apps[0]["Gid"].split()) == {str(uid)}, rows
        for row in apps:
            assert row["CapEff"] == row["CapPrm"] == row["CapAmb"] == row["CapInh"] == "0000000000000000"
            assert row["NoNewPrivs"] == "1"
        return rows

    def core(self):
        self.compose("up", "-d", "--no-build", "--no-deps", "nanobot-gateway")
        gateway = self.env["PERCIVAL_GATEWAY_CONTAINER_NAME"]
        self.wait(gateway, self.http(18790, "/health"))
        # Gateway process readiness is deliberately independent of broker readiness.
        late = self.docker("exec", gateway, "nanobot", "mcp-docker", "doctor", ok=False)
        assert late.returncode == 1
        self.compose("up", "-d", "--no-build", "percival-mcp-broker")
        broker = self.name + "-percival-mcp-broker-1"
        self.wait(gateway, f"from nanobot.mcp_docker.client import BrokerClient; from pathlib import Path; "
                  f"assert BrokerClient(Path('{STATE}/mcp-docker/broker-token')).action('health','broker',{{}})['ready'] is True")
        tcp_denied = self.exec(gateway, r"""
import socket
from pathlib import Path
routes = Path('/proc/net/route').read_text().splitlines()[1:]
gateways = [str(__import__('ipaddress').IPv4Address(int(row.split()[2],16).to_bytes(4,'little')))
            for row in routes if row.split()[1] == '00000000']
assert gateways, 'default route missing from gateway fixture'
for address in gateways:
    try:
        with socket.create_connection((address,2375),timeout=1):
            raise AssertionError('gateway reached Docker Engine TCP API')
    except OSError:
        pass
""")
        assert tcp_denied.returncode == 0
        self.docker("exec", broker, "python3", "-m", "nanobot.mcp_docker.probe")
        self.process(gateway, 1000)
        self.process(broker, 65532)
        self.exec(gateway, "import shutil; from pathlib import Path; assert shutil.which('docker') is None; assert not Path('/var/run/docker.sock').exists()")
        self.record("Engine API TCP denied from gateway; broker socket/probe authorized; single init/non-root zero capabilities",
                    processes={"gateway": self.process(gateway,1000), "broker": self.process(broker,65532)})
        # API is a separate run: do not start another writer beside the gateway.
        started = time.monotonic()
        self.compose("stop", "nanobot-gateway")
        assert self.inspect(gateway)["State"]["ExitCode"] == 0
        self.record("gateway SIGTERM exits 0 without SIGKILL", seconds=round(time.monotonic()-started,3))
        self.compose("up", "-d", "--no-build", "--no-deps", "nanobot-api")
        api = self.name + "-nanobot-api-1"
        self.wait(api, self.http(8900, "/health"))
        self.exec(api, self.http(8900, "/v1/models", 401))
        self.exec(api, """
import urllib.request, urllib.error
url='http://127.0.0.1:8900/v1/models'
for key, expected in [('fixture-api-key-distinct',200), ('Runtime-fixture-2026!changed',401)]:
    try:
        r=urllib.request.urlopen(urllib.request.Request(url,headers={'Authorization':'Bearer '+key}),timeout=3)
        assert r.status==expected
    except urllib.error.HTTPError as e:
        assert e.code==expected
""")
        self.process(api, 1000)
        started=time.monotonic()
        self.compose("stop", "nanobot-api")
        assert self.inspect(api)["State"]["ExitCode"] == 0
        self.record("API health/auth distinct from human password; separate writer; SIGTERM exit 0", seconds=round(time.monotonic()-started,3))
        # Recreate the pair, not just the network-namespace owner.
        old_id = self.inspect(gateway)["Id"]
        self.compose("up", "-d", "--no-build", "--force-recreate", "nanobot-gateway", "percival-mcp-broker")
        self.wait(gateway, self.http(18790, "/health"))
        assert self.inspect(gateway)["Id"] != old_id
        self.wait(gateway, f"from nanobot.mcp_docker.client import BrokerClient; from pathlib import Path; assert BrokerClient(Path('{STATE}/mcp-docker/broker-token')).action('health','broker',{{}})['ready']")
        self.record("gateway+broker pair recreation rejoins new network namespace")
        return gateway, broker

    def mcp(self, gateway, broker):
        source = (ROOT / "tests/mcp_docker/runtime_server.py").read_text()
        fixture_image = self.name + "-mcp:fixture"
        dockerfile = f"FROM {self.args.gateway_image}\nUSER 1000:1000\nENTRYPOINT " + json.dumps(["python", "-u", "-c", source]) + "\n"
        self.docker("build", "-t", fixture_image, "-", input=dockerfile)
        self.docker("run", "--rm", "-i", "--network", "none", fixture_image, input="")
        self.record("stdio MCP EOF exits 0 without a remaining fixture container")
        image_id = json.loads(self.docker("image", "inspect", fixture_image).stdout)[0]["Id"]
        self.exec(gateway, f"""
from pathlib import Path
from nanobot.mcp_docker.client import BrokerClient
from nanobot.mcp_docker.service import DockerMcpService
from nanobot.webui.settings_services import WebUISettingsConfig
d=DockerMcpService(WebUISettingsConfig(Path('{STATE}/config.json')),BrokerClient(Path('{STATE}/mcp-docker/broker-token')))
d.act('install',{{'server_id':'i2fixture','expected_revision':0,'source':{{'type':'local-image','reference':'{image_id}'}},'configuration':{{'mounts':[],'network':'none','persistent':True}}}})
""")
        call = """
import asyncio
from nanobot.agent.tools.mcp import MCPProvider
from nanobot.agent.tools.registry import ToolRegistry
from nanobot.config.loader import load_config
async def check():
    registry=ToolRegistry()
    provider=MCPProvider.from_config(load_config(),registry)
    try:
        await provider.connect()
        tool=registry.get('mcp_percival_docker_i2fixture_ping')
        assert tool is not None, provider.runtime_status()
        result=await tool.execute()
        assert 'pong' in str(result), result
    finally:
        await provider.aclose()
asyncio.run(check())
"""
        self.wait(gateway, call)
        # Frozen v1 caller: intentionally does not import today's client/producer.
        self.exec(gateway, f"""
import json, urllib.request
from pathlib import Path
token=Path('{STATE}/mcp-docker/broker-token').read_text().strip()
request=urllib.request.Request('http://127.0.0.1:18081/v1/status',data=b'{{"server_id":"i2fixture"}}',headers={{'Authorization':'Bearer '+token,'Content-Type':'application/json'}},method='POST')
with urllib.request.urlopen(request,timeout=30) as r:
    assert json.load(r)['registered'] is True
""")
        self.record("independent v1 client request accepted by current broker")
        if self.args.old_broker_image:
            base_image = self.env["PERCIVAL_MCP_BROKER_IMAGE"]
            self.env["PERCIVAL_MCP_BROKER_IMAGE"] = self.args.old_broker_image
            self.compose("up", "-d", "--no-build", "--force-recreate", "percival-mcp-broker")
            self.wait(gateway, call)
            self.record("current gateway + baseline 0.3.5 broker: real hydrate/initialize/list/call")
            self.env["PERCIVAL_MCP_BROKER_IMAGE"] = base_image
            self.compose("up", "-d", "--no-build", "--force-recreate", "percival-mcp-broker")
            self.wait(gateway, call)
        original = (self.scratch / "state/config.json").read_bytes()
        marker = self.scratch / "state/persistence-marker"
        marker.write_text("I2-persistence")
        self.docker("kill", broker)
        failed = self.docker("exec", gateway, "nanobot", "mcp-docker", "doctor", ok=False)
        assert failed.returncode == 1
        self.compose("up", "-d", "--no-build", "--force-recreate", "nanobot-gateway", "percival-mcp-broker")
        self.wait(gateway, self.http(18790, "/health"))
        self.wait(gateway, call)
        assert original == (self.scratch / "state/config.json").read_bytes()
        assert marker.read_text() == "I2-persistence"
        self.exec(broker, r"""
from pathlib import Path
for path in Path('/proc').glob('[0-9]*/cmdline'):
    try:
        args=path.read_bytes().split(b'\0')
    except OSError:
        continue
    assert args[:2] != [b'/usr/bin/docker',b'attach'], 'orphan attach process'
""")
        owned=self.docker("ps", "-a", "--filter", "label=percival.mcp-docker.managed-by=percival-broker", "--format", "{{.Names}}").stdout.split()
        assert owned == ['percival-mcp-i2fixture'], owned
        self.record("MCP initialize/list/call; broker SIGKILL/recreate/hydrate; config and marker persist")
        self.exec(gateway, """
import json, urllib.request, urllib.error
r=urllib.request.Request('http://127.0.0.1:18081/v1/health',data=b'{"server_id":"broker"}',headers={'Authorization':'Bearer '+('x'*64),'Content-Type':'application/json'})
try:
    urllib.request.urlopen(r,timeout=3)
    raise AssertionError('invalid token accepted')
except urllib.error.HTTPError as e:
    assert e.code==401
""")
        # Prove the sidecar healthcheck fails against a running but unauthenticated service.
        self.exec(broker, "from pathlib import Path; p=Path('/tmp/wrong-token'); p.write_text('z'*64); p.chmod(0o600)")
        denied = self.docker("exec", "-e", "PERCIVAL_BROKER_TOKEN_FILE=/tmp/wrong-token", broker,
                             "python3", "-m", "nanobot.mcp_docker.probe", ok=False)
        assert denied.returncode == 1
        self.record("invalid broker token: HTTP 401 and readiness exit 1")
        self.docker("stop", "--time", "10", broker)
        assert self.inspect(broker)["State"]["ExitCode"] == 143
        self.record("broker SIGTERM exit 143 (no application drain); owned persistent MCP retained")

    def root_drop(self):
        self.docker("run", "--rm", "--user", "0:0", "--entrypoint", "mkdir",
                    "--mount", "type=bind,src=/fixture,dst=/fixture", self.args.gateway_image, "/fixture/render-new")
        for _ in range(2):
            self.docker("run", "--rm", "--network", "none", "--user", "0:0", "-e", "RENDER=true",
                        "-e", "ANTHROPIC_API_KEY=fixture-unused",
                        "--mount", f"type=bind,src=/fixture/render-new,dst={STATE}", self.args.gateway_image,"status")
            data=(self.scratch / "render-new/config.json").read_bytes()
            if _ == 0:
                initial=data
            else:
                assert data==initial
        self.record("Render=true fresh root-owned disk initialized once; config retained")
        name = self.name + "-root-drop"
        self.docker("run", "-d", "--name", name, "--init", "--user", "0:0",
                    "--network", "none", "--cap-drop=ALL", "--cap-add=CHOWN", "--cap-add=SETUID", "--cap-add=SETGID", "--cap-add=KILL",
                    "--security-opt=no-new-privileges", "-e", "RENDER=true",
                    "--mount", f"type=bind,src=/fixture/state,dst={STATE}",
                    "-e", "PERCIVAL_BROKER_TOKEN_GID=65532", self.args.gateway_image, "gateway", "--foreground")
        self.wait(name, self.http(18790, "/health"))
        self.process(name,1000)
        started=time.monotonic()
        self.docker("stop", "--time", "60", name)
        assert self.inspect(name)["State"]["ExitCode"] == 0
        self.record("Render=true existing state: root entrypoint drops to UID 1000; one init; SIGTERM exit 0", seconds=round(time.monotonic()-started,3))

    def finish(self):
        self.compose("stop", "nanobot-gateway")
        self.root_drop()
        # A fake version response injects only the unsupported Server decision.
        (self.scratch / "docker-incompatible").write_text('#!/bin/sh\nif [ "$1" = version ]; then echo "29.9.0|28.0.0"; exit 0; fi\nexit 99\n')
        (self.scratch / "docker-incompatible").chmod(0o755)
        incompatible = self.docker("run", "--rm", "--network", "none", "--user", "65532:65532",
                                    "-e", "PERCIVAL_BROKER_TOKEN_FILE=/run/token",
                                    "--mount", "type=bind,src=/fixture/state/mcp-docker/broker-token,dst=/run/token,readonly",
                                    "--mount", "type=bind,src=/fixture/docker-incompatible,dst=/usr/bin/docker,readonly",
                                    self.args.broker_image, ok=False)
        assert incompatible.returncode != 0 and "Server 27.x required" in incompatible.stderr
        self.record("unsupported Server version fails before broker listener (injected Docker version)")
        # Full alternate-UID gateway through Compose, on its own correctly owned bind.
        alternate_config=json.loads((self.scratch / "state/config.json").read_text())
        alternate_config["tools"]["mcpDocker"]={"schemaVersion":1}
        self.docker("run", "--rm", "-i", "--user", "1001:1001", "--entrypoint", "python",
                    "--mount", f"type=bind,src=/fixture/alternate,dst={STATE}", self.args.gateway_image,
                    "-c", "import sys; from pathlib import Path; p=Path.home()/'.nanobot/config.json'; p.write_text(sys.stdin.read()); p.chmod(0o600)",
                    input=json.dumps(alternate_config))
        self.env.update({"NANOBOT_UID":"1001", "NANOBOT_GID":"1001",
                         "PERCIVAL_STATE_HOST_PATH":"/fixture/alternate",
                         "PERCIVAL_BROKER_TOKEN_HOST_PATH":"/fixture/alternate/mcp-docker/broker-token"})
        self.cli("onboard", "--refresh")
        self.cli("auth", "init", input=PASSWORD+"\n"+PASSWORD+"\n")
        self.compose("up", "-d", "--no-build", "--no-deps", "--force-recreate", "nanobot-gateway")
        gateway=self.env["PERCIVAL_GATEWAY_CONTAINER_NAME"]
        self.wait(gateway, self.http(18790,"/health"))
        self.process(gateway,1001)
        self.compose("stop", "nanobot-gateway")
        assert self.inspect(gateway)["State"]["ExitCode"] == 0
        self.record("alternate UID/GID 1001 Compose gateway: own state, auth setup, health and SIGTERM exit 0")

    def cleanup(self):
        if self.created:
            run(["docker", "rm", "-f", "-v", self.name], ok=False)

    def diagnostics(self):
        if not self.inner_ready:
            return
        for container in self.docker("ps", "-aq", ok=False).stdout.split():
            logs = self.docker("logs", "--tail", "150", container, ok=False)
            (self.scratch / (container + ".log")).write_text(logs.stdout + logs.stderr)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gateway-image", required=True)
    parser.add_argument("--broker-image", required=True)
    parser.add_argument("--old-broker-image", help="Optional independently built baseline broker for cross-version replay")
    parser.add_argument("--scratch-parent", type=Path, required=True)
    args = parser.parse_args()
    if not args.scratch_parent.is_dir():
        parser.error("scratch parent must already exist")
    scratch = Path(tempfile.mkdtemp(prefix="i2-", dir=args.scratch_parent.resolve()))
    # Broker host inventory needs traversal on its disposable host, not access to live files.
    scratch.chmod(0o755)
    rehearsal = Rehearsal(args, scratch)
    completed = False
    try:
        rehearsal.start()
        rehearsal.permissions()
        rehearsal.setup()
        gateway, broker = rehearsal.core()
        rehearsal.mcp(gateway,broker)
        rehearsal.finish()
        completed = True
    except BaseException:
        rehearsal.diagnostics()
        raise
    finally:
        (scratch / "results.json").write_text(json.dumps({"completed": completed, "finished_at": datetime.now(timezone.utc).isoformat(), "images": rehearsal.ids, "checks": rehearsal.results}, indent=2)+"\n")
        rehearsal.cleanup()
        print(f"Evidence: {scratch / 'results.json'}", flush=True)


if __name__ == "__main__":
    main()
