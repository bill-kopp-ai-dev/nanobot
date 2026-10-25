# Planos arquivados — histórico e donos ativos

**Atualização: 2026-10-25, consolidação em três planos.** Arquivamento por
transferência não fecha gates técnicos. Só os três documentos abaixo são trackers:

1. [Plano 1 — Prontidão local do produto](../2026-10-25-01-product-readiness-plan.md): L01–L18.
2. [Plano 2 — Qualificação, distribuição e aquisição](../2026-10-25-02-qualification-distribution-plan.md): D01–D12.
3. [Plano 3 — Implantação, recuperação e operação](../2026-10-25-03-deployment-operations-plan.md): O01–O10.

O [mapa integral](../../reports/2026-10-25-three-plan-consolidation.md) registra
origens, redundâncias e a sequência. Corpos históricos abaixo preservam especificações
detalhadas e evidências; expressões como “ativo”/“dono único” dentro deles valem para
a data original, não competem com os três sucessores. I3 e AUTH-P2 continuam adiados.

| Arquivado | Dono ativo das pendências |
| --- | --- |
| [2026-10-09-docker-standardization-refactor-plan.md](2026-10-09-docker-standardization-refactor-plan.md) e [continuidade Docker](2026-10-25-docker-standardization-continuation-plan.md) | R07/R08/R10–R13 e skill → Plano 1; R01/R03/R06/R09 e CI/distribuição → Plano 2; R02/R04/R05/R14 e alvo → Plano 3 |
| `kg-integration-plan.md`, `2026-10-11-kg-runtime-recovery-and-product-fix-plan.md` e [integrado KG/MCP](2026-10-23-integracao-pendencias-kg-e-mcp-docker-plan.md) | KG-A1–A5/MCP-B1–B6 → Plano 1; KG-A7/MCP-B7/C1 → Plano 2; KG-A6/C2–C4 → Plano 3 |
| `2026-10-06-mcp-docker-first-class-execution-plan.md` e `2026-10-08-mcp-docker-ui-service-refactor-plan.md` | MCP local → L04–L06; CI → D03; implantação/aceite → O03/O08/O09 |
| `2026-10-10-f4-f5-closure-plan.md`, `2026-10-10-f7-operations-acceptance-closure-plan.md` e `2026-10-23-fechamento-padronizacao-docker-f4-f5-f7-plan.md` | [fechamento Docker, D1–D12](2026-10-23-fechamento-padronizacao-docker-f4-f5-f7-plan.md), encerrado em 2026-10-24; gates transferidos seguem nos planos ativos |
| `2026-10-11-percival-single-password-auth-refactor-plan.md` e [aceite senha única](2026-10-11-single-password-acceptance-closure-plan.md) | AUTH-A1–A6 → L03; AUTH-A8 → D03; AUTH-A7 → O06; AUTH-A9 → O03/O08 |
| `2026-10-24-d8-promotion-readiness-closure-plan.md`, [B5/B6](2026-10-24-b5-b6-ci-distribution-closure-plan.md) e [F5/C1](2026-10-25-f5-c1-remote-ci-closure-plan.md) | C1/B5/WP1–WP4 → D03; WP5 → D11; DIST-B6 → D01/D04–D08; promoção → O04/O05/O10 |
| [Acompanhamento D11](2026-10-24-d11-skill-operations-closure-plan.md) | M-1/C8 → L01; demais gates técnicos → L11; administrativo não reabre |
| [Integração IaC](2026-10-23-iac-alignment-execution-plan.md) | I1/I2 evidência encerrada; I3/I5/I6/I7 → Plano 2; I4/I8/I9 → Plano 3; V01–V24 preservados |
| [Auditoria/índice](2026-10-23-auditoria-planos-status.md) | Histórico, sem gate próprio; mapa/índice corrente no relatório de consolidação |

O plano IaC arquivado conserva as 55 subtarefas e V01–V24 como especificação herdada;
somente os sucessores registram execução nova. Não há um quarto plano de coordenação.

Nos arquivos históricos, `local-image`/`pinned-image` e `--pull=never` descrevem a
primeira fase; `.percival` e `positronic-mcp-catalog` descrevem propostas da época.
Não ler esses trechos como veto ao alvo IaC posterior nem como interfaces prontas.
Os planos ativos definem o handoff sem revogar implicitamente B14–B25, permissões,
dados ou risco indireto aceito. A primeira versão pretendida continua `0.1.0`;
publicação e deploy exigem seus próprios gates. Evidência passada não foi reexecutada
por esta atualização do mapa de sucessores.
