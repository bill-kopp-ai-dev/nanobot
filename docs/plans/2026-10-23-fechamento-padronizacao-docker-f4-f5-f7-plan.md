# Fechamento da padronização Docker — F4/F5/F7

- **Preparado em:** 2026-10-23, por fusão dos dois planos de fechamento da padronização
  Docker: o [F4/F5](closed/2026-10-10-f4-f5-closure-plan.md) e o
  [F7 — aceite de operação](closed/2026-10-10-f7-operations-acceptance-closure-plan.md).
- **Estado / revisão pós-I1/I2 (2026-10-23):** D1 está **fechado** (rotação executada
  pelo operador, inventário do agente em §2.1, decisão de histórico registrada);
  D2–D12 continuam sem fechamento integral. I1 concluiu arquitetura/handoff
  (`eb4e3555`) e I2 concluiu runtime 1 e conformance local Linux/amd64 (`0e7ff072`),
  ambos commitados/enviados. A evidência reduz a lacuna core de D7, acrescenta seus
  builds worktree ao resíduo de D8 e atualiza as entradas de D9/D11/D12. I3 foi adiado
  pelo operador; I4–I9 permanecem pendentes. Restore/rollback F4 anteriores continuam
  reaproveitáveis no seu escopo. A
  [auditoria planos × código](../reports/2026-10-23-auditoria-planos-vs-codigo.md)
  §3.4 é o snapshot anterior a I1/I2; suas referências `arquivo:linha` e ferramentas
  externas exigem reconferência, não são observações novas desta revisão.
- **Plano de fase de origem:** [padronização Docker](2026-10-09-docker-standardization-refactor-plan.md),
  seções F4, F5, F7 e F8. Este plano substitui os dois planos de fechamento e passa a ser a
  fonte de verdade do quadro de pendências, hoje desatualizado no plano de fase.
- **Autoridade:** não autoriza reescrita de histórico, push, remoção de containers/imagens,
  rotação de credencial pelo agente, alteração de allowlist ativa, deploy em VPS, tag ou
  publicação. Cada mutação real exige a autorização aplicável e a interface suportada.
- **Numeração:** neste documento, F4/F5/F7 designam sempre as fases do plano de **padronização**
  Docker. As fases homônimas do plano MCP Docker first-class (arquivado) são outras e estão
  consolidadas no [plano integrado](2026-10-23-integracao-pendencias-kg-e-mcp-docker-plan.md).
- **Revisão IaC (2026-10-23):** [I1–I9](2026-10-23-iac-alignment-execution-plan.md)
  tratam distribuição, contratos e handoff IaC. D1–D12 continuam donos das pendências
  locais abaixo (D1 fechado em 2026-10-23). [ADR I1](../Decisions/2026-10-23-open-iac-contracts.md) e
  [handoff](../iac-p0-contract-handoff.md) decidem o alvo; [runtime 1](../agent-runtime-contract.md)
  e [relatório I2](../reports/2026-10-23-i2-runtime-contract-conformance.md) descrevem
  a implementação local. Atualização de plano não é nova execução nem aceite público.

### Contratos de integração aplicáveis a D1–D12

- Docker Hub é o alvo das imagens oficiais abertas, não escolha ainda livre de registry;
  I1 decidiu namespace `pbeanlabs`, imagens `percival-gateway`/`percival-mcp-broker`
  e Weather/OSM como primeiros MCPs oficiais. Acesso/publicação/homologação dependem
  de I3/I5/B13. CI de conformance C1 não faz push. Tags locais/IDs não são digests OCI.
- I1 escolheu `pyproject.toml` como fonte de versão; I2 alinhou fonte/lock/fallback/
  defaults/labels core a `0.1.0`, sem upgrades de dependências nem rename de
  `nanobot-ai`/`nanobot`. D2/D8 preservam rastreabilidade e exigem candidato final
  coerente; não tratam o metadado herdado `0.3.5` como versão atual ou nova release.
- Runtime real é gateway/manager + broker separado, com API opt-in como alternativa
  ao gateway no mesmo estado. CLI/API/gateway compartilham o bind inventariado;
  setup mutável exige writers parados. Compose controla core; manager controla MCPs.
  `capabilities.lock` (I7) e `deployment.lock` (I4) têm owners decididos, mas ainda
  não estão implementados; não descrever export/deployment como funções já disponíveis.
  D4/D10/D11 devem preservar essa fronteira, sem duplicar gestão por Compose/WUD.
- I1 definiu raiz monolítica de referência `/srv/pblabs/config/agent/`, montada em
  `/home/nanobot/.nanobot`, com token dentro da raiz inventariada. I4/C2 validam o
  mapeamento real de `~/.nanobot`/proposta `.percival`, UID/GID e coberturas antes de
  migrar. P0 suporta uma instância Percival por daemon; projeto Compose diferente
  não isola nomes MCP. `chmod 777` de fixture não é política de instalação.
- D6 exige avaliação do candidato exato, não contagem de vulnerabilidades de imagem
  antiga. Fechar triagem F3 não concede waiver nem revoga a política Critical/High.
  D7 verifica usuário efetivo e probes por modo; não exige HTTP healthcheck na CLI.
- D9 cobre o manual MCP; I8 cobre recuperação do core e estado completo, incluindo
  auth/KG/workspace/locks. Aceite local D12 não fecha integração IaC I9, publicação ou
  gates de outro produto. Se um contrato mudar, revalidar só as evidências afetadas.
- I1 escolheu índice JSON estático em GitHub e aquisição por extensão restrita do
  broker. I6/I7 ainda implementam aquisição/schema 2/export; runtime 1 mantém schema 1,
  `local-image`/`pinned-image` e spawn `--pull=never`, sem `repository`/`trustedCatalogs`.
  Novos installs de catálogo exigirão consentimento e começarão sem binds/rede;
  registros existentes não recebem migração de permissões implícita.

## 1. Evidência já produzida (não refazer sem mudança de artefato)

| Fechamento | Evidência | Origem |
| --- | --- | --- |
| Restore byte a byte de Notes e Khan, nas quatro fixtures (Positronic e Percival), SHA-256 igual e leitura OK após restore | [relatório F4/F5](../reports/2026-10-10-f4-f5-closure-report.md) | F4, item 2 |
| Rollback de imagem/configuração A→B→A nos dois gestores (Notes e Khan), com CAS e `tools/list` | [relatório F4/F5](../reports/2026-10-10-f4-f5-closure-report.md) | F4/F6, item 3 |
| Commits dos candidatos publicados nos seis MCPs | [relatório F4/F5](../reports/2026-10-10-f4-f5-closure-report.md) | F5, item 4a |
| Seis MCPs ativos nos dois gestores, 4 `update-image` + 2 `install`, 99 tools observadas | [canário F7](../reports/2026-10-10-f7-canary-execution.md) e [stack local](../reports/2026-10-10-f7-local-stack-provisioning.md) | F7 |
| Inventário de proveniência em 8 repos, 6 identidades distintas, sem `.mailmap` e sem reescrita | [proveniência e identidade](../reports/2026-10-10-f7-provenance-and-identity.md) | F7 P1 |
| Diagnóstico do Khan e das duplicatas (sem órfãos confirmados no snapshot) | [Khan e duplicatas](../reports/2026-10-10-f7-khan-allowlist-and-duplicates.md) | F7 P2 |
| Bloqueios de runtime, segurança e CI | [P4/P5 blockers](../reports/2026-10-10-f7-p4-p5-blockers.md) | F7 P4/P5 |
| Identidades, versão-fonte, aquisição restrita, consentimento, single-writer, layout e sequência B13/publicação/homologação/VPS decididos | [ADR I1](../Decisions/2026-10-23-open-iac-contracts.md) e [handoff](../iac-p0-contract-handoff.md); fonte `eb4e3555` | I1.1–I1.7; entradas de D2/D7–D12 |
| Metadata core `0.1.0`, bind CLI/API/gateway unificado, API opt-in, UID/GID efetivos, root-drop fail-closed, init único e probes por modo | [runtime 1](../agent-runtime-contract.md) e [relatório I2](../reports/2026-10-23-i2-runtime-contract-conformance.md); resultado fonte em `0e7ff072` | I2.1–I2.4; parte core de D7 |
| Startup com broker atrasado, crash/hydrate, persistência e recriação conjunta; 19 checks PASS em Engine 27.5.1 rootful/amd64, com MCP fixture real | relatório I2, §§2–4, `i2-5atl75uj/results.json` no diretório privado ali referenciado | I2.5; parte local de D7, não VPS nem recovery em carga |
| Gateway atual/broker baseline real e caller v1 independente/broker atual; protocolo WebUI 1/schema MCP 1 preservados; CI usa runner isolado e arquiva `results.json` | runtime 1, §5, e relatório I2, §§2/4 | I2.6; compatibilidade core, sem fechar B3/C1 |

**Lacunas residuais de F4/F7** (que os itens abaixo precisam fechar): a prova Khan usa
verificação em filesystem/stderr como proxy, não chamada MCP real; os builds locais de
Notes/AgentMail carregam diff pré-commit na label e não reproduzem o HEAD dos commits atuais;
o stack F7 usou overlay local de Engine 29, que não prova o gate VPS Engine 27.x; e as fixtures
A/B foram removidas ao final do ensaio, então não há par de rollback retido.

**Limites de I2:** seu daemon isolado era Server 27.5.1, sem override Engine 29, mas
isso não certifica VPS. A fixture stdio não homologa Khan nem os seis MCPs reais.
Os builds executados foram baseline `eb4e3555` + diff explícito `-dirty-i2`; o commit
posterior `0e7ff072` não os transforma em builds de checkout limpo. Image IDs estão
no relatório, sem digest OCI público. I2 não produziu scan/SBOM novo, run Actions,
teste Render como serviço ou recovery de trabalho em voo. Compatibilidade wire com
broker antigo não autoriza usar a probe nova que aquele artefato não contém.

## 2. Itens abertos

Responsáveis: **agente** levanta evidência e propõe; **operador** decide, autoriza e assina.
Cada item registra a pendência da tabela do plano de fase entre parênteses.

| # | Item | Critério de aceite | Origem | Resp. | Estado |
| --- | --- | --- | --- | --- | --- |
| D1 | Rotacionar a credencial `operator-admin` e avaliar a exposição no histórico | Rotação pela interface suportada, autenticação com o segredo novo e invalidação do anterior sem registrar nenhum dos dois; inventário de commits/arquivos afetados; decisão explícita sobre histórico privado/remoto. Sem este gate, nenhuma mutação autenticada em instância real | F7 P0 / Extra | operador (rotação) + agente (inventário) | **fechado em 2026-10-23** — inventário do agente em §2.1; rotação executada pelo operador (afirmação do operador: trocou a senha recentemente); decisão de histórico registrada pelo operador: manter o histórico exposto, por se tratar de segredo legado inerte e repositório privado. **O literal foi redigido da árvore nesta revisão** (`docs/reports/2026-10-10-f4-f5-closure-report.md:16`), mas permanece em 32 commits de `origin/main` — remediação de histórico não é parte deste fechamento. Correção do inventário anterior: exposição de 32 commits, não 5; o commit `07f08314` citado antes **não existe**; o valor exposto casa com o verificador legado `operator.json` e **não** com `auth/verifier.json`, a credencial de instância vigente, que nenhum código legado valida. **Não reproduzir o valor em documento versionado** |
| D2 | Matriz de proveniência e política de identidade | Matriz repo → SHA → autor/committer bruto → atribuição confirmada → mapeamento aprovado → image ID/revision revisada; `.mailmap` apenas quando duas identidades forem comprovadamente a mesma pessoa; nenhuma reescrita de `main` publicado | F7 P1 (#10) | agente + operador | **parcial** — levantamento feito; falta decisão de atribuição |
| D3 | Permissão do Khan e projeção efetiva | Decisão registrada do operador sobre a superfície por gestor; lista efetiva extraída do protocolo e verificada nos dois consumidores; `allowedProjects` não confundido com permissão de tool | F7 P2 (#7) | operador | **aberto, e o critério estava errado** — o servidor expõe 17 identificadores `khan_*` (7 de escrita, entre eles `khan_delete_event` e `khan_update_event`) enquanto o canário observou 12 tools: a discrepância precisa ser explicada. **Não existe modo somente leitura** no servidor (busca por `read_only`/`readonly` em `percival-khan-calendar/src/` não retorna nada), então "somente leitura ou subset" não é alternativa de configuração: ou se aceita a superfície, ou se implementa a restrição |
| D4 | Atribuição das duplicatas por container ID | Mapa container → processo/sessão cliente/registry/escopo, com ciclo de vida demonstrado e cardinalidade esperada documentada; limpeza apenas com autorização específica e zero referências confirmadas | F7 P2 (#8) | agente | **parcial, e o mapeamento já é ferramenta** — `nanobot/mcp_docker/inventory.py:136` coleta `containerId` e `:299` renderiza tabela com `percival.mcp-docker.owner`, `.managed-by`, `.server-id` e `.instance-id`. O que falta é o que o inventário não prova: ciclo de vida demonstrado e cardinalidade esperada documentada |
| D5 | Regressão Khan `tools/call` | Chamada MCP real de leitura com evidência no protocolo, não em filesystem/stderr; reproduzir em fixture sem tocar calendário real; investigar a versão do FastMCP/`mcp[cli]` ou registrar limitação aprovada | relatório F4/F5 | agente | **aberto, confirmado** — **não existe** teste de protocolo: buscas por `tools/call`, `call_tool`, `ClientSession`, `stdio_client`, `jsonrpc` em `tests/` e `src/` do Khan não retornam nada, e todos os testes chamam a função por trás do tool (`tests/_helpers.py:24`-`:34`). O isolamento do calendário real está garantido (`tests/conftest.py:11` redireciona `DATA_DIR`/`DB_FILE` e desliga o lock). Versões em jogo: `mcp` 1.30.0 e `fastmcp` 3.4.4 (`uv.lock`), faixas `mcp[cli]>=1.28.1,<2.0.0` e `fastmcp>=3.2.0` (`pyproject.toml:13`-`:14`) |
| D6 | Resíduo OpenSSH `CVE-2026-60002` no gateway (#11a) | Build do gateway em base corrigida com OpenSSH >= 10.4 e regressão de Percival Remote SSH na imagem, **ou** exceção individual documentada e aprovada; OpenVEX do gateway não estendido aos MCPs sem análise por imagem | F7 P4.2 (#11a) | agente + operador | **aberto, sem remediação por I2** — fonte atual preserva base uv/Trixie pinada e `openssh-client=1:10.0p1-7+deb13u4` no `Dockerfile`. O finding Critical e o waiver não aprovado são da triagem F3; I2 não executou novo scan nem teste Remote SSH na imagem. OpenVEX antigo é restrito ao image ID analisado e não cobre esta CVE; não se transfere aos novos IDs I2. Testar OpenSSH Forky fora da imagem não fecha D6 |
| D7 | Consolidar evidência de runtime nos artefatos finais | Runtime 1 por modo, usuário/caps/init efetivos, sinais/EOF, probes/autenticação e persistência; MCP stdio sem porta/TTY/health HTTP e sem init duplicado por gestor. Evidência ligada aos SHAs/imagens finais e aos consumidores afetados | F4/F5 closure, item 2; I2.1–I2.6 | agente | **parcial, com core comprovado localmente em I2** — 19 checks PASS cobrem gateway/API/CLI/broker, doctor/probe autenticada, init/caps/UID, SIGTERM e crash/recreate/hydrate com fixture. Restam artefatos finais e contratos MCP por gestor. A auditoria pré-I2 encontrou tini em OSM/Deep e `--init` incondicional no consumidor Positronic, além de falta de contrato de imagem em Notes/Khan/AgentMail. I2 alterou o core Percival, não esses repositórios; não encerra esses achados nem certifica Positronic |
| D8 | Reconciliar pins e par core com builds de checkout limpo e promover | Rebuild Notes/AgentMail, par core I2 e qualquer candidato alterado a partir de commit limpo, com SHA/versão/labels/imagem coerentes; promover por gestor só com aprovação, canário e rollback independentes; reter último bom e par A/B, com config/dados compatíveis | F7 P4.1 (#4, #6); I2 → I3 | agente + operador | **parcial, com resíduo core explícito** — guard de checkout/worktree já existe em `scripts/percival-docker-build.py`. I2 alinhou metadata core a `0.1.0`, mas seus builds são baseline + diff, não builds do commit limpo `0e7ff072`. A auditoria dos seis MCPs registrou falta de guard equivalente e SHA curto do OSM incompatível com verificação por SHA completo; esses achados não foram corrigidos por I1/I2. Revalidar no candidato final. Sem promoção, rebuild limpo novo ou digest público nesta revisão |
| D9 | Alinhar/exercitar o manual operacional e assinar a retenção | Walkthrough em fixture de update, rollback, restore e falsa falha de health; comandos/APIs e procedimentos compatíveis com runtime 1; política de retenção e revisão trimestral assinada | F7 P3 (#2, #5); handoff I2/I4/I8 | agente (redige) + operador (aprova) | **parcial, precisa incorporar runtime 1** — [manual criado](../operations/mcp-docker-local-runbook.md); existência de `auth init` e `mcp-docker doctor` já verificada não prova o procedimento inteiro. Corrigir no walkthrough API alternativa/single-writer, bind comum/token, significado das probes, init e sinais por modo (gateway/API exit 0 idle; broker 143, sem promessa de drain). I2 não exercitou esse manual nem assinou retenção/revisão trimestral; D10 mantém dono dos comandos Positronic |
| D10 | Caminho de reinstalação do MCP Docker no consumidor Positronic (**item reescrito em 2026-10-23**) | (a) Determinar e registrar qual é o caminho de reinstalação **suportado**, pela interface suportada; (b) corrigir a documentação que promete comandos inexistentes — a skill global `mcp-docker-workflow` lista 11 comandos `positronic mcp server …` (`SKILL.md:31`-`:43`) que **não existem** no pacote de CLI do fork; (c) remover o workaround de edição direta do registry | F7 P3 / relatório F4/F5 | agente + operador | **premissa errada → reescrito** — não há binário `positronic` no PATH, o CLI do fork é `packages/cli` (`@opencode-ai/cli`, bin `lildax`) e a busca por `install-local` em todo o TypeScript do fork, fora de `node_modules` e docs, **não retorna nada**: **não existe comando para corrigir**. O estado real é o registry gerido pelo servidor (`~/.positronic/mcp/registry.json`, `schemaVersion` + 6 servidores) |
| D11 | Skill de gestão F8 e instruções nos `AGENTS.md` | Matriz efetiva dos `AGENTS.md`; skill revisada com dry-run e fixture; ativação pelo operador | F8 (#9) | agente + operador | **parcial, raiz Percival atualizada** — `AGENTS.md` já cobre MCP Docker/IaC, runtime 1 e limites de I2; a ausência citada na auditoria foi resolvida. Restam decisão extensão versus skill própria, matriz dos demais escopos, arquivos Notes/AgentMail ausentes no inventário anterior, revisão/dry-run/fixture e ativação. Reconfirmar esses inventários externos antes de editar; I1/I2 não os alteraram |
| D12 | Assinatura F7 e registro de encerramento único | Relatório único com `pendência → decisão → SHA/image ID → verificação → evidência → operador/data`, inventário pós-cutover sem segredos, URLs dos runs e risco residual; registrar **aceite local**, **aprovação B13**, **homologação pública** e **aceite VPS/deploy** como atos separados, na ordem I1 | F7 P5; I1.6 | operador (assina) + agente (consolida) | **encerramento consolidado bloqueado** por D1–D10, C1–C4 e A1–A9; evidência parcial I1/I2 incorporada, sem assinatura F7. Registro local não certifica VPS e publicação B13 não depende integralmente de I9/C3/C4 públicos; homologação pós-push é gate de promoção |

### 2.1 D1 — inventário de exposição (reexecutado em 2026-10-23, agente)

Método: leitura do working tree, `git grep` sobre todos os commits alcançáveis e
comparação dos dois verificadores por scrypt, sem imprimir o valor em nenhum
registro. Nenhuma mutação de credencial, de instância, de imagem ou de remoto.

| Fato | Verificação |
| --- | --- |
| O literal ainda estava na árvore atual | `docs/reports/2026-10-10-f4-f5-closure-report.md:16` — redigido nesta revisão. `07f28314` removeu o literal de três arquivos, mas não deste |
| Exposição real | **32 commits**, todos ancestrais de `origin/main` (`git rev-list --all` = 4854 commits; os 32 estão em `origin/main`) |
| Arquivos atingidos no histórico | `docs/reports/2026-10-10-f4-f5-closure-report.md` (presente em todos os 32), `docs/reports/2026-10-10-f7-local-stack-provisioning.md`, `docs/reports/2026-10-10-f7-canary-execution.md`, `docs/plans/2026-10-09-docker-standardization-refactor-plan.md` (estes três, apenas em `beaccab9` e `0e90fa2a`) |
| Primeiro commit com o literal | `beaccab9` (2026-10-10) |
| Referência errada do plano anterior | `07f08314` **não existe** no repositório (`git cat-file -t` falha) |
| Entropia do valor exposto | 8 caracteres, **abaixo** do mínimo de 15 da política vigente ([`nanobot/access/password.py`](../../nanobot/access/password.py), `MIN_PASSWORD_CHARS = 15`). Era o segredo do esquema legado, anterior a `auth init`; hoje a política o rejeitaria |
| O literal exposto é a credencial viva? | **Não.** Ele casa com o verificador legado `~/.nanobot/mcp-docker/operator.json` (`scrypt$32768$8$1$…`, mesmo salt/digest) e **não** com `~/.nanobot/auth/verifier.json`, que é a credencial de instância vigente |
| O verificador legado ainda é lido? | **Não.** Nenhum código vigente abre `operator.json`; a única menção em `nanobot/access/credential.py:4` é docstring. A mutação autenticada de MCP Docker passa por sessão do gateway + elevação (`helpers/deploy_mcp.py:137`-`:147`) |
| Arquivos em disco | `~/.nanobot/mcp-docker/operator-password` (9 bytes, 0600) e `operator.json` (98 bytes, 0600) existem; `audit.jsonl` e `config.json` estão limpos. O `operator-password` é o **texto plano** que casa com o verificador legado |
| Arquivos em disco dentro do container | Ambos existem em `/home/nanobot/.nanobot/mcp-docker/` no gateway em execução (bind mount de `~/.nanobot`) — presença, não uso |
| Superfície externa | O `operator.token` do Positronic (`~/.positronic/mcp/operator.token`, 64 hex) **não** é o literal exposto e não é derivado dele |
| Repos irmãos | Nenhum outro repositório sob `/home/bill/Projects/` contém o literal |

**Consequências para o gate:**

1. A rotação de que D1 fala é a do **segredo de instância** (`auth/verifier.json`),
   pelo caminho suportado `nanobot auth change` — não do verificador legado já
   inerte. `auth change` exige a senha atual; `auth reset` é a via de recuperação
   local e exige autorização explícita do operador.
2. A rotação sozinha **não** fecha a exposição no histórico: o literal continua em
   32 commits de `origin/main`. Fechar isso é reescrita de histórico publicado,
   ato do operador, com decisão sobre repositório privado/remoto. Enquanto o
   repositório for privado e o valor não autenticar nada vigente, o risco
   residuo é disclosure do segredo legado inerte.
3. Revogação: o valor legado não concede acesso hoje, porque nenhum caminho
   vigente o valida. Isto **não** substitui a rotação pedida no critério.

**Decisão do operador (2026-10-23):** rotação da senha executada pelo operador e
decisão de **manter o histórico exposto**, por se tratar de segredo legado inerte
em repositório privado. Com isso o gate D1 fecha: rotação feita, inventário
completo, decisão explícita registrada. A remediação do histórico nos 32 commits
não faz parte deste fechamento e permanece como risco residual aceito; o literal
foi redigido da árvore versionada corrente nesta revisão.

**Complementos de aceite após a harmonização:**

- **D7:** reaproveitar a matriz e execução I2 para o core sem repeti-las como tarefa
  inédita. Gateway/API não podem ser writers simultâneos; API é opt-in. Health do
  gateway pode passar sem verifier, enquanto bootstrap protegido retorna 401;
  health do broker autentica e exige `ready: true`. `doctor` e tools/call são provas
  adicionais, não equivalentes a TCP aberto. Gateway/broker devem ser recriados
  juntos quando muda o namespace. I4 ainda entrega deployment/preflight; D7/C1
  comprovam os artefatos finais. Aplicar a matriz de compatibilidade: broker
  baseline exige seu próprio bundle/probe, não a probe I2 inexistente nele.
  Registrar channels incluídos no build: `.venv` é mutável por UID 1000 no startup,
  não por UID alternativo. Deployment imutável/offline exige dependências dos
  channels habilitados pré-instaladas; digest sozinho não fixa mutações posteriores.
- **D8:** para candidatos locais, manter o build limpo e ID verificável; para os
  publicados, aquisição homologada por digest em I3/I5/I6, registrando tag, digest OCI
  e image ID separadamente. MCPs são promovidos pelo manager; o par core é atualizado
  por tooling externo de deployment, nunca por capabilities Compose ou pelo agente.
  Retenção inclui imagem/configuração/dados compatíveis; rebuild não é instalação padrão
  no VPS. Corrigir a discrepância de SHA do OSM antes de alegar proveniência conforme.
- **D9:** acrescentar ao walkthrough o handoff para I4/I8: `deployment.lock` futuro pelo tooling
  de deploy, `capabilities.lock` futuro pelo manager, backup/retorno de estado completo e
  classificação de migrações. Não alegar que rollback MCP substitui recovery do core.
- **D10/D11:** comandos por gestor precisam ser verificados no checkout/launcher instalado,
  sem copiar o CLI proposto de outro documento. Catálogo/manifest não é script autorizado;
  nenhuma skill assume capacidade de pull ainda inexistente nem edita registry/locks
  diretamente. Revisão/ativação de skill permanece no fluxo próprio de D11.
- **D12:** anexar o status dos contratos I1/I2/I4 aplicáveis ao candidato. Sign-off local
  pode avançar sem catálogo público pronto; sign-off IaC I9 requer suas próprias provas.
  I1/I2 estão entregues, I4 pendente. B13 requer fonte/candidato revisados e gates
  locais/Actions/segurança aplicáveis; pull anônimo/homologação são posteriores ao
  push e anteriores à promoção. Não usar a assinatura consolidada de D12 para criar
  ciclo B13 → publicação → VPS/I9 → B13.

## 3. Itens transferidos (fora de escopo, com dono)

| Gate | Dono |
| --- | --- |
| Actions remotas nos sete SHAs candidatos; inventário do VPS; migração/rollback para destino aprovado em I4/C2 no Engine 27.x; novo aceite do risco no alvo | [plano integrado, C1–C4](2026-10-23-integracao-pendencias-kg-e-mcp-docker-plan.md) |
| Distribuição OCI, bootstrap/Compose de deployment, índice, aquisição e locks | [integração IaC, I1–I9](2026-10-23-iac-alignment-execution-plan.md); I1 decidido, I2 local concluído, I3 adiado e I4–I9 pendentes; não duplica D/C |
| Browser WebUI + gateway + broker, matriz end-to-end das oito famílias, testes de UI e acessibilidade | [plano integrado, B1–B6](2026-10-23-integracao-pendencias-kg-e-mcp-docker-plan.md) |
| Autenticação de senha única: ensaio em Engine 27.x, elevação, proxy TLS, expiração, cutover real | [fechamento de senha única, A1–A9](2026-10-11-single-password-acceptance-closure-plan.md) |
| KG nativo: dados reais, ensaio B6/B7, release dos repositórios legados | [plano integrado, A1–A7](2026-10-23-integracao-pendencias-kg-e-mcp-docker-plan.md) |

Uma execução pode satisfazer gates de planos diferentes, desde que cada plano registre a própria
evidência e aponte para o run, inventário ou relatório comum.

## 4. Ordem de execução

```
D1 (credencial) ─┬─→ D8 (promoção) ─┐
D2 (proveniência)┤                  ├─→ D12 (assinatura F7)
D3, D4, D5 (Khan)┘                  │
D6 (OpenSSH) ───────────────────────┤
D7, D9, D10 (runtime/manual) ───────┘
D11 (skill F8) — independente, pode correr em qualquer momento
C1–C4 (Actions/VPS) ───────────────→ D12
```

O diagrama resume dependências do **encerramento consolidado**, não a ordem inteira
de publicação. I1/I2 são entradas já disponíveis; I3 continua adiado e nenhuma
implementação é iniciada por esta revisão. Na retomada, I3.1–I3.3 não exigem push
token; bill prepara o secret Docker Hub `pbeanlabs` no ambiente protegido para
I3.4/I5.3. Pull público é anônimo, sem login local. A migração para `p-bean-labs`
foi recomendada antes de I3.4 para fixar labels de origem antes do digest público;
decisão/execução do operador, sem transferência realizada por I1/I2.

- **D1 é pré-requisito** de qualquer mutação autenticada em instância real.
- **D3** bloqueia a projeção efetiva do Khan e, junto com **D5**, o item 2 do aceite. Se a decisão
  for restringir a superfície, ela vira trabalho de engenharia: não há modo somente leitura.
- **D6** bloqueia F7 e a publicação da primeira versão 0.1.0, e é hoje o item de maior severidade da
  lista: um Critical conhecido no candidato local do gateway. Não há evidência aqui de
  publicação dessa imagem em registry; reavaliar o finding no candidato final.
- **D7** reaproveita I2 no core; o defeito `--init` do consumidor Positronic e os
  contratos MCP faltantes pertencem aos respectivos repositórios, fora da execução
  I2. Reconfirmar o checkout/consumidor antes de corrigi-los; não fechar o defeito
  Positronic com uma prova do broker Percival.
- **D9** e **D10** são executáveis localmente, sem dependência externa. **D10** passou a ser
  verificação de caminho suportado e correção de documentação, não correção de handler.
- **D11** não bloqueia F7, mas fica fechado no mesmo plano por pertencer à mesma padronização; exige
  a decisão extensão-versus-skill-separada e a criação de dois `AGENTS.md`.

## 5. Riscos e critérios de parada

| Risco | Controle |
| --- | --- |
| Apagar evidência ao limpar fixtures | reter um par A/B de imagem conhecido por gestor antes de qualquer nova promoção; `docker image prune -a` e `system prune` nunca são atalho de limpeza |
| Confundir proxy de evidência com prova | verificação em filesystem/stderr não fecha `tools/call`; o critério exige protocolo MCP real |
| `chmod 777` de fixture local virar política de produção | registrar modo e owner reais no inventário antes de qualquer promoção |
| Estender o VEX do gateway aos MCPs | reavaliar findings por imagem e escopo; sem extensão automática |
| Reescrever `main` publicado | `mailmap` altera apresentação, não objetos nem SHA; reescrita é ato separado com autorização específica |
| Prova local ser lida como aceite VPS | I2 usou Server 27.5.1 isolado; F7 histórico usou overlay Engine 29. Nenhum prova o host alvo: inventário e aceite VPS são C2–C4 |
| Preservar `local-only` como veto permanente à proposta IaC | I1 já aditou o contrato e escolheu índice JSON/aquisição restrita; runtime atual ainda é local-only e I6 implementa a evolução. I3/I5 e B13 mantêm gates próprios |
| Commit de I2 ser confundido com release limpa ou scan atual | conservar identidade dos worktree builds e checks originais; candidato limpo e scan/SBOM próprios em D8/I3, Actions em C1 e digest público só após push |

**Parar e escalar** se a credencial exposta ainda der acesso, se uma duplicata não puder ser
atribuída com confiança, se uma imagem de retorno não existir, se a observação divergir da
configuração, se houver Critical sem correção ou decisão, ou se a topologia do alvo divergir do
aprovado. Não eliminar incerteza por `docker rm`, waiver implícito ou edição manual de estado.

## 6. Registo de execução

_Vazio na abertura (2026-10-23). Registrar por item: data, responsável, SHA/imagem/digest,
comando, resultado, artefato de evidência, limitações e decisão do operador. Não declarar item
fechado por teste local, por `Client.Version` ou por ausência de runs._

**2026-10-23 — reverificação contra o código (não é execução).** Todos os itens foram confrontados
com o repositório, com as imagens dos seis MCP e com o host; veredictos em
[auditoria planos × código](../reports/2026-10-23-auditoria-planos-vs-codigo.md) §3.4. Nenhum item
foi executado e nenhum foi fechado. Mudanças de conteúdo: **D10 reescrito** (o comando objeto não
existe nesta máquina), D3 corrigido (não há modo somente leitura), D7 dividido entre defeito de
código e falta de teste, D8 reduzido ao que falta nos seis MCP mais um defeito novo do OSM, D4 e D9
reduzidos ao que falta, D11 desmembrado em tarefas verificáveis.

Quando D12 for assinado, o relatório único deve substituir os snapshots de pendência hoje
dispersos entre o plano de fase, o relatório F4/F5 e os relatórios F7, mantendo os links.

**2026-10-23 — harmonização IaC (não é execução).** Incluídas fronteiras de ownership,
handoff de D7–D11, separação de aceite F7/I9 e dependências de layout e distribuição.
Preservadas as evidências existentes e o estado aberto de D1–D12.

**2026-10-23 — instruções do Percival atualizadas.** O `AGENTS.md` raiz agora cobre
responsabilidades IaC/produto/índice, ownership core/MCP, aquisição por digest, locks,
persistência, testes e gates, com links aos planos ativos. Isso resolve a ausência
dessas orientações na raiz citada no snapshot D11, mas **D11 continua parcial**:
matriz dos demais repositórios, decisão de skill, fixture/dry-run e ativação ainda
exigem suas próprias evidências. A revisão não fecha F8 nem altera runtime.

**2026-10-23 — reconciliação após I1/I2 (revisão documental sobre `ca19cab9`).**
Incorporadas ADR/handoff I1 (`eb4e3555`), contrato/relatório I2 e fonte executável
do core (`0e7ff072`): metadata 0.1.0, API opt-in, single-writer/bind comum,
UID/caps/init/probes, compatibilidade e recovery local. D7 permanece parcial com
essa cobertura core comprovada; D8 inclui explicitamente os builds core worktree;
D9 passa a consumir runtime 1; D11 não repete a lacuna já corrigida no `AGENTS.md`.
D6 permanece aberto, sem scan novo. D12 distingue encerramento consolidado de
aprovação pré-publicação e homologação/aceite no alvo posteriores, conforme I1.6.
I3 permanece adiado por decisão do operador; nenhum item D foi executado ou fechado
integralmente por esta revisão. Relatórios históricos e SHAs/imagens originais
foram preservados; alterações só nos dois planos Docker, sem mutação de instância,
credencial, imagem, repositório externo ou publicação.
Verificação desta revisão: 84 links locais/2 fragmentos e estrutura Markdown nos
dois planos; F0–F8 e D1–D12 preservados; checkers do plano IaC e dos sete docs I2
passaram; `git diff --check` limpo. `sha256sum --check` confirmou os 38 inputs de
I2, inclusive o relatório e os resultados brutos: evidência original reaproveitada,
sem reexecução de testes de produto ou containers.

**2026-10-23 — D1 executado no escopo do agente (inventário; D1 permanece aberto).**
- **Responsável:** agente. **Operador:** ação de rotação e decisão de histórico pendentes.
- **SHA base:** `5b38c3b1` (`main`, igual a `origin/main` no início). **Sem commit e sem push.**
- **Comandos:** `git grep -l -F` sobre `git rev-list --all` com o literal carregado de
  arquivo temporário; `git rev-list origin/main`; comparação scrypt dos dois
  verificadores com `hashlib`; `docker ps`/`docker inspect` para mounts; leitura da
  imagem em execução via `docker exec`.
- **Resultado:** inventário refeito e corrigido (§2.1). O literal **ainda estava na
  árvore atual** (`docs/reports/2026-10-10-f4-f5-closure-report.md:16`) e foi
  redigido nesta revisão; a exposição real é de **32 commits**, todos em
  `origin/main`, não os 5 listados antes. O commit `07f08314`, citado no plano
  anterior, **não existe** no repositório. O valor exposto casa com o verificador
  **legado** `operator.json` e **não** com a credencial de instância vigente
  `auth/verifier.json`; nenhum código vigente valida o legado.
- **Artefato de evidência:** §2.1 deste plano; linha D1 da tabela de §2.
- **Mutações:** apenas a redação documental do literal na árvore de trabalho
  (`git diff --check` limpo). Nenhuma credencial rotacionada, nenhuma instância,
  imagem, container, repositório externo ou publicação tocados.
- **Limitações:** não reproduz o valor em documento versionado; a rotação depende
  do operador; a exposição em 32 commits de `origin/main` permanece até decisão
  do operador sobre reescrita. D1 **não** está fechado.

**2026-10-23 — D1 fechado (decisão do operador; registro do agente).**
- **Rotação:** executada pelo operador (afirmação do operador: trocou a senha
  recentemente). Registrada por declaração do operador; o agente não executou nem
  pode executar a rotação, e nenhum valor de senha foi registrado.
- **Decisão de histórico:** o operador decide **manter** o histórico exposto — o
  literal é de um esquema legado que nenhum código vigente valida, e o repositório
  de desenvolvimento é privado. Remediação dos 32 commits de `origin/main` fica
  como risco residual aceito, fora do escopo deste fechamento.
- **Inventário:** §2.1 deste plano, já produzido acima.
- **Mutações desta etapa:** apenas o estado documental do plano e do relatório de
  auditoria. Sem push, sem reescrita de histórico, sem rotação pelo agente.
- **Estado:** **D1 fechado.** D2–D12 inalterados e abertos/parciais; o encerramento
  consolidado continua bloqueado por D2–D10 e pelos gates externos C1–C4 e A1–A9.
