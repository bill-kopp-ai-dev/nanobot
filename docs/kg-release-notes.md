# Percival KG — notas de release candidata (não publicada)

- Distribuição existente: `nanobot-ai` 0.3.5; sem versão/tag KG aprovada.
- Native: 20 CM + 14 AK, 12 skills descobertas, CLI `nanobot kg`, gateway
  autenticado + SPA React/D3 em `/kg-interface/`.
- Commit candidato para a próxima release KG: o commit **"feat(kg): close
  F9 with platform CI, endpoint inventory and migration tests"** no branch
  `main` do fork (ver histórico do branch; o SHA exato muda a cada amend).
  Ele inclui o snapshot SPA reconciliado com `f607d6a` (`dirty=false`) e a
  deleção dos três assets antigos.
- Migração: seguir [guia](kg-migration.md); manter os MCPs instaláveis para
  rollback, backup **incluindo** `sources/` e `assets/` e ensaio em cópia.
- Incompatibilidades: `cmEnrichModel`/`cmEnrichBaseUrl` rejeitados; provider
  do turno substitui chave dedicada. Grafo nativo não gera HTML/rotulagem
  graphify. Áudio nativo não transcreve e retorna `unsupported_capability`.
- Distribuição/plataformas: core KG usa `fcntl` no Linux/macOS e `msvcrt`
  no Windows. CI matrix em `.github/workflows/kg-platform.yml` ainda não foi
  executado em runner macOS/Windows real (apenas local em Linux); manter a
  ressalva até que `.github/workflows/kg-platform.yml` rode verde nos três.

## Proveniência verificada em clone limpo do fork (A3)

Em clone sem vizinhos a partir do commit `5c26b30c` (sem `webui/` ou
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
  `scripts/kg_platform_modality_smoke.py`) passam no Linux; o matrix
  macOS/Windows é o gate aberto até a primeira execução em runner real.

Gate de publicação: seguir [checklist upstream](releasing.md) **mais**
[F9](plans/kg-integration-plan.md#f9--skills-documentação-migração-e-release),
smoke wheel/sdist isolado, comparação e rollback sobre **cópias de bundles
reais**, CI por plataforma e decisão explícita para áudio. Após os gates,
reconciliar versão/changelog/artefatos com o commit final; tag, push remoto,
PyPI e status/EOL dos repos legados exigem autorização do operador.
