# MCP Docker F0 — inventário e prova de viabilidade

- **Data / revisão:** 2026-10-07; base do Percival `e62e2ce4e5c3ed41d02068746640260d11d127b0`.
- **Escopo da evidência:** árvore versionada e host de desenvolvimento Arch/Omarchy; **não** é o VPS alvo. Nenhum serviço, usuário, imagem ou configuração do Percival foi instalado/modificado no host.
- **Resultado:** inventário e prova discriminante executados. **Gate F0 não aprovado (versão inicial):** o mount raiz expõe o daemon a containers MCP com UID root ou grupo do socket; além disso o Compose existente não conecta o gateway ao broker em loopback e o Engine local não é 27.x. F1 depende de decisão do operador sobre a fronteira B14/B16/B22 e da topologia alvo.  **2026-10-07 — F0 fechado (B24):** o operador adotou B23 (Docker no VPS, persistência futura em `.percival`), validou-o via disposable env local (`scripts/percival-f0-validate.sh` — 11 asserts verdes) e aceitou formalmente o risco **indireto** descrito em §7.2 (R/W no restante do host e leitura do token pelo exec tool).  A execução real de `scripts/percival-vps-inventory.sh` no VPS continua **pendente** e deve acontecer antes do F5/deploy canônico; divergências no inventário podem reabrir a discussão.  F1 ainda não foi iniciada.
- **Fonte normativa:** [plano v1.1](../plans/2026-10-06-mcp-docker-first-class-execution-plan.md), seções 2, 4 (F0) e 5. Este relatório registra observações e um contrato **proposto**, não altera B14–B22.

> **Adendo posterior, 2026-10-07:** o operador adotou B23 e confirmou Percival em Docker no VPS, com persistência futura em `.percival`. As observações acima e as opções da seção 3 preservam o estado **anterior** à decisão. O desenho atual, o novo experimento local e o gate remanescente estão na seção 6 e no [plano v1.2](../plans/2026-10-06-mcp-docker-first-class-execution-plan.md).

## 1. Topologia e pontos de integração

| Fronteira | Inventário verificável | Consequência para F1/F2 |
| --- | --- | --- |
| Deployment existente | `docker-compose.yml` define `nanobot-gateway` e `nanobot-api` na bridge `nanobot_default`, com apenas `~/.nanobot:/home/nanobot/.nanobot`; não define broker nem monta socket. Gateway publica 18790 só em `127.0.0.1` do host e 8765 sem `host_ip`. `docker compose ps --format json` retornou vazio neste host. `Dockerfile` cria UID 1000 `nanobot`, entrypoint reduz privilégios; `docker-compose.bwrap.yml` altera caps/seccomp para sandbox opt-in. | O loopback do gateway em Compose é o **do container**, não o do host. Broker systemd host-only em `127.0.0.1` não é acessível dessa bridge por pressuposição. Escolher/provar uma topologia alvo (p.ex. gateway em processo host, broker também no host; ou proxy autenticado interno que mantenha o broker em loopback) antes de programar transporte; nenhuma escolha foi aprovada. A publicação de 8765 precisa de revisão no ensaio remoto. |
| Identidade e daemon | `docker --version` e `docker version` neste host: Client e Server **29.7.2**, contexto `default`; `docker info` indica raiz `/var/lib/docker` e sem opção rootless reportada. `/usr/bin/docker` existe. `/var/run` é symlink para `/run`; `/run/docker.sock` é socket `0660`, UID 0, GID 966 (`docker`). `getent passwd nanobot docker-broker` não encontrou esses usuários **no host**; `bill` pertence a `docker`. | A instalação local **não** valida o requisito 27.x. Confirmar Client/Server 27.x, suporte e manutenção dessa linha e permissões no VPS/runner aprovado; `docker --version` sozinho não valida Server.Version. Não usar o daemon 29.x como evidência de compatibilidade 27.x. |
| Paths sensíveis | `/:/host` inclui `/run` (socket real), `/var/run` (alias), `/etc`, diretórios home, `/var/lib/docker`, config/credenciais do Percival e possivelmente `/proc` e caminhos alternativos do daemon. O volume `~/.nanobot` do Compose inclui dados e config do gateway. | Redação de respostas não impede leitura via mount. Mapear também `DOCKER_HOST`, sockets TCP, symlinks, bind aliases, `/proc/*/root` e outros endpoints **na topologia alvo**. Não registrar conteúdos de arquivos sensíveis no teste. |
| MCP | `nanobot/agent/tools/mcp.py`: `MCPProvider.from_config`, `connect`, `reload`, reconnect; cliente `streamable_http_client`, `httpx` e `validate_url_target` bloqueiam loopback por padrão. `MCPToolWrapper.execute` mantém `_session` e retries; `ToolRegistry` guarda wrappers, substitui colisões por nome e faz cache de schemas. Recursos/prompts são wrappers distintos (registrados por default nos MCPs genéricos). | A capability gerenciada precisa de namespace próprio, gate em **cada** execução (inclusive wrapper antigo/reconnect e todos os canais), e transporte privado autorizado sem abrir `ssrfWhitelist` global. Desativação não pode depender só de unregister ou filtro em `tools/list`. |
| WebUI/autorização | `nanobot/webui/ws_http.py` allowlista ações WS → rotas; HTTP direto a mutações recebe 405. `settings_routes.py` valida WebUI bearer e roteia settings; `gateway_endpoint.py` autentica handshake; `http_utils.py` calcula origem local considerando proxy. | Adicionar 11 ações ao allowlist e 1 leitura; credencial admin em campo separado do payload WS, consumida sem entrar na query/log/audit; verificar origem **real** em proxy. O bearer WebUI já ocupa Authorization. |
| Config e durabilidade | `ToolsConfig.mcp_servers` em `config/schema.py`; `config/loader.py` carrega/resolve `${VAR}` e `save_config` serializa arquivo inteiro; `_write_text_atomic` preserva modo **apenas** quando arquivo pré-existe. `WebUISettingsConfig.update/run_serialized` usa `RLock` + `FileLock`; também há chamadas diretas a `save_config` em CLI, Feishu, Weixin e domínios WebUI. | Introduzir `tools.mcpDocker` tipado e garantir que `reference` seja resolvida **no broker**, sem a resolução global prematura de `${VAR}` no gateway. Um writer único de *todo* `config.json` requer reconciliar escritores diretos e CLI/canais, sem criar lock próprio da capability (B17); CAS por seção/servidor não corrige perda de escrita em outras seções. Criar config privado `0600` desde a primeira escrita. |

## 2. Experimento discriminante de alcance do daemon

**Hipótese que permitiria prosseguir:** um container MCP com `/:/host` R/W não consegue usar o socket Docker, mesmo quando a imagem escolhe UID root ou obtém o grupo do socket. **Critério de refutação:** `GET /_ping` devolve sucesso via `/host/run/docker.sock` ou alias. O teste usou imagem local `percival-weather-mcp:audit` como runtime Python, `--pull=never`, container efêmero `--rm`, rede `none`, `--cap-drop=ALL`, `no-new-privileges`, raiz da imagem read-only e bind do host **read-only** (mais restritivo que B22). Somente `GET /_ping` no socket; nenhum comando de alteração foi enviado.

| Processo do container | Caminho | Observação neste host |
| --- | --- | --- |
| UID 999 padrão, sem grupo 966 | `/host/run/docker.sock` | Socket visível; `connect` → `PermissionError` errno 13. |
| UID 0 (`--user 0`) | `/host/run/docker.sock` | Socket visível; `GET /_ping` → **HTTP/1.0 200 OK**. |
| UID 999 + `--group-add 966` | `/host/var/run/docker.sock` | Socket visível; `GET /_ping` → **HTTP/1.0 200 OK**. |

Reprodução controlada (read-only, sem rede, sem pull) da linha que refutou a hipótese:

```sh
docker run --rm --pull=never --network=none --cap-drop=ALL \
  --security-opt=no-new-privileges --read-only --user 0 \
  --mount type=bind,src=/,dst=/host,readonly \
  --entrypoint python percival-weather-mcp:audit -c '
import socket
s = socket.socket(socket.AF_UNIX)
s.settimeout(2)
s.connect("/host/run/docker.sock")
s.sendall(b"GET /_ping HTTP/1.0\r\nHost: docker\r\n\r\n")
print(s.recv(128).split(b"\r\n", 1)[0].decode())'
```

O código da imagem permite UID não-root, mas a capability aceita imagens locais arbitrárias e o plano não fixa/impõe UID ou grupos. Bind read-only não impede **operações de escrita pelo protocolo do socket**; root no container conseguiu conectar mesmo sem capacidades adicionais ou rede. Isto prova bypass neste host, não mede ainda aliases/proteções de um VPS não inventariado. Um simples mask de `/host/run/docker.sock` ou `--network=none` não é prova suficiente: alias `/host/var/run`, outros caminhos e escrita no host continuam em escopo.

## 3. Mapa de ameaças e decisão de topologia

| Origem → alvo | Caminho / consequência | Ensaio mínimo que falta |
| --- | --- | --- |
| Imagem/tool MCP → daemon rootful | Socket exposto por mount raiz; Docker API concede controle do host. **Exploração de conectividade já observada.** | Em F1, testar a **imagem real com UID efetivo** e uma imagem local root, aliases, grupo e rotas alternativas em VPS isolado; acesso precisa falhar fechado sem exceções de servidor. |
| Imagem/tool MCP → host | `/:/host` R/W permite acesso aos arquivos autorizados pelo UID/mapeamento efetivo, inclusive segredos/config, e possivelmente a caminhos que reabrem acesso ao daemon. | Validar leitura/escrita efetivas de paths controlados sem dados sensíveis, proc/symlink e permissões; documentar o alcance residual, não prometer confidencialidade de segredos do host. |
| Gateway/exec → daemon | Compose hoje não monta socket, mas o gateway precisa falar com broker sem ganhar Docker CLI/socket/endpoint equivalente. | Testar tentativas do processo gateway e da exec tool, incluindo acesso indireto pela API broker; comandos administrativos arbitrários devem ser inexistentes. |
| Rede externa → broker | Bind em 127.0.0.1 host e token estático; Compose bridge não partilha namespace; reverse proxy/headers podem falsificar origem. | Provar MCP/admin acessíveis **apenas** pelo gateway na topologia escolhida, bloqueio externo, autenticação por request e rotação sem vazamento; host/bridge/proxy testados. |
| Várias escritas → `config.json` | `save_config` grava o arquivo todo; locks WebUI não cobrem todos os writers identificados. | Intercalar mutações de canal, CLI e WebUI com CAS e verificar que outras seções não são perdidas. |

**Opções para decisão do operador (não implementadas):**

1. **Recomendada para investigar:** redefinir a fronteira como acesso amplo a arquivos do host **com exclusão explícita e testada do plano de controle do daemon**, por isolamento efetivo de mount/UID/serviço e de caminhos alternativos. Isso modifica o literal `/:/host` irrestrito de B22 e o sentido de "toda a árvore" de B14; mascarar um path isolado não é solução comprovada. Exige nova decisão e teste adversarial no VPS.
2. Manter mount raiz irrestrito e reconhecer que um MCP pode controlar o daemon. É incompatível com a proibição de B14/B16 de expor socket/equivalente ao agente; exigiria revogar explicitamente essa garantia e aceitar o risco rootful. **Não recomendado.**
3. Manter todas as decisões e adiar a capability: não há evidência de uma topologia que simultaneamente mantenha o mount raiz irrestrito e negue o daemon a imagens arbitrárias.

Escolher host-gateway + host-broker resolve **apenas** o problema de loopback, não o acesso do MCP ao socket. Qualquer proposta de proteção do socket deve enfrentar mounts alternativos, `/proc`, grupo/UID, credenciais e escrita em paths do host; não declarar isolamento por construção verbal.

## 4. Contrato proposto e viabilidade restante

- **Transporte candidato para ensaio:** gateway e broker em processos distintos no **mesmo namespace de rede host**, broker bind apenas em `127.0.0.1`, MCP Streamable HTTP autenticado + endpoints administrativos tipados autenticados, token distinto do WebUI bearer e da senha operator-admin. O deployment atual em Compose **não** satisfaz essa condição; alternativa de proxy local exige desenho e ensaio adicionais. Sem transporte genérico de comandos Docker. Aplicar limite de tamanho, timeouts de conexão/execução, erros redigidos e autorização a cada request; rejeitar redirects e bypass SSRF por origem genérica. Política exata de timeout e rotação (troca atômica, revogação da chave antiga e reconexão das sessões) precisa de teste em F1/F2; não há contrato operacional validado ainda.
- **SDK:** `pyproject.toml` declara `mcp>=1.26.0,<2.0.0`; no ambiente `uv run --no-sync` do Percival há MCP **1.30.0**, Python **3.12.14**. Fixar versão de teste no lock/CI e validar `initialize`, `tools/list` e `tools/call` no protocolo real em F1.
- **Fixtures:** `percival-weather-mcp` versão 0.9.0, SHA `b5032f4fe4f0e89cc49556b62725ba598fb1c181`, e `percival-osm` versão 0.5.0, SHA `ca3c3977fc124b649876900fc0c3ffb6fe7c87fb`, têm Dockerfiles multi-stage e entrada stdio. OSM tem `uv.lock` modificado localmente; não copiar árvore de trabalho como CI. F1 deve fazer checkout por SHA em diretório independente, verificar licenças/locks, construir com `--pull` controlado e registrar IDs de imagem e RepoDigest **separadamente**; fixtures buildadas localmente não geram automaticamente RepoDigest, exigindo registry de ensaio para `pinned-image` e segundo digest real de update. `percival-weather-mcp/LICENSE` contém **Apache-2.0**, enquanto seu OCI label anuncia **MIT**: reconciliar proveniência/licença antes de copiar/redistribuir a fixture. `percival-osm/LICENSE` é MIT. Não houve build nem chamada MCP das duas fixtures nesta fase.
- **Viabilidade CI:** o Docker 27.x não está instalado aqui; disponibilidade/suporte de Client+Server 27.x no VPS e no runner Arch/Ubuntu, manutenção da linha e configuração de daemon rootful continuam **não verificados**. F0 não instala Docker no VPS. Propor ensaio controlado após aprovação da topologia, com gateway sem socket, broker dedicado e controle de UID/grupo dos MCPs, mais matriz de testes abaixo.

## 5. Provas mínimas para abrir F1

1. Operador escolhe e aceita a fronteira de acesso (ou mantém gate bloqueado); confirmar diagrama host/Compose, namespaces, usuários/grupos, sockets, montagens e superfícies de rede do **VPS real**.
2. Prova negativa com gateway, exec tool e containers MCP (root e não-root, alias `/host/var/run`, `/host/run`, symlink/proc e endpoints TCP) em ambiente descartável; provar acesso a arquivos pretendidos e **negação** de Docker API quando essa for a política escolhida.
3. Prova de Streamable HTTP `initialize`/`tools/list`/`tools/call` com token em broker não exposto externamente; requests sem token/rotacionados e falha do broker devem fechar gate, com timeouts medidos.
4. Validar CLI **e daemon** 27.x, permissões do usuário dedicado e política de Docker Engine suportada; registrar comandos, versões, digests e inspeção de rede/mounts sem segredos.
5. Reconciliar licença weather, registrar SHAs/lockfiles reproduzíveis, executar fixture pinada sem depender de `~/Projects/*` e criar registry/digests reais para cenário de update.

**Estado do gate:** **F0 fechado em 2026-10-07 via B24** (registrada em `.positronic/PROJECT.md`).  O operador aceitou o desenho + disposable env + risco indireto documentado; o inventário real do VPS continua pendente e o F5 exigirá nova aceitação formal antes de qualquer deploy canônico.

## 6. Adendo B23 — exclusões locais testadas e desenho Docker-first

**Decisão do operador:** acesso amplo a arquivos do host por default, com exclusões do controle do Docker e estado/credenciais da capability; instalação real do Percival **em Docker no VPS**; persistência do host em `.percival` (hoje `~/.nanobot`); segurança proporcional ao custo, com risco residual deliberado e visível. B23 em `.positronic/PROJECT.md` registra o escopo da revisão de B14/B22. Nenhuma mudança de runtime/deployment foi aplicada nesta F0.

**Hipótese local:** desativar a recursão do bind raiz omite submounts do host, incluindo `/run` e `/proc` neste host; mascarar o Docker data-root em segundo mount impede leitura **direta** desse diretório. Resultado com `--user 0`, `--network=none`, `--cap-drop=ALL`, `--read-only`, `--pull=never`, `--rm`, bind **read-only** de `/` para `/host` com `bind-recursive=disabled`:

| Caminho no container | Sem cobertura do data-root | Com `tmpfs /host/var/lib/docker` |
| --- | --- | --- |
| `/host/run/docker.sock` | ausente; `FileNotFoundError` | ausente; `FileNotFoundError` |
| `/host/var/run/docker.sock` | ausente; `FileNotFoundError` | ausente; `FileNotFoundError` |
| `/host/proc/1/root/run/docker.sock` | ausente; `FileNotFoundError` | ausente; `FileNotFoundError` |
| `/host/var/lib/docker/containers` | **visível** (Docker data-root neste filesystem raiz) | ausente |

Reprodução do segundo caso (probes de paths, sem ler conteúdos ou escrever no host):

```sh
docker run --rm --pull=never --network=none --cap-drop=ALL \
  --security-opt=no-new-privileges --read-only --user 0 \
  --mount type=bind,src=/,dst=/host,readonly,bind-recursive=disabled \
  --tmpfs /host/var/lib/docker:rw,noexec,nosuid,nodev,mode=0700 \
  --entrypoint python percival-weather-mcp:audit -c '
import os
for path in ("/host/run/docker.sock", "/host/var/run/docker.sock",
             "/host/proc/1/root/run/docker.sock", "/host/var/lib/docker/containers"):
    print(path, os.path.exists(path))'
```

**Prova local separada de loopback:** um container efêmero sem socket, com servidor Python em `127.0.0.1:18472`, foi acessado por outro com `--network container:<id>`. O segundo recebeu HTTP 501 (handler de teste sem implementação de GET: conectividade confirmada) e `/run/docker.sock` estava ausente. O primeiro foi parado/removido por `trap`; isso prova compartilhamento do namespace sem compartilhar os mounts, **não** autenticação do futuro broker ou semântica real do Compose. A referência [Compose `network_mode: service:`](https://docs.docker.com/reference/compose-file/services/#network_mode) cobre a forma prevista; a [documentação do bind recursivo](https://docs.docker.com/engine/storage/bind-mounts/#recursive-mounts) confirma que `disabled` omite submounts, não caminhos comuns do filesystem raiz.

**Topologia candidata do VPS:** gateway em container com pasta absoluta `.percival` do host ligada a `/home/nanobot/.nanobot` (path interno atual), broker Python em container separado com `network_mode: service:nanobot-gateway` e único mount do socket Docker. Broker ouve em `127.0.0.1` no namespace compartilhado, sem porta publicada; UID dedicado recebe GID numérico do socket do VPS. O antigo systemd host não será o deploy canônico. Não existem broker, imagem do broker, configuração Compose correspondente nem ensaio no VPS hoje. Docker local ainda é Client/Server 29.7.2, não 27.x.

**Por que não declarar isolamento total:** Docker data-root em `/var/lib/docker` é path normal do rootfs e não some sem cobertura; o path real no VPS pode ser outro. A pasta `.percival` e o token também precisam de cobertura, inclusive possíveis backing stores/aliases. Acesso R/W ao resto do host pode alterar arquivos que levem a escalada indireta mesmo quando o socket direto está ausente. Além disso, o gateway e a exec tool podem atingir o loopback do broker; `nanobot/agent/tools/sandbox.py` mascara o diretório de config no bwrap, mas **não** desabilita rede, e sandbox é opcional (`ExecToolConfig.sandbox` default vazio). Proteção por token deve ser testada contra shell, sem assumir que um segredo legível pelo gateway é inacessível ao processo de exec. B16 segue com broker separado e gateway sem socket, mas sua promessa de que exec não ganha API equivalente **não foi provada**. Não executar testes destrutivos de escalada; demonstrar caminhos, medir impacto e pedir aceite explícito do risco residual.

**Gate atualizado:** B23 resolve a decisão de escopo; F0 ainda depende de inventário real do VPS (volumes, path `.percival`, aliases do Docker, rede, UID/GID, versão 27.x e persistência) e aceitação da topologia. F1 deve provar em ambiente descartável um mount **R/W** para arquivos comuns, negativas de acesso direto ao daemon a partir dos três componentes, e o alcance indireto do broker; falha de uma exclusão direta bloqueia o perfil default. Se o custo de proteger acesso indireto for proibitivo, levar risco/custo e alternativa ao operador para aceite deliberado antes de deploy, sem renomear o teste local de “isolamento completo”.

## 7.5. Revisão de código F0 (2026-10-07, **após** B24)

Após o fechamento do gate, foi feita uma revisão completa dos scripts
novos.  As correções aplicadas:

- **`percival-vps-inventory.sh`** — três campos JSON embutiam
  saída multi-linha sem escape (`host_mount_at_socket`, `submounts`,
  `proxy_containers`), produzindo JSON inválido.  Agora achatam
  newlines/tabs para uma única linha; o JSON passa no parser
  `python3 -c 'import json,sys; json.load(sys.stdin)'`.
- **`percival_mcp_broker_f0.py`** — três correções de
  segurança/robustez:
  1. **Validação de imagem** — `container_image` é verificado contra
     a gramática de referência Docker (alphanumeric + `._-/:@`, sem
     iniciar com `-`, sem ser nenhum flag conhecido) **e** o
     `sha256:...` deve ter 64 caracteres hexadecimais.  Sem isso,
     um caller poderia passar `container_image = "--privileged"`
     (ou `-v`, `--cap-add`, etc.) e o `docker run` do broker
     interpretaria como flag, sobrescrevendo `--cap-drop=ALL` e
     `--security-opt=no-new-privileges` do próprio broker.
  2. **Token comparison** — `==` substituído por
     `hmac.compare_digest` (constant-time), alinhando com o resto
     do projeto.
  3. **Política de mount mais rigorosa** — `src=...` e `dst=...`
     extraídos da long syntax são comparados byte-a-byte com a
     lista de paths protegidos.
- **`percival-f0-validate.sh`** — `trap` final também remove a
  imagem `percival-f0-broker:dev` (antes ficava órfã).
- **`scripts/percival_gateway_probe_f0.py`** — removido por ser
  dead code (nenhum script nem teste o importava; o validate
  embute seus próprios probes Python via heredoc).

**Reexecução do `percival-f0-validate.sh`:** 11 asserts verdes
(incluindo as novas validações de imagem; `alpine:3.20` e
`percival-weather-mcp:audit` passam, `--privileged` e `-v` são
rejeitados com HTTP 400 e mensagem `container_image '...' is
not a valid image reference`).  `ruff check` passa nos scripts
novos; `git diff --check` limpo.

## 7. Disposable env (F0, F1 do plano) — execução local

Esta seção registra a rodada que fecha o entregável F0 local do plano: um
ambiente descartável com gateway e sidecar broker Python compartilhando
namespace de rede, prova de R/W, exclusões e gate de token.  O desenho
segue o plano v1.2 e B23; o broker é o protótipo mínimo, não o produto.
Scripts versionados no repositório e reexecutáveis:

- `scripts/percival-f0-validate.sh` — orquestra containers, aplica as
  assertivas e imprime um sumário `ok/FAIL`.  Constrói uma imagem
  `percival-f0-broker:dev` no diretório temporário e a remove no
  `trap` final; nenhuma alteração persiste fora do diretório de
  build.
- `scripts/percival-vps-inventory.sh` — coleta, em JSON válido no
  stdout, o inventário que F0 exige do VPS real (Client/Server,
  data-root, socket e GID, submounts/aliases, candidato `.percival`,
  paths sensíveis e segredos em disco).  Idempotente e read-only.
- `scripts/percival_mcp_broker_f0.py` — broker mínimo com auth por
  token (`hmac.compare_digest`), validação rigorosa de imagem
  (rejeita `--privileged`, `-v`, `alpine` sem tag e strings arbitrárias
  que docker interpretaria como flag) e endpoints tipados
  `/v1/ping`, `/v1/run` com política de mount/command.

### 7.1. Resultados do `percival-f0-validate.sh` no host de desenvolvimento

| # | Verificação | Esperado | Observado |
| --- | --- | --- | --- |
| A1 | bind-recursive=enabled expõe `/host/run/docker.sock` (controle negativo) | presente | presente |
| A2 | bind-recursive=disabled esconde `/host/run`, `/host/var/run`, `/host/proc/.../run` | ausente | ausente; `/host/var/lib/docker/containers` continua visível |
| A3 | tmpfs sobre `/host/var/lib/docker` esconde o data-root | ausente | ausente |
| A4 | container MCP grava arquivo de teste em `/host/tmp` | sucesso | sucesso |
| A5 | custom mount `--mount type=bind,src=/var/run,dst=/host/var/run` reintroduz o socket sem filtro do broker | reintroduz | reintroduz |
| B1 | broker rejeita `/v1/ping` sem token; aceita com token; gateway não tem `/var/run/docker.sock` | 401/200/ausente | 401/200/ausente |
| B2 | exec tool em outro container que entra no mesmo namespace via `--network container:<gw>` não consegue chamar `/v1/run` sem token | 401 | 401 |
| B3 | com token, broker rejeita comando que referencia `/host/var/run` | 400 | 400 |
| B3 | com token, broker rejeita mount com `src=/var/run/docker.sock` (long syntax) | 400 | 400 |

A linha A5 **confirma** que a proteção passiva do mount (sem o filtro do
broker) é insuficiente: o container MCP pode solicitar `type=bind,src=/var/run,dst=/host/var/run`
e abrir caminho para o socket.  O gate de token e a checagem do
`/v1/run` no broker (B3) são o que mantém a exclusão; sem o broker, a
fronteira se desfaz.  B1/B2 mostram que o gateway (e qualquer processo
no mesmo namespace) **não** pode chamar a API broker sem o token e
**não** tem o socket diretamente; B1 também confirma que o gateway
recebe 200 ao pingar o broker, o que é necessário para a operação
normal.

### 7.2. Achados e ressalvas

- **Bind recursivo confirmado como via única do socket neste host.**
  `--mount src=/ dst=/host bind-recursive=enabled` entrega
  `/host/run/docker.sock`; `bind-recursive=disabled` o esconde, mas
  deixa o data-root visível.  A política precisa dos dois mecanismos:
  `bind-recursive=disabled` **mais** tmpfs/Mount sobre o data-root
  descoberto em runtime.
- **Custom mounts podem reesconder o socket.**  O broker deve, em todo
  `/v1/run`, decompor o mount em `src`/`dst` e recusar caminhos
  protegidos — não basta validar `/host` no contrato.  A prova A5 + B3
  é o teste de regressão para isto.
- **Exec no mesmo namespace consegue falar com o broker.**  O gate de
  token é o que separa; um segredo em `runtime_data_dir/mcp-docker/operator.json`
  deve ser legível apenas pelo gateway e revogável sem reinício (B18).
  O presente protótipo do broker não mede rotação nem expiração, e
  não foi exercitado em um host onde o gateway seja um processo
  executando como root, como será no Compose real.
- **Loopback do namespace não é segredo.**  Qualquer container
  adicional atachado ao `network_mode: service:nanobot-gateway` chega
  ao broker na mesma `127.0.0.1`.  A autenticação é o único limite.
  O exec tool do gateway herda esse mesmo limite.
- **Docker local 29.7.2, não 27.x.**  O bind-recursive=disabled
  testado aqui é de Docker 29.7; em 27.x a semântica é a mesma segundo
  a [documentação de bind recursivo](https://docs.docker.com/engine/storage/bind-mounts/#recursive-mounts),
  mas a decisão de deployment no VPS continua pendente até o
  inventário confirmar Client/Server 27.x.

### 7.3. O que **ainda** falta para o gate F0 fechar

- **Inventário real do VPS.**  Rodar `scripts/percival-vps-inventory.sh`
  no VPS e anexar o JSON ao relatório F0.  Esse inventário confirma
  data-root, socket/GID numérico, presença/ausência de aliases e
  reverse proxy, e o caminho candidato para `.percival`.
- **Aceite do operador sobre o risco residual medido.**  Mesmo com
  o disposable env verde, o risco indireto (R/W no restante do host,
  token lido pelo processo gateway) **persiste**.  O operador decide
  se o perfil `bind-recursive=disabled` + tmpfs no data-root + tmpfs
  em `.percival` + filtros server-side do broker é aceitável para o
  deploy no VPS, ou se quer relaxar (ex.: perfis mais restritos para
  alguns MCPs) ou endurecer (ex.: user namespace, rootless).
- **Engine 27.x e permissões do daemon.**  A versão e o suporte de
  longo prazo de 27.x devem ser validados no daemon do VPS, e o GID
  do socket lido em runtime; o `docker-broker` herdado de B22 já não
  é deployment canônico.
- **Persistência `.percival`.**  O script de migração
  `~/.nanobot → /srv/percival/.percival` ainda não foi escrito;
  pertence a F5, mas precisa de smoke após recriação do gateway
  (capability `restore` não pode perder `config.json`/audit).
- **F1 ainda não foi iniciada.**  O disposable env prova a topologia
  **e o filtro do broker**, mas F1 (B19/B20/B22) precisa das duas
  fixtures (weather + osm) construídas por SHA, com o segundo digest
  real para o ensaio de update e a medição de cold start/latência.

### 7.4. Estado final do gate F0

- **F0 fechado em 2026-10-07 via B24.**  Decisão registrada em
  `.positronic/PROJECT.md`: o operador não tem VPS ativa para o
  inventário neste momento, então Client/Server 27.x, GID do socket
  no VPS e candidato `.percival` permanecem pendentes de execução
  futura; aceita formalmente o risco **indireto** descrito em §7.2
  (R/W no restante do host e leitura do token do gateway pelo
  exec tool).
- **Consequência para F1/F2/F3/F4:** podem começar em ambiente
  descartável **local** — o desenho compõe exatamente as exclusões
  e o gate de token medidos em §7.1.
- **Consequência para F5/deploy canônico:** o operador precisa (i) rodar
  `scripts/percival-vps-inventory.sh > vps-inventory.json` no VPS e
  anexar o JSON a este relatório, (ii) reexecutar o validate no
  VPS, e (iii) emitir nova aceitação formal do risco medido no
  protótipo antes de tag, publicação ou release.  Divergências
  relevantes (GID diferente de 966, data-root não-canônico, ausência
  de `~/.nanobot`, portas já publicadas) exigem nova decisão de
  produto, não fallback silencioso.
- **Ressalva explícita:** esta aceitação não equivale a isolamento
  total.  O mount R/W ao host, a credencial legível pelo gateway e o
  token compartilhado no namespace continuam sendo vetores reais;
  qualquer regressão aqui é motivo para reabrir B14/B16/B22, não
  para "tudo bem, aceito".