# Plano 3 — Implantação, recuperação e operação

- **Estado:** **diferido e arquivado em 2026-10-25**, a pedido de bill. Nenhuma destas
  etapas será executada no futuro próximo. Este documento conserva escopo, critérios,
  origens e controles para retomada; não é plano ativo, backlog de execução ou
  autorização. Não existe data de retomada definida.
- **Planos ativos:** somente Plano 1 (prontidão local) e Plano 2 (qualificação/
  distribuição). Nenhum item daqui bloqueia o fechamento desses planos.
- **Motivo/decisão:** deploy, testes em VPS, rollout/cutover e trabalhos estreitamente
  dependentes (inventário de alvo, backup/restore de estado real, migração real, pins A/B,
  canário e aceite operacional) não são prioridade no horizonte próximo informado pelo
  operador. A retirada não os declara concluídos nem elimina o histórico.
- **Mapa vigente:** [adiamento e classificação de escopo](../../reports/2026-10-25-three-plan-consolidation.md#deferred-deployment-vps).
- **Objetivo:** instalar/atualizar uma combinação compatível de core, configuração,
  autenticação e dados, com backup/retorno medidos e aceite específico do alvo.
- **Dono:** bill aprova host, dados, janelas, riscos e cortes; agente verifica/executa
  por interface do owner autorizado. Tooling IaC controla core; manager controla MCPs.
- **Entrada:** contratos I1/runtime 1; [Plano 1](../2026-10-25-01-product-readiness-plan.md)
  entrega comportamento local e [Plano 2](../2026-10-25-02-qualification-distribution-plan.md)
  qualifica os artefatos. [Mapa integral](../../reports/2026-10-25-three-plan-consolidation.md).
- **Baseline:** análise documental sobre `5f77f438`, sem novo inventário host/gestor.

## 1. Fronteiras e contratos preservados

Preparar deployment/backup em fixture não precisa esperar publicação ou host real;
aplicar no VPS exige inventário e autorização próprios. I3 permanece adiado. O pedido
de reorganizar planos não autoriza instalação Docker, OpenTofu apply, acesso remoto,
promoção, mudança de pins/credenciais, migração de dados ou limpeza.

Decisões [I1](../../Decisions/2026-10-23-open-iac-contracts.md),
[handoff](../../iac-p0-contract-handoff.md) e [runtime 1](../../agent-runtime-contract.md)
regem execução; [runbook local](../../operations/mcp-docker-local-runbook.md) detalha
gestores e transportes. F7/D12 e D11 administrativo permanecem encerrados com limites;
seis MCPs canariados em 2026-10-10 não provam adoção dos candidatos posteriores.

Uma instância Percival por daemon no P0; Compose/WUD (se validado) gerencia só core,
MCP Manager/gateway com broker é dono de seus containers. Sem segundo writer/registry.
Gateway não recebe socket/CLI Docker; host R/W e acesso indireto ao token/broker
continuam risco B23–B25, exigindo novo aceite no alvo, não promessa de isolamento total.

## 2. Atividades canônicas

| ID / origem | Entrega e aceite verificável | Estado / dependências |
| --- | --- | --- |
| O01 / I4.1–I4.6 | Bundle separado de produção, layout/preflight, bootstrap idempotente/manual e transação `deployment.lock` do par core; critérios §3. Implementação IaC no seu workspace, contratos/correções de produto aqui | **Pendente**; local com I1/I2 e imagens fixture rastreadas; prova pública exige D06, aplicação VPS exige O03 |
| O02 / I8.1–I8.7, extensões V02/V03 | Mecanismo de backup **do estado inteiro**, RPO/RTO aprovados, update do par, restore independente medido e falhas; critérios §4. Estágio local antes de O08, extensão no alvo produzida por O08/O09 | **Pendente**; core local O01; catálogo/restore remoto requer D08/D09. Não espera I5c para iniciar backup |
| O03 / VPS-C2 | Identificar host/staging, conta/SSH, projeto Compose, paths/owners, proxy, janela e responsável; inventário read-only datado/redigido por `scripts/percival-vps-inventory.sh`. Client/Server, socket/GID, data-root/aliases/submounts, portas e layout aprovados | **Bloqueado por host**, bill fornece/autoriza. Pode anteceder publicação e L03 |
| O04 / R02 | Antes de cada corte, aplicar mecanismo O02 ao contexto real por owner/serviço: pin A/B, configurações/revisões/CAS/allowlists/mounts/dados atuais, backup privado íntegro e retorno ensaiado. Reter A disponível; IDs removidos não reaparecem ao trocar config | **Pendente**; D01 e antes de mutação. Rebuild funcional não é imagem bit-idêntica |
| O05 / R04 | Promoção/canário do conjunto aprovado, um consumidor/gestor por vez; ordem Deep Research → OSM → AgentMail → Weather → Khan → Notes. Manager suportado/CAS; handshake/list/call segura, imagem/init/labels/portas/probes/sinais/logs/persistência; retorno para A em falha | **Não executado para o novo conjunto**; D01/D03/D04-R03/D06 e O04, com autorização específica |
| O06 / AUTH-A7/P2-F | Cutover de autenticação da instância real: identificar volume/arquivos sem valores, backup privado de imagem/config/auth/dados e senha fornecida interativamente; sucesso após rehearsal L03, retorno da combinação inteira em falha | **Aberto**, bill autoriza corte, L03 aprovado/O04. Nunca binário antigo sobre estado parcialmente migrado |
| O07 / KG-A6, B6/B7 de dados | Operador executa ensaio em cópia autorizada de bundle real: backup inteiro verificável, doctor, idempotência `ak-migrate-lateral-links --apply`, leitura pós-nativo no legado e rollback. Registrar decisão de `kg.mode="native"`; corte real só com autorização própria | **Bloqueado por L08 e cópia**, bill. Não operar sobre bundle original nem inferir que dado sintético substitui real |
| O08 / VPS-C3, AUTH-A9/P4 extensão | Aplicar no alvo aprovado receita O01 e ensaios locais O02, imagens homologadas D06 no fluxo público; provar topologia/segurança, Browser+gateway+broker, auth/proxy, oito famílias, persistência/recreate/recovery/locks e retorno | **Bloqueado por O03/O01**, mais gates do candidato. Produz prova-alvo de O02; não espera O02 integral no alvo antes de poder ensaiá-lo |
| O09 / VPS-C4, I9.1–I9.4 | Aceites separados local/CI/público/staging-VPS/B13, matriz requisito→repo/SHA/digest→teste→decisão, walkthrough independente manual/automatizado e handoff de runbooks/limitações/manutenção. Novo aceite expresso bill no alvo e risco indireto; certifica só Percival | **Pendente**, O08 e I1–I8/gates aplicáveis; P0 público exige D07-I5c e D08 nos três apps |
| O10 / R05, R14 | Inventário pós-corte e retenção A/B nos dois gestores, mapa de referências e classificação individual dos resíduos §5. Remoção nominal só com zero referências e autorização própria; nenhuma limpeza/prune implícita | **Pendente**, inventário inicial pode ser preparado; pós-corte depende O05/O06/O08 aplicáveis |

AUTH-A9 não cria segundo gate VPS: inventário é O03 e prova de autenticação no alvo
integra O08, com conclusão no registro O09. O07 preserva propriedade pessoal bill e
não se torna condição indiscriminada da publicação de MCP/core sem migração KG.

## 3. O01 — deployment e commit de estado aplicado

1. Confirmar repo/workspace IaC e dono/acesso; fontes em Downloads são referência,
   não workspace pronto. OpenTofu provisiona, cloud-init/bootstrap prepara host;
   caminho manual equivalente disponível, sem depender de `curl | sh`.
2. Aprovar mapa host→container. `/srv/pblabs/config/agent/` é referência host;
   `/home/nanobot/.nanobot` segue path interno suportado, um bind de estado validado.
   CLI/API habilitada/gateway leem a mesma instância; não renomear `.nanobot` para
   `.percival` nem fragmentar estado por convenção documental.
3. Token broker sob estado verificado, acessível a gateway/broker com owners/GID/modes
   testados (receita atual 0640), sem imprimir conteúdo. Path de secrets separado
   exige evolução/prova de MountPolicy. Proteger **também** backups/locks/secrets novos
   fora da raiz hoje mascarada; aliases/submounts/UIDs não reabrem superfícies Full.
4. Compose agregado de produção sem `build:`/`:dev` ou bind de fixture herdado;
   imagens por tag+digest, broker sidecar/rede compartilhada, init único, socket só
   no broker. Validar lista `-f`, diretório-base/env/project name efetivos. CLI setup
   one-shot, API opt-in só com chave distinta; overlay Engine29/bwrap não é padrão.
5. Preflight valida schema/contrato/revisão/bundle/plataforma, disco/backup/portas,
   todos os pais/permissões, UID/GID/socket/data-root, Engine/CLI/Compose e nome real
   do gateway, sem literal inventado. Server 27.x continua gate do broker; homologar
   patch seguro/disponível. Incompatibilidade demanda decisão/testes, não downgrade
   ou uso silencioso de override descartável Engine29.
6. Sequência: preflight → paths/owners/credenciais **ausentes** → adquirir imagens
   aprovadas → setup CLI interativo → subir core → probes conjuntos/persistência →
   recreate → commit do lock. Reexecutar preserva senha/token/config/CAS/dados/digest;
   sem senha default, rotação automática ou `chmod 777`.
7. `deployment.yaml` é intenção; lock é aplicado somente após par completo/readiness/
   persistência. Exclusão mútua por instância, geração esperada, operação registrada,
   replace durável no mesmo filesystem e leitura de confirmação. Falha não avança
   sucesso. Crash pode deixar runtime novo/lock antigo: reconciliar explicitamente,
   não editar lock à mão nem prometer transação global Docker/config/filesystem.
8. Instalação limpa e segunda execução em fixture/VM; falha parcial, disco cheio,
   erro rename/fsync e updates concorrentes. `tofu fmt -check`/`validate` no workspace
   real antes de plan/apply separadamente autorizados; state/plan sensível privados.

## 4. O02/O04/O08 — uma estratégia de recuperação, três aplicações

O02 constrói o mecanismo; O04 o aplica ao serviço/gestor antes do corte; O08 o
revalida no alvo. Reutilizar prova identificada não dispensa o backup atual nem cria
três implementações de restore.

- **Cobertura:** config/auth/token, sessões/workspace/memória/KG/DB, MCP
  config/audit/journal/transições/backups, locks/bundle e dados externos dos apps.
  Separar caches reconstruíveis do estado autoritativo e resolver paths absolutos
  configurados. `persistent: true` não comprova persistência de dados externos.
- **Política:** bill define frequência/retenção/destino/criptografia/chaves/espaço,
  RPO (perda tolerável) e RTO (tempo-alvo). Sem metas numéricas inventadas; rever
  D02-R06/L12 antes de copiar conteúdo com secrets válidos.
- **Consistência:** parar/quiescer writers ou snapshot consistente de DB/SQLite/apps;
  hashes/revisões/UID/GID/modes e combinação core/config/dados. Cópia viva não prova
  backup. Raw e secrets privados e protegidos de Full, nunca artifacts públicos.
- **Update:** tooling externo troca o par compatível, suspende mutações MCP na janela,
  resolve operações em voo e recria sidecar com gateway quando necessário. Compose
  não recria os MCPs nativos; probes conjuntos antes do lock.
- **Retorno:** distinguir runtime-only de migration-bearing. Para o segundo,
  restaurar imagem+config+auth+dados compatíveis; imagem antiga sozinha não desfaz
  migração. Falha no restore fica observável/pendente e com acesso controlado,
  nunca anunciada como rollback OK.
- **Falhas:** registry/índice fora, cache vazio/verificado, 429/backoff limitado,
  pull demorado/CAS, crash antes do lock, segundo serviço falho, disco/rename/export
  atrasado. Sem fallback de digest nem desinstalar MCP instalado por indisponibilidade.
  Imagem em cache não garante tool offline se ela chama API externa.
- **Restore medido:** fixture independente, não apenas reatar bind original; login,
  leitura/escrita fixture, hashes/doctor KG/dados MCP/reconciliação e métricas contra
  RPO/RTO aprovados. Depois O08 acrescenta proxy/mounts/GID/UID/topologia/risco do alvo.

## 5. O05/O10 — promoção local e achados condicionais

Gates históricos F3/D8 exigem C1 e DIST-B6 antes de promoção do novo conjunto.
D01 pode pedir decisão/aditamento sobre caminho local versus publicado; até que
exista essa decisão explícita, **não dispensar D06 por inferência**. Preparar fixtures
e inventário não é promover. O05 não autoriza por si operação em gestor Positronic.

Na execução: owner/Percival ou Positronic, interface suportada, CAS/revisão e
configurationId relidos; imagem A retida; handshake/list/call segura por serviço;
um init efetivo, labels dos dois esquemas, SIGTERM/restart/persistência. Stdio sem
TTY/porta/probe HTTP, stdout só JSON-RPC; Docker unhealthy não substitui MCP readiness.
Cada serviço/gestor tem resultado e rollback independentes. HTTP exige auth/bind/probe
do profile homologado, não suposto suporte universal do bridge.

| Origem R14 / achado | Destino e critério vigente |
| --- | --- |
| F0 A1/A2/A9: metadata core/broker, tag local, override Engine29 | D01/O01 reconciliam par/versionamento/pin imutável; runtime de desenvolvimento não homologa produção |
| F0 A5/A6: double init e imagens dirty antigas | Lógica corrigida no candidato não prova adoção: O05 verifica imagem e init no consumidor |
| F0 A7: pins compartilhados | O04/O10 cruzam referências **dos dois gestores** antes de retenção/remoção |
| F0 A8: dados Notes/Khan múltiplos por gestor | Bill decide consolidação; O01/O02 mapeiam dados/retorno antes de migração, sem mover por semelhança de path |
| F0 A10 e broker Compose preexistente reportado órfão | Inventário/owner/referências atuais; mensagem Compose não prova descarte. Fixtures `d6-nopip`, `d7host-noinit`/volume exigem classificação nominal |
| F0 A12: labels Compose antigos | `.Image` observado é evidência runtime, não label Compose herdado |
| F0 A13: API key vazia/API não ativa | Fail-closed correto; só habilitar profile API escolhido com chave distinta fornecida pelo owner |
| F0 A14: sem digest remoto | D06/D07, não derivar OCI de image ID |
| Diagnóstico Deep `f5-recheck` construído com contexto Notes | Nunca candidato. Reter/remover só por decisão nominal de O10 |
| Retenção/revisão operacional | Política local assinada, revisão trimestral em **2027-01-24**; scan antes de promover não espera essa data. Revisão pin Arch é D10 |

## 6. Sequência e marcos

| Marco | Pré-condição | Resultado |
| --- | --- | --- |
| Preparação local | I1/I2 existentes e autorização de fixture | O01 + parte local O02; D09 pode avançar em paralelo lógico |
| Descoberta do alvo | Bill identifica/autoriza host | O03 read-only, sem esperar publicação nem escrever no alvo |
| Rehearsals de dados/auth | L03 para auth; L08/cópia para KG | O06 preparado em privado e O07 ensaiado pelo operador; sem corte real implícito |
| Elegibilidade do corte | D01/D03/D04/D06 aplicáveis e retorno atual | O04; depois O05/O06 com aprovação e janela próprias |
| Implantação pública no alvo | O01/O02 locais, O03, D06/D08/D09 conforme release e autorização | O08 produz prova-alvo de recovery/auth/Browser; C3 não espera I8 integral para produzir essa prova |
| Aceite e manutenção | O08 e gates aplicáveis concluídos | O09 assinatura alvo/I9; O10 inventário/retenção e responsabilidades |

Não impor ordem artificial O05→O08 se ambientes independentes; cada corte usa
seus próprios gates. O07 é cadeia pessoal de dados KG, não barreira para trabalho
UI/MCP independente. B13 precede publicação; aceites O08/O09 vêm depois da
homologação pública, sem ciclo release↔VPS. Nenhuma data/orçamento novo aprovado.

## 7. Evidência e encerramento

Matriz O*: requisito/origem → repo/SHA/contrato → par/imagem/digest/plataforma →
ambiente/datado/host redigido → teste esperado/observado → artefato/hash/URL →
decisão bill/risco/limitação → próximo responsável. Reusar V01–V04/V07–V10/V15/
V20–V24 da [especificação IaC histórica](2026-10-23-iac-alignment-execution-plan.md)
com identidade, limites e extensão requerida; prova local não fecha VPS.

Parar se não houver autorização/alvo/retorno, se Server/digest/plataforma divergirem,
se surgir blocker da política de vulnerabilidades, se paths/UID/máscaras falharem,
se houver writer concorrente ou secrets em logs. Sem prune, hand-edit de estado/
locks/journal ou remoção por nome/tag/idade. Remoção de registro preserva dados.

Fecha o plano quando O01–O10 têm evidência/aceite aplicável ou transferência explícita
aceita com dono e risco. O09 exige walkthrough independente e novo aceite bill
no alvo, com manutenção/runbooks/owners transferidos; não é simples consolidação
de PASS locais. O aceite Percival não certifica Positronic nem aprova release B13.

**Próxima ação:** preparar O01/O02 em fixture quando autorizado e obter de bill
o alvo para O03; nenhum inventário de VPS foi executado nesta reorganização.
