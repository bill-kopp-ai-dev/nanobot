# RUNBOOK — sincronizar o fork Percival com HKUDS/nanobot

**Revisão:** 2026-10-06. A política de 2026-08-01 (main como espelho do
upstream, customização só em `feat/percival-branding` e submódulo
`mcp-servers-percival`) foi substituída na prática: o fork atual integra
customizações diretamente em `main`. Consultar `git status`, `git remote -v`
e o histórico antes de planejar novo sync; não presumir caminhos de um
monorepo antigo. Este documento não autoriza publicação.

## Preparar e medir impacto

1. Confira remotes e SHA de `origin/main`, `upstream/main` e checkout local.
   Configure `upstream` para `https://github.com/HKUDS/nanobot.git` somente
   se ainda não existir; não sobrescreva outro remote. Anote a faixa de
   commits e o diff de arquivos entre os dois heads. Nunca faça merge sobre
   a árvore suja: em especial preserve `.positronic/` e quaisquer assets SPA
   deletados/alterados localmente; use checkout de trabalho separado.
2. Revise mudanças upstream em CLI, KG, autenticação do gateway, build Hatch,
   política de paths, `pyproject.toml`, WebUI/TUI e tests. Compare
   `docs/plans/kg-integration-plan.md`,
   [ADR KG](docs/Decisions/2026-10-06-native-kg-operations.md) e
   [migração KG](docs/kg-migration.md). Registre conflitos de contrato e
   gates afetados **antes** do merge.
3. Faça fetch e ensaie merge em branch temporária baseada no `main` atual;
   não rebase commits publicados nem use `-X theirs/ours` como substituto de
   revisão de conflitos. Preserve novos comportamentos upstream e reaplique
   deliberadamente as customizações Percival. Revalide a faixa completa.

```bash
git status --short --branch
git remote -v
git fetch upstream
git log --oneline HEAD..upstream/main
git log --oneline upstream/main..HEAD
git switch -c chore/preview-upstream-YYYYMMDD main
git merge --no-commit --no-ff upstream/main
```

Se houver conflito, resolva com comparação por arquivo e teste; não crie
commit/push sem solicitação específica. Se o merge não fizer sentido, pare o
ensaio e replaneje. Ao retomar o trabalho no branch principal, leve apenas
mudanças revisadas. Atualize o plano e o relatório de execução com SHAs,
decisões e evidências.

## Verificação após o merge

- `uv run --no-sync pytest`, `uv run --no-sync basedpyright nanobot`,
  `uv run --no-sync ruff check .` (não rodar `ruff format`).
- Em `~/Projects/spa`: `bun run test`, `bun run lint`, `bun run build` quando
  transporte/API/schema/assets mudarem. Testar bootstrap, WS autenticado,
  leitura CM/AK, GraphData e rotas SPA no listener real.
- Build isolado do sdist e wheel, instalação limpa e hashes da licença/vendor,
  12 skills e snapshot SPA. Use
  [workflow de atualização](docs/kg-snapshot-workflow.md) e não sobrescreva
  artefatos de fonte dirty como se fossem reprodutíveis.
- Teste migração e rollback em cópias com writers isolados quando mudar schema
  ou core; confira o guia [KG](docs/kg-migration.md).
- CI, contrato de TUI/WebUI e release upstream em
  [`docs/releasing.md`](docs/releasing.md). Um merge validado em Linux não
  prova Windows/macOS nem autoriza tag ou deploy.
