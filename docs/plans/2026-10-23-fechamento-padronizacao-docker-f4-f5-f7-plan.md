# Fechamento da padronização Docker — F4/F5/F7

- **Preparado em:** 2026-10-23, por fusão dos dois planos de fechamento da padronização
  Docker: o [F4/F5](closed/2026-10-10-f4-f5-closure-plan.md) e o
  [F7 — aceite de operação](closed/2026-10-10-f7-operations-acceptance-closure-plan.md).
- **Estado / revisão pós-I1/I2 (2026-10-23):** D1, D2, D3, D4 e D5 estão **fechados**
  (D1: inventário do agente em §2.1, rotação e decisão de histórico do operador;
  D2: matriz de proveniência em §2.2, atribuição confirmada, `.mailmap` aplicado nos sete repositórios
  e rebuild limpo dos seis MCPs; D3: levantamento da superfície em §2.3, decisão do
  operador e aplicação em §2.4 — 12 tools do Khan liberadas nos dois gestores,
  prompts/resources registrados como limitação; D4: atribuição das duplicatas em
  §2.5 — mapa container → dono → contexto nos dois gestores, ciclo de vida
  demonstrado, cardinalidade formalizada e nenhuma limpeza; D5: regressão
  `tools/call` do Khan em §2.6 — o defeito do F4/F5 não reproduz com cliente MCP
  real, causa isolada no harness × camada `fastmcp` 3.x, teste de protocolo e
  conformance com `tools/call` gravados no repo do Khan); **D7: fechada em
  2026-10-24** (§2.7 — core reaproveitado do I2, contratos dos
  seis MCPs medidos por gestor, um defeito de sinal novo no caminho do
  Percival: sem `--init`, o `docker stop` de um MCP sem init passa o grace
  period inteiro e sai 137 — corrigido com init único e dono único, e o
  contrato de imagem agora existe nos seis repositórios); D6, D8, D9, D10, D11
  e D12 continuam sem
  fechamento integral. I1 concluiu
  arquitetura/handoff (`eb4e3555`) e I2 concluiu runtime 1 e conformance local
  Linux/amd64 (`0e7ff072`), ambos commitados/enviados. A evidência reduz a lacuna
  core de D7, acrescenta seus builds worktree ao resíduo de D8 e atualiza as entradas
  de D9/D11/D12. A D7 **executou** em 2026-10-23 e reduziu a lacuna dos contratos
  MCP por gestor (§2.7). I3 foi adiado pelo operador; I4–I9 permanecem pendentes. Restore/rollback
  F4 anteriores continuam reaproveitáveis no seu escopo. A
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
| D2 | Matriz de proveniência e política de identidade | Matriz repo → SHA → autor/committer bruto → atribuição confirmada → mapeamento aprovado → image ID/revision revisada; `.mailmap` apenas quando duas identidades forem comprovadamente a mesma pessoa; nenhuma reescrita de `main` publicado | F7 P1 (#10) | agente + operador | **fechado em 2026-10-23** — matriz completa em §2.2. Atribuição confirmada por vínculo com a API do GitHub (a API resolve o autor de cada commit para a conta que o assinou); `.mailmap` aplicado nos sete repositórios (Opção A), colapsando 3–5 grafias em `Bill Kopp <bill.kopp.dev@gmail.com>` por repo, sem reescrever nenhum objeto commit; identidades de automação e contribuições externas ficam sem mapeamento (D2-b Opção A); rebuild limpo dos seis MCPs a partir do HEAD, com SHA completo no label `revision` e smoke stdio 6/6 (D2-d Opção A). Defeito corrigido no caminho: `.mailmap` vazava para a imagem do Deep Research (`COPY . .`), corrigido em `e076f29`. **Restam fora deste fechamento:** promoção das imagens (D8, exige aprovação/canário/rollback), push dos `.mailmap` e a política de assinatura de commits, que segue aberta e independente |
| D3 | Permissão do Khan e projeção efetiva | Decisão registrada do operador sobre a superfície por gestor; lista efetiva extraída do protocolo e verificada nos dois consumidores; `allowedProjects` não confundido com permissão de tool | F7 P2 (#7) | operador | **fechado em 2026-10-23** — decisão do operador em §2.4: **superfície completa nos dois gestores**, prompts/resources como limitação aceita e registrada, aplicação autorizada ao agente. Superfície real: **12 tools + 6 prompts + 1 resource = 19** (§2.3), escrita efetiva em 5 tools. Aplicado: `allowedTools` do Khan no Positronic elevada de 1 para 12 via `positronic mcp server configure` (config `revision` 1→2, `configurationId` preservado, `network: none`, mount e env intactos, snapshot de rollback em `~/.local/state/positronic-d3-snapshots/`); o Percival já estava em 12 tools (`toolsDisabled: []`) e não foi mutado. Projeção verificada nos dois gestores: `discover` 12 tools, `preview` `refreshKey 10:9ee229c8-…:2`, `reconnect` `generation 777b633dce4cf9fa` (= hash da revisão 2), broker Percival `tools/list` 12 tools, log do gateway `connected, 12 capabilities registered`. **Limitação registrada:** prompts/resources não são cobertos por allowlist de tool no Positronic (viram comandos/resource), e não são expostos no Percival — assimetria por construção, não remediavel por configuração |
| D4 | Atribuição das duplicatas por container ID | Mapa container → processo/sessão cliente/registry/escopo, com ciclo de vida demonstrado e cardinalidade esperada documentada; limpeza apenas com autorização específica e zero referências confirmadas | F7 P2 (#8) | agente | **fechado em 2026-10-23, com achado residual** — mapa completo em §2.5. **Não há duplicata nem órfão**: os 17 containers MCP são 17 instâncias legítimas. Lado Percival: nome determinístico `percival-mcp-<server_id>` ([`broker.py:135`](../../nanobot/mcp_docker/broker.py#L135)) torna impossível duas instâncias do mesmo servidor (o nome é o lock), 6 containers com labels `percival.mcp-docker.{owner,managed-by,server-id,instance-id}`, todos os journals de servidor em `committed`. Lado Positronic: 11 containers, nome `positronic-mcp-<server>-<run12>`, distinguidos por **contexto de projeto** (label `io.positronic.context` = hash do diretório) — `/home/bill` (6 servidores, via `opencode serve` PID 98403) e `/home/bill/.positronic` (5, via `opencode attach` PID 111547); cardinalidade formalizada como **≤1 por `(servidor, contexto)`**. **Nenhum órfão:** 11/11 containers casam com `owner.json` (`state: acquired`, `pid`/`boot`/`start` idênticos ao `/proc/98403/stat`), 0 `cleanup-pending`, 0 container sem dono. **Ciclo de vida demonstrado** pela auditoria (`acquire` → `tools-list` → `close transport-closed` na reconexão, com `--rm` removendo o anterior), não por inferência. **Nenhuma limpeza executada** — o critério "zero referências confirmadas" não é atingido: os containers estão em uso. **Achado residual de observabilidade:** 7 das 150 aquisições não têm desfecho gravado (o `close` não foi escrito quando o cliente foi interrompido entre `acquire` e `tools-list`); uma delas tem efeito observável — o deep-research ficou ausente no contexto `/home/bill/.positronic` e `GET /mcp` nesse diretório responde HTTP 499. Não é órfão nem duplicata; é lacuna de auditoria que exige gravar o `close` nesse caminho |
| D5 | Regressão Khan `tools/call` | Chamada MCP real de leitura com evidência no protocolo, não em filesystem/stderr; reproduzir em fixture sem tocar calendário real; investigar a versão do FastMCP/`mcp[cli]` ou registrar limitação aprovada | relatório F4/F5 | agente | **fechado em 2026-10-23** — o defeito reportado pelo F4/F5 ("o FastMCP 3.4.4 não devolve o frame JSON-RPC em `tools/call`") **não reproduz** com cliente MCP real, nem no checkout nem contra a imagem F3 em uso. Diagnóstico em §2.6: a causa é a **combinação entre o harness da F4 e a camada `fastmcp` 3.x** — o harness fechava o stdin via `subprocess.run(input=…)` antes de ler a resposta, e a camada `fastmcp` 3.x não cancela o handler em voo quando o transporte fecha (o SDK low-level cancela). **Não é pin nem config**: as duas pontas da faixa (`mcp` 1.28.1/`fastmcp` 3.2.0 e `mcp` 1.30.0/`fastmcp` 3.4.4`) comportam-se igual, e a mesma imagem que reproduzia o defeito responde 10/10 com o transporte aberto. **Evidência no protocolo**: `initialize` + `tools/list` (12 tools) + `tools/call` de `khan_get_status`, `khan_list_calendars`, `khan_list_events` e round-trip `create`→`list`→`search`, mais erro de validação retornando `isError: true` — todos com `isError: false` e conteúdo correto, sobre workspace isolado por `KHAN_WORKSPACE_DIR`, sem tocar o calendário real. **Correção durável**: novo `tests/test_protocol_stdio.py` (7 testes) no repo do Khan; `scripts/docker-ci-conformance.py` estendido com `--call-tool`/`--call-args` (emite o `tools/call` antes de fechar o stdin) e invocado pelo CI com `--call-tool khan_get_status`. **Limite registrado**: a fragilidade da camada `fastmcp` 3.x permanece (0/10 sob EOF imediato, em ambas as formas de payload medidas); os consumidores reais (broker do Percival, runtime do Positronic) leem o frame antes de fechar o transporte. **Correção após reexecução** (§2.6.2): o controle do Notes **também** perde o frame de forma intermitente sob EOF (9/10 na forma F4, 1/10 na forma com `tools/list` antes) — o registro anterior de "5/5" estava errado; o que distingue o Khan é a falha **determinística**, e a taxa intermitente das camadas do SDK é propriedade do harness, não do servidor. **Ressalva**: as mudanças foram **commitadas e enviadas** em 2026-10-23 (core `1eeed82f`, Khan `0bc52b9`), **não publicadas** |
| D6 | Resíduo OpenSSH `CVE-2026-60002` no gateway (#11a) | Build do gateway em base corrigida com OpenSSH >= 10.4 e regressão de Percival Remote SSH na imagem, **ou** exceção individual documentada e aprovada; OpenVEX do gateway não estendido aos MCPs sem análise por imagem | F7 P4.2 (#11a) | agente + operador | **aberto, sem remediação por I2** — fonte atual preserva base uv/Trixie pinada e `openssh-client=1:10.0p1-7+deb13u4` no `Dockerfile`. O finding Critical e o waiver não aprovado são da triagem F3; I2 não executou novo scan nem teste Remote SSH na imagem. OpenVEX antigo é restrito ao image ID analisado e não cobre esta CVE; não se transfere aos novos IDs I2. Testar OpenSSH Forky fora da imagem não fecha D6 |
| D7 | Consolidar evidência de runtime nos artefatos finais | Runtime 1 por modo, usuário/caps/init efetivos, sinais/EOF, probes/autenticação e persistência; MCP stdio sem porta/TTY/health HTTP e sem init duplicado por gestor. Evidência ligada aos SHAs/imagens finais e aos consumidores afetados | F4/F5 closure, item 2; I2.1–I2.6 | agente | **fechado em 2026-10-24** — §2.7. **Core reaproveitado**: os 19 checks PASS do I2 (gateway/API/CLI/broker, doctor/probe autenticada, init/caps/UID, SIGTERM, crash/recreate/hydrate) mantêm-se válidos, com a justificativa de que nada do core foi alterado. **Contratos MCP por gestor medidos** com o instrumento novo `scripts/percival-mcp-runtime-contract.py` (24 medições: 6 imagens × 2 gestores × EOF/SIGTERM). **Conforme em todas**: sem TTY, stdin aberto, zero portas publicadas, zero sockets em escuta, `CapEff=0`, sem healthcheck HTTP. **Achado novo (defeito de código do core)**: o broker do Percival **não passa `--init`** ([`broker.py:182`-`:189`](../../nanobot/mcp_docker/broker.py#L182-L189)), e 4 das 6 imagens não têm init embutido — logo **PID 1 não trata SIGTERM**, o `docker stop` paga o grace period inteiro (10,2 s) e sai **137** em vez de 143, contra 0,1 s/143 com `--init`; mecanismo confirmado por caso mínimo (bit 14 de `SigCgt` = "SIGTERM tratado"; `SigCgt=0` no init é correto, porque o init encaminha). **Achado confirmado (outro repositório)**: `--init` incondicional do consumidor Positronic ([`managed.ts:640`](../../../alternative-positronic/packages/positronic-mcp-docker/src/managed.ts#L640)) empilha `docker-init` sobre o tini de OSM/Deep Research — 2 camadas de init, medidas. **Divergência registrada**: `NoNewPrivs=1` sob o Percival vs `0` sob o Positronic. **Correção aplicada (§2.7.8)**: init único com dono único — o init pertence ao gestor (`--init` / Compose `init: true`) e a imagem não embute init. Broker do core passa `--init` e verifica a política após o spawn e na retomada (core `79dda0a0`); OSM e Deep Research deixam de embutir tini e declaram `init: true`; os seis compose renderizam `init: true`; teste de contrato de imagem criado em Notes, Khan e AgentMail e ampliado no Weather (OSM `7f3cb3e`, Deep Research `6bcb752`, Notes `36c4016`, Khan `13f8fce`, AgentMail `31d6b1c`, Weather `81b3aaa`). **Resíduo**: a `NoNewPrivs` do Positronic e o alinhamento do manual (D9) permanecem abertos; as imagens de OSM e Deep Research precisam ser reconstruídas e promovidas sob a D8 |
| D8 | Reconciliar pins e par core com builds de checkout limpo e promover | Rebuild Notes/AgentMail, par core I2 e qualquer candidato alterado a partir de commit limpo, com SHA/versão/labels/imagem coerentes; promover por gestor só com aprovação, canário e rollback independentes; reter último bom e par A/B, com config/dados compatíveis | F7 P4.1 (#4, #6); I2 → I3 | agente + operador | **parcial, com resíduo core explícito** — guard de checkout/worktree já existe em `scripts/percival-docker-build.py`. I2 alinhou metadata core a `0.1.0`, mas seus builds são baseline + diff, não builds do commit limpo `0e7ff072`. A auditoria dos seis MCPs registrou falta de guard equivalente e SHA curto do OSM incompatível com verificação por SHA completo; esses achados não foram corrigidos por I1/I2. **O SHA curto do OSM foi corrigido em 2026-10-23**: os seis MCPs foram reconstruídos a partir do HEAD limpo com SHA completo no label `revision` e smoke stdio 6/6 (§2.2), o que remove o resíduo de proveniência dos MCPs. Restam: build limpo do **par core** a partir de `0e7ff072`, promoção das seis imagens novas por gestor (exige aprovação, canário e rollback independentes) e retenção do par A/B. Sem promoção, nenhum digest público nesta revisão |
| D9 | Alinhar/exercitar o manual operacional e assinar a retenção | Walkthrough em fixture de update, rollback, restore e falsa falha de health; comandos/APIs e procedimentos compatíveis com runtime 1; política de retenção e revisão trimestral assinada | F7 P3 (#2, #5); handoff I2/I4/I8 | agente (redige) + operador (aprova) | **parcial, precisa incorporar runtime 1** — [manual criado](../operations/mcp-docker-local-runbook.md); existência de `auth init` e `mcp-docker doctor` já verificada não prova o procedimento inteiro. Corrigir no walkthrough API alternativa/single-writer, bind comum/token, significado das probes, init e sinais por modo (gateway/API exit 0 idle; broker 143, sem promessa de drain). I2 não exercitou esse manual nem assinou retenção/revisão trimestral; D10 mantém dono dos comandos Positronic |
| D10 | Caminho de reinstalação do MCP Docker no consumidor Positronic (**item reescrito em 2026-10-23**) | (a) Determinar e registrar qual é o caminho de reinstalação **suportado**, pela interface suportada; (b) corrigir a documentação que promete comandos inexistentes — a skill global `mcp-docker-workflow` lista 11 comandos `positronic mcp server …` (`SKILL.md:31`-`:43`) que **não existem** no pacote de CLI do fork; (c) remover o workaround de edição direta do registry | F7 P3 / relatório F4/F5 | agente + operador | **premissa errada → reescrito; agora parcialmente invalidada** — em 2026-10-23 o binário `positronic` **passou a existir** no PATH (`/home/bill/.local/bin/positronic`, wrapper do runtime nativo fixado) e expõe `mcp server configure <id> <revision> --tools <lista>`; os 11 comandos da skill **existem** no CLI atual. A afirmação anterior ("não há binário `positronic` no PATH", "não existe comando para corrigir") **não vale mais** — ver §2.3. Restam: reescrever a D10 à luz do CLI atual, confirmar na skill os nomes/flags reais (o `recover-transition` exige `--confirm`), e remover o workaround de edição direta do registry. O estado real continua sendo o registry gerido pelo servidor (`~/.positronic/mcp/registry.json`, `schemaVersion` + 6 servidores) |
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

### 2.2 D2 — matriz de proveniência e política de identidade (2026-10-23)

Decisões do operador nesta data: **D2-a** atribuição das identidades do operador
confirmada por vínculo com a API do GitHub; **D2-b** Opção A (identidades de
automação permanecem no histórico, sem reescrita); **D2-c** Opção A (`.mailmap`
aplicado agora); **D2-d** Opção A (rebuild limpo dos seis MCPs a partir do HEAD).

**Atribuição confirmada (D2-a).** A API do GitHub resolve o autor de cada commit
para a conta que o assinou, o que dá vínculo verificável onde não há assinatura
GPG/SSH (173 commits da janela F0–F7 com `%G?` = `N`):

| Identidade bruta | Vínculo verificado | Verificação |
| --- | --- | --- |
| `bill.kopp.dev@gmail.com` | conta `bill-kopp-ai-dev` (id 266513903) | `GET /repos/…/commits/beaccab99` → `author.login = bill-kopp-ai-dev` |
| `whats.up.ai.chat@gmail.com` | conta `bill-kopp` (id 217495821), pessoal do operador | `GET /repos/…/commits/d2e9987` → `author.login = bill-kopp`; `bill-kopp/nanobot-webui` é fork de `Good0007/nanobot-webui` |
| `bill-kopp-ai-dev@users.noreply.github.com` | login da conta de trabalho | identidade de login do próprio GitHub |
| `bill@example.com`, `bill@percival.local`, `billkopp@example.com` | identidade local do próprio repositório (§1 do [relatório F7](../reports/2026-10-10-f7-provenance-and-identity.md)), enviada pela conta do operador | `GET /repos/HKUDS/nanobot/commits/c92f732` e `…/1e7518a` confirmam autoria sob esses endereiros; push events da conta do operador |

O operador **corrigiu** a primeira lista apresentada: `bill.kopp@gmail.com` não
existe em nenhum histórico, e `willkopp@gmail.com` também não (aparece apenas
como destinatário em journals do Positronic). Ambos foram removidos.

**`.mailmap` aplicado (D2-c, Opção A).** Um mapeamento por email cobre todas as
grafias de nome (`bill`, `bill-kopp`, `bill-kopp-ai-dev`, `Bill Kopp`). Após a
aplicação, cada um dos sete repositórios apresenta uma única identidade de
operador:

| Repo | HEAD com `.mailmap` | Identidade apresentada | Autor/committer brutos colapsados |
| --- | --- | --- | --- |
| `nanobot` | `7d2312a6` | `Bill Kopp <bill.kopp.dev@gmail.com>` | 5 |
| `percival-notes-mcp` | `78c2810` | idem | 4 |
| `percival-agentmail-mcp` | `54461f4` | idem | 3 |
| `percival-weather-mcp` | `b5dd4eb` | idem | 5 |
| `percival-khan-calendar` | `ce69267` | idem | 4 |
| `percival-osm` | `55aa673` | idem | 4 |
| `percival-deep-research` | `44ae8a1` | idem | 3 |

Identidades de automação (`Positronic`, `Percival`, `Trae`, `positronic-bot`,
`positronic-f1-bot`, `agente`) e contribuições externas (upstream HKUDS:
`Xubin Ren`, `chengyongru`, `Daniel Nowak`) permanecem **sem mapeamento** e
visíveis no histórico — decisão D2-b, Opção A. Nenhum objeto commit foi
reescrito; os SHAs de `origin/main` permanecem idênticos.

**Rebuild limpo (D2-d, Opção A).** `scripts/percival-docker-build.py` a partir do
HEAD limpo de cada repo, `linux/amd64`, SHA completo no label `revision`, sem
label de worktree sujo:

| Serviço | HEAD | Tag | Image ID | `revision` | Versão | Smoke stdio |
| --- | --- | --- | --- | --- | --- | --- |
| Notes | `78c2810` | `percival-notes-mcp:0.1.5-78c2810` | `sha256:5a802a632fd2…` | `78c2810…` | 0.1.5 | initialize ok, 12 tools |
| AgentMail | `54461f4` | `percival-agentmail-mcp:0.4.0-54461f4` | `sha256:7f8a2ab5b85b…` | `54461f4…` | 0.4.0 | initialize ok, 24 tools |
| Weather | `b5dd4eb` | `percival-weather-mcp:0.9.0-b5dd4eb` | `sha256:6da5d43f2168…` | `b5dd4eb…` | 0.9.0 | initialize ok, 9 tools |
| Khan | `ce69267` | `percival-khan-calendar:0.4.0-ce69267` | `sha256:b7d56ee4b313…` | `ce69267…` | 0.4.0 | initialize ok, 12 tools |
| OSM | `55aa673` | `percival-osm:0.5.0-55aa673` | `sha256:bb88ae358e90…` | `55aa673…` | 0.5.0 | initialize ok, 37 tools |
| Deep Research | `e076f29` | `percival-deep-research:3.0.1-e076f29` | `sha256:bad6defa8ce4…` | `e076f29…` | 3.0.1 | initialize ok, 5 tools |

A discrepância de SHA do OSM relatada em 2026-10-10 (SHA curto no label) está
corrigida: os seis labels carregam o SHA completo de 40 caracteres.

**Defeito encontrado e corrigido durante o rebuild:** o `.mailmap` do Deep
Research entrou na imagem em `/app/.mailmap`, porque o Dockerfile faz
`COPY . .` e o `.dockerignore` não o excluía. Corrigido em `e076f29`
(`.dockerignore` + `.mailmap`), com rebuild e verificação de ausência na imagem.

**Limites desta execução:** nenhuma imagem foi promovida; os pins de runtime
continuam apontando para os IDs antigos (`ef4082ef1390`, `e104ac754951`,
`e75fdd4abc8a`, `55cd5a038d22`, `67f8ada63989`, `265891c14514`). Promoção exige
aprovação, canário e rollback independentes (D8). Os `.mailmap` estão commitados
localmente nos sete repositórios, sem push. Não há assinatura de commits:
continuar sem assinatura enfraquece a proveniência mesmo com o mapeamento
  aplicado — decisão de chave e de política de assinatura permanece aberta e
  independente.

### 2.3 D3 — levantamento da superfície efetiva do Khan (2026-10-23, agente)

Read-only. Nenhuma mutação de configuração, registry, container, broker ou
imagem. Objetivo: substituir o critério errado da D3 por evidência do protocolo
e uma lista efetiva por gestor.

**Correção do critério anterior.** O texto anterior da D3 afirmava "17
identificadores `khan_*`, 7 de escrita". A contagem misturava tools e prompts.
Levantamento por `tools/list`, `prompts/list`, `resources/list` e
`resources/templates/list` contra o container em execução
(`percival-khan-calendar:0.4.0-ce69267`, image `sha256:55cd5a038d22…`):

| Superfície | Quantidade | Itens |
| --- | --- | --- |
| Tools | **12** | `khan_list_events`, `khan_search_events`, `khan_create_event`, `khan_update_event`, `khan_delete_event`, `khan_delete_event_safe`, `khan_get_event`, `khan_view_agenda`, `khan_view_calendar`, `khan_get_status`, `khan_list_calendars`, `khan_export_ics` |
| Prompts | **6** | `khan_overview`, `khan_create_event_semantics`, `khan_update_workflow`, `khan_delete_with_confirmation`, `khan_search_strategy`, `khan_quick_action_quick_create` |
| Resources | **1** | `khan://schema/main` |
| Resource templates | 0 | — |

Total 19, o que o próprio servidor documenta em
`percival-khan-calendar/src/percival_khan_calendar/server.py:99` ("process to
discover 12 tools, 6 prompts and 1 resource"). Escrita efetiva entre as 12
tools: `khan_create_event`, `khan_update_event`, `khan_delete_event`,
`khan_delete_event_safe`, `khan_export_ics` (5). Os 18 identificadores `khan_*`
no source são tools + prompts; `khan_delete_event` remove sem preview, enquanto
`khan_delete_event_safe` faz dry-run por padrão e só apaga com `confirm=True`
(`tools/delete_event.py:30` e `:54`).

**Superfície efetiva por gestor — os dois divergem.**

| Gestor | Mecanismo | Lista efetiva do Khan | Efeito sobre prompts/resources |
| --- | --- | --- | --- |
| Percival | `toolsDisabled` em `tools.mcpDocker.servers["khan-calendar"]` → `enabled_tools` em [`nanobot/agent/tools/mcp.py:1451`](../../nanobot/agent/tools/mcp.py#L1451); poda client-side e no broker ([`broker.py:684`](../../nanobot/mcp_docker/broker.py#L684)) | **12 tools** (as 12 do servidor; `toolsDisabled: []` em `~/.nanobot/config.json`) | **Não expostos.** Com `enabled_tools` sem `"*"`, o cliente não registra resources/prompts ([`mcp.py:1282`](../../nanobot/agent/tools/mcp.py#L1282)); log do gateway: `skipping resource/prompt registration (enabledTools does not include '*')` e `connected, 12 capabilities registered` |
| Positronic | `allowedTools` em `~/.positronic/mcp/servers/khan-calendar.json`, imposto no cliente em [`packages/opencode/src/mcp/index.ts:863`](../../../alternative-positronic/packages/opencode/src/mcp/index.ts#L863) e revalidado antes de cada chamada em [`packages/positronic-mcp-docker/src/managed.ts:620`](../../../alternative-positronic/packages/positronic-mcp-docker/src/managed.ts#L620) | **1 tool** — `khan_get_status` | **Expostos.** `MCP.prompts` não consulta a allowlist: os **6 prompts** do Khan viram comandos no Positronic (`GET /command` → `khan-calendar:khan_overview`, `khan-calendar:khan_delete_with_confirmation`, …), e o **1 resource** aparece em `GET /experimental/resource` (`khan-calendar:khan://schema/main`) |

Consequência: **a allowlist do gestor restringe tools, não prompts nem
resources.** No Positronic, os prompts de escrita (`khan_update_workflow`,
`khan_delete_with_confirmation`, `khan_create_event_semantics`) são alcançáveis
mesmo com `allowedTools: ["khan_get_status"]`. Isso não é falha do Khan — é
semântica do gestor, e vale para os demais MCPs.

**O estado do Positronic mudou em 2026-10-20** e o [relatório F7 de
2026-10-10](../reports/2026-10-10-f7-khan-allowlist-and-duplicates.md) está
desatualizado nesse ponto: ele registra `allowedTools` com 12 tools e
`configurationId: fb8ba208-…`; hoje são 1 tool, `revision: 1`,
`configurationId: 9ee229c8-…`. A mudança foi o gate humano de revisão de
allowlist do smoke F3.0.1, que autorizou apenas a chamada segura
`khan_get_status` (runbook `POSITRONIC_F3_F301_OPERATOR_RUNBOOK.md` §3.1.1,
"tool que lê/modifica estado externo → **não** incluir"). Verificado pela
interface suportada: `positronic mcp server show khan-calendar` → `allowedTools:
["khan_get_status"]`, e pela API do servidor em execução
(`GET /experimental/positronic/mcp/installed`).

**`allowedProjects` não é permissão de tool** (critério da D3, confirmado):
não existe em nenhum código do gateway; no registry do Positronic é `[]` com
`scope: "global"` para os seis servidores; e no código do fork só aparece como
filtro de **projeto** para servidores de escopo local
([`managed.ts:614`](../../../alternative-positronic/packages/positronic-mcp-docker/src/managed.ts#L614)),
ao lado de `allowedTools`, que é o filtro de **tool**.

**Correção factual adicional (D10).** O binário `positronic` **passou a
existir** no PATH desde a última revisão deste plano
(`/home/bill/.local/bin/positronic`, wrapper do runtime nativo fixado), e o
fork expõe `mcp server configure <id> <revision> --tools <lista>` como
caminho de alteração de allowlist suportado
([`packages/opencode/src/cli/cmd/positronic-mcp-docker.ts:179`](../../../alternative-positronic/packages/opencode/src/cli/cmd/positronic-mcp-docker.ts#L179)).
A afirmação anterior da D10 — "não há binário `positronic` no PATH" e "não
existe comando para corrigir" — **não vale mais** e precisa ser reescrita. Os
11 comandos listados na skill global `mcp-docker-workflow` **existem** no CLI
atual (`install-local`, `configure`, `scope`, `projects`, `update-image`,
`metadata`, `preview`, `discover`, `recover-runs`, `delete`, `restore`); o
comando inexistente era `install-local` na revisão antiga do fork, e o
`recover-transition` pede `--confirm` explícito.

**Superfície no Percival — caminho suportado para restringir.** O `toolsDisabled`
é um estado **negativo** (lista de tools desabilitadas), não uma allowlist:
`enabled_tools` é calculado como `tools − toolsDisabled`. Restringir a 1 tool
exige desabilitar 11 tools individualmente, via WebUI
(`Per-tool access` → botão `Disable`, [`webui/src/components/McpDockerManagement.tsx:482`](../../webui/src/components/McpDockerManagement.tsx#L482))
ou via `POST /api/settings/mcp-docker/disable-tool` (exige WebSocket
autenticado). Não há allowlist positiva equivalente no Percival; introduzi-la
seria mudança de contrato, não configuração.

**Achado colateral (D4).** A duplicação de containers não é só do Khan: há
**2 containers Positronic por servidor** para os 6 servidores (12 no total) e
**1 container Percival por servidor** (6), todos `Up`. Os containers Positronic
são `docker start --attach --interactive` de processo filho do `opencode serve`
(PID 98403), com registro de ownership em
`~/.positronic/mcp/executions/<run>/owner.json` (`state: "acquired"`, mesmo
PID/boot/engine) — portanto **não são órfãos**: são uma instância por
sessão ativa, e o segundo conjunto nasce de reativação dentro da mesma
sessão. O container Percival (`percival-mcp-khan-calendar`) carrega
`percival.mcp-docker.owner=percival`, `.managed-by=percival-broker`,
`.server-id=khan-calendar` e `.instance-id=68fae821-…`. O `AutoRemove=true`
nos containers Positronic confirma o descarte no encerramento da sessão.

**Limites desta execução.** Nada foi alterado: `allowedTools` do Positronic,
`toolsDisabled` do Percival, registry e containers seguem como estavam. A
decisão de superfície por gestor, que é a parte que cabe ao operador, **não foi
tomada** nesta etapa — foi tomada depois e registrada em §2.4, que também
documenta a aplicação.

### 2.4 D3 — decisão do operador e aplicação (2026-10-23)

**Decisão do operador (2026-10-23), registrada antes de qualquer mutação:**

| Eixo | Decisão |
| --- | --- |
| Superfície | **Completa nos dois gestores** — 12 tools do Khan liberadas em ambos |
| Prompts e resources | **Limitação aceita e registrada** — sem cobertura por allowlist de tools |
| Aplicação | **Agente aplica, com autorização explícita** |

**O que foi aplicado.** Uma mutação, no Positronic: a `allowedTools` do Khan
passou de 1 para 12 tools. O Percival **não foi mutado** — já estava em
`toolsDisabled: []` com as 12 tools em `~/.nanobot/config.json`, que é
exatamente a superfície decidida.

**Rollback preparado antes da mutação.** `saveConfig` não cria backup próprio
(o backup vive do fluxo de transição/delete), então foi feito snapshot privado
da configuração anterior:

```
/home/bill/.local/state/positronic-d3-snapshots/
  khan-calendar.json.rev1.20261023T220640Z.bak   (revision 1, allowedTools: ["khan_get_status"])
```

**Comando aplicado** (caminho suportado, sem edição direta do registry):

```bash
positronic mcp server configure khan-calendar 1 \
  --network none \
  --mount '/home/bill/.positronic-reports/f3-0-1-khan-workspace-20261020T172539Z|/data|rw' \
  --env KHAN_WORKSPACE_DIR=/data \
  --tools 'khan_list_events,khan_search_events,khan_create_event,khan_update_event,khan_delete_event,khan_delete_event_safe,khan_get_event,khan_view_agenda,khan_view_calendar,khan_get_status,khan_list_calendars,khan_export_ics'
```

O `1` é a revisão da **configuração**, não a do registry (que é 10). Todos os
campos foram passados explicitamente porque o CLI tem default
`--network bridge` e defaults vazios de `--mount`/`--env`
([`positronic-mcp-docker.ts:184`](../../../alternative-positronic/packages/opencode/src/cli/cmd/positronic-mcp-docker.ts#L184)):
omitir qualquer um deles sobrescreveria o isolamento em vez de preservá-lo.

**Resultado — isolamento preservado, `configurationId` intacto:**

| Campo | Antes | Depois |
| --- | --- | --- |
| `revision` (config) | 1 | **2** |
| `configurationId` | `9ee229c8-c6ce-4d5c-b030-e39028fb6349` | **idêntico** |
| `network` | `none` | `none` |
| `mounts` | workspace sintético → `/data`, gravável | **idêntico** |
| `env` | `KHAN_WORKSPACE_DIR=/data` | **idêntico** |
| `allowedTools` | 1 (`khan_get_status`) | **12** |
| registry `revision` | 10 | **10** (inalterado) |

**Projeção efetiva verificada nos dois gestores.**

| Verificação | Resultado |
| --- | --- |
| `positronic mcp server show khan-calendar` | 12 `allowedTools`, `revision: 2`, `network: none` |
| `positronic mcp server discover khan-calendar` | **12 tools** pelo protocolo, contra o container em execução |
| `positronic mcp server preview khan-calendar <projeto>` | `tools: 12`, `refreshKey: 10:9ee229c8-…:2` — a revisão nova entrou no ciclo de vida |
| `POST /experimental/positronic/mcp/managed/inspect` | `configRevision: 2`, `configurationId` preservado, 12 `allowedTools`, `network: none`, mount e env intactos |
| `POST …/managed/command {"action":"reconnect"}` | `{"khan-calendar":{"status":"ready","generation":"777b633dce4cf9fa"}}` |
| `generation` × `Bun.hash(refreshKey)` | `777b633dce4cf9fa` = hash de `10:9ee229c8-…:2` (a revisão 1 daria `a06460b29a18bd0f`) — **o runtime absorveu a configuração nova** |
| `GET /mcp` | `khan-calendar: connected` |
| `GET /command` | **6 comandos de prompt** do Khan: `khan-calendar:khan_overview`, `khan_create_event_semantics`, `khan_update_workflow`, `khan_delete_with_confirmation`, `khan_search_strategy`, `khan_quick_action_quick_create` |
| `GET /experimental/resource` | **1 resource**: `khan-calendar:khan://schema/main` |
| Broker Percival, `tools/list` em `/mcp/khan-calendar` | **12 tools** (JSON-RPC completo, dentro do container do broker) |
| Log do gateway Percival | `percival_docker_khan-calendar: connected, 12 capabilities registered` e `skipping resource/prompt registration (enabledTools does not include '*' — only tools allowed)` |

**O que a verificação não prova.** O `/experimental/tool/ids` do Positronic
lista **25 tools** e nenhuma delas é do Khan (`khan-calendar_*` ausente). Isso
não é falha da allowlist: `registry.ids()` devolve apenas as tools **builtin e
custom** do registry
([`packages/opencode/src/tool/registry.ts:313`](../../../alternative-positronic/packages/opencode/src/tool/registry.ts#L313)),
e as tools MCP entram por caminho distinto
([`packages/opencode/src/session/tools.ts:390`](../../../alternative-positronic/packages/opencode/src/session/tools.ts#L390)).
Portanto **não existe endpoint do runtime que enumere as tools MCP efetivas**;
a prova da allowlist no Positronic é a composição de `preview` (lista efetiva
+ `refreshKey`), `discover` (12 tools pelo protocolo), `inspect` (config
persistida) e `reconnect` (geração nova, hash compatível com a revisão 2).
O `/experimental/tool` exige `provider` e `model`, e o runtime ativo está sem
provedor configurado (`GET /api/provider` → `data: []`), o que impede essa
segunda via.

**Segundo portão, verificado por leitura de código.** A allowlist é aplicada
duas vezes no Positronic: na composição da lista
([`mcp/index.ts:863`](../../../alternative-positronic/packages/opencode/src/mcp/index.ts#L863))
e na revalidação antes de cada chamada
([`managed.ts:620`](../../../alternative-positronic/packages/positronic-mcp-docker/src/managed.ts#L620)).
Como a revalidação consulta a mesma `config.allowedTools`, as 11 tools
liberadas passam pelos dois portões — não há uma segunda allowlist a
atualizar.

**Limitação registrada (aceita pelo operador).** Prompts e resources do Khan
continuam **fora** de qualquer allowlist de tool no Positronic: os 6 prompts
viram comandos e o resource é exposto, independentemente de `allowedTools`.
Isso é semântica do gestor (`MCP.prompts`/`MCP.resources` não consultam a
allowlist), vale para os demais MCPs e **não** é remediavel por configuração.
No Percival o oposto ocorre: prompts e resources **não** são expostos, porque
`enabled_tools` sem `"*"` suprime o registro de extras
([`mcp.py:1282`](../../nanobot/agent/tools/mcp.py#L1282)) e o broker não
encaminha `prompts/list`/`resources/list`
([`broker.py:32`](../../nanobot/mcp_docker/broker.py#L32)). Os dois gestores
têm, portanto, **superfícies assimétricas por construção**.

**Auditoria.** `~/.positronic/logs/audit.jsonl` registrou
`experimental.positronic.mcp.server.config` → `committed` para
`khan-calendar` em `2026-10-23T22:06:48Z`, e eventos `lifecycle`/`tools-list`
`succeeded` do Khan nas projeções seguintes.

**Estado da D3.** **Fechada em 2026-10-23.** Decisão registrada, aplicada,
verificada nos dois gestores e com rollback preparado. Não resta pendência
local nesta linha. O que permanece fora do alcance desta linha, e segue em
outros itens: **promoção** das imagens (D8), **duplicatas de container**
(D4), **regressão `tools/call`** do Khan (D5) e a **reescrita da D10** à luz
do CLI atual.

### 2.5 D4 — atribuição das duplicatas por container ID (2026-10-23, agente)

Read-only. Nenhum `docker stop`/`rm`/`kill`, nenhuma remoção, nenhuma mudança de
configuração. Objetivo: responder às duas metades que faltavam na D4 — o
*mapa* container → dono, e o que o inventário não provava: **ciclo de vida
demonstrado** e **cardinalidade esperada documentada**.

**Veredito curto.** O termo "duplicata" do F7 era um erro de leitura. Não há
duplicata nem resíduo: os 17 containers MCP da máquina são **17 instâncias
legítimas**, cada uma com dono vivo e rastreável. A contagem por servidor
(2×5 e 1×6 no Positronic) **não** é duplicação — são **dois contextos de
projeto distintos**, e o runtime mantém **no máximo 1 instância por
`(servidor, contexto)`**.

**Inventário atual (2026-10-24T00:00Z).** 19 containers no total: 2 do core
(`nanobot-nanobot-gateway-1`, `nanobot-percival-mcp-broker-1`), 6 do broker
Percival (`percival-mcp-*`) e **11** do Positronic (`positronic-mcp-*`).

| Grupo | Containers | Dono | Cardinalidade |
| --- | --- | --- | --- |
| Core Percival | 2 | Compose (`nanobot-*`) | fixa |
| MCP via broker | 6 | `percival-broker` | 1 por `server_id` |
| MCP via Positronic | 11 | runtime Positronic | ≤1 por `(server_id, contexto)` |

#### Lado Percival — 6 containers, cardinalidade 1:1

O broker é o **único dono**: nome determinístico `percival-mcp-<server_id>`
([`broker.py:135`](../../nanobot/mcp_docker/broker.py#L135)), o que torna
**impossível** haver duas instâncias do mesmo servidor — a segunda
`docker run` colidiria no nome e falharia. Cada container carrega os quatro
labels `percival.mcp-docker.{owner,managed-by,server-id,instance-id}`, com
`owner=percival` e `managed-by=percival-broker`
([`broker.py:182`-`:186`](../../nanobot/mcp_docker/broker.py#L182)). O
`instance-id` é um **UUID novo por spawn**, não um identificador de sessão:
ele distingue **instâncias**, não **duplicatas**.

| Container | server-id | instance-id | Criado | Papel |
| --- | --- | --- | --- | --- |
| `percival-mcp-agentmail` | agentmail | `040d382a-…` | 2026-10-10 15:26 | broker |
| `percival-mcp-deep-research` | deep-research | `effd3c9f-…` | 2026-10-10 15:27 | broker |
| `percival-mcp-khan-calendar` | khan-calendar | `68fae821-…` | 2026-10-10 18:32 | broker |
| `percival-mcp-notes` | notes | `adee065a-…` | 2026-10-10 18:32 | broker |
| `percival-mcp-osm` | osm | `1b2998fe-…` | 2026-10-10 15:26 | broker |
| `percival-mcp-weather` | weather | `7ee291aa-…` | 2026-10-10 15:26 | broker |

**Ciclo de vida.** Todo spawn passa por `_spawn`, que re-lê a política
(`ready()`), valida a identidade da imagem (`--pull=never`), e **verifica
depois de subir** que a rede, o modo zero-bind e as coberturas exigidas
batem com a configuração ([`broker.py:178`-`:210`](../../nanobot/mcp_docker/broker.py#L178)).
Se o container não sobe, `_remove` roda e o registro é removido
([`broker.py:521`-`:525`](../../nanobot/mcp_docker/broker.py#L521)). Todo
reconfigure faz `_remove` + `_spawn`, então **não há janela com duas
instâncias** do mesmo `server_id`: o nome determinístico é o lock. O broker
não usa `AutoRemove`, e a remoção de container não toca volumes
(`docker rm -f`, **nunca** `-v` — [`broker.py:161`-`:163`](../../nanobot/mcp_docker/broker.py#L161)).

**Estado transacional.** Os 6 journals de servidor em
`~/.nanobot/mcp-docker/transitions/*.json` estão em `state: "committed"`
(nenhum `preparing` pendente); o `audit.jsonl` mostra pares
`started`/`committed` por operação. Existe um sétimo journal,
`probe.json`, em `state: "failed"` (`action: install`, `base_revision: 8`) —
resíduo de uma instalação de **sonda** que falhou em 2026-10-10; não
corresponde a nenhum `server_id` do registry e não tem container associado.

#### Lado Positronic — 11 containers, cardinalidade ≤1 por (servidor, contexto)

Aqui o nome **não** é determinístico: `positronic-mcp-<server>-<run12>`
([`execution.ts:50`-`:55`](../../../alternative-positronic/packages/positronic-mcp-docker/src/execution.ts#L50)),
onde `run` é um UUID por execução. Por isso dois containers do mesmo servidor
**podem** coexistir — mas cada um pertence a um **contexto de projeto
diferente**, e a distinção está no label `io.positronic.context`, que é o
hash SHA-256 do diretório de contexto
([`execution.ts:37`-`:38`](../../../alternative-positronic/packages/positronic-mcp-docker/src/execution.ts#L37)).

Os dois contextos foram resolvidos por hash:

| Label `io.positronic.context` | Diretório | Containers | Servers |
| --- | --- | --- | --- |
| `5c9e98ce905e…` | `/home/bill/.positronic` | 5 | agentmail, khan-calendar, notes, osm, weather |
| `f1a3fc6cfd85…` | `/home/bill` | 6 | agentmail, deep-research, khan-calendar, notes, osm, weather |

O mapeamento confere com o processo: `opencode serve` (PID 98403, cwd
`/home/bill`) e `opencode attach --dir /home/bill/.positronic` (PID 111547)
são **duas instâncias do runtime em diretórios de projeto distintos**, cada uma
com seu próprio conjunto de clientes MCP. `InstanceState.directory` é o que
alimenta `activeConfigs(directory)` ([`mcp/index.ts:751`](../../../alternative-positronic/packages/opencode/src/mcp/index.ts#L751)),
e portanto o que separa os dois conjuntos.

**Cardinalidade esperada, formalizada.** Para cada par `(servidor, contexto)`
há **no máximo 1 container**. Os 6 servidores do registry têm todos
`scope: "global"` e `activated: true`, e o `effective()` do gestor inclui um
servidor global **em todo contexto**
([`managed.ts:586`-`:587`](../../../alternative-positronic/packages/positronic-mcp-docker/src/managed.ts#L586)),
o que explica por que o contexto `/home/bill` tem os 6 e o contexto
`/home/bill/.positronic` tem 5.

**A ausência do deep-research em `/home/bill/.positronic` tem causa
identificada, e não é a que a contagem sugeria.** O `deep-research` **já
teve** container nesse contexto: a auditoria registra `acquire 19:28:05` →
`tools-list 19:28:11 succeeded` (run `013798ea`) → `close 19:50:47
transport-closed`. O que falta é o **segundo** container: a aquisição seguinte
(`acquire 19:53:42`, attempt `79f41e61`) **não tem desfecho** — nem
`tools-list`, nem `failed`. O transporte foi encerrado na janela
`acquire` → `tools-list`, e o `close` correspondente **não** foi gravado.

O efeito é observável: o container antigo **não** foi removido pelo `cleanup`
(o `close` é o que o dispara), e a tentativa nova **não** criou container
próprio naquele contexto. O `recover()` do gestor removeu o registro de
execução do run antigo, e o container correspondente saiu pelo `--rm` do
`docker run` quando o processo `docker start --attach` dono encerrou. O
snapshot final tem `deep-research` **apenas** em `f1a3fc6cfd85` (`/home/bill`),
com o container `6de22058` criado às 19:52:10.

Ou seja: o deep-research está **ausente em 1 dos 2 contextos** porque a
tentativa naquele contexto foi interrompida antes de `tools-list` e nunca
foi refeita. O `recover()` do gestor reconciliaria na próxima aquisição
desse contexto; até lá, o servidor fica **indisponível apenas naquele
contexto** — e `GET /mcp` com `x-opencode-directory: /home/bill/.positronic`
retorna **HTTP 499** (o runtime não consegue projetar um conjunto de MCP
completo nesse diretório), enquanto o mesmo endpoint em `/home/bill` devolve
os 6 servidores `connected`.

Isso **não** é órfão (o container não existe) nem resíduo de auditoria pura: é
uma **aquisição interrompida** cujo desfecho não foi gravado. Ver §2.5.1.

**Nenhum órfão.** Cruzamento integral entre os 11 containers Positronic e os
11 registros de execução em `~/.positronic/mcp/executions/*/owner.json`:

| Verificação | Resultado |
| --- | --- |
| Label `io.positronic.run` do container == diretório do `owner.json` | **11/11 coincidem** |
| `owner.json` sem container vivo | **0** |
| Container sem `owner.json` | **0** |
| Estados de execução | **11 `acquired`, 0 `cleanup-pending`, 0 `creating`** |
| Diretórios de execução sem `owner.json` | **0** |
| Dono do processo | todos com `pid: 98403`, `boot: 09e3c814-…`, `start: 200692` — **idêntico ao `/proc/98403/stat` do processo vivo** (mesmo boot, mesmo start-time, mesma máquina) |
| `AutoRemove` | `true` em todos os 11 |

O `recover()` do gestor é o que garante essa consistência: ele revalida
máquina, boot, start-time e PID contra o processo atual; se o dono morreu,
**remove o container**; se o `owner.json` não corresponde, marca `ambiguous`
e **não** remove ([`execution.ts:132`-`:175`](../../../alternative-positronic/packages/positronic-mcp-docker/src/execution.ts#L132)).

**Ciclo de vida — demonstrado, não inferido.** A auditoria
`~/.positronic/logs/audit.jsonl` registra o ciclo completo por tentativa
(`attempt`): `acquire started` → `tools-list succeeded` (com o `run` UUID) →
`close failed` com `code: transport-closed` quando o cliente reconecta. Para o
Khan em `/home/bill`: `acquire 19:49:28` → `tools-list 19:49:31 (run
c06bcab0)` → `close failed 19:50:47 transport-closed` → `acquire 19:52:10` →
`tools-list 19:52:13 (run 38085fa5)`. Ou seja: **cada reconnect encerra a
execução anterior por `transport-closed` e cria um container novo**, e o
`--rm` do `docker run` remove o antigo. Esse é o mecanismo que produz
"duas instâncias por servidor" sem produzir resíduo.

O `reconnect` que eu disparei na D3 aparece na auditoria como o par
`acquire 22:20:50` → `tools-list 22:20:54`, com `run 7eb054ef` — e o
container correspondente é o `positronic-mcp-khan-calendar-8ad0fc1c9794`,
criado às 19:10:56 (o `docker start --attach` do processo `docker` 698411,
ainda vivo). O `acquire` das 22:20 **não** criou um container novo: o
`8ad0fc1c` já existia e foi **reutilizado** pelo mesmo `run`. Cada aquisição
cria **no máximo um** container; o `8ad0fc1c` **substituiu** o `7a2560e3` no
contexto `/home/bill/.positronic`, não se multiplicou.

#### 2.5.1 Achado residual: 7 aquisições sem desfecho auditado

Cruzando `attempt` entre `acquire started` e o evento de desfecho, **7 das
150 aquisições** não têm desfecho registrado:

| Momento | id | contexto | Efeito observável |
| --- | --- | --- | --- |
| 19:53:42 | deep-research | `/home/bill/.positronic` | **container ausente** nesse contexto (§2.5) |
| 22:14:24 | notes, agentmail, khan-calendar, osm, deep-research, weather | `/home/bill/Projects/nanobot` | nenhum container criado nesse contexto |

A causa é o mesmo padrão: o transporte foi encerrado na janela `acquire` →
`tools-list`, e o `close` que dispararia o `cleanup` **não foi gravado** pelo
transporte. No caso de 22:14:24 o contexto é
`/home/bill/Projects/nanobot`, que **não tem nenhum container** — o runtime
tentou abrir 6 clientes MCP nesse diretório e foi interrompido antes de
completar qualquer um.

O impacto é **de auditoria e de disponibilidade**, não de integridade: não há
container sem dono, não há `cleanup-pending`, e `recover()` reconciliaria
qualquer divergência real no próximo `acquire`. Mas é uma lacuna real de
observabilidade: o `audit.jsonl` **não** fecha o ciclo dessas tentativas, e
sem o `close` o `cleanup` não roda — o que deixa o container anterior com
`--rm` **sem** remoção automática caso o processo dono morra sem o
`recover()`.

**Contagem de falhas na auditoria (histórico completo).** De 707 eventos
`experimental.positronic.mcp.server.lifecycle` (288 em 21/10, 204 em 22/10,
215 em 23/10): 312 `resolve failed`
(`configuration-resolution-failed`, **todos** até `2026-10-22T00:37:42` —
zero após, quando as configurações server passaram a existir), 102 `close
failed` (`transport-closed`, normal na reconexão; último em
`2026-10-23T19:50:47`), 2 `initialize failed`
(`container-vault-access-denied`, ambos em 2026-10-21), 141 `tools-list
succeeded`, 150 `acquire started`. **Nenhum `create` ou `start` falhou**, e
nenhum `container-create-unknown` — ou seja, **nenhum create ficou sem CID
observado**, que é a condição que o `cleanup` trata como tombstone
([`execution.ts:235`-`:242`](../../../alternative-positronic/packages/positronic-mcp-docker/src/execution.ts#L235)).

#### 2.5.2 Critério de "limpo", documentado

O relatório F7 propôs "encerrar o cliente e recontar". A verificação por
`owner.json` é **mais forte** e não exige derrubar nada: um container é
legítimo se, e somente se, existe um `owner.json` cujo `container` casa com
ele, cujo `state` é `acquired`, e cujo `pid`/`boot`/`start` casam com um
processo vivo. **No snapshot de 2026-10-24T00:00Z, os 11 containers
Positronic e os 6 containers do broker passam nesse critério.** Não há
candidato a limpeza.

**Por que não houve limpeza.** A D4 condiciona limpeza a "autorização
específica e zero referências confirmadas". Esse segundo critério **não é
atingido**: os containers estão em uso (`GET /mcp` em `/home/bill` → 6
servidores `connected`; `docker logs` do Khan mostra o ciclo
`initialize` → `ListToolsRequest` → `tools/list` com as 12 tools), e
destruí-los derrubaria tools MCP vivas. **Nenhum `docker rm` foi executado.**

**Nota sobre contagem de referências.** O inventário read-only do Percival
(`nanobot/mcp_docker/inventory.py`) filtra containers por nome, label ou
referência de imagem, e por isso **inclui os 11 containers do Positronic**,
que não são geridos pelo broker. Quem precisa da cardinalidade por gestor
tem de separar os dois grupos pelo label `percival.mcp-docker.managed-by`
(presente só nos 6 do broker) ou pelo prefixo de nome. O inventário **não
distingue** esses dois conjuntos sozinho.

**Efeito colateral da D3 sobre a D4.** A elevação da allowlist do Khan para 12
tools (§2.4) **não** alterou a cardinalidade: o `reconnect` de 22:10 revalidou
**um** container para o Khan em `/home/bill` e o antigo saiu pelo `--rm`. O
conteúdo de `allowedTools` não é parte da chave de identidade do container
(`server.revision:configurationId:config.revision`), então **não** dispara
re-criação em massa.

**Limites desta execução.** Nenhuma mutação de runtime, configuração,
registry, container ou journal. Toda a evidência é de leitura: `docker ps -a`,
`docker inspect`, `~/.positronic/mcp/executions/*/owner.json`,
`~/.positronic/logs/audit.jsonl`, `~/.nanobot/mcp-docker/transitions/*.json`,
`~/.nanobot/mcp-docker/audit.jsonl` e leitura do source dos dois gestores.

**Estado da D4.** **Fechada em 2026-10-23, com um achado residual
registrado.** O mapa container → dono → contexto → registry está completo nos
dois gestores, o ciclo de vida está demonstrado por evidência de auditoria
(não por inferência), a cardinalidade esperada está formalizada, e **não há
container a limpar**. O resíduo encontrado é de **observabilidade**: 7
aquisições sem desfecho gravado, das quais uma tem efeito observável
(deep-research ausente no contexto `/home/bill/.positronic`, que faz
`GET /mcp` nesse diretório responder HTTP 499). Isso **não** é órfão nem
container duplicado, e **não** exige limpeza — exige que o `close` do
transporte seja gravado mesmo quando o cliente é interrompido entre
`acquire` e `tools-list`.

### 2.6 D5 — regressão Khan `tools/call` (2026-10-23, agente)

**Critério de aceite da D5:** "chamada MCP real de leitura com evidência no
protocolo, não em filesystem/stderr; reproduzir em fixture sem tocar calendário
real; investigar a versão do FastMCP/`mcp[cli]` ou registrar limitação
aprovada".

**Veredicto: o defeito reportado pelo F4/F5 não existe no servidor.** O
sintoma ("o handler `call_tool` do FastMCP 3.4.4 não devolve o frame JSON-RPC
ao cliente") reproduz, mas a causa é a **combinação entre o harness e a
camada `fastmcp` 3.x** — não o pin, não a configuração do Khan, e não um
defeito de protocolo. O `tools/call` funciona sobre o protocolo, com o
cliente real, contra o checkout e contra a imagem em uso.

#### 2.6.1 O que o F4/F5 realmente executou

O harness original da F4 está versionado no core (`7e28d272`, quatro scripts
`scripts/f4-*-test.py`). O helper de chamada é:

```python
proc = subprocess.run(cmd, input=payload, capture_output=True, text=True, timeout=300)
```

`subprocess.run(input=...)` **fecha stdin assim que o payload é escrito**. O
servidor MCP recebe EOF no meio do `tools/call` em voo, e a camada
`fastmcp` 3.x — que o Khan usa — **não cancela o handler em voo** quando o
transporte fecha (a diferença de mecanismo está na §2.6.2). O resultado é o
sintoma observado: `khal` retorna 0 (visível no stderr), o efeito no
filesystem ocorre, mas **o frame de resposta se perde**.

O harness original da F4 confirmava isso no próprio código — ele **não** lia o
stdout para o Khan. As três asserções eram todas de filesystem/stderr:

```python
check(KHAN.joinpath("khal.db").exists(), "khan auto-heal wrote khal.db")
check("khal.call" in proc.stderr, "khan recreate executed khal CLI")
check("returncode\": 0" in proc.stderr, "khal returned 0 after recreate")
```

O relatório F4/F5 descreveu o proxy como "verificação no nível do filesystem +
stderr" — a escolha foi correta como método, mas a causa foi atribuída à
versão do FastMCP sem reproduzir o caminho.

#### 2.6.2 Reprodução do sintoma e da causa (matriz controlada)

Reprodução **fiel** do harness original (mesmo payload, mesma imagem F3
`sha256:55cd5a038d22…`, mesmo `protocolVersion: 2024-11-05`):

| Cenário | Frames recebidos | `khal.call` no stderr |
| --- | --- | --- |
| Harness F4 original (EOF imediato, via `subprocess.run(input=…)`) | **`[1]`** — só o `initialize` | sim |
| Mesmo payload, stdin mantido aberto | **`[1, 2]`** — `initialize` + `tools/call` | sim |

O frame do `tools/call` **aparece** quando o transporte não é fechado. O
comando `tools/call` é executado em ambos os casos (o log
`Processing request of type CallToolRequest` aparece nos dois) — o que se
perde é só o frame de resposta.

**Matriz de discriminação (N=10 repetições por célula, `stderr` para
arquivo, workspace novo por repetição).** Quatro servidores, mesmo
payload, mesma máquina; a única variável é a camada de servidor e se o
stdin é fechado antes da resposta:

| Servidor | EOF imediato | stdin aberto |
| --- | --- | --- |
| `fastmcp` 3.4.4 standalone (o que o Khan usa) | **0/10** | **10/10** |
| `mcp.server.fastmcp` (SDK v1) | 8/10 | 10/10 |
| `mcp.server.lowlevel.Server` (sem FastMCP) | 8/10 | 10/10 |
| **KHAN real** (`python -m percival_khan_calendar.server`) | **0/10** | **10/10** |

> **Ressalva de método, registrada após a reexecução:** os "8/10" das
> células do SDK são **propriedade do harness**, não do servidor — a
> reexecução abaixo mede 9/10 na forma F4 e 2/10 na forma com `tools/list`
> antes. A coluna de EOF imediato deve ser lida pela **distinção**
> (determinístico 0/10 vs. intermitente), e não pelo número absoluto.

A leitura correta da matriz:

1. **Com o transporte aberto, todos respondem** — 10/10 em todas as
   células. O `tools/call` do Khan funciona; não há defeito no servidor.
2. **O EOF é a condição necessária para perder o frame.** Nenhum servidor
   real pierde a resposta quando o cliente fecha o stdin *depois* de
   escrever o payload.
3. **O `fastmcp` 3.4.4 é o único que perde o frame de forma
   determinística** (0/10), enquanto as camadas sem FastMCP perdem de
   forma intermitente (8/10) — a corrida existe em todas, mas o FastMCP
   3.x a torna sempre presente.

**Reexecução da matriz (2026-10-23, harness reconstruído do zero) e
sensibilidade à forma do payload.** A matriz acima foi reconferida com um
harness independente, que mediu as duas formas de payload usadas nos
harnesses da F4 e da matriz:

| Forma do payload (mesma imagem, mesmo `mcp` 1.30.0) | `fastmcp` 3.4.4 | `mcp.server.fastmcp` | `mcp.server.lowlevel` | KHAN real |
| --- | --- | --- | --- | --- |
| **F4** (`initialize` + `initialized` + `tools/call` como id 2) | **0/10** | 9/10 | 8/10 | **0/10** |
| **Com `tools/list` antes** (`tools/call` como id 3) | **0/10** | 2/10 | 4/10 | **0/10** |

Com transporte aberto, as quatro camadas respondem **10/10** nas duas
formas. Duas conclusões se seguem, e elas **endurecem** a leitura
anterior:

- O **discriminante continua sendo a camada de servidor**: a célula
  `fastmcp` 3.x é **0/10 em ambas as formas**, enquanto as camadas do SDK
  são apenas intermitentes. Nenhuma forma do payload faz o Khan
  responder sob EOF.
- A **taxa intermitente das camadas do SDK depende da forma do payload**
  (de 9/10 para 2/10) — os "8/10" da tabela original são **propriedade
  do harness**, não do servidor. A afirmação estável é apenas a
  distinção **determinístico (0/10) vs. intermitente**, e ela se mantém
  em todas as medições.

**Mecanismo.** O `fastmcp` 3.4.4 **sobrescreve** o laço de execução do
SDK low-level: em `fastmcp/server/low_level.py:234`-`:268` (no `.venv` do
repositório do Khan), o `run()` reimplementado **não tem o
`finally: tg.cancel_scope.cancel()`** que o SDK tem
(`mcp/server/lowlevel/server.py:691`-`:696`).
Sem esse cancelamento, o *task group* do servidor fica esperando o handler
em voo; quando o `stdio_server` fecha o stream de escrita (por causa do
EOF do cliente), o `respond()` do handler cai em
`anyio.BrokenResourceError`/`ClosedResourceError` e o frame é descartado
(`mcp/server/lowlevel/server.py:808`-`:816`).

**Correção de uma leitura anterior.** A primeira hipótese levantada durante
esta D5 era de **latência de inicialização** (o Node do Notes sobe em
~1.9 s, o Python em ~0.6 s). Os dados a **refutam**: o Khan é *mais
rápido* que o Notes e mesmo assim é o que perde o frame de forma
determinística, e a matriz acima isola a camada de servidor, não o tempo
de subida. A hipótese de latência está **descartada**; a causa é a
diferença no tratamento do fechamento do transporte entre o
`fastmcp` 3.x e o SDK low-level.

**Controle com o servidor Notes (imagem F3 `sha256:ef4082ef13905…`, mesmo
harness):** o Notes **também** perde o frame de forma intermitente sob EOF
imediato — **9/10** na forma F4 e **1/10** na forma com `tools/list` antes.
A primeira medição desta D5 registrava "5/5" e sugeria que o Notes nunca
perdia o frame; a reexecução **corrige esse registro** — o que o Notes não
faz é *falhar de forma determinística*. A imagem do Notes usa
`mcp.server.fastmcp` (`notes_mcp.py:19`) sobre o **mesmo** `mcp` 1.30.0,
com o **mesmo** `stdio_server` e o **mesmo** mecanismo de cancelamento — e
por isso nunca é determinístico. Isso explica por que o F4/F5 observou o
defeito **apenas no Khan** e não o registrou como sistêmico: o Khan é a
única célula que falha **10/10**, independentemente da forma do payload.

#### 2.6.3 A versão: onde está e onde não está a causa

O critério exige separar **bug de versão**, **pin** e **config**. A
separação é a seguinte:

| Dimensão | Verificação | Veredicto |
| --- | --- | --- |
| **Pin** (`mcp[cli]`) | `pyproject.toml:13` declara `mcp[cli]>=1.28.1,<2.0.0`; `uv.lock` fixa `mcp 1.30.0`; a **imagem F3 em uso** (`sha256:55cd5a038d22…`) carrega `mcp 1.30.0` — verificado por `importlib.metadata` **dentro** do container. O pin não mudou desde `d8d4122` (2026-10-09) | **Não é o pin.** A imagem que reproduziu o defeito é a mesma que o pin declara, e o `mcp` 1.30.0 não é a camada que perde o frame (ver abaixo) |
| **Configuração** | `protocolVersion`, `notifications/initialized`, ordem dos ids, `KHAN_WORKSPACE_DIR`, `KHAN_ENABLE_LOCK` | **Não é configuração.** Descartadas por teste direto (tabela abaixo) |
| **Versão da camada FastMCP** | `fastmcp` 3.4.4 standalone vs `mcp.server.fastmcp` (SDK v1) vs `mcp.server.lowlevel.Server`, todos sobre o **mesmo** `mcp` 1.30.0 | **É a camada `fastmcp` 3.x.** Ver a matriz da §2.6.2: com o **mesmo** SDK e o **mesmo** payload, só a célula `fastmcp` 3.4.4 perde o frame de forma determinística (0/10) — e o 0/10 se mantém nas **duas** formas de payload medidas |
| **Pontas da faixa** | `fastmcp` 3.4.4 (lockfile atual) vs `fastmcp` 3.2.0 / `mcp` 1.28.1 (piso do `pyproject.toml`) | **Ambas perdem o frame** sob EOF imediato e **ambas respondem** com o transporte aberto. Atualizar ou rebaixar dentro da faixa **não** corrige o sintoma |

**Conclusão da dimensão de versão:** o defeito **não é do SDK `mcp`**, é da
**camada `fastmcp` 3.x** usada pelo Khan — e ela **não tem correção dentro
da faixa declarada** (`fastmcp>=3.2.0`). Porém, como §2.6.2 e §2.6.4
mostram, essa camada **responde corretamente** em qualquer cliente que
mantenha o transporte aberto, que é o comportamento de todo cliente MCP
real (`mcp.ClientSession`, o broker do Percival, o runtime do Positronic).
Logo: **não há defeito a fechar no servidor, e nenhuma limitação precisa
ser aprovada** — o que o F4/F5 mediu foi o instrumento, não o produto.

A camada `fastmcp` 3.x é, ainda assim, uma **fragilidade real e
registrada**: qualquer harness futuro que feche o stdin antes de ler a
resposta voltará a "detectar" o defeito. A correção durável é o teste de
protocolo (§2.6.5), que mantém o transporte aberto e lê o frame — e o
conformance de container, que emite o `tools/call` antes do fechamento
(stdin).

Também descartadas por teste direto:

| Hipótese | Teste | Resultado |
| --- | --- | --- |
| Falta `notifications/initialized` | payload sem a notificação | **responde** (`[1, 2]`) |
| `protocolVersion` antigo rejeitado | `2024-11-05` | **responde**, e o servidor devolve `2024-11-05` |
| `tools/list` consome o frame seguinte | id 2 = `tools/list`, id 3 = `tools/call` | ambos chegam |
| Tool assíncrona vs síncrona é o gatilho | mesma tool como `def` e como `async def` sob `fastmcp` 3.4.4 | **ambas perdem** o frame sob EOF imediato — o gatilho não é a forma da tool |

#### 2.6.4 O `tools/call` real funciona (evidência no protocolo)

Cliente MCP real (`mcp.ClientSession` + `mcp.client.stdio.stdio_client`),
servidor real, workspace isolado por `KHAN_WORKSPACE_DIR`:

| Chamada | `isError` | Evidência no protocolo |
| --- | --- | --- |
| `initialize` | — | `serverInfo.name = percival-khan-calendar`, `protocolVersion 2025-11-25` |
| `tools/list` | — | **12 tools**, exatamente a superfície declarada |
| `tools/call khan_get_status` | `false` | `Percival Khan Calendar Server operational.` + workspace isolado |
| `tools/call khan_list_calendars` (invoca `khal`) | `false` | calendário `nanobot` no envelope `<calendar_untrusted_data>` |
| `tools/call khan_list_events` (invoca `khal`) | `false` | `No events found.` |
| `tools/call khan_create_event` → `khan_list_events` → `khan_search_events` | `false` | round-trip: o evento criado aparece nas três leituras |
| `tools/call khan_list_events` com argumento inválido | **`true`** | `unexpected_keyword_argument` — erro de validação volta como frame, não como queda |

A mesma execução contra a **imagem F3 em uso**
(`percival-khan-calendar:0.4.0-d8d4122-f3-2500221a747e`, image
`sha256:55cd5a038d22…`, via `docker run --network=none` com `/data` em
tmpfs) devolve `tools/call` correto para `khan_get_status`,
`khan_list_calendars` e `khan_list_events`. O defeito do F4/F5 **não se
reproduz nem no checkout nem na imagem**.

#### 2.6.5 Correção durável: teste de protocolo e conformance

O teste de protocolo foi gravado no repositório do Khan, onde a ausência era
o defeito de fundo (todos os testes antigos chamavam a função por trás do
tool — `tests/_helpers.py:9`-`:34`).

- **Novo** `tests/test_protocol_stdio.py` (7 testes): handshake
  `initialize`; `tools/list` com as 12 tools; `tools/call` de
  `khan_get_status`; `tools/call` de `khan_list_calendars` (com `khal`);
  round-trip de escrita/leitura; erro de validação como frame; e prova de que
  o calendário real não é tocado. Cada servidor sobe com
  `KHAN_WORKSPACE_DIR` temporário e `KHAN_ENABLE_LOCK=false`; a fixture
  `isolated_workspace` (`tests/conftest.py:12`-`:13`) continua sendo a unidade de
  isolamento do resto da suíte. O transporte **fica aberto** durante a
  chamada — a própria lição do bug está no desenho do fixture.
- **Estendido** `scripts/docker-ci-conformance.py`: novas flags
  `--call-tool` / `--call-args`, com o `tools/call` emitido **antes** do
  fechamento do stdin (a ordem que o harness F4 errou) e validação de
  `result`, `isError` e `content` do frame.
- **CI** (`.github/workflows/ci.yml`): o job `docker` passa a invocar o
  conformance com `--call-tool khan_get_status`, para que a imagem
  publicada seja provada no protocolo e não só no handshake.

Verificação local no repositório do Khan:

```
pytest                → 227 passed, cobertura 87.89% (mínimo 80% do pyproject)
ruff check .          → All checks passed!
ruff format --check . → 55 files already formatted
conformance (imagem F3, tmpfs em /data, --network=none)
                      → stdio MCP conformance passed: initialize + tools/list (12 tools) + tools/call khan_get_status
```

#### 2.6.6 Estado da D5

**Fechada em 2026-10-23.** O critério de aceite foi cumprido integralmente:
chamada MCP real de leitura com evidência **no protocolo**; reprodução em
fixture sem tocar o calendário real; e a investigação da versão **fechada
com separação explícita** entre bug de versão, pin e config — o veredicto é
que **não é pin nem config**, que a camada `fastmcp` 3.x é o gatilho
**apenas quando o cliente fecha o transporte**, e que **não há defeito de
protocolo a corrigir**.

**Sem promoção de imagem.** As mudanças são no repositório do Khan
(`tests/test_protocol_stdio.py`, `scripts/docker-ci-conformance.py`,
`.github/workflows/ci.yml`) e foram **commitadas e enviadas** em
2026-10-23 (`0bc52b9`, `test(protocol): prove tools/call over the wire and
gate the image on it`) — **não publicadas**; o gate de imagem publicada
continua sendo D8/I3.

**Correção retroativa pendente de decisão do operador:** o
[relatório F4/F5](../reports/2026-10-10-f4-f5-closure-report.md) (linha 18) e a
§5 do [relatório F7](../reports/2026-10-10-f7-khan-allowlist-and-duplicates.md)
afirmam que o Khan não devolve o frame JSON-RPC e sugerem "investigar a
versão e testar `khan_get_status` com `mcp client` Python ou atualizar o
`mcp[cli]`". Essa afirmação está **corrigida** por esta seção. O relatório
versionado não foi reescrito — relatórios são evidência, e a reescrita
excederia o escopo desta D5 —; o registro da correção fica aqui e no registo
de execução (§6). A **recomendação de "atualizar o `mcp[cli]`" fica sem
fundamento**: nenhuma das duas pontas da faixa (`1.28.1`/`3.2.0` e
`1.30.0`/`3.4.4`) reproduz o defeito com transporte aberto.

**Risco residual registrado, sem ação imediata:** a camada `fastmcp` 3.x
é determinística em perder o frame quando o cliente fecha o stdin antes de
ler a resposta (0/10, nas duas formas de payload medidas). Os consumidores
reais — broker do Percival
([`broker.py:283`-`:325`](../../nanobot/mcp_docker/broker.py#L283-L325), que
faz o handshake e lê o frame **antes** de fechar) e runtime do Positronic —
não fecham o transporte nesse ponto, e o §2.6.4 prova o `tools/call` pelo
cliente real. Fica como **fragilidade a monitorar**: um futuro harness
fechar o stdin cedo voltará a reportar um defeito inexistente. A mitigação
é o teste de protocolo e o conformance, ambos já gravados.

**Ampliação do risco residual, medida na reexecução:** a fragilidade **não
é exclusiva** do `fastmcp` 3.x. As camadas do SDK (`mcp.server.fastmcp` e
`mcp.server.lowlevel.Server`) também perdem o frame de forma intermitente
sob EOF imediato — 9/10 e 8/10 na forma F4, caindo para 2/10 e 4/10 na
forma com `tools/list` antes. O Notes real, sobre `mcp.server.fastmcp`,
falha em 9/10 e 1/10 respectivamente. Ou seja: **qualquer servidor MCP
stdio que use o `stdio_server` do SDK perde o frame de forma intermitente
quando o cliente fecha o stdin antes de ler a resposta**; o que o
`fastmcp` 3.x acrescenta é a **determinismo** da falha. Isso reforça a
conclusão central desta D5 — o defeito era do **harness** — e reforça a
mitigação: nenhum consumidor real deve fechar o transporte antes de ler o
frame.

**Não decidido nesta D5, por estar fora do escopo:** migrar o Khan de
`fastmcp` 3.x para a camada `mcp.server.fastmcp` do SDK (ou para
`mcp.server.lowlevel.Server`), o que eliminaria a fragilidade na origem.
Isso é mudança de arquitetura do servidor, não correção de regressão, e
exige decisão própria do operador.

### 2.7 D7 — contrato de runtime por gestor (2026-10-23, agente)

**Veredicto: o core já está provado (I2), mas os seis MCPs não têm contrato
de runtime homologado — e a medição encontrou um defeito de sinal no caminho
do Percival que a auditoria pré-I2 não tinha registrado.** A D7 não é uma
tarefa inacabada: ela tinha duas partes, e as duas foram executadas. O
reaproveitamento do I2 é válido para o core e está citado abaixo; o que
faltava eram os **contratos MCP por gestor**, medidos agora.

#### 2.7.1 O que o I2 já provou e o que foi reaproveitado

O [contrato de runtime 1](../agent-runtime-contract.md) e o
[relatório I2](../reports/2026-10-23-i2-runtime-contract-conformance.md)
mantêm-se válidos para o **core**: 19 checks PASS cobrindo gateway/API/CLI/
broker, identidade de processo, UID/GID, caps, `NoNewPrivs=1`, probe
autenticada, `doctor`, EOF e SIGTERM. Conforme
[`.agent/workflow.md`](../../.agent/workflow.md), essa evidência é
**carried forward** com a justificativa de que nada do core foi alterado
nesta D7: o único arquivo novo é um script de medição, e nenhuma imagem,
configuração ou container de produto foi tocado. **O que o I2 não cobre, e
que a D7 precisava cobrir**, são os **MCPs**: o I2 exercitou um fixture
stdio genérico, não os seis servidores oficiais.

#### 2.7.2 Instrumento: `scripts/percival-mcp-runtime-contract.py`

O gap era de evidência, não de conceito: os seis MCPs tinham **contratos
de imagem declarados** (Dockerfile, entrypoint, `EXPOSE`, `HEALTHCHECK`,
`USER`, `STOPSIGNAL`) e **testes de contrato de imagem** em apenas três
repositórios — Weather (`tests/test_dockerfile.py`), OSM
(`tests/test_d6_docker.py`) e Deep Research (`tests/test_docker.py`). Notes,
Khan e AgentMail **não tinham** teste de contrato de imagem; o Khan só
recebeu, na D5, um teste de **protocolo**, que é outra coisa.

O instrumento novo mede o contrato **em runtime**, sobre containers
descartáveis, e é **read-only** quanto ao estado vivo: nome único, rede
privada, workspace temporário e remoção no fim. Ele não toca containers em
execução, configuração, credenciais nem estado do host. Para cada imagem e
cada gestor, mede duas coisas em containers separados:

- **EOF** — o cliente fecha o stdin; o servidor deve responder `initialize`
  e terminar com **exit 0**;
- **SIGTERM** — o container é parado como um gestor para; deve terminar com
  **exit 143**.

E mede, em ambos: TTY, stdin aberto, portas publicadas, healthcheck, UID
efetivo, `CapEff`, `NoNewPrivs`, sockets em escuta, PID 1 e a máscara
`SigCgt` de PID 1. As flags de lançamento **não são inventadas**: são as
que cada gestor usa de fato — `nanobot/mcp_docker/broker.py:182`-`:189`
(`--cap-drop=ALL --security-opt=no-new-privileges`, sem `--init`) e
`alternative-positronic/packages/positronic-mcp-docker/src/managed.ts:640`
(`--pull=never --rm --init --interactive`).

Reprodução de uma célula (o `exit` é diferente de zero quando há violação
do contrato, o que é o comportamento esperado hoje no caminho do Percival):

```bash
python3 scripts/percival-mcp-runtime-contract.py \
  --image sha256:ef4082ef13905cdaa0da23830bcc6c5b88ca3beb30074e11d56593d11a097460 \
  --name notes --manager percival \
  --env PERCIVAL_NOTES_VAULT_PATH=/vault \
  --mount type=tmpfs,destination=/vault,tmpfs-mode=0777 \
  --output /tmp/d7-contract/notes.json
```

#### 2.7.3 Matriz medida (imagens F3 em uso, 2026-10-23)

Seis imagens, dois gestores, dois modos: 24 medições. Resultado
**consolidado**:

| MCP | init na imagem | Percival: EOF / SIGTERM | Positronic: EOF / SIGTERM | `NoNewPrivs` (Percival / Positronic) |
| --- | --- | --- | --- | --- |
| Notes | não | 0 / **137** | 0 / 143 | 1 / 0 |
| Khan | não | 0 / **137** | 0 / 143 | 1 / 0 |
| Weather | não | 0 / **137** | 0 / 143 | 1 / 0 |
| AgentMail | não | **não serviu** / **137** | **não serviu** / 143 | 1 / 0 |
| OSM | tini | 0 / 143 | 0 / 143 (**2 camadas de init**) | 1 / 0 |
| Deep Research | tini | 0 / 143 | 0 / 143 (**2 camadas de init**) | 1 / 0 |

O que está **conforme** em todas as 24 medições: **sem TTY**, **stdin
aberto**, **zero portas publicadas**, **zero sockets em escuta** (o stdio
não abre listener), `CapEff=0`, e **sem healthcheck HTTP** — exceto o OSM,
que traz `HEALTHCHECK NONE` explicito, que é a forma correta de declarar
"não há probe". O `EXPOSE` de OSM/Deep/Weather é **documentação**, não
publicação: nenhuma porta é publicada em runtime.

#### 2.7.4 Achado 1 — no caminho do Percival, o SIGTERM não chega ao servidor

**É o achado novo desta D7, e é um defeito de código do core, não falta de
evidência.** Quatro das seis imagens (Notes, Khan, Weather, AgentMail) **não
têm init embutido**: o PID 1 é o próprio processo do servidor. O broker do
Percival **não passa `--init`** ([`broker.py:182`-`:189`](../../nanobot/mcp_docker/broker.py#L182-L189)),
e o runbook do próprio projeto determina o contrário — "Stdio usa
`stdin_open: true`/`tty: false` e `docker run --init`"
([`docs/operations/mcp-docker-local-runbook.md:14`](../../docs/operations/mcp-docker-local-runbook.md#L14)).

Sem init, **PID 1 não instala handler de SIGTERM**, e o kernel **não
entrega o sinal**: dentro de um namespace de PID, o init do namespace só
recebe sinais externos se tiver handler instalado. O `docker stop` então
espera o grace period inteiro e escala para SIGKILL.

**Mecanismo medido, não inferido** — caso mínimo controlado, sem MCP:

| Caso | PID 1 | `SigCgt` | `docker stop` | Saída |
| --- | --- | --- | --- | --- |
| `sh` com `trap … TERM`, sem init | o script | `0x14002` (bit 14 ligado) | 1,1 s | **42** (o trap roda) |
| `sh` sem trap, sem init | o script | `0x10002` | 10,2 s | **137** (SIGKILL) |
| `sh` sem trap, **com** `--init` | `/sbin/docker-init` | `0x0` | 0,1 s | **143** |

Ou seja: **o `SigCgt=0` do init não é defeito** — o init não precisa de
handler, ele **encaminha** o sinal ao filho. E o bit 14 (`0x4000`) de
`SigCgt` é exatamente "SIGTERM tratado".

**Efeito prático, medido no caminho real do broker** (`docker stop` com o
grace default de 10 s, container do Notes):

| Caminho | Duração do stop | Código de saída |
| --- | --- | --- |
| Percival (sem `--init`) | **10,2 s** | **137** |
| Positronic (com `--init`) | 0,1 s | 143 |

Ou seja: **todo `stop`/`deactivate`/`exclude` de um MCP sem init sob o
Percival custa o grace period inteiro e termina em SIGKILL**, e o
`docker rm -f` do caminho de remoção ([`broker.py:163`](../../nanobot/mcp_docker/broker.py#L163))
é o que encerra de fato o container. Para os MCPs com tini (OSM, Deep
Research) o caminho está correto: 0,1 s e 143.

**Alcance.** É um defeito de **parada limpa**, não de funcionamento: as
24 medições mostram que os MCPs servem corretamente (exit 0 no EOF) sob o
Percival, e nada na D5/D7 indica perda de dado. Mas ele contradiz o
runbook, produz saída 137 em vez de 143 e paga o grace period a cada
parada. **Correção:** o broker deve passar `--init` ao lançar MCPs stdio
— o que é seguro para os MCPs **sem** init (Notas/Khan/Weather/AgentMail) e
**precisa** ser pareado com a remoção do tini embutido de OSM e Deep
Research, sob o gestor que os lança, para não criar init duplo. Como os
dois lados pertencem a repositórios distintos (core e MCPs), a correção é
**dupla** e o operador precisa decidir a ordem.

#### 2.7.4.1 Dono do init — decisão do agente, com a medição que a sustenta

Os dois achados de init (1 e 2) **não são dois defeitos independentes**:
são **um só defeito com duas faces** — a camada de init do runtime stdio
**não tem dono único** no Percival. O levantamento por repositório mostra
quatro donos diferentes para a mesma responsabilidade:

| MCP | `init:` no compose | tini embutido na imagem | `--init` do Positronic | `--init` do broker |
| --- | --- | --- | --- | --- |
| Notes / Weather / Khan / AgentMail | `init: true` | não | sim | **não** |
| OSM / Deep Research | não | **tini** | sim | **não** |

O contrato de runtime 1 **já nomeia o dono** e é explícito:
*"`init: true` belongs to Compose. Images do not embed a second init"*
([`docs/agent-runtime-contract.md:109`-`:112`](../../docs/agent-runtime-contract.md#L109-L112)).
O runbook diz o mesmo para o caminho stdio: *"Stdio usa `stdin_open:
true`/`tty: false` e `docker run --init`. Duplo init cria falsa camada de
supervisão"* ([runbook:14](../../docs/operations/mcp-docker-local-runbook.md#L14)).

**Decisão: o init pertence ao gestor (o `--init` do launch), e a imagem não
embute init.** Essa é a direção que reconcilia os três repositórios com o
contrato já vigente, e resolve os dois achados de uma vez:

- o broker do Percival passa a passar `--init` → o achado 1 desaparece;
- OSM e Deep Research deixam de embutir tini → o achado 2 desaparece
  (o `docker-init` do Positronic deixa de ser duplicado);
- os compose dos seis MCPs passam a declarar `init: true` → o caminho
  local/self-hosted também fica com um init só.

**A decisão precisa ser segura sob as flags do broker.** O contrato de
runtime 1 alerta que *"Root init needs `CAP_KILL` to signal the child after
UID drop … Without KILL the constrained root init was observed to fail
forwarding SIGTERM"*, e o broker usa `--cap-drop=ALL`. Essa combinação
**não** estava medida. Medida antes de decidir, com a imagem do Notes:

| Flags | PID 1 | `SigCgt` de PID 1 | `docker stop` | Saída |
| --- | --- | --- | --- | --- |
| `--cap-drop=ALL --security-opt=no-new-privileges` (**atual**) | o servidor Python | `0x100000002` | **10,1 s** | **137** |
| `--cap-drop=ALL --security-opt=no-new-privileges --init` (**proposta**) | `/sbin/docker-init` | `0x0` | **0,1 s** | **143** |
| `--cap-drop=ALL --cap-add=KILL --init` | `/sbin/docker-init` | `0x0` | 0,1 s | 143 |
| `--init` (Positronic) | `/sbin/docker-init` | `0x0` | 0,1 s | 143 |

**O `--init` funciona mesmo com `--cap-drop=ALL`**: não é preciso
`--cap-add=KILL`. O `docker-init` corre com `CapEff=0` e ainda assim
encaminha o SIGTERM ao filho — o filho continua com `SigCgt=0x100000002`
(bit 14 ligado) e o container sai em 143.

**Sobre o `SigCgt=0` do init:** o init **não instala handler** — ele
**encaminha** o sinal ao filho. Por isso `SigCgt=0` em PID 1 com `--init`
não é defeito, e por isso o `SigCgt` **não é o critério de conformidade**.
O critério é o **comportamento observável**: `docker stop` deve terminar em
143, e não em 137. Note ainda que, sem init, o PID 1 **é** o servidor
Python e tem o bit 14 ligado — ou seja, o servidor **tem** handler de
SIGTERM, mas **o kernel não entrega o sinal** a ele: dentro de um
namespace de PID, o init do namespace só recebe sinais externos se tiver
handler instalado. Um handler no processo não basta enquanto o processo é
o init do namespace — é o init que precisa estar em condições de
encaminhar.

#### 2.7.5 Achado 2 — init duplicado no consumidor Positronic

**Confirmado, e é defeito de código de outro repositório.**
`alternative-positronic/packages/positronic-mcp-docker/src/managed.ts:640`
monta `docker run --pull=never --rm --init --interactive` **incondicionalmente**.
As imagens do OSM (`percival-osm/Dockerfile:146`) e do Deep Research
(`percival-deep-research/Dockerfile:155`) **já entram por tini**. O
resultado medido é **2 camadas de init** (`docker-init` sobre `tini`) em
todas as 4 medições desses dois MCPs sob o gestor Positronic. É o achado
de F6 ([`docs/reports/2026-10-10-f6-local-cutover.md:49`](../../docs/reports/2026-10-10-f6-local-cutover.md#L49)),
**ainda vivo**, e agora medido: as árvores de processo confirmam
`/sbin/docker-init -- /usr/bin/tini -- …` nos containers Positronic de
OSM e Deep Research, contra `/usr/bin/tini -- …` nos containers Percival
dos mesmos MCPs.

**Consequência medida:** a falha é de **supervisão falsa**, não de
funcionamento — os dois MCPs continuam servindo (EOF exit 0) e param
limpo (143). O custo é uma camada de supervisão que mascara qual processo
é o responsável pelo sinal, o que o runbook proíbe explicitamente
("Duplo init cria falsa camada de supervisão") e o que a auditoria
pré-I2 classificou como N1.

#### 2.7.6 Achado 3 — `NoNewPrivs` e caps divergem entre gestores

O Percival aplica `--cap-drop=ALL --security-opt=no-new-privileges`; o
Positronic **não aplica nenhum dos dois**. Medido: `NoNewPrivs=1` e
`CapEff=0` sob o Percival; **`NoNewPrivs=0`** sob o Positronic em todos os
6 MCPs. `CapEff=0` em ambos, porque as imagens já correm como não-root com
`USER` — mas `NoNewPrivs=0` significa que um binário setuid ou um
`capability` herdado **não** seria impedido pelo kernel.

Este é **diferença de política entre gestores**, não um defeito do core: o
broker do Percival escolhe deliberadamente `--cap-drop=ALL` +
`no-new-privileges`, e o runbook exige "privilégio mínimo". O consumidor
Positronic não tem essa escolha equivalente. **Registrado como divergência
a decidir pelo operador** — não é coberto pelo contrato de runtime 1, que
descreve o core e o broker, não o consumidor Positronic.

#### 2.7.7 Achado 4 — o AgentMail não serviu no ambiente isolado

Nas 2 medições de EOF, o AgentMail **não respondeu `initialize`** e
terminou com **exit 1**. A causa é externa ao contrato de runtime: o
entrypoint do MCP faz um **health check do upstream** no startup
(`percival_agentmail_mcp/server.py:41`-`:57`) e falha com
`httpx.ConnectError` quando o upstream não é resolvível
(`--network=none` + chave de teste inválida). O mesmo vale para o Deep
Research, que exige `INFERENCE_API_KEY`/`OPENAI_API_KEY` — resolvido ao
passar a variável, e então ele **serviu** normalmente (exit 0 no EOF).

Isto **não** é uma violação do contrato de runtime: é uma **precondição de
startup** do servidor. O probe distingue os dois casos e reporta
"startup precondition not met", e não "falha de EOF" — distinção que
importa porque um servidor que falha no startup **não** pode ser julgado
pelo EOF.

#### 2.7.8 Correção aplicada — init único, com dono único

Os dois achados de init foram **corrigidos** em 2026-10-24, com a
autorização do operador, aplicando a decisão da §2.7.4.1: **o init pertence
ao gestor, e a imagem não embute init.**

**Core (broker do Percival)** — commit `79dda0a0`:

- [`broker.py:182`](../../nanobot/mcp_docker/broker.py#L182) passa `--init` no
  `docker run` do `_spawn`.
- A política é **verificada após o spawn** ([`broker.py:204`](../../nanobot/mcp_docker/broker.py#L204)):
  se o daemon não honrou o init, o broker falha fechado com `BrokerError`.
- O gate de **retomada** ([`broker.py:247`](../../nanobot/mcp_docker/broker.py#L247))
  rejeita containers criados antes do fix, em vez de reutilizá-los com o init
  quebrado.
- Testes: `tests/mcp_docker/` → **85 passed**; `ruff check` e
  `basedpyright nanobot/mcp_docker/broker.py` limpos.

**Imagens (seis MCPs)** — OSM `7f3cb3e`, Deep Research `6bcb752`, Notes
`36c4016`, Khan `13f8fce`, AgentMail `31d6b1c`, Weather `81b3aaa`:

| Repo | Dockerfile | Compose | Teste de contrato | Lançadores locais |
| --- | --- | --- | --- | --- |
| OSM | tini removido | `init: true` | `tests/test_d6_docker.py` invertido | smoke com `--init` |
| Deep Research | tini removido | `init: true` | `tests/test_docker.py` invertido | smoke + probe stdio com `--init` |
| Notes | já sem init | `init: true` (já tinha) | **`tests/test_docker_contract.py` (novo)** | conformance, smokes e benchmark com `--init` |
| Khan | já sem init | `init: true` (já tinha) | **`tests/test_docker_contract.py` (novo)** | conformance e README com `--init` |
| AgentMail | já sem init | `init: true` (já tinha) | **`tests/test_docker_contract.py` (novo)** | conformance e README com `--init` |
| Weather | já sem init | `init: true` (já tinha) | `tests/test_dockerfile.py` ampliado | smoke e README com `--init` |

O teste de contrato de imagem nos três repositórios que não o tinham é
**estático** (lê Dockerfile e compose como texto, sem daemon): a imagem **não
pode** embutir init, o serviço compose **tem** de declarar o `init: true`
único, o usuário **tem** de ser não-root e o serviço stdio **não** pode expor
porta nem healthcheck.

**Verificação de que há um init só, renderizada pelo próprio Compose** —
`docker compose config --format json` nos seis repositórios:

| Repo | Serviço | `init` |
| --- | --- | --- |
| OSM | `mcp-osm` | `true` |
| Deep Research | `percival-deep-research-stdio` / `-http` | `true` / `true` |
| Weather | `percival-weather-stdio` | `true` |
| Notes | `percival-notes` | `true` |
| Khan | `server` | `true` |
| AgentMail | `server` | `true` |

**Suítes:** core `tests/mcp_docker/` 85 passed; Notes 52 passed; Khan 231
passed; AgentMail 236 passed + 1 skipped (integração live); Weather, OSM e
Deep Research verdes. `ruff check` limpo nos seis (o desvio de `ruff format`
no Deep Research e os 99 avisos do OSM são **pré-existentes**, confirmados por
`git stash` sobre a árvore sem as mudanças). `git diff --check` limpo nos
sete repositórios.

> **Retificação (2026-10-24, ver §6):** a afirmação "OSM e Deep Research
> verdes" acima se refere às **suítes de teste**, não aos smokes de imagem. Os
> smokes de imagem do OSM e do Deep Research **não executavam a tempo** — a
> verificação de init herdou a asserção anterior à correção e affirmava o
> **inverso** do contrato. Corrigido depois, em `946ce44` (OSM) e `1d4c541`
> (Deep Research), com os dois smokes passando contra a imagem reconstruída.

**O consumidor Positronic não precisou de alteração:** o `--init`
incondicional dele deixa de duplicar quando as imagens param de embutir tini
(§2.7.4.1). O `NoNewPrivs=0` sob o Positronic (achado 3) **continua
divergente** e não foi tocado — é decisão de política do gestor, não um
defeito de contrato.

#### 2.7.9 O que a D7 **não** fecha

- **O manual operacional ainda tem uma lacuna que esta D7 expôs:** a §3.10
  do [runbook](../../docs/operations/mcp-docker-local-runbook.md) diagnostica
  o **init duplicado**, mas não o caso **sem init algum** — que é
  exatamente o defeito do caminho do Percival, e em que o `docker stop`
  termina em 137 em vez de 143. O alinhamento do manual continua sendo
  **D9** (que já é dona do walkthrough de sinais por modo); a D7 não edita o
  manual para não antecipar um item que o operador ainda não fechou.
- **Não é** homologação de release: as imagens medidas são as F3 de
  diagnóstico (`io.percival.build.worktree=dirty` em quatro delas), sem
  digest OCI de registry, sem SBOM, sem scan, sem build limpo. O gate de
  build limpo e pin por digest é da **D8**; o de publicação, do **D8/I3**.
  As correções de init mudam o conteúdo das imagens de OSM e Deep Research:
  elas **precisam** ser reconstruídas e promovidas sob a D8.
- **Não é** aprovação de serviço externo: o AgentMail falhou por
  dependência de upstream, o que não diz nada sobre a qualidade do serviço
  nem sobre credenciais.
- **ARM64, VPS, Engine 27.x, I6 (homologação de apps), I8 (recuperação sob
  carga) e C1–C4** mantêm seus escopos. Nada aqui substitui o I2 para o
  core nem o I6 para os MCPs.
- **A `NoNewPrivs` do Positronic** (achado 3) segue aberta como decisão de
  política do gestor.

**Estado da D7:** **fechada em 2026-10-24** — os dois defeitos de init foram
corrigidos, os testes de contrato de imagem existem nos seis repositórios e
o init único está verificado no core e no renderizado do Compose dos seis.
A evidência de runtime é reproduzível com
`scripts/percival-mcp-runtime-contract.py`; nenhum container de produto,
imagem, registry, instância ou credencial foi mutado — só código, testes,
compose e documentação.

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
  Positronic com uma prova do broker Percival. **Fechado em 2026-10-24**: init
  único com dono único (o gestor), broker do core passa `--init` e verifica a
  política, os seis compose declaram `init: true` e o contrato de imagem existe
  nos seis repositórios (§2.7.8).
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

**2026-10-23 — D3: levantamento da superfície efetiva do Khan (agente; decisão do operador pendente).**
Read-only. Nenhuma mutação de configuração, registry, container, broker ou imagem.
Levantamento completo em §2.3. Verificações: `tools/list`, `prompts/list`,
`resources/list` e `resources/templates/list` contra o container em execução
(`percival-khan-calendar:0.4.0-ce69267`, image `sha256:55cd5a038d22…`); estado
canônico do Percival (`~/.nanobot/config.json` → `tools.mcpDocker.servers["khan-calendar"]`);
allowlist do Positronic (`~/.positronic/mcp/servers/khan-calendar.json`, via
`positronic mcp server show khan-calendar`); API do Positronic em execução
(`GET /experimental/positronic/mcp/installed`, `GET /mcp`,
`GET /experimental/resource`, `GET /command`); log do gateway
(`skipping resource/prompt registration` + `connected, 12 capabilities registered`);
código dos dois consumidores (`nanobot/agent/tools/mcp.py`,
`nanobot/mcp_docker/broker.py`, `packages/opencode/src/mcp/index.ts`,
`packages/positronic-mcp-docker/src/managed.ts`); source do Khan
(`src/percival_khan_calendar/server.py:99`, `tools/delete_event.py:30` e `:54`,
`constants.py`).

Achados que mudam o quadro: (1) o critério anterior da D3 estava errado — são
**12 tools + 6 prompts + 1 resource = 19**, não "17 / 7 de escrita"; (2) os dois
gestores **divergem** — Percival expõe 12 tools e nenhum prompt/resource,
Positronic expõe **1 tool** (`khan_get_status`) mas **todos os 6 prompts e o
resource**; (3) a allowlist do gestor restringe **tools**, nunca prompts nem
resources; (4) `allowedProjects` é escopo de projeto, não permissão de tool;
(5) o [relatório F7 de 2026-10-10](../reports/2026-10-10-f7-khan-allowlist-and-duplicates.md)
está desatualizado: a allowlist do Positronic mudou para 1 tool em 2026-10-20
(gate humano do smoke F3.0.1); (6) **D10 está parcialmente invalidada** — o
binário `positronic` passou a existir no PATH e os 11 comandos da skill
existem no CLI atual.

A D3 **não fecha** aqui: falta a decisão do operador sobre a superfície por
gestor (§2.4) e a aplicação do reflexo dessa decisão nas configurações.

**2026-10-23 — D3 fechado (decisão do operador; aplicação pelo agente).**
- **Decisão do operador:** superfície **completa nos dois gestores** (12 tools do
  Khan liberadas em ambos); prompts e resources **fora** de allowlist de tool
  registrados como **limitação aceita**; aplicação autorizada ao agente.
- **Mutação aplicada:** uma, no Positronic — `allowedTools` do Khan elevada de 1
  (`khan_get_status`) para 12 via `positronic mcp server configure khan-calendar 1
  --network none --mount … --env KHAN_WORKSPACE_DIR=/data --tools <12>`. Config
  `revision` 1→2; `configurationId` `9ee229c8-…` **inalterado**; `network: none`,
  mount do workspace sintético em `/data` e `env` preservados; registry
  `revision` 10 inalterado. **O Percival não foi mutado** — já estava em
  `toolsDisabled: []` com as 12 tools.
- **Rollback:** snapshot privado da configuração anterior em
  `~/.local/state/positronic-d3-snapshots/khan-calendar.json.rev1.20261023T220640Z.bak`
  (`saveConfig` não cria backup próprio).
- **Verificação da projeção (Positronic):** `server show` (12 tools, rev 2),
  `server discover` (12 tools pelo protocolo), `server preview` (`tools: 12`,
  `refreshKey 10:9ee229c8-…:2`), `POST …/managed/inspect` (config persistida),
  `POST …/managed/command {"action":"reconnect"}` → `status: ready`,
  `generation 777b633dce4cf9fa` (= `Bun.hash("10:9ee229c8-…:2")`; a revisão 1
  daria `a06460b29a18bd0f`), `GET /mcp` (connected), `GET /command` (6 prompts
  como comandos) e `GET /experimental/resource` (1 resource).
- **Verificação da projeção (Percival):** `tools/list` JSON-RPC completo contra
  o broker (12 tools, executado dentro do container do broker, onde a porta
  18081 não é publicada) e log do gateway (`connected, 12 capabilities registered`;
  `skipping resource/prompt registration`).
- **Auditoria:** `~/.positronic/logs/audit.jsonl` → `experimental.positronic.mcp.server.config`
  `committed` para `khan-calendar` em `2026-10-23T22:06:48Z`.
- **Limitações registradas:** (1) prompts e resources do Khan **não** são
  cobertos por allowlist de tool no Positronic e **não** são expostos no
  Percival — assimetria por construção, não remediavel por configuração;
  (2) não existe endpoint do runtime Positronic que enumere as tools MCP
  efetivas (`registry.ids()` devolve só builtin/custom), então a prova é a
  composição `preview` + `discover` + `inspect` + `reconnect`.
- **Artefato de evidência:** §2.4 deste plano.
- **Estado:** **D3 fechado.** Sem promoção de imagem, sem alteração do servidor
  Khan, sem alteração do fork do Positronic. D4–D12 inalterados; o encerramento
  consolidado continua bloqueado por D4–D10 e pelos gates externos C1–C4 e A1–A9.

**2026-10-23 — D4: atribuição das duplicatas por container ID (agente; read-only).**
Nenhum `docker stop`/`rm`/`kill`, nenhuma mudança de configuração, registry ou
journal. Levantamento completo em §2.5. Verificações: `docker ps -a` e
`docker inspect` nos 19 containers da máquina; labels `percival.mcp-docker.*` nos
6 do broker; labels `io.positronic.{run,context,home}` nos 11 do Positronic;
cruzamento integral com `~/.positronic/mcp/executions/*/owner.json`
(`state`, `container`, `pid`, `boot`, `start`); resolução dos dois contextos por
hash SHA-256 do diretório; correlação com os processos vivos
(`opencode serve` PID 98403 cwd `/home/bill`; `opencode attach --dir
/home/bill/.positronic` PID 111547); auditoria de lifecycle em
`~/.positronic/logs/audit.jsonl` (707 eventos) por `attempt`; journals em
`~/.nanobot/mcp-docker/transitions/*.json` e `audit.jsonl` do broker; leitura do
source dos dois gestores (`broker.py`, `execution.ts`, `managed.ts`,
`managed-stdio.ts`, `inventory.py`).

Achados: (1) **não há duplicata nem órfão** — 17 containers MCP, 17 donos
vivos; (2) o nome determinístico do broker torna **impossível** duas
instâncias do mesmo `server_id`; (3) no Positronic a cardinalidade é **≤1 por
`(servidor, contexto)`**, e os "2×" do F7 são **dois contextos de projeto**,
não duplicação; (4) o ciclo de vida é **demonstrado** pela auditoria
(`acquire` → `tools-list` → `close transport-closed` → novo `acquire`, com
`--rm` removendo o anterior); (5) o `instance-id` do broker é **por spawn**,
não por sessão — não é identificador de duplicata; (6) o inventário do Percival
**inclui** os containers do Positronic, porque filtra por nome/label/imagem —
quem precisar da cardinalidade por gestor tem de separar por
`percival.mcp-docker.managed-by`; (7) **achado residual de observabilidade** —
7 das 150 aquisições não têm desfecho gravado, porque o `close` não é
escrito quando o cliente é interrompido entre `acquire` e `tools-list`; uma
delas tem efeito observável (deep-research ausente em
`/home/bill/.positronic`, com `GET /mcp` nesse diretório em HTTP 499).

**Nenhuma limpeza.** O critério "zero referências confirmadas" da própria D4
não é atingido: os containers estão em uso. Nenhum `docker rm` executado.

**Estado:** **D4 fechado, com achado residual registrado.** Sem promoção de
imagem, sem mutação de runtime. Registrado no core no commit `1eeed82f`
(`docs(d4,d5): close the duplicate-attribution and Khan tools/call gates`),
enviado a `origin/main` em 2026-10-23. D5–D12 inalterados.

**2026-10-23 — D5: regressão Khan `tools/call` (agente).**
Investigação e correção em `/home/bill/Projects/percival-khan-calendar`.
Nenhuma mutação de instância, registry, container, imagem publicada ou
credencial; nenhuma promoção. Levantamento completo em §2.6.

Verificações: cliente MCP real (`mcp.ClientSession` +
`mcp.client.stdio.stdio_client`) contra o checkout; contra a imagem F3 em
uso (`percival-khan-calendar:0.4.0-d8d4122-f3-2500221a747e`, image
`sha256:55cd5a038d22…`) via `docker run --network=none` com `/data` em
tmpfs; reprodução fiel do harness F4 (`7e28d272`,
`scripts/f4-fixture-test.py`) contra o mesmo payload e a mesma imagem;
matriz de discriminação com N=10 por célula (`fastmcp` 3.4.4 standalone ×
`mcp.server.fastmcp` do SDK v1 × `mcp.server.lowlevel.Server` × Khan real,
com EOF imediato e com stdin aberto, `stderr` para arquivo e workspace novo
por repetição); matriz de duas pontas da faixa (`mcp` 1.28.1/`fastmcp` 3.2.0 em
venv isolado × `mcp` 1.30.0/`fastmcp` 3.4.4 do lockfile); **reexecução da
matriz** com harness reconstruído do zero, medindo as **duas** formas de
payload (forma F4 e forma com `tools/list` antes) nas quatro camadas, contra
o checkout e contra as imagens F3 do Khan e do Notes; leitura do source
do SDK (`mcp/server/lowlevel/server.py`, `mcp/server/stdio.py`,
`mcp/server/session.py`) e do FastMCP (`fastmcp/server/low_level.py`); e
inspeção da imagem do Notes (`mcp` 1.30.0, `mcp.server.fastmcp`,
`notes_mcp.py:19`) como controle.

Achados: (1) **o defeito do F4/F5 não reproduz** — `tools/call` responde
com cliente MCP real, no checkout e contra a imagem, para `khan_get_status`,
`khan_list_calendars`, `khan_list_events` e para o round-trip
`create`→`list`→`search`, com erro de validação retornando `isError: true`;
(2) a **causa** é a combinação entre o harness da F4 — que fechava o stdin
via `subprocess.run(input=…)` antes de ler a resposta — e a camada
`fastmcp` 3.x, cujo `run()` sobrescrito **não** cancela o handler em voo
quando o transporte fecha (o SDK low-level cancela em
`mcp/server/lowlevel/server.py:691`-`:696`); (3) **não é pin nem config**:
as duas pontas da faixa se comportam igual, e o `protocolVersion` antigo, a
notificação ausente e a forma da tool (sync/async) foram descartados por
teste direto; (4) **correção de leitura intermediária** — a hipótese de
latência de inicialização (o Node do Notes sobe em ~1.9 s, o Python em
~0.6 s) foi **refutada** pelos dados: o Khan é o mais rápido e mesmo assim
é o que perde o frame de forma determinística; a variável real é a camada
de servidor; (5) **controle com o Notes** (`mcp.server.fastmcp` sobre o
mesmo `mcp` 1.30.0) também perde o frame de forma **intermitente** sob EOF
imediato — o registro anterior de "5/5" foi **corrigido** na reexecução:
9/10 na forma F4 e 1/10 na forma com `tools/list` antes. O que distingue o
Khan é a **falha determinística (10/10)**, e é por isso que o F4/F5
observou o defeito só no Khan; (6) **reexecução da matriz** com harness
reconstruído, nas **duas** formas de payload: a célula `fastmcp` 3.x
continua **0/10** em ambas, enquanto a taxa das camadas do SDK varia com
a forma do payload (de 9/10 para 2/10) — o "8/10" original era
propriedade do harness, e a afirmação estável é a distinção
determinístico vs. intermitente.

**Artefatos gravados, commitados e enviados:** no repo do Khan,
`tests/test_protocol_stdio.py` (novo, 7 testes de protocolo com workspace
isolado por `KHAN_WORKSPACE_DIR`), `scripts/docker-ci-conformance.py`
(estendido com `--call-tool`/`--call-args`, emitindo o `tools/call` antes do
fechamento do stdin) e `.github/workflows/ci.yml` (job `docker` invocando o
conformance com `--call-tool khan_get_status`) — commit `0bc52b9`
(`test(protocol): prove tools/call over the wire and gate the image on it`),
enviado a `origin/main` em 2026-10-23. Os untracked `.positronic/policy.json`
e `.positronic/project.json` do repo do Khan são **pré-existentes e não
deste escopo**, e foram deixados de fora do commit.

**Verificação local:** `pytest` → 227 passed, cobertura 87.89% (mínimo 80%);
`ruff check .` → All checks passed!; `ruff format --check .` → 55 files
already formatted; conformance contra a imagem F3, com as mesmas flags do
CI (tmpfs em `/data` com `tmpfs-mode=0777`, `--env KHAN_WORKSPACE_DIR=/data`,
`--expected-uid 1000`, `--compose-service server`) →
`stdio MCP conformance passed: initialize + tools/list (12 tools) + tools/call khan_get_status`.
Teste negativo do conformance (`--call-tool khan_nonexistent`) → exit 1 com
`tools/call khan_nonexistent reported isError=true`, provando que o gate não
passa por ignorância.

**Estado:** **D5 fechado.** Sem promoção de imagem, sem mutação de runtime,
sem alteração do servidor Khan. A fragilidade da camada `fastmcp` 3.x
permanece registrada como risco residual; a decisão de migrar de camada
fica com o operador. D6–D12 inalterados.

**2026-10-23 — commit e push de D4 e D5 (operador autorizou).** O operador
decidiu: **commitar e enviar** nos dois repositórios; **manter** os
relatórios F4/F5 e F7 como estão (a correção fica na §2.6 e neste registo,
sem reescrever evidência versionada); e **não decidir agora** a migração do
Khan para a camada do SDK (registrada como risco residual). Commits:
core `1eeed82f` (`docs(d4,d5): close the duplicate-attribution and Khan
tools/call gates`) e Khan `0bc52b9`. Ambos enviados a `origin/main`. Nenhuma
imagem construída, promovida ou publicada; nenhum container, registry,
instância ou credencial foi mutado.

**CI após o push (2026-10-23).** No repo do Khan, o run
[40055008222](https://github.com/bill-kopp-ai-dev/percival-khan-calendar/actions/runs/40055008222)
(`0bc52b9`) está **verde**: `test (3.11)`, `test (3.12)` e
`Docker build + smoke` — incluindo o passo **"MCP stdio conformance
(offline)"**, que agora exige o `tools/call` real sobre a imagem recién
construída. É a **primeira prova remota** do `tools/call` por protocolo em
imagem de container, e fecha o gate local sem depender de confiança no
harness local. Nenhum workflow de push publica imagem: o run só constrói o
candidato local e arquiva `docker-build-manifest.json` e `sbom.cdx.json`.

O core **não gerou run**: o CI do core tem `paths-ignore` para `docs/**` e
`1eeed82f`/`b0f57b8c` só tocam `docs/**`. O gate de conformance do core
continua sem evidência nova neste SHA — dispara-lo por `workflow_dispatch`
autenticado é decisão do operador, como já registrado no D2. Nenhuma
imagem foi promovida: o gate D8/I3 segue aberto.

**2026-10-23 — D7: contrato de runtime por gestor (agente).**
Levantamento completo em §2.7. **Read-only quanto ao estado vivo**: nenhum
container de produto, imagem, registry, instância ou credencial foi mutado;
todos os containers de medição foram descartáveis, de nome único, com rede
privada e removidos no fim. Nenhuma promoção, nenhuma publicação.

Verificações: reaproveitamento justificado da evidência do I2 para o core
(nada do core foi alterado); leitura do contrato de runtime 1 e do relatório
I2; inventário read-only dos containers vivos dos dois gestores via
`python3 -m nanobot.mcp_docker.inventory` (19 containers, 17 MCP, com
`init`/`tty`/`stdinOpen`/`ports`/`healthcheck`); leitura dos Dockerfiles e
Compose dos seis MCPs; leitura das flags de lançamento de cada gestor
([`broker.py:182`-`:189`](../../nanobot/mcp_docker/broker.py#L182-L189) e
[`managed.ts:640`](../../../alternative-positronic/packages/positronic-mcp-docker/src/managed.ts#L640));
leitura da árvore de processo (`docker top`) dos 17 containers MCP vivos; e
**medição em runtime** dos seis MCPs × dois gestores × dois modos (EOF e
SIGTERM) = 24 medições, com o instrumento novo
`scripts/percival-mcp-runtime-contract.py`. O mecanismo do achado 1 foi
confirmado por **caso mínimo controlado** (script com e sem `trap`, com e
sem `--init`), medindo `SigCgt` de PID 1 e o tempo e código de saída do
`docker stop`.

Achados: (1) **o broker do Percival não passa `--init`** e 4 das 6 imagens
não têm init embutido — sem init, PID 1 não trata SIGTERM, o `docker stop`
paga o grace period inteiro (10,2 s) e sai **137**, contra 0,1 s e 143 com
`--init`; o `SigCgt=0` do init é correto (o init encaminha o sinal), e o bit
14 de `SigCgt` é o que distingue "SIGTERM tratado"; (2) **init duplicado**
no consumidor Positronic (`docker-init` sobre o tini de OSM/Deep Research),
medido em 4 das 24 medições; (3) **`NoNewPrivs=0`** sob o Positronic contra
`1` sob o Percival — divergência de política entre gestores, não defeito do
core; (4) o AgentMail **não serviu** no ambiente isolado por fazer health
check do upstream no startup — precondição de startup, não violação do
contrato, e o Deep Research deixou de servir pelo mesmo motivo até receber
`OPENAI_API_KEY`.

Artefatos gravados: `scripts/percival-mcp-runtime-contract.py` (novo, no
core) e a §2.7 deste plano. A evidência bruta por imagem (JSON) é
reproduzível pelo próprio script com `--output`; fica **fora** da fonte
rastreada, conforme `.agent/workflow.md`.

**Estado:** **D7 — execução concluída, item aberto.** Restam dois defeitos
de código (o `--init` do broker, no core; o init duplicado, no consumidor
Positronic) e os testes de contrato de imagem de Notes, Khan e AgentMail.
As correções são de escrita em repositórios distintos e **não** foram
executadas: exigem autorização do operador. D6, D8–D12 inalterados.

**Ressalva:** esta execução da D7 **não está commitada nem enviada** — a
autorização de commit/push do operador cobria a D4 e a D5. No working tree
do core restam a §2.7 (modificada) e
`scripts/percival-mcp-runtime-contract.py` (novo, não rastreado). A
validação documental executada nesta rodada: links/âncoras/CJK/tabelas
consistentes, `git diff --check` limpo e `ruff check` limpo no script novo
(o `ruff format` não é aplicado neste repositório, por decisão registrada
em `AGENTS.md`).

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

**2026-10-23 — D2 fechado (decisões do operador; registro do agente).**
- **Decisões:** D2-a (atribuição confirmada), D2-b Opção A, D2-c Opção A,
  D2-d Opção A.
- **Atribuição (D2-a):** verificada pela API do GitHub, que resolve o autor de
  cada commit para a conta que o assinou — `bill.kopp.dev@gmail.com` →
  `bill-kopp-ai-dev`, `whats.up.ai.chat@gmail.com` → `bill-kopp` (conta pessoal
  do operador, confirmada pelo fork `bill-kopp/nanobot-webui`). Os endereços
  placeholder eram a identidade local do próprio repositório e foram enviados
  pela conta do operador. `bill.kopp@gmail.com` não existe em nenhum
  histórico; `willkopp@gmail.com` foi removido pelo operador e também não
  existe — aparece apenas como destinatário em journals do Positronic.
- **`.mailmap` (D2-c):** commitado nos sete repositórios (`nanobot` `7d2312a6`,
  `percival-notes-mcp` `78c2810`, `percival-agentmail-mcp` `54461f4`,
  `percival-weather-mcp` `b5dd4eb`, `percival-khan-calendar` `ce69267`,
  `percival-osm` `55aa673`, `percival-deep-research` `44ae8a1`). Um mapeamento
  por email colapsa 3–5 grafias em `Bill Kopp <bill.kopp.dev@gmail.com>` por
  repositório. Identidades de automação e contribuições externas ficam sem
  mapeamento (D2-b). Nenhum objeto commit reescrito; SHAs de `origin/main`
  intactos.
- **Rebuild (D2-d):** `python3 scripts/percival-docker-build.py notes-mcp
  agentmail-mcp weather-mcp khan-calendar osm deep-research` a partir do HEAD
  limpo de cada repo. Resultado: seis imagens `linux/amd64` com SHA completo de
  40 caracteres no label `revision`, sem `io.percival.build.worktree`. Smoke
  stdio JSON-RPC **6/6** (`initialize` + `tools/list`): Notes 12, AgentMail 24,
  Weather 9, Khan 12, OSM 37, Deep Research 5 tools.
- **Defeito corrigido no caminho:** o `.mailmap` do Deep Research entrou na
  imagem em `/app/.mailmap` (`COPY . .` sem exclusão no `.dockerignore`).
  Corrigido em `e076f29`, com rebuild e verificação de ausência na imagem.
- **Artefato de evidência:** §2.2 deste plano e §7 do
  [relatório de proveniência](../reports/2026-10-10-f7-provenance-and-identity.md).
- **Mutações:** `.mailmap` e `.dockerignore` commitados nos repos MCP; imagens
  construídas localmente. Sem promoção, sem alteração de instância ou de pin de
  runtime. Push para `origin/main` executado depois, com autorização explícita do
  operador (registrado abaixo).
- **Limitações:** promoção das imagens novas depende de D8 (aprovação, canário e
  rollback independentes); os pins de runtime seguem nos IDs antigos. Política de
  assinatura de commits continua aberta e independente.
- **Estado:** **D2 fechado.** D3–D12 inalterados; o encerramento consolidado
  continua bloqueado por D3–D10 e pelos gates externos C1–C4 e A1–A9.

**2026-10-23 — push de D1/D2 para `origin/main` nos sete repositórios
(autorização explícita do operador).**
- **Commits enviados:** `nanobot` `5b38c3b1..1fc7903d` (três commits: D1,
  `.mailmap`, D2), `percival-notes-mcp` `78c2810`,
  `percival-agentmail-mcp` `54461f4`, `percival-weather-mcp` `b5dd4eb`,
  `percival-khan-calendar` `ce69267`, `percival-osm` `55aa673`,
  `percival-deep-research` `e076f29` (dois commits: `.mailmap` e
  `.dockerignore`). Após o push, todos reportam `ahead=0 behind=0`.
- **Nenhum workflow publica imagem em push de `main`:** os seis MCPs só constroem
  candidato local (`percival-osm:ci`) e publicam sob tag `v*`. O push disparou
  apenas CI de build/test, sem publicação em registry.
- **CI disparado nos seis MCPs:** AgentMail e Khan **verdes**; Notes, Weather e
  OSM **vermelhos**, com as mesmas causas e nos mesmos passos já vermelhos em
  2026-10-10 (antes deste trabalho): Notes "Inspect identity and privilege
  posture", Weather "Resolve image metadata", OSM "Run `uv sync --locked`".
  Deep Research reprovou em "Lint and check formatting". **Nenhuma dessas
  falhas foi introduzida pelos commits do D2** — os passos falhos são os mesmos
  e os repos já estavam vermelhos em `origin/main` antes do push.
- **`nanobot` não gerou run:** o CI do core tem `paths-ignore` para `docs/**`, e
  os três commits enviados só tocam `docs/**` mais `.mailmap` na raiz. Nenhum
  check-run foi registrado para `8e052162`, `7d2312a6` nem `1fc7903d`. O
  gate de conformance do core continua sem evidência nova neste SHA; disparar
  `workflow_dispatch` autenticado é decisão do operador.
- **Ressalva de visibilidade:** a API do GitHub reporta os sete repositórios
  como `private=false` / `visibility=public`, e o fetch anônimo responde HTTP
  200. Isso diverge do pressuposto de "repositório privado de desenvolvimento"
  do [AGENTS.md do projeto](../../AGENTS.md) e da
  [decisão de governança](../percival-governance.md). **Este achado não foi
  tratado aqui**: alterar visibilidade e a política de disclosure é ato do
  operador, fora do escopo do D2, e precisa ser reconciliado antes de I3.4.
- **Estado:** **D2 fechado e enviado.** Sem promoção de imagem, sem mudança de
  pin de runtime, sem tag e sem publicação em registry.

**2026-10-24 — D7 corrigida e fechada (decisão e autorização do operador;
execução e registo do agente).**
- **Decisão do operador:** "siga com a task e realize um push no github" —
  a correção dos dois defeitos de init e a escrita dos testes de contrato de
  imagem foram autorizadas, com commit e push por SSH.
- **Diagnóstico antes da correção:** os dois achados de init **não são dois
  defeitos independentes** — são **um só defeito com duas faces**: a camada de
  init do runtime stdio **não tem dono único**. O levantamento por repositório
  mostrou quatro donos para a mesma responsabilidade (Compose `init:`, tini
  embutido na imagem, `--init` do Positronic, `--init` do broker). O contrato
  de runtime 1 e o runbook já nomeiam o dono correto: **o gestor**. Decisão
  registrada em §2.7.4.1.
- **Medição que sustenta a decisão:** `--init` **funciona mesmo com
  `--cap-drop=ALL`** (PID 1 = `/sbin/docker-init`, `docker stop` em 0,1 s,
  exit **143**), sem necessidade de `--cap-add=KILL`; sem `--init` o mesmo
  container paga o grace period inteiro (10,1 s) e sai **137**. Critério de
  conformidade corrigido: `SigCgt` de PID 1 **não** é critério — o init
  encaminha o sinal, não o trata; o critério é o **comportamento observável**
  (143, não 137).
- **Commits enviados** (todos por SSH, `origin/main`): core `79dda0a0`
  (`fix(mcp-docker): give the broker the init layer it owns`), OSM `7f3cb3e`,
  Deep Research `6bcb752` (`fix(docker): give the launcher the init layer
  this image used to embed`), Notes `36c4016`, Khan `13f8fce`, AgentMail
  `31d6b1c`, Weather `81b3aaa` (`test(docker): gate the image contract on a
  single launcher-owned init`).
- **Conteúdo:** core — `--init` no `_spawn`, verificação pós-spawn
  (`Init is not True` → `BrokerError`) e gate de retomada que rejeita
  containers criados antes do fix; OSM e Deep Research — tini removido do
  Dockerfile, `init: true` no compose, smoke e probe stdio com `--init`;
  Notes, Khan, AgentMail — **teste de contrato de imagem novo**
  (`tests/test_docker_contract.py`), conformance e receitas com `--init`;
  Weather — contrato ampliado no `tests/test_dockerfile.py`, smoke e README
  com `--init`.
- **Verificação local:** core `tests/mcp_docker/` **85 passed**,
  `ruff check` limpo, `basedpyright nanobot/mcp_docker/broker.py` → 0 erros;
  Notes 52 passed; Khan 231 passed; AgentMail 236 passed + 1 skipped
  (integração live); Weather, OSM e Deep Research verdes; `git diff --check`
  limpo nos sete repositórios. `docker compose config --format json` renderiza
  `init: true` nos seis serviços dos seis repositórios.
- **Desvios de lint pré-existentes (não introduzidos aqui):** `ruff format`
  no `scripts/docker_stdio_probe.py` do Deep Research e 99 avisos de
  `ruff check` no OSM — confirmados por `git stash` sobre a árvore sem as
  mudanças deste trabalho.
- **O consumidor Positronic não foi alterado:** com as imagens sem tini
  embutido, o `--init` incondicional dele deixa de duplicar. A divergência de
  `NoNewPrivs=0` sob o Positronic **permanece** e é decisão de política do
  gestor, não defeito de contrato.
- **Mutações:** só código, testes, compose e documentação. Nenhum container de
  produto, imagem construída, registry, instância ou credencial foi mutado;
  nenhuma promoção, nenhuma publicação.
- **Estado:** **D7 fechada.** Resíduos transferidos: a `NoNewPrivs` do
  Positronic (divergência de política), o alinhamento do manual de sinais
  (D9) e a reconstrução/promoção das imagens de OSM e Deep Research (D8).
  D6, D8–D12 inalterados.

**2026-10-24 — Sweep de restos não commitados (pedido do operador) e
retificação do smoke de init do OSM e do Deep Research.**
- **Pedido do operador:** "commite todas as mudanças não commitadas e
  realize um push em main em todos os repositórios, caso ainda não tenha
  sido feito". O sweep apurou que a D7 já estava integralmente enviada
  (`ahead=0` nos doze repositórios) e que os restos eram untracked de
  **outra toolchain** (Positronic), anteriores à D7.
- **Defeito real encontrado no caminho do sweep:** a verificação de init
  dos smokes de imagem do OSM e do Deep Research **herdou a asserção
  anterior à correção** — exigia PID 1 = `/usr/bin/tini` e
  `HostConfig.Init != true`, isto é, o **inverso** do contrato que a
  própria D7 estabeleceu. Além disso, lia o campo errado:
  `docker inspect --format {{.Path}}` reporta o *path do processo*, não
  o init, e por isso permanecia no entrypoint da imagem mesmo com PID 1
  = `docker-init`. No Deep Research o fixture HTTP sequer era lançado
  com `--init`.
- **Medição que fecha o diagnóstico:** com `--init`, `HostConfig.Init`
  é `true` e o PID 1 é `docker-init` (medido com `docker top` e
  `/proc/1/status`); `{{.Path}}` continua a apontar para o entrypoint do
  processo. O critério correto é o **comportamento observável** (143,
  não 137), já estabelecido na §2.7.4.1.
- **Correções enviadas:** OSM `946ce44` e Deep Research `1d4c541`
  (`fix(docker): assert the launcher-owned init the smoke actually
  launches`) — asserção pelo `HostConfig.Init` + nome real do PID 1 lido
  de `/proc/1/status`, `--init` no fixture HTTP do Deep Research, e o
  README do OSM alinhado (a linha de controle dizia `PID 1 = tini`).
- **Verificação:** ambos os smokes **executados contra a imagem
  reconstruída** e verdes (`scripts/docker-smoke-test.sh` no OSM,
  `scripts/docker_smoke_test.sh` no Deep Research).
- **Conteúdo versionado nos restos** (convenção do operador: versionar
  onde há precedente — template Positronic e `percival-khan-calendar`;
  manter ignorado onde há decisão explícita — AgentMail, acquire-knowledge,
  notes, weather, collective-memory, nanobot):
  - SPA `f0d4085` — `scripts/dev-spa.sh`, `src/tests/dev-spa.test.ts` e
    `src/tests/gateway-browser-probe.ts`, já referenciados por
    `package.json:20` e pelo core em `tests/kg/test_transport.py:153`.
  - SPA `6e5fdaf`, OSM `ea42aeb`, Deep Research `6e767df` + `720d8be`,
    Khan `4d3178f`, acquire-knowledge `9235030`, okf-bundle-core
    `0d01045` — `.positronic/{PROJECT.md,project.json,policy.json}` e
    `AGENTS.md`, com os fatos desatualizados corrigidos antes de
    versionar (o PROJECT.md do OSM afirmava `tini` e 74 testes — real
    76; o do SPA afirmava o modelo CM/AK pré-F7, 206 testes, 10 locales
    e o export HTML do grafo; o do Deep Research fixava `61cdf26`/v3.0.0;
    o do acquire-knowledge citava `.gitmodules` e
    `mcp_servers/config.json`, que não existem neste checkout).
  - O `.positronic/memory/` do Deep Research (estado de runtime) ficou
    **fora** do versionamento, com a regra de ignore explícita.
- **Verificação final:** os doze repositórios com remote estão
  `ahead=0` e com árvore limpa. `cevap-unesp` permanece **intocado** por
  decisão do operador (repo sem commit, sem remote, 12 MB de PDFs de
  material-fonte e `state.sqlite`).
- **Mutações:** só código, testes, scripts, `.gitignore` e documentação.
  Nenhuma imagem publicada, nenhuma promoção, nenhum registry tocado.
