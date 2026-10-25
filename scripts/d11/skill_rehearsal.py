#!/usr/bin/env python3
"""Disposable D11 skill context check plus the D9 manager A→B→A rehearsal.

Requires Docker + Compose on Linux/amd64 and the exact local gateway/broker
images selected on the command line. All manager writes stay in a uniquely
named Docker-in-Docker Engine; the host daemon only runs that disposable Engine.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

repo = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(repo))
spec = importlib.util.spec_from_file_location(
    "i2_smoke", repo / "scripts/percival-i2-runtime-smoke.py"
)
i2 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(i2)


def load_d9():
    source = (repo / "scripts/d11/d9_rehearsal.py").read_text()
    namespace = {"i2": i2, "json": json, "Path": Path, "repo": repo}
    exec(compile(source, "d9_rehearsal", "exec"), namespace)
    return namespace["D9Rehearsal"]


D9Rehearsal = load_d9()


class D11Rehearsal(D9Rehearsal):
    def __init__(self, args, scratch):
        super().__init__(args, scratch)
        self.context_dir = scratch / "d11-context"
        (self.context_dir / "builtin" / "mcp-docker-operations").mkdir(parents=True)
        (self.context_dir / "docs" / "operations").mkdir(parents=True)
        (self.context_dir / "builtin" / "mcp-docker-operations" / "SKILL.md").write_bytes(
            (repo / "nanobot/skills/mcp-docker-operations/SKILL.md").read_bytes()
        )
        (self.context_dir / "docs" / "operations" / "mcp-docker-local-runbook.md").write_bytes(
            (repo / "docs/operations/mcp-docker-local-runbook.md").read_bytes()
        )
        self.context_mounted = False

    def compose(self, *args, **kwargs):
        if "config" in args and not self.context_mounted:
            path = self.scratch / "compose.yaml"
            content = path.read_text()
            anchor = '    ports: !reset []\n  nanobot-api:'
            addition = '''    ports: !reset []
    volumes:
      - type: bind
        source: /fixture/d11-context/builtin/mcp-docker-operations
        target: /app/nanobot/skills/mcp-docker-operations
        read_only: true
      - type: bind
        source: /fixture/d11-context/docs
        target: /app/docs
        read_only: true
  nanobot-api:'''
            if anchor not in content:
                raise RuntimeError("D11 Compose context mount anchor changed; refusing to run")
            path.write_text(content.replace(anchor, addition, 1))
            self.context_mounted = True
        return super().compose(*args, **kwargs)

    def before_fixture_mutation(self, image_a, image_b, image_false_health):
        gateway = self.env["PERCIVAL_GATEWAY_CONTAINER_NAME"]
        code = f"""
import hashlib, json
from pathlib import Path
from nanobot.config.loader import load_config
from nanobot.mcp_docker.client import BrokerClient
from nanobot.mcp_docker.service import DockerMcpService
from nanobot.webui.settings_services import WebUISettingsConfig
root=Path('/home/nanobot/.nanobot')
service=DockerMcpService(WebUISettingsConfig(root/'config.json'),BrokerClient(root/'mcp-docker/broker-token'))
snapshot=service.list()
section=load_config(root/'config.json').tools.mcp_docker
server=section.servers['i2fixture']
observed=snapshot['servers']['i2fixture']
assert snapshot['brokerStatus']['status']=='ready'
assert observed['dockerObservation']=='running' and observed['mcpConnectivity']=='connected', observed
assert not snapshot['pendingTransitions']
before=(root/'config.json').read_bytes()
audit=root/'mcp-docker/audit.jsonl'
audit_before=audit.read_bytes() if audit.exists() else b''
backups=len(list((root/'mcp-docker/backups').iterdir())) if (root/'mcp-docker/backups').exists() else 0
calls=[]
def forbidden(*args, **kwargs):
 calls.append(args)
 raise AssertionError('dry-run attempted broker action')
service.broker.action=forbidden
for index,payload in enumerate((
 {{'server_id':'i2fixture','expected_revision':section.revision-1,'expected_server_revision':server.revision,'source':{{'type':'local-image','reference':'{image_b}'}}}},
 {{'server_id':'i2fixture','expected_revision':section.revision,'expected_server_revision':server.revision,'source':{{'type':'local-image','reference':'{image_b}'}},'unexpected':'reject'}},
)):
 try: service.act('update-image',payload)
 except Exception as exc:
  assert getattr(exc,'status',None)==(409 if index==0 else 400), type(exc).__name__
 else: raise AssertionError('invalid dry-run payload accepted')
assert not calls
assert before==(root/'config.json').read_bytes()
assert audit_before==(audit.read_bytes() if audit.exists() else b'')
assert backups==(len(list((root/'mcp-docker/backups').iterdir())) if (root/'mcp-docker/backups').exists() else 0)
print(json.dumps({{'owner':'Percival manager fixture','server_id':'i2fixture','transport':'stdio','image_a':'{image_a}','image_b':'{image_b}','false_health_image':'{image_false_health}','global_revision':section.revision,'server_revision':server.revision,'docker_observation':observed['dockerObservation'],'mcp_connectivity':observed['mcpConnectivity'],'pending_transitions':0,'dry_run_mutations':0,'stale_cas':'rejected','invalid_field':'rejected'}}))
"""
        result = json.loads(self.exec(gateway, code).stdout)
        self.record("D11 fixture dry-run identified owner, A/B IDs, transport, revisions and rollback; stale CAS and invalid field rejected before broker", **result)

    def finish(self):
        gateway = self.env["PERCIVAL_GATEWAY_CONTAINER_NAME"]
        code = r"""
import hashlib, json
from pathlib import Path
from nanobot.agent.skills import SkillsLoader
from nanobot.config.loader import load_config
root=Path('/home/nanobot/.nanobot')
config=load_config(root/'config.json')
loader=SkillsLoader(Path('/tmp/d11-agent-workspace'), disabled_skills=set(config.agents.defaults.disabled_skills or []))
all_entries=loader.list_skills(filter_unavailable=False)
available=loader.list_skills(filter_unavailable=True)
entries=[entry for entry in all_entries if entry['name']=='mcp-docker-operations']
assert len(entries)==1 and entries[0]['source']=='builtin', entries
assert any(entry['name']=='mcp-docker-operations' for entry in available)
content=loader.load_skill('mcp-docker-operations')
assert content and 'Default to read-only' in content
context=loader.load_skills_for_context(['mcp-docker-operations'])
assert 'Required rehearsal' in context
runbook=Path('/app/docs/operations/mcp-docker-local-runbook.md')
assert runbook.is_file() and runbook.stat().st_size > 1000
print(json.dumps({'source':'builtin','duplicates':len(entries)-1,'enabled':True,'skill_sha256':hashlib.sha256(content.encode()).hexdigest(),'runbook_readable':True,'agent_model_invoked':False}))
"""
        result = json.loads(self.exec(gateway, code).stdout)
        expected = __import__("hashlib").sha256(
            (repo / "nanobot/skills/mcp-docker-operations/SKILL.md").read_bytes()
        ).hexdigest()
        assert result["skill_sha256"] == expected, result
        self.record("D11 Built-in skill enabled, unique and loaded into context; runbook readable",
                    skill_sha256=expected, agent_model_invoked=False)
        self.results.append({"check": "D11 agent LLM dry-run", "status": "blocked", "reason": "context and manager dry-run were verified deterministically; no isolated agent model endpoint is configured"})
        print("BLOCKED: D11 agent LLM dry-run has no isolated model endpoint", flush=True)
        super().finish()


def main():
    sys.argv[0] = str(repo / "scripts/d11/skill_rehearsal.py")
    i2.__doc__ = __doc__
    i2.Rehearsal = D11Rehearsal
    i2.main()


if __name__ == "__main__":
    main()
