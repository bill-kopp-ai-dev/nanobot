# Consolidação e recorte de escopo dos planos abertos

- **Data:** 2026-10-25. **Solicitante/decisor de organização:** bill.
- **Adendo de escopo:** a pedido posterior de bill, implantação/VPS e trabalhos
  estreitamente dependentes foram retirados dos planos ativos e diferidos. A partir
  deste adendo há **dois planos ativos**; o Plano 3 é apenas registro arquivado.
  Ver §8, que prevalece sobre a organização inicial registrada nas §§1–7.
- **Baseline observado:** `nanobot/main` em `5f77f438`, `git status --short --branch`
  inicialmente limpo e alinhado ao tracking local `origin/main`.
- **Método:** leitura integral dos oito documentos da raiz `docs/plans/` (sete planos
  e um índice/auditoria), diretrizes, governança e evidências por eles referenciadas.
  Revisão de dependências e critérios; sem nova inspeção de código/runtime/CI/registry
  ou host remoto. Estados técnicos abaixo são herdados, não resultados desta campanha.
- **Resultado inicial:** três planos ativos, então 40 atividades agrupadas (18 L*,
  12 D*, 10 O*), sem quatro trackers para CI. A decisão posterior reduz o escopo
  ativo a L01–L16 e D01–D11; O01–O10 e outras atividades correlatas foram diferidas.

## 1. Organização recomendada e aplicada

| Plano / dono do detalhamento e aceite | Resultado | Interface |
| --- | --- | --- |
| [1 — Prontidão local do produto](../plans/2026-10-25-01-product-readiness-plan.md) | Trabalho local/fixture de auth, Browser, KG, skill e resíduos independentes | L* pode fornecer evidência de produto ao Plano 2; KG real permanece diferido |
| [2 — Qualificação, distribuição e aquisição](../plans/2026-10-25-02-qualification-distribution-plan.md) | Candidato único, C1, B13/publicação, digest homologado, índice/aquisição e export MCP local | D* termina em aquisição/homologação descartável; sem consumo em deployment vivo |
| [Escopo diferido: deployment/recuperação/operação](../plans/closed/2026-10-25-03-deployment-operations-plan.md) | **Não é plano ativo.** Deployment/backup/restore real, promoção/cutover, inventário/VPS e aceite do alvo foram retirados do horizonte próximo | Retomada futura somente por nova decisão explícita; nenhum Plano 1/2 depende desse trabalho |

Critério de agrupamento: **o que o trabalho entrega e quem aceita**, não o nome da
campanha que o originou. Escopos e gates conservados; “consolidar” não é reduzir
suporte, aceitar riscos novos ou dispensar critérios. Não há estimativa nova de
prazo/orçamento: esforço técnico mantém-se até medição. A redução esperada é de
preparação/revisão repetidas; não foi medida como economia realizada.

## 2. Redundâncias, complementaridades e correções de sequência

| Achado na leitura | Organização resultante | Limite preservado |
| --- | --- | --- |
| C1 no integrado, execução F5/C1, B5 em B5/B6 e P3/AUTH-A8 repetiam ações/remotos | D03 contém checklist **e** aceite único dos sete repos. Auth e promoção apontam à mesma matriz | Cada requisito precisa ser coberto pelo SHA/run/artifact aplicável; nenhum teste local substitui Actions |
| DIST-B6 descrevia publicação/pull já detalhados em I3/I5 e aquisição I6 | D01 fixa conjunto/método; D04–D08 executam preparo/publicação/homologação/aquisição uma vez | Oito artefatos D8 versus dois MCPs oficiais é decisão de escopo, não redundância eliminável |
| MCP-B1/B4/B6 tinham campanhas Browser com mesmo backend; auth e KG também precisam Browser | L02 compartilha infraestrutura; L05 agrega smoke/matriz E2E/a11y, L03/L07 mantêm cenários próprios | CLI/happy-dom não provam Browser; estado/reset separado por cenário, não uma execução que “fecha tudo” |
| D11 só determinístico não prova comportamento LLM; incidente M-1 era citado em dois lugares | L01 apura M-1; L11 concentra dry-run real, HTTP e política admin | Evidência inconclusa não prova exclusão nem ausência dela. M-1 precede novo ensaio read-only |
| R02/R04, senha P2-F, I8 e C3 repetiam backup/retorno em domínios diferentes | Inicialmente O02/O04/O06/O07/O08; agora todo pacote de backup/restore real e cutover está diferido | Retorno sintético em L03/D08 permanece confinado à fixture; não é backup operacional |
| I4/C2/C3/P4 tratavam host/layout/implantação | Inicialmente O01/O03/O08/O09; agora o pacote todo está diferido, sem descoberta ou inventário de alvo ativo | Nenhuma escrita/inventário remoto; D06 continua homologação de artefato em daemon descartável |
| KG benchmark precedia insumo representativo na leitura superficial | L08 → L09 continua; L08 usa conteúdo autorizado em ambiente local/isolado; KG-A6/A7 e EOL → escopo diferido | Bundle de produção e migração não são dependência dos testes locais; operador decide se dá acesso a fixture/conteúdo |
| I3 final podia parecer bloquear I6 que precisa entrar no próprio core | Primeiro MCP/índice D07 → I6 em core candidato **local** D08 → SHA final/C1 → core público | I3 permanece adiado. MCP publicado precisa de sua própria aprovação; não antecipar publicação do core |
| Continuidade e índice replicavam status sem execução própria | Continuidade distribuída entre os três; índice histórico arquivado, relatório contém mapa sem novo tracker | Nenhum quarto plano de coordenação; status novo é registrado só em L*/D*/O* |

## 3. Precedência e regra de migração

Os documentos originais foram movidos para `docs/plans/closed/`, com aviso de
transferência e links realocados. Corpos históricos preservam conteúdo, critérios,
contratos e resultados. Sua linguagem “ativo/dono único/próxima ação” é datada.
Os planos ativos iniciais prevaleceram **para ownership e sequência**, sem revogar ADRs,
governança ou requisitos detalhados herdados. Especificações antigas são referências
estáticas dos novos itens, não lugares para registrar execução nova.

Todos os filhos de um ID transferido (por exemplo I6.1–I6.8) seguem o destino do pai,
salvo divisão explícita na tabela abaixo. ST-01–ST-16 e D11-C1–C10 ficam sob L11,
com M-1/C8 acompanhado em L01. V01–V24 estão mapeados na §5. Nenhuma subtarefa fica
sem dono por não reaparecer verbatim no resumo do novo plano.

## 4. Mapa de atividades da consolidação inicial (histórico)

As destinações L*/D*/O* abaixo descrevem a primeira organização, não o recorte
vigente depois do adendo. Ver §8 para a classificação atual: itens O* e atividades
íntimas foram arquivados como diferidos; nenhum O* permanece como owner ativo.

### 4.1 Produto integrado e autenticação

| Origem | Atividade atual / dono | Estado herdado preservado |
| --- | --- | --- |
| KG-A1 | L07 | Browser aviso/auth aberto |
| KG-A2 | L09 | Benchmark/política aberto, depende L08 |
| KG-A3 | L07 | Parcial: cliente SPA/build fail-closed, provas anteriores herdadas |
| KG-A4 | L10 | ASR real ou aceite de não paridade; parcial |
| KG-A5 | L08 | Bloqueado por dados autorizados |
| KG-A6 / B6/B7 de migração real | O07 | Bloqueado, cópia/ensaio/decisão pessoal bill |
| KG-A7 / D5/D10 de EOL KG | D12 | Aberto; reconciliar freeze/banners antes de repetir |
| MCP-B1 | L05, habilitado por L02 | Browser+gateway+broker aberto |
| MCP-B2 | L04 | Checklist 11 casos; viewport real usa evidência L05 |
| MCP-B3 | L06 | Compatibilidade parcial |
| MCP-B4 | L05 | Acessibilidade/layout Browser aberto |
| MCP-B5 | L04 | UX mounts/Full/i18n aberto |
| MCP-B6 | L05 | Oito famílias/terceiro registro exercitado aberto |
| MCP-B7 | D10 | Revisão pin/automação ou adiamento aberto |
| C1 do integrado | D03 | Único CI aberto, sem aceite novo |
| C2 do integrado | O03 | VPS bloqueado por host |
| C3 do integrado | O08 | Deployment/migração/alvo bloqueado |
| C4 do integrado | O09 | Novo aceite alvo bloqueado |
| AUTH-A1 / P2 | L03 | Adiado pelo operador, Server 27.5.1 integrado |
| AUTH-A2 / P2-B | L03 | Negação admin não-loopback por WS aberto |
| AUTH-A3 / P2-C | L03 local; O08 extensão no alvo | Túnel/TLS/renovação aberto; não são dois aceites da mesma execução |
| AUTH-A4 / P2-D | L03 | Renovação silenciosa a confirmar/implementar, TTL/WS/logout abertos |
| AUTH-A5 / P2-E | L03 | Ensaio init/change/recusa antiga aberto |
| AUTH-A6 / recreate/P5 | L03 | Login/estado/CAS após recreate integrado aberto |
| AUTH-A7 / P2-F | O06 | Cutover real aberto e separadamente autorizado |
| AUTH-A8 / P3 | D03 | Compartilha único gate Actions |
| AUTH-A9 / P4 | O03 inventário; O08 prova alvo | Compartilha gates VPS, sem segundo tracker |
| AUTH-P0/P1 | Evidência herdada do Plano 1 | Já concluídos; não refazer snapshot limpo sem mudança |
| AUTH-P5 | Registro local L03, CI D03 e cutover O06/O08 | Handoff por domínio, sem etapa técnica duplicada |

### 4.2 Resíduos Docker e D11

| Origem | Atividade atual / dono | Estado herdado preservado |
| --- | --- | --- |
| R01 | D01 | Caminho/conjunto/candidato aberto |
| R02 | O04 | Inventário/backup/retorno antes do corte pendente |
| R03 | D04 | Evidência/scans exatos por candidato; DB datada não é scan atual |
| R04 | O05 | Canário por serviço/gestor novo não executado |
| R05 | O10 | Pós-corte/retenção pendente, sem limpeza autorizada |
| R06 / F0 D-4 | D02 | Risco aceito/rotação adiada indefinidamente, revisão antes de exposição/migração |
| R07 | L12 | Decisão de persistência secrets aberta |
| R08 / D4 | L13 | Eventos terminais/aquisição residual externo Positronic |
| R09 / D2 | D02 | Assinatura/proveniência sem decisão; .mailmap já feito |
| R10 / D5 | L14 | Anotação histórica/EOF, não nova correção FastMCP obrigatória |
| R11 / D6 | L15 | Robustez da regressão SSH; fix local já encerrado |
| R12 | L16 | Proxy nginx opcional não verificado, inclusão condicional |
| R13 | L17 | Checks/ambiente a reconciliar sem presumir defeitos atuais |
| R14 | O10, com referências D01/O01/O02/O05/D06/D10 | Todos os achados A1/A2/A5–A10/A12–A14 e diagnóstico F5 individualizados na tabela O10 |
| D11 M-1 | L01 | Incidente prioridade alta e efeito inconcluso |
| D11-C1/C2 | L11 evidência herdada | Built-in/instruções confirmados no contexto anterior |
| D11-C3 | L11 após L01 | Dry-run LLM pendente, determinístico não fecha |
| D11-C4/C5/C7 | L11 evidência herdada | A→B→A/controles/restore provados na fixture |
| D11-C6 | L11 | Stdio demonstrado; fixture HTTP falha pendente |
| D11-C8 | L01 | Limite não mutação fixture versus auditoria M-1 |
| D11-C9 | L11 | Política admin/bind/portas sem decisão registrada |
| D11-C10 | L11 evidência herdada | Proveniência local identificada, não release |
| D10 residual install-local | L18 | Smoke CLI Positronic ainda não bem-sucedido |
| D11 ST-01–ST-16 / fases A–E | L11 | Resultados individuais/evidência/contexto preservados; retomar só lacunas |

### 4.3 IaC, CI e distribuição

| Origem | Atividade atual / dono | Estado herdado preservado |
| --- | --- | --- |
| I1.1–I1.7 | ADR/handoff herdados dos Planos 2/3 | Concluído arquitetura, não acesso/publicação |
| I2.1–I2.6 | Runtime 1 herdado; extensões L06/O01/O02/D03 | Concluído localmente em `0e7ff072`, sem aceitar remoto/alvo |
| I3.1–I3.3 | D04 | Adiado, sem implementação iniciada |
| I3.4 | D05 | Adiado/publicação exige B13 por candidato |
| I3.5–I3.6 | D06 | Pull/promoção de metadados pendente |
| I4.1–I4.6 | O01 | Deployment/bootstrap/lock pendente; execução alvo O08 |
| I5.1–I5.6 / I5a/I5b/I5c | D07 | Template/MCPs/índice pendentes; publicação/pull executados uma vez via D04–D06 |
| I6.1–I6.8 | D08 | Aquisição/lifecycle pendentes, prova incremental sem ciclo core público |
| I7.1–I7.5 | D09 | Export/reconciliação pendentes; IaC não vira writer |
| I8.1–I8.7 | O02 | Recovery incremental; resultados alvo O08/O09, sem espera circular |
| I9.1–I9.4 | O09 | Matriz/walkthrough/aceite/handoff pendentes |
| F5/C1 WP1 | D03 | Acesso/Actions core pendentes, owner bill |
| F5/C1 WP2 | D03 | Logs Deep autenticados/causa falha pendentes |
| F5/C1 WP3 | D03 | Sete workflows verdes no SHA final pendentes |
| F5/C1 WP4 | D03 | Artifacts/comparação pendentes |
| F5/C1 WP5 | D11 | Reparo do handoff existente via API/CAS pendente |
| DIST-B5 / fase B histórica | D03 | Transferido ao único CI, não checklist antigo a executar |
| DIST-B6 fase A | D01 | Conjunto/método/release owner pendentes |
| DIST-B6 fase C | D04 | Preparo condicionado ao escopo e I3/I5 |
| DIST-B6 fase D/aceite | D05/D06; D08 se manager escolhido | Publicação e aquisição não executadas, nenhuma promoção autorizada |
| B13 | Decisão bill em D02/D05 | Pré-publicação, não requisito circular de homologação/VPS já completos |
| Índice/auditoria 2026-10-23 | Este relatório como mapa estático; status nos três planos | Sem atividade de execução própria; percentuais históricos não recalculados |

## 5. Cobertura original dos 24 casos de aceitação IaC

Esta matriz registra para onde os critérios foram mapeados na primeira consolidação.
As extensões de deployment, estado real, restore integral e alvo estão diferidas pela §8.

| Caso original | Atividade que conserva o critério / evidência |
| --- | --- |
| V01 | Runtime I2 herdado; O01 revalida modos/UID/GID/probes afetados |
| V02 | L03 autenticação e O01/O02 bootstrap/estado |
| V03 | O02 sinais/crash/recreate e O08 extensão alvo |
| V04 | L06 compatibilidade, D03 CI e D08 migração/schema |
| V05 | D04 proteção PR/release/scan/waiver |
| V06 | D05/D06 par parcial e pull/digests |
| V07 | O01 Compose agregado/preflight |
| V08 | O01/O02 idempotência e preservação |
| V09 | O01/O02 falha sem avanço lock |
| V10 | O01/O02 crash/atomicidade/concorrência |
| V11 | D07 determinismo/validação índice |
| V12 | D08 manifests/origens/redirect/revisões |
| V13 | D08 consentimento/policy/requisitos não suportados; L03 origem remota |
| V14 | D08 digest/plataforma/RepoDigest divergentes |
| V15 | D08 rede/cache/timeout; O02 indisponibilidade sem trocar artefato |
| V16 | D08 concorrência/CAS/retry |
| V17 | D08 três apps/lifecycle/call real; O02 dados/restore |
| V18 | D08 bridge/EOF/timeout/transporte suportado |
| V19 | D09 export/snapshot/falha após commit |
| V20 | D09 restore/reconciliação/owner externo e O02 backup |
| V21 | O01/O08 paths protegidos/aliases/submounts/topologia |
| V22 | O02 par core runtime-only/migration-bearing |
| V23 | O02 restore independente medido com KG/MCP/auth |
| V24 | D02/D04–D09 e O02/O09 redação de logs/metadados/handoff |

Compartilhar prova não multiplica o aceite: dono do mecanismo registra resultado e
consumidores apontam à mesma identidade. Casos com extensões local/público/alvo
permanecem abertos até cobrir seus ambientes aplicáveis; `SKIP` não é `PASS`.

## 6. Sequência da primeira consolidação (histórico)

```text
L01 → L11                         L08 → L09
L02 → L03/L05/L07                 L08 + cópia real → O07 → D12 (EOL)
L04/L06/L12/L15/L17 → checks locais → D01/D03 final

O01 + O02 locais e D09 export podem avançar antes do registry/VPS
D07 primeiro MCP + índice → D08 no core local → candidato final D01/D03/D04
→ B13 → D05 → D06 + regressão publicada D08/D09
→ O04 → cortes autorizados O05/O06 ou O08 → O09/O10
O03 read-only pode ocorrer antes da publicação; O08 exige O03/O01/O02 locais
```

Setas expressam dependência, não autorização de início nem ordem total entre todos
os itens. L03/AUTH-P2 e I3 continuam adiados; dados/provedor/endpoint LLM, GitHub
Actions/artifacts, workspaces IaC/índice/template, namespace registry e VPS são
recursos a fornecer/confirmar por bill. Falta de um recurso bloqueia seu consumidor,
não todos os trabalhos independentes. Nenhuma delegação/subagente foi solicitada.

## 7. Mudanças, verificações e próximo passo da consolidação inicial

- Três planos criados; oito documentos anteriores arquivados com avisos de destino;
  referências e índice de arquivo realocados, `.gitignore` alinhado aos três ativos.
- `AGENTS.md` e runbook apontam aos donos atuais; links históricos preservam o
  documento original arquivado, não substituem silenciosamente o relato por plano novo.
- Escopo de checks desta campanha: contagem de planos, cobertura de IDs/subtarefas/
  casos, unicidade dos destinos, links/âncoras locais, tabelas/fences, preservação
  histórica normalizando realocação de links, `git diff --check` e regras de ignore.
  Resultados efetivamente obtidos são apresentados no handoff da sessão.
- Nenhum teste de runtime/CI/container/registry/VPS executado: só documentação mudou.
  Nenhum gate técnico recebeu aceite pela consolidação.
- Nenhum commit/push novo está autorizado pelo pedido atual; alterações locais ficam
  disponíveis para revisão. O commit `5f77f438` é baseline da campanha anterior.

### Verificações editoriais realizadas na primeira consolidação

Validador local: `/home/bill/.positronic/runtime/tmp/opencode/check_three_plan_consolidation.py`.
As verificações abaixo são documentais; não são homologação do produto.

| Critério | Resultado |
| --- | --- |
| Limite inicial de planos ativos | Exatamente três Markdown na raiz, antes da decisão posterior de redução |
| Atividades da primeira consolidação | L01–L18, D01–D12 e O01–O10 contíguos, sem definição duplicada |
| Transferência | KG-A1–A7, MCP-B1–B7, AUTH-A1–A9, R01–R14 e V01–V24 mapeados; 55 subtarefas IaC preservadas e encaminhadas |
| Links/âncoras | 571 referências locais e 22 fragmentos válidos em 30 documentos Markdown |
| Estrutura | 154 tabelas consistentes; fences fechadas; dois delimitadores finais ausentes em tabela histórica corrigidos sem mudar conteúdo |
| Preservação | Oito corpos recém-arquivados iguais ao baseline `5f77f438`, normalizando só realocação dos links e excluindo os avisos novos |
| Versionabilidade | Planos novos, arquivos movidos e relatório não ignorados por `.gitignore` |
| Whitespace | `git diff --check` passou |

**Próximo passo da primeira consolidação:** começar por M-1 e pelo harness comum, enquanto
bill decide conjunto/método de distribuição e fornece acesso CI/dados necessários. Este
registro foi depois atualizado pelo adendo abaixo.

## 8. Adiamento de deploy e VPS — recorte vigente

<a id="deferred-deployment-vps"></a>

**Decisão do operador:** as atividades relacionadas a deploy/testes em VPS e as etapas
estreitamente dependentes não serão executadas no futuro próximo, porque há prioridades
anteriores. Não se registra data de retomada. O Plano 3 foi movido integralmente para
`docs/plans/closed/2026-10-25-03-deployment-operations-plan.md`, preservando critérios,
responsáveis e decisões sem manter um terceiro plano ativo. O arquivamento é **diferimento**,
não conclusão, transferência para execução atual nem autorização.

| Etapas identificadas | Tratamento vigente | O que permanece ativo |
| --- | --- | --- |
| I4.1–I4.6 / O01 — layout do host, bundle Compose de produção, bootstrap/OpenTofu, preflight e `deployment.lock` | Diferidas integralmente, incluindo ensaios locais que só servem ao pacote de deployment | Verificação de produto em fixtures, CI e artefatos no Plano 2; não gerar bundle/receita de deploy agora |
| I8.1–I8.7 / O02 — política de backup do estado inteiro, RPO/RTO, update/restore, recuperação e ensaios de falha | Diferidas; backup/restore de configuração, auth, KG, MCPs, journals e estado real fora do escopo atual | Retorno de uma operação sintética dentro dos testes L03/D08 continua restrito à fixture e não é um programa de backup/DR |
| C2–C4, AUTH-A9, O03/O08/O09, I9 — inventário, instalação, auth/proxy e aceite de VPS/staging | Diferidos; nenhum host será selecionado/inventariado/aplicado como parte dos planos ativos | Checks locais/Actions e pull/homologação D03–D08 não exigem VPS |
| R02/R04/R05/R14, O04/O05/O10 — snapshots do estado de consumidores, pins A/B, backup antes do corte, promoção/canário, inventário pós-corte/retenção | Diferidos; sem atividade de cutover em gestor vivo, alteração de pins, reconciliação pós-corte ou limpeza | D01 matriz de artefato não inclui pin por consumidor; D08 adquire e exercita lifecycle só em manager/daemon descartável |
| AUTH-A7/P2-F / O06 — cutover de autenticação em instância real | Diferido; testes L03 permanecem em DIND/fixture e não migram credenciais reais | L03 segue adiado pelo operador; seus ensaios locais não são de VPS |
| KG-A6/O07 e KG-A7/D12 — migração/rollback de bundle real, decisão `kg.mode=native`, EOL/archive CM/AK dependentes de release/upgrade real | Diferidos, inclusive reconciliação e release/EOL operacional dos legados; decisão de manter/arquivar não é reaberta aqui | L08/L09 com conjunto autorizado e sintético/isolado permanecem ativos; não usar bundle de produção |
| R07 — escolher representação de secrets em backups/transições e migração/restore | Diferido junto com I8/O02 | D02 continua tratando exposição/proveniência estritamente para avaliação do candidato e pré-publicação; nenhuma migração de secret |
| R12/L16 anterior — validar profile nginx de Deep Research como runtime de produção | Diferido como qualificação de um modo de implantação; se o modo não estiver no candidato, não bloqueia testes locais gerais | Outros testes Browser/auth/WebUI em fixture permanecem ativos |
| D09 / I7.1–I7.4 — export e reconciliação de `capabilities.lock` | Mantidos apenas como trabalho de projeção/export local, sem restore, deployment lock ou reconciliação no host | D09 ativo no Plano 2; restauração de estado real está diferida |
| D12 / KG-A7 — reconciliação de banner/MIGRATION/freeze e release estável com upgrade/rollback | Retirado do Plano 2 e diferido junto com O07; sem arquivamento de repos/tags/actions | Nenhum requisito de EOL legado para fechar Plano 1 ou Plano 2 |

### Casos IaC afetados

Em V01–V24, provas de contrato/produto ainda necessárias para a qualificação são
executadas em escopo local/fixture conforme Plano 1/2. As porções que exigem pacote
de produção, estado real, restore completo, paths do host, aquisição implantada, VPS,
staging ou aceite operacional são diferidas (em particular V07–V10, V15 quando se
trata de core/restore, V20–V24 nas extensões de recovery/alvo). O inventário original
dos 24 casos permanece no histórico IaC; nenhum `PASS` é inferido nem o critério é
considerado concluído. Se um caso combinar local e VPS, apenas a parte local que serve
diretamente a L*/D* pode rodar; ela não satisfaz a extensão diferida.

### Plano ativo após o adendo

- **Plano 1:** L01–L16, local/fixture e atividades independentes de rollout; AUTH-P2
  continua explicitamente adiado pelo operador. L08→L09 permanece; cópia/migração real
  de KG não é prerequisite nem subtarefa ativa.
- **Plano 2:** D01–D11 termina em CI, distribuição e aquisição/homologação em ambientes
  descartáveis. D05 ainda exige retomada de I3, B13 e autorização própria; D06 não
  significa implantação nem promoção de gestor vivo. D12/KG-A7 foi removido para o
  escopo diferido.
- **Escopo diferido (antigo Plano 3):** arquivado como referência de critérios para eventual retomada; não conta
  como terceiro plano ativo nem como backlog prioritário. AGENTS/runbook/índice devem
  encaminhar implantação, rollback real e VPS para esse registro diferido.

**Critério de retomada:** decisão futura explícita de bill para reabrir escopo e
priorizar infraestrutura/deploy; nessa ocasião reavaliar os critérios arquivados, o
estado atual dos candidatos, a disponibilidade do alvo/recursos e criar um plano ativo
ou aditamento com sequência/aceites atuais. Não presumir que os snapshots de 2026-10-25
continuarão válidos. Nenhuma atividade diferida foi executada por esta edição.

**Verificação editorial do adendo:** raiz `docs/plans/` contém dois planos ativos;
L01–L16 e D01–D11 são contínuos; o registro O01–O10 está arquivado, sem execução.
Links/fragmentos, tabelas e preservação dos históricos foram validados pelo checker
local da campanha; `git diff --check` foi repetido para esta alteração. Nenhum teste
de runtime, Actions, registry, daemon ou VPS foi executado.
