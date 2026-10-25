# Plano integrado — pendências de KG nativo e MCP Docker no Percival

> **Arquivado por consolidação em 2026-10-25, a pedido de bill.** KG-A1–A5 e
> MCP-B1–B6 → [Plano 1](../2026-10-25-01-product-readiness-plan.md);
> KG-A7/MCP-B7/C1 → [Plano 2](../2026-10-25-02-qualification-distribution-plan.md);
> KG-A6/C2–C4 → [Plano 3](../2026-10-25-03-deployment-operations-plan.md).
> Não fecha gates: o restante é histórico/especificação, não tracker corrente.
> Ver [mapa integral e precedência](../../reports/2026-10-25-three-plan-consolidation.md).

- **Preparado em:** 2026-10-23, por consolidação de quatro planos cujas pendências estavam
  espalhadas e sem dono único.
- **Estado:** ativo; abertura/auditoria de 2026-10-23, com atualização documental de
  C1 em 2026-10-25. Os demais estados e contagens abaixo são snapshots da auditoria,
  não nova inspeção do host. Nenhum gate ganhou aceite pela revisão cruzada. Evidência inicial:
  [auditoria planos × código](../../reports/2026-10-23-auditoria-planos-vs-codigo.md).
- **Coordenação em 2026-10-25:** [continuidade Docker](2026-10-25-docker-standardization-continuation-plan.md)
  recebe F0–F8 e resíduos sem outro dono. Este plano conserva A1–A7 KG, B1–B7 MCP
  e C1–C4; D1–D12/F7 encerrados não são dependências administrativas ainda abertas.
- **Revisão IaC (2026-10-23):** contratos de distribuição/deployment e novos trabalhos têm
  dono em I1–I9 do [plano de integração IaC](2026-10-23-iac-alignment-execution-plan.md).
  C1 continua dono da evidência remota de conformance; C2–C4 continuam donos dos gates
  no alvo. Catálogo antigo e migração obrigatória para `.percival` deixam de ser
  pressupostos futuros; ver C2/C3 e §4. Nenhum item foi fechado por esta revisão.
- **Autoridade:** este plano consolida, não amplia, escopo. Não autoriza tag, release,
  publicação, escrita em VPS, cutover de dados reais nem mudança de compatibilidade do broker.
  Cada item preserva o critério de aceite e o responsável do plano de origem.
- **Planos de origem (arquivados em `closed/` em 2026-10-23):**
  [`kg-integration-plan.md`](kg-integration-plan.md) ·
  [`2026-10-11-kg-runtime-recovery-and-product-fix-plan.md`](2026-10-11-kg-runtime-recovery-and-product-fix-plan.md) ·
  [`2026-10-06-mcp-docker-first-class-execution-plan.md`](2026-10-06-mcp-docker-first-class-execution-plan.md) ·
  [`2026-10-08-mcp-docker-ui-service-refactor-plan.md`](2026-10-08-mcp-docker-ui-service-refactor-plan.md).
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

O broker/manager existente é a base da integração P0-F da IaC, não trabalho a
reimplementar. As evidências abaixo não provam isolamento total: o risco indireto
B23–B25 (host R/W e acesso ao broker a partir do gateway) continua explícito e precisa
de reavaliação no alvo. Adapter de índice, aquisição autorizada por digest e export
de `capabilities.lock` são lacunas distintas, em I6/I7.

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
| A1 | Browser smoke de autenticação e aviso de bundle ausente (`bundle_uninitialized`) | KG runtime P1 | Chromium prova recusa/login anônimo sem vazamento; após login/bootstrap, a SPA mostra o aviso de setup diante do 503 autenticado, sem erro de rede nem `0` fictício. Registrar SHA/assets | agente | **aberto, critério reconciliado em 2026-10-25** — `tests/kg/test_gateway_f6.py:244–255` distingue 401 anônimo de 503 autenticado. O 503 em `kg_http.py` não autoriza resposta pública. Falta o browser; não enfraquecer auth para satisfazer o antigo enunciado “anônimo” |
| A2 | Política de custo e benchmark de rebuild do grafo | KG runtime P4 | Medir duração/custo de `nanobot kg graph rebuild` em conjunto representativo e em cópia; decidir se habilita reconstrução automática após escrita, com limite e política explícitos | agente | **aberto, e depende de A5** — `graph rebuild` existe (`nanobot/cli/kg.py:107`), mas `nanobot/config/kg.py` **não tem** campo de reconstrução automática: ela não está desligada por configuração, não está implementada. A medição em conjunto representativo depende dos dados de A5; medir em fixture vazia não decide política |
| A3 | Lacunas residuais de F0 (provas curtas de transporte/empacotamento) | KG integração | Fechar os bullets de prova que F0 deixou abertos, ou registrar por escrito que foram substituídos por evidência equivalente (gate Browser real de F7) | agente | **parcial** — dos três bullets: o de Windows/macOS está encerrado (Linux-only); o de rota GET + ação WS está provado (`tests/kg/test_gateway_f6.py:36`, negação anônima em `:244`); o de build fail-closed está **implementado sem teste** (`hatch_build.py:186` aborta sem prebuilt e `:194` exige `bun` para a fonte). Falta o cliente SPA do bullet e um teste que exija a recusa |
| A4 | Paridade de áudio AK | KG integração F4 (D12) | `audio_transcribe` exercitado com **amostra real**; ou, na ausência de amostra, aceitação formal de que a paridade de ASR não está provada | agente | **parcial** — caminho Groq e recusa explícita já implementados e testados (`nanobot/agent/kg/ak/multimodal.py:275`, `:278`; `tests/kg/test_ak_multimodal.py:211`). O sucesso usa `fake_transcribe` (`:187`), logo **stub não é paridade**. Como D12 desacopla o ASR do par do turno, a cláusula sobre "par do turno sem ASR" já não é o caso aplicável: resta amostra real (exige `GROQ_API_KEY` + arquivo) ou aceitação formal |
| A5 | População autorizada dos bundles CM/AK | KG runtime P5 (cenário B) | Criar ao menos uma nota CM e uma Source/ExtractedNote AK autorizadas; provar link, `rebuild` e navegação; `doctor --json` reporta `valid` com conteúdo real | operador (dados) + agente | **bloqueado, confirmado por inspeção** — não existe bundle nativo com conteúdo no host: a única estrutura é `~/.nanobot/workspace/memory/` com 2 arquivos legados (`MEMORY.md`, `history.jsonl`) e `workspace/khalCalendar`, sem raiz nativa nem `acquire/`. Também é o insumo de A2 |
| A6 | Ensaio B6/B7 em cópia de bundle real | KG integração + KG runtime P5 | Backup verificável do bundle inteiro; `kg doctor --json`; idempotência de `ak-migrate-lateral-links --apply`; leitura pós-nativo no legado; decisão de cutover para `kg.mode="native"`; rollback ensaiado em cópia — **nunca** em bundle real | operador | **bloqueado** — depende de A5 e da cópia autorizada |
| A7 | Entrega de D5/D10 e EOL dos repos legados CM/AK | KG integração F9/§5 | Arquivamento dos repositórios legados pelo console do GitHub (decisão de 2026-10-06), banner + `MIGRATION.md`, tag local após ao menos uma release estável com teste de upgrade/rollback | operador | **aberto, baseline a reconciliar** — a auditoria registrou ausência de banner/MIGRATION, enquanto registros anteriores relatam freeze e documentação. Reler checkouts/remotos/arquivamento antes de criar ou repetir entregas; a condição de release/upgrade/rollback continua pendente |

### Onda B — Trilha B: MCP Docker (executável localmente, com fixtures)

| # | Pendência | Origem | Critério de aceite | Resp. | Estado |
| --- | --- | --- | --- | --- | --- |
| B1 | Smoke **Browser WebUI + gateway + broker** das mutações afetadas | UI/service (condição transversal; relatório admite que o driver CLI não fecha o gate) | Fluxo de browser real provando que a UI envia as escolhas (rede, mounts, env) e recebe estado; sem segredos; contra fixture isolada | agente | **aberto, e hoje não executável** — a WebUI **não tem** ferramenta de browser (`webui/package.json` e `bun.lock` sem `playwright`/`puppeteer`) e o único teste da página é `happy-dom` com cliente mockado (`mcp-containers.test.tsx:105`). O smoke real é driver CLI (`tests/mcp_docker/smoke_driver.py:1`). Exige antes o harness de browser (ver nota de dependência em §5) |
| B2 | Testes de UI exigidos pelos critérios de aceite | UI/service itens 1, 2, 3, 5, 6 | Cobrir os 11 casos listados | agente | **aberto, cobertura real = 1 de 11** — coberto: `stopped-persistent` (`mcp-containers.test.tsx:78`, render em `McpContainersPage.tsx:36`). Sem teste de UI: 409 no install (handler `McpDockerManagement.tsx:220`; o 409 de backend em `test_contract.py:172` é de update), falha no editor de host, `image-missing`/`container-missing` (render `McpContainersPage.tsx:35`, `:38`), "Data outdated; refresh failed" (render `:33`), cópia de digest (botão `:195`), senha rejeitada (handler `:244`), backup não restaurável (estado `:453`-`:455`; o teste `mcp-containers.test.tsx:444` cobre só o restaurável), zero backups (o bloco só renderiza se houver, `:449`), viewport estreito (nenhum) |
| B3 | Prova de compatibilidade bidirecional | UI/service (`.agent/review-guide.md`) | Cliente atual + host atual; cliente novo + host mais antigo suportado; cliente antigo + host novo — com fixtures independentes e ausência de campo tratada como **não confirmada**, nunca autorização implícita | agente | **parcial** — o núcleo do critério já está satisfeito: campo ausente cai para o mínimo (`nanobot/mcp_docker/service.py:93`-`:94`), com fixture de host antigo (`tests/mcp_docker/test_contract.py:253`) e teste de UI (`mcp-containers.test.tsx:126`); o contrato WebUI tem o mesmo padrão com fixture independente (`tests/webui/test_client_contract.py:10`, `:33`). Falta a terceira direção (cliente antigo + host novo) como fixture, a matriz versionada e a faixa de protocolo declarada |
| B4 | Acessibilidade e layout em browser | UI/service (condição transversal) | Inspeção de teclado, foco e layout em largura estreita e larga, registrada com evidência | agente | **aberto, e hoje não executável** — não há engine de a11y (`axe` ausente) nem teste de viewport/teclado/foco nesta página; existem afordâncias não testadas (`McpContainersPage.tsx:132`-`:217`). `happy-dom` **não calcula layout**, então a parte de layout exige browser real (mesmo harness de B1); a parte de teclado e foco pode ser feita em componente |
| B5 | Lacuna de UX do acesso ao host | UI/service item 2 | Estado de observação de mounts distingue **confirmado / divergente / indisponível**; destaque visual do modo Full; remover a chave i18n morta `mcpDocker.networkFixed` | agente | **aberto, caminho corrigido em 2026-10-25** — frontend e traduções em `webui/`; `nanobot/webui/` é backend e `spa` é KG. Inspeção estática de `webui/src/components/McpDockerManagement.tsx:489–490` confirma observação por contagem/unavailable e radio Full sem destaque. As contagens i18n da auditoria são datadas e devem ser reconferidas no candidato |
| B6 | Matriz end-to-end F3/F4 com Browser + gateway + broker | MCP Docker first-class | Oito famílias de operação em Browser WebUI real, gateway e broker, com Weather/OSM **e** um servidor preservado; estados, auditoria e recovery observáveis | agente | **aberto, e hoje não executável** — as oito famílias são exercitadas por driver CLI com gateway e broker reais, por `FakeBroker` in-process (`tests/mcp_docker/test_contract.py:230`) e por componente `happy-dom`; nenhum browser. "Servidor preservado" foi atendido só como não-interferência passiva, não como terceiro registro exercitado. Herda o bloqueio de harness de B1 |
| B7 | Revisão trimestral do pin da imagem Arch de CI | MCP Docker first-class (B21) | Pin revisado; renovar via issue automatizada ou registrar adiamento explícito | agente | **aberto, e o pin não se moveu** — segue em `.github/workflows/ci.yml:415` como `archlinux:base-20261004.0.606936@sha256:4e77cf2ea5f410e6f8be5abf93ccf17ce2436e87a138c167208356711a405dbd`, único `archlinux:base` com digest em qualquer workflow. Sem automação de renovação (`renovate`/`dependabot` ausentes; o agendamento de `ci.yml:5` reexecuta contra o mesmo pin) e sem adiamento registrado. O procedimento e a tabela de saída exigida existem no runbook (`mcp-docker-local-runbook.md:101`, `:111`) e a tabela não foi produzida |

### Onda C — dependências externas compartilhadas

Estes itens absorveram, em 2026-10-23, os passos de CI e VPS dos planos de fechamento da
padronização Docker, para que exista **um único dono por gate**. O detalhe operacional vem do
[plano F7 de fechamento](../../reports/2026-10-10-f7-p4-p5-blockers.md) e do
[runbook F5](../../mcp-docker-f5-runbook.md).

| # | Pendência | Origem | Critério de aceite | Resp. | Estado |
| --- | --- | --- | --- | --- | --- |
| C1 | GitHub Actions verde no SHA candidato | MCP Docker first-class (B21/F5), padronização F7 P4.3 e F4/F5 closure 4b (#3) | Jobs obrigatórios verdes nos **sete** repos (gateway/broker + 6 MCPs), `headSha` conferido, manifest/SBOM baixados e confrontados com fonte, lock e digest de base. Fixar candidatos finais após decisões D2/D3/D4 e mudanças I1/I2 que os afetem; rodar conformance intermediária sem esperar essas decisões, revalidando o candidato alterado. Conformance não publica: publicação/digest OCI/pull anônimo são I3/I5. Execução detalhada no [plano F5/C1](2026-10-25-f5-c1-remote-ci-closure-plan.md) | operador (Actions core + `gh auth`) + agente | **aberto — snapshot 2026-10-25:** Notes, AgentMail, Khan, Weather e OSM têm Actions verdes; Deep Research falha em pytest; no snapshot inicial `nanobot` SHA `f3ad1590` tinha 0 runs e a página pública reporta Actions desabilitado no fork. Manifest/SBOM não foram baixados/confrontados; logs Deep requerem autenticação |
| C2 | Inventário real do VPS e mapeamento de layout | MCP Docker first-class (B24), padronização F7 P5; handoff I4 | Inventário read-only por `scripts/percival-vps-inventory.sh` anexado ao [relatório F0](../../reports/2026-10-07-mcp-docker-f0-inventory-and-feasibility.md) §7.3; Client/Server, data-root, socket/GID, submounts, portas, proxy e diretórios separados. Confirmar destino absoluto e mapping entre estado atual `~/.nanobot`, proposta histórica `.percival` e layout IaC `/srv/pblabs/`; preservar path interno suportado. Divergência relevante vira decisão; não copiar `.env`, config, token ou inspect integral para relatório versionado | operador + agente | **bloqueado** — sem VPS identificada; layout final depende de I1/I4 e do inventário, não da mera existência de `~/.percival` |
| C3 | Implantação/migração, rollback e topologia no VPS | MCP Docker first-class (B23/B24), padronização F7 P5; I4/I8 | Backup/restauração do estado completo para o destino aprovado em C2/I4, sem rename automático nem divisão em paths internos não suportados; retorno ensaiado. Compose de deployment por tag+digest, **sem build no VPS**, gateway+broker compatíveis, socket só no broker, UID/GID/token/coberturas e persistência verificados. Engine Server **27.x** continua gate atual; fixar versão homologada pelo host tooling, sem usar overlay Engine 29. Browser + gateway + broker, journal/restore/boot/recreate/oito famílias no alvo; locks sob seus donos, sem avanço em falha | operador + agente | **bloqueado** — depende de C2 e I4; deploy público exige I3/I8 aplicáveis ao candidato |
| C4 | Novo aceite formal do operador para o deploy | MCP Docker first-class (B24), padronização F7 P5 | Aceite **no alvo**, distinto de B25 e da publicação, cobrindo risco indireto residual, mounts/UID/GID, destino real aprovado, locks, backup e retorno; reconciliação pós-cutover por gestor, pins/dados e digests core, hashes/URLs, limitações e decisões. Nenhum deploy sem autorização específica e plano de retorno próprio | operador | **bloqueado** — exige C2/C3 |

## 4. Sobreposições com planos ativos (quem é dono de quê)

Nenhum item deve ser duplicado nem perdido quando dois planos tratam do mesmo gate.
IDs A1–A9 do plano de senha e B5/B6 da D8 têm escopos diferentes de A/B aqui:

| Gate | Dono | Observação |
| --- | --- | --- |
| C1 (Actions) e C2–C4 (VPS, migração, aceite) | este plano | C1 permanece o único gate/registro de aceitação; o [plano F5/C1](2026-10-25-f5-c1-remote-ci-closure-plan.md) contém o checklist operacional de Actions/artifacts e não duplica a propriedade do gate. C2–C4 continuam neste plano. O [plano de fechamento de senha única](2026-10-11-single-password-acceptance-closure-plan.md) mantém P3/P4 próprios para o candidato de autenticação; uma execução de Actions ou de VPS pode satisfazer todos, desde que cada plano registre sua própria evidência e aponte para o run/inventário comum |
| Credencial `operator-admin` exposta, proveniência/identidade, permissão do Khan, duplicatas, OpenSSH, walkthrough do manual, skill F8 | [fechamento da padronização F4/F5/F7](2026-10-23-fechamento-padronizacao-docker-f4-f5-f7-plan.md) | D1–D12 encerrados/arquivados; os gates C1–C4 e de autenticação mantêm seus donos ativos neste plano e no plano de senha única |
| F6/candidatos/rollback, exposição válida F0 D-4, observabilidade D4 e decisões residuais | [continuidade Docker, R01–R14](2026-10-25-docker-standardization-continuation-plan.md) | Sucessor ativo de F0–F8; não reabre D1–D12 nem duplica C1–C4 |
| Incidente M-1, dry-run do agente, fixture HTTP e política admin D11 | [acompanhamento D11](2026-10-24-d11-skill-operations-closure-plan.md) | F8 administrativo encerrado; gates técnicos não convertidos em PASS |
| A1–A9 (autenticação: Engine 27.x, elevação, proxy TLS, expiração, senha alterada, cutover real) | [fechamento de senha única](2026-10-11-single-password-acceptance-closure-plan.md) | já transferido do plano de senha única; não repetir aqui |
| Índice público PBLabs e aquisição OCI (`static-json` + digest) | [integração IaC, I1/I5/I6/I7](2026-10-23-iac-alignment-execution-plan.md) | Substitui como alvo a dependência futura de `positronic-mcp-catalog` OCI. B20 continua baseline local: tipo `repository` reservado/rejeitado em v1 e `trustedCatalogs` não são APIs prontas; migração/compatibilidade exigem contrato explícito. Docker MCP Catalog é opcional, não substituto do manager |
| Bootstrap/Compose de referência, `deployment.yaml`/`.lock`, `/srv/pblabs/` | [integração IaC, I4/I8](2026-10-23-iac-alignment-execution-plan.md) | Tooling externo controla core; manager exporta `capabilities.lock`. C2–C4 verificam o alvo e consomem esses contratos, sem criar outro dono de locks/MCPs |
| `remote_auth_required` no browser-proxy SSH | decisão de escopo | permanece fail-closed, acompanhamento separado |

## 5. Ordem de execução e dependências

```
Onda A (A1–A4)  ─┐
Onda B (B1–B7)  ─┼─→Onda C (C1–C4)  → aceite final por trilha
A5 ──────────────┘        ↑
A6 depende de A5            └── exige C2 (inventário) antes de qualquer escrita
A7 depende de release estável + A6
```

- **Itens locais independentes das ondas A e B** podem avançar com fixtures descartáveis;
  A2/A4–A7 mantêm suas dependências de dados/provedor/operador. Começar por **B2** e **B3**, que são
  executáveis hoje em componente e domínio; **B1** deixa de ser o ponto de partida porque não é
  executável antes do harness de browser.
- **Harness de browser para a WebUI.** B1/B4/B6 e o aviso KG-A1 exigem browser real;
  a auditoria não encontrou harness na WebUI (`webui/package.json` sem
  `playwright`/`puppeteer`; `happy-dom` não calcula layout). D9 foi fechado com
  walkthrough de runtime em fixture: falso unhealthy stdio não exige browser por si.
  Isso não fecha os gates Browser B1/B4/B6. Prior art
  reutilizável: `tests/kg/test_f7_browser.py:104` dirige Chromium por CDP sem Playwright, e
  `spa/src/tests/gateway-browser-probe.ts:1` é um probe empacotado à parte, executado a partir de
  `tests/kg/test_transport.py:206`. Enquanto o harness não existir, B1/B4/B6 e A1 ficam **bloqueados por
  capacidade ausente**, não por esforço.
- **A2 depende de A5**: o benchmark exige conjunto representativo, e A5 é o que o cria. Medido em
  fixture vazia, o resultado não decide política.
- **A5 → A6** é a única cadeia de dados que depende do operador; ela não trava as ondas A/B.
- **C1** espera autenticação e candidatos verificáveis; não é gate de publicação I3/I5.
  **C2** espera host identificado; **C3** também espera contrato/receita I4 e, para o
  deployment público, imagem I3 e ensaios **locais** de recuperação I8. A parte de I8
  no alvo é produzida junto de C3/C4, sem dependência circular. O ensaio DIND local
  não precisa aguardar registry/namespace nem host remoto.
- I1/I2 já estão concluídos em seus escopos. Não há prazo/custo novo aprovado;
  reestimar após recursos, C2, dados A5 e primeira execução dos itens locais.
  Escopo KG não muda por integrar a IaC.

## 6. Riscos e critérios de parada

| Risco | Controle |
| --- | --- |
| Browser gate usado como atalho: rodar o driver CLI e chamar de browser | nomear explicitamente o executor do smoke (`driver CLI` ≠ `browser`) em qualquer relatório |
| Evidência local usada para fechar gate remoto | Actions exige `headSha` conferido e artefato baixado; VPS exige inventário datado no host alvo |
| Fechar o KG com bundles vazios como se houvesse conteúdo | `0` nós/links só é resultado válido de fixture; A5 exige fonte autorizada antes de qualquer afirmação sobre dados reais |
| Regressão de segurança ao mexer em mounts/rede | `mounts` continua obrigatório em `configure`; `[]` nunca vira Full; masks e cobertura do data-root permanecem; socket só no broker |
| Rebaixar o gate de Engine para forçar teste | o broker aceita Client 27.x/29.x mas **exige** Server 27.x; se o alvo não for 27.x, registrar divergência e parar |
| Congelar dados reais durante ensaio | B6/B7 de migração KG (origem de KG-A6), não os IDs MCP-B6/B7, operam sobre cópia; backup antes de qualquer mudança de modo |
| Perder rastreabilidade ao arquivar | cada item mantém origem, critério e responsável; a consolidação não apaga histórico dos planos |
| IaC vira segundo dono de MCP/estado | Compose atualiza apenas core; manager mantém `tools.mcpDocker`/CAS e exporta seu lock; descoberta remota não altera permissões por si só |
| Mudar layout sem proteger o novo estado | I4/C2 aprovam caminhos absolutos e aliases; testar máscaras de todos os paths reais de estado/segredos e data-root antes do spawn |

**Parar e escalar** se um item exigir waiver implícito, `docker rm` em massa, edição manual de
`config.json`/journal, exposição de segredo em log ou artefato, ou se a topologia do alvo
divergir do aprovado.

## 7. Registo de execução

_Vazio na abertura (2026-10-23). Registrar por item: data, responsável, SHA/imagem/digest,
comando executado, resultado, artefato de evidência, limitações e decisão do operador. Não
declarar item fechado por teste local, por `Client.Version` ou por ausência de runs._

**2026-10-23 — reverificação contra o código (não é execução).** Todos os itens foram confrontados
com o repositório e com o host; veredictos e evidência `arquivo:linha` em
[auditoria planos × código](../../reports/2026-10-23-auditoria-planos-vs-codigo.md). Nenhum item foi
executado. Três premissas foram corrigidas: B5 apontava para o repositório errado; A2 era medível sem
A5; B1/B4/B6 eram executáveis sem harness de browser. Sete defeitos novos, fora de qualquer plano,
estão listados em §5 do relatório.

**2026-10-23 — harmonização IaC (planejamento, sem execução).** C2/C3 passam a
consumir o layout/receita I4 em vez de impor rename `.nanobot`→`.percival`; C1
distingue conformance de publicação I3/I5. Índice e aquisição OCI têm dono em I5–I7,
sem reabrir o catálogo antigo nem duplicar o broker. Gates e aceites continuam abertos.

**2026-10-25 — revisão cruzada documental.** C1 mantém o snapshot posterior de cinco
MCPs verdes/Deep falho/core sem run; demais gates não foram executados nesta revisão.
Corrigidos auth do aviso KG, caminho frontend, D9 como evidência de runtime e
referências ao sucessor F0–F8. A possível divergência dos banners legados exige
nova verificação no dono KG-A7, não uma declaração de entrega ou exclusão.
