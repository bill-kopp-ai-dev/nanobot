# D12 — Registro consolidado F7

- **Data do registro:** 2026-10-24.
- **Estado:** D12 e o aceite local F7 foram assinados e fechados pelo operador em 2026-10-24, com o escopo e as ressalvas deste registro. B13, homologação pública e aceite VPS/deploy continuam separados e não foram concedidos.
- **Fonte de evidência:** plano mestre D1–D12 e artefatos vinculados neste registro. Este documento não substitui nem reinterpreta os relatórios de execução.
- **Escopo:** aceite operacional local, aprovação B13, homologação pública e aceite VPS/deploy são atos separados. Este registro não é aprovação B13, autorização de publicação, homologação ou aceite VPS.

## 1. Decisão e assinatura

| Ato | Estado em 2026-10-24 | Evidência/condição |
| --- | --- | --- |
| Consolidação D12 | **Executada** | Este registro reúne as decisões, revisões, verificações e evidências disponíveis para D1–D11, além do estado dos gates externos. |
| Aceite operacional local F7 | **Assinado e fechado com ressalvas** | Assinatura textual do operador nesta sessão, limitada às evidências e riscos documentados; B5/B6 e demais gates não são declarados aprovados. Ver §§3–5. |
| Aprovação B13 | **Não concedida** | Nenhum candidato está aprovado para publicação. Os oito artefatos D8 são imagens locais e não possuem digests OCI publicados. |
| Homologação pública | **Não executada** | Não houve publicação, pull anônimo nem smoke contra artefato público. |
| Aceite VPS/deploy | **Não executado** | Nenhum VPS/staging foi identificado ou inventariado; nenhum cutover ocorreu. |

**Operador/data da assinatura F7:** operador, 2026-10-24 (confirmação textual nesta sessão: “considere-o assinado. Feche D12 e o plano”). Assinatura cobre D12 e o aceite operacional local nos limites registrados; não é aprovação B13, publicação, homologação ou aceite VPS/deploy.

## 2. Matriz consolidada — pendência, decisão, revisão, verificação e evidência

| Item | Decisão/estado | SHA, image ID ou revisão pertinente | Verificação | Evidência |
| --- | --- | --- | --- | --- |
| D1 — credencial/histórico | Fechado; operador declarou rotação e decidiu manter histórico privado exposto. Segredo removido da árvore, permanece em 32 commits remotos. | Ver §2.1 do plano mestre; sem reproduzir literal ou segredo. | Inventário de commits e verificadores; nenhuma reescrita de histórico. | [Plano mestre §2.1](../plans/closed/2026-10-23-fechamento-padronizacao-docker-f4-f5-f7-plan.md) |
| D2 — proveniência | Fechado; `.mailmap` aplicado sem reescrever commits; política de assinatura de commits segue independente. | Sete repositórios MCP; commits preservados. | Atribuição conferida; rebuilds MCP com SHA de fonte nos labels. | [Plano mestre §2.2](../plans/closed/2026-10-23-fechamento-padronizacao-docker-f4-f5-f7-plan.md) |
| D3 — superfície Khan | Fechado por decisão do operador; 12 tools liberadas nos dois gestores; prompts/resources são limitação registrada. | Positronic config revision 2; Percival `toolsDisabled: []`. | `discover`, `preview`, `reconnect`, `tools/list` e conexão observada. | [Plano mestre §2.3–2.4](../plans/closed/2026-10-23-fechamento-padronizacao-docker-f4-f5-f7-plan.md) |
| D4 — ownership/duplicatas | Fechado com resíduo de observabilidade; sem duplicatas/órfãos confirmados e nenhuma limpeza. | 17 containers observados; 7/150 aquisições sem evento terminal. | Labels, owners, processos, journals e ciclo acquire/close comparados no snapshot datado. | [Plano mestre §2.5](../plans/closed/2026-10-23-fechamento-padronizacao-docker-f4-f5-f7-plan.md) |
| D5 — Khan `tools/call` | Fechado; falha original atribuída ao harness/EOF, não ao servidor. | Khan `0bc52b9`; core `1eeed82f`. | Chamadas MCP reais em fixture, resposta lida antes de fechar stdin; teste de protocolo adicionado. | [Plano mestre §2.6](../plans/closed/2026-10-23-fechamento-padronizacao-docker-f4-f5-f7-plan.md) |
| D6 — OpenSSH | Fechado; candidato local sem waiver; não publicado. | Gateway rev `92eeff90cdb81c27c80ff239e84325021b9bd840`; image `sha256:1ad324379fa94b8e7b4768f703ea10213eda0986c4b4a3e8e9bb70de486f0368`. | OpenSSH 10.6p1; Remote SSH 5/5; scan 0 Critical/0 High/1 Medium; OpenVEX restrito ao image ID. | [Plano mestre §2.8](../plans/closed/2026-10-23-fechamento-padronizacao-docker-f4-f5-f7-plan.md), [OpenVEX D6](2026-10-24-d6-openvex.json) |
| D7 — runtime | Fechado; init único com dono único aplicado no core e MCPs. | Core `79dda0a0`; MCP commits e images listados em §2.7. | 24 medições gestor×EOF/SIGTERM; runtime e smokes conforme; nenhum init duplicado. | [Plano mestre §2.7](../plans/closed/2026-10-23-fechamento-padronizacao-docker-f4-f5-f7-plan.md) |
| D8 — prontidão local | Fechada no escopo local; B5/B6 transferidos, sem promoção/publicação. | Oito candidatos e image IDs listados na [matriz D8](../plans/closed/2026-10-24-d8-promotion-readiness-closure-plan.md#71-candidatos-vigentes). Core rev `50e6ebd0ab8f62a9ed242030459ef0581f7da1a6`. | B1–B4 atendidos; B5 falha/sem run; B6 sem digest OCI. | [Plano D8 §7.4–7.5](../plans/closed/2026-10-24-d8-promotion-readiness-closure-plan.md), [relatório F3](2026-10-10-f3-remediation-triage.md), [plano B5/B6](../plans/2026-10-24-b5-b6-ci-distribution-closure-plan.md) |
| D9 — manual/retenção | Fechado; política §5 aprovada textualmente em 2026-10-24; próxima revisão até 2027-01-24. | Fixture DIND Server 27.5.1; gateway/broker locais `0.1.0-3daabe2`; IDs internos registrados no relatório. | 22/22 checks: update, rollback, falsa health HTTP em stdio, backup/restore, CAS e smoke MCP. | [Walkthrough D9](2026-10-24-d9-runbook-walkthrough.md), [runbook §5](../operations/mcp-docker-local-runbook.md) |
| D10 — reinstalação Positronic | Fechado; caminho delete+restore validado em fixture. `install-local` continua sem smoke bem-sucedido e não é recomendado pela skill. | Fixture `/tmp/positronic-d10-service-home`; revisão 1 e image ID sintético. | CLI isolada preservou imagem/config/allowlist no restore; sem estado de produto. | [Plano mestre §2.11](../plans/closed/2026-10-23-fechamento-padronizacao-docker-f4-f5-f7-plan.md) |
| D11 — skill/instruções | Fechado administrativamente por decisão do operador; os gates técnicos transferidos continuam pendentes. | Skill candidata local `81373efc83c7ec8a043dc38990254653137d85cb36351356c8061d347d1a8bdd`; rehearsal 24 PASS/1 BLOQUEADO. | Built-in implantada e confirmada Enabled; rehearsal sem mutação de MCP de produto. | [Plano mestre §2.12](../plans/closed/2026-10-23-fechamento-padronizacao-docker-f4-f5-f7-plan.md), [plano D11](../plans/2026-10-24-d11-skill-operations-closure-plan.md), [relatório D11](2026-10-25-d11-skill-operations-rehearsal.md) |

## 3. Estado das Actions remotas

Snapshot histórico de 2026-10-24. Os seis runs abaixo terminaram em failure; cinco repetiram steps já falhos no run anterior. Nenhum deles satisfaz B5. Os URLs permitem inspecionar os runs e seus SHA:

| Repositório | SHA candidato | Run | Resultado/observação |
| --- | --- | --- | --- |
| [percival-notes-mcp](https://github.com/bill-kopp-ai-dev/percival-notes-mcp) | `c1047355bce2512cc50ca89c0c8af0b82837909a` | [40133387366](https://github.com/bill-kopp-ai-dev/percival-notes-mcp/actions/runs/40133387366) | Failure em step repetido. |
| [percival-agentmail-mcp](https://github.com/bill-kopp-ai-dev/percival-agentmail-mcp) | `cd55a2fe7121f41e8bd5470973ff84e1ba5e58f8` | [40133390113](https://github.com/bill-kopp-ai-dev/percival-agentmail-mcp/actions/runs/40133390113) | Failure em steps repetidos. |
| [percival-weather-mcp](https://github.com/bill-kopp-ai-dev/percival-weather-mcp) | `437a41c3fd55ae7994c71894e639a6c4ca6d8d43` | [40133392465](https://github.com/bill-kopp-ai-dev/percival-weather-mcp/actions/runs/40133392465) | Failure em step repetido. |
| [percival-khan-calendar](https://github.com/bill-kopp-ai-dev/percival-khan-calendar) | `e8c5d8c0ad2ed498f96985dd77f6247539f62cfb` | [40133396025](https://github.com/bill-kopp-ai-dev/percival-khan-calendar/actions/runs/40133396025) | Failure em steps repetidos. |
| [percival-osm](https://github.com/bill-kopp-ai-dev/percival-osm) | `04d4399c8f8d1a9ce24c8d5ac4cb2208b1801b76` | [40133398880](https://github.com/bill-kopp-ai-dev/percival-osm/actions/runs/40133398880) | Failure; step 6 do smoke Docker é o delta, diagnosticado como flake preexistente do harness. |
| [percival-deep-research](https://github.com/bill-kopp-ai-dev/percival-deep-research) | `af3b23be6d3bdec88bc0da3e419d62ecd55e9aa4` | [40133402029](https://github.com/bill-kopp-ai-dev/percival-deep-research/actions/runs/40133402029) | Failure em steps repetidos. |
| Core Percival (gateway/broker) | `50e6ebd0ab8f62a9ed242030459ef0581f7da1a6` | **Sem run** | Actions estava desabilitado no fork; `total_count: 0` no snapshot D8. |

B5 continua aberto. O core precisa de Actions habilitado pelo owner; os workflows MCP precisam de correção/reconciliação e novos runs verdes nos SHAs finais. Revalidar todos os estados antes de qualquer decisão posterior, pois esta matriz é um snapshot datado.

## 4. Inventário operacional e cutover

**Não houve cutover D8, promoção nem publicação.** O inventário de 2026-10-24 da §7.2 do plano D8 registra os doze containers MCP dos dois gestores nos image IDs A anteriores. O Compose local executava um par core separado, do deploy D11, rev `29a482cec88506e579c4d5c0b32c6aec16e3fc55`, image ID gateway prefixo `ac62466dfd99` e broker `6ea63b38852c`; o par D8 (`50e6ebd0`) estava retido localmente e não ativo. Os IDs completos, owners, revisões e estado A/B estão no snapshot referenciado abaixo; segredos foram omitidos.

O inventário é uma observação datada, não uma leitura do estado atual em 2026-10-24 nem um atestado de VPS. Antes de qualquer ação futura, obter novo inventário pelo runbook e pelo gestor dono.

## 5. Risco residual e gates separados

| Gate/resíduo | Estado | Dono/evidência seguinte |
| --- | --- | --- |
| D8 B5 — CI | Aberto; seis runs MCP falhos, core sem run. | Plano [B5/B6](../plans/2026-10-24-b5-b6-ci-distribution-closure-plan.md); fechar workflows e obter evidência no SHA final. |
| D8 B6 — digest/distribuição | Aberto; nenhum digest OCI publicado ou pull homologado. | I3/I5/I6 e B13 antes de publicação; autorização explícita separada. |
| A1–A7 — autenticação/ensaio e cutover | Abertos; execução integrada 27.5.1, política remota, proxy TLS, expiração, rotação e cutover real sem prova completa. | [Plano de senha única §1.2](../plans/2026-10-11-single-password-acceptance-closure-plan.md). |
| A8/C1 — Actions e artefatos | Bloqueados/pendentes no snapshot por autenticação e estado dos runs; sem manifests/SBOM homologados para todos os candidatos. | Revalidar acesso e cumprir critérios do plano integrado. |
| A9/C2–C4 — VPS/deploy | Bloqueados; sem host/staging identificado, inventário real, migração ou aceite no alvo. | [Plano integrado C1–C4](../plans/2026-10-23-integracao-pendencias-kg-e-mcp-docker-plan.md); operador precisa nomear alvo e executar aceite correspondente. |
| D11 — incidente M-1 e gates técnicos | D11 foi encerrada por decisão administrativa; permanece incerteza sobre efeito de `notes_rm("x")` e follow-ups do plano. | [Plano dedicado D11](../plans/2026-10-24-d11-skill-operations-closure-plan.md). |
| D4 — observabilidade | Sete aquisições sem desfecho terminal no snapshot; sem órfão confirmado. | Corrigir/observar o registro de close e reavaliar com evidência nova. |
| Política de retenção | Aprovada para operação local, sem limpeza; revisão vence em 2027-01-24. | Runbook §5; aprovação textual em D9, separada do aceite F7. |

## 6. Conclusão D12

D12 e o aceite local F7 estão **fechados por assinatura do operador**, limitados ao inventário e às evidências deste registro. B5/B6, A1–A9 e C1–C4 permanecem nos planos donos e não foram convertidos em PASS. Não houve cutover; B13, publicação, homologação pública e aceite VPS/deploy continuam pendentes como atos separados. A assinatura não atesta esses resultados nem autoriza tais ações.
