# RUNBOOK — Sincronizando o fork com o upstream

> **Escopo:** procedimentos operacionais para manter o fork `bill-kopp-ai-dev/nanobot`
> em sincronia com o upstream `HKUDS/nanobot`, mantendo a branch `feat/percival-branding`
> viva como linha de customização cumulativa.
>
> **Última atualização:** 2026-08-01.

---

## 0. Política de branches (regra fixa)

> **Todos os push em `docker/nanobot` (este fork) vão para branches de feature, nunca para `main`.**
> **O repo `mcp-servers-percival` (repo pai, escopo mais amplo) continua recebendo push em `main` como padrão.**

- **`main` deste fork** = espelha o upstream, recebe apenas `fetch + merge` do `upstream/main`.
- **`feat/*`** (e.g. `feat/percival-branding`) = linhas de customização. **Nunca** mergeadas em `main` por enquanto.
- **Customizações cumulativas** (P8, P9, P10, ...) entram como **novas branches de feature** ou como **commits adicionais** na branch `feat/percival-branding` — decisão a tomar com o time à medida que o escopo crescer.

Razão: preservar o "diff cirúrgico" e tornar o merge com upstream trivial.

---

## 1. Configuração inicial (já feita)

Adicionar o remote `upstream` (uma vez por clone):

```bash
cd docker/nanobot
git remote add upstream https://github.com/HKUDS/nanobot.git
git fetch upstream
```

Resultado esperado:

```
origin    https://github.com/bill-kopp-ai-dev/nanobot.git (fetch/push)
upstream  https://github.com/HKUDS/nanobot.git (fetch/push)
```

---

## 2. Sincronizar `main` do fork com o upstream

Quando o `HKUDS/nanobot` lançar novos commits e você quiser trazê-los:

```bash
cd docker/nanobot
git fetch upstream
git checkout main
git merge upstream/main
git push origin main
```

> **Atenção:** `main` deve continuar sendo um espelho próximo do upstream. Se aparecer
> conflito aqui, **algo entrou errado** — investigue antes de prosseguir.

---

## 3. Atualizar a branch de customização

A branch `feat/percival-branding` (e futuras) precisa absorver as mudanças do `main`
periodicamente. **Use merge, não rebase** (preserva histórico, evita reescrita de SHA,
simplifica o trabalho com submódulos).

```bash
cd docker/nanobot
git checkout feat/percival-branding
git merge main
# resolver conflitos — esperados em:
#   webui/public/brand/*
#   webui/src/main.tsx (import)
#   webui/src/components/Sidebar.tsx (região do NavItem / rodapé)
git push origin feat/percival-branding
```

> **Por que merge e não rebase?** Squash e rebase reescrevem SHAs, o que confunde o
> ponteiro do submodule em `mcp-servers-percival`. Merge preserva o histórico e mantém
> o submodule consistente.

---

## 4. Quando o upstream reescrever um arquivo que customizamos

Backup antes de mexer:

```bash
cd docker/nanobot
cp webui/src/components/Sidebar.tsx webui/src/components/Sidebar.tsx.bak
git merge main
# revisar diff, reaplicar manualmente as mudanças do percival:
#   - esconder "Settings"
#   - link "Knowledge Graph" com URL resolvida
git add webui/src/components/Sidebar.tsx
git diff --cached
git commit
git push origin feat/percival-branding
```

Idem para `webui/src/main.tsx` (import do `percival-overrides.css`) e
`webui/public/brand/*` (assets).

---

## 5. Atualizar o ponteiro do submodule no repo pai

> **Política:** o repo `mcp-servers-percival` (pai) continua com push em `main`.
> Atualizar o ponteiro do submodule é uma operação **do repo pai**, não deste fork.

```bash
cd /home/bill/Codes/mcp-servers-percival
git checkout main
git submodule update --remote docker/nanobot
git status
git diff docker/nanobot
git add docker/nanobot
git commit -m "chore(nanobot): point submodule at feat/percival-branding"
git push origin main
```

> **Quando rodar?** Somente quando a branch `feat/percival-branding` (ou a branch
> equivalente da vez) estiver **publicada e estável** no fork — i.e., após o
> `git push origin feat/percival-branding` do passo 3.

---

## 6. Comandos úteis de diagnóstico

```bash
# Estado do fork vs upstream
git fetch upstream
git log --oneline HEAD..upstream/main       # commits upstream ainda não aplicados
git log --oneline upstream/main..HEAD       # commits locais ahead do upstream

# Estado vs origin
git fetch origin
git log --oneline HEAD..origin/main
git log --oneline origin/main..HEAD

# Confirmar em qual branch estamos
git rev-parse --abbrev-ref HEAD

# Verificar remotes
git remote -v
```

---

## 7. Política de tags e releases

A definir com o time. Sugestão:

- **Não** criar tags neste fork até que a estratégia de "merge ou não em main" esteja
  fechada.
- Quando fechar, usar semver: `v0.1.0-kg-graph` (P8), `v0.2.0-...` (próxima).

---

## 8. Política de contribuição externa

A definir. Se você receber PRs de colaboradores externos no fork:

- PR contra `main` upstream → não aceita aqui.
- PR contra `feat/percival-branding` → revisar e merge local.

---

## 9. Resumo da arquitetura de branches

```
upstream/main   o---o---o---o---o---o          (HKUDS/nanobot)
                   \
origin/main       o---o---o---o---o---o        (mirror, recebe só fetch+merge de upstream)
                       \
origin/feat/percival-branding \---a---b---c---d   (customizações cumulativas, P8...)
```

**Regras:**

- `origin/main` ↔ `upstream/main` mantém-se em sincronia (passo 2).
- `feat/percival-branding` absorve `main` periodicamente (passo 3).
- Submodule em `mcp-servers-percival` aponta para SHA de `feat/percival-branding` (passo 5).
- **Push em `main` do fork está explicitamente fora de escopo** — qualquer mudança do
  percival entra na branch de feature.
