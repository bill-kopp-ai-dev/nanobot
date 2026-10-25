# Planos arquivados — histórico e donos ativos

**Atualização: 2026-10-25, transferência F0–F8 e revisão dos sucessores.** Arquivamento não significa
que todos os gates foram fechados. Estes documentos preservam decisões, snapshots e
evidências; trabalho pendente deve seguir os sucessores, não reabrir o arquivo.

| Arquivado | Dono ativo das pendências |
| --- | --- |
| [2026-10-09-docker-standardization-refactor-plan.md](2026-10-09-docker-standardization-refactor-plan.md) | [continuidade Docker](../2026-10-25-docker-standardization-continuation-plan.md) — todos os resíduos e referências de gate transferidos; origem fechada por decisão de bill em 2026-10-25, sem declarar F6/CI/público/VPS executados |
| `kg-integration-plan.md` e `2026-10-11-kg-runtime-recovery-and-product-fix-plan.md` | [plano integrado, A1–A7](../2026-10-23-integracao-pendencias-kg-e-mcp-docker-plan.md) |
| `2026-10-06-mcp-docker-first-class-execution-plan.md` e `2026-10-08-mcp-docker-ui-service-refactor-plan.md` | [plano integrado, B1–B7/C1–C4](../2026-10-23-integracao-pendencias-kg-e-mcp-docker-plan.md) |
| `2026-10-10-f4-f5-closure-plan.md`, `2026-10-10-f7-operations-acceptance-closure-plan.md` e `2026-10-23-fechamento-padronizacao-docker-f4-f5-f7-plan.md` | [fechamento Docker, D1–D12](2026-10-23-fechamento-padronizacao-docker-f4-f5-f7-plan.md), encerrado em 2026-10-24; gates transferidos seguem nos planos ativos |
| `2026-10-11-percival-single-password-auth-refactor-plan.md` | [fechamento de senha única, A1–A9](../2026-10-11-single-password-acceptance-closure-plan.md) |
| `2026-10-24-d8-promotion-readiness-closure-plan.md` | [F5/C1](../2026-10-25-f5-c1-remote-ci-closure-plan.md) para checklist CI (aceite C1 no integrado) e [B6](../2026-10-24-b5-b6-ci-distribution-closure-plan.md) para distribuição; promoção local remanescente no sucessor Docker |

O [plano de integração IaC, I1–I9](../2026-10-23-iac-alignment-execution-plan.md)
é o dono das evoluções novas: contratos de distribuição, Docker Hub, deployment por
digest, índice GitHub, aquisição autorizada e export de `capabilities.lock`.

Nos arquivos históricos, `local-image`/`pinned-image` e `--pull=never` descrevem a
primeira fase; `.percival` e `positronic-mcp-catalog` descrevem propostas da época.
Não ler esses trechos como veto ao alvo IaC posterior nem como interfaces prontas.
Os planos ativos definem o handoff sem revogar implicitamente B14–B25, permissões,
dados ou risco indireto aceito. A primeira versão pretendida continua `0.1.0`;
publicação e deploy exigem seus próprios gates. Evidência passada não foi reexecutada
por esta atualização do mapa de sucessores.
