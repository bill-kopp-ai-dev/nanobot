# Relatório técnico — MCP containerizado no Percival

**Projeto:** Percival  
**Base:** fork de `HKUDS/nanobot`  
**Data da pesquisa:** 3 de outubro de 2026  
**Objetivo:** avaliar a maturidade das soluções existentes para uso de servidores MCP empacotados em imagens Docker e consolidar referências úteis para a arquitetura do Percival.

---

## 1. Resumo executivo

A pesquisa avaliou quatro grupos principais de referências:

1. o suporte MCP atual do **HKUDS/nanobot**;
2. forks, derivados e projetos relacionados ao nanobot;
3. o subsistema MCP do **NousResearch/hermes-agent**;
4. forks, derivados e integrações do Hermes com Docker/MCP.

A principal conclusão é que **o nanobot já consegue executar servidores MCP empacotados em Docker**, mas faz isso indiretamente: Docker é tratado como um launcher de processo `stdio`, por exemplo `command: docker` com `args: ["run", ...]`. O projeto não possui uma abstração first-class para imagens, containers, volumes, redes, políticas de pull, recursos, healthchecks ou lifecycle de containers.

O Hermes chega mais longe no gerenciamento do **lifecycle MCP**, oferecendo conceitos como lazy startup, cache persistente de schemas, reciclagem por inatividade ou idade máxima, supervisão de processos, health/reconnect e shutdown estruturado. Entretanto, também não trata Docker como um runtime MCP first-class: um `docker run` continua sendo apenas um comando `stdio`.

As referências mais importantes encontradas fora dos cores principais foram:

- **`lucmuss/nanobot-webgui`**, que reconhece manifests OCI, traduz `runtimeArguments` em `docker run`, verifica o runtime Docker e automatiza instalação/registro;
- **`obot-platform/nanobot`**, projeto homônimo e não relacionado ao HKUDS, que implementou sandbox/containerização MCP como conceito explícito;
- **Docker MCP Gateway**, que oferece o modelo mais completo encontrado para servidores MCP containerizados: `image` first-class, containers gerenciados, secrets por servidor, controles de rede, recursos e verificação de imagens;
- **`simonferquel-clanker/hermes-agent-mcp-kit`**, que demonstra uma arquitetura prática na qual o agente executa dentro de um sandbox e se conecta automaticamente a um MCP Gateway externo, sem receber controle direto do Docker daemon;
- **`uudruid74/hermes-agent`**, fork direto do Hermes com melhorias úteis de robustez operacional no subsistema MCP, como prevenção de double-spawn e exposição do `stderr` real do subprocesso.

A arquitetura recomendada para o Percival é, portanto, **não transformar o agente em um orquestrador Docker**. O Percival deve manter um subsistema MCP robusto e independente do runtime, enquanto servidores containerizados são executados por um componente especializado, preferencialmente o Docker MCP Gateway ou outra implementação compatível.

A separação recomendada é:

```text
MCP protocol != MCP transport != MCP runtime
```

Em alto nível:

```text
                         PERCIVAL
                            │
              ┌─────────────┴─────────────┐
              │                           │
        MCP Client Core             MCP Registry
       (nanobot-based)           + policies/config
              │                           │
              └─────────────┬─────────────┘
                            │
                  Streamable HTTP MCP
                            │
                            ▼
                  ┌──────────────────┐
                  │ MCP Runtime Host │
                  │ Docker Gateway   │
                  └────────┬─────────┘
                           │
             ┌─────────────┼─────────────┐
             ▼             ▼             ▼
        PubMed MCP     UniProt MCP    GitHub MCP
        container      container      container
```

A consequência mais importante desse desenho é que o container do Percival **não precisa montar `/var/run/docker.sock`** e não precisa receber privilégios equivalentes aos do Docker daemon.

---

# 2. Escopo e perguntas da pesquisa

A investigação buscou responder principalmente às seguintes perguntas:

- O nanobot já executa MCPs empacotados em Docker?
- Esse suporte é apenas uma consequência do transporte `stdio` ou existe uma abstração Docker explícita?
- Há forks do nanobot que já tenham resolvido esse problema?
- O Hermes Agent possui uma arquitetura MCP mais madura que possa inspirar o Percival?
- Existem forks ou derivados do Hermes com integração Docker/MCP mais avançada?
- É tecnicamente justificável implementar um `DockerMCPManager` diretamente dentro do Percival?
- Ou é preferível delegar container lifecycle a um runtime/gateway externo?

Neste relatório, **first-class Docker MCP support** significa que o sistema entende conceitualmente objetos como:

```text
image
image digest
container
container id
pull policy
volumes
network policy
resource limits
secrets
health
container lifecycle
```

e não apenas que consegue executar:

```bash
docker run ...
```

como qualquer outro subprocesso.

---

# 3. Estado atual do MCP no HKUDS/nanobot

Repositório:

<https://github.com/HKUDS/nanobot>

## 3.1 O nanobot possui um cliente MCP real e relativamente maduro

O suporte MCP atual está concentrado principalmente em:

<https://github.com/HKUDS/nanobot/blob/main/nanobot/agent/tools/mcp.py>

O código utiliza o SDK oficial MCP para Python e suporta os transportes:

```text
stdio
SSE
Streamable HTTP
```

O core inclui, entre outras funções:

- descoberta e registro dinâmico de tools;
- resources e prompts;
- paginação de `tools/list`;
- filtros de tools habilitadas;
- timeouts;
- reconnect em falhas transitórias;
- cleanup assíncrono;
- normalização de JSON Schema;
- sanitização de nomes de tools;
- handling de notificações MCP problemáticas;
- validação de destinos HTTP;
- proteção contra SSRF;
- OAuth para servidores remotos;
- status operacional exposto ao WebUI.

Portanto, **não é necessário reimplementar a camada de protocolo MCP no Percival**.

---

## 3.2 Modelo de configuração atual

O schema de configuração está em:

<https://github.com/HKUDS/nanobot/blob/main/nanobot/config/schema.py>

O modelo de um servidor MCP possui campos equivalentes a:

```python
type: Literal["stdio", "sse", "streamableHttp"] | None
auth: Literal["oauth"] | None

command: str
args: list[str]
env: dict[str, str]
cwd: str

url: str
headers: dict[str, str]

tool_timeout: int
enabled_tools: list[str]
```

Esse schema descreve:

```text
transport
+
launch command
+
connection settings
```

Mas não descreve um container.

Não há, no modelo MCP, propriedades first-class como:

```text
image
container_name
pull_policy
volumes
ports
read_only
user
network
memory
cpus
healthcheck
restart_policy
```

Essa ausência é uma evidência direta de que Docker não é um runtime MCP de primeira classe no nanobot.

---

# 4. Como o nanobot executa MCPs Docker hoje

O transporte `stdio` constrói um `StdioServerParameters` com:

```python
command
args
env
cwd
```

Conceitualmente:

```text
nanobot
   │
   ▼
stdio_client()
   │
   ▼
subprocess(command, args)
```

Logo, esta configuração é válida:

```yaml
tools:
  mcpServers:
    github:
      type: stdio
      command: docker
      args:
        - run
        - -i
        - --rm
        - ghcr.io/github/github-mcp-server
```

O nanobot enxerga:

```text
process = docker
```

e não:

```text
runtime = docker
image = ghcr.io/...
container = ...
```

---

## 4.1 Evidência oficial dentro do próprio projeto

O WebUI do nanobot possui um preset para o servidor MCP oficial do GitHub em:

<https://github.com/HKUDS/nanobot/blob/main/nanobot/webui/mcp_presets_api.py>

O padrão é equivalente a:

```python
MCPServerConfig(
    type="stdio",
    command="docker",
    args=[
        "run",
        "-i",
        "--rm",
        "-e",
        "GITHUB_PERSONAL_ACCESS_TOKEN",
        "ghcr.io/github/github-mcp-server",
    ],
    tool_timeout=60,
)
```

Portanto:

> **MCP via Docker é um caso de uso oficialmente utilizado pelo nanobot.**

Mas a implementação continua sendo:

```text
Docker CLI as stdio launcher
```

e não:

```text
managed Docker MCP runtime
```

---

## 4.2 Histórico do suporte

A implementação original foi introduzida pelo PR:

<https://github.com/HKUDS/nanobot/pull/554>

O PR já descrevia explicitamente suporte a:

```text
stdio (local commands / Docker)
streamable HTTP
```

O exemplo utilizava:

```json
{
  "tools": {
    "mcpServers": {
      "github": {
        "command": "docker",
        "args": [
          "run",
          "-i",
          "--rm",
          "-e",
          "GITHUB_PERSONAL_ACCESS_TOKEN=<token>",
          "ghcr.io/github/github-mcp-server"
        ]
      }
    }
  }
}
```

Desde então, o subsystem MCP cresceu consideravelmente em robustez, mas o modelo Docker continuou fundamentalmente igual.

---

# 5. Maturidade do suporte Docker no nanobot

Uma forma útil de classificar o estado atual é:

| Camada | Maturidade |
|---|---|
| Protocolo MCP | alta |
| MCP stdio | alta |
| MCP HTTP | alta |
| OAuth MCP | alta |
| Tool discovery | alta |
| `docker run` como stdio | funcional/oficial |
| Docker image awareness | inexistente no core |
| Container ID tracking | inexistente |
| Pull policy | inexistente |
| Volumes como objeto semântico | inexistente |
| Network policy por MCP | inexistente |
| Resource limits por MCP | inexistente |
| Container health | inexistente |
| Docker-specific lifecycle | inexistente |

Assim, o suporte atual pode ser resumido como:

> **MCP Docker é suportado operacionalmente, mas Docker não é uma abstração do domínio MCP.**

---

# 6. Problema especial: Percival executado dentro de Docker

Esse ponto é particularmente importante para o projeto Percival.

Se o próprio Percival estiver dentro de um container e sua configuração MCP contiver:

```yaml
command: docker
```

serão necessários:

1. Docker CLI dentro do container;
2. acesso a um Docker daemon.

Uma solução comum seria montar:

```text
/var/run/docker.sock
```

dentro do container.

Entretanto, acesso ao Docker socket normalmente representa poder muito elevado sobre o host e reduz significativamente a fronteira de isolamento do container do agente.

A arquitetura:

```text
Percival container
      │
      ▼
/var/run/docker.sock
      │
      ▼
Docker daemon
      │
      ▼
host
```

deve ser evitada quando existir uma alternativa com separação de privilégios.

Não foi encontrado no HKUDS/nanobot um subsystem específico para administrar com segurança esse cenário.

---

# 7. Forks e derivados do nanobot

## 7.1 `lucmuss/nanobot-webgui`

Repositório:

<https://github.com/lucmuss/nanobot-webgui>

Arquivo especialmente relevante:

<https://github.com/lucmuss/nanobot-webgui/blob/main/nanobot_webgui/mcp_service.py>

Esse projeto foi o derivado mais relevante encontrado dentro do ecossistema próximo ao nanobot.

Ele adiciona um serviço de instalação/gerenciamento MCP que reconhece diferentes estratégias de instalação, incluindo:

```text
npm
source
remote
OCI
```

Para OCI, o código implementa explicitamente uma modalidade semelhante a:

```text
install_mode = "oci"
```

e traduz manifests OCI para uma execução Docker.

---

## 7.2 Tradução de OCI para `docker run`

A implementação possui lógica específica para:

```text
runtimeArguments
```

e uma função equivalente a:

```text
_build_oci_runtime_args(...)
```

cujo objetivo é traduzir argumentos declarados pelo manifest em argumentos de runtime Docker.

O resultado final segue o padrão:

```python
run_command = "docker"

run_args = [
    "run",
    "-i",
    "--rm",
    ...runtime_args,
    image,
]
```

Arquiteturalmente:

```text
MCP manifest
    │
    ▼
OCI metadata
    │
    ▼
runtimeArguments
    │
    ▼
docker run generation
    │
    ▼
MCPServerConfig(command="docker")
```

Esse projeto melhora significativamente a ergonomia e o onboarding de MCPs Docker.

---

## 7.3 O que ele resolve

O projeto adiciona:

- identificação de manifests OCI;
- parsing de imagem;
- tradução de runtime arguments;
- verificação da presença do Docker runtime;
- fluxo de instalação;
- preflight;
- teste de conexão;
- `tools/list`;
- persistência de status;
- logging de erros;
- registro no nanobot.

Isso representa uma camada de:

```text
discovery
+
installation
+
configuration
+
validation
```

bastante útil.

---

## 7.4 O que ele não resolve

Depois de toda a lógica OCI, o core do nanobot ainda recebe:

```text
command = docker
args = [...]
```

Não há um objeto equivalente a:

```text
DockerMCPRuntime
DockerMCPInstance
ContainerHandle
ContainerManager
```

Logo, o projeto não implementa:

- container ID tracking;
- image lifecycle;
- healthcheck Docker;
- políticas de pull;
- resource limits como modelo semântico;
- network policy como modelo semântico;
- garbage collection;
- auditoria de containers;
- gerenciamento especializado de volumes.

**Conclusão:** excelente referência para **importação/configuração OCI**, mas não um runtime completo.

---

# 8. `obot-platform/nanobot`: importante referência externa

Repositório:

<https://github.com/obot-platform/nanobot>

Esse projeto **não é fork do HKUDS/nanobot**. É um projeto homônimo, anterior e independente.

Atualmente o repositório informa estar em maintenance mode e que parte de sua funcionalidade está sendo substituída por outras tecnologias do ecossistema Obot.

Apesar disso, é uma referência arquitetural valiosa porque tratou MCP como um elemento central da plataforma e implementou sandboxing/containerização de servidores MCP de forma mais explícita.

Durante a pesquisa foram encontrados componentes de sandbox MCP, incluindo lógica de execução de containers e conceitos como:

```text
image
dockerfile
unsandboxed
container name
port mapping
```

Essa abordagem é muito mais próxima de:

```text
MCP server
   │
   ▼
sandbox/container runtime
   │
   ▼
Docker
```

que do padrão:

```text
command = docker
```

do HKUDS/nanobot.

Por isso, o projeto é uma boa referência para estudar **como modelar runtime e sandbox como domínio**, mesmo que não seja apropriado copiar diretamente sua implementação.

---

# 9. Docker MCP Gateway

Repositório:

<https://github.com/docker/mcp-gateway>

Documentação principal:

<https://github.com/docker/mcp-gateway/blob/main/docs/mcp-gateway.md>

Especificação de servidor:

<https://github.com/docker/mcp-gateway/blob/main/docs/server-entry-spec.md>

Segurança:

<https://github.com/docker/mcp-gateway/blob/main/docs/security.md>

Essa foi a referência mais importante encontrada para a parte de runtime/container orchestration.

---

## 9.1 Docker image como objeto first-class

O Gateway possui tipo específico para servidor containerizado.

Exemplo conceitual:

```yaml
name: github-official
type: server
title: GitHub Official
description: GitHub MCP server
image: ghcr.io/github/github-mcp-server@sha256:...

secrets:
  - name: github.personal_access_token
    env: GITHUB_PERSONAL_ACCESS_TOKEN

allowHosts:
  - api.github.com:443
  - github.com:443
```

Na especificação do Gateway, servidores do tipo:

```text
type: server
```

representam explicitamente:

> um MCP server containerizado executado e gerenciado pelo gateway.

Isso é first-class Docker MCP support.

---

## 9.2 Campos relevantes

A especificação suporta conceitos como:

```text
image
command
volumes
user
longLived
secrets
allowHosts
disableNetwork
```

Além disso, a documentação de segurança descreve:

- isolamento Docker;
- `no-new-privileges`;
- limites de CPU e memória configurados;
- controle de bind mounts;
- bind mounts read-only por padrão em contextos protegidos;
- restrições sobre caminhos sensíveis;
- secrets escopados por servidor;
- políticas de egress;
- verificação de assinatura para imagens do namespace MCP da Docker;
- recomendação de pin por digest.

Esse conjunto de propriedades é muito mais próximo do que o Percival precisaria caso tentasse criar seu próprio runtime.

---

# 10. Implicação arquitetural do Docker MCP Gateway

Com um gateway, a arquitetura muda de:

```text
Percival
   │
   ▼
Docker daemon
   │
   ▼
MCP containers
```

para:

```text
Percival
   │
   │ MCP
   ▼
Docker MCP Gateway
   │
   ▼
Docker daemon
   │
   ├── MCP container A
   ├── MCP container B
   └── MCP container C
```

Isso cria uma separação clara de responsabilidades.

### Percival

Responsável por:

```text
agent reasoning
tool selection
MCP client
tool policy
schema caching
connection health
user-facing errors
```

### Gateway

Responsável por:

```text
image
container
network
volumes
resource limits
container health
secrets
image verification
container lifecycle
```

Essa separação é desejável do ponto de vista de segurança e manutenção.

---

# 11. Hermes Agent

Repositório:

<https://github.com/NousResearch/hermes-agent>

O Hermes foi analisado porque é um dos frameworks Python agentic mais completos atualmente disponíveis e possui um subsystem MCP consideravelmente mais sofisticado que o nanobot.

---

# 12. Modelo MCP do Hermes

Referência:

<https://github.com/NousResearch/hermes-agent/blob/main/website/docs/reference/mcp-config-reference.md>

O modelo principal continua baseado em dois padrões.

### Servidor local

```yaml
mcp_servers:
  server:
    command: "..."
    args: []
    env: {}
```

### Servidor remoto

```yaml
mcp_servers:
  server:
    url: "https://..."
    headers: {}
```

Assim como no nanobot, não existem propriedades MCP first-class como:

```text
image
container
pull_policy
network
volumes
container_id
```

Portanto:

> **Hermes também não implementa Docker MCP como runtime first-class.**

---

# 13. Docker no Hermes

Apesar disso, Docker é uma forma explicitamente reconhecida de launcher MCP.

O Desktop possui um parser em:

<https://github.com/NousResearch/hermes-agent/blob/main/apps/desktop/src/lib/mcp-import.ts>

que aceita conteúdo colado de documentação, incluindo:

```text
mcp.json
npx command
docker command
claude mcp add
server URL
Cursor install deeplink
```

Docker aparece na lista de comandos `stdio` reconhecidos.

O parser entende argumentos comuns de `docker run`, inclusive opções que consomem valores, como:

```text
--entrypoint
--env
--label
--mount
--name
--network
--platform
--publish
--pull
--user
--volume
--workdir
```

Isso permite converter:

```bash
docker run -i --rm -e TOKEN=... ghcr.io/acme/mcp:1
```

em:

```yaml
mcp_servers:
  acme:
    command: docker
    args:
      - run
      - -i
      - --rm
      - ...
```

É excelente UX, mas arquiteturalmente continua sendo:

```text
Docker command → generic stdio MCP
```

---

# 14. O grande diferencial do Hermes: lifecycle MCP

O Hermes introduz conceitos que são extremamente úteis para o Percival.

## 14.1 `MCPServerTask`

Cada servidor possui uma task gerenciada responsável por:

```text
connect
initialize
discover
health
call handling
reconnect
shutdown
```

Em termos conceituais:

```text
MCP event loop
    │
    ├── MCPServerTask A
    ├── MCPServerTask B
    └── MCPServerTask C
```

Isso é superior a pensar em MCP apenas como uma lista estática de ferramentas.

---

## 14.2 Lazy startup

O Hermes suporta:

```yaml
lazy: true
```

Com lazy startup:

```text
Hermes starts
    │
    ▼
load tool schema cache
    │
    ▼
expose tools to model
    │
    ▼
no MCP process yet
```

Somente quando a tool é chamada:

```text
tool call
   │
   ▼
spawn/connect MCP
   │
   ▼
execute
```

Esse padrão é particularmente atraente para MCPs containerizados.

---

## 14.3 Schema cache persistente

O Hermes persiste schemas de tools previamente descobertas.

Isso permite iniciar o agente sem subir imediatamente todos os servidores MCP.

Aplicado ao Percival:

```text
Percival start

PubMed MCP    OFF
UniProt MCP   OFF
ChEMBL MCP    OFF
GitHub MCP    OFF

tool schemas available from cache
```

Quando uma tool do UniProt é chamada:

```text
tool call
   │
   ▼
activate runtime
   │
   ▼
connect
   │
   ▼
execute
```

Esse padrão pode reduzir significativamente cold starts e consumo de recursos.

---

## 14.4 Idle recycle

O Hermes suporta:

```yaml
idle_timeout_seconds: N
```

O servidor pode ser desligado após período sem uso e reativado na chamada seguinte.

Fluxo:

```text
RUNNING
   │
   │ idle timeout
   ▼
STOPPED
   │
   │ next tool call
   ▼
RUNNING
```

---

## 14.5 Max lifetime

Também existe:

```yaml
max_lifetime_seconds: N
```

Esse recurso permite reciclar servidores após um tempo máximo, mesmo em uso prolongado.

Para workloads containerizados isso pode ajudar a:

- conter memory leaks;
- renovar conexões;
- eliminar estado acumulado;
- simplificar recuperação.

---

## 14.6 Shutdown estruturado

O Hermes possui funções específicas de shutdown que permitem que cada task MCP encerre seu próprio contexto async corretamente.

Essa abordagem é preferível a matar processos indiscriminadamente.

---

# 15. Robustez operacional do Hermes

Além do lifecycle, a pesquisa encontrou mecanismos para:

```text
orphan process cleanup
death supervision
stderr capture
startup failure diagnostics
reconnect
session expiration
tool filtering
trust policies
safe environment construction
OAuth
```

Portanto, mesmo que não copiemos código, o Hermes é uma excelente referência para a camada:

```text
MCP connection/runtime supervision
```

do Percival.

---

# 16. Docker sandbox do Hermes é first-class — mas separado do MCP

O Hermes possui um subsystem first-class de execução Docker para:

```text
terminal
file operations
execute_code
```

O backend Docker pode manter um container persistente e executar comandos com:

```text
docker exec
```

Há configurações relacionadas a:

```text
docker_image
docker_volumes
docker_env
docker_extra_args
docker_shm_size
persistent container
```

Isso comprova que os desenvolvedores sabem modelar Docker como runtime.

Entretanto, esse subsystem não é utilizado como runtime para MCP.

A separação é aproximadamente:

```text
terminal subsystem
    │
    ▼
DockerBackend
```

versus:

```text
MCP subsystem
    │
    ▼
stdio_client
    │
    ▼
subprocess(command, args)
```

Essa separação é arquiteturalmente instrutiva para o Percival.

---

# 17. Forks e derivados do Hermes

## 17.1 `uudruid74/hermes-agent`

Repositório:

<https://github.com/uudruid74/hermes-agent>

É um fork direto e bastante modificado do Hermes.

Ele não implementa um Docker MCP runtime, mas adiciona melhorias úteis de robustez.

### Diagnóstico de `stderr`

Commit relevante:

<https://github.com/uudruid74/hermes-agent/commit/db704c4072d5d94a4c312389d18990777245deeb>

Uma falha de servidor stdio podia aparecer apenas como:

```text
Connection closed
```

mesmo que o subprocesso tivesse produzido uma mensagem útil.

O fork passou a recuperar o `stderr` recente do servidor e incluí-lo no diagnóstico.

Para Docker, isso transforma:

```text
Connection closed
```

em algo operacionalmente útil como:

```text
permission denied
image not found
invalid mount
network not found
invalid argument
```

Esse padrão deve ser considerado para Percival.

---

## 17.2 Prevenção de duplicate spawn

Outro conjunto de alterações no fork lida com:

```text
duplicate MCP spawns
stale connecting entries
```

Esse problema é importante em qualquer modelo lazy:

```text
two concurrent tool calls
        │
        ▼
both see STOPPED
        │
        ▼
both start server
```

Para Percival, o runtime state deveria ser protegido por lock e possuir estados explícitos:

```text
STOPPED
STARTING
RUNNING
STOPPING
FAILED
```

Uma interface desejável seria:

```python
async with lifecycle_lock(server_id):
    runtime = await ensure_running(server_id)
```

---

# 18. `simonferquel-clanker/hermes-agent-mcp-kit`

Repositório:

<https://github.com/simonferquel-clanker/hermes-agent-mcp-kit>

Esse é um dos achados mais importantes da pesquisa.

Não é um fork direto do código do Hermes. É uma customização do kit de sandbox da Docker para Hermes.

O projeto implementa explicitamente:

> **MCP gateway awareness**

---

## 18.1 Descoberta automática de gateway

Quando o sandbox possui um gateway MCP reservado, a plataforma injeta:

```text
MCP_GATEWAY_URL
MCP_SENTINEL_TOKEN_NAME
```

No startup, o kit registra automaticamente:

```yaml
mcp_servers:
  mcp-gateway:
    url: $MCP_GATEWAY_URL
    headers:
      Authorization: "Bearer $MCP_SENTINEL_TOKEN_NAME"
```

Assim, o Hermes não precisa receber acesso ao Docker daemon.

A arquitetura é:

```text
Hermes sandbox
      │
      │ MCP
      ▼
MCP Gateway
      │
      ▼
containerized MCP servers
```

Esse é um precedente real extremamente próximo da arquitetura recomendada para Percival.

---

## 18.2 Reconfiguração a cada boot

O gateway é registrado em todos os starts do sandbox.

Isso protege contra situações em que snapshots carregam:

```text
old URL
old token
missing gateway config
```

A regra é:

```text
boot
  │
  ▼
read runtime environment
  │
  ▼
reconcile effective MCP config
```

Essa abordagem é preferível a assumir que runtime endpoints são permanentemente estáveis.

---

## 18.3 Merge atômico de configuração

O kit não sobrescreve todo:

```text
~/.hermes/config.yaml
```

Ele faz merge da entrada correspondente e usa escrita atômica com arquivo temporário + rename.

Uma versão ainda melhor para Percival seria manter separadamente:

```text
persistent user config
runtime-discovered config
```

e construir uma configuração efetiva em memória.

---

# 19. Sentinel credentials

O `hermes-agent-mcp-kit` introduz um padrão especialmente interessante para segurança.

O sandbox recebe um token-sentinela, e um componente externo substitui a referência pela credencial real.

Conceitualmente:

```text
Agent sandbox
     │
     │ Bearer SENTINEL
     ▼
credential proxy
     │
     │ real credential
     ▼
MCP Gateway
```

Com isso, o segredo real não precisa estar disponível no ambiente do agente.

Para Percival, um design equivalente poderia usar referências como:

```yaml
auth:
  secret_ref: percival://mcp/github
```

em vez de:

```yaml
env:
  GITHUB_TOKEN: ghp_...
```

Esse padrão deve ser considerado em uma fase futura de hardening.

---

# 20. `nativ3ai/hermes-agent-camel`

Repositório:

<https://github.com/nativ3ai/hermes-agent-camel>

Esse fork não resolve Docker MCP, mas é útil do ponto de vista de segurança.

Ele adiciona um runtime guard inspirado em CaMeL e trata MCP servers como componentes de confiança inferior a código instalado diretamente.

Um princípio particularmente útil é:

```text
Skills installed locally → high trust
MCP server subprocesses  → lower trust
```

O subprocesso MCP recebe um ambiente filtrado, com baseline restrita e apenas variáveis explicitamente permitidas.

Esse padrão deve ser aplicado no Percival mesmo quando Docker não estiver envolvido.

---

# 21. MCPJungle

Projeto:

<https://github.com/mcpjungle/MCPJungle>

O MCPJungle funciona como registry/gateway central para múltiplos servidores MCP.

A arquitetura é:

```text
Agent clients
      │
      ▼
single MCP endpoint
      │
      ▼
MCPJungle
      │
      ├── MCP A
      ├── MCP B
      └── MCP C
```

Um aspecto interessante é o suporte a modos de sessão.

---

## 21.1 Stateless

Por padrão, uma chamada pode seguir:

```text
tool call
   │
   ▼
spawn/connect server
   │
   ▼
execute
   │
   ▼
close
```

Isso minimiza estado persistente, mas aumenta cold-start.

---

## 21.2 Stateful

Com:

```json
{
  "session_mode": "stateful"
}
```

a conexão pode permanecer viva:

```text
first call
   │
   ▼
start server
   │
   ├── call
   ├── call
   ├── call
   │
   ▼
idle timeout / shutdown
```

Esse modelo é semelhante, em nível de gateway, ao `lazy + idle_timeout` do Hermes.

---

# 22. Padrão arquitetural comum observado

Após comparar todos os projetos, aparecem três camadas conceitualmente diferentes.

## 22.1 Protocolo

```text
MCP JSON-RPC semantics
tools
resources
prompts
sampling
elicitation
```

## 22.2 Transporte

```text
stdio
Streamable HTTP
SSE
```

## 22.3 Runtime

```text
native process
Docker container
Podman container
remote service
Kubernetes workload
gateway-managed runtime
```

O erro arquitetural a evitar é misturar os três conceitos.

---

# 23. Arquitetura recomendada para Percival

A recomendação consolidada é criar uma arquitetura na qual o Percival entende runtime como conceito lógico, mas **não precisa necessariamente implementar o runtime Docker internamente**.

```text
Percival
│
├── MCP Client Core
│   ├── transport
│   ├── discovery
│   ├── schema normalization
│   ├── calls
│   └── reconnect
│
├── MCP Registry
│   ├── server metadata
│   ├── tool policy
│   ├── trust
│   └── runtime references
│
├── MCP Lifecycle
│   ├── lazy activation
│   ├── schema cache
│   ├── health
│   ├── idle recycle
│   └── diagnostics
│
└── Runtime adapters
    ├── process
    ├── remote
    └── gateway
```

Inicialmente:

```text
process
remote
gateway
```

seriam suficientes.

Um runtime direto:

```text
docker
```

poderia ser adicionado posteriormente caso uma necessidade concreta justifique isso.

---

# 24. Schema conceitual proposto

Uma configuração futura poderia seguir:

```yaml
mcp_servers:

  local_tool:
    transport:
      type: stdio

    runtime:
      type: process
      command: uvx
      args:
        - some-mcp-server

  remote_tool:
    transport:
      type: streamable_http

    runtime:
      type: remote
      url: https://example.com/mcp

  container_tools:
    transport:
      type: streamable_http

    runtime:
      type: gateway
      gateway: docker
      server: github-official

    lifecycle:
      lazy: true
      idle_timeout_seconds: 600

    tools:
      include:
        - create_issue
        - search_code
```

Isso separa corretamente:

```text
connection semantics
from
execution semantics
```

---

# 25. Caso futuro: Docker first-class dentro do Percival

Se no futuro for necessário implementar Docker diretamente, o schema poderia evoluir para:

```yaml
mcp_servers:
  uniprot:
    transport:
      type: stdio

    runtime:
      type: docker
      image: ghcr.io/percival/uniprot-mcp@sha256:...

      pull_policy: if-not-present

      security:
        read_only: true

      network:
        allow_hosts:
          - rest.uniprot.org:443

      resources:
        memory: 512m
        cpus: 0.5

    lifecycle:
      lazy: true
      idle_timeout_seconds: 600
      max_lifetime_seconds: 86400
```

Mas essa funcionalidade deve ser vista como uma segunda fase, não como requisito inicial.

---

# 26. Componentes recomendados para o Percival

## 26.1 `MCPProvider`

Pode aproveitar diretamente a arquitetura já existente no nanobot.

Responsabilidades:

```text
connect
discover
register tools
invoke
reconnect
close
```

---

## 26.2 `MCPRegistry`

Nova camada Percival.

Responsabilidades:

```text
server metadata
runtime type
transport type
tool policy
trust tier
secret references
schema cache references
```

---

## 26.3 `MCPLifecycleManager`

Inspirado principalmente no Hermes.

Responsabilidades:

```text
lazy activation
server state machine
locking
idle recycle
max lifetime
health
restart
diagnostics
stderr/error propagation
```

Estados sugeridos:

```text
STOPPED
STARTING
RUNNING
STOPPING
FAILED
```

---

## 26.4 `GatewayRuntimeAdapter`

Responsável por converter a configuração do Percival em uma conexão a um gateway.

Inicialmente pode tratar o Docker MCP Gateway como backend preferencial.

Conceitualmente:

```python
class GatewayRuntimeAdapter:
    async def resolve(self, server_config):
        ...
```

O adapter não precisa necessariamente controlar containers.

Ele pode apenas resolver:

```text
gateway endpoint
authentication
available server
tool exposure
```

---

## 26.5 `ProcessRuntimeAdapter`

Mantém compatibilidade com o comportamento atual do nanobot:

```text
npx
uvx
python
docker run
custom executable
```

Isso evita breaking changes.

---

# 27. Features do Hermes que valem ser portadas conceitualmente

As ideias mais valiosas do Hermes são:

### Schema cache

Permitir exposição das tools sem cold-start obrigatório.

### Lazy activation

Subir/conectar um MCP apenas quando necessário.

### Idle recycle

Liberar processos/conexões sem uso.

### Max lifetime

Reciclar runtimes antigos.

### Structured shutdown

Encerrar recursos pelo owner correto.

### Spawn locking

Impedir activation races.

### Better diagnostics

Capturar stderr e erros do runtime.

### Trust policy

Distinguir servidores confiáveis e não confiáveis.

### Environment filtering

Nunca herdar o ambiente inteiro do processo do agente.

---

# 28. Features do `nanobot-webgui` que valem ser aproveitadas

Especialmente:

```text
OCI manifest recognition
runtimeArguments parsing
automatic dependency checks
preflight
connection test
tool enumeration
installation status
```

Uma função futura de importação no Percival poderia aceitar:

```text
Docker command
MCP JSON
OCI/server manifest
remote URL
Docker MCP catalog entry
```

e normalizar tudo para o schema interno.

---

# 29. Features do Docker MCP Gateway que não devemos reimplementar sem necessidade

Entre outras:

```text
image handling
signature verification
digest enforcement
container lifecycle
secrets per server
network egress controls
bind mount validation
resource limits
container isolation
gateway multiplexing
```

Essas funções são complexas, sensíveis à segurança e já possuem uma implementação especializada.

---

# 30. Threat model simplificado

## 30.1 Ameaça: Docker socket exposto ao agente

Evitar:

```text
Percival container
   │
   ▼
/var/run/docker.sock
```

Risco:

```text
agent compromise
    ↓
Docker control
    ↓
host compromise
```

---

## 30.2 Ameaça: secret leakage

Evitar:

```text
global os.environ
       ↓
every MCP process/container
```

Preferir:

```text
secret store
   │
   ▼
per-server mapping
   │
   ▼
specific MCP runtime
```

---

## 30.3 Ameaça: malicious MCP server

Considerar todos os MCPs não controlados diretamente como componentes de confiança inferior.

Aplicar:

```text
tool allowlist
network policy
minimal secrets
minimal filesystem access
resource limits
approval for write-capable actions
```

---

## 30.4 Ameaça: malicious image

Preferir:

```text
immutable digest
trusted registry
signature verification
catalog allowlist
```

em produção.

Evitar tags mutáveis como única forma de identificação.

---

## 30.5 Ameaça: race no lazy startup

Usar:

```text
server-scoped lock
+
explicit state machine
```

---

# 31. Comparação consolidada

| Capability | HKUDS nanobot | nanobot-webgui | Hermes | obot nanobot | Docker MCP Gateway |
|---|---:|---:|---:|---:|---:|
| stdio MCP | ✅ | ✅ | ✅ | ✅ | ✅ |
| HTTP MCP | ✅ | ✅ | ✅ | ✅ | ✅ |
| Docker via `command: docker` | ✅ | ✅ | ✅ | n/a | n/a |
| Import automático de Docker/OCI | ❌ | ✅ | ✅ para comando Docker | — | catálogo próprio |
| MCP lazy startup | limitado | limitado | ✅ | — | runtime/on-demand |
| Schema cache | limitado | — | ✅ | — | — |
| Idle recycle | ❌ | ❌ | ✅ | — | gateway/runtime dependent |
| Structured MCP lifecycle | médio | médio | ✅ forte | forte | ✅ |
| `image` first-class | ❌ | parcial/import | ❌ | ✅ | ✅ |
| container ID awareness | ❌ | ❌ | ❌ | ✅ | ✅ |
| per-server secrets | config/env | config/env | config/env + secret scopes | parcial | ✅ |
| network policy por container | ❌ | ❌ | ❌ | parcial | ✅ |
| resource limits por MCP | ❌ | ❌ | ❌ | ✅/parcial | ✅ |
| image verification | ❌ | ❌ | ❌ | — | ✅ |
| container runtime specialization | ❌ | ❌ | ❌ | ✅ | ✅ |

---

# 32. Avaliação de maturidade

## Nanobot MCP core

**Maturidade: boa a alta.**

A base já contém a maior parte do que é necessário para protocolo MCP.

Não há justificativa para substituir esse subsystem completamente no Percival.

---

## Nanobot + Docker

**Maturidade: funcional, porém genérica.**

É suficiente para:

```text
docker run -i --rm ...
```

em ambientes controlados.

Não é suficiente para um produto cujo objetivo seja administrar múltiplos MCP containers com políticas consistentes.

---

## Hermes MCP lifecycle

**Maturidade: alta e uma excelente referência.**

É provavelmente a melhor fonte encontrada para desenhar:

```text
lazy
cache
recycle
health
reconnect
shutdown
diagnostics
```

---

## Docker MCP Gateway

**Maturidade: a referência mais completa encontrada para runtime Docker MCP.**

É o candidato natural para ser avaliado como backend inicial do Percival.

---

# 33. Recomendação de implementação em fases

## Fase 1 — preservar upstream

Manter o MCPProvider do nanobot o mais intacto possível.

Objetivo:

```text
minimize fork divergence
```

---

## Fase 2 — adicionar lifecycle Percival

Introduzir:

```text
MCPRegistry
MCPLifecycleManager
schema cache
lazy connect
idle timeout
state machine
spawn locking
diagnostics
```

Inspirar-se no Hermes sem necessariamente copiar sua implementação.

---

## Fase 3 — gateway runtime

Adicionar:

```text
runtime: gateway
```

com suporte inicial ao Docker MCP Gateway.

O Percival continua sendo um MCP client normal.

---

## Fase 4 — secure secret references

Introduzir referências de segredo:

```yaml
secret_ref: percival://...
```

e resolver secrets apenas no runtime que precisa deles.

---

## Fase 5 — OCI/import UX

Adicionar importadores inspirados em:

```text
nanobot-webgui
Hermes Desktop
```

para aceitar:

```text
docker run
MCP JSON
remote URL
OCI manifest
Docker MCP catalog entry
```

---

## Fase 6 — Docker runtime interno, somente se necessário

Implementar:

```text
runtime: docker
```

apenas se o Gateway não puder atender algum requisito concreto do Percival.

---

# 34. Critérios para decidir se um Docker runtime interno será necessário

Devemos implementar controle direto apenas se houver necessidade comprovada de uma ou mais das seguintes capacidades que um gateway externo não consiga oferecer:

- integração muito específica com state interno do Percival;
- controle de containers por sessão/agente impossível de expressar no Gateway;
- runtime alternativo não suportado;
- requisitos offline/embedded incompatíveis com Gateway;
- necessidade de container lifecycle transacional com o agent loop;
- requisitos de UX que não possam ser implementados sobre APIs do Gateway.

Sem uma dessas necessidades, um runtime interno acrescentaria:

```text
security-sensitive code
Docker API coupling
more tests
more lifecycle edge cases
more upstream divergence
more maintenance
```

sem benefício proporcional.

---

# 35. Decisão arquitetural recomendada

A recomendação final da pesquisa é:

> **Percival deve possuir MCP como subsystem first-class, mas Docker não deve ser inicialmente um subsystem first-class dentro do agente.**

Em vez disso:

```text
Percival understands:
- MCP server
- MCP transport
- MCP lifecycle
- runtime type
- trust
- policies
```

e delega:

```text
container orchestration
```

a um runtime especializado.

Arquitetura preferencial:

```text
                         PERCIVAL
                            │
                    MCP Client Core
                            │
                    Lifecycle Manager
                            │
                    Runtime Adapter
                            │
              ┌─────────────┴──────────────┐
              │                            │
        native/stdio                  MCP Gateway
                                           │
                                     Docker runtime
                                           │
                        ┌──────────────────┼──────────────────┐
                        ▼                  ▼                  ▼
                    MCP image A        MCP image B        MCP image C
```

---

# 36. Benefícios esperados para o Percival

Essa arquitetura oferece:

### Segurança

O agente não precisa controlar o Docker daemon.

### Compatibilidade upstream

O core MCP do nanobot pode permanecer próximo do upstream.

### Portabilidade

Um `RuntimeAdapter` permite trocar:

```text
Docker MCP Gateway
MCPJungle
custom gateway
remote hosted MCP platform
```

sem alterar o agent loop.

### Escalabilidade

O gateway pode evoluir independentemente do agente.

### Testabilidade

Podemos testar separadamente:

```text
MCP semantics
lifecycle
gateway integration
container runtime
```

### Manutenção

Menor volume de código de infraestrutura dentro do fork.

---

# 37. Principais referências

## HKUDS/nanobot

Repositório:

<https://github.com/HKUDS/nanobot>

MCP core:

<https://github.com/HKUDS/nanobot/blob/main/nanobot/agent/tools/mcp.py>

Config schema:

<https://github.com/HKUDS/nanobot/blob/main/nanobot/config/schema.py>

MCP presets:

<https://github.com/HKUDS/nanobot/blob/main/nanobot/webui/mcp_presets_api.py>

Guia MCP:

<https://github.com/HKUDS/nanobot/blob/main/docs/guides/configure-mcp-tools.md>

Guia MCP para agentes:

<https://github.com/HKUDS/nanobot/blob/main/docs/guides/mcp-tools-for-ai-agents.md>

PR original de MCP:

<https://github.com/HKUDS/nanobot/pull/554>

---

## nanobot-webgui

Repositório:

<https://github.com/lucmuss/nanobot-webgui>

MCP service:

<https://github.com/lucmuss/nanobot-webgui/blob/main/nanobot_webgui/mcp_service.py>

---

## obot-platform/nanobot

<https://github.com/obot-platform/nanobot>

---

## Docker MCP Gateway

Repositório:

<https://github.com/docker/mcp-gateway>

Gateway docs:

<https://github.com/docker/mcp-gateway/blob/main/docs/mcp-gateway.md>

Server entry specification:

<https://github.com/docker/mcp-gateway/blob/main/docs/server-entry-spec.md>

Security:

<https://github.com/docker/mcp-gateway/blob/main/docs/security.md>

Container deployment example:

<https://github.com/docker/mcp-gateway/blob/main/examples/container/README.md>

---

## Hermes Agent

Repositório:

<https://github.com/NousResearch/hermes-agent>

MCP reference:

<https://github.com/NousResearch/hermes-agent/blob/main/website/docs/reference/mcp-config-reference.md>

MCP user guide:

<https://github.com/NousResearch/hermes-agent/blob/main/website/docs/user-guide/features/mcp.md>

Desktop MCP importer:

<https://github.com/NousResearch/hermes-agent/blob/main/apps/desktop/src/lib/mcp-import.ts>

MCP tool core:

<https://github.com/NousResearch/hermes-agent/blob/main/tools/mcp_tool.py>

MCP lifecycle:

<https://github.com/NousResearch/hermes-agent/blob/main/tools/mcp_tool_lifecycle.py>

MCP health:

<https://github.com/NousResearch/hermes-agent/blob/main/tools/mcp_tool_health.py>

---

## Hermes forks/derivatives

`uudruid74/hermes-agent`:

<https://github.com/uudruid74/hermes-agent>

Relevant MCP diagnostics commit:

<https://github.com/uudruid74/hermes-agent/commit/db704c4072d5d94a4c312389d18990777245deeb>

`hermes-agent-mcp-kit`:

<https://github.com/simonferquel-clanker/hermes-agent-mcp-kit>

`hermes-agent-camel`:

<https://github.com/nativ3ai/hermes-agent-camel>

---

## MCPJungle

<https://github.com/mcpjungle/MCPJungle>

---

# 38. Conclusão

A pesquisa não encontrou, dentro dos forks diretos do HKUDS/nanobot ou do NousResearch/hermes-agent, uma implementação madura que transforme Docker em um runtime MCP first-class completo dentro do próprio agente.

Entretanto, encontrou todos os componentes necessários distribuídos em projetos diferentes:

```text
nanobot
    → bom MCP client core

nanobot-webgui
    → OCI discovery/import/config

Hermes
    → lifecycle, lazy, schema cache, health

uudruid74/hermes-agent
    → robustez, spawn locking, stderr diagnostics

obot-platform/nanobot
    → referência de sandbox/container model

Docker MCP Gateway
    → container runtime first-class

hermes-agent-mcp-kit
    → precedent for agent → gateway architecture

MCPJungle
    → gateway/session lifecycle alternative
```

O melhor desenho para Percival não é reproduzir todas essas capacidades dentro do fork.

O desenho mais sustentável é combinar:

```text
nanobot MCP core
        +
Hermes-inspired MCP lifecycle
        +
Percival registry/policy layer
        +
external container MCP runtime
```

com o **Docker MCP Gateway como primeiro backend a ser prototipado**.

Essa arquitetura mantém a responsabilidade do Percival concentrada naquilo que pertence ao agente — raciocínio, tools, políticas e sessões MCP — e desloca a responsabilidade de containers para uma camada especializada em containers.

Esse princípio deve orientar a implementação inicial:

> **O Percival deve saber que um MCP possui um runtime, mas não precisa ser o runtime.**
