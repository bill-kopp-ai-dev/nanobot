# RUNBOOK — incorporar melhorias selecionadas do HKUDS/nanobot ao Percival

**Revisão:** 2026-10-06. Política B10/B11:
[governança do Percival](docs/percival-governance.md). Percival não mantém
`main` como espelho do upstream. Desenvolvimento permanece no repositório
privado até o operador aprovar um repositório público separado. Este runbook
não autoriza push, PR upstream nem publicação.

## Triagem mensal (e extraordinária para correções urgentes)

1. Confira `git status`, remotes, revisão do Percival e última revisão
   upstream triada. O checkout atual tem somente `origin`; configure
   `upstream` para `https://github.com/HKUDS/nanobot.git` se necessário,
   sem sobrescrever remotes. Faça `fetch` e anote SHAs/tags; não presuma que
   a versão upstream é compatível com a atual.
2. Revise release notes, advisories e diferenças relevantes em CLI, gateway,
   segurança, build, configuração, WebUI/TUI e testes. Compare contratos
   específicos do Percival, especialmente KG, memória, SPA e MCP-in-Docker.
   Registre para cada candidata: origem (SHA/release), licença, motivo,
   decisão (importar/adiar/rejeitar), conflitos e gates afetados.
3. Faça alterações apenas em branch/worktree de integração com árvore limpa,
   preservando `.positronic/` e trabalho local. Prefira `cherry-pick` ou
   patch de commits isolados, com adaptação explícita; não rebaseie `main`
   publicado. Um merge amplo é exceção justificada por análise prévia de
   conflitos, custo e revalidação completa.

```bash
git status --short --branch
git remote -v
# Só se o remote ainda não existir:
# git remote add upstream https://github.com/HKUDS/nanobot.git
git fetch upstream
git log --oneline -n 50 upstream/main  # Compare com o ultimo SHA triado registrado
git switch -c chore/upstream-select-YYYYMMDD main
# Revise cada commit antes de importar; exemplo para um commit escolhido:
# git cherry-pick -x <sha-upstream>
```

Se um commit não for separável, aplique a mudança por patch revisado,
citando a origem. Se houver conflito de contrato, pare e decida como adaptar
antes de continuar; não use `-X theirs/ours` como atalho. Integre em `main`
após revisão e testes aplicáveis. PR para HKUDS só para correção genérica
separável e com aprovação do operador para divulgar. Documente SHAs,
diferenças de comportamento e evidência da revisão.

## Verificação após a importação

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
- CI do Percival, contrato de TUI/WebUI e release em
  [`docs/releasing.md`](docs/releasing.md). Rode checks afetados na branch;
  antes da tag, rode o gate completo no commit exato. O CI herdado ainda
  contém jobs Windows e precisa ser reconciliado com a política Linux-only;
  um sync validado localmente não autoriza tag ou deploy.
