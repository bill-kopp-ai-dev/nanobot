# D9 — Walkthrough do manual operacional e retenção

- **Data:** 2026-10-24 UTC.
- **Resultado:** walkthrough local concluído; 22/22 checks registrados como PASS.
- **Runbook:** [MCP Docker local](../operations/mcp-docker-local-runbook.md), revisão 0.2.
- **Engine de teste:** Docker-in-Docker rootful 27.5.1 descartável; endpoint no loopback/porta efêmera. O host só recebeu o container dind de nome único, removido no `finally` do runner.
- **Imagens core:** tags locais `percival-gateway:0.1.0-3daabe2` e `percival-mcp-broker:0.1.0-3daabe2`, transferidas por `docker save/load` para o Engine interno. IDs internos medidos: gateway `sha256:8b4042b651aa38a400d32c63b359deadb22bb3cae72d3fdb6cff190e183971c2`; broker `sha256:b0f7801379341f8f2265d63f11c993e1575392267b84aa9b64639adef60473d2`. Estes IDs pertencem ao daemon interno e não são digests OCI publicados.
- **Artefato bruto local:** `/tmp/positronic-d9/i2-pl3_0wgl/results.json` (`completed: true`). Contém os 22 checks e IDs internos; o diretório é evidência local, não artefato de release.

## Walkthrough D9

| Passo | Ação e prova | Resultado |
| --- | --- | --- |
| Update | Serviço Percival atualizou a fixture de image A para B com revisão global e de servidor (CAS); chamada MCP real `ping` retornou a resposta de B. | PASS |
| Rollback | Novo `update-image` B→A, com revisão lida após o update; chamada MCP retornou a resposta de A. | PASS |
| Health falso | Imagem stdio fixture incluiu probe HTTP deliberadamente inválida; Docker reportou `unhealthy`, enquanto a chamada MCP `ping` passou. | PASS; runbook instrui remover a probe e avaliar handshake/call via manager |
| Backup/restore | `exclude` gerou backup; restore aceitou checksum, revisão atual e confirmação igual ao server ID, recriou o servidor e `ping` voltou a passar. | PASS |
| Sinais/probes do runtime | Gateway e API encerraram idle com exit 0; broker com SIGTERM exit 143, sem promessa de drain; broker autenticado, health/probe, init único e MCP stdio por EOF foram exercitados. | PASS |

O restante da campanha revalidou bind único de estado para CLI/API/gateway, comportamento single-writer (API como modo alternativo), autenticação com chaves distintas, readiness protegida, recuperação após crash do broker, persistência e UID/capabilities. O conjunto total tem 22 checks; não somar à contagem histórica do relatório I2.

## Escopo e retenção

O processo usou imagens sintéticas A/B e estado/token de fixture dentro do dind. Não atualizou nenhum pin do Percival ou Positronic no host, não alterou containers/volumes/imagens host, não acessou provider pago, registry, GitHub Actions, VPS ou dados reais, e não publicou nada. A limpeza externa removeu o container dind ao terminar.

A política §5 do runbook foi aprovada textualmente pelo operador mediante sua solicitação explícita para executar D9 nesta sessão (2026-10-24). A aprovação cobre a política e o calendário, não limpeza. A próxima revisão trimestral vence em 2027-01-24. Não foi feita remoção de artefatos nem prune.
