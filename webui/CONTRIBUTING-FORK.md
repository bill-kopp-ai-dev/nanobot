# Contribuindo no fork `feat/percival-branding`

Documento de referência para a branch `feat/percival-branding` do `agent-docker/nanobot`,
a webui customizada do Percival. Cobre:

- O que foi alterado em relação à `nanobot/webui` upstream (HKUDS/nanobot).
- Pontos de atrito para **mesclar mudanças upstream no nosso fork** no futuro.
- Convenções para **adicionar patches novos** sem inflar o diff.

> Última atualização: 2026-08-02.
> Branch: `feat/percival-branding` (no remote do submodule).
> Estado: pós-rebrand P8 etapas 1–7 + revisão visual/funcional de 2026-08-02.

---

## 1. Filosofia do fork

A webui vive como **submodule** de `agent-docker/mcp_servers/spa/percival` apontando
para https://github.com/bill-kopp-ai-dev/nanobot.git, branch `feat/percival-branding`.
A upstream é `git://github.com/HKUDS/nanobot.git` (remote `upstream`).

**Dois princípios guiam todas as mudanças neste fork:**

1. **Diff mínimo com upstream.** Preferimos composição **por fora** da Sidebar
   (wrapper `PercivalSidebar`) a patch direto em `Sidebar.tsx`. Toda alteração
   no upstream deve entrar com o menor atrito possível.
2. **Cobertura de testes máxima na borda.** Patches visuais/funcionais devem
   trazer regressões automáticas em `*.test.tsx` — jsdom não calcula layout,
   mas checa estrutura/classe/ordem do DOM que, combinados com smoke visual
   manual, seguram 100% dos bugs já vistos.

Quando esses dois princípios entrarem em tensão com um requisito novo, **abrir
PR descrevendo o trade-off antes de fazer o patch** — decisões historicamente
discutidas (B1, B2, B4, G2-AltB) ficam em
`agent-docker/mcp_servers/MCP_Docs/percival-collective-memory-Docs/plans/`.

---

## 2. Inventário de patches por categoria

Esta seção lista **cada arquivo modificado** entre a base `2cb6fd1c` e o HEAD
da branch, agrupado por intenção. O diff cumulativo está em
`git diff 2cb6fd1c..HEAD -- webui/`.

### 2.1. Rebrand textual (P8 etapa 6)

Arquivo: [`webui/src/tests/rebranding-textual.test.ts`](src/tests/rebranding-textual.test.ts) (regressão) + dezenas de arquivos em `webui/src/` que
continham `nanobot` / `Nanobot` em texto visível ao usuário.

- **Substituído** (regra atual da P8 etapa 6): `nanobot` → `percival`,
  `Nanobot` → `Percival` em **todo texto visível** (títulos, aria-labels,
  descrições, mensagens, tooltips, índices OpenGraph, placeholders).
- **NÃO substituído** (preservação de chaves técnicas — decisão A1 do plano):
  `localStorage` keys (`nanobot-webui.theme`, `nanobot.locale`),
  identificadores de classe do Tailwind, nomes de arquivos binários
  (`nanobot_mark.svg`, `nanobot_icon.png` etc — dec A2).
- **Teste**: `rebranding-textual.test.ts` faz walker recursivo em `*.tsx`
  + `index.html` e garante zero `nanobot` visível e zero refs quebradas
  às constantes técnicas preservadas. **Atualizar este teste ao adicionar
  uma nova string do usuário.**

Quando mesclar upstream que adiciona strings contendo `nanobot`/`Nanobot`:
rodar `bun run test src/tests/rebranding-textual.test.ts`. Se quebrar,
aplicar a substituição **manualmente** (decisão humana: o que é
texto visível vs chave técnica).

### 2.2. Logo do header da sidebar

Arquivo: [`webui/src/components/Sidebar.tsx`](src/components/Sidebar.tsx) (linha 109–128).

- `src`: `/brand/nanobot_mark.svg` → `/brand/nanobot_icon.png`.
- Wrapper: `h-9 w-9` (36px) → `h-20 w-20` (80px).
- Imagem: `h-8 w-8` (32px) → `h-19 w-19` (76px).
- Arquivo físico [`webui/public/brand/nanobot_mark.svg`](public/brand/nanobot_mark.svg) substituído por uma versão nova (viewBox 192×192, marca percival). **md5sum
  bate com** `New_logos/percival_icon.png` por design.
- Documentação: [`webui/public/brand/ASSETS-SPEC.md`](public/brand/ASSETS-SPEC.md)
  marca `nanobot_icon.png` como referenciado em `Sidebar.tsx:117`.

**Trade-off conhecido (etapa 9 pendente)**: o SVG não foi regenerado para
a marca nova (só PNG). Quando entrarem SVG vetoriais, voltar `<img
src=...svg>` é trivial; o PNG continua útil para apple-touch-icon e
future hardware que precise de bitmap.

**Risco em merge:** upstream pode mexer no `Sidebar.tsx` (incluindo o
botão do header). Se preservarem o `<img>` com mesma estrutura visual,
nosso patch cai automaticamente; se mudarem pra outro componente (ex
`Avatar`, `Logo`), re-alinhar o `src`/tamanho.

### 2.3. Wrapper `PercivalSidebar` (overlay sem patch em Sidebar)

Arquivo: [`webui/src/components/percival/PercivalSidebar.tsx`](src/components/percival/PercivalSidebar.tsx).

Adota `<UpstreamSidebar>` como filho e adiciona um **slot externo**
(`data-testid="external-cards-slot"`) absolutamente posicionado em
`bottom-[60px]`, que renderiza:

- **Modo expandido (>= 57px largura)**:
  1. `ExternalSidebarCard` para KG (ícone `Network`, URL via `resolveKgInterfaceUrl()`).
  2. `ExternalSidebarCard` para Positronic Bean (ícone `Sprout`,
     URL via `resolvePositronicBeanUrl()`).

- **Modo collapsed (rail de 56px)**:
  1. KG icon-only (quadrado 32×32 com `Network`).
  2. Positronic Bean **omitido** (não cabe no rail).

`ExternalSidebarCard` é um sub-componente interno parametrizado por
`href` / `label` / `Icon` (tipado `LucideIcon`). Quando adicionar um
novo botão externo, **estenda este componente** em vez de duplicar markup.

**Padrão de uso upstream:** `App.tsx` (do nanobot) instancia `<Sidebar />`
diretamente. No nosso fork substituímos por `<PercivalSidebar />` no(s)
mesmo(s) call site(s). Conferir em `git grep "PercivalSidebar\|<Sidebar"`
no merge para garantir que o call site foi atualizado.

### 2.4. Helpers de URL

Arquivos:
- [`webui/src/lib/kg-interface.ts`](src/lib/kg-interface.ts) — `resolveKgInterfaceUrl()`.
- [`webui/src/lib/positronic-bean.ts`](src/lib/positronic-bean.ts) — `resolvePositronicBeanUrl()`.

Ambos seguem o mesmo padrão (decisão B1 do P8): build-time env var
`VITE_*` com fallback para constantes embutidas. Detalhes em
`kg-interface.ts`'s header comment.

**Diferenças semânticas:**
- KG default é **`/kg-interface/`** (relativo) — funciona em produção
  porque o Caddy do P10 serve SPA + adapters no mesmo origin.
- Positronic Bean default é **`https://labs.positronicbean.com`**
  (absoluto) — site público, não roda no origin da webui.

Ambos têm **detecção em runtime** pra porta do dev server (webui na
5173 → aponta pra SPA dev em 5174) só no `kg-interface.ts`; Positronic
Bean não precisa porque é URL absoluta fixa.

**Testes:** `src/tests/kg-interface.test.ts` (9 casos) e
`src/tests/positronic-bean.test.ts` (3 casos). Cobertura dos 3 níveis
do helper e do fallback de runtime.

### 2.5. Footer alignment (Sidebar.tsx + PercivalSidebar.tsx)

Arquivo: [`webui/src/components/Sidebar.tsx`](src/components/Sidebar.tsx) (linha 237).

- Footer `px-2.5` → `px-3` para alinhar com o `px-3` externo do slot
  de cards. Resolve desalinhamento visual de 2px entre a borda do
  `<a>` Settings e a borda dos cards externos KG/Positronic Bean.

Esse patch **não afeta layout do upstream sozinho** — só fica visível
em conjunto com o slot do `PercivalSidebar`. Se um merge upstream mexer
no footer (cores, items), revalidar o `px-3`.

### 2.6. i18n

Arquivos: [`webui/src/i18n/locales/*/common.json`](src/i18n/locales/)
(10 locales) + testes correspondentes.

**Chaves adicionadas em 2026-08-02:**
- `sidebar.positronicBean` em todos os 10 locales, com valor literal
  `"Positronic Bean"` (nome próprio, mantido idêntico em todos).

**Convenção:** nomes próprios (empresas, marcas, produtos) NÃO são
traduzidos — o valor permanece o mesmo em todos os locales, alinhado
com a decisão do P8 etapa 6 que mantém `percival` literal em todos.

Quando adicionar uma nova chave:
1. Adicionar **em todos os 10 locales** simultaneamente.
2. Adicionar teste em `src/tests/i18n-<nome>.test.ts` (mesmo padrão do
   `i18n-knowledge-graph.test.ts`).
3. Se for nome próprio, adicionar assertion extra do valor literal.

Locales suportados: `en, es, fr, id, ja, ko, pt-BR, vi, zh-CN, zh-TW`.

### 2.7. Configuração e tooling

- [`webui/tsconfig.json`](tsconfig.json): `"vite/client"` adicionado em
  `types` (o `tsconfig.build.json` já tinha). Necessário para tipar
  `import.meta.env` corretamente e eliminar o erro TS "Property 'env'
  does not exist on type 'ImportMeta'" no IDE/tsc.
- [`webui/.env.development`](.env.development) (novo): `VITE_KG_INTERFACE_URL=
  http://localhost:5174/`. Não comitar mudanças no `.env.development`
  sem justificativa — é por-dev, sobrescrevível.
- [`webui/.gitignore`](.gitignore): exceção `!.env.development` adicionada
  (debaixo da regra geral `!.env.example`).
- [`webui/package.json`](package.json): script `build:dev-kg` adicionado
  para embutir a env var de dev no bundle de prod local (cobre o caso
  `gateway :8765` que não dispara o fallback de runtime).
- [`webui/README.md`](README.md) §4a: instruções de dev local, fallback
  de runtime, e quando usar `build:dev-kg`.

**Atenção:** ao adicionar scripts novos em `package.json`, NÃO usar
nomes que colidam com `dev`, `build`, `preview`, `test`, `test:watch`,
`lint` — esses são do upstream e merge vai dar conflito de propósito.

### 2.8. Cobertura de testes

Arquivos adicionados/expandidos:

- [`src/tests/percival-branding.test.tsx`](src/tests/percival-branding.test.tsx)
  (14 testes) — cobre: clipping do slot, centralização, fallback rail,
  href, target/rel, ordem no DOM, KG icon-only, Positronic Bean
  presente/omitido.
- [`src/tests/i18n-knowledge-graph.test.ts`](src/tests/i18n-knowledge-graph.test.ts)
  — `sidebar.knowledgeGraph` em todos os locales.
- [`src/tests/i18n-positronic-bean.test.ts`](src/tests/i18n-positronic-bean.test.ts)
  (novo) — `sidebar.positronicBean` em todos os locales + assertion de
  nome próprio.
- [`src/tests/kg-interface.test.ts`](src/tests/kg-interface.test.ts)
  (9 testes) — 3 níveis de resolução do helper + fallback runtime +
  env var sobrescreve detecção.
- [`src/tests/positronic-bean.test.ts`](src/tests/positronic-bean.test.ts)
  (novo, 3 testes) — helper Positronic Bean (default, override, sem
  coerção).

**Suíte total**: 1007 testes em 58 arquivos (estado em 2026-08-02).

---

## 3. Pontos de atrito pra merges futuros

Tabela de risco estimado por arquivo quando `git pull upstream main`:
**Alto** = vai dar conflito com certeza; **Médio** = provável; **Baixo**
= raramente dá conflito (touch apenas se reescrita ampla).

| Arquivo (path relativo a `webui/`) | Risco | Conflito típico | Ação recomendada |
|---|---|---|---|
| `src/components/Sidebar.tsx` | **Alto** | patch nosso no logo wrapper + footer `px-3` vs upstream reescrevendo o mesmo `<button>`/`<div>` do header/footer | Compare char-a-char na hora; reaplicar `(1)` troca do `src` + sizes no botão de logo, `(2)` mudança de `px-3` no footer. **Não** tentar portar via tooling — diff é cirúrgico. |
| `src/components/percival/PercivalSidebar.tsx` | **Baixo** | (arquivo não existe no upstream) | Se upstream criar algo similar, manter os dois até consolidar. Senão, merge limpo. |
| `src/lib/kg-interface.ts` | **Baixo** | (arquivo nosso — upstream não tem) | Merge limpo. |
| `src/lib/positronic-bean.ts` | **Baixo** | (arquivo nosso) | Merge limpo. |
| `src/i18n/locales/*/common.json` | **Alto** | adicionamos `sidebar.positronicBean` em todos os 10; upstream pode adicionar outras chaves no mesmo arquivo | `git diff --check` em todos os 10 arquivos. Resolver manualmente (JSON simples, sem reordenação). Se upstream reordenar as chaves, manter ordem alfabética upstream e adicionar o nosso no fim. |
| `src/tests/percival-branding.test.tsx` | **Médio** | testes dependem de strings dos locales e do `data-testid` do slot — se upstream renomear `data-testid` (`kg-card-slot` → `external-cards-slot` foi nosso) ou mudar a i18n, precisamos atualizar | Re-verificar `data-testid` e referências textuais após merge. |
| `src/tests/i18n-knowledge-graph.test.ts`, `i18n-positronic-bean.test.ts` | **Baixo** | merge limpa a menos que upstream adicione novos locales | Atualizar lista `supportedLocales` se houver. |
| `tsconfig.json` (`vite/client` em `types`) | **Médio** | upstream pode reorganizar `types` re-ordenando nossa entrada | Garantir que `"vite/client"` permanece presente — tipar `import.meta.env` é o motivo. |
| `package.json` (script `build:dev-kg`) | **Médio** | conflito de string se upstream reorganizar scripts | Manter script no fim do bloco `scripts`. Se colidir de nome, renomear para `build:with-dev-kg-url`. |
| `.gitignore` | **Baixo** | exceção `!.env.development` na linha debaixo de `!.env.example` | Verificar que ambas exceções permanecem. |
| `src/tests/rebranding-textual.test.ts` | **Alto** | walker pode quebrar se upstream adicionar arquivos em `webui/src/` que ainda falam de `nanobot` (ex: comentários, JSDoc) | Rodar teste após merge; aplicar decisão humana (texto visível vs chave técnica). Se quebrar, ajustar o teste OU o código, justificar no PR. |
| `public/brand/nanobot_mark.svg` | **Baixo** | upstream tem o mesmo nome, mas o conteúdo é diferente (era nanobot, agora é percival) | Cuidado: `git pull` pode sobrescrever. Se isso acontecer, o wrapper recupera o logo antigo — corrigir com `git checkout HEAD@{1} -- public/brand/nanobot_mark.svg` ou re-aplicar o conteúdo correto. |
| `public/brand/nanobot_icon.png`, `nanobot_favicon_32.png`, `nanobot_apple_touch.png`, `nanobot_logo.png`, `nanobot_logo.webp` | **Baixo** | mesma situação da `mark.svg` (decisão A2 — nomes preservados, conteúdo substituído) | Mesmo cuidado. |

---

## 4. Procedimento de merge com upstream

```bash
# Workspace no submodule agent-docker/nanobot
git checkout feat/percival-branding
git fetch upstream main

# Merge (não rebase, para preservar histórico do fork)
git merge upstream/main --no-ff -m "merge upstream/main into feat/percival-branding (YYYY-MM-DD)"
```

**Após o merge:**

```bash
cd webui
bun install     # se package.json mudou
bun run test    # suíte completa — DEVE passar (1007+) antes de commitar
bun run lint
bun run build   # garante que a compilação TypeScript funciona
```

**Checklist obrigatório:**

- [ ] `rebranding-textual.test.ts` continua passando (ou tem justificativa
      documentada pra cada nova menção de `nanobot` que apareceu).
- [ ] `percival-branding.test.tsx` continua passando. Se quebrar, ler o
      diff do upstream — provavelmente mudou o DOM esperado e atualizamos
      o teste (não o wrapper) pra refletir a nova estrutura.
- [ ] `tsconfig.json` mantém `"vite/client"` em `types`.
- [ ] Nenhum dos nossos arquivos novos (`positronic-bean.ts`,
      `PercivalSidebar.tsx`, testes relacionados) foi deletado acidentalmente.
- [ ] `package.json` mantém o script `build:dev-kg` e não colidiu de nome.
- [ ] `ASSETS-SPEC.md` continua coerente (se upstream tocar na pasta
      `brand/`, revalidar nomes referenciados).

**Conflitos esperados e como resolvê-los:**

| Onde | Como |
|---|---|
| `Sidebar.tsx` (header wrapper) | Reaplicar nossos 2-3 patches: `src` do `<img>`, classes `h-*`/`w-*`. NÃO aceitar a versão upstream sem re-aplicar, ou o logo volta pequeno/SVG antigo. |
| `Sidebar.tsx` (footer) | Manter o `px-3` que aplicamos; rejeitar `px-2.5` do upstream se for essa a versão deles. |
| `i18n/locales/*/common.json` | Aceitar upstream + re-adicionar `sidebar.positronicBean` no fim de cada um. Se upstream já tem essa chave, manter a versão deles (deve bater). |
| `tests/rebranding-textual.test.ts` | Aceitar upstream + auditar manualmente quais strings o teste novo pega. Aplicar rebrand onde for texto visível. |

---

## 5. Como adicionar um novo botão no slot externo

Template (adicionar **dentro do `<div data-testid="external-cards-slot"
...>` em `PercivalSidebar.tsx`**, dentro do `!collapsed`):

```tsx
{!collapsed && (
  <ExternalSidebarCard
    href={resolveNovaUrl()}
    label={t("sidebar.novaFeature")}
    Icon={NovaIcon}  // escolha um Lucide-react distinto do Network/Sprout
  />
)}
```

Se for expandir o rail (collapsed) também:

```tsx
{collapsed && (
  <a
    href={resolveNovaUrl()}
    target="_blank"
    rel="noopener noreferrer"
    aria-label={t("sidebar.novaFeature")}
    title={t("sidebar.novaFeature")}
    className="pointer-events-auto grid h-8 w-8 place-items-center rounded-lg text-sidebar-foreground hover:bg-sidebar-accent/75 transition-colors duration-200 ease-out focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/40"
  >
    <NovaIcon className="h-4 w-4" aria-hidden />
  </a>
)}
```

**E criar:**

1. Helper `webui/src/lib/nova-feature.ts`:
   ```ts
   export const DEFAULT_NOVA_FEATURE_URL = "https://..." as const;
   export function resolveNovaFeatureUrl(): string {
     return import.meta.env.VITE_NOVA_FEATURE_URL ?? DEFAULT_NOVA_FEATURE_URL;
   }
   ```

2. Chave i18n `sidebar.novaFeature` em **todos os 10 locales**
   (ver §2.6 sobre nome próprio).

3. Testes (`src/tests/i18n-nova-feature.test.ts`,
   `src/tests/nova-feature.test.ts`).

4. Adicionar 1 caso em `percival-branding.test.tsx`
   validando que o link está dentro do `external-cards-slot`.

**Atenção:** mantenha a ordem de empilhamento consistente com a
hierarquia visual desejada (KG primeiro, depois links de produto/empresa,
depois links de comunidade, etc.). Não ordene por data de criação.

---

## 6. Convenções gerais

### 6.1. Comentários `// PERCIVAL:`

Toda alteração não-trivial do fork traz um bloco `// PERCIVAL:` no topo
do arquivo ou perto da mudança explicando **por que** diverge do upstream.
Isso é o "manual de instruções" pra quem for revisar um PR de merge
no futuro.

Mantenha o `PERCIVAL:` curto: **o que mudou** + **por que** + referência
à decisão do plano se houver (B1, B2-2, G2-AltB).

### 6.2. Sem `git push --force`

A branch `feat/percival-branding` é compartilhada. Force-push reescreve
histórico dos colaboradores. Em emergências, usar `git push --force-with-lease`
e avisar no canal.

### 6.3. Não tocar `Sidebar.tsx upstream` sem checklist

Qualquer patch direto em `Sidebar.tsx` (vs compor por fora) é uma
exceção à filosofia §1. Abrir PR com: justificativa + diff mínimo + teste
regressivo + entrada na tabela §3.

### 6.4. Teste antes do commit

```bash
bun run test       # suíte completa (deve passar 1000+)
bun run lint       # sem warnings
bun run build      # bundle deve ser gerado em ../nanobot/web/dist
```

Não commitar se algo estiver vermelho.

---

## 7. Histórico de mudanças neste fork

| Data | Hash | Descrição |
|---|---|---|
| 2026-07-31 | `b2989a7` et al | P8 etapas 1-5: KG link textual rebrand (ver `git log --oneline 2cb6fd1c^..d5673cfd~1`) |
| 2026-08-01 | `d5673cfd` | substituído SVG mark por PNG percival 192×192 (ASSETS-SPEC.md etapa 7) |
| 2026-08-02 | `ec673342` | card KG elegante acima de Settings (dec B2) |
| 2026-08-02 | `a8f37e39` | runtime KG URL detection + dev/prod env handling (dec B1 refactor) |
| 2026-08-02 | `f1ba7bca` | trocar mark SVG por icon PNG 192×192 e crescer 32→36px |
| 2026-08-02 | `2d26105f` | grow sidebar logo to h-20 w-20 |
| 2026-08-02 | `41c54a45` | 2º card externo "Positronic Bean" abaixo do KG (dec B2-2) |
| 2026-08-02 | `18b9c42f` | alinhar Settings com cards externos + unificar ordem no rail |

Para o histórico completo desta branch desde o fork inicial:

```bash
git log --oneline 2cb6fd1c^..HEAD
```

---

## 8. Contatos / referências

- Plano P8 completo: `agent-docker/mcp_servers/MCP_Docs/percival-collective-memory-Docs/plans/`.
- Decisões históricas (B1, B2, B4, G2-AltB): ver índice em
  `agent-docker/mcp_servers/MCP_Docs/percival-collective-memory-Docs/plans/P8-decisions-2026-08-01.md`.
- Upstream remoto: `https://github.com/HKUDS/nanobot`.
- Branch remoto fork: `https://github.com/bill-kopp-ai-dev/nanobot/tree/feat/percival-branding`.
