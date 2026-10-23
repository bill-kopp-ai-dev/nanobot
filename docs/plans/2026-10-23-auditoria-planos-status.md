# Auditoria de planos — status de conclusão

- **Data:** 2026-10-23.
- **Escopo:** os 9 documentos em `docs/plans/` (nenhum já arquivado; `closed/` estava vazia).
- **Método:** para cada plano, as fases/gates explícitos do próprio documento foram
  pontuados como **concluído** (100), **implementado com gate aberto** (55–75, conforme
  o que resta ser local ou depender de terceiro), **parcial** (30–50) ou **não iniciado**
  (0–20). A média é a estimativa de conclusão. Verificações de código foram feitas onde o
  plano afirmava implementação; o estado declarado nos próprios documentos foi aceitado
  quando confirmado por relatório de execução versionado.
- **Aviso:** porcentagem alta **não** equivale a plano concluído. Três documentos proíbem
  explicitamente declarar-se fechados antes de gates externos (Actions, Engine 27.x, VPS).

## Situação consolidada

| Grupo | Critério | Planos | Leitura |
| --- | --- | --- | --- |
| 1 | > 90% | 1 (arquivado) | código pronto; falta só evidência de aceite externo |
| 2 | > 50% e <= 90% | 5 | núcleo implementado; falta evidência de aceite e/ou gates externos |
| 3 | < 50% | 3 | planos de execução ainda não rodados ou quase nada executado |

**Atualização 2026-10-23 (pós-auditoria):** cinco planos foram arquivados em
[`closed/`](closed/) e as suas pendências consolidadas em dois documentos ativos:

- [Plano de senha única](closed/2026-10-11-percival-single-password-auth-refactor-plan.md) →
  pendências no [fechamento de senha única](2026-10-11-single-password-acceptance-closure-plan.md) §1.2 (itens A1–A9).
- [KG integração](closed/kg-integration-plan.md), [KG runtime recovery](closed/2026-10-11-kg-runtime-recovery-and-product-fix-plan.md),
  [MCP Docker first-class](closed/2026-10-06-mcp-docker-first-class-execution-plan.md) e
  [MCP Docker UI/service](closed/2026-10-08-mcp-docker-ui-service-refactor-plan.md) →
  pendências no [plano integrado](2026-10-23-integracao-pendencias-kg-e-mcp-docker-plan.md) (itens A1–A7, B1–B7, C1–C4).
- [F4/F5 closure](closed/2026-10-10-f4-f5-closure-plan.md) e
  [F7 closure](closed/2026-10-10-f7-operations-acceptance-closure-plan.md) → fundidos no
  [fechamento da padronização Docker F4/F5/F7](2026-10-23-fechamento-padronizacao-docker-f4-f5-f7-plan.md)
  (itens D1–D12); os passos de Actions e VPS migraram para C1–C4 do plano integrado, de modo que
  cada gate tem um único dono.

O achado 1 foi resolvido com `!docs/plans/closed/` no `.gitignore` e os links relativos dos
arquivados foram corrigidos. O achado 3 (gates órfãos) foi parcialmente resolvido pela
consolidação; permanecem abertos os itens de padronização F4/F5/F7/F8, que continuam nos seus
planos. O achado 4 segue aberto.

---

## Grupo 1 — mais de 90%

### `2026-10-11-percival-single-password-auth-refactor-plan.md` — ~92% **(arquivado em `closed/`)**

| Etapa (A–F) | Estado |
| --- | --- |
| A. Contrato compartilhado | concluída |
| B. Núcleo gateway (login, sessões, rate limit, revogação) | concluída |
| C. Administração MCP por elevação | concluída |
| D. Clientes (WebUI, TUI, onboard, SSH) | concluída |
| E. Empacotamento e documentação | concluída |
| F. Validação única final | parcial (~55%) |

**Evidência:** `9348 passed, 49 skipped` em `pytest`; `basedpyright nanobot` 0 erros;
`ruff check .` limpo; SPA `251 passed`, lint e build; snapshot KG reconstruído de worktree
limpo `8e4ff73` com `SOURCE.json dirty=false` (commit `d3b29843`); builds das imagens
gateway e broker; container com senha fixture: bootstrap anônimo `401`, senha errada `401`,
senha correta `200`, GET KG com bearer `200`, e **mesma senha após restart** do contêiner.

**Falta:** (1) ensaio de elevação + mutação MCP + auditoria em **Docker Server 27.x**
(adiado; o broker entrou em restart loop no Engine 29.7.2 local, que não satisfaz o gate);
(2) Actions remotas; (3) inventário/staging em VPS. O próprio plano (§5) exige evidência dos
gates finais antes de marcar implementado. **Em 2026-10-23 estas pendências foram transferidas
para o plano de fechamento de senha única** (§1.2, itens A1–A9), que ganhou etapas novas
P2-B a P2-F para o que não estava coberto: negação de admin remoto (`allowRemoteAdmin=false`),
acesso por proxy TLS representativo, expiração de token e revogação em WebSockets já abertos,
senha criada **e alterada** pelo operador, e cutover da instância real com backup e retorno
preservados.

---

## Grupo 2 — mais de 50% (até 90%)

### [`kg-integration-plan.md`](closed/kg-integration-plan.md) — ~88% *(limítrofe do Grupo 1; **arquivado**)*

| Fase | Estado |
| --- | --- |
| F0 — Fundación/viabilidade | parcial (provas curtas feitas; gate aberto) |
| F1 (4 tools CM) | concluída |
| F2 (15 tools CM) | concluída |
| F3 (1 tool enrich) | concluída |
| F4 (8 tools AK) | parcial — multimodal entregue; `audio_transcribe` retorna `unsupported_capability` |
| F5 (6 tools AK) | concluída |
| F6 — bridge gateway + contrato SPA | concluída |
| F7 — SPA empacotada + GraphView | concluída (proveniência do fork corrigida depois, em `d3b29843`) |
| F8 — CLI `nanobot kg` | concluída |
| F9 — skills, docs, migração, release | parcial — skills/docs/ADR prontos; **D5/D10 não entregues** |

**Falta:** gate de release e compatibilidade com dados reais; paridade do áudio (decisão D12);
proveniência reproduzível do commit limpo do fork (resolvida no plano de senha única);
validação do ensaio B6/B7 em dados reais (depende do operador).

### [`2026-10-11-kg-runtime-recovery-and-product-fix-plan.md`](closed/2026-10-11-kg-runtime-recovery-and-product-fix-plan.md) — ~84% **(*arquivado*)**

| Fase | Estado |
| --- | --- |
| P0 — inventário read-only e contrato | concluída (G0: instalação nova escolhida) |
| P1 — fixture operacional isolada | ~90% (falta browser smoke anônimo do aviso de bundle ausente) |
| P2 — diagnóstico e leitura no gateway | concluída |
| P3 — UX e transporte da SPA | concluída |
| P4 — consistência do artefato após escritas | ~90% (rebuild automático não habilitado: falta benchmark e política de custo) |
| P5 — fonte real, migração/recuperação, cutover | parcial (~60%) — instalação nova executada e `doctor` `ok`, mas **zero notas**; populamento depende de fonte autorizada |
| P6 — validação do candidato e handoff | parcial (~50%) — imagem `29a482ce` construída e containers `healthy`, mas **login humano não foi exercitado** |

**Evidência:** `KgGatewayBridge` diferencia `bundle_uninitialized` de nota ausente;
`/graph` informa `missing|valid|stale|invalid`; fingerprint SHA-256 detecta stale após escrita
sem rebuild no GET; imagem `sha256:d06d8eed…` com label de revisão conferindo; rollback
preservado (snapshot `a2782c48…` + imagem `percival-gateway:pre-kg-29a482ce`).

### [`2026-10-06-mcp-docker-first-class-execution-plan.md`](closed/2026-10-06-mcp-docker-first-class-execution-plan.md) (v1.8) — ~82% **(*arquivado*)**

| Fase | Estado |
| --- | --- |
| F0 — viabilidade/inventário | **fechada** (B24: gate F0 fechado com aceite do risco indireto) |
| F1 — protótipo descartável | **fechada localmente** (B25: aceite expresso do risco medido) |
| F2 — broker próprio tipado | **fechada localmente** (8 famílias, fixtures Weather/OSM, Engine 27.5.1 em daemon descartável) |
| F3 — observabilidade/read | implementada, gate end-to-end aberto (~70%) |
| F4 — página de gestão | implementada, gate end-to-end aberto (~70%) |
| F5 — recovery/CI readiness | implementada; matriz Browser WebUI e topologia VPS abertas (~50%) |

**Falta:** matriz end-to-end F3/F4 em Browser WebUI + gateway + broker reais; execução de
`scripts/percival-vps-inventory.sh` no VPS e anexação do JSON ao relatório F0; ensaio de
migração/rollback `~/.nanobot → .percival`; GitHub Actions verde no SHA candidato; **novo
aceite formal do operador** para o risco do deployment real. O plano diz textualmente:
"Não marcar a capability ou plano totalmente fechado antes desses gates."

### [`2026-10-08-mcp-docker-ui-service-refactor-plan.md`](closed/2026-10-08-mcp-docker-ui-service-refactor-plan.md) — ~80% *(marcado como superado; **arquivado**)*

Itens 1–7 **todos implementados** no código (commit `0475065e`, base `ca9634ae`), incluindo
as proteções de contrato exigidas: `mounts` obrigatório em `configure`
(`service.py:515`/contrato), rejeição de no-op antes de backup/journal e antes de remoção no
broker, bloqueio de `stopped-persistent`, fallback quando o host não anuncia suporte.

**Falta:** o gate **Browser WebUI + gateway + broker** do próprio plano não foi satisfeito — o
smoke `scripts/percival-f2-docker-smoke.sh` roda `tests/mcp_docker/smoke_driver.py`, um driver
CLI, e o próprio relatório admite que isso não fecha o gate; ~10 testes de UI exigidos pelos
critérios de aceite (conflito 409 no install, falha/conflito no editor de host,
`stopped-persistent`, `image-missing`/`container-missing`/"Data outdated", cópia de digest,
senha rejeitada, backup não restaurável, zero backups, viewport estreito); prova de
compatibilidade bidirecional cliente velho/host novo exigida por `.agent/review-guide.md`;
inspeção de teclado/foco em browser.

### `2026-10-09-docker-standardization-refactor-plan.md` — ~68%

| Fase | Estado declarado no plano |
| --- | --- |
| F0 — baseline/inventário | **gate concluído** |
| F1 — correções imediatas (Deep Research, OSM) | **gate concluído em candidatos locais** |
| F2 — contrato de identidade e inventário | implementada, gate aberto (faltam builds canônicos em checkout limpo dos 6 MCPs) |
| F3 — reprodutibilidade/SBOM/scan | **gate fechado** por documentação+triagem; resíduo transferido para a pendência #11 |
| F4 — Compose e contratos de runtime | implementação parcial, gate aberto (falta restore real Notes/Khan) |
| F5 — conformance e CI | workflows commitados e enviados, **nunca executados remotamente** (`gh auth status: not logged into any GitHub hosts`) |
| F6 — migração/cutover | parcial: 6 MCPs ativos nos dois agentes; **rollback não ensaiado** |
| F7 — aceite de operação | parcial: P1 parcial, P2 diagnóstico, P3 manual criado sem walkthrough, P4/P5 bloqueados |
| F8 — skill de gestão e AGENTS.md | não iniciado (bloqueia ativação pelo operador) |

Das 11 pendências da tabela de F7, apenas a #1 está fechada; as #2–#11 seguem abertas, e a #11
(Critical OpenSSH `CVE-2026-60002` no gateway + ausência de Actions remotas) **bloqueia F7 e a
publicação do 0.1.0**.

---

## Grupo 3 — menos de 50%

### `2026-10-11-single-password-acceptance-closure-plan.md` — ~33%

| Etapa | Estado |
| --- | --- |
| P0 — fixar candidatos e fronteiras | concluída |
| P1 — reconstruir snapshot SPA de fonte limpa | concluída (`d3b29843`) |
| P2 — ensaio gateway+broker em Server 27.5.1 | **adiado pelo operador** |
| P3 — GitHub Actions no SHA final | bloqueado (operador precisa autenticar `gh`) |
| P4 — inventário read-only e gate VPS | bloqueado (sem host/staging identificado) |
| P5 — consolidação e handoff | não iniciado |

### [`2026-10-10-f4-f5-closure-plan.md`](closed/2026-10-10-f4-f5-closure-plan.md) — ~15% *(pre-execução; **a execução existe** em [relatório F4/F5](../reports/2026-10-10-f4-f5-closure-report.md); **arquivado**)*

Sequência de 5 passos; nenhum executado. Passo 1 parcial: o literal da senha `operator-admin`
foi removido da versão **local** de três documentos, mas persiste no histórico/remote, sem
rotação nem push. Passos 2–5 (fixture de dados e restore Notes/Khan, rollback nos dois
gestores, execução de CI nos 7 SHAs, fechamento de evidência) não executados.

### [`2026-10-10-f7-operations-acceptance-closure-plan.md`](closed/2026-10-10-f7-operations-acceptance-closure-plan.md) — ~5% *(a marca de supersession estava errada: era o único dono de trabalho vivo; **arquivado**)*

Pacotes P0–P5 (conter credencial, procedência, Khan/duplicatas, manual, runtime/CI, VPS) sem
execução registrada; plano superado pelo de senha única.

---

## Achados da auditoria

1. **~~`docs/plans/closed/` é ignorado pelo git~~ — resolvido em 2026-10-23** com
   `!docs/plans/closed/` no `.gitignore`. Antes de qualquer movimentação é preciso
   `!docs/plans/closed/` no `.gitignore`; a exceção existe e já vale para os planos movidos.
2. **80 links relativos quebrariam na movimentação.** Sete dos nove planos referenciam
   `../reports/...` e dois referenciam `../../AGENTS.md`; um nível a mais de profundidade
   invalida todos eles (`2026-10-09-…`: 37 links; `2026-10-06-…`: 17 + 1). O primeiro
   arquivamento (senha única) tinha apenas 1 link relativo, corrigido para `../`; os demais
   planos ainda exigem essa correção no momento em que forem movidos.
3. **Gates órfãos.** Quatro planos — first-class MCP Docker, UI/service, standardization e F7
   closure — foram marcados `Superseded by` o plano de senha única (commit `a9ad9bf9`). Esse
   plano **não cobre** os gates que eles carregavam (inventário VPS, Engine 27.x, matriz Browser
   WebUI, Actions). Esses gates permanecem abertos sem plano ativo que os possua.
4. **Inconsistência de `.gitignore`.** `2026-10-10-f4-f5-closure-plan.md` está versionado mas
   ausente da lista de exceções (linhas 14–21); sobrevive apenas por já estar rastreado.
5. **Documentação desatualizada.** `docs/reports/2026-10-08-mcp-docker-ui-refactor-execution.md`
   afirma 19 testes em `mcp-containers.test.tsx`; o arquivo atual tem 17 (2 removidos por
   `58d4a193` com o plano de senha única). Obsolescência documental, não lacuna de escopo.

## Encaminhamento recomendado

1. Tratar o grupo 1 como **pronto para aceite**, não para arquivo: o ensaio em Engine 27.x
   (P2 do plano de senha única) é o teste que fecha a maior parte do que falta.
2. Dar dono ativo aos gates órfãos (achado 3) antes de qualquer arquivamento; sem isso,
   arquivar os 4 planos superados oculta gates de VPS/CI/segurança ainda obrigatórios.
3. Resolver o conflito do `.gitignore` (achados 1 e 4) **antes** de criar a convenção
   `closed/`, e corrigir os links relativos junto com a movimentação.
4. Nenhum plano satisfaz a condição "totalmente concluído" no sentido estrito dos próprios
   documentos: 3 deles proíbem declarar-se fechados antes dos gates externos.