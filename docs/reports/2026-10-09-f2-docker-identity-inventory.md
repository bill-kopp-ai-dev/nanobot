# F2 — Contrato de identidade e inventário contínuo

- **Data:** 2026-10-09
- **Estado:** implementação revisada e integrada em `origin/main`; o gate final
  de builds canônicos em checkout limpo permanece aberto.
- **Plano:** [`padronização Docker`](../plans/2026-10-09-docker-standardization-refactor-plan.md), fase F2.
- **Engine local observado:** Docker Engine 29.7.2, linux/amd64. Isto não demonstra compatibilidade com Engine 27.x do gate remoto.

## Contrato implementado

### Identidade OCI dos seis MCPs

Os seis Dockerfiles publicam os labels OCI comuns: `title`, `description`,
`source`, `documentation`, `licenses`, `version`, `revision` e `vendor` sob o
namespace `org.opencontainers.image.*`. Cada label obrigatório é definido no
stage runtime, sobrescrevendo qualquer valor herdado da imagem-base. Os
metadados de origem/documentação agora apontam para o repositório independente
de cada MCP, não para o antigo monorepo.

O comando canônico local é:

```bash
python scripts/percival-docker-build.py
```

O script lê `project.version` de `pyproject.toml`, exige SemVer válido e um
checkout Git com SHA completo, recusa placeholders (`0.0.0`, `unknown`,
`local`) e mudanças tracked por padrão, constrói somente `linux/amd64` sem
registry e inspeciona plataforma e os oito labels exigidos antes de emitir o
manifest JSON. O tag imutável segue `percival-<service>:<version>-<shortsha>`.
`:dev` só é adicionado quando `--dev-alias` é explicitamente pedido; tags
existentes não são sobrescritas. Para validação de alterações ainda não
commitadas, `--worktree-candidate` cria um tag com hash do diff, adiciona os
labels `io.percival.build.worktree=dirty` e
`io.percival.build.source-diff-sha256`, e não atualiza `:dev`.

### Identidade de containers broker-managed

O broker conserva `percival.mcp-docker.server-id` e aplica em cada novo
container:

- `percival.mcp-docker.owner=percival`
- `percival.mcp-docker.managed-by=percival-broker`
- `percival.mcp-docker.instance-id=<UUID v4>`

`instance-id` identifica uma encarnação de container; recriar/reiniciar cria
novo UUID. Não foi adicionado `container_name` fixo ao broker; removi também os
nomes fixos preexistentes dos dois serviços Compose OSM para evitar colisão ao
executar múltiplos projetos/instâncias. Containers antigos não foram
reescritos e mantêm seus labels atuais até um futuro ciclo autorizado de
recriação.

### Inventário read-only

Comando:

```bash
python -m nanobot.mcp_docker.inventory --format markdown
# ou --format json para automação
```

O inventário cobre imagens relevantes e imagens referenciadas por containers,
containers Percival/Positronic associados por nome/label/referência de imagem,
IDs e RepoDigests separados, tags, labels OCI, data/plataforma, healthcheck,
ports, mounts, init/TTY/stdin e referências de `docker-compose.yml`,
`~/.nanobot/config.json`, registry MCP do Positronic e configuração OpenCode.
Usa consultas Docker `list`/`inspect` e lê somente caminhos de referência nos
arquivos JSON; não consulta `Config.Env`, conteúdo de arquivos de segredo ou
valores de configuração além das referências de imagem. Caminhos de mounts
com `.env`/`secrets` são redigidos. Sem containers identificáveis só pelo nome
aleatório, as referências da registry permitem relacioná-los por image ID sem
atribuir ownership não comprovado.

Snapshot final desta execução: **55 imagens, 11 containers e 13 referências**. As duas
instâncias Positronic AgentMail foram identificadas pelo mesmo image ID e
permanecem distintas por container ID/nome; a razão da duplicação segue
desconhecida. Labels owner/manager/instance estão ausentes nos containers
históricos, como esperado antes de eventual recriação. O inventário não
alterou containers, pins ou configurações. Foi verificado que o JSON produzido
não contém `/run/secrets/` nem o caminho do arquivo de token do broker.

## Imagens candidatas locais

As imagens abaixo foram criadas com `--worktree-candidate` quando a árvore
continha mudanças tracked; o tag e label adicional ligam a imagem à revisão
base e ao hash do diff. Khan Calendar estava clean e usou o tag canônico. Todos
os seis passaram as verificações automáticas do build script: labels comuns,
versão igual a `pyproject.toml`, revision igual ao SHA completo do checkout e
plataforma `linux/amd64`. RepoDigests são observações do daemon local, não
publicação em registry.

| MCP | Tag local | Checkout SHA | Diff SHA-256 (worktree) | Image ID / RepoDigest local |
|---|---|---|---|---|
| Notes | `percival-notes-mcp:0.1.5-4db7ddb-f2-294e1bfdff72` | `4db7ddb4d4a0195e6b05765ec65227a248aa0fd0` | `294e1bfdff723273d1def9012e82135ff2f2aa8405f3d72ff6274df18a028b25` | `sha256:409d37bb8784d5aa75db820f9523811bc9444ac19f26b5f8efe9337325df0620` |
| AgentMail | `percival-agentmail-mcp:0.4.0-aff0c00-f2-393da4f45026` | `aff0c00ef298d69930fdee91ea4faf64e1389d99` | `393da4f45026d166d637181f425cfabce5e1a296960b4ea9ccf9ad45111ad1cc` | `sha256:0e6fae8c1deac7f742da2f7a7b3ff7c77ad0cb5ec9908e4afbde6892c8fb80f5` |
| Weather | `percival-weather-mcp:0.9.0-b8befdc-f2-77e3b7f425ca` | `b8befdc63ab49272861aa18edeba772b28fa36b4` | `77e3b7f425ca6530266de383629148fd16f4d23adfcb76254af47e565ee63207` | `sha256:f44f7bd3867e3c6c67bb8f4a1f64229c499c67b4ac650ec9cec574b727b784bf` |
| Khan Calendar | `percival-khan-calendar:0.4.0-ec725d9-f2-2da703c83515` | `ec725d94682f3d792824e8f5a8ca9c13b055a7c2` | `2da703c83515f0fbee5d09191c17feb78d83494db6b43838a4367469dd29a6d0` | `sha256:b293b2a4efaf7e5a1510d58803a22d0e0235b12d97e8261bbfbd06d480255636` |
| OSM | `percival-osm:0.5.0-0f2f078-f2-1ad8a6b2636a` | `0f2f078ca53082627a209056a11e9e9a52301cfd` | `1ad8a6b2636ab807e578e6b1533d5d3f29183613b73f61ec0a3223b892032b17` | `sha256:77231bd58f43cd4107583b49476a292e12edb7e409943784e43290a2c8cafff8` |
| Deep Research | `percival-deep-research:3.0.1-37a474f-f2-b2b6543ecdba` | `37a474f9d413bb49f91d62d822fc801fb84f09fe` | `b2b6543ecdba809cc64bd9aaf1a4746dd5e7669d15e614e08089872a3a11f1ac` | `sha256:9a68a525685d3baa4cf189359ff9a0daa7b2b642b434997b2f3d275a1aa76560` |

O RepoDigest local de cada candidato observado corresponde ao Image ID listado
na tabela. Tags temporários de tentativas anteriores e todas as imagens
históricas foram preservados; nenhuma limpeza foi feita. Os consumidores do
broker continuam fixados nos IDs anteriores, sem pull nem cutover.
Weather e Khan também passaram a excluir `.positronic/` e `AGENTS.md` do
contexto de build local, impedindo que metadados de projeto ignorados pelo Git
sejam enviados ao daemon durante builds.

Uma tag Deep Research de uma tentativa intermediária,
`percival-deep-research:3.0.1-37a474f-f2-d57ab300b72e` (ID
`sha256:c12a9582fb03ceef08f8942ba59d0c81b818b385307d881126679bb4d9675399`),
foi sobrescrita por um script de smoke antigo e ficou com label version
`0.0.0`. Ela é **superseded/invalid; não usar**. Foi preservada para não fazer
cleanup incidental; a imagem final válida está na tabela com tag `...b2b6543ecdba`.

## Verificação

- Builds dos seis MCPs passaram e foram inspecionados por versão/revisão/labels
  e arquitetura. Os seis candidatos de worktree têm tag + label com hash do
  diff. O build script também exige que `.positronic/` e `AGENTS.md` locais
  sejam excluídos do Docker context antes de permitir esses candidatos.
- Smokes Docker de Deep Research e OSM passaram contra imagens F2 separadas:
  initialize/tools-list stdio; HTTP/auth/health/bind; encerramento por SIGTERM
  com um `tini`. O teste Deep Research revelou uma regressão no script de smoke:
  ele deixava `VERSION` no default `0.0.0` e regravava o tag candidato; o script
  agora lê versão do TOML, passa versão e SHA completo ao Dockerfile, e o smoke
  foi executado em tag dedicada `smoke-f2-*`, sem sobrescrever o candidato
  versionado. A imagem Deep candidata final foi reconstruída/inspecionada após
  a correção.
- `docker compose config --quiet` passou para OSM (normal e HTTP) e Deep
  Research (HTTP e production). O teste OSM de contrato Docker passou após a
  remoção de `container_name`.
- Testes de aplicação: Percival `9302 passed, 49 skipped`; Notes `45 passed`;
  AgentMail `230 passed, 1 skipped`; Khan Calendar `220 passed`; Deep Research
  `414 passed, 3 skipped`; Weather e OSM também passaram suas suítes completas.
- Percival: `uv run basedpyright nanobot` sem erros; `uv run ruff check .`
  passou. Testes focados de broker/inventário: `26 passed`.
- Inventário executado e inspecionado como read-only; as verificações automáticas
  confirmaram que conteúdo/env de segredo não aparece no JSON.

## Gate e limites restantes

F2 está implementada, revisada e integrada em `origin/main`, mas **o gate não é
declarado fechado**: os seis candidatos `-f2-<diff>` vieram de worktrees dirty e
não representam builds canônicos dos commits integrados. Para fechar o gate,
reconstruir os seis checkouts limpos com
`python scripts/percival-docker-build.py`, registrar os novos IDs/digests e
confirmar que a configuração broker permanece pinada nos IDs prévios. Na
execução original não houve commit/push, publicação, pull explícito, cutover,
alteração de consumers ou remoção de imagens; os commits F2 foram enviados
posteriormente em 2026-10-09.

O gate F2 pendente é especificamente a reconstrução canônica em checkout limpo
após a integração. A implementação F3 começou depois dos commits F2 estarem em
`origin/main`; os candidatos F3 são independentes e não fecham retroativamente
esse gate.
