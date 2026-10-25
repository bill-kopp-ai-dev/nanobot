# Continuidade da padronização Docker — pendências, promoção e aceites

> **Arquivado por consolidação em 2026-10-25, a pedido de bill.** Resíduos de
> engenharia/skill → [Plano 1](../2026-10-25-01-product-readiness-plan.md);
> candidato/segurança/CI/distribuição → [Plano 2](../2026-10-25-02-qualification-distribution-plan.md);
> backup/promoção/operação → [Plano 3](../2026-10-25-03-deployment-operations-plan.md).
> R01–R14 e todos os gates referenciados têm destino no
> [mapa integral](../../reports/2026-10-25-three-plan-consolidation.md).
> Transferência não executa F6 nem fecha gates; corpo abaixo é histórico/especificação.

- **Criado em:** 2026-10-25, por decisão explícita de bill nesta sessão.
- **Estado:** ativo; transferência documental concluída, execução técnica pendente.
- **Origem:** [plano F0–F8 arquivado](2026-10-09-docker-standardization-refactor-plan.md).
  O operador determinou transferir todos os itens abertos para este plano, fechar e
  arquivar o anterior, revisar os planos ativos e commitar/enviar a revisão em `main`.
- **Resultado pretendido:** nenhum resíduo sem dono; candidato rastreado, canário e
  rollback por serviço/gestor, e aceites local, Actions, distribuição e VPS separados.
- **Autoridade desta campanha:** documentação, arquivamento, commit e push da fonte
  deste repositório. Não autoriza mutação de gestores/pins/dados, limpeza, login,
  mudança de settings GitHub, publicação de imagens, release B13 ou deploy.
- **Baseline da revisão:** `nanobot/main` em `d4cabe45`, árvore limpa. Fontes abaixo
  são registros datados, não novo inventário do host nem nova consulta de Actions.

## 1. Transferência, escopo e precedência

Este é o **sucessor de coordenação** de F0–F8 e o dono dos resíduos locais R01–R14.
Todo item aberto do levantamento anterior está aqui: resíduos locais na §3 e gates
especializados na §4, com origem, estado, responsável e evidência de fechamento.
Os critérios detalhados dos planos especializados continuam normativos para seus
próprios gates; suas linhas aqui são referências de acompanhamento, não segundo
aceite nem autorização adicional. Atualizar primeiro o dono, depois este índice.

| Assunto | Dono único do detalhamento/aceite | Papel neste plano |
| --- | --- | --- |
| F6 remanescente, candidatos, observabilidade e decisões locais | Este plano, R01–R14 | Execução/decisão e registro local |
| C1 Actions dos sete repos | [integrado, C1](2026-10-23-integracao-pendencias-kg-e-mcp-docker-plan.md); [checklist F5/C1](2026-10-25-f5-c1-remote-ci-closure-plan.md) | Dependência, sem duplicar aceite |
| B6 de distribuição da D8 | [B5/B6](2026-10-24-b5-b6-ci-distribution-closure-plan.md), em conjunto com I3/I5/I6 | Escopo/método e homologação; B5 CI já transferido a C1 |
| D11 técnico e incidente M-1 | [acompanhamento D11](2026-10-24-d11-skill-operations-closure-plan.md) | Resíduos de F8, sem reabrir D11 administrativo |
| UI/compatibilidade e VPS | [integrado, B1–B7/C2–C4](2026-10-23-integracao-pendencias-kg-e-mcp-docker-plan.md) | Dependências de produto/alvo |
| Autenticação | [senha única, A1–A9](2026-10-11-single-password-acceptance-closure-plan.md) | Ensaios específicos não substituídos pelo runtime I2 |
| Distribuição, deployment, índice, aquisição, locks e recovery | [IaC, I3–I9](2026-10-23-iac-alignment-execution-plan.md) | Evolução separada; I1/I2 concluídos |
| KG nativo | [integrado, A1–A7](2026-10-23-integracao-pendencias-kg-e-mcp-docker-plan.md) | Referência transversal, não requisito indiscriminado de F6 |

**IDs não são intercambiáveis:** `AUTH-A1` abaixo é A1 do plano de senha;
`KG-A1` e `MCP-B1` são do integrado; `DIST-B6` é distribuição da D8, não o
`MCP-B6` Browser. C1–C10 do acompanhamento D11 são gates locais daquela skill,
não C1–C4 do integrado. D-4 de F0 trata chaves válidas, não o segredo legado de D1.

## 2. Evidência encerrada e limites preservados

| Origem | Estado herdado | Limite / próxima lacuna |
| --- | --- | --- |
| F0 | Fechado em 2026-10-24 com risco D-4 aceito | Não homologa runtime nem resolve persistência de segredos |
| F1/F2 | Revalidação local e gate de identidade concluídos | Não significa adoção das imagens pelos consumidores |
| F3 | Fechado localmente em 2026-10-25: candidatos limpos, conjunto resolvido repetível, 0 Critical/High | CI builder e distribuição em C1/I3; não foi demonstrado determinismo bit a bit |
| F4 | Receitas/smokes locais aprovados nas superfícies exercitadas | Nginx opcional de Deep Research sem prova de runtime |
| F5 | Implementação local fechada | Aceite remoto C1 aberto |
| F6/F7 histórico | Seis MCPs canariados nos dois gestores em 2026-10-10 | Não prova a promoção dos candidatos posteriores F3/D8/F5 |
| D1–D12 / F7 | Encerrados; F7 assinado com ressalvas em 2026-10-24 | [Registro D12](../../reports/2026-10-24-d12-f7-closure-record.md); B13/público/VPS não concedidos |
| D11 / F8 | Encerramento administrativo; Built-in habilitada; fixture 24 PASS/1 BLOCKED | Dry-run LLM, HTTP, política admin e M-1 continuam abertos |
| I1/I2 | Arquitetura/handoff e runtime 1 local concluídos | Não reexecutar por tratar esses itens como futuros; I3 adiado |

Fontes: [F0](../../reports/2026-10-24-f0-closure-record.md),
[F1/F2](../../reports/2026-10-24-f1-f2-runtime-identity-revalidation.md),
[F3](../../reports/2026-10-25-f3-reproducibility-contexts-posture.md),
[F4](../../reports/2026-10-25-f4-compose-runtime-revalidation.md),
[F5](../../reports/2026-10-25-f5-ci-conformance-revalidation.md) e
[D1–D12](2026-10-23-fechamento-padronizacao-docker-f4-f5-f7-plan.md).
As imagens, processos, revisões e contagens desses registros precisam ser relidos
antes de operação real; não são o estado observado nesta campanha documental.

## 3. Resíduos transferidos para execução/decisão neste plano

Responsáveis: **agente** coleta/verifica/implementa quando autorizado;
**bill** decide política, recursos, riscos e aprova operações reais.

| ID | Origem / pendência | Estado e dependência | Aceite verificável / responsável |
| --- | --- | --- | --- |
| R01 | F6 — fixar conjunto e caminho de promoção | **Aberto.** Existem candidatos F3, builds diagnósticos F5 e commits posteriores; nenhum representa automaticamente o HEAD final. Reconciliar F6 local com prontidão F3/D8 que exige C1 e DIST-B6 | Matriz repo/SHA/versão/imagem/plataforma por gestor, pin A e candidato B, diff/evidências aplicáveis; decisão explícita de caminho local ou publicado. Não dispensar B6 por inferência. Agente + bill |
| R02 | F6 — inventário, backup e rollback antes do corte | **Pendente**, após R01 e antes de mutação. IDs antigos removidos em 2026-10-10 não reaparecem por trocar config | Owner/server/config/CAS/escopo/allowlist/mounts/dados atuais registrados sem secrets; A retida, backup privado íntegro e ensaio independente por serviço/gestor. Rebuild funcional não é imagem bit-idêntica. Agente |
| R03 | F3/F6 — validade das evidências finais | **Pendente** para o conjunto de R01; DB F3 registrada expira em 2026-10-26 | Scan/SBOM por image ID exato, scanner/DB registrados, Critical/High tratados pela política e OpenVEX restrito; rebuild e runtime só quando o diff exigir. C1 prova builder remoto. Agente |
| R04 | F6 — canário e rollback por serviço/gestor | **Não executado para o novo conjunto**; gates R01–R03/C1 e caminho aprovado | Ordem Deep Research, OSM, AgentMail, Weather, Khan, Notes; um consumidor por vez. Manager suportado/CAS, initialize/list/call segura, imagem efetiva, init, labels dos dois esquemas, portas/TTY/probe por transporte, sinais/restarts/logs/persistência; retorno A comprovado em falha. Agente executa após aprovação de bill |
| R05 | F6/F7 — inventário final e retenção | **Pendente após R04**; sem limpeza autorizada | Inventário pós-cutover e mapa de referências nos dois gestores; retenção de A/B. Qualquer remoção tem lista de IDs, zero referências e aprovação própria; nenhum prune. Agente + bill |
| R06 | F0 D-4 — chaves válidas expostas | **Risco aceito**, rotação adiada indefinidamente, sem dono/prazo técnico no registro original | Bill revê antes de I3/I5, migração de estado/IaC ou auditoria de conteúdo que alcance backups/transições. Fechar tecnicamente exige rotação suportada/verificação sem revelar valores; manter aceitação explícita enquanto adiado |
| R07 | F0 — formato de persistência de secrets | **Sem decisão**, independente de R06 | Decidir referência por nome/ID versus valor em backups/transições; se mudar, desenho de resolução/restore/migração compatível e testes de não vazamento. Bill decide; agente implementa sob autorização |
| R08 | D4 — aquisições sem evento terminal | **Resíduo aberto**, 7/150 no snapshot; ausência Deep em um contexto/HTTP 499, não órfão comprovado | Reproduzir interrupção acquire→tools-list, registrar close/falha e confirmar reconexão/cardinalidade por owner/contexto no Positronic. Mudança em outro repo exige seu escopo/autorização; agente + bill |
| R09 | D2 — política de assinatura/proveniência | **Decisão independente aberta**; .mailmap já aplicado, não repetir atribuição | Política/chave/identidade e verificação aprovadas, ou decisão explícita de manter sem assinatura com limites; conferir sincronização dos arquivos de proveniência no candidato, sem presumir que o snapshot antigo de “sem push” ainda vale. Bill |
| R10 | D5 — correção de relatórios e EOF | **Decisão documental pendente**; bug original do harness, tools/call real já provado | Decidir anotação dos dois relatórios históricos com link à correção, sem apagar evidência. Preservar leitura do frame antes de EOF nos smokes. Migração da camada FastMCP é opção arquitetural separada, não fix obrigatório. Bill + agente |
| R11 | D6 — robustez da regressão SSH | **Pendente**, não reabre correção OpenSSH concluída | Espera explícita pela prontidão do sshd fixture e regressão determinística antes de torná-la gate definitivo. Agente |
| R12 | F4 — proxy nginx opcional de Deep Research | **Não verificado**; falta imagem/configuração fixture revisadas | Se esse profile for adotado, testar runtime production, TLS/auth/bind/probes em fixture; caso contrário registrar exclusão explícita do aceite daquele modo. Agente + bill |
| R13 | F1/F2/F3 — checks canônicos e ambiente de desenvolvimento | **Aberto como reconciliação de evidência**, não nova falha de runtime: F3 registrou 7 Ruff no runner D11 e basedpyright com opcionais ausentes; F4 registrou .venv inutilizável | Reler estado/commits, corrigir apenas problemas reproduzidos e executar checks afetados/canônicos no ambiente correto. Não levar o “sem commit” antigo de F2 como fato atual: houve commits posteriores e baseline desta revisão está limpo. Agente |
| R14 | F0 — desvios operacionais condicionais e manutenção | **Registrados**, detalhes abaixo; não são todos blockers de F6 | Classificação individual, evidência e decisão por finalidade; nenhuma alteração/limpeza implícita. Agente + bill |

### R14 — cobertura dos achados F0 e resíduos auxiliares

- **A1/A2/A9:** metadata do broker/core, tag `:local` e override Engine 29 no runtime
  histórico. R01/I4 devem reconciliar o par core e pin imutável; não homologa produção.
- **A5/A6:** duplo init OSM/Deep e imagens dirty antigas no consumidor. As correções
  existem nos candidatos; R04 deve demonstrar adoção e um init efetivo por caminho.
- **A7:** pins compartilhados exigem cruzar os dois gestores antes de R05.
- **A8:** Notes/Khan com múltiplos locais por gestor: bill decide eventual consolidação;
  I4/I8 mapeiam dados, backup e retorno antes de qualquer migração.
- **A10:** fixtures `d6-nopip`, `d7host-noinit` e volume sem uso no snapshot; F4 também
  observou broker preexistente reportado como órfão pelo Compose. Classificar por
  owner/referências atuais; mensagem Compose não prova que é descartável.
- **A12:** labels Compose de imagem obsoletos; `.Image` é evidência de runtime.
- **A13:** API key vazia e API não ativa é fail-closed, não bug a “corrigir” ligando-a;
  fornecer chave distinta somente se o profile API for escolhido.
- **A14:** ausência de digest remoto é lacuna de DIST-B6/I3/I5, não digest derivável de ID.
- **F5 diagnóstico:** tag Deep `f5-recheck` foi construída com contexto Notes por
  engano; classificar como artefato diagnóstico incorreto, nunca candidato; reter ou
  remover somente mediante decisão nominal R05.
- **Calendário:** política local de retenção já assinada; revisão trimestral vence em
  **2027-01-24**. Renovação de scan antes de promoção não espera essa data.

## 4. Todos os gates externos e acompanhamentos preservados

### 4.1 CI e distribuição

| Gate / dono | Pendência e evidência de fechamento | Estado herdado / responsável |
| --- | --- | --- |
| C1 / F5-C1 WP1 | Habilitar Actions core e acesso autenticado a logs/artifacts; reler SHA final, não despachar f3ad1590 como se ainda fosse HEAD | **Bloqueado por acesso**, bill |
| C1 / WP2 | Logs do pytest Deep #15, reprodução/correção demonstrada, novo run se mudar fonte | **Falho no snapshot**, agente após acesso |
| C1 / WP3 | Sete workflows obrigatórios verdes no headSha exato | Cinco MCPs verdes no snapshot de 2026-10-25; Deep falho/core sem run. Agente |
| C1 / WP4 | Baixar e confrontar manifest/SBOM/locks/bases/plataforma/imagens e results.json core | **Pendente**, agente após acesso |
| F5-C1 WP5 | Atualizar handoff existente via Journal/CAS após erro da API, sem duplicata | **Pendente**, agente; bill resolve acesso se necessário |
| DIST-B6 / fases A/C/D | Selecionar oito artefatos ou subconjunto, decidir pull limpo ou manager, preparar ambiente/owner de release, publicar só após C1/B13/autorização; digests reais e aquisição homologada | **Não iniciado**, agente + bill; implementação I3/I5/I6 conforme escopo |
| B13 | Revisar candidato final, histórico/licenças/proveniência/secrets, release notes e evidências aplicáveis antes de publicar | **Não concedido**, bill; homologação pública/VPS não são pré-requisitos circulares da primeira publicação |

### 4.2 F8 / D11 técnico

| Gate D11 | Pendência | Aceite / responsável |
| --- | --- | --- |
| M-1 / C3 | Apurar chamada notes_rm("x") na auditoria declarada read-only | Evidência anterior/backup determina efeito ou registra inconclusão; allowlist realmente read-only revisada antes de repetir; agente + bill, **prioridade alta** |
| C3 | Dry-run real do agente/LLM, não só harness determinístico | Endpoint isolado sem vaults/credenciais/MCPs reais; zero chamadas mutáveis, owner/CAS/backup/rollback corretos; agente |
| C6 | Profile HTTP com readiness deliberadamente falha | Fixture descartável, resultado correto via manager e sem troca de pin de produto; agente |
| C9 | Decisão allowRemoteAdmin/bind/portas | Bill registra política; nenhuma mudança ativa presumida |
| C8 | Limite da prova de não mutação | Distinguir fixture D11 sem mutação de produto da auditoria M-1 inconclusa; agente |
| D10 residual | install-local sem smoke bem-sucedido | Corrigir/reexercitar no Positronic antes de recomendar CLI; TUI e delete/restore já documentados; agente no escopo daquele repo |

### 4.3 Autenticação — dono plano de senha única

| ID local | Pendência preservada | Estado / aceite mínimo |
| --- | --- | --- |
| AUTH-A1 | Gateway+broker/elevação/mutação MCP reversível em daemon 27.5.1 limpo | **Adiado pelo operador**; prova por HTTP/WS real, auditoria redigida e tokens distintos |
| AUTH-A2 | Negação de admin não-loopback com allowRemoteAdmin=false | **Aberto**; prova de origem, não só campo implementado |
| AUTH-A3 | Login e renovação por túnel/proxy TLS | **Aberto**; fixture representativa e extensão no alvo |
| AUTH-A4 | Renovação/expiração/revogação com WebSockets abertos e logout | **Aberto**; confirmar engenharia de renovação silenciosa antes do ensaio |
| AUTH-A5 | auth init/change e recusa da senha antiga | **Aberto**; ensaio de troca sem registrar valores |
| AUTH-A6 | Recreate gateway+broker com mesmo volume e login/estado preservados | **Aberto**; I2 é evidência parcial de runtime, não fecha o fluxo de senha |
| AUTH-A7 | Cutover da autenticação real com backup/retorno completo | **Aberto**; ensaio aprovado + autorização própria |
| AUTH-A8 | Actions/artifacts no SHA final | **Bloqueado**, compartilhar C1 sem segundo gate remoto |
| AUTH-A9 | Inventário/staging VPS | **Bloqueado**, compartilhar C2–C4 |

### 4.4 Produto MCP, browser e alvo — dono plano integrado

| Gate | Pendência preservada / condição de fechamento | Estado herdado |
| --- | --- | --- |
| MCP-B1 | Smoke Browser+gateway+broker real das mutações; harness isolado | **Aberto**, capacidade browser a preparar |
| MCP-B2 | Completar 11 casos UI: install 409, editor host, stopped-persistent, image/container missing, refresh falho, copiar digest, senha recusada, backup não restaurável, zero backups e viewport | **Aberto**, snapshot de cobertura 1/11; recontar no candidato |
| MCP-B3 | Cliente antigo/host novo com fixture independente, matriz versionada/faixa de protocolo | **Parcial**; I2 não prova todos os clientes WebUI |
| MCP-B4 | Acessibilidade, teclado/foco e layout estreito/largo em browser | **Aberto**, compartilha harness B1 |
| MCP-B5 | Mounts confirmado/divergente/indisponível, destaque Full e i18n morta | **Aberto**, código UI em webui/, não SPA KG |
| MCP-B6 | Oito famílias em Browser real com Weather/OSM e terceiro servidor exercitado | **Aberto**, CLI/happy-dom não satisfazem |
| MCP-B7 | Revisão do pin Arch/automação de renovação ou adiamento explícito | **Aberto**, respeitar revisão trimestral; não afirmar pin vencido sem verificar calendário |
| C2 | Identificar VPS/staging e inventário read-only com layout, Engine/socket/GID/data-root/paths | **Bloqueado por host**, bill fornece; agente inventaria |
| C3 | Deployment/migração/rollback e topologia no alvo; runtime/Browser/estado/locks | **Bloqueado por C2/I4** e I3/I8 aplicáveis ao caminho público |
| C4 | Novo aceite no alvo, risco indireto/backup/retorno e reconciliação | **Bloqueado por C2/C3**, bill assina |

### 4.5 IaC — dono I3–I9

| Gate | Pendência preservada | Estado / dependência |
| --- | --- | --- |
| I3 | Pipeline protegido e publicação/homologação do par core, scanner/secrets, digests/pull anônimo/proveniência | **Adiado**, nova autorização; acessos Docker Hub, fonte pública e owner revisados antes de publicar |
| I4 | Deployment Compose sem build/dev, preflight/layout/UID/GID/token, bootstrap idempotente e deployment.lock atômico do par | **Pendente**, local pode começar com autorização antes de VPS/publicação |
| I5 | Template, Weather/OSM oficiais, server.json e índice determinístico + um comunitário upstream | **Pendente**, publicação por repo exige autorização própria |
| I6 | Adapter estático e aquisição restrita por digest com confiança/consentimento, timeout/concorrência e lifecycle real | **Pendente**, primeira prova usa I5a/I5b; aceite completo I5c |
| I7 | Export/reconciliação capabilities.lock atômico sem secrets/segundo registry, migração compatível | **Pendente**, export local pode anteceder aquisição |
| I8 | Backup consistente do estado inteiro, RPO/RTO decididos, update/retorno do par e restore medido/falhas | **Pendente**, ensaio local antecede C3; extensão no alvo compartilha C3/C4 |
| I9 | Matriz final, walkthrough independente e aceites separados da integração Percival | **Pendente**, I1–I8 e gates aplicáveis; não certifica Positronic |

Workspaces IaC/índice/template e fonte pública precisam de dono/acesso/disponibilidade
confirmados; nomes decididos em I1 não significam recursos criados. A migração de owner
GitHub é recomendação a decidir antes de publicação, não autorização para transferir
o repo privado nem exigência de publicar seu histórico.

### 4.6 KG — referências transversais do plano anterior

| Gate | Pendência preservada no integrado | Estado / dependência |
| --- | --- | --- |
| KG-A1 | Mensagem bundle_uninitialized em Chromium real | **Aberto**; preservar auth, verificar contexto HTTP/WS antes do teste |
| KG-A2 | Benchmark/política de rebuild automático | **Aberto**, conjunto representativo KG-A5 |
| KG-A3 | Cliente SPA e teste de recusa no build fail-closed | **Parcial**, provas de transporte já herdadas |
| KG-A4 | Áudio com amostra real ou aceitação formal de paridade não provada | **Parcial**, provedor/arquivo autorizado |
| KG-A5 | População autorizada CM/AK, links/rebuild/navegação/doctor com conteúdo | **Bloqueado por dados**, bill + agente |
| KG-A6 | Migração/rollback em cópia de bundle real | **Bloqueado por KG-A5/cópia**, operador |
| KG-A7 | Release/upgrade/rollback e EOL/arquivamento dos legados | **Aberto**, operador; snapshots conflitantes de banners exigem reverificação |

Browser-proxy SSH remoto continua fail-closed `remote_auth_required`, fora do escopo
de senha única e desta transferência. Não convertê-lo em nova funcionalidade prometida.

## 5. Sequência de trabalho, dependências e controles

1. **M-1/D11:** apurar a auditoria antes de novo dry-run do agente; nunca usar Notes real.
2. **R01 e C1:** preparar matriz e acesso/readiness do CI; refixar candidato após qualquer
   mudança. Decidir abrangência/método DIST-B6 sem presumir que todo trabalho local
   depende de registry. Até decisão/aditamento específico, manter os gates de promoção
   C1/DIST-B6 registrados em F3/D8; esta revisão não os dispensa.
3. **Trabalho independente:** R07–R13, UI em fixture, AUTH-P2 quando reautorizado,
   I4/I8 locais e export I7 podem avançar em seus escopos. I3 continua adiado.
4. **Caminho publicado:** C1/gates locais → B13 → publicação I3/I5 → aquisição e
   homologação DIST-B6/I6 aplicáveis → R02–R05. Não esperar C3/I9 completos para
   autorizar a primeira publicação e criar dependência circular.
5. **Alvo:** C2 pode ser inventário antes da publicação; aplicação C3 consome I4 e
   ensaios locais I8, com artefatos/autorizações aplicáveis. C4/I9 encerram seus aceites.

**Invariantes:** owner correto e interface suportada, CAS, pin imutável, stdout só
JSON-RPC/sem TTY/porta/probe HTTP em stdio, init único do gestor, socket só no broker,
single-writer do estado, backups privados, sem hand-edit/prune nem segredo em artifacts.
Riscos B23–B25 e política de severidade seguem vigentes. Não substituir Engine Server
27.x homologado pelo override Engine 29 de desenvolvimento para fechar gate do alvo.

Não há prazo/orçamento/alocação novos aprovados. Transferência documental não altera
custo/esforço técnico, permissões ou riscos aceitos; cronograma depende de acesso,
seleção de artefatos, recursos de fixture e host/dados fornecidos pelo operador.

## 6. Evidência e encerramento

Por item registrar `origem → decisão → repo/SHA/diff → imagem/digest/plataforma →
ambiente/teste → resultado/artefato → responsável/data → próximo passo`. Evidência
herdada conserva sua data e identidade; reler configurações reais antes de agir.

O plano só fecha quando R01–R14 tiverem evidência/decisão aplicável e todos os gates
referenciados estiverem fechados **no dono** ou transferidos explicitamente com dono,
estado, critério, evidência e risco residual. Não exige reabrir F7/D11 administrativos.
Aceite local, Actions, B13, homologação pública, autenticação e VPS/I9 são atos separados.

**2026-10-25 — registro de transferência:** inventário completo acima recebido do
plano F0–F8 por decisão de bill; origem fechada por transferência, não por execução
integral de F6/CI/distribuição/VPS. A revisão cruzada e seus checks estão no
[relatório desta campanha](../../reports/2026-10-25-plans-cross-review-and-docker-handoff.md).
Próxima ação técnica: bill disponibiliza acesso C1 e decide o caminho/escopo R01;
apuração M-1 precede novo ensaio read-only do agente.
