# Revisão cruzada dos planos e transferência da padronização Docker

- **Data:** 2026-10-25.
- **Solicitação:** bill determinou criar sucessor com todas as pendências F0–F8,
  registrar/fechar/arquivar o plano original, revisar todos os planos ativos,
  corrigir inconsistências e commitar/enviar a revisão em `main`.
- **Baseline:** `d4cabe45`, `main...origin/main`, árvore limpa antes da campanha.
- **Natureza da evidência:** revisão documental e inspeções estáticas focadas;
  não é novo inventário Docker, run Actions, build, canário, login ou deploy.

## 1. Transferência e cobertura

O [sucessor ativo](../plans/closed/2026-10-25-docker-standardization-continuation-plan.md)
recebe R01–R14 e todos os acompanhamentos referenciados: C1/WP1–WP5, DIST-B6/B13,
D11/M-1/D10 residual, AUTH-A1–A9, MCP-B1–B7/C2–C4, I3–I9 e KG-A1–A7.
Não existem dois donos de aceite: cada referência mantém o plano especializado;
R01–R14 passam a ter este sucessor como dono onde não havia acompanhamento próprio.

O [original arquivado](../plans/closed/2026-10-09-docker-standardization-refactor-plan.md)
registra a decisão do operador e seu mapa de transferência. Preserva seções,
contratos e snapshots, com links rebased. Fechamento por transferência não declara
F6 dos novos candidatos, C1, distribuição, autenticação ou VPS completos.

## 2. Revisão de todos os documentos ativos

Oito Markdown na raiz de `docs/plans/` após a substituição; sete planos e um índice.
Todos foram lidos/cruzados; documentos especializados mantêm seus critérios salvo
correções explícitas de contrato atual, nunca para transformar teste falho em PASS.

| Documento | Problema / correção |
| --- | --- |
| [Continuidade Docker](../plans/closed/2026-10-25-docker-standardization-continuation-plan.md) | Novo inventário completo, owners, aceites, decisões condicionais e sequência; distingue corte histórico dos candidatos novos e F6 local do caminho publicado. Gates C1/DIST-B6 preservados até decisão específica R01 |
| [Integrado KG/MCP](../plans/closed/2026-10-23-integracao-pendencias-kg-e-mcp-docker-plan.md) | Abertura de 2026-10-23 não era estado atual de C1; D1–D12/F7 fechados; aviso KG precisa de auth; frontend é webui/, não nanobot/webui/; D9 runtime não depende de Browser; conflito de banners KG marcado para reverificação, sem inventar resultado |
| [Senha única](../plans/closed/2026-10-11-single-password-acceptance-closure-plan.md) | Critério A2 ainda exigia credencial/endpoint operator-admin removidos; usa sessão/elevation/WS atual. A3 proibia senha/token em qualquer payload, incompatível com login; limitada aos campos auth permitidos, mantendo proibição de URL/storage/log e payload MCP. “Coberto por P2” esclarecido como planejado, não executado |
| [IaC](../plans/closed/2026-10-23-iac-alignment-execution-plan.md) | Baseline a299da09 explicitamente histórico; D1 não é bloqueio atual; risco F0 de chaves válidas é distinto. I1/I2 e D1–D12 fechados não são trabalho futuro. I3 adiado não impede preparação local autorizada; migração de owner é decisão recomendada, não transferência implícita do histórico privado |
| [Distribuição B6](../plans/closed/2026-10-24-b5-b6-ci-distribution-closure-plan.md) | Removida duplicação ativa do diagnóstico CI B5 já transferido; seleção de escopo na fase A antes de C/D, não fase B histórica. Atualização de status vai ao sucessor/novo candidato, não sobrescreve relatório F3 |
| [D11 técnico](../plans/closed/2026-10-24-d11-skill-operations-closure-plan.md) | Distingue roteiro original A–E de §6 executada/§7 remanescente; não reabrir D8/D12. Próximas evidências vão ao acompanhamento/sucessor, preservando fechamento administrativo |
| [F5/C1](../plans/closed/2026-10-25-f5-c1-remote-ci-closure-plan.md) | WP1 ainda mandava executar f3ad1590 como candidato futuro; agora exige SHA atual aprovado. WP2 vincula logs #15 ao SHA histórico, não ao HEAD por inferência. C1 permanece dono único; sincronização atual aponta ao sucessor |
| [Índice/auditoria](../plans/closed/2026-10-23-auditoria-planos-status.md) | Tabela “corrente” ainda dizia namespace pendente/D1–D12 abertos. Atualizada; porcentagens e achados antigos ficam sob seção histórica, sem novos percentuais nem execução presumida |

## 3. Evidências usadas e conflitos materiais

- D12 registra assinatura F7 de 2026-10-24 com ressalvas; D11 administrativo não
  implica gates técnicos satisfeitos. O sucessor não pede nova assinatura do mesmo ato.
- F3/F4/F5 de 2026-10-25 substituem afirmações antigas de ausência total de prova
  local. C1 conserva cinco MCPs verdes/Deep pytest falho/core sem run no snapshot;
  artifacts não comparados. Nenhum resultado remoto foi consultado de novo aqui.
- `tests/kg/test_gateway_f6.py:244–255` comprova por contrato estático **401 anônimo**
  e **503 bundle_uninitialized autenticado**. A correção KG-A1 preserva auth; não
  usa o mapeamento de erro em `kg_http.py` como autorização pública.
- `nanobot/webui/settings_routes.py:397–421` aceita actions atuais, autenticação,
  origem e elevação; o antigo operator-bootstrap não integra as actions aceitas.
  AUTH-A2 foi alinhado sem fechar a prova de execução ainda pendente.
- `webui/src/components/McpDockerManagement.tsx:489–490` confirma frontend/mounts;
  `nanobot/webui/` é backend. Referências de linha são desta inspeção, não promessa
  de estabilidade futura.
- Governança I1 prevê fonte pública separada `percival` e decisão de owner;
  corrigida a instrução AGENTS que transformava recomendação em migração obrigatória.
- B12 ainda afirmava que workflows continham jobs Windows; inspeção dos três YAMLs
  não encontrou Windows/macOS. A nota foi corrigida como inspeção de fonte, sem
  declarar C1 verde ou afirmar execução remota.
- Exceções `.gitignore` reconciliadas: novo plano incluído, dois acompanhamentos
  ativos adicionados, exceções de paths raiz agora arquivados removidas. Dados e
  regras dos repositórios MCP não foram editados.
- Relatórios históricos e ADR receberam correção de link ao plano movido; a tabela
  de aliases F0 recebeu escape de pipe para não criar uma coluna falsa. Conteúdo
  factual desses relatórios foi preservado;
  mapa `closed/README.md`, AGENTS e runbook apontam ao sucessor. Nenhum resultado
  antigo foi reatribuído ao novo candidato.

## 4. Verificação editorial e limites

Verificação executada após as correções:

| Check | Resultado |
| --- | --- |
| Documentos ativos | 8/8 revistos (7 planos + índice); 29 Markdown afetados/verificados no total |
| Links locais / fragmentos | 459 referências e 19 fragmentos; zero destino/âncora inválidos |
| Estrutura | 139 tabelas com colunas consistentes; fences fechadas |
| Cobertura | R01–R14, AUTH-A1–A9, MCP-B1–B7, KG-A1–A7, I3–I9 e gates compartilhados presentes; sem IDs ausentes/duplicados nos grupos |
| Preservação do arquivo | Corpo histórico idêntico ao baseline d4cabe45 após normalizar realocação de links; novo aviso de encerramento separado |
| Links de entrada | Nenhum link Markdown rastreado continua apontando ao path raiz removido |
| Ignore | Novo plano, acompanhamentos B6/D11 e arquivo movido não ignorados |
| Whitespace | git diff --check passou |

Os números contam referências, não destinos únicos. Revisão do conteúdo e do diff
confirma estados/owners sem reatribuir resultados históricos. O stage é revisado
antes de commit; nenhum segredo/backup/artefato runtime faz parte da alteração.
O verificador temporário fica fora do repositório em
`/home/bill/.positronic/runtime/tmp/opencode/check_nanobot_plans.py`.

Não se executam pytest, rebuild ou smokes Docker para esta alteração documental,
conforme `.agent/workflow.md` e AGENTS. As limitações reais (M-1 inconcluso,
segredos válidos aceitos como risco, CI/artifacts, candidato final e recursos
VPS/dados) continuam abertas nos seus donos.

## 5. Handoff

Resultado documental: original fechado por transferência, sucessor completo,
planos ativos coerentes e links realocados. Commit/push são solicitados para
esta revisão de fonte; o SHA e o resultado do envio serão informados no handoff
da sessão após confirmação do remoto. Isso não habilita Actions, publica imagens
ou concede B13. Próximos responsáveis técnicos: bill para acesso C1/escopo R01;
apuração M-1 antes de repetir dry-run do agente.
