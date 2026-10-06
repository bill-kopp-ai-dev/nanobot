# Percival KG — notas de release candidata (não publicada)

**Rascunho para revisão do operador — sem sign-off, tag ou publicação.**
Percival é independente, derivado do nanobot. Primeira versão pretendida:
0.1.0; pacote e canal de distribuição ainda serão definidos. Ver
[governança](percival-governance.md).

- Distribuição existente: `nanobot-ai` 0.3.5; sem versão/tag KG aprovada.
- Native: 20 CM + 14 AK, 12 skills descobertas, CLI `nanobot kg`, gateway
  autenticado + SPA React/D3 em `/kg-interface/`.
- SHA candidato final: **a definir** após gates e revisão do operador; o
  commit F9 histórico não é automaticamente o candidato à versão 0.1.0.
  Verificar novamente o snapshot SPA e a exclusão dos assets obsoletos
  no SHA exato escolhido.
- Migração: seguir [guia](kg-migration.md); manter os MCPs instaláveis para
  rollback, backup **incluindo** `sources/` e `assets/` e ensaio em cópia.
- Incompatibilidades: `cmEnrichModel`/`cmEnrichBaseUrl` rejeitados; enrich e
  imagem usam provider do turno. Grafo nativo não gera HTML/rotulagem graphify.
  Para áudio AK, a decisão B5 usa o serviço Groq Whisper do nanobot: envia o
  arquivo à Groq, requer credencial/configuração explícita e não troca o
  modelo de chat do turno. A integração foi testada com HTTP simulado; falta
  prova com credencial e arquivo reais.
- Distribuição/plataformas: o Percival declara **Linux-only** (decisão
  do operador 2026-10-06 — `docs/reports/2026-10-05-kg-f0-execution-status.md`
  §B4). O backend `msvcrt` continua no vendor do core para desenvolvedores
  em Windows, mas o gate KG (`kg-platform.yml`) executa **somente** em
  `ubuntu-latest`. O CI geral ainda inclui Windows e requer ajuste. macOS
  não é mais prometido nem anunciado. Quem roda em outras plataformas o
  faz por conta própria, sem SLA nem gate de release.

## Proveniência verificada em clone limpo do fork (A3)

Em clone sem vizinhos a partir do commit `3129e0f1` (sem `webui/` ou
`spa/` vizinhos), em `uv build --sdist` → `uv build --wheel` → instalação
isolada em Python 3.12:

- `nanobot/web/kg-interface/SOURCE.json` aponta para a revisão
  `f607d6a2f97d7a539170e99ec843c3cd02691b47` com `dirty=false`.
- Os 9 assets KG (LICENSE, index.html, JS, JS map, CSS, dois PNG, ASSETS-SPEC,
  SVG) batem SHA-256 com `SOURCE.json`.
- Nenhum dos 3 assets obsoletos (`index-DoY8kHsm.css`, `index-ZIxPmxp_.js`
  e `.js.map`) está presente na árvore ou no tarball.
- As 12 skills KG (6 AK + 6 CM) são descobertas por `SkillsLoader` no venv
  instalado.
- `nanobot kg graph rebuild --help`, `nanobot kg doctor --help` e
  `nanobot kg bundle --help` funcionam a partir do wheel instalado.
- Testes `tests/kg` no clone limpo: 121 passed / 2 skipped (sem o teste de
  browser).
- Smoke scripts (`scripts/kg_platform_lock_smoke.py` e
  `scripts/kg_platform_modality_smoke.py`) passaram no Linux naquele clone;
  a CI do commit candidato ainda precisa ser verificada. macOS/Windows
  não são plataformas suportadas do Percival.

## Known limitations e gates abertos

- B6/B7: ensaio de migração/rollback com bundles reais e decisão de cutover
  `kg.mode="native"` são do operador; testes sintéticos não substituem isso.
- Áudio Groq: HTTP simulado testado; falta amostra consentida e credencial
  real para medir custo, latência e resultado.
- CI geral ainda contém Windows; empacotamento TUI herdado presume cinco
  plataformas. Ajustar ambos e validar artefatos Linux antes da release.
- UI e memória customizadas e suporte MCP-in-Docker ainda têm trabalho
  planejado; não anunciá-los como funcionalidades lançadas.
- SHA candidato, destino de distribuição e sign-off final indefinidos.

Gate de publicação: seguir [checklist Percival](releasing.md),
[F9](plans/kg-integration-plan.md#f9--skills-documentação-migração-e-release),
smoke de wheel/sdist isolado, ensaio em **cópias de bundles reais**,
validação operacional do áudio e CI Linux no SHA candidato. O agente redige
changelog, limitações e referências; o operador assina a versão final antes
de tag, repositório público ou publicação.

## Repos legados congelados (2026-10-06)

`percival-collective-memory` e `percival-acquire-knowledge` foram congelados
(D5/D10) com tag `legacy-final` apontando para o último commit antes do
banner EOL; ver
[`docs/reports/2026-10-05-kg-f0-execution-status.md`](reports/2026-10-05-kg-f0-execution-status.md#b8b9--freeze-d5-e-eol-d10-dos-servidores-mcp-legados-2026-10-06)
e o `MIGRATION.md` na raiz de cada repositório legado para o mapeamento de
tools, migração de `config.json` e rollback via tag `legacy-final`. A flag
`Archive this repository` será aplicada pelo operador no console web do
GitHub (CM primeiro, AK em seguida); não depende de `gh auth login`.
Evitar novas instalações dos MCPs legados. `nanobot-ai` não é uma release
do Percival; não recomendar upgrade público para pacote ainda não lançado.
