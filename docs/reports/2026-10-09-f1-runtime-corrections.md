# F1 — Correções imediatas de runtime: Deep Research e OSM

- **Data:** 2026-10-09
- **Estado:** gate F1 concluído para candidatos locais; sem cutover.
- **Plano:** [`padronização Docker`](../plans/2026-10-09-docker-standardization-refactor-plan.md), fase F1.
- **Engine de teste:** Docker Engine 29.7.2, linux/amd64.

## Escopo e preservação

Foram corrigidos os contratos de runtime dos MCPs Deep Research e OSM conforme
F1. Os repositórios estavam em `main`, nos SHAs `e91ad8b` e `c01063b`; no início
da fase não havia mudanças rastreadas pendentes. Os arquivos locais não
rastreados `.positronic/` e `AGENTS.md` foram preservados. As árvores agora têm
as mudanças F1 não commitadas descritas abaixo.

Não houve chamada a API externa nem uso de credenciais reais: os smoke tests
usaram placeholders descartáveis e executaram somente `initialize`,
`tools/list`, `/health` e verificações locais de auth/listener. Os containers
históricos, configurações dos consumidores, imagens antigas, tags existentes e
volumes reais não foram modificados ou removidos. Containers de fixture,
networks e volumes Compose próprios do smoke foram removidos após a verificação;
as imagens candidatas locais foram mantidas para rollback.

## Alterações

### Deep Research

- Removido o `HEALTHCHECK` HTTP da imagem: seu transporte padrão é stdio, que
  não abre a porta 8000.
- Separados `percival-deep-research-stdio` e
  `percival-deep-research-http` em profiles Compose distintos. Stdio mantém
  `stdin_open: true`, `tty: false`, sem porta, healthcheck ou restart
  persistente. HTTP/SSE possui porta, restart e probe `GET /health` próprios.
- Removido `init: true` do Compose; `/usr/bin/tini` embutido na imagem é o único
  init.
- HTTP publica em `127.0.0.1` por padrão. A probe trata HTTP 200 e 503 como
  listener ativo e preserva o body `/health` como informação de readiness de
  configuração; não testa APIs upstream nem confunde falha externa com morte
  do processo.
- Atualizados smoke, regressões estáticas, README, Docker README e changelog.

### OSM

- Removido `pgrep` indisponível da imagem; `HEALTHCHECK NONE` impede que stdio
  seja marcado `unhealthy` por uma probe que não pode funcionar. O serviço
  Compose stdio explicita `tty: false`, stdin aberto, sem porta, healthcheck ou
  restart persistente.
- Healthcheck de listener existe somente no serviço Compose HTTP e consulta
  `/`, aceitando 200/401/404/405 sem testar Nominatim, Overpass ou ORS.
- O profile HTTP exige `MCP_OSM_AUTH_TOKEN`, habilita o bind remoto dentro da
  rede do container e publica em `127.0.0.1` por padrão. Um bind externo exige
  override explícito de `HTTP_BIND_ADDRESS`; o bearer token continua
  obrigatório.
- Corrigida a composição de variáveis: o profile HTTP herda também
  `USER_AGENT` e `FROM_HEADER`, que são obrigatórios para o servidor iniciar.
- Atualizados smoke, testes de deployment, README, `.env.example` e guia de
  Docker.

## Candidatos construídos

Tags locais de candidato incluem o SHA-base e o sufixo F1; a label de revision
identifica explicitamente o worktree sujo usado no build. RepoDigests abaixo
são observações do Docker local, não publicação em registry.

| Servidor | Tag local | Source SHA / revision label | Image ID | RepoDigest local | Plataforma | Tamanho |
|---|---|---|---|---|---|---:|
| Deep Research | `percival-deep-research:3.0.1-e91ad8b-f1-20261009-2` | `e91ad8b` / `e91ad8b-f1-worktree` | `sha256:09e07bfc9f3b3bc1391066475439a4acde323f62d06aa79e58ad951f4201b5af` | `percival-deep-research@sha256:09e07bfc9f3b3bc1391066475439a4acde323f62d06aa79e58ad951f4201b5af` | `linux/amd64` | 317,010,015 bytes |
| OSM | `percival-osm:0.5.0-c01063b-f1-20261009-2` | `c01063b` / `c01063b-f1-worktree` | `sha256:43676d422dbbc87c8bce85bb8e7cf9a7fc7ffd818f0dc667515b1db488046f33` | `percival-osm@sha256:43676d422dbbc87c8bce85bb8e7cf9a7fc7ffd818f0dc667515b1db488046f33` | `linux/amd64` | 60,383,028 bytes |

As labels de revision foram aplicadas apenas às imagens locais de candidato;
não substituem o trabalho F2 de labels/proveniência canônicos nos Dockerfiles.
As bases foram resolvidas durante o build para:

- Deep Research: `ghcr.io/astral-sh/uv:python3.11-bookworm-slim@sha256:4f5d923c9dcea037f57bda425dd209f3ec643da2f0b74227f68d09dab0b3bb36` e `python:3.11-slim@sha256:0dd364ba7e10242f07755449e3a3d0e35f9efd987952737b90def6709ab0c5ce`.
- OSM: `ghcr.io/astral-sh/uv:python3.12-bookworm-slim@sha256:e5b65587bce7de595f299855d7385fe7fca39b8a74baa261ba1b7147afa78e58` e `python:3.12-slim-bookworm@sha256:34386ef0cb081344d7ec1c103ba398e6e9f64e9ab3a1509accc92a4e24a07258`.

## Evidência do gate

### Deep Research

- `docker compose --profile http config --quiet`, profile `production` config e
  configuração normalizada dos serviços passaram.
- `uv run pytest -q`: **414 passed, 3 skipped**; uma warning upstream de
  depreciação `langchain-community`.
- `uv run --with ruff ruff check .`: passou.
- `scripts/docker_smoke_test.sh`, com a tag candidata e revision explícitos:
  imagem sem healthcheck HTTP, entrypoint único `tini`, stdio
  `initialize`/`tools/list` com as cinco tools públicas, HTTP/SSE em porta
  efêmera loopback, `/health` 200, healthcheck de listener saudável e SIGTERM
  encaminhado por `tini` (exit 143 antes de qualquer SIGKILL).
- O profile Compose HTTP foi iniciado em projeto descartável com a imagem
  candidata: host bind `127.0.0.1`, `tty=false`, PID 1 `/usr/bin/tini`, sem
  `init: true`, `GET /health` respondeu `healthy`, healthcheck Compose ficou
  `healthy`; container e network foram removidos.
- O profile Compose stdio foi executado com `run --rm -T`: `initialize` e
  `tools/list` das cinco tools passaram sem porta ou TTY; network descartável
  removida.

### OSM

- `USER_AGENT=... FROM_HEADER=... MCP_OSM_AUTH_TOKEN=... docker compose
  --profile http config --quiet` e a configuração normalizada passaram.
- `uv run pytest -v`: **75 passed**. `uv lock --check` passou.
- `scripts/docker-smoke-test.sh` contra a imagem candidata passou: healthcheck
  stdio explicitamente desabilitado, usuário não-root, env obrigatório,
  stdio MCP e tools canônicas, HTTP Streamable com bind loopback, 401 sem token,
  `initialize` 200 com bearer token, listener healthcheck saudável e SIGTERM
  encaminhado por `tini` sem timeout (exit 143).
- Profile Compose HTTP executado em projeto/container/volume isolados:
  host bind `127.0.0.1`, requisição sem auth `401`, `initialize` autenticado
  `200`, healthcheck Compose `healthy`, PID 1 `/usr/bin/tini`, sem Docker
  `init:true`. Container, volume e network foram removidos.
- Profile Compose stdio executado com `run --rm -T`: `initialize` e tools
  canônicas passaram; volume/network descartáveis removidos.

### Inspeção e integridade

- `docker inspect` confirmou `linux/amd64`, tags, image IDs, revision labels,
  `ExposedPorts` informativo (`8000/tcp` e `8080/tcp`) e healthcheck ausente
  para Deep Research / explicitamente `NONE` para OSM.
- Os profiles HTTP renderizados publicam apenas na interface de host
  `127.0.0.1` por default; OSM exige token no Compose HTTP. As duas imagens
  mantêm somente o `tini` embutido e não usam `init: true`.
- `git diff --check` passou nos dois repositórios. Não houve commit, push,
  registry publication, alteração de consumidor, remoção de imagem histórica ou
  mudança em container real. Os builds resolveram referências `FROM` e
  baixaram bases/camadas ausentes, registradas acima; não houve `docker pull`
  explícito nem envio remoto.

## Limitações e próximo passo

- As duas instâncias Positronic Deep Research existentes continuam em execução
  e `unhealthy`, associadas à imagem antiga
  `sha256:fa1e3cec8cd3c1423f87987f41c0d3c5f15505826953224924f015194c30ac99`.
  O container histórico Percival Deep Research permanece `Exited (143)` e o
  OSM histórico `Exited (143)`. Isso é esperado: F1 validou candidatos, não
  alterou consumers. Canary, rollback por consumer e cutover continuam em F6.
- O profile `production` do Deep Research foi validado em `docker compose
  config`, não iniciado. `nginx.conf` não existe neste checkout; esse profile
  precisa de configuração de proxy antes de uma validação end-to-end.
- Pins de digest das imagens base, labels OCI canônicas, builds reprodutíveis,
  CI e inventário contínuo pertencem às fases seguintes. Nenhuma base foi
  fixada nesta fase.

**Próximo passo do plano:** F2 — formalizar metadados OCI/container e inventário
read-only. Não promover as imagens candidatas aos consumidores até F6.
