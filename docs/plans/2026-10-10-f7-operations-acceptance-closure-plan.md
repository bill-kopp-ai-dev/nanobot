# F7 — plano de fechamento do aceite de operação e manutenção Docker

- **Preparado em:** 2026-10-10; plano de trabalho, não declaração de aceite.
- **Fonte:** [plano de padronização, F7](2026-10-09-docker-standardization-refactor-plan.md#f7--aceite-de-operação-e-manutenção), [fechamento F4/F5](../reports/2026-10-10-f4-f5-closure-report.md), [canário local](../reports/2026-10-10-f7-local-stack-provisioning.md) e [governança B13](../percival-governance.md#b13-release-authority).
- **Objetivo:** fechar com evidência a operação local dos seis MCPs em Percival e Positronic, a rastreabilidade de imagens/commits e os gates de segurança, CI e VPS exigidos antes da assinatura F7. F8 (skill e `AGENTS.md`) permanece gate posterior independente.
- **Limite de autorização:** este plano não autoriza reescrita de histórico, push, remoção de containers/imagens, rotação de credencial pelo agente, alteração de allowlist ativa, deploy em VPS, tag ou publicação. Para cada mutação real, obter a autorização aplicável e usar a interface suportada.

## 1. Ponto de partida e correções da lista antiga

O quadro de pendências no plano principal registra snapshots anteriores. Atualizar seu status **somente depois** de anexar as evidências correspondentes; não executar novamente trabalhos apenas porque a tabela está desatualizada.

| Pendência do plano principal | Situação verificada em 2026-10-10 | Lacuna de fechamento |
| --- | --- | --- |
| #1, #11 — F3 e segurança | #1 fechada como **triagem documental**, não como ausência de vulnerabilidades. Broker 0 Critical/High; há Critical OpenSSH no gateway e High nos runtimes Debian. OpenVEX existente é restrito ao image ID do gateway. | Resolver ou aprovar exceção individual do Critical; validar aplicabilidade das High por imagem e artefatos finais em CI. Nenhum waiver presumido. |
| #2 — F4 | [Relatório F4/F5](../reports/2026-10-10-f4-f5-closure-report.md) registra restore byte a byte de Notes/Khan nas quatro fixtures e rollback A→B→A nos dois gestores. | Consolidar runtime efetivo (SIGTERM/PID 1, stdio/HTTP e auth) nos artefatos finais; investigar Khan `tools/call` sem resposta no ensaio de fixture antes de afirmar aceitação funcional. |
| #3 — F5 | Workflows implementados, commits MCP publicados; `gh auth status` nesta revisão ainda informa ausência de login. | Runs verdes nos SHAs finais dos sete repos, manifests/SBOM baixados e confrontados com fonte, locks, bases, IDs e labels. |
| #4, #6 — pins Percival | [Canário F7](../reports/2026-10-10-f7-local-stack-provisioning.md) registra 4 updates + 2 installs e 6/6 conectados no Engine local 29.7.2. | Reconciliar pins de runtime construídos com diff contra builds dos commits finais; observar novamente após eventual promoção. Engine 27.x do VPS é gate distinto. |
| #5 — rollback Positronic | Ensaio A→B→A de **fixtures** realizado para Notes/Khan nos dois gestores. | Documentar que não restaurou os quatro IDs antigos removidos; estabelecer e reter par conhecido A/B para rollback futuro, por gestor, sem prometer recuperação de IDs inexistentes. |
| #7 — Khan | `~/.positronic/mcp/servers/khan-calendar.json` tem 12 `allowedTools`; o registry tem revisão 8 e a config revisão 1. Percival expõe 12 tools, `toolsDisabled: []`. | Decisão explícita do operador sobre leitura/escrita e escopo por gestor; registrar e verificar projeção efetiva. Não confundir `allowedProjects` com `allowedTools`. |
| #8 — duplicatas | Snapshot F0 tinha dois AgentMail e dois Deep Research Positronic. No runtime atual existem múltiplos containers stdio com nomes aleatórios e seis `percival-mcp-*` gerenciados separadamente. | Atribuir cada instância a processo/sessão e demonstrar ciclo de vida; simultaneidade não prova órfão. Limpeza apenas se órfão comprovado e aprovada. |
| #10 — identidade | Commits recentes dos oito repos envolvidos exibem várias identidades de autor **e** committer (`@percival.local`, `@example.com`, `@positronic.local`, noreply e Gmail); não há `.mailmap` nesses repos. | Identificar quem efetivamente assinou/produziu cada mudança, corrigir configuração futura e escolher representação histórica aprovada, sem atribuir commits do agente ao operador por conveniência. |
| Extra — credencial | Credencial operator-admin foi incluída em documentos versionados; retirada da árvore corrente, ainda presente no histórico/remoto segundo [relatório F4/F5](../reports/2026-10-10-f4-f5-closure-report.md). | Rotação via interface suportada e verificação; revisão da extensão do histórico por metadados/varredura sem imprimir o valor; decisão do operador sobre tratamento do histórico remoto. |
| Extra — manutenção Positronic | `mcp server install-local` falhou silenciosamente no ensaio F4; uma edição direta de registry foi usada somente como workaround de fixture. | Corrigir e testar caminho suportado, ou registrar limitação/alternativa suportada aprovada antes de declarar reinstalação recuperável. |

**Conflitos a apurar, sem apagá-los:** a prova Khan da fixture relata `tools/list` com seis tools em uma fase e ausência de resposta a `tools/call`, enquanto o canário final informa 12 descobertas e uma chamada `khan_get_status`; comparar image IDs, versão FastMCP, transporte e cliente dos dois ensaios. Rebuilds Notes/AgentMail dos commits atuais têm IDs diferentes dos pins em execução: funcionalidade equivalente não comprova identidade de artefato.

## 2. Pacotes de trabalho e ordem de execução

### P0 — Conter credencial e fixar baseline (pré-requisito das mutações autenticadas)

**Responsáveis:** operador rota credencial e decide tratamento do histórico; agente prepara inventário redigido e verifica efeitos.

1. Registrar HEAD, status do worktree, imagem/pin por ID, registry/revision, escopo, mounts/UID/GID, instâncias e backups dos sete repos de runtime e do consumidor Positronic. Não copiar env, senhas, tokens ou `docker inspect` integral para artefatos versionados.
2. Rotacionar operator-admin pelo mecanismo suportado; verificar autenticação com o segredo novo e invalidação do antigo sem registrar nenhum deles. Inventariar commits/arquivos potencialmente afetados pela exposição e decidir separadamente se histórico público/privado requer intervenção; jamais rebasear `main` publicado por implicação deste plano.
3. Preservar backups/configurações e image IDs de retorno antes de qualquer nova promoção; confirmar o dono de cada diretório persistente. `chmod 777` da fixture local não é política de produção.

**Saída/gate:** inventário datado sem segredos + registro de rotação e verificação (sem valor da credencial). Sem esse gate, nenhuma operação nova autenticada em instâncias reais.

### P1 — Procedência e identidade (#10; pode correr em paralelo a P2/P3)

**Responsáveis:** agente levanta evidência e propõe mapeamento; operador confirma atribuições e política de publicação.

1. Para cada um dos seis MCPs, gateway e consumidor Positronic, comparar autor e committer do intervalo afetado, suas configurações Git atuais, SHA da fonte e OCI revision/diff hash das imagens promovidas. Separar identidades reais de placeholders e identidades de automação; sinalizar autoria incerta.
2. Escolher por identidade: manter atribuição original, adicionar `.mailmap` **somente quando duas identidades forem comprovadamente da mesma pessoa**, ou corrigir commits futuros. `mailmap` muda a apresentação do log, **não** os objetos, assinaturas, identidades gravadas nem o SHA. Reescrita dos commits já enviados exige decisão explícita e plano de impacto para clones, CI, pins e proveniência; não é a opção padrão.
3. Produzir matriz repo → SHA → autor/committer bruto → atribuição confirmada → mapeamento aprovado → image ID/revision; verificar logs com e sem `--use-mailmap`, além dos manifests de build.

**Saída/gate:** matriz de proveniência revisada, aliases aprovados por responsável e configuração futura coerente; B13 recebe referência a SHAs/imagens e ressalvas pendentes antes de publicação.

### P2 — Khan e duplicatas (#7/#8; diagnóstico primeiro)

**Responsáveis:** operador decide permissão do Khan; agente comprova projeção, lifecycle e propõe correção se necessária.

1. Apresentar ao operador as alternativas Khan: as 12 tools atuais (incluindo escrita/exclusão), somente leitura, ou subset nominal. Registrar escolha para Positronic e Percival, justificativa e alcance dos dados reais; confirmar se `khan_delete_event_safe` e demais mutações são desejadas. Registrar em ADR ou em `docs/percival-governance.md`. Somente após aprovação, aplicar por API/CLI do gestor com revisão atual, validar tools permitidas e negadas e preservar rollback da configuração.
2. Investigar duplicatas por **container ID**: imagem, labels filtradas, criação, PID/PPID do `docker run`, processo/sessão cliente, registry e escopo, stderr/log redigido e `docker events` quando disponível. O código Positronic em `source/opencode/packages/positronic-mcp-docker/src/managed.ts` monta `docker run --rm --init --interactive` para stdio; portanto sessões concorrentes podem gerar containers legítimos sem labels do broker. Separar discovery/fixture de sessões ativas; verificar desaparecimento após encerramento controlado do consumidor e repetição em fixture.
3. Se houver container sem cliente após janela de observação, identificar referências, estado de dados e owner; propor lista por ID e ação suportada. Parar/remover **somente** com autorização específica e zero referências confirmadas. Se forem instâncias legítimas, documentar cardinalidade esperada e lacuna de labels/observabilidade, sem cleanup.
4. Confrontar a regressão Khan `tools/call` com o canário final usando a mesma imagem e cliente; reproduzir em fixture sem tocar calendário real. Corrigir ou documentar limitação aprovada, com evidência de chamada MCP efetiva (não apenas `tools/list`/`khal` CLI).

**Saída/gate:** decisão formal, lista efetiva de tools testada nos dois consumidores; mapa container → criador/consumer/sessão e conclusão documentada sobre órfãos; execução `tools/call` comprovada ou desvio aceito explicitamente pelo operador.

### P3 — Manual operacional e exercício (#2/#5 e etapa 6)

**Responsáveis:** agente redige e valida em fixture; operador aprova política de retenção e manual.

1. Criar `docs/operations/mcp-docker-local-runbook.md` com link na governança. Cobrir inventário seguro antes de agir; build com SHA/lock/base e pin por ID; atualização por serviço e por gestor (Positronic `update-image` + `configure` após novo `configurationId`; Percival API/UI com CAS/journal); backup e restore de Notes/Khan; rollback A→B→A e falha de imagem ausente; incidentes, falso `unhealthy` em stdio versus HTTP health e readiness MCP; SIGTERM/PID 1; coleta redigida e escalonamento.
2. Vincular sem duplicar o [runbook F5 de migração/recuperação](../mcp-docker-f5-runbook.md). Incluir revisão **trimestral** de bases/locks/Trivy/SBOM, gatilho urgente para CVE, owner e janela de revisão; propor regra explícita para retenção de IDs atuais/último bom/fixtures e limite de imagens intermediárias. Os números e a eliminação de qualquer ID exigem escolha do operador e verificação de referências em ambos os gestores.
3. Executar walkthrough em fixture descartável para update, rollback, restore e falsa falha de health; comparar texto do manual com comandos/API instalados e com [evidências F4/F5](../reports/2026-10-10-f4-f5-closure-report.md). Verificar caminho suportado de reinstalação Positronic e resolver ou aceitar formalmente seu bug; não instruir edição direta de registry real.

**Saída/gate:** manual revisado com links válidos, política de retenção assinada e log redigido do exercício; não extrapolar restore em fixture para backup real no VPS.

### P4 — Fechar runtime, segurança e CI (#2/#3/#4/#11)

**Responsáveis:** agente implementa/avalia; operador disponibiliza acesso GitHub e decide exceções, promoção de pins e risco residual.

1. Fixar o **SHA candidato** por repo após P1/P2/P3; verificar checkout limpo e reconciliar imagens ativas com builds dos SHAs atuais (Notes/AgentMail diferem conforme relatório F4/F5). Promover novo image ID por gestor somente se aprovado, com canário/rollback independente e retenção do último bom. Repetir smokes de SIGTERM/init, auth/loopback, stdio/HTTP e MCP no artefato final **apenas onde fonte/config/imagem mudou**.
2. Fechar OpenSSH do gateway por build/teste de base corrigida e regressão Remote SSH, **ou** exceção individual documentada e aprovada; reavaliar os demais findings por imagem e escopo real, sem estender automaticamente o VEX do gateway aos MCPs.
3. Operador autentica `gh`; agente consulta/dispara workflows adequados nos **sete** SHAs candidatos (gateway/broker + seis MCPs), registra URLs, status e SHA executado e baixa manifest/SBOM/scan. Comparar locks, base digests, image IDs e labels; corrigir falhas e repetir apenas os jobs afetados. `workflow_dispatch` pode ser necessário no gateway quando a mudança é somente em docs. Não alegar gate F5 verde baseado só em tests locais ou ausência de runs.

**Saída/gate:** F4 e F5 com relatórios atualizados, runs verdes e artefatos confrontados com os candidatos, risco F3 resolvido ou exceção explícita aplicável; nenhum finding alto é considerado resolvido apenas por uma nota genérica.

### P5 — VPS e assinatura F7

**Responsáveis:** operador controla acesso, janela e aceite; agente prepara checklist/evidência e apoia ensaio autorizado.

1. Aplicar os gates independentes do [plano MCP Docker first-class](2026-10-06-mcp-docker-first-class-execution-plan.md): Browser WebUI + gateway + broker, inventário real VPS, Engine 27.x, socket só no broker, mounts/UID/GID/token, restore/journal, boot/recreate e rollback da migração de estado conforme [runbook F5](../mcp-docker-f5-runbook.md). O overlay local Engine 29 não prova compatibilidade no VPS.
2. Reconciliar inventário pós-cutover, instâncias de cada servidor por gestor, pins e dados; anexar checklist com resultado, hashes/URLs, limitações e decisões do operador. Não executar deploy/cutover sem autorização e plano de retorno próprio.
3. Atualizar o quadro F7 do plano principal item a item com link para evidência; registrar aceite **local** separado do aceite **VPS/deploy** e da aprovação B13 de release no SHA final. F7 geral só fecha quando gates locais, CI/segurança, VPS e assinatura explícita estiverem completos.

## 3. Dependências, critérios de parada e handoff

**Caminho crítico:** P0 → mutações autenticadas; P1/P2/P3 → candidato estável e manual; P4 → CI/segurança com SHAs finais; P5 → aceite VPS e assinatura. P1, investigação read-only de P2 e redação de P3 podem avançar em paralelo. Se uma imagem/config mudar após CI, invalidar a evidência afetada e atualizar o candidato; sem prazo ou custo aprovado, não estimar data de conclusão.

**Parar e escalar** se a credencial exposta ainda der acesso, se `tools/call` Khan falhar na imagem final sem decisão de limitação, se uma duplicata não puder ser atribuída com confiança, se faltar imagem de rollback, se a observação divergir da configuração, se houver Critical sem correção/decisão ou se a topologia VPS divergir da aprovada. Não eliminar incerteza por `docker rm`, waiver implícito ou hand-edit de estado.

**Registro de encerramento recomendado:** um relatório F7 único com tabela `pendência → decisão → SHA/image ID → verificação → evidência → operador/data`, links ao manual e aos relatórios F4/F5/F3, inventário pós-cutover sem segredos, URLs dos runs e declaração de risco residual. A aprovação final de B13 para release é ato separado do fechamento técnico local.
