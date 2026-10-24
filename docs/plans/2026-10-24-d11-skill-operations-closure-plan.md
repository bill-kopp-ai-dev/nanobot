# Plano de fechamento D11 — skill de operações MCP Docker

- **Preparado em:** 2026-10-24.
- **Objetivo:** fechar D11/F8 com uma skill Percival Built-in disponível, compreensível no contexto real do agente e exercitada em ambiente descartável pelo fluxo do manager.
- **Estado inicial:** D11 parcial. A presença, categoria **Built-in** e ativação da skill foram confirmadas visualmente pelo operador em 2026-10-24. O diagnóstico estruturado do agente aprovou a política em leitura, mas não executou o rehearsal; portanto não fecha o aceite operacional.
- **Referências:** [plano integrado D1–D12](2026-10-23-fechamento-padronizacao-docker-f4-f5-f7-plan.md), §2.12; [skill](../../nanobot/skills/mcp-docker-operations/SKILL.md); [runbook D9](../operations/mcp-docker-local-runbook.md); [walkthrough D9](../reports/2026-10-24-d9-runbook-walkthrough.md).
- **Autoridade:** este plano orienta trabalho local e fixtures sintéticas. Não aprova mudanças em servidores MCP reais, pins/allowlists/credenciais, limpeza de imagens ou estado, acesso remoto, publicação, VPS ou qualquer deploy adicional. Essas ações exigem aprovação específica do operador pela interface suportada.

## 1. Estado conhecido e interpretação do diagnóstico

A skill possui frontmatter válido, o loader a reconhece como `builtin`, está habilitada na UI e a cópia Custom do workspace foi removida. O hash do conteúdo aprovado e implantado é `d17c78c3eb0c8fb41260c297c6cdbc98970cee6c07d35d76919de50f0351d60c`.

O agente reportou 8 PASS, 1 PARCIAL, 3 FAIL e 4 BLOQUEADO, sem mutações. O resultado principal — **política aprovada, procedimento ainda não demonstrado** — é mantido. As linhas abaixo separam defeito, contexto de execução e teste fora do contrato:

| Evidência | Interpretação para D11 | Tratamento |
| --- | --- | --- |
| ST-01, ST-05, ST-07, ST-09, ST-10, ST-11, ST-16 PASS | Metadata, probe, pins, redação, recusas de CAS/payload, arquivos de estado e prova de não mutação passaram no escopo lido. | Reusar no relatório final; não repetir sem mudança de artefato. |
| ST-02/03: runbook e fixture ausentes no `/app` do agente | O checkout do host contém o runbook e o relatório D9. A imagem exclui `docs/` e scripts de desenvolvimento pelo `.dockerignore`; a fixture D9 era Docker-in-Docker efêmera e seu resultado em `/tmp` não é um runner distribuível. A ausência dentro do container é real e impede o agente de seguir essa referência naquele contexto. | Fazer o agente operar contra uma fixture isolada acessível por manager e disponibilizar-lhe as instruções requeridas; não dar Docker socket/CLI ao gateway. Tornar o runner D9 reproduzível a partir do checkout sem reutilizar estado temporário. |
| ST-04: `doctor` falha no GID padrão e passa com GID efetivo | O cliente valida o GID configurado em `PERCIVAL_BROKER_TOKEN_GID`; `65532` é fallback, não o GID do deploy verificado (`1999`). A probe do broker verifica acesso ao token e readiness pelo lado do broker; os dois comandos têm perspectivas diferentes. | Repetir `doctor` no mesmo contexto/configuração efetiva do deploy, com saída redigida, e registrar o GID numérico. Não alterar o token nem simplificar validações para fazer os resultados coincidirem. |
| ST-06: CLI/socket Docker indisponíveis no gateway | Essa separação é intencional: só o broker recebe acesso Docker. A indisponibilidade de CLI/socket local não impede operações tipadas pelo manager. | Manter o isolamento. Executar inventário e chamadas através do owner/manager; a criação da fixture fica no host/runner isolado. |
| ST-08: divergência pontual de observação `notes` | Read-model `connected` e observação volátil do broker divergiram uma vez; não há reprodução suficiente para concluir defeito. | No rehearsal, capturar observações consecutivas e comparar `initialize`/`tools/list` do owner com a projeção. Abrir defeito separado somente se reproduzível e persistente. |
| ST-12/13/14: falsos health/readiness e A→B→A bloqueados | São gates centrais do exercício e ainda não foram demonstrados pelo agente neste cenário. O D9 anterior cobre o runtime local, mas não prova que o agente aplica a skill usando o manager. | Executar no fixture D11 descrito na §3, nunca nos seis MCPs de produto. |
| ST-15: `restore-f1` recusa backup atual como incompleto | `restore-f1` é caminho legado exclusivo da fixture F1 (`PERCIVAL_F1_DISPOSABLE=1`) e espera outra forma de manifest. Não é o restore de produção do `McpDockerService.restore_backup`, que valida o backup atual com `server` e `configuration`. | Tirar esse caso do gate D11. Se backups F1 ainda precisarem ser recuperáveis, abrir uma decisão/tarefa de compatibilidade própria com uma cópia sintética anonimizada. Exercitar no D11 o restore atual no fixture. |
| `allowRemoteAdmin=true`; gateway interno em `0.0.0.0`; portas do host em loopback | O valor de configuração foi confirmado; o bind interno atende o port mapping e, isoladamente, não prova exposição externa. A opção amplia a superfície para peers capazes de alcançar o serviço. | Incluir um preflight explícito da política admin/bind/portas e registrar decisão do operador. Não mudar a configuração ativa neste plano. |

## 2. Escopo e fronteiras

Incluído: skill Built-in, documentação operacional acessível ao agente, roteamento por owner, dry-run, rehearsal sintético, evidência redigida e atualização do plano mestre.

Fora do escopo: atualização de pin dos seis servidores observados; instalar/ativar/configurar/excluir/restaurar MCP real; alteração de `allowRemoteAdmin`, credenciais, GID ou allowlist ativos; provisionar uma porta de administração remota; `docker prune`; publicar ou promover imagens; fechar D8, D12, I3/I9 ou gates VPS.

## 3. Plano de execução

### Fase A — Fixar o contexto de execução (somente leitura)

1. Registrar `git rev-parse HEAD`, `git status --short`, hash da skill, identidade completa da imagem ativa, versão e labels. Distinguir o conteúdo de checkout do que está embutido no container; não usar tag mutável como identidade.
2. Confirmar pelo loader, com e sem filtro de disponibilidade, que `mcp-docker-operations` tem `source=builtin`, metadata válida, está habilitada e não existe cópia Custom concorrente.
3. Mapear quais instruções o agente consegue ler no runtime e quais só existem no checkout do host. A skill não pode prometer que `/app/docs/...` está disponível quando a imagem não o empacota.
4. Fazer o preflight de owner, token/GID (somente valor numérico e permissões), `allowRemoteAdmin`, bind interno e publicação host. Nunca registrar token, valores de env, configuração MCP secreta, mounts completos ou conteúdo de conversa.
5. Interromper se a configuração/owner, o endpoint do fixture ou a conectividade do manager não forem os previstos. Nenhuma ação de leitura deve avançar revisão ou criar backup/journal.

**Saída:** registro preflight redigido com SHA/imagem, escopo e disponibilidade das instruções; hash/contagens de não mutação antes do teste.

### Fase B — Tornar o exercício reprodutível e acessível ao agente

1. Versionar um runner/orquestrador mínimo para a fixture D11 no checkout Percival, baseado no contrato D9 e sem credenciais externas. O runner deve provisionar um Engine/Docker-in-Docker descartável e estado/config independentes; ao final, preservar `results.json` redigido e remover somente recursos nomeados criados por ele.
2. Criar A e B como MCPs sintéticos que respondam `initialize`, `tools/list` e uma chamada segura determinística (`ping`). Guardar IDs imutáveis completos; não depender de tags mutáveis para pin ou rollback.
3. Executar a skill dentro de um agente de teste descartável com acesso ao endpoint/manager da fixture e sem socket Docker no gateway. O agente recebe acesso ao runbook/procedimento D9 necessário no ambiente de teste; documentar como esse recurso é empacotado ou disponibilizado sem incluir os scripts de teste na imagem de produto.
4. Antes de codificar uma referência de runbook no bundle, verificar a forma de distribuição escolhida e a regra `.dockerignore`. O agente deve falhar de modo explícito e read-only quando não tiver instruções/fixture; não deve improvisar comandos de host nem solicitar Docker direto no gateway.
5. Fazer uma execução dry-run sem chamadas mutáveis. O agente deve identificar owner, imagens A/B, revisão global/servidor, transportes, riscos, backup, smoke e rollback, declarar que nenhuma ação ocorreu e parar para aprovação.

**Saída:** procedimento reproduzível no repo, fixture isolada identificada e dry-run do agente aprovado, sem mudança de estado.

### Fase C — Rehearsal autorizado, somente contra a fixture

1. O operador aprova explicitamente a ação **sobre o fixture descartável**; essa aprovação não se estende a nenhum MCP real.
2. Reler owner e revisões imediatamente antes de cada mutação. A cada etapa usar CAS atual e image ID completo; parar em qualquer divergência ou journal pendente.
3. Atualizar A→B pelo manager Percival suportado. Verificar `initialize` → `tools/list` → `ping` e a resposta sintética de B; reconciliar o read-model com a observação do broker.
4. Reprovar intencionalmente uma revisão obsoleta e um payload fora da allowlist. Confirmar recusa antes de qualquer chamada Docker e estado/pin inalterados.
5. Reverter B→A pelo mesmo manager, relendo CAS. Confirmar ID A, `initialize` → `tools/list` → `ping`, estado final e transição/auditoria terminal.
6. Reproduzir stdio com probe HTTP falsa: Docker pode reportar `unhealthy`, mas a decisão deve usar handshake e chamada MCP através do manager. Registrar ambas as observações sem confundi-las.
7. Exercitar profile HTTP somente em fixture: autenticação, bind e probe de readiness deliberadamente falha; provar que o manager reporta a falha e não troca o pin automaticamente.
8. Exercitar `exclude`/backup/restore atual na fixture, verificando checksum, server ID, revisão, confirmação e image ID disponível. Usar a interface suportada e confirmar a tool depois do restore. Não invocar `restore-f1` para esse backup.
9. Repetir a leitura do estado `notes` sintético pelo manager e broker. Uma divergência reproduzível abre defeito separado e bloqueia o aceite até explicação.
10. Verificar hashes, revisão global/servidor, número de backups, journals e auditoria antes/depois; permitir apenas as mudanças esperadas dentro do estado temporário. Nenhum recurso fora do namespace/nome da fixture pode ser removido.

**Saída:** `results.json` e log redigidos com todos os passos, IDs A/B, revisões esperadas/obtidas, códigos de retorno, MCP responses sintéticas, prova de rollback e prova de não mutação de produto.

### Fase D — Ajustar instruções e construir o bundle validado

1. Atualizar a skill só para corrigir lacunas que o ensaio reproduzir: acesso condicional ao runbook, ausência de CLI/socket no gateway, contexto correto de `doctor`, decisão de superfície admin e encaminhamento de restore legado.
2. Manter a política de segurança: owner explícito; manager suportado; read-only por padrão; aprovação para mutações; CAS; imagem A preservada; segredo redigido; nenhuma edição manual, prune ou limpeza por tag/nome/idade.
3. Revalidar frontmatter/loader em imagem candidata: metadata válida, Built-in, disponível, enabled no workspace alvo e nenhuma duplicata Custom.
4. Construir imagem local candidata a partir do commit/diff efetivamente testado, com versão de produto e SHA integral corretos. Registrar image ID/labels. Uma imagem de worktree ou com identidade incorreta ou herdada é somente desenvolvimento e não é evidência de release.
5. Preservar a imagem ativa antes da substituição; fazer deploy local somente conforme a autorização já aplicável, recriar gateway e broker juntos se necessário, verificar health/readiness e loader. Isso não autoriza publicação nem VPS.

**Saída:** skill e documentação coerentes com a execução, artefato local identificado e verificação pós-deploy.

### Fase E — Decisão e fechamento documental

1. Registrar status individual de ST-01–ST-16: PASS, corrigido e repetido, limitação de contexto, fora de escopo ou defeito separado. Nenhum FAIL/BLOQUEADO fica oculto em contagem agregada.
2. Atualizar §2.12 e a linha D11 do plano mestre com data, commit/SHA, skill hash, imagem local, evidência e risco residual.
3. Marcar D11 **fechada** apenas quando a UI estiver confirmada como Built-in+Enabled, o teste do loader passar no artefato identificado, o agente produzir dry-run correto e completar C1–C9 no fixture sem mutação de produto, e as provas de integridade/redaction estiverem anexadas.
4. Se o rehearsal permanecer inacessível, preservar estado **parcial/bloqueado por ambiente** e registrar exatamente o requisito de acesso que falta; aprovação da política ou screenshot não substitui execução.
5. Manter D8, D12, aprovação B13, release/publicação e VPS como gates independentes.

## 4. Critérios de aceite

| Gate | Aceite verificável |
| --- | --- |
| C1 — Catálogo | Skill no image ID candidato com `source=builtin`, metadata válida, disponível, enabled e sem duplicata Custom. |
| C2 — Instruções | Agente consegue ler todos os procedimentos necessários no runtime de teste; ausência de arquivo resulta em parada segura. |
| C3 — Dry-run | Plano identifica owner, transporte, pins, CAS, backup, checks e rollback; zero chamadas mutáveis. |
| C4 — A→B→A | Mutação só no fixture via manager/CAS, handshake+tools/list+ping em B e A, rollback para o mesmo image ID A. |
| C5 — Controles | CAS obsoleto e payload inválido são negados sem chamada Docker; secrets não aparecem. |
| C6 — Probes | Caso stdio falso `unhealthy` e fixture HTTP com readiness falhando interpretados por transporte correto. |
| C7 — Restore/read-model | Backup atual restaurado pela interface atual; read-model converge com observação do broker; divergência reproduzível vira blocker separado. |
| C8 — Não mutação | Estado real, pins, revisões, allowlists, credenciais e containers de produto inalterados; prova redigida anexada. |
| C9 — Operador | Screenshot/confirmação Built-in+Enabled e aprovação da política de acesso remoto registradas; nenhuma alteração de configuração remota presumida. |
| C10 — Proveniência | Commit, versão, SHA integral, image ID e hashes da skill/resultado correspondem ao bundle testado. |

## 5. Riscos, paradas e rollback

- Se o agente só tiver acesso ao runtime de produção e não a uma fixture isolada, limitar-se a read-only; não apontar comandos mutáveis para os seis MCPs existentes.
- Se o token/GID, owner, bind, política admin, revisão, pin ou estado divergirem do preflight, parar. Não corrigir automaticamente configuração ativa.
- Se smoke, rollback, restore, integridade ou broker falhar, manter A e a imagem anterior, preservar logs redigidos e não repetir sobre estado de produto.
- Sem `docker system prune`, bulk cleanup, remoção de container por nome/tag/idade, mudanças de credencial, alteração de allowlist ativa, pull/publicação ou deploy externo.
- O teste legado `restore-f1` fica separado. Qualquer requisito de restaurar backups F1 exige inventário/owner, compatibilidade deliberada e fixture própria antes de alterar o fluxo atual.
