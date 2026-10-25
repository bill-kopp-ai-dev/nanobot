import json
from pathlib import Path

class D9Rehearsal(i2.Rehearsal):
    def finish(self):
        gateway = self.env['PERCIVAL_GATEWAY_CONTAINER_NAME']
        self.compose('up', '-d', '--no-build', '--no-deps', 'percival-mcp-broker')
        self.wait(gateway, f"from pathlib import Path; from nanobot.mcp_docker.client import BrokerClient; assert BrokerClient(Path('/home/nanobot/.nanobot/mcp-docker/broker-token')).action('health','broker',{{}})['ready'] is True")
        original = self.ids[self.args.gateway_image]
        source = (repo / 'tests/mcp_docker/runtime_server.py').read_text()
        dockerfile_a = f"FROM {self.args.gateway_image}\nUSER 1000:1000\nENTRYPOINT " + json.dumps(['python', '-u', '-c', source]) + '\n'
        source_b = source.replace('"pong"', '"pong-b"')
        dockerfile_b = f"FROM {self.args.gateway_image}\nUSER 1000:1000\nENTRYPOINT " + json.dumps(['python', '-u', '-c', source_b]) + '\n'
        dockerfile_h = dockerfile_a + "HEALTHCHECK --interval=1s --timeout=1s --retries=1 CMD python -c \"import urllib.request; urllib.request.urlopen('http://127.0.0.1:8765/health', timeout=1)\"\n"
        self.docker('build', '-t', self.name + '-mcp-a:fixture', '-', input=dockerfile_a)
        self.docker('build', '-t', self.name + '-mcp-b:fixture', '-', input=dockerfile_b)
        self.docker('build', '-t', self.name + '-mcp-false-health:fixture', '-', input=dockerfile_h)
        a_id = json.loads(self.docker('image', 'inspect', self.name + '-mcp-a:fixture').stdout)[0]['Id']
        b_id = json.loads(self.docker('image', 'inspect', self.name + '-mcp-b:fixture').stdout)[0]['Id']
        h_id = json.loads(self.docker('image', 'inspect', self.name + '-mcp-false-health:fixture').stdout)[0]['Id']
        before_fixture_mutation = getattr(self, 'before_fixture_mutation', None)
        if before_fixture_mutation:
            before_fixture_mutation(a_id, b_id, h_id)
        state = '/home/nanobot/.nanobot'
        def mutate(action, image_id=None):
            image = f"\npayload['source']={{'type':'local-image','reference':'{image_id}'}}" if image_id else ''
            code = f"""
import json
from pathlib import Path
from nanobot.config.loader import load_config
from nanobot.mcp_docker.client import BrokerClient
from nanobot.mcp_docker.service import DockerMcpService
from nanobot.webui.settings_services import WebUISettingsConfig
root=Path('{state}')
d=DockerMcpService(WebUISettingsConfig(root/'config.json'),BrokerClient(root/'mcp-docker/broker-token'))
s=load_config(root/'config.json').tools.mcp_docker
entry=s.servers['i2fixture']
payload={{'server_id':'i2fixture','expected_revision':s.revision,'expected_server_revision':entry.revision}}{image}
if '{action}' == 'exclude': payload['expected_confirmation']='i2fixture'
print(json.dumps(d.act('{action}',payload)))
"""
            return json.loads(self.exec(gateway, code).stdout)
        def ping(expected):
            code = f"""
import asyncio
from nanobot.agent.tools.mcp import MCPProvider
from nanobot.agent.tools.registry import ToolRegistry
from nanobot.config.loader import load_config
async def main():
 r=ToolRegistry(); p=MCPProvider.from_config(load_config(),r)
 try:
  await p.connect(); tool=r.get('mcp_percival_docker_i2fixture_ping'); assert tool is not None, p.runtime_status()
  result=await tool.execute(); assert '{expected}' in str(result), result
 finally: await p.aclose()
asyncio.run(main())
"""
            self.exec(gateway, code)
        mutate('update-image', b_id)
        ping('pong-b')
        self.record('D9 update A→B through broker/CAS; MCP call returns B fixture', image_a=a_id, image_b=b_id)
        mutate('update-image', a_id)
        ping('pong')
        self.record('D9 rollback B→A through broker/CAS; MCP call returns A fixture', image_a=a_id, image_b=b_id)
        mutate('update-image', h_id)
        ping('pong')
        names = self.docker('ps', '-q', '--filter', 'label=percival.mcp-docker.server-id=i2fixture').stdout.split()
        assert len(names) == 1, names
        unhealthy = False
        import time
        for _ in range(15):
            info = self.inspect(names[0])
            health = info.get('State', {}).get('Health', {}).get('Status')
            if health == 'unhealthy':
                unhealthy = True
                break
            time.sleep(1)
        assert unhealthy, info.get('State')
        self.record('D9 stdio fake HTTP healthcheck reports unhealthy while MCP ping succeeds', health=health)
        mutate('update-image', a_id)
        ping('pong')
        excluded = mutate('exclude')
        assert excluded['state'] == 'excluded' and excluded.get('backup')
        section = self.exec(gateway, f"from pathlib import Path; from nanobot.config.loader import load_config; p=Path('{state}/config.json'); print(load_config(p).tools.mcp_docker.revision)").stdout.strip()
        restore_code = f"""
import json
from pathlib import Path
from nanobot.config.loader import load_config
from nanobot.mcp_docker.client import BrokerClient
from nanobot.mcp_docker.service import DockerMcpService
from nanobot.webui.settings_services import WebUISettingsConfig
root=Path('{state}'); d=DockerMcpService(WebUISettingsConfig(root/'config.json'),BrokerClient(root/'mcp-docker/broker-token'))
revision=load_config(root/'config.json').tools.mcp_docker.revision
print(json.dumps(d.restore_backup(Path({excluded['backup']!r}), revision, 'i2fixture')))
"""
        restored = json.loads(self.exec(gateway, restore_code).stdout)
        assert restored['state'] == 'running'
        ping('pong')
        observe_code = f"""
import json
from pathlib import Path
from nanobot.mcp_docker.client import BrokerClient
from nanobot.mcp_docker.service import DockerMcpService
from nanobot.webui.settings_services import WebUISettingsConfig
root=Path('{state}')
print(json.dumps(DockerMcpService(WebUISettingsConfig(root/'config.json'),BrokerClient(root/'mcp-docker/broker-token')).list()))
"""
        observation=json.loads(self.exec(gateway, observe_code).stdout)
        observed=observation['servers']['i2fixture']
        assert observed['dockerObservation']=='running' and observed['mcpConnectivity']=='connected', observed
        self.record('D9 exclude/backup/restore with checksum and confirmation; MCP call and read-model recover', broker_observation=observed['dockerObservation'], read_model=observed['mcpConnectivity'])
        super().finish()
