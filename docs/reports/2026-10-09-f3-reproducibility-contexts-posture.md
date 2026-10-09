# F3 — Reprodutibilidade, contextos e postura base

- **Data:** 2026-10-09
- **Estado:** implementação e validação local concluídas; **gate F3 aberto** por
  findings Critical/High sem triagem/waiver e ausência de build em checkout limpo
  no builder CI.
- **Plano:** [`padronização Docker`](../plans/2026-10-09-docker-standardization-refactor-plan.md), fase F3.
- **Manifest detalhado:** [`F3 image build manifest`](2026-10-09-f3-image-build-manifest.json).
- **Política:** [`Docker image security and maintenance policy`](../Decisions/2026-10-09-docker-image-posture-policy.md).
- **Target:** `linux/amd64`; imagens locais apenas, sem cutover/publicação.

## Mudanças implementadas

### Locks e toolchains

- O `uv.lock` do Percival já existia localmente, mas estava ignorado pelo
  `.gitignore`; a exceção `!uv.lock` agora permite rastreá-lo. O arquivo ainda
  está untracked/não commitado neste worktree. `uv lock --check` passou (`145`
  pacotes) e o Dockerfile do gateway usa `uv sync --locked` nos passos de
  instalação do projeto e das dependências.
- A imagem preinstala dependências de canal por meio de 13 locks de requirements
  com hashes, compilados para Python 3.12/Linux amd64 a partir dos manifests
  Python. `channel-locks/manifest.json` liga cada lock ao conteúdo exato de
  `ChannelPlugin.dependencies`. O verificador
  `uv run python -m scripts.compile_channel_locks --check` passou; o instalador
  dentro da imagem valida o manifest/lock e usa `pip --require-hashes`. Um lock
  ausente ou divergente falha fechado para canais. Extras de projeto que não
  são canais mantêm o fluxo atual.
- Weather e OSM não exportam mais requirements com `--no-hashes`; os dois
  Dockerfiles sincronizam diretamente pelo `uv.lock` (`uv sync --frozen`).
- O bootstrap uv do Notes (`uv==0.12.18`) também tem requirements lock com hash.
  Os 13 channel locks, o `docker/mcp-broker-requirements.lock` e o
  `compile_channel_locks.py` do Percival são arquivos novos desta execução e
  ainda não commitados. O `uv.lock` foi liberado para commit mas também
  permanece untracked.
  As imagens AgentMail/Khan usam uv `0.5.11`, Weather `0.5.7`, e as bases uv
  pinadas do gateway/OSM/Deep Research usam `0.9.30`. O `package-lock.json` da
  WebUI é consumido com `npm ci` e incluído no manifest.
- O `Dockerfile.mcp-broker` instala `pydantic==2.13.5` e suas dependências via
  lock/hash para Alpine/Python 3.12; Python e pip Alpine estão pinados em
  `3.12.15-r0` e `24.3.1-r0`.

### Bases, sistema e contextos

- Todas as instruções `FROM` dos seis MCPs, gateway e broker agora usam digest
  imutável apropriado a amd64. A lista completa aparece em `baseImages` no
  manifest de builds.
- Imagens Debian usam `snapshot.debian.org` em `20261009T000000Z`, upgrade
  explícito da base e versões pinadas para pacotes instalados diretamente.
  Ferramentas de build do OSM também usam esse snapshot. Isso permite update
  trimestral controlado e mudança emergencial do snapshot/pins, sem resolver
  silenciosamente contra um mirror móvel.
- `.dockerignore` do gateway e dos MCPs foi ampliado para excluir venvs,
  `.env*`/secrets, `.positronic`, `AGENTS.md`, caches, logs, artefatos e arquivos
  não copiados pelo Dockerfile. BuildKit confirmou os tamanhos de contexto dos
  worktrees-candidatos:

  | Imagem | Contexto transferido |
  |---|---:|
  | Notes | 193 B |
  | AgentMail | 2.65 kB |
  | Weather | 4.63 kB |
  | Khan Calendar | 3.94 kB |
  | OSM | 968 B |
  | Deep Research | 6.85 kB |
  | Gateway/WebUI | 28.78 MB |
  | MCP broker | 432 B |

  Esses valores são observados com `docker buildx build --output=type=cacheonly
  --progress=plain` nas árvores locais F3. O build candidato normal do broker
  reportou 11.64 kB de transferência, enquanto o modo cache-only transferiu os
  432 B efetivamente necessários aos `COPY`; ambos são preservados no manifest.
  Não são medições em checkout CI limpo, e não foi exportado um snapshot de
  contexto para inspeção de conteúdo. O baseline F0 do gateway (346.73 MB)
  continha estado local; não é uma comparação equivalente nem base aceita para
  orçamento.

## Candidatos, SBOM e scan

Oito candidatos foram construídos/inspecionados em worktrees dirty; tag e label
guardam o SHA-256 do diff. IDs, RepoDigests, locks, bases, build args, tamanhos,
contextos e verificações estão no manifest JSON.

SBOMs CycloneDX foram gerados com Docker Scout CLI 1.25.0. O scan de imagem foi
feito com Trivy 0.67.2 (imagem amd64
`aquasec/trivy@sha256:ac2f9d0197456a8ce460884b113e49d65b667f506c31d014c9955869a7a5d682`),
sem montar `docker.sock`: cada imagem foi exportada por `docker save` para um
tarball temporário montado read-only no scanner. A base de vulnerabilidades
Trivy foi atualizada em `2026-10-09T13:10:00Z`, baixada em `15:53:02Z`. Os
artefatos ficam localmente em `/home/bill/.positronic/runtime/tmp/opencode/`;
seus hashes estão no manifest para detectar alterações.
O endpoint CVE do Docker Scout não foi usado porque exige login; a análise CVE
foi feita pelo Trivy, sem entregar acesso ao Docker socket.

| Imagem | Componentes SBOM | Findings Critical | Findings High |
|---|---:|---:|---:|
| Notes | 189 | 3 | 64 |
| AgentMail | 193 | 3 | 61 |
| Weather | 189 | 4 | 64 |
| Khan Calendar | 236 | 3 | 61 |
| OSM | 212 | 5 | 83 |
| Deep Research | 415 | 5 | 97 |
| Gateway | 343 | 3 | 89 |
| Broker | 280 | 7 | 162 |
| **Total de observações** | — | **33** | **681** |

As contagens são findings por imagem, não CVEs únicos; findings repetidos em
imagens/dependências comuns contam mais de uma vez. Exemplos registrados:
PyJWT (`CVE-2026-102268`, instalado 2.12.1/2.13.0, correção reportada em
2.14.0), NLTK (`CVE-2026-79657` e `CVE-2026-79675`, 3.10.0 → 3.10.3), h11
(`CVE-2025-43859`, 0.14.0 → 0.16.0), AnyIO (`CVE-2026-63374`, 4.8–4.11 →
4.14.2), Docker CLI/golang stdlib/gRPC e bibliotecas base Debian/Alpine.
Trivy também avisou que a SBOM de terceiro pode reduzir a precisão para Deep
Research e gateway; esses findings necessitam triagem humana antes de decisão.

A política F3 bloqueia promoção com findings Critical/High, salvo exceção
individual aprovada com owner, justificativa, mitigação e validade. **Nenhuma
exceção foi registrada**; não classifiquei os findings como falso positivo ou
não aplicável sem análise. Por isso, apesar da geração de SBOM e scan, o gate
permanece aberto.

## Verificação

- Percival: `uv lock --check`, `uv run python -m scripts.compile_channel_locks
  --check`, basedpyright e Ruff passaram; `uv run pytest`: **9306 passed, 49
  skipped**.
- MCPs: Notes **45 passed**; AgentMail **230 passed, 1 skipped**; Khan **220
  passed**; Deep Research **414 passed, 3 skipped**. Weather e OSM passaram suas
  suítes completas locais; os locks passaram `uv lock --check` nos seis MCPs.
- OSM smoke passou em stdio/HTTP, auth, bind loopback e shutdown. Deep Research
  smoke passou em stdio `initialize`/`tools/list`, HTTP `/health` e shutdown por
  SIGTERM; testes de aplicação também passaram. As suites Deep Research tentam
  algumas integrações sem API key e emitem tracebacks esperados, mas terminaram
  com 414 passed/3 skipped.
- Gateway candidato contém e valida locks de 13 canais; runtime verificou
  `neonize==0.4.3.post0`, `segno==1.6.6`, `NANOBOT_CHANNEL_LOCK_DIR` e o comando
  `--check`. Broker runtime importou `pydantic==2.13.5`.
- Todos os `uv.lock` dos seis MCPs passaram `uv lock --check`; não foi executado
  build remoto GitHub Actions em SHA candidato.

## Gate e próximos passos

F3 permanece aberta porque: (1) há 33 Critical e 681 High findings por imagem,
sem triagem ou waivers aprovados; (2) as builds vêm de worktrees locais dirty,
não de checkout limpo em builder CI; (3) a repetibilidade do conjunto resolvido
está sustentada pelos locks/hash e snapshots, mas ainda precisa de execução
comparativa em CI/checkout limpo. O SBOM/scan externo está armazenado em paths
locais citados no manifest e não foi commitado como artefato binário.

Prioridade seguinte: triagem de findings Critical/High e fixes de versões que
tenham correção disponível; revisar CVEs de pacotes base e a advertência de
SBOM externo; então reconstruir/scanear em checkout limpo. Não usar os
candidatos F3 como tags canônicas, não mover `:dev`, não alterar pins de
consumers e não remover tags/imagens antigas.
