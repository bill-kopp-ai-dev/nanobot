# Plano integrado — pendências de KG nativo e MCP Docker no Percival

- **Preparado em:** 2026-10-23, por consolidação de quatro planos cujas pendências estavam
  espalhadas e sem dono único.
- **Estado:** abertura. Todas as etapas de implementação dos planos de origem estão concluídas
  e evidenciadas; **nenhuma** pendência abaixo foi executada até 2026-10-23.
- **Autoridade:** este plano consolida, não amplia, escopo. Não autoriza tag, release,
  publicação, escrita em VPS, cutover de dados reais nem mudança de compatibilidade do broker.
  Cada item preserva o critério de aceite e o responsável do plano de origem.
- **Planos de origem (arquivados em `closed/` em 2026-10-23):**
  [`kg-integration-plan.md`](closed/kg-integration-plan.md) ·
  [`2026-10-11-kg-runtime-recovery-and-product-fix-plan.md`](closed/2026-10-11-kg-runtime-recovery-and-product-fix-plan.md) ·
  [`2026-10-06-mcp-docker-first-class-execution-plan.md`](closed/2026-10-06-mcp-docker-first-class-execution-plan.md) ·
  [`2026-10-08-mcp-docker-ui-service-refactor-plan.md`](closed/2026-10-08-mcp-docker-ui-service-refactor-plan.md).
  As etapas concluídas desses documentos (F1–F3, F5–F8 do KG; P0–P4 e a instalação P5-B do
  runtime; F0–F2 do MCP Docker; itens 1–7 da UI) continuam válidas como evidência e não são
  reexecutadas.

## 1. Por que um plano só, e com duas trilhas

As pendências pertencem a **duas capacidades distintas** com gates e responsáveis diferentes:
o KG nativo (dados, grafo, aceite do operador em dados reais) e a capability MCP Docker
(containers, broker, CI, VPS). Unificar o rastreio não deve fundir os gates: por isso o plano
mantém a **Trilha A (KG)** e a **Trilha B (MCP Docker)** com fechamentos independentes, e uma
**Onda C** de dependências externas compartilhadas (Actions, VPS, aceite do operador) que serve
às duas.

## 2. O que já está entregue e não é refeito

| Origem | Entregas fechadas | Evidência |
| --- | --- | --- |
| KG integração | F1 (4 tools CM), F2 (15), F3 (enrich), F5 (6 tools AK), F6 (bridge gateway + contrato SPA), F7 (SPA empacotada + GraphView), F8 (CLI `nanobot kg`) | suites `pytest` por fase registradas no plano de origem; snapshot SPA reconciliado em checkout limpo |
| KG runtime | P0 (G0: instalação nova), P1 (fixtures + browser smoke dos grafos), P2 (status tipado), P3 (estados na SPA), P4 (fingerprint SHA-256 → `missing\|valid\|stale\|invalid`), P5-B (instalação nova com `kg bundle init cm/ak`) | imagem `29a482ce`, image ID `sha256:d06d8eed…`, `doctor` `ok` em CM e AK, contêineres `healthy` |
| MCP Docker | F0 (gate fechado por B24), F1 (protótipo descartável, aceite B25), F2 (broker próprio tipado, 8 famílias, fixtures Weather/OSM) | relatórios F0–F5; DIND com Client/Server 27.5.1 |
| MCP Docker UI | itens 1–7 implementados (commit `0475065e`, base `ca9634ae`), incluindo `mounts` obrigatório em `configure`, rejeição de no-op antes de backup/journal, bloqueio de `stopped-persistent` e fallback de capacidade | `webui` 2641 testes, `pytest` 9298 passed, `basedpyright` 0 |

## 3. Pendências consolidadas

Responsáveis: **agente** executa e evidencia; **operador** autoriza, fornece dados/hosts e
assina o aceite. "Bloqueado por" indica a dependência externa que impede a execução.

### Onda A — Trilha A: KG nativo (executável localmente, sem host externo)

| # | Pendência | Origem | Critério de aceite | Resp. | Estado |
| --- | --- | --- | --- | --- | --- |
| A1 | Browser smoke **anônimo** do aviso de bundle ausente (`bundle_uninitialized`) | KG runtime P1 | Browser sem bearer mostra a mensagem de setup, não erro de rede nem `0` fictício; registrado com SHA e assets do candidato | agente | **aberto** |
| A2 | Política de custo e benchmark de rebuild do grafo | KG runtime P4 | Medir duração/custo de `nanobot kg graph rebuild` em conjunto representativo e em cópia; decidir se habilita reconstrução automática após escrita, com limite e política explícitos | agente | **aberto** — reconstrução automática deliberadamente desligada |
| A3 | Lacunas residuais de F0 (provas curtas de transporte/empacotamento) | KG integração | Fechar os bullets de prova que F0 deixou abertos, ou registrar por escrito que foram substituídos por evidência equivalente (gate Browser real de F7) | agente | **aberto** |
| A4 | Paridade de áudio AK | KG integração F4 (D12) | `audio_transcribe` exercitado com **amostra real** pelo par provider/modelo de ASR; se o par do turno não suportar ASR, manter `unsupported_capability` explícito e declarar a lacuna em vez de contar stub como paridade | agente | **aberto** — hoje só API simulada |
| A5 | População autorizada dos bundles CM/AK | KG runtime P5 (cenário B) | Criar ao menos uma nota CM e uma Source/ExtractedNote AK autorizadas; provar link, `rebuild` e navegação; `doctor --json` reporta `valid` com conteúdo real | operador (dados) + agente | **bloqueado** — bundles vazios (0 notas/nós/links), falta fonte autorizada |
| A6 | Ensaio B6/B7 em cópia de bundle real | KG integração + KG runtime P5 | Backup verificável do bundle inteiro; `kg doctor --json`; idempotência de `ak-migrate-lateral-links --apply`; leitura pós-nativo no legado; decisão de cutover para `kg.mode="native"`; rollback ensaiado em cópia — **nunca** em bundle real | operador | **bloqueado** — depende de A5 e da cópia autorizada |
| A7 | Entrega de D5/D10 e EOL dos repos legados CM/AK | KG integração F9/§5 | Arquivamento dos repositórios legados pelo console do GitHub (decisão de 2026-10-06), banner + `MIGRATION.md`, tag local após ao menos uma release estável com teste de upgrade/rollback | operador | **aberto** — sem release estável ainda |

### Onda B — Trilha B: MCP Docker (executável localmente, com fixtures)

| # | Pendência | Origem | Critério de aceite | Resp. | Estado |
| --- | --- | --- | --- | --- | --- |
| B1 | Smoke **Browser WebUI + gateway + broker** das mutações afetadas | UI/service (condição transversal; relatório admite que o driver CLI não fecha o gate) | Fluxo de browser real provando que a UI envia as escolhas (rede, mounts, env) e recebe estado; sem segredos; contra fixture isolada | agente | **aberto** |
| B2 | Testes de UI exigidos pelos critérios de aceite | UI/service itens 1, 2, 3, 5, 6 | Cobrir: conflito 409 no install; falha/conflito no editor de host; `stopped-persistent`; `image-missing`, `container-missing` e "Data outdated; refresh failed"; cópia de digest; senha rejeitada; backup não restaurável; zero backups; viewport estreito | agente | **aberto** |
| B3 | Prova de compatibilidade bidirecional | UI/service (`.agent/review-guide.md`) | Cliente atual + host atual; cliente novo + host mais antigo suportado; cliente antigo + host novo — com fixtures independentes e ausência de campo tratada como **não confirmada**, nunca autorização implícita | agente | **aberto** |
| B4 | Acessibilidade e layout em browser | UI/service (condição transversal) | Inspeção de teclado, foco e layout em largura estreita e larga, registrada com evidência | agente | **aberto** |
| B5 | Lacuna de UX do acesso ao host | UI/service item 2 | Estado de observação de mounts distingue **confirmado / divergente / indisponível** (hoje só `N` vs `unavailable`); destaque visual do modo Full; remover a chave i18n morta `mcpDocker.networkFixed` | agente | **aberto** — comportamento entregue, afordância incompleta |
| B6 | Matriz end-to-end F3/F4 com Browser + gateway + broker | MCP Docker first-class | Oito famílias de operação em Browser WebUI real, gateway e broker, com Weather/OSM **e** um servidor preservado; estados, auditoria e recovery observáveis | agente | **aberto** |
| B7 | Revisão trimestral do pin da imagem Arch de CI | MCP Docker first-class (B21) | Pin `archlinux:base-20261004.0.606936@sha256:4e77cf2ea5f410e6…` revisado; renovar via issue automatizada ou registrar adiamento explícito | agente | **aberto** — obrigação recorrente |

### Onda C — dependências externas compartilhadas

Estes itens absorveram, em 2026-10-23, os passos de CI e VPS dos planos de fechamento da
padronização Docker, para que exista **um único dono por gate**. O detalhe operacional vem do
[plano F7 de fechamento](../reports/2026-10-10-f7-p4-p5-blockers.md) e do
[runbook F5](../mcp-docker-f5-runbook.md).

| # | Pendência | Origem | Critério de aceite | Resp. | Estado |
| --- | --- | --- | --- | --- | --- |
| C1 | GitHub Actions verde no SHA candidato | MCP Docker first-class (B21/F5), padronização F7 P4.3 e F4/F5 closure 4b (#3) | Jobs obrigatórios verdes nos **sete** repos (gateway/broker + 6 MCPs), `headSha` conferido, manifest/SBOM baixados e confrontados com fonte, lock e digest de base. Fixar o SHA candidato por repo **após** D2/D3/D4, para não promover imagem de candidata errada. O CI já está implementado no repositório; falta a evidência remota | operador (`gh auth`) + agente | **bloqueado** — `gh` sem autenticação |
| C2 | Inventário real do VPS | MCP Docker first-class (B24), padronização F7 P5 | `scripts/percival-vps-inventory.sh > vps-inventory.json` executado no host e anexado ao [relatório F0](../reports/2026-10-07-mcp-docker-f0-inventory-and-feasibility.md) §7.3; Client/Server, data-root, socket/GID, submounts, portas, proxy e diretórios capturados separadamente; divergência relevante (GID do socket, data-root não-canônico, portas já publicadas) vira decisão de produto. Não transferir `.env`, config, token, `docker inspect` integral ou valores de secret para relatório versionado | operador + agente | **bloqueado** — sem VPS identificada |
| C3 | Migração, rollback e topologia no VPS | MCP Docker first-class (B23/B24), padronização F7 P5 | Backup verificado de `~/.nanobot` → `.percival` com rollback ensaiado; Compose no **Engine 27.x** com socket apenas no broker, mounts/UID/GID/token e persistência `.percival`; browser WebUI + gateway + broker reais; restore/journal, boot/recreate e as oito famílias no alvo. O overlay local de Engine 29 não prova compatibilidade no VPS | operador + agente | **bloqueado** — depende de C2 |
| C4 | Novo aceite formal do operador para o deploy | MCP Docker first-class (B24), padronização F7 P5 | Aceite **no alvo**, distinto do aceite local de B25, cobrindo risco indireto residual, mounts/UID/GID, persistência `.percival` e rollback; reconciliação pós-cutover de instâncias por gestor, pins e dados, com checklist de resultado, hashes/URLs, limitações e decisões. Nenhum deploy sem autorização específica e plano de retorno próprio | operador | **bloqueado** — exige C2/C3 |

## 4. Sobreposições com planos ativos (quem é dono de quê)

Nenhum item deve ser duplicado nem perdido quando dois planos talkam do mesmo gate:

| Gate | Dono | Observação |
| --- | --- | --- |
| C1 (Actions) e C2–C4 (VPS, migração, aceite) | este plano | absorveram em 2026-10-23 os passos de CI e VPS dos dois planos de fechamento da padronização Docker; o [fechamento da padronização F4/F5/F7](2026-10-23-fechamento-padronizacao-docker-f4-f5-f7-plan.md) não os repete. O [plano de fechamento de senha única](2026-10-11-single-password-acceptance-closure-plan.md) mantém P3/P4 próprios para o candidato de autenticação; uma execução de Actions ou de VPS pode satisfazer todos, desde que cada plano registre sua própria evidência e aponte para o run/inventário comum |
| Credencial `operator-admin` exposta, proveniência/identidade, permissão do Khan, duplicatas, OpenSSH, walkthrough do manual, skill F8 | [fechamento da padronização F4/F5/F7](2026-10-23-fechamento-padronizacao-docker-f4-f5-f7-plan.md) | itens D1–D11; a assinatura F7 (D12) depende deste plano e da autenticação |
| A1–A9 (autenticação: Engine 27.x, elevação, proxy TLS, expiração, senha alterada, cutover real) | [fechamento de senha única](2026-10-11-single-password-acceptance-closure-plan.md) | já transferido do plano de senha única; não repetir aqui |
| Catálogo OCI compartilhado (`source.type: "repository"`, `trustedCatalogs`) | fase posterior | B20 reserva o schema e rejeita o tipo em v1; fora de escopo |
| `remote_auth_required` no browser-proxy SSH | decisão de escopo | permanece fail-closed, acompanhamento separado |

## 5. Ordem de execução e dependências

```
Onda A (A1–A4)  ─┐
Onda B (B1–B7)  ─┼─→Onda C (C1–C4)  → aceite final por trilha
A5 ──────────────┘        ↑
A6 depende de A5            └── exige C2 (inventário) antes de qualquer escrita
A7 depende de release estável + A6
```

- **Ondas A e B** não dependem de nada externo e podem correr em paralelo, com fixtures
  descartáveis. São o caminho de menor perturbação e devem começar por A1 e B1, que hoje
  bloqueiam a afirmação "a UI envia o que o usuário escolheu".
- **A5 → A6** é a única cadeia de dados que depende do operador; ela não trava as ondas A/B.
- **C1** só espera autenticação do GitHub CLI; **C2–C4** esperam um host identificado.
- Não há prazo ou custo confiável até C2 e A5; reestimar depois da primeira execução de A/B.

## 6. Riscos e critérios de parada

| Risco | Controle |
| --- | --- |
| Browser gate usado como atalho: rodar o driver CLI e chamar de browser | nomear explicitamente o executor do smoke (`driver CLI` ≠ `browser`) em qualquer relatório |
| Evidência local usada para fechar gate remoto | Actions exige `headSha` conferido e artefato baixado; VPS exige inventário datado no host alvo |
| Fechar o KG com bundles vazios como se houvesse conteúdo | `0` nós/links só é resultado válido de fixture; A5 exige fonte autorizada antes de qualquer afirmação sobre dados reais |
| Regressão de segurança ao mexer em mounts/rede | `mounts` continua obrigatório em `configure`; `[]` nunca vira Full; masks e cobertura do data-root permanecem; socket só no broker |
| Rebaixar o gate de Engine para forçar teste | o broker aceita Client 27.x/29.x mas **exige** Server 27.x; se o alvo não for 27.x, registrar divergência e parar |
| Congelar dados reais durante ensaio | B6/B7 e A6 operam sobre cópia; backup verificado antes de qualquer mudança de modo |
| Perder rastreabilidade ao arquivar | cada item mantém origem, critério e responsável; a consolidação não apaga histórico dos planos |

**Parar e escalar** se um item exigir waiver implícito, `docker rm` em massa, edição manual de
`config.json`/journal, exposição de segredo em log ou artefato, ou se a topologia do alvo
divergir do aprovado.

## 7. Registo de execução

_Vazio na abertura (2026-10-23). Registrar por item: data, responsável, SHA/imagem/digest,
comando executado, resultado, artefato de evidência, limitações e decisão do operador. Não
declarar item fechado por teste local, por `Client.Version` ou por ausência de runs._