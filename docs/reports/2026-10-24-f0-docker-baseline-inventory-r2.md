# F0 (reexecução) — baseline e inventário Docker do Percival

- **Data da observação:** 2026-10-24 (America/Sao_Paulo); janela 22:10–22:35.
- **Estado:** inventário read-only capturado e decisões D-1, D-2, D-3, D-5, D-6 e
  item 7 confirmadas pelo operador em 2026-10-24 (adendo da ADR); **gate F0
  (reexecução) fechado em 2026-10-24** por assinatura do operador, com D-4
  (rotação de credencial exposta) encerrada por aceitação formal do risco residual
  — ver [registro de fechamento](2026-10-24-f0-closure-record.md). Nenhuma mutação
  foi executada.
- **Plano:** [padronização Docker do Percival](../plans/2026-10-09-docker-standardization-refactor-plan.md),
  fase F0 (§3) e decisões §2.
- **Precedente:** [inventário F0 de 2026-10-09](2026-10-09-f0-docker-baseline-inventory.md)
  (histórico, gate então concluído) e
  [ADR de padronização](../Decisions/2026-10-09-docker-standardization.md),
  aditada pela [ADR I1](../Decisions/2026-10-23-open-iac-contracts.md).

## 1. Por que reexecutar F0

O plano determina, na revisão v1.1, que o snapshot de 2026-10-09 **não seja usado
como inventário atual** e que os checkouts sejam reverificados antes de novas edições.
Entre aquele baseline e hoje houve: ADR I1 (identidades/versão `0.1.0`), I2 (runtime 1
e metadata core), cutover F6 local dos MCPs, fechamento D8–D12, substituição do core
(gateway e broker) e dozens de builds candidatos novos. Este documento é a
reexecução read-only de F0 sobre o estado de 2026-10-24: substitui o snapshot inicial
como referência corrente de inventário e **não** reabre nem fecha F1–F8.

## 2. Escopo e método

- InSPECIONADO: Engine/Compose, 16 containers, 94 imagens (53 tags `percival-*`,
  2 `nanobot-*`, 5 `positronic-*`, bases e fixtures), 20 volumes, 8 redes,
  `~/.nanobot/config.json`, `~/.positronic/mcp/{registry.json,servers/*.json}`,
  `~/.nanobot/mcp-docker/{audit.jsonl,transitions/*.json,backups/*}`,
  `~/.positronic/mcp/{transitions,backups,executions}` e os oito repositórios.
- LIDO: metadados OCI, `Config.Image`, labels, healthcheck efetivo, mounts, ports,
  init, TTY/stdin, política de restart, `CapAdd`/privileged/read-only rootfs e
  referências de imagem em configs.
- NÃO LIDO/REGISTRADO: valores de `Config.Env`, conteúdo de arquivos de credencial,
  tokens de broker/operador. Chaves de env aparecem apenas por nome.
- NÃO EXECUTADO: pull, push, build, `docker compose up/down`, criação/remoção de
  container ou imagem, alteração de config, `prune`. Nenhuma imagem antiga foi
  removida.
- Snapshot local pontual — não é série temporal nem prova de comportamento.

## 3. Host/runtime observado

| item | valor |
| --- | --- |
| Docker Engine | 29.9.2, linux/amd64 |
| Docker Compose | 5.6.1 (label `com.docker.compose.version`) |
| containers | 16 (15 em execução; `d7host-noinit` exited) |
| imagens | 94 IDs visíveis via `docker images -q` (10 referenciadas por container ativo), 9 dangling; `docker system df` reporta 103 no total (inclui camadas/intermediários), 33,12 GB |
| reclaimable | imagens 26,93 GB; build cache 139,1 GB de 185,7 GB; volumes 2,498 GB de 20 (1 ativo) |
| volumes nomeados | `percival-state` (2026-10-11), `positronic-percival-registry` (2026-09-30), `trivy-f3-cache` (2026-10-10) — **nenhum montado por container ativo** |
| stacks Compose | apenas o projeto `nanobot` (gateway + broker) |

## 4. Worktrees e versão declarada

Todos os oito repositórios estão **limpos**, em `main` e sincronizados com
`origin/main`. Nenhuma alteração local pendente a preservar.

| repositório | HEAD | versão `pyproject.toml` | estado |
| --- | --- | --- | --- |
| Percival `~/Projects/nanobot` | `ff7a4dda` | `0.1.0` (name ainda `nanobot-ai`) | limpo, `main...origin/main` |
| Notes | `c104735` | `0.1.5` | limpo |
| AgentMail | `cd55a2f` | `0.4.0` | limpo |
| Weather | `437a41c` | `0.9.0` | limpo |
| Khan Calendar | `e8c5d8c` | `0.4.0` | limpo |
| OSM | `04d4399` | `0.5.0` | limpo |
| Deep Research | `af3b23b` | `3.0.1` | limpo |
| consumidor Positronic `alternative-positronic` | `78f7598149` | TypeScript (sem `pyproject.toml`) | limpo |

`ff7a4dda` é o HEAD que assina/arquiva o plano de padronização Docker
(`docs(d12): sign closure and archive docker plan`).

## 5. Inventário de imagens

### 5.1 Imagem ativa (pin real) por serviço

`image ID` é a identidade observada. O Engine devolve, para imagens locais, um
`RepoDigest` **igual ao próprio image ID** — isso é artefato de tag local, **não**
é digest de manifest remoto nem prova de publicação. Nenhum digest OCI remoto
existe hoje neste host.

| serviço | pin ativo (image ID) | tags legíveis do mesmo ID | OCI version / revision | observações |
| --- | --- | --- | --- | --- |
| Notes | `ef4082ef1390` | `percival-notes-mcp:0.1.5-f7-test-vaultpath-0012523b9a96` | 0.1.5 / `ab0f07d-f7-vaultpath-…` | `io.percival.build.phase=f3`, `worktree=dirty`; User `65532:65532` |
| AgentMail | `e104ac754951` | `percival-agentmail-mcp:0.4.0-f7-test-keyfile-4ff291ec7a33` | 0.4.0 / `d2d6458-f7-keyfile-…` | fase f3, worktree dirty; User `app` |
| Weather | `e75fdd4abc8a` | `percival-weather-mcp:0.9.0-94c7fde-f3-c0ae6523cf2f` | 0.9.0 / `94c7fdeffdb0` | fase f3, worktree dirty; entrypoint `docker-entrypoint.sh`, `Cmd=stdio` |
| Khan Calendar | `55cd5a038d22` | `percival-khan-calendar:0.4.0-d8d4122-f3-2500221a747e` | 0.4.0 / `d8d412255c4b` | fase f3, worktree dirty; User `app` |
| OSM | `67f8ada63989` | `percival-osm:0.5.0-311a49d-f3-c71c69ddb5b2` | 0.5.0 / `311a49da1f05` | fase f3, worktree dirty; entrypoint **tini** + entrypoint.sh; `Healthcheck.Test=["NONE"]` |
| Deep Research | `265891c14514` | `percival-deep-research:3.0.1-9e8272b-f3-608be1420abd` | 3.0.1 / `9e8272be8dd7` | fase f3, worktree dirty; entrypoint **tini** + binário; `ExposedPorts 8000/tcp` |
| Gateway (em execução) | `d128e0ca1dee` | `nanobot-nanobot-gateway:latest`, `percival-gateway:0.1.0-40d8eb9-d11-2e4d276142d8` | 0.1.0 / `40d8eb99e5ef` | fase `d11-skill-closure`, **worktree dirty** (diff `2e4d2761…`); `Config.User=root` (compose aplica `1000:1000`) |
| Broker (em execução) | `6ea63b38852c` | `percival-mcp-broker:local`, `percival-mcp-broker:0.3.5-29a482c-d11-probe-20261024` | **0.3.5** / `29a482cec885` | **versão 0.3.5, não 0.1.0** (ver A1); User `65532:65532`; `Healthcheck=null` (o healthcheck vem do Compose) |

### 5.2 Candidatos locais adicionais (não pins)

- Core: `percival-gateway` com 15 tags (8 candidatas `0.1.0-<sha>`, `0.3.5-29a482c-d11-builtin-20261024`, `rollback-d11-20261024`, `rollback-d11-pre-skill-20261025`, `d6-forky`, `d6-nopip-build`, `d6-nopip-test`, `forky-probe`) → 14 IDs distintos; `percival-mcp-broker` com 7 tags → 6 IDs distintos.
- MCPs: 4–6 tags por serviço, sendo `<semver>-<shortsha>` de checkout limpo
  (ex.: `percival-notes-mcp:0.1.5-c104735` → `3abd363f5a35`, `revision=c104735…`,
  igual ao HEAD atual do repositório) coexistindo com o candidato `f3`/dirty que está
  **em execução**.
- Fixture/ensaio: `percival-i2-gateway:ses-e96f9440`, `percival-i2-broker:ses-e96f9440`,
  `percival-i2-old-broker:eb4e3555`, `percival-remote-ssh-fixture:10.6p1`,
  `positronic-mcp-local-smoke-f3-0-1:2026-10-20T15-21-35-376Z`, `pinprobe:{local,full,diag,libs}`,
  `d8-python312-forky-proto:latest`, `positronic:dev-*` (5).
- Bases/ferramentas sem classificação de descarte neste inventário: `ghcr.io/astral-sh/uv` (7 IDs),
  `debian` (trixie/forky), `python` (4), `docker:27.5.1-dind`, `docker:29.9.0-cli-alpine3.24`,
  `alpine` (2), `node:24-bookworm-slim`, `archlinux`, `registry:2`, `aquasec/trivy` (2),
  `anchore/syft`.

## 6. Inventário de containers

### 6.1 Core (projeto Compose `nanobot`)

| container | ID | imagem | estado | contrato observado |
| --- | --- | --- | --- | --- |
| `nanobot-nanobot-gateway-1` | `5edf4db07b41` | `nanobot-nanobot-gateway` (`d128e0ca1dee`) | Up **healthy**, 0 restarts | User `1000:1000`; `init: true`; `no-new-privileges`; caps CHOWN/KILL/SETGID/SETUID; bind `~/.nanobot` → `/home/nanobot/.nanobot` **rw**; ports **loopback** `127.0.0.1:8765` e `127.0.0.1:18790`; healthcheck HTTP em `127.0.0.1:18790/health` (intervalo 30 s) |
| `nanobot-percival-mcp-broker-1` | `9b122c33db70` | `percival-mcp-broker:local` (`6ea63b38852c`) | Up **healthy**, 0 restarts | User `65532:65532`; `init: true`; `read_only: true`; `cap_drop: ALL`; `no-new-privileges`; `network_mode: service:nanobot-gateway`; socket Docker **rw**; `/` → `/host-inventory` **ro**; `/proc/1/mountinfo` ro; token do broker ro; healthcheck `python3 -m nanobot.mcp_docker.probe` (60 s / start 45 s) |

O gateway **não** tem socket Docker; o broker é o único serviço com daemon — invariante
B16/B23 preservada. A API (`nanobot-api`, profile `api`) **não está em execução**;
`~/.nanobot/config.json` tem `api.apiKey = ""` (vazio) e `api.port 8900`.

### 6.2 MCPs — Percival broker (6) e Positronic (6)

Doze containers, exatamente **um por servidor por gestor**; a duplicação registrada
no F0 de 2026-10-09 (dois containers aleatórios por servidor) **não se reproduz**.

| servidor | container broker | container Positronic | transporte | init | healthcheck | ports |
| --- | --- | --- | --- | --- | --- | --- |
| agentmail | `percival-mcp-agentmail` (`a663a4cb4006`) | `positronic-mcp-agentmail-f5505767694f` | stdio (`OpenStdin=true`, `Tty=false`) | broker: tini na imagem; positronic: `Init=true` | nenhum | nenhum |
| weather | `percival-mcp-weather` (`8738c040527c`) | `positronic-mcp-weather-352b1ee02fa8` | stdio | idem | nenhum | nenhum |
| osm | `percival-mcp-osm` (`c99bee5c5184`) | `positronic-mcp-osm-8b695ffe7faf` | stdio | broker: tini na imagem; positronic: **`Init=true` + tini na imagem** | `Test=["NONE"]` (correto) | nenhum |
| deep-research | `percival-mcp-deep-research` (`9c30f1341b50`) | `positronic-mcp-deep-research-3e6ddb382950` | stdio | broker: tini na imagem; positronic: **`Init=true` + tini na imagem** | nenhum | nenhum |
| notes | `percival-mcp-notes` (`aa4b3cc0079b`) | `positronic-mcp-notes-808c413688c6` | stdio | broker: sem init na imagem; positronic: `Init=true` | nenhum | nenhum |
| khan-calendar | `percival-mcp-khan-calendar` (`de4a1a4e46d9`) | `positronic-mcp-khan-calendar-2d7970903fe2` | stdio | broker: sem init; positronic: `Init=true` | nenhum | nenhum |

Estado HTTP: `ExposedPorts 8000/tcp` (deep-research) e `8080/tcp` (weather, osm) são
metadados de **imagem**; nenhum container MCP em execução publica porta, e o
healthcheck HTTP foi removido do caminho stdio — invariante F1 preservada.

### 6.3 Containers residuais (fixtures)

| container | ID | imagem | estado | observação |
| --- | --- | --- | --- | --- |
| `d6-nopip` | `282c794fd8ca` | `percival-gateway:0.1.0-b49dd8b` (`84e4c8f13ca4`) | Up há ~10 h | `User=root`, `Cmd=sleep infinity`, sem rede/healthcheck — **fixture viva**, não é serviço |
| `d7host-noinit` | `72fa0b0acac2` | `docker:27.5.1-dind` (`aa3df78ecf32`) | Exited (0) há ~22 h | fixture de Engine; volume `455c65df…` órfão |

### 6.4 Montagens e superfície de host (dados e persistência)

| consumer | mounts | leitura/escrita | observação |
| --- | --- | --- | --- |
| gateway | `~/.nanobot` → `/home/nanobot/.nanobot` | rw | estado único do core (config, journal, sessions, logs, workspace) |
| broker | `/` → `/host-inventory`; `/proc/1/mountinfo`; token; `docker.sock` | ro, ro, ro, **rw** | inventário do host + daemon; surface aprovada B14–B25 |
| MCPs do broker (deep-research, weather, osm, agentmail) | `/`→`/host`, `/boot`, `/home`, `/tmp`, `/var/log`, `/var/cache/pacman/pkg` | **rw** | surface ampla de host, conforme política B14 |
| MCPs do broker (notes, khan) | `~/.local/share/percival-test-mcp/{notes-vault,khan-calendar}` | rw | workspace de teste local |
| MCPs Positronic | notes → `~/.positronic-reports/f3-0-1-notes-vault-20261020T172539Z` (`/vault`); khan → `~/.positronic-reports/f3-0-1-khan-workspace-20261020T172539Z` (`/data`); agentmail/deep-research → `~/.positronic/mcp/secrets/*.env` (`/app/.env`, ro) | rw / rw / ro | **dados do mesmo servidor vivem em dois lugares distintos conforme o gestor** |

Os diretórios `~/.positronic-reports/f3-0-1-*` são, hoje, o local de dados de uso real
de Notes e Khan no gestor Positronic — herança de fixture F3/D6, não um caminho de
estado nomeado por finalidade.

## 7. Consumidores e pin por `server_id`

### 7.1 Percival (broker)

`~/.nanobot/config.json` → `tools.mcpDocker`: `schemaVersion 1`, `revision 18`,
`allowRemoteAdmin: true`, **6 servidores**, todos `source.type = local-image` com
`reference` = **image ID completo** (`sha256:…`), `active: true`, `state: running`.
Nenhum `pull` implícito; o pin por ID é a autoridade.

| `server_id` | pin (image ID) | tools | container broker | label `percival.mcp-docker.instance-id` |
| --- | --- | --- | --- | --- |
| `agentmail` | `e104ac754951…` | 24 | `percival-mcp-agentmail` | `040d382a-3be9-4e3a-a2a5-9921633ad1d3` |
| `weather` | `e75fdd4abc8a…` | 9 | `percival-mcp-weather` | `7ee291aa-b3f8-4a9a-87db-38a93495f56e` |
| `osm` | `67f8ada63989…` | 37 | `percival-mcp-osm` | `1b2998fe-066d-47db-85cc-2180db8ee915` |
| `deep-research` | `265891c14514…` | 5 | `percival-mcp-deep-research` | `effd3c9f-76a1-47a8-9b04-5179f9167af6` |
| `notes` | `ef4082ef1390…` | 12 | `percival-mcp-notes` | `adee065a-cb8f-4f6c-a2b2-da93be09b08c` |
| `khan-calendar` | `55cd5a038d22…` | 12 | `percival-mcp-khan-calendar` | `68fae821-bbb5-417b-bb80-30aa654b9363` |

### 7.2 Positronic

`~/.positronic/mcp/registry.json`: `schemaVersion 2`, **6 servidores**, todos
`scope: global`, `activated: true`, `allowedProjects: []`, `transport: stdio`, com
`source.type = local-image` e `source.imageId` = **o mesmo image ID** do broker.
Configuração por servidor em `~/.positronic/mcp/servers/<id>.json` (mounts, rede,
`allowedTools`, `env`).

| servidor | pin (image ID) | revision | allowlist de tools | container |
| --- | --- | --- | --- | --- |
| agentmail | `e104ac754951…` | 16 | 5 | `positronic-mcp-agentmail-f5505767694f` |
| khan-calendar | `55cd5a038d22…` | 10 | 12 | `positronic-mcp-khan-calendar-2d7970903fe2` |
| deep-research | `265891c14514…` | 16 | 1 | `positronic-mcp-deep-research-3e6ddb382950` |
| notes | `ef4082ef1390…` | 19 | 2 | `positronic-mcp-notes-808c413688c6` |
| weather | `e75fdd4abc8a…` | 4 | 9 | `positronic-mcp-weather-352b1ee02fa8` |
| osm | `67f8ada63989…` | 4 | 15 | `positronic-mcp-osm-8b695ffe7faf` |

**Achado estrutural:** os dois gestores compartilham **os mesmos seis image IDs**.
Um único conteúdo de imagem serve a dois consumidores com contratos de segurança
diferentes (surface de host do broker vs. rede `none`/montagem restrita no
Positronic). Qualquer remoção de imagem, re-tag ou "limpeza" por ID atinge os dois
gestores ao mesmo tempo — a regra de cleanup do gate F6 ("lista explícita por Image
ID após confirmar zero referências") precisa checar **as duas** fontes de pin.

### 7.3 Execução Compose manual

Nenhum container MCP ativo é gerenciado por Compose: os 12 têm
`com.docker.compose.project` vazio e são Launcher (`docker start --attach --interactive`)
sob demanda — broker (via containerd) e Positronic (via `opencode serve`, PID 1049).
A execução manual por Compose permanece disponível como fixture documentada em cada
repositório MCP, mas **não há consumidor Compose MCP ativo** neste host.

### 7.4 Rastreabilidade dos containers até a imagem

`Config.Image` resolve o pin de forma útil; os labels `com.docker.compose.image` do
gateway e do broker apontam para IDs **que não existem mais** (`fc4b6dc270b8…`,
`2a869b209237…`) porque os containers foram substituídos fora de `compose up`
(label `com.docker.compose.replace` presente). **Proveniência de runtime deve ser lida
de `.Image`**, não do label de Compose.

## 8. Referências de config, rollback e compatibilidade de aliases

### 8.1 Fontes de referência a imagens (verificadas)

| fonte | conteúdo | status |
| --- | --- | --- |
| `~/.nanobot/config.json` (`tools.mcpDocker.servers`) | 6 pins por image ID | **autoridade do broker** |
| `~/.positronic/mcp/registry.json` | 6 pins por image ID | **autoridade do Positronic** |
| `~/.nanobot/mcp-docker/transitions/<server>.json` | `before.source.reference` = image ID anterior | pins anteriores **inexistentes** no Engine (ver A3) |
| `~/.nanobot/mcp-docker/audit.jsonl` | trilha install/update-image até 2026-10-10, revisão 18 | coincide com `revision 18` da config; sem eventos posteriores |
| `~/.nanobot/mcp-docker/backups/*/manifest.json` | manifesto de backup por transição | guardam `before` + configuração (com segredos em claro, ver A4) |
| `~/.positronic/mcp/transitions/*.json` | 6 transições `committed` (2026-10-20), `backup` + `result.server` | guardam o pin anterior (registry `source.imageId`) |
| `~/.positronic/mcp/backups/<ts>-<server>-*/` | cópias de `registry.json` e `servers/*.json` por transição | rollback de **configuração**, não de imagem |
| `~/Projects/nanobot/docker-compose*.yml` + `.env` | build do gateway (`VERSION`, `GIT_SHA`) e `image: percival-mcp-broker:local` no override | override local **descartável** (ver A2) |
| `~/Projects/nanobot/.env` | `PERCIVAL_STATE_HOST_PATH`, `PERCIVAL_BROKER_TOKEN_HOST_PATH`, `PERCIVAL_BROKER_TOKEN_GID`, `PERCIVAL_DOCKER_SOCKET_GID`, `PERCIVAL_DISPOSABLE_ENGINE29`, `PERCIVAL_IMAGE_REVISION`, `PERCIVAL_GATEWAY_CONTAINER_NAME`, `NANOBOT_CHANNELS` | sem segredos; `PERCIVAL_IMAGE_REVISION` é a revisão embutida no build |

Não há referência em config a tags antigas (`positronic/*:0.1.5-local`,
`nanobot-nanobot-gateway:latest` etc.) nos seis repositórios MCP: os caminhos de
configuração foram migrados para pin por image ID.

### 8.2 Caminho de rollback (descrito, não ensaiado)

1. **Sem mudança de imagem**: reverter `source.reference` / `source.imageId` no
   registro correspondente (broker ou Positronic) e recriar o container. O estado
   persistido é preservado por volume/bind; nada é reconstruído.
2. **Com imagem anterior ausente**: os seis IDs `before` do broker **não existem**
   mais localmente. O caminho aplicável é **rebuild a partir da revisão registrada**:
   as revisões `ab0f07d` (notes), `d2d6458` (agentmail), `94c7fde` (weather),
   `d8d4122` (khan), `311a49d` (osm), `9e8272b` (deep-research) e `29a482c` (core)
   **existem como commits** nos oito repositórios locais (verificado com
   `git cat-file -t`). O rebuild não é bit-idêntico ao original (bases, timestamps,
   caches), portanto o rollback é *funcional*, não *byte-idêntico*.
3. **Rollback do core**: `percival-gateway:rollback-d11-20261024` (`d06d8eedcc4e`,
   rev `29a482c`, 2026-10-11) e `percival-mcp-broker:rollback-d11-broker-before-fix`
   (`c6e370a5d56c`, rev `c63b8b68`, 2026-10-11) preservam o passo D11, **não** o
   cutover dos MCPs. O par atual (`d128e0ca1dee` / `6ea63b38852c`) tem
   `rollback-d11-pre-skill-20261025` = `ac62466dfd99` (gateway, rev `29a482c`,
   metadata 0.3.5) como vizinho do broker em execução.
4. **Configuração**: transições do broker e backups do Positronic guardam o estado
   anterior de config (não de imagem) e permitem reverter mounts/env/allowlist
   sem tocar no runtime.

### 8.3 Compatibilidade de aliases (mapeamento observado → padrão)

| alias legado observado | papel | destino no padrão |
| --- | --- | --- |
| `nanobot-nanobot-gateway:latest` | alias mutável do core | `percival-gateway:<semver>-<shortsha>` (+ alias `:dev` só para desenvolvimento) |
| `nanobot-nanobot-cli:latest` | imagem CLI (mesma base do gateway) | mesma imagem do gateway (runtime 1: CLI/API/gateway compartilham imagem) |
| `percival-mcp-broker:local` | **pin efetivo em execução**, mutável | `percival-mcp-broker:<semver>-<shortsha>` + `docker.io/pbeanlabs/percival-mcp-broker` (ADR I1) |
| `percival-<mcp>:<semver>-<shortsha>` | padrão já em uso | mantido (fonte da versão = `pyproject.toml`) |
| `percival-<mcp>:*-f3-<diff>` / `*-f7-test-*` / `:smoke` / `:local` / `:audit` | candidatos de worktree/smoke | sem papel de identidade; mantidos como rollback até decisão de retenção |
| `localhost:5000|5001/...` | registries de fixture | sem papel; já sem imagem referenciada |
| `positronic/<servidor>:<versão>-local` | aliases do gestor Positronic (2026-10-09) | não existem mais; pins passaram a ser image ID |

## 9. Labels de container em uso

| chave | broker Percival | Positronic | contrato F0/F2 |
| --- | --- | --- | --- |
| `percival.mcp-docker.owner` | `percival` | **ausente** | definido (`percival`/`positronic`) |
| `percival.mcp-docker.managed-by` | `percival-broker` | **ausente** | definido (`percival-broker`/gestor Positronic) |
| `percival.mcp-docker.instance-id` | UUID v4 por encarnação | **ausente** (há `io.positronic.run`, UUID v4 equivalente) | definido (UUID v4 novo a cada recreate) |
| `percival.mcp-docker.server-id` | presente (`server_id`) | **ausente** (há `io.positronic.server-name`) | preservado por compatibilidade |
| `io.positronic.managed` / `.run` / `.server` / `.server-name` / `.context` / `.home` | — | presentes | esquema próprio do gestor |

O contrato de labels de F2 está implementado **apenas no lado do broker**. O lado
Positronic usa um esquema próprio (`io.positronic.*`), o que impede um inventário
unificado por `owner`/`managed-by`/`instance-id` sem leitura específica por gestor.

## 10. Achados (ordenados por severidade)

**A1 — Versão de metadata do core divergente da fonte (alto).** O broker em execução
(`percival-mcp-broker:local`, `6ea63b38852c`) carrega `org.opencontainers.image.version
= 0.3.5` e `revision = 29a482c`, enquanto o gateway em execução carrega `0.1.0` /
`40d8eb9`, e o HEAD do repositório (`ff7a4dda`) declara `0.1.0`. O par core em
execução está, portanto, em **séries de versão diferentes**, e o broker contradiz a
fonte de versão única decidida na ADR I1 (§3). O inventário de 2026-10-09 já registrava
`0.3.5` como baseline herdado; a divergência segue sem correção no artefato em uso.

**A2 — Core em execução por tag mutável + override descartável (alto).** O broker é
iniciado com `image: percival-mcp-broker:local` via
`docker-compose.engine29-override.yml`, que também relaxa a verificação de Engine
(27.x) com `PERCIVAL_DISPOSABLE_ENGINE29=1` num host em **Engine 29.9.2**. O
arquivo se declara "NEVER use in a real deploy". Isto é coerente com um ambiente
local descartável, mas significa que o runtime local **não** está no contrato
aprovado (Engine 27.x + pin imutável) e não pode ser usado como evidência de
homologação.

**A3 — Rollback por transição do broker aponta para imagens inexistentes (médio).**
Os seis `before.source.reference` gravados em `transitions/*.json` não existem no
Engine. O rollback por transição é, hoje, um caminho morto; resta o rebuild a partir
da revisão (commits presentes) e as tags `rollback-d11-*` do core.

**A4 — Segredos de servidor MCP persistidos em claro (alto).**
`~/.nanobot/mcp-docker/transitions/{agentmail,deep-research}.json` e os manifestos
de backup correspondentes gravam **valores** de segredos (`kind: secret`) em JSON
legível, em `~/.nanobot/mcp-docker/`. Ao inventariar o baseline esses valores foram
expostos no output da sessão. **Recomendação: rotacionar a credencial do AgentMail e a
chave de inferência** e corrigir a gravação para referenciar segredo por nome/ID, não
valor. (O plano já registra rotação de credencial exposta em D1; esta evidência
confirma que a exposição não é só histórica.) Nenhum valor foi reproduzido neste
documento.

**A5 — Duplo init no caminho Positronic de OSM e Deep Research (médio).** Os
containers Positronic de `osm` e `deep-research` combinam `HostConfig.Init = true`
(docker-init) com **tini embutido na imagem** (`/usr/bin/tini -- …`), exatamente a
combinação que F1 proibiu ("escolher um único init"). Notes, Khan, AgentMail e
Weather usam apenas `Init=true`; o caminho do broker usa apenas tini da imagem
(`Init=null`). Os candidatos de checkout limpo já removeram o tini da imagem
(ex.: `percival-osm:0.5.0-04d4399`), o que elimina o duplo init quando promovidos.

**A6 — Artefatos em execução não vêm de checkout limpo (médio).** As seis imagens MCP
em execução carregam `io.percival.build.worktree = dirty` (candidatos F3 de
2026-10-10, revisões `ab0f07d`/`d2d6458`/`94c7fde`/`d8d4122`/`311a49d`/`9e8272b`),
~2 semanas atrás do HEAD dos repositórios. Candidatos derivados de HEAD **existem**
localmente (`<semver>-<shortsha>` com `revision` = HEAD) mas **não estão pinados por
nenhum gestor**. O gateway em execução também é `worktree=dirty` (`d11-skill-closure`).

**A7 — Fixação compartilhada entre os dois gestores (médio).** Ver §7.2: um image ID
serve ao broker e ao Positronic. Limpeza/re-tagging por ID tem efeito simultâneo nos
dois; qualquer lista de remoção precisa cruzar as duas fontes de pin.

**A8 — Dados do mesmo servidor em dois locais por gestor (médio).** Notes e Khan
mantêm vaults/workspaces em `~/.local/share/percival-test-mcp/` (broker) e em
`~/.positronic-reports/f3-0-1-*` (Positronic). São conjuntos de dados distintos,
embora o MCP e o `server_id` sejam os mesmos.

**A9 — Alias mutável no pin efetivo do core (médio).** `percival-mcp-broker:local` é
tag mutável usada como pin em execução; um rebuild sobrescreve a referência sem
alterar o pin por ID — o contrato "alias legível sincronizada, identidade imutável
como autoridade" está invertido apenas no caminho de *início* do container.

**A10 — Fixture viva fora de qualquer contrato (baixo).** `d6-nopip` roda como root
com `sleep infinity` há ~10 h, usando imagem de gateway; `d7host-noinit` (dind) está
exited com volume órfão; `pinprobe:*`, `percival-i2-*`, `d8-python312-forky-proto`
permanecem sem classificação de descarte. Nada foi removido neste inventário.

**A11 — Labels de container incompletas no gestor Positronic (baixo).** Ver §9.

**A12 — Rastreabilidade por label de Compose quebrada (baixo).** Ver §7.4.

**A13 — `api.apiKey` vazio (baixo, fail-closed).** A API do core exige chave
obrigatória; com `apiKey = ""` o profile `api` falha fechado. O serviço não está em
execução. Nenhuma exposição de porta 8900 observada.

**A14 — Sem digest OCI remoto (informativo).** Nenhuma imagem foi publicada; todo
`RepoDigest` local ecoa o image ID. A passagem a digest real é gate de I3/I5, fora
desta refatoração.

## 11. Decisões F0 — estado, confirmação de 2026-10-24 e pendências

| # | decisão (2026-10-09) | estado observado em 2026-10-24 | ação |
| --- | --- | --- | --- |
| 1 | repos `percival-<service>`, `percival-gateway`, `percival-mcp-broker`; tag imutável `<semver>-<shortsha>`; `:dev` só dev | **mantida e em uso**; ADR I1 fixa destino público `docker.io/pbeanlabs/percival-{gateway,mcp-broker}` e `percival-weather-mcp`/`percival-osm` | reconfirmar escopo do destino público (I3/I5) |
| 2 | registry local-only, sem push/pull/release | mantida localmente; ADR I1 adita o alvo (Docker Hub) sem autorizar execução | manter; publicação depende de I3/B13 |
| 3 | `linux/amd64` único alvo | **mantida**: todas as imagens de aplicação observadas são amd64; host amd64 | manter |
| 4 | rastrear `uv.lock` + instalação locked | mantida (F3); `uv.lock` presente nos seis MCPs | manter |
| 5 | `khal` pinado na imagem do Khan (12 tools) | mantida: `khal` presente no ambiente da imagem Khan em uso; allowlist de 12 tools no Positronic e 12 tools no broker | manter |
| 6 | API com `api_key` obrigatória, bind loopback; item 6 superado por I2 (API em profile `api`, runtime alternativo) | runtime 1 em execução: gateway em loopback `8765`/`18790`, API fora de execução, `apiKey` vazio | manter; preencher `api_key` apenas ao decidir usar o profile |
| 7 | labels `owner`, `managed-by`, `server_id`, `instance_id`; cada gestor rotula suas instâncias | implementadas no broker; **ausentes no Positronic** (esquema `io.positronic.*`) | **confirmado em 2026-10-24 (D-6)**: manter esquema duplo documentado; unificar fica como recomendação futura |

Além disso, a reexecução de F0 propõe registrar na ADR:

- **D-1** — versão do produto: `pyproject.toml` = 0.1.0 é a **única** fonte de
  verdade; o broker em execução com metadata 0.3.5 é um **desvio** a corrigir antes
  de qualquer claim de release (A1).
- **D-2** — runtime local: o override `docker-compose.engine29-override.yml` +
  `percival-mcp-broker:local` é explicitamente **não-homologado**; evidência de
  runtime local não vale como homologação de Engine 27.x nem de distribuição (A2, A9).
- **D-3** — rollback: caminho oficial é **rebuild por revisão registrada** (commits
  presentes), com rebuilds não bit-idênticos; o caminho por `transitions` só é válido
  se a imagem anterior existir localmente (A3, §8.2).
- **D-4** — segurança: **adiada pelo operador em 2026-10-24, sem prazo e sem dono**.
  A rotação de `AGENTMAIL_API_KEY` e da chave de inferência não será feita; o
  registro em claro nos arquivos de transição/backup permanece. Risco residual
  aceito de forma explícita: as chaves seguem válidas no disco e no histórico de
  sessão, e qualquer auditoria de imagem, publicação ou migração de estado
  voltará a lê-las. A mudança do **formato de gravação** (referenciar segredo por
  nome/ID em vez de gravar o valor) segue **sem decisão** e é independente da
  rotação (A4).
- **D-5** — init: **um** init por caminho; a promoção dos candidatos de checkout
  limpo remove o tini embutido e resolve o duplo init do Positronic em OSM e Deep
  Research (A5).
- **D-6** — labels: **esquema duplo documentado**. O broker mantém
  `percival.mcp-docker.*`; o gestor Positronic mantém `io.positronic.*`, com
  `io.positronic.run` como equivalente funcional de `instance-id`. Unificar fica
  como recomendação futura, fora do gate F0 (A11).

O operador confirmou D-1, D-2, D-3, D-5, D-6 e a decisão 7 (esquema duplo) em
2026-10-24; a formalização está no
[adendo da ADR](../Decisions/2026-10-09-docker-standardization.md). D-4 foi adiada
pelo operador.

## 12. Gate F0 (reexecução) — status

| critério do gate | status | evidência |
| --- | --- | --- |
| inventário com cada container/Image ID conhecido, dono/consumidor comprovado, pendências marcadas | **atendido** | §5, §6, §7; origem de todos os 16 containers e dos 8 pins comprovada por ID/labels/config |
| padrão de tag, labels, transporte/health, arch e lock strategy aprovados | **atendido com decisão**: tag/arch/lock mantidos; labels por esquema duplo documentado (D-6); core ainda em tag mutável, classificado como não-homologado (D-2) | §9, §11 |
| caminho de compatibilidade dos aliases antigos e rollback descrito | **descrito, não ensaiado** | §8.2, §8.3 |
| nenhuma imagem antiga removida neste gate | **atendido** | nenhuma mutação executada; contagens conferidas ao final da captura (16 containers, 94 IDs de imagem) e iguais às do início |

O gate **foi fechado** em 2026-10-24 por assinatura do operador
([registro de fechamento](2026-10-24-f0-closure-record.md)): D-1, D-2, D-3, D-5,
D-6 e o item 7 foram confirmados e formalizados no adendo da ADR, e D-4 foi
encerrada por **aceitação formal do risco residual** — a rotação das credenciais
expostas em claro permanece adiada, sem dono e sem prazo, com o risco registrado e
revisável (§3 do registro). O fechamento não converte os achados do §10 em
conformidade; eles permanecem abertos nos planos donos, listados na §4 do registro.

## 13. O que não foi verificado

- Nenhum handshake MCP, `tools/list` ou `tools/call` foi executado: o inventário é
  estrutural (`inspect`), não funcional.
- Não foi verificada a procedência byte a byte das imagens (rebuild não reproduzido);
  nenhuma imagem foi recomputada.
- Não houve consulta ao registry remoto, GitHub Actions ou estado do VPS.
- O conteúdo de `~/.nanobot/config.json` além de `tools.mcpDocker`, `api` e `gateway`
  (channels, providers, kg, modelPresets) não foi inventariado — irrelevante para o
  escopo de imagem.
- `scripts/percival-f0-validate.sh` (harness de validação de superfície B14–B25 em
  daemon descartável) **não foi executado**: ele constrói e remove containers e uma
  imagem de teste, o que excede o escopo read-only desta reexecução. Permanece
  disponível para uma execução isolada, com autorização própria.
- Não foi inspecionado o conteúdo das imagens (SBOM, vulnerabilidades, packages);
  os scans Trivy/OpenVEX existentes referem-se a outros image IDs.

## 14. Próximos passos sugeridos (nenhum executado)

1. **Feito:** D-1, D-2, D-3, D-5, D-6 e o item 7 confirmados pelo operador e
   formalizados no [adendo da ADR](../Decisions/2026-10-09-docker-standardization.md).
2. **Feito:** gate F0 (reexecução) fechado em 2026-10-24 por assinatura do operador
   ([registro de fechamento](2026-10-24-f0-closure-record.md)), com D-4 encerrada
   por aceitação formal do risco residual. A revisão de D-4 fica prevista para antes
   de I3/I5 ou de qualquer migração de estado/IaC, quando a exposição deixa de ser
   local; o formato de gravação dos registros de transição/backup continua sem
   decisão e é independente da rotação.
3. **Se e somente se autorizado:** promoção dos candidatos de checkout limpo
   (`<semver>-<shortsha>` de HEAD) para os seis MCPs, com canário e rollback por
   rebuild — remove A5/A6 e alinha os artefatos em execução à fonte.
4. **Se e somente se autorizado:** rebuild do broker com metadata derivada da fonte
   (`0.1.0`), encerrando o desvio D-1/A1 e o pin por tag mutável (D-2/A9).
5. Tratar A10 (fixtures) com lista explícita por Image ID, após confirmar zero
   referências nas **duas** fontes de pin (A7).
