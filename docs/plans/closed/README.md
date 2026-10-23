# Planos arquivados — histórico e donos ativos

**Atualização: 2026-10-23, harmonização com a proposta IaC.** Arquivamento não significa
que todos os gates foram fechados. Estes documentos preservam decisões, snapshots e
evidências; trabalho pendente deve seguir os sucessores, não reabrir o arquivo.

| Arquivado | Dono ativo das pendências |
| --- | --- |
| `kg-integration-plan.md` e `2026-10-11-kg-runtime-recovery-and-product-fix-plan.md` | [plano integrado, A1–A7](../2026-10-23-integracao-pendencias-kg-e-mcp-docker-plan.md) |
| `2026-10-06-mcp-docker-first-class-execution-plan.md` e `2026-10-08-mcp-docker-ui-service-refactor-plan.md` | [plano integrado, B1–B7/C1–C4](../2026-10-23-integracao-pendencias-kg-e-mcp-docker-plan.md) |
| `2026-10-10-f4-f5-closure-plan.md` e `2026-10-10-f7-operations-acceptance-closure-plan.md` | [fechamento Docker, D1–D12](../2026-10-23-fechamento-padronizacao-docker-f4-f5-f7-plan.md); CI/VPS no plano integrado C1–C4 |
| `2026-10-11-percival-single-password-auth-refactor-plan.md` | [fechamento de senha única, A1–A9](../2026-10-11-single-password-acceptance-closure-plan.md) |

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
