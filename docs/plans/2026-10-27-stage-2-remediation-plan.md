# Stage-2 — Remediação do Percival (`nanobot`)

**Data / revisão:** 2026-10-30 / 1.9.
**ID / estado:** S2-NB / em execução; aceite local parcial.
**Checkout executor:** `/home/bill/Projects/nanobot`.
**Responsável:** Bill Kopp é o único owner, trabalhador, decisor e signatário do
Percival, das aplicações MCP relacionadas e da infraestrutura IaC da Positronic
Bean Labs; executor técnico: Positronic.
Contato: `bill.kopp.dev@gmail.com`; site `labs.positronicbean.com` (em desenvolvimento).

## 1. Objetivo, fontes e baseline

Corrigir ou tratar explicitamente todos os achados da **seção 6** do
[relatório Percival](../../../positronic-bean-IaC/docs/reports/2026-10-27-nanobot-iac-readiness-report.md#6-achados-issues-e-inconsistências),
complementado pelas seções 7 e 9. Origem: 12 achados e 12 ações, sendo 1 P0,
3 P1 e 8 P2. Snapshot diagnosticado: `766d33bfeca997e4159f2cf9561782c668f39b60`.
Na emissão deste plano o HEAD é `62d1e4e2`; não se presume que evidência do snapshot
anterior qualifique esse HEAD. Há exclusões documentais locais preexistentes.

[Plano coordenador stage-2](../../../positronic-bean-IaC/docs/plans/2026-10-27-iac-v1-stage-2-remediation-plan.md)
— atualizar S2-NB nas seções 3 e 7 ao finalizar. Referências comuns:
[consolidação](../../../positronic-bean-IaC/docs/reports/2026-10-26-stage-1-consolidated-readiness-report.md)
e [D-01..D-06](../../../positronic-bean-IaC/docs/decisions/2026-10-27-iac-stage-1-scope-and-pilot-decisions.md).

Este plano permanece o tracker local desta campanha. Não retoma deploy/VPS/cutover,
I3/B13 ou gates adiados. Os planos ativos L*/D* seguem localmente excluídos; o
mapeamento disponível no relatório/coordenador foi preservado sem recriar esses
arquivos. Decisão de Bill em 2026-10-29: trackers L*/D* antigos são obsoletos; seguir
somente os planos ativos vigentes. Referências legadas permanecem como proveniência,
não como trackers ativos. As ações técnicas sem encaminhamento permanecem abertas até
terem dependência e resultado rastreáveis; Bill continua owner único, sem exigir novo
owner ou aceite duplicado e sem recriar trackers.

## 2. Preparação obrigatória da execução

- [x] Ler `AGENTS.md`, `.agent/workflow.md`, runtime contract, runbook e handoff;
  reconciliar com bill os trackers L*/D* localmente excluídos. A leitura foi feita;
  Bill decidiu em 2026-10-29 que os trackers antigos são obsoletos e que somente os
  planos ativos vigentes serão usados. Arquivos ausentes não foram restaurados.
- [x] Registrar SHA/worktree e ambiente. Baseline de execução:
  HEAD `8c2ac64b68e8428dd1ed38e4474a7e4c91f26720`, worktree dirty preexistente;
  Python 3.12.14 em `nanobot-stage2-env`; Bill é owner e decisor único, Positronic
  executa o trabalho técnico. O caso 143 foi reproduzido antes da correção; alterações
  de produto/teste foram commitadas em `a51802103a1cfac26e394e469f757fff1072784b`.
- [x] Distinguir IaC **D-01..D-06** de Percival **D01..D12** e usar o mapeamento
  A-001→L06/D08, A-002→L02, A-006→L14/L15/D03 e as dependências das ações abaixo.
- [x] Decisão `R-02` (2026-10-28): registro histórico da receita restrita e da
  proposta `mounts=[]` por default. Em 2026-10-29, Bill supersedeu formalmente
  R-02 quanto ao default de mounts por `R-10`: manter o acesso amplo como default,
  conforme B14/B22/B23–B25; ver seção 8.5. O registro da receita vigente permanece
  histórico. Nenhuma mudança de runtime foi autorizada por essa decisão.
- [x] Decisão `R-03` (2026-10-28): removida a exigência de estimar esforço,
  custo ou prazo.
- [x] Decisão `R-05` (2026-10-28): o tracker F3 canônico será mantido em
  `pblabs-mcp-index`, por imagem publicada; checkouts apontam para ele em vez
  de manter cópias.
- [x] Decisões `R-06` a `R-09` (2026-10-28): metadata MCP usa schema externo
  de `server.json` e extensão operacional `pblabs.app.yaml`, com manifests em
  `pblabs-mcp-index` e sem dependência do Docker MCP Catalog; promoção exige
  VEX por CVE associado ao image ID e assinado pelo owner, herdando CVEs da
  imagem base; operações dependentes usam pin aprovado e janela única datada;
  suporte/limitação de cancelamento e deadlines é registrado por transporte,
  método e deadline, sem obrigação geral de implementar cancelamento.
- [x] `R-11` (2026-10-29): Trivy foi escolhido como scanner padrão e está
  instalado por Bill, que autorizou o agente a executar autonomamente o scan do
  candidato exato; cobrir todas as severidades, atualizar a Vulnerability
  DB e registrar versão, data da DB, SHA e image ID; preferir TAR do candidato
  sem montar Docker socket.
  O scan não aprova VEX, release ou promoção, que seguem os gates de `R-07`.

## 3. Backlog integral e critérios de aceite

O estado por ação após esta execução está na seção 6. Condições externas indicadas
continuam pendentes. Prioridade é a da ação de origem, não uma nova classificação.
Áreas abaixo são as apontadas pelo relatório; caminhos foram conferidos no SHA executor.

| Ação | Achado / P | Trabalho e áreas previstas | Dependência técnica / responsável | Evidência suficiente para verificar |
|---|---|---|---|---|
| A-001 | F-001 / P0 | Corrigir predicado de ownership em `nanobot/mcp_docker/broker.py`, incluindo inspect/mutate/hydrate/recover/start/exclude; vínculo de instância compatível | L06/D08; decidir adoção de containers históricos | Labels owner/managed-by/server-id ausentes ou divergentes recusadas antes de mutar; ID, estado e dados de fixture alheia preservados; fluxo próprio positivo |
| A-002 | F-002 / P1 | Segregar transporte de controle do Engine em `scripts/percival-i2-runtime-smoke.py`/harness e CI; não apenas retirar socket | L02; receita autorizada, IaC D-05 se aplicável | Unix e TCP negados de gateway/MCP; controlador e broker autorizados operam; Engine 27.x continua gate, sem override para esconder falha |
| A-003 | F-003 / P1 | Retirar conteúdo do pedido e argumentos dos logs INFO em loop/progress hook; metadados operacionais e transcript privado separados | Política de opt-in/retencão com bill | Canários sintéticos de pedido e argumentos ausentes de stderr/log operacional; sessão privada suportada permanece íntegra |
| A-004 | F-004 / P2 | Empacotar cliente TUI matching ou declarar TUI externa/origem aprovada em launcher/packaging; impedir download implícito do upstream como produto | B13/D01/D04 históricos | Cliente da revisão compatível, launcher e PTY reais; offline se alegar imagem completa; fallback classic explícito |
| A-005 | F-005 / P2 | Aplicar regra de permissão de config sensível no owner do config, sem mudar todos os writers genéricos | Decisão para arquivos existentes e backups; S2-C01 | Criação e replace com 0600 ou recusa documentada; backup restrito; fixture 0644 não preserva exposição inadvertidamente |
| A-006 | F-006 / P1 | Investigar readiness curta, igualdade de floats, branding WebUI e símbolos indefinidos em `scripts/d11/d9_rehearsal.py`; alinhar comando Ruff/CI | L14/L15/D03; ambiente lock/SDK/toolchains | Suíte, CLI, typecheck, lint e frontend pertinentes verdes no candidato; causas e scope de Ruff explicados; sem mascarar skips/retries; sem `ruff format` |
| A-007 | F-007 / P2 | Manter inventário fonte→imagem→instância, separando saved/observed/connectivity; preparar reconciliação no manager existente | D01/D03; owner e janela próprios para runtime real | Inventário datado e sanitizado; imagem e revisão efetivas identificadas; stopped sob demanda não vira falha por inferência |
| A-008 | F-008 / P2 | Reancorar triagem do Medium no candidato exato, hashes/código/testes e SBOM/scan com Trivy (`R-11`) | Vulnerability DB atualizada; candidato identificado; gate `R-07` | Scan Trivy de todas as severidades ligado a SHA/image ID e DB; decisão por CVE e VEX assinado pelo owner; CVEs herdados da imagem base seguem a postura por herança; sem mudar metadata para ocultar finding ou reaproveitar waiver de outra imagem |
| A-009 | F-009 / P2 | Integrar catálogo, aquisição, policy independente e export no manager/broker existentes; CAS/migração explícita | D07/D08/D09; C01/C02/C03; etapas 2/4/5 IaC | Matriz negativa de origem/digest/policy; export atômico sem segredo; estado canônico único; implementação local pode avançar no índice designado; adoção operacional depende de contratos compatíveis e gates próprios |
| A-010 | F-010 / P2 | Homologar bridge por app, método e deadline; erro/cancelamento/EOF e attach em `broker.py`/client/MCPProvider | D08; Notes, receita isolada; etapa 5 IaC; formato `R-09` | Correlação de respostas, calls concorrentes, EOF/timeout sem attach órfão. Bill decidiu implementar `resources/list/read` e `prompts/list/get` para Notes (recurso estático e prompts anunciados); gate por server ativo e capability descoberta. Streaming, resource templates e cancelamento ficam fora deste escopo salvo requisito separado. |
| A-011 | F-011 / P2 | Especificar restrições do produto e entregar requisito de preflight de writers/instâncias à IaC; produto testa o contrato que controla | Bill é owner único da IaC; implementar bundle/preflight e fixture consumidora | Fixture recusa segundo writer e segunda instância no daemon antes de mutar; mudar nome Compose não é isolamento de instalação |
| A-012 | F-012 / P2 | Definir e ensaiar shutdown/recovery carregado no broker, preservando store/journal e dados | Teste sintético concluído; manter em fixtures até necessidade operacional concreta | Calls ativas têm término/erro limitado documentado; restart reconcilia operação sem duplicação; não confundir idle/crash sintético com recovery real |

### 3.1. Dependências recebidas de outros projetos

Estas subtarefas complementares não alteram as 12 ações de origem.

| ID | Origem / execução aqui | Decisão e critério compartilhados |
|---|---|---|
| S2-NB-X01 | AgentMail A-006/A-008; Research A-005/A-009; Khan A-001/A-002/A-008; OSM A-008 e Weather A-005: implementar perfis explícitos de mounts, init, secrets por arquivo e lifecycle conforme S2-C01 | Default do broker Percival: acesso host amplo R/W, com máscaras/exclusões de superfícies de controle, estado e credenciais conforme B23–B25; sem acesso direto ao socket. Cada app declara e configura seu perfil: `[]` para nenhum bind, mounts estreitos quando necessários; não depender do default para stateless. Aumentar escopo de perfil configurado exige confirmação/auditoria; teste do consumidor |
| S2-NB-X02 | Khan A-005 e gates de qualificação dos MCPs: receber scans/manifests por candidato e coordenar o CI do gateway quando exigido | Evidência por SHA/image ID/manifest digest e DB; CI remoto não fechado por teste local; retorno para cada plano MCP |

O risco de rotação da chave de teste do Deep Research foi explicitamente aceito
em `R-01`; este plano não deve solicitar nem executar essa rotação. A entrega por
arquivo continua sendo requisito de configuração, sem implicar revogação da chave.
Nunca incluir o segredo em evidência ou plano.

## 4. Ordem dos lotes e dependências

1. **Lote NB-1:** A-001, A-003 e A-006; A-002 após receita de ensaio adequada.
   O P0 deve estar comprovadamente fechado antes da integração pelo broker.
2. **Lote NB-2:** A-005 e S2-NB-X01 com revisão mínima de S2-C01; A-004 e A-008
   na qualificação. A-007 prepara inventário sem trocar pins reais.
3. **Lote NB-3:** A-009/A-010 após contratos/ADR; A-011 com a IaC, A-012 após
   retomada de escopo; S2-NB-X02 com candidatos e gate de distribuição.
4. Depois do deploy da imagem Percival, o teste completo será feito diretamente
   pelo agente com prompts de teste para o servidor MCP; definir casos e resultados
   esperados antes da execução. O deploy não ocorreu nesta revisão e não é inferido
   do push de código. `R-03` remove qualquer requisito de dimensionamento prévio.

Alterações em ownership podem impedir adoção de recursos legados: recusar adoção
não comprovada é preferível a remover recurso de outro dono. Dados e rollback são
preservados. Não há requisito de estimar esforço, custo ou prazo (`R-03`).

## 5. Qualificação e condições de conclusão técnica

- [x] Regressões de A-001/A-003/A-006 passaram; smoke repetido no candidato local
  atual. Nenhum teste replica literalmente o predicado de ownership.
  - [x] Gates locais: `pytest` amplo 9.209 passed/49 skipped e CLI serial 160 passed;
  `basedpyright` 0 erros/avisos; `ruff check .` passou. WebUI pertinente: 100 testes
  de `remote-instances`, 87 de `app-layout`, lint e build passaram; `npm ci --ignore-scripts
  --dry-run` passou. Não foi executado `ruff format`. A suíte local Python 3.14.8
  foi executada (detalhes em E3 abaixo). CI remoto foi verificado no SHA
  `9735441c315b12a792476a629df1beeac1893fa8`, run `Test Suite` #64, com Docker,
  Python 3.14, Python 3.12, Arch e MCP broker smoke aprovados; WebUI/TUI foram
  corretamente skipped pelo filtro de paths. Ver E11.
- [x] Build e smoke com fixtures sintéticas; imagens gateway/broker separadas e
  proveniência local registrada. Sem push/publicação.
- [ ] Reconciliar `V-BUILD`, `V-RUN`, `V-CONFIG`, `V-DATA` e limites
  `V-MCP`/`V-FUNC`/`V-REUSE` no plano final; a execução CI posterior no SHA
  `9735441c` passou os jobs aplicáveis de Docker/Python/broker, mas não substitui
  a qualificação integral por V-* nem o aceite de cada app. `V-PILOT` será um teste
  completo do servidor MCP no agente por prompts, após deploy autorizado da imagem.
- [ ] Runtime real só pela interface suportada, após revisão/CAS e backup. Uma
  autorização explícita de Bill pode cobrir a operação e seus pré-requisitos em um
  único registro; push de código não implica deploy/publicação.

Evidências locais podem fechar antes de dependências externas. Uma dependência
permanece aberta até seu resultado ser observado ou Bill decidir explicitamente
diferir/aceitar a limitação; não exige handoff ou aceite de outro owner.

## 6. Penúltima etapa — documentar a execução neste plano

- [x] Atualizar ações/lotes, mapeamento L*/D* disponível, comandos/ambiente, testes,
  SHA inicial/candidato, resultados e limites; evidências sintéticas ficam no scratch
  privado indicado abaixo. A limpeza documental de 85 arquivos foi commitada em
  `c185b51a`; alterações Stage-2 posteriores foram commitadas e enviadas a `main` em
  `51a5d3821bce6082bd448dcd9cd8b9e213cad95b`. Esse push contém código e documentação,
  não imagem publicada, release nem deploy. Referências quebradas no `AGENTS.md` e
  `.positronic/PROJECT.md` foram alinhadas ao tracker vigente.
- [x] Acrescentar à seção 9 do relatório de origem revalidação parcial de E7/A-011,
  E10/A-008 e limites atuais de CI/TUI/manager/piloto; preservar baseline e veredito
  histórico. Os gates que não foram reexecutados continuam explicitamente pendentes.
- [x] Sincronizar o estado S2-NB nas seções 3/7 do plano coordenador IaC, incluindo
  decisões posteriores de Bill, resultado E10 e a evidência E7/A-011 desta iteração.
  As alterações foram commitadas localmente em IaC `79cb3ad`; esse checkout não tem
  remote configurado, portanto não houve push.

| Data / owner | Ações / achados | SHA inicial → final | Mudança e evidências locais | Resultado / V-* / pendências |
|---|---|---|---|---|
| 2026-10-28 / executor local + bill | A-001/A-002/A-003/A-004/A-005/A-006/A-008 verificadas localmente; A-007 parcial por escolha do owner | HEAD inicial `8c2ac64b68e8428dd1ed38e4474a7e4c91f26720`; alterações de produto commitadas em `a51802103a1cfac26e394e469f757fff1072784b`. O candidato F2 foi construído antes do commit, em worktree dirty, com source-diff `3cf4719bf4bdf7b2fd35ae77f7e5aa071bfbc3b8e5ff53563c45d29883577b1a`; não é release/clean-SHA candidate. | Gateway `sha256:301d1a58d6e6e6682c728facc60df47bef72370017e7d7bcec99f1ef898367ac`; broker `sha256:e9343df917b971a6a907670f8029bbff3aabb1ef09d0cf669339802c30636d88`; smoke Engine 27.5.1 completo em `~/.positronic/runtime/tmp/opencode/percival-stage2-8c2ac64/i2-_pclfmoo/results.json`; pytest 9.209 + CLI 160, BasedPyright/Ruff/WebUI/TUI gates verdes | A-007 foi deixada parcial por Bill; A-009–A-012 dependentes/abertas; sem piloto, CI remoto, release, push ou runtime real |
| 2026-10-29 / executor local + bill | E5/S2-NB-X01 parcial; A-004 atualizado; A-012 verificada em fixture | HEAD `c185b51a9df72dca1c52dd4db1c391adfe9a12af` mais worktree modificado; sem candidato limpo. Notes consumido a partir do checkout local HEAD `7101caea83f74ed97f975df22aef2e587978d944`, preservando a exclusão documental preexistente `docs/search-benchmark.md`. | `tests/mcp_docker`: 98 passed; BasedPyright 0 erros; Ruff passou; WebUI MCP 17 passed, lint/build passaram. Bun 1.4.4 oficial: `check`, 255 testes, build, PTY smoke, notices e archive Linux x64 passaram; testes wheel/launcher/package: 49 passed. A-012 DinD Engine 27.5.1: chamada em voo completou; SIGTERM/drain exit 0 em 4,40 s; restart reconciliou mesma instância (ID estável, RestartCount 0). Notes profile DinD: 12 tools registradas, `notes_write`/`notes_read` passaram, mount protegido recusado e vault sintético limpo ao remover DinD. | A-004 continua parcial: proveniência por arquivo/hunk, SHA limpo, B13 e CI remoto abertos. A-007 segue adiada. A-009/A-010/A-011 e outros consumidores X01 continuam dependentes de contrato/índice/ADR. A-012 tem aceite local sintético, não runtime real/piloto. Sem alteração dos containers Percival ativos, publicação ou release. |
| 2026-10-29 / executor local | A-010 implementada e homologada em fixture descartável; C02 aprovado por Bill | HEAD `c185b51a9df72dca1c52dd4db1c391adfe9a12af`; worktree sem commit/candidato limpo. ADR C02 aprovado em conteúdo, ainda sem SHA commitado. Tags locais de smoke e image IDs estão no resultado I2; labels `GIT_SHA` apontam para HEAD-base e não constituem identidade de release. | Broker encaminha `resources/list/read` e `prompts/list/get`, descobre capacidades anunciadas/paginadas, valida IDs de resposta e restringe `read/get` a URI/nome descoberto. MCPProvider mantém allowlist de tools independente, registra extras para managed servers explicitamente configurados, e wrappers revalidam active/running/source. Notes DinD exercitou tool read/write, recurso estático e dois prompts em chamadas concorrentes; cleanup pelo manager. `tests/mcp_docker/test_broker.py`, `test_contract.py` e `tests/tools/test_mcp_tool.py`: 189 passed; Ruff e BasedPyright dos módulos alterados sem erros. | A-010 passou localmente em Engine descartável 27.5.1; streaming, resource templates e cancelamento seguem fora do escopo acordado. Permanecem sem SHA limpo, CI remoto e homologação de release/runtime/piloto. |
| 2026-10-29 / Bill + Positronic | Decisões de ownership, Trivy, índice, C02, A-007/A-012 e teste pós-deploy; build e scan local | `c185b51a9df72dca1c52dd4db1c391adfe9a12af` → `51a5d3821bce6082bd448dcd9cd8b9e213cad95b`; commit foi enviado a `origin/main`. Após isso, `93559579` registrou R-11 localmente; é um commit posterior ainda não enviado. O plano está sendo atualizado neste worktree. | Bill confirmou ser owner único do Percival, servidores MCP e IaC da Positronic Bean Labs; definiu `/home/bill/Projects/pblabs-mcp-index` como local de trabalho do índice; C02 permanece no workspace IaC sem SHA/commit como pré-requisito até migração futura; A-007 após o próximo ciclo; A-012 fica em fixtures salvo necessidade operacional; teste completo do MCP no agente por prompts após deploy. Build limpo do SHA `51a5d382`: gateway ID `sha256:1fef7c37b5a33408fd0fb68693ebf62ca9e7f393506d0e8de895a78cdd2219ed`; broker ID `sha256:c52891eefd78218882b3e7e75dab74e24748a6b3ec25af171cda273894f30c70`. Trivy 0.76.1, DB `UpdatedAt 2026-10-29T13:09:46Z`: 1 MEDIUM no gateway (`CVE-2026-49138`, nanobot-ai 0.1.0, fix 0.2.1), nenhum CVE no broker, nenhum secret/misconfiguration reportado; SBOM CycloneDX 1.7 com 237/46 componentes. | A postura/VEX do MEDIUM, CI do SHA, implementação IaC A-011, perfis por app e teste pós-deploy permanecem abertos. Sem publicação de imagem ou alteração de runtime. |

### 6.2. Evidência desta iteração — 2026-10-29

- **E5 / confirmação de aumento de escopo:** `DockerMcpService.act("configure")`
  agora recusa ampliação de mounts restritos para Full ou rede `none` para `bridge`
  sem `expected_confirmation == server_id`. A WebUI envia o valor digitado. O audit
  registra `scope_change` com enum permitido (`host_mounts_to_full`,
  `network_none_to_bridge` ou ambos), sem guardar paths ou secrets. Teste direto cobre
   ausência/valor errado antes de broker calls, sucesso com confirmação e leitura do
   audit; regressão WebUI exige que a confirmação siga na mutation.
- **E5 / perfil Notes:** imagem construída no DinD isolado a partir do checkout local
  Notes HEAD `7101caea83f74ed97f975df22aef2e587978d944`, sem incluir a exclusão
  documental preexistente no contexto Docker. Image ID local Notes:
  `sha256:ef440f295966b0c6e9fcfff084b64ea05bb9c4a8b3e7000c305e6b41aa578402`.
  Docker Server observado: 27.5.1 no DinD acima. Manager configurado somente no DinD com
  `mounts=["/notes-profile-scratch/notes-vault"]`, `network="none"` e
  `PERCIVAL_NOTES_VAULT_PATH=/host/notes-profile-scratch/notes-vault`. Handshake
  registrou 12 tools; `notes_write`/`notes_read` com conteúdo sintético passaram.
  Tentativa de ampliar mount a `/var/lib/docker` foi recusada e o perfil salvo
  permaneceu estreito. Notes foi excluído pela API do manager, depois DinD e scratch
  foram removidos. Isso testa perfil de consumidor em fixture; não homologa release,
   manager real ou piloto.
- **E6 / extensão aprovada e homologação local:** Bill decidiu implementar
  resources/prompts na bridge Notes e aprovou C02 em 2026-10-29. Broker e MCPProvider
  encaminham `resources/list/read` e `prompts/list/get`, respeitam capabilities
  anunciadas no `initialize`, paginam discovery e verificam correlação de IDs; o
  broker limita `read/get` às URIs/nomes descobertos. Tools mantêm allowlist própria;
  wrappers revalidam active/running/source. Notes foi exercitado via manager no DinD
  Engine 27.5.1: tool read/write, resource estático e dois prompts em chamadas
  concorrentes; o driver validou o mount sintético estreito e excluiu o servidor pelo
  manager. O I2 smoke completo, incluindo ausência de attach órfão após as chamadas,
  passou: `/home/bill/.positronic/runtime/tmp/opencode/i2-wx29as0p/results.json`.
  Última execução inclui novos testes de EOF/timeout com subprocesso simulado e ID
  divergente: 189 testes focados passaram; Ruff e BasedPyright focados passaram.
  Imagens de smoke (não-candidatas) registradas no JSON: gateway
    `sha256:7a33ad1164ee0abd9c2e3a9abcc8b4f190fefb92af1bfba000a80a6c07941002`, broker
   `sha256:11c5a42f360a00760dc4a6fcc2905cce6f134fb6d51ad5b912c84a0793313f0a` e Notes
   `sha256:9680e3866e55133c5ad53db4b5b9ddbd3524649a794dc60b5e04b6def0ee0c71`.
    Foram construídas de worktree dirty com `GIT_SHA` igual ao HEAD-base; IDs/tag provam
    o par usado no ensaio, não a identidade de um candidato.
- **E6 / matriz R-09 de método e deadline:** `initialize`, `tools/list/call`,
  `resources/list/read` e `prompts/list/get` são encaminhados somente se as
  capabilities correspondentes forem anunciadas; `notifications/initialized` recebe
  202. Listagens paginam; `read` exige URI estática descoberta, `get` exige prompt
  descoberto e chamadas de tools continuam sob allowlist/disabled gate. Resposta com
  `id` diferente do request é recusada (HTTP 503). Broker response wait = 18 s; attach
  é encerrado e aguardado até 5 s em timeout/EOF, com cleanup unit-testado. A smoke
  Notes cobriu concorrência; timeout/EOF de attach foram exercitados com subprocesso
  simulado, não por espera real de 18 s em DinD. Streaming, templates de resource e
  cancelamento não são suportados/não reivindicados no escopo atual.
- **E8 / A-012:** o DinD `docker:27.5.1-dind` foi iniciado com digest verificado
  (`sha256:aa3df78ecf320f5fafdce71c659f1629e96e9de0968305fe1de670e0ca9176ce`), acesso restrito a `127.0.0.1`, e scratch sintético
  privado. A fixture `tests/mcp_docker/fixtures/a012/` expõe uma tool `delay` e grava
  marker no path sintético. Broker e gateway foram construídos localmente em imagens
  de teste; não são candidatos de release. O stop do broker enviou SIGTERM enquanto
  a chamada estava comprovadamente em voo; resposta completou em 4,40 s, logs
  registraram drain e exit code foi 0. Após `docker start` e `MCPProvider.connect`,
  a tool voltou a funcionar sem criar outro container. Os containers de teste foram
  removidos através do manager/API e o DinD descartável foi removido.
- **A-004 / Bun:** Bill decidiu atualizar para a release estável mais recente;
  em 2026-10-29 era Bun 1.4.4, release oficial de 2026-10-22, commit
  `38afee6c84fcf48c0edb2466aa4b27d287a59c30`. O asset Linux x64 foi conferido contra
  o digest publicado pelo GitHub (`sha256:bf8ccbfb2b0b80159e0f9a6d15c55317add8077534dbc6130a3edb52fccb395c`). A nota de licença do
  mesmo tag foi comparada byte a byte e tem SHA-256
  `362fe32c954ec829240bd7429c53d705eef08c6bfa45ffc2d02005f857cba4dd`.
  Alterados os pins de CI/release, `@types/bun`, lockfile, `RELINKING.md`, release
  notices, wheel/archive packagers e documentação de release. Artefato gerado só
  localmente; B13, provenance map e CI remoto continuam pendentes.
- **CI remoto — estado em 2026-10-29:** run #52/`40862581288` ainda não tinha sido
  verificado. A consulta sem a configuração padrão do GitHub CLI retornava 404/não
  autenticado; esse registro antecede a autenticação local e a reconciliação feita em
  2026-10-30 abaixo.
- **E10 / A-008 — build limpo e scan Trivy (2026-10-29):** criado worktree detached
  limpo em `/home/bill/.positronic/runtime/tmp/opencode/percival-stage2-20261029-51a5d382`
  no SHA `51a5d3821bce6082bd448dcd9cd8b9e213cad95b`. Builds locais com os Dockerfiles
  versionados produziram `linux/amd64` gateway tag `percival-gateway:0.1.0-51a5d382`,
  Docker image ID `sha256:1fef7c37b5a33408fd0fb68693ebf62ca9e7f393506d0e8de895a78cdd2219ed`,
  e broker `percival-mcp-broker:0.1.0-51a5d382`, ID
  `sha256:c52891eefd78218882b3e7e75dab74e24748a6b3ec25af171cda273894f30c70`.
  Labels OCI `org.opencontainers.image.revision` nos dois apontam ao SHA completo.
  TARs foram salvos no scratch privado e escaneados via `trivy image --input` com
  Trivy 0.76.1; nenhuma imagem foi publicada nem scanner container recebeu Docker
  socket. Vulnerability DB `UpdatedAt=2026-10-29T13:09:46.269823229Z`, baixada
  `2026-10-29T16:53:22.488269009Z`; checks bundle foi atualizado. Scan de todas as
  severidades, misconfiguration, secrets e licenses: gateway tem 1 MEDIUM
  `CVE-2026-49138` no pacote PyPI `nanobot-ai 0.1.0`, Trivy indica versão corrigida
  `0.2.1`; broker sem CVEs. Nenhum secret ou misconfiguration foi reportado; Trivy
  detectou zero arquivos de configuração. O scan não assina postura `not_affected`.
  A imagem gateway foi identificada como Debian `forky/sid`; Trivy emitiu aviso de
  que essa versão não consta na lista EOL. CycloneDX 1.7 SBOMs: gateway 237
  componentes, broker 46. Artefatos: `percival-stage2-20261029-51a5d382-{gateway,broker}-tar-scan.json`,
  `...-{gateway,broker}-tar.cdx.json`, e TARs homônimos sob
  `/home/bill/.positronic/runtime/tmp/opencode/`. SHA256 TAR gateway
  `7024dfd9d1d881b5f30bab5086e7c1d444aa909ec2c19a9cdffb396944e5d6d7`, broker
  `7f0f03be69e688f71429a96ac1e83210e59e21f1568488f184154203a17ddc64`. SBOM SHA256:
  gateway `7dff04fe9c806a74f117b165190122d553a4ad8b0b11922b54a3da5a41dacf4e`, broker
  `e7062a0d078a526d507dc4f9fb3e69376b8fe9538b8668bf9c35a1f7c399a160`. Scan JSON
  SHA256: gateway `c30ced4b3ac42e5ad35d1ed38cebe0addc0f9358d1317ca94d41e91048cf46f0`,
  broker `2f89b2ad43f6f1e189c1aaf804026400bcd833be6ea082d35c5c7fde2d359b9e`.
  Próximo gate: reavaliar o MEDIUM contra código/testes e decidir postura para esses
  image IDs; não reutilizar VEX de candidato anterior.

#### E7 — A-011: preflight e consumidor (2026-10-29)

Bill aprovou o desenho de identidade do Engine mais recursos Docker com nomes
globais determinísticos para claim e exclusão mútua. A IaC contém agora
`scripts/preflight.py` e `docs/preflight.md`; o Percival contém a fixture
`tests/mcp_docker/fixtures/a011/consumer.py`. A claim durável
`pblabs-installation-claim-v1` aceita retries da mesma instalação e recusa outro
ID ou labels divergentes. O recurso temporário
`pblabs-installation-writer-v1` serializa comandos concorrentes no mesmo daemon;
uma interrupção deixa o recurso presente e falha fechada até inspeção explícita.

Verificação: `python -m unittest discover -s tests -p 'test_preflight.py' -v`
passou (1 teste). Em DinD descartável `docker:27.5.1-dind`, a fixture Percival
foi executada simultaneamente duas vezes contra o mesmo Engine: exatamente uma
execução completou (exit 0) e a outra recusou (exit 2); uma instalação com ID
distinto também recusou sem executar o comando e sem alterar os recursos Docker.
O lock temporário foi removido e o daemon descartável encerrado. Isso não altera
o runtime ativo. O bootstrap/bundle canônico ainda não existe neste workspace;
integrar o wrapper quando esse ponto de entrada for implementado. A implementação
IaC foi commitada em `79cb3ad25fc1c8b8125729fdb88ee20770f69b47`; a fixture e o
provenance map Percival em `22b9e33c7aaecfb0e87184e76e2498d0eec9fcec`; a fundação
do índice local em `6a23188ef24d1beebaec7c74f2e94d9dbf6f3748` (sem remoto).

### 6.1. Estado por ação em 2026-10-28

| Ação | Estado nesta execução | Evidência / dependência restante |
|---|---|---|
| A-001 | Verificada localmente | `_inspect()` falha fechado sem owner/managed-by/server-id/UUID; testes negativos e `exclude` preservam fixture sem ownership; smoke exercitou o broker em Engine 27.5.1. Nenhum container real foi alterado. |
| A-002 | Verificada localmente e em CI remoto | Causa do 143: `docker exec` externo não encaminhava stdin ao `python -`, então `wait()` aceitava EOF/exit 0 sem executar probes e o gateway era parado durante startup. `-i` agora é encaminhado nos níveis externo/interno; env Compose é reescrito do estado corrente. Smoke final completo: TCP Engine negado no gateway, broker/controlador operantes; sem endpoint TCP publicado no host. CI do SHA `9735441c` passou no run #64, incluindo smoke MCP com Engine 27.5.1. |
| A-003 | Verificada localmente | Logs INFO só registram metadados; canários de argumentos/conteúdo ausentes; full pytest preserva transcript privado e resultados de tool. Política bill: sem opt-in de conteúdo. |
| A-004 | Aceite local; provenance map gerado; gates de release pendentes | Fallback/download HKUDS removido; wheel candidate Linux x64, build TUI e PTY smoke passaram localmente com Bun 1.4.4. Foi gerado mapa Git file/hunk de 91 arquivos/2.516 hunks para o SHA `51a5d382` em `docs/provenance/tui-lineage-51a5d382.md`. O mapa preserva os autores/commits registrados por Git; não é opinião jurídica. No run #64 a job TUI foi skipped pelo filtro de paths; B13 continua revisão/assinatura de Bill e não houve publicação. |
| A-005 | Verificada localmente | `save_config` força 0600 em toda substituição, inclusive config existente permissiva; backup root/diretórios 0700 e manifest 0600. Fixture validou 0644→0600 e modos de backup; smoke final verificou reparo do config sintético; nenhum arquivo real foi alterado. |
| A-006 | Verificada localmente e em CI remoto | Corrigidos timeout de startup do teste concorrente, igualdade float de TTL, dois títulos de documento rebrandados para `Percival` e lint do D9; CI alinhado para `ruff check .`. Python 3.14/coverage, Python 3.12 compatibilidade e Arch passaram no run #64; WebUI/TUI foram skipped pelo filtro de paths, com gates locais registrados acima. |
| A-007 | Adiada para depois do próximo ciclo | Inventário read-only anterior reportou 14 containers relevantes, todos `running`, mas não reconcilia o manager, handshake ou conectividade. Bill decidiu retomar `list()` após o próximo ciclo de execução do plano; antes da consulta, identificar a instalação e confirmar SHA/image ID em execução. A página pode acionar `recover_pending()`. |
| A-008 | Scan do candidato exato concluído; postura aprovada para o artefato citado | Gateway e broker foram construídos em worktree limpo do SHA `51a5d382` e exportados para TAR. Trivy 0.76.1, DB `UpdatedAt 2026-10-29T13:09:46Z`: 1 MEDIUM `CVE-2026-49138` no gateway (`nanobot-ai 0.1.0`, fix indicado `0.2.1`); broker sem CVEs. Scan também não reportou segredos nem misconfigurations (0 arquivos de configuração detectados). SBOMs CycloneDX 1.7: 237 componentes gateway, 46 broker. Bill aprovou `not_affected / vulnerable_code_not_present` em 2026-10-29 apenas para gateway image ID `sha256:1fef7c37…`; decisão registrada em E12 e artefato OpenVEX owner-approved. Sem promoção ou autorização de release. |
| A-009 | Implementação local integrada; release/install ainda indisponível | Índice local gera snapshot hash-pinado, valida todos os drafts 0.2 e exige hashes/schema para cada release; o manager valida `pblabs.app.yaml`/`server.json`, perfis, variáveis declaradas, digest e revisão. Broker recebe policy independente read-only, só adquire repositório/plataforma permitidos por digest exato; config v1→v2 usa migração explícita, backup/CAS; mounts são mapeados por instalação e `capabilities.lock` é export derivado, atômico e sem secrets/host paths. Os seis perfis e casos de policy/migração/export passaram localmente. Nomes candidatos `io.github.p-bean-labs/*` foram definidos conforme identidade informada por Bill e formato atual do Registry; claim/autenticação não foram verificados, por isso manifestos seguem draft. Índice local sem remoto e `catalog.yaml`/`public/catalog.json` sem entries/digests; nenhum pull/instalação MCP real foi feito. |
| A-010 | Bridge revalidada localmente; pós-deploy pendente | Notes e bridge resources/prompts passaram em DinD e no candidato limpo documentado; na revisão atual, 190 testes `test_broker.py`, `test_contract.py` e `test_mcp_tool.py` passaram no checkout. Run #64/SHA `9735441c` permanece evidência CI histórica; não houve novo CI autenticado. O teste completo do MCP diretamente pelo agente requer deploy autorizado e alvo que Bill confirmará depois. Streaming, resource templates e cancelamento seguem fora do escopo acordado. |
| A-011 | Integração local ao entrypoint canônico concluída; instalação de bundle P0-C ainda não implementada | IaC tem `scripts/preflight.py` e novo `bootstrap/install.sh`, que executa o bundle local sob claim/lock do daemon; teste de integração comprova encaminhamento de argumentos e recusa de outra instalação antes de executar o payload. Fixture Percival permanece em `tests/mcp_docker/fixtures/a011/`. Testes IaC: 2 passed; `bash -n` e `git diff --check` passaram. Não há fetch, validação ou instalação real de bundle nem mutação de daemon real. |
| A-012 | Encerrada nesta fase com aceite fixture-only | DinD isolado validou chamada em voo, SIGTERM/drain e restart/reconcile (§6.2). Bill decidiu manter em fixtures até necessidade operacional concreta; não fazer ensaio real agora. Se surgir necessidade, definir alvo, janela, carga, backup, critério de parada e autorização do owner antes de executar. |

#### E11 — CI remoto do Percival (2026-10-29)

No SHA `9735441c315b12a792476a629df1beeac1893fa8`, GitHub Actions `Test Suite` #64
(https://github.com/bill-kopp-ai-dev/nanobot/actions/runs/40961513538) concluiu com
sucesso. Passaram os jobs Docker (build, Compose/API/auth, SSH, dependências,
manifests e SBOM), Python 3.14 (lint, BasedPyright, cobertura e CLI), Python 3.12
(compatibilidade e CLI), Arch pinado e MCP broker smoke com Engine 27.5.1. O smoke
exerceu topologia gateway+sidecar, operações/guards e token UID/GID 1000, modo 0640;
o log confirmou conexão MCP e 15 capabilities anunciadas pelo servidor fixture. O
driver foi corrigido para enviar `mounts: []` explicitamente ao `configure`, como
exige o contrato. WebUI/TUI foram skipped pelo filtro de paths, não falharam; seus
gates locais anteriores permanecem evidência distinta. A-002 tem CI remoto verificado
e A-010 tem suíte/typecheck remotos. Release e teste pós-deploy permanecem separados.
Nenhuma imagem foi publicada nem runtime alterado.

O smoke final registra ainda gateway/API exit 0 em idle, broker exit 143 sem drain,
stdio EOF exit 0, pair recreation/hydrate e identidade alternativa UID/GID 1001.
Os arquivos de imagem tar e resultados estão fora do checkout em
`/home/bill/.positronic/runtime/tmp/opencode/percival-stage2-8c2ac64/`; não contêm
credenciais reais. O scan usou apenas os tarballs e cache Trivy local, sem montar o
Docker socket no scanner.

## 7. Última etapa — atualizar o plano coordenador

- [x] Reler o [stage-2 geral](../../../positronic-bean-IaC/docs/plans/2026-10-27-iac-v1-stage-2-remediation-plan.md);
  atualizar **S2-NB na seção 3** e acrescentar retorno na **seção 7**, com ações
  verificadas/abertas, SHA/evidências, dependências liberadas e condições externas.
- [x] Informar efeitos sobre M1/etapas 2–5; preservar retornos de outros projetos.
  Sem acesso à IaC: entregar resumo e ficar **aguardando sincronização**. Somente
  declarar concluído quando os aceites e o retorno estiverem atendidos; registrar
  parcial/bloqueado se houver pendências, sem converter transferência em solução.

## 8. Plano de execução para os itens ainda abertos

**Revisão:** 2026-10-30. **Owner único do produto, trabalho e decisões:** Bill Kopp
(`bill.kopp.dev@gmail.com`), Positronic Bean Labs. **Executor técnico:** Positronic.
Este plano detalha a execução
dos resíduos identificados em S2-NB e não substitui este tracker nem o plano
coordenador IaC. O relatório de itens abertos de 2026-10-28 e o guia de ações do
owner são fontes de contexto; decisões posteriores listadas na seção 8.3 deste tracker
prevalecem onde houver divergência. Critérios e evidência precisam ser revalidados
antes de declarar aceite. Para detalhes operacionais de CI, manager, contratos e
preflight da IaC, ver o [guia de ações do owner](2026-10-29-stage-2-owner-actions-guide.md).

### 8.1 Regras de execução e fronteiras

- Fechar decisões/documentos comuns que destravam vários itens; executar em paralelo
  tarefas independentes. Uma decisão de Bill registrada uma vez cobre os projetos e
  artefatos explicitamente incluídos nela; não pedir novo aceite em cada repositório.
  Decisão não prova implementação, e teste local não prova resultado remoto.
- Escopo deste plano: A-007 e resíduos de A-002/A-004/A-008; A-009–A-012;
  S2-NB-X01/X02; reconciliação dos trackers L*/D*; revalidação da seção 9 do
  relatório de origem; atualização do plano coordenador IaC. A-001/A-003/A-005/A-006
  e o aceite local já registrado de A-004/A-008 são preservados, sem repetição
  desnecessária de testes se as fontes/evidências permanecerem aplicáveis.
- O push de código ao `main` em `51a5d382` foi explicitamente solicitado por Bill e
  concluído; ele não publicou imagem/pacote, não criou release e não alterou runtime.
  A decisão de realizar teste completo por prompts no agente após deploy define o
  método do teste, mas não é execução do deploy nesta revisão. Publicação de artefato
  e alterações no runtime continuam fora do escopo executado aqui.
- Bill é owner único do Percival, das aplicações MCP relacionadas e da IaC, e também
  o único trabalhador desses projetos; não existem handoffs ou aprovações de terceiros.
  A-011 tem implementação e evidência técnica local;
  falta acoplá-la ao ponto de entrada canônico do bundle/bootstrap e versionar o trabalho.
  A-012 permanece em fixtures até haver necessidade operacional;
  eventual ensaio real deve ter alvo, janela, carga, backup e critério de parada.

### 8.2 Sequência de trabalho e aceites

| Lote | Itens | Trabalho / critério verificável | Dependências técnicas / responsável único |
|---|---|---|---|
| E0 — Reconciliação | Preparação, L*/D*, estado atual | Relê `AGENTS.md`, workflow, contratos, runbook, handoff e Git; trackers antigos permanecem obsoletos e referências históricas são proveniência, não fonte de execução. Atualiza baseline SHA/worktree e distingue evidência local, externa e histórica. | Bill é owner e decisor único. Acompanhar dependências reais no plano; não criar handoffs ou aceite adicional entre projetos de Bill. |
| E1 — Contratos e ADR | S2-C01, S2-C02, S2-C03; habilita A-009/A-010/X01 | C01/C03 seguem com conteúdo aprovado por Bill no SHA IaC local `bf9c25201453f1f9c89b9a49030def4b2a053599`; cabeçalhos locais alinhados a 0.2-approved, sem declarar adoção. C02 continua aprovado e não exige SHA agora. `/home/bill/Projects/pblabs-mcp-index` está em repo Git local `6a23188`, sem remoto. Tem schemas, seis manifests draft e catálogo vazio. | Vincular contratos aos consumidores e validar schemas/implementação. Índice sem release/digest, remote ou pipeline. Perfis ainda não integrados ao broker nem ao schema 0.1. |
| E2 — A-007 + trackers | A-007, NB-11 | Bill adiou a consulta do manager até depois do próximo ciclo de execução do plano. Após esse ciclo, identificar instalação e confirmar versão/SHA ou image ID em execução; então usar a página autenticada Contêineres MCP, revisar estado salvo/observado/conectividade e registrar recovery de `list()`. | Não abrir/atualizar a página antes desse marco; `list()` pode executar `recover_pending()` e acionar o broker. A localização e o procedimento estão no guia do owner. Não editar config/audit/registry. |
| E3 — A-004 residual + A-002 residual | A-004/B13; A-002/CI | Bun 1.4.4, workflows, lockfile, `@types/bun`, licença e relinking foram alinhados; checks anteriores passaram. O mapa Git file/hunk foi gerado para o SHA `51a5d382` (91 arquivos/2.516 hunks) em `docs/provenance/tui-lineage-51a5d382.md`. O mapa é histórico técnico e não substitui avaliação de copyright/licenças. Build/PTY de candidato limpo e revisão/assinatura B13 continuam pendentes. Reconciliar V-BUILD/V-RUN/V-CONFIG/V-DATA/V-MCP/V-FUNC/V-REUSE. | `gh` e Bun não estavam disponíveis nessa coleta; Python global 3.14 não tinha dependências do projeto e o `.venv` não iniciava. CI remoto, build/PTY TUI no SHA exato e gates Python 3.14 atuais não foram reexecutados então. Run #52 (`40862581288`) não verificado naquela data. Não instalar ferramentas sem autorização. |
| E4 — A-008 + S2-NB-X02 | Gate de segurança/distribuição | Reexportados os image IDs de E10 e confirmados os TARs originais. Trivy 0.76.1 atualizado: gateway 1 MEDIUM, broker 0. O pacote com finding é o próprio Percival `nanobot-ai 0.1.0`; mudar metadado para upstream `0.2.1` falsearia a identidade SemVer. Código candidato já inclui fix upstream `545294c` e redirects manuais/DNS pinning. Draft OpenVEX foi preparado, sem assinatura. | Bill confirmou que revisará e assinará o draft se concordar. Não há ainda assinatura, VEX aprovado ou decisão de promoção. CI remoto continua aberto. Sem alteração de versão/publicação. |
| E5 — Broker e consumidor | S2-NB-X01; A-009 | Fundação canônica local do índice no commit `6a23188`; worktree atualizado com schema 0.2, seis manifests draft, nomes candidatos `io.github.p-bean-labs/*`, matriz de perfis e `catalog.schema.1.0` com hashes do snapshot. `catalog.yaml` permanece vazio. Manager/broker agora consomem snapshot local somente sob hash registrado, validam schema 0.2 e `server.json`, mapeiam mounts/env por consumidor e protegem aquisição por policy independente + digest/plataforma exatos. `tests/test_catalog.py`: 9 passed; manager/broker/rotas: 269 passed; build local do broker e gateway passou. Evidência de contrato em `docs/mcp-manager-contract.md`. | Decisões de Bill: GitHub oficial `p-bean-labs`, Docker Hub `pbeanlabs`; AgentMail usa env `secret` tipado até suporte a arquivo; catálogo local por enquanto; policy independente em arquivo read-only. O índice não tem remoto nem release OCI/digest, portanto o catálogo não oferece instalação real; o arquivo de policy de exemplo é vazio e aquisição fica desabilitada até provisionamento explícito. Namespace Registry permanece candidato até autenticação/claim. Sem mutação de runtime ou pull de MCP. |
| E6 — A-010 bridge | A-010 | Broker/MCPProvider mantêm `resources/list/read` e `prompts/list/get` para Notes, com descoberta paginada condicionada a capabilities, validação de IDs e allowlist de URI/nome descoberto. O código da bridge não foi alterado pelo trabalho de catálogo. | Baseline limpo em `b3e25d73` tinha apenas alterações documentais sobre `9735441c`; suíte focada então passou (189). Na revisão atual, após mudanças adjacentes no broker, `tests/mcp_docker/test_broker.py`, `test_contract.py` e `tests/tools/test_mcp_tool.py`: 190 passed. I2 DinD Engine 27.5.1 existente validou Notes: tools `notes_write`/`notes_read`, resource estático, dois prompts concorrentes, cleanup, restart/hydrate e ausência de attach órfão. Sem deploy ou runtime ativo; validação pós-deploy permanece pendente de alvo e autorização que Bill confirmará depois. Streaming, resource templates e cancelamento seguem fora do escopo. |
| E7 — A-011 preflight | A-011 | Implementados e commitados `scripts/preflight.py`/`docs/preflight.md` na IaC (`79cb3ad`) e fixture consumidora no Percival (`22b9e33`). O wrapper reserva claim durável por daemon e lock temporário de writer durante o comando. | Unidade de teste com Docker fake passou. DinD descartável Docker 27.5.1 real: concorrência exit 0/2, segunda instalação recusada antes do comando sem alterar daemon; lock removido e DinD encerrado. Falta integrar ao bootstrap/bundle canônico. |
| E8 — A-012 shutdown/recovery | A-012 | Ensaio autorizado executado em DinD descartável com broker e fixture MCP sintética: chamada em voo, SIGTERM, drain, restart/reconcile e verificação de uma única instância. Nenhum container/runtime ativo do Percival foi tocado. | Conteúdo C01 aprovado no SHA IaC `bf9c25201453f1f9c89b9a49030def4b2a053599`; evidência local de fixture agora registrada abaixo. Permanece sem homologar runtime real; o timeout máximo de 25 s não foi consumido integralmente no ensaio. |
| E9 — Teste pós-deploy e retorno | V-PILOT, seção 9, coordenador | Matriz de casos foi preparada abaixo: initialize/server identity; tools/list + chamadas seguras em fixture; resources/list/read e prompts/list/get; validação de chamadas concorrentes/correlação; negativas de URI/prompt desconhecidos e recursos inacessíveis; falhas limitadas/sem attach órfão. Registrar resposta sanitizada e SHA/image ID. | Nenhum deploy/publicação ocorreu; aguardar alvo, janela e autorização operacional própria. A-007 também aguarda imagem nova confirmada em execução antes da página `list()`. Não abrir manager nem iniciar deploy por esta preparação. |

**Matriz V-PILOT preparada (executar somente após deploy autorizado):**

| Caso | Prompt/ação no agente | Resultado esperado | Evidência segura |
|---|---|---|---|
| P1 — identidade | Inicializar sessão MCP com o servidor Notes e solicitar lista de tools | `initialize` retorna versão/protocolo esperados; `tools/list` corresponde à allowlist ativa e ao image ID verificado | `serverInfo`, lista/número de tools, SHA/image ID; sem env ou token |
| P2 — tool read/write | Usar prompt para gravar e ler marcador sintético único no vault de teste aprovado | `notes_write` confirma gravação e `notes_read` devolve exatamente o marcador | Resultado redigido com ID sintético e confirmação de cleanup |
| P3 — resources | `resources/list` e `resources/read` para o recurso estático anunciado | Lista contém URI esperada; read devolve conteúdo conhecido da fixture, sem revelar vault real | URI sanitizada, tamanho/hash do fixture e status MCP |
| P4 — prompts | `prompts/list` e `prompts/get` para cada prompt anunciado | Nomes anunciados e payloads correspondem à revisão homologada | Nomes e resultado estrutural, removendo conteúdo sensível |
| P5 — concorrência/correlação | Disparar chamadas independentes de tool/resource/prompt ao mesmo tempo | Cada resposta casa com o request correto; nenhuma resposta cruzada, timeout sem término ou attach órfão | IDs de correlação sintéticos, estados e tempos; sem payload privado |
| P6 — recusas | Solicitar URI e nome de prompt não anunciados e tool desabilitada/não allowlisted | Recusa MCP sanitizada; nenhum acesso ou execução indevida; sessão permanece consistente | Código/forma do erro, prova de não mutação da fixture |
| P7 — falha/indisponibilidade | Forçar input malformado e indisponibilidade apenas se houver fixture isolada aprovada | Erro limitado e legível, sem travar o agente nem deixar processo/attach órfão | Estado antes/depois e cleanup observado; não induzir falha no runtime de produção |

Pré-condições: conta/sessão de teste, Notes de fixture ou vault sintético dedicado,
allowlist/perfil revisados, caso de rollback/cleanup definido e image ID/SHA
confirmados. Não gravar dados reais nem secrets. Cada caso deve ter timestamp,
resultado, log sanitizado e critério pass/fail antes do ensaio.

#### E10 — A-008: rescan com DB atualizada (2026-10-29)

Trivy 0.76.1 atualizou a DB (`UpdatedAt=2026-10-29T13:09:46.269823229Z`,
download às `2026-10-29T17:17:10Z`) e o checks bundle (`sha256:b591e919...`). Os
TARs foram reexportados dos image IDs locais de E10; SHA256 permaneceu idêntico
ao registro original: gateway `7024dfd9d1d881b5f30bab5086e7c1d444aa909ec2c19a9cdffb396944e5d6d7`,
broker `7f0f03be69e688f71429a96ac1e83210e59e21f1568488f184154203a17ddc64`.
Docker inspect confirmou gateway `sha256:1fef7c37b5a33408fd0fb68693ebf62ca9e7f393506d0e8de895a78cdd2219ed`
e broker `sha256:c52891eefd78218882b3e7e75dab74e24748a6b3ec25af171cda273894f30c70`,
ambos com revision OCI `51a5d3821bce6082bd448dcd9cd8b9e213cad95b`.

Rescan em TAR, Trivy vuln/misconfig/secret/license: gateway mantém um MEDIUM
`CVE-2026-49138` em `nanobot-ai 0.1.0` (fixed version reportada `0.2.1`), sem
achados de secret/config; broker sem CVEs e sem achados de secret/config. JSONs
privados em `/home/bill/.positronic/runtime/tmp/opencode/`:
`percival-stage2-20261029-51a5d382-gateway-rescan-20261029.json` e
`...-broker-rescan-20261029.json`. SHA256: gateway `de746a9a26366bea9cafd0f21d02dbcd5f5eff005ff0a9f1d022f9ace085bfd4`,
broker `efd08fd9869e7e5b2b9afd29d7f15d8141008308e25e7d1cf4eb66e3d305559b`.
O Trivy identifica no relatório a imagem lida do TAR como
`sha256:ea640eb3fb163939badaacb9ce9095e4ac4ff927fa3c284be4b327c1d12efde3` /
`sha256:b6c70706cd1a52976fe6df978b75867fafd723c988cafbdf68d440be838c2837`;
esses identificadores de análise são preservados separadamente do Docker image ID,
com vínculo confirmado pelo SHA256 dos TARs reexportados. Nenhuma imagem foi mutada,
publicada ou promovida.

O pedido de atualizar para 0.2.1 foi confrontado com a autoridade de versão:
`nanobot-ai` é o próprio pacote do produto Percival, cuja versão permanece 0.1.0.
Alterar só esse metadado para suprimir a regra do scanner seria incorreto. O código
no candidato já contém o fix upstream `545294c` e valida cada redirect manualmente;
os 18 testes de segurança previamente aprovados pertencem ao mesmo código, que não
mudou entre `51a5d382` e o HEAD documental atual. A suíte não pôde ser reexecutada
nesta máquina: faltam `pytest`/dependências no Python global e o `.venv` local está
inutilizável. Recomendação: draft VEX `not_affected` limitado ao image ID gateway
exato, sujeito à revisão e assinatura de Bill segundo R-07; até isso, promoção fica
bloqueada. Draft OpenVEX unsigned preparado em
`/home/bill/.positronic/runtime/tmp/opencode/percival-stage2-20261029-51a5d382-gateway-openvex-draft.json`;
não foi copiado para release nem assinado.

#### E2 — A-007: evidência read-only de 2026-10-29

O inventário seguro do runbook foi executado com o ambiente `nanobot-stage2-env` e
gravado fora do checkout em
`/home/bill/.positronic/runtime/tmp/opencode/percival-stage2-20261029-inventory.json`.
Ele observou 14 containers relevantes: seis MCPs Percival, seis MCPs Positronic,
gateway e broker; todos reportados como `running`. Identidades e mounts observados
estão no artefato privado. Isso não reconcilia configuração salva, revision/CAS,
recovery de `list()` nem readiness MCP. Bill adiou a consulta autenticada até a
atualização do agente e confirmação da nova imagem em execução; nenhum container ou
estado foi alterado nesta etapa.

#### E3 — A-004: revisão inicial de proveniência e pacote (2026-10-29; antes da decisão Bun 1.4.4)

| Área | Evidência no checkout | Estado / limite |
|---|---|---|
| `tui/src/**`, origem do cliente | A origem do TUI nativo é o commit upstream `ce070c832d3dafbfa67aff86f62659ed35686771` (2026-08-17, Xubin Ren, com coautores). O histórico contém continuação upstream até `99ba062a` (2026-09-30). | Base herdada de HKUDS/nanobot; não classificar o conjunto do código como originalmente escrito pelo Percival. O histórico por commit foi inspecionado; ainda falta mapa de proveniência por arquivo/hunk para transferência/publicação. |
| Alterações Percival identificadas | `722eb962` (2026-10-11) adaptou o login do TUI à senha da instância e removeu segredo local; `d773f8b5` adicionou `tui/src/client/instance-login.ts`. O commit local `a5180210` também alterou integração/empacotamento e o smoke PTY. | Evidência de manutenção e alterações locais, não de autoria de toda a implementação. |
| Pacote e relinking | `tui/package.json` fixa `@opentui/core` em `0.5.11`; `tui/RELINKING.md` declara Bun `1.3.13`, OpenTUI e revisões de origem do runtime. `ci.yml` usa Bun `1.3.13` no job TUI (`1.3.6` no job WebUI). | A decisão pendente é se manter o pin atual ou alterar conjuntamente CI/build local. Bun disponível localmente é `1.4.2`; `check` e testes passaram nessa versão, sem equivaler ao pin CI. |
| Avisos e fonte correspondente | O bundle chama o projeto de `nanobot`, inclui a licença MIT herdada, avisos do Bun/OpenTUI e textos LGPL-2.0/2.1. `SOURCE_OFFER.md` ainda atribui a oferta por três anos à HKUDS e direciona pedidos ao upstream; o arquivo de source inclui `tui/`, `packages/client-events/` e licenças/build scripts. | Antes de distribuição como Percival, o owner deve revisar titularidade/atribuição e substituir ou confirmar a oferta de fonte correspondente e seu responsável. Não foram alterados avisos/licenças nem feita conclusão jurídica nesta revisão. |
| Verificação local | `pytest tests/cli/test_tui_wheels.py tests/cli/test_tui_release_packaging.py tests/cli/test_tui_launcher.py -q`: 49 passed. Bun `1.4.2`: `bun run check` passou; `bun run test`: 255 passed. | Não foi executado `bun run build`, smoke PTY, build de candidato TUI em SHA limpo, Bun `1.3.13`, CI remoto, B13 ou publicação. |
| Python 3.14 / suíte | Em Python `3.14.8`, após `uv sync --all-extras --dev` e instalação das dependências de canais, `pytest -k 'not test_test_mcp_preset_connects_and_reports_tools and not test_test_mcp_preset_inspects_tools_outside_the_enabled_allowlist'`: 9.365 passed, 51 skipped, 2 deselected; `uv pip check` sem conflitos (170 pacotes). O teste de contrato Matrix que falhou antes por `nh3` passou após instalar as dependências de canal. | Os dois testes excluídos exigem `npx`, ausente no host; sem exclusão, falham por precondição ambiental `npx` ausente, não por teste de protocolo. Isso é execução local, não CI remoto. Naquela coleta, o wrapper `gh` era bloqueado pela configuração mise não confiada e não houve verificação independente do Actions; a autenticação foi posteriormente resolvida via `GH_CONFIG_DIR`, com reconciliação em E15. |

#### E4 — A-008: candidato e triagem inicial (2026-10-29)

Foi criado um worktree detached limpo no SHA `d0687402ac2accb29fd645584a700fdc7a9f26f3`
em `/home/bill/.positronic/runtime/tmp/opencode/percival-stage2-20261029-candidate`.
O builder do projeto produziu, em Docker Server `29.9.2`, imagens locais `linux/amd64`:

| Imagem | Image ID local | Resultado Trivy 0.76.1 / CycloneDX 1.7 |
|---|---|---|
| `percival-gateway:0.1.0-d068740` | `sha256:316a670dbac62c2366022bd268710cfde17190064352fbea583402fc81f34867` | 1 MEDIUM (`CVE-2026-49138`), 237 componentes no SBOM |
| `percival-mcp-broker:0.1.0-d068740` | `sha256:879d531ac69b96bdd6ac22aa95c9dcb75e903435428d14c920c433e106fc22ff` | 0 vulnerabilidades, 46 componentes no SBOM |

O Trivy DB foi atualizado em 2026-10-29 (`UpdatedAt 07:17:11 UTC`; próximo update
2026-10-30). Artefatos privados: `percival-stage2-20261029-d068740-{gateway,broker}-vuln.json`
e `percival-stage2-20261029-d068740-{gateway,broker}.cdx.json` sob
`/home/bill/.positronic/runtime/tmp/opencode/`; os comandos usaram scan offline após
o download da DB. O ID do gateway é novo e não herda automaticamente o VEX do candidato
anterior.

O finding é MEDIUM em `nanobot-ai 0.1.0`, com versão corrigida indicada `0.2.1`. O registro
[NVD consultado em 2026-10-29](https://nvd.nist.gov/vuln/detail/CVE-2026-49138) informa
faixa afetada `<0.2.1`, status `Deferred`, e referencia
o [fix upstream `545294c`](https://github.com/HKUDS/nanobot/commit/545294c62c0947da40eb5b65288aaf02b5fdf632)
e o [release 0.2.1](https://github.com/HKUDS/nanobot/releases/tag/v0.2.1). Esse commit é
ancestral do SHA candidato. No código presente, `web_fetch` desativa redirects automáticos,
valida cada destino antes da requisição e usa transporte DNS pinado; `pytest
tests/tools/test_web_fetch_security.py -q` passou (18 testes), incluindo a regressão que
confirma que o destino privado não é requisitado. A evidência sustenta reavaliar o finding
contra a implementação efetiva, mas o metadata de versão continua abaixo do range de fix e
não autoriza autoatribuir `not_affected`. Bill deve assinar a postura/VEX deste image ID, ou
escolher correção/mitigação/bloqueio conforme R-07. Não houve promoção, smoke do
candidato no Engine gate ou alteração de versão. O CI remoto foi iniciado (run
`40862581288`), mas o resultado reportado como falho ainda não tinha sido confirmado nos logs
do Actions.

#### Reconciliação do guia do owner — evidência de 2026-10-29

- **CI — histórico:** Bill iniciou `Test Suite` em `main`; run `40862581288` (#52) apareceu
  `Queued` na captura com SHA abreviado `fead9`. Bill reportou que a execução falhou,
  mas a evidência encaminhada não é a página do Actions nem mostra resultado final,
  SHA completo, jobs, logs ou artifacts. Manter o gate aberto até reconciliar esses
  dados; não inferir causa nem resultado a partir do diff do commit.
- **Manager / A-007:** a página suportada é Contêineres MCP na WebUI (`#/mcp-containers`,
  instalação Compose local padrão `http://127.0.0.1:18790/#/mcp-containers`). Bill adiou
  a consulta até as atualizações do agente estarem concluídas e a nova imagem estar
  rodando no alvo. Não abrir/atualizar a página antes de verificar essa condição,
  porque `list()` executa ao carregar e periodicamente e pode fazer recovery. A
  autorização anterior não é instrução para consultar agora.
- **C01/C03:** Bill aprovou o conteúdo em 2026-10-29, imutavelmente identificado pelo
  commit local IaC `bf9c25201453f1f9c89b9a49030def4b2a053599`. A revisão de conteúdo
  está concluída; vincular o SHA aos consumidores, provar schemas/adoção e obter
  evidência de implementação continuam pendentes. O formato `server.json` +
  `pblabs.app.yaml` e as decisões R-06/R-09/R-10 não devem ser reabertos.
- **A-011:** Bill já é o responsável pela IaC; não requer novo handoff. Ainda faltam a
  implementação executável do preflight na IaC e a fixture/teste de contrato no
  Percival; validar somente em ambiente descartável e registrar ambos os SHAs.
- **Índice e ADR — estado histórico, atualizado por decisão posterior:** C02 permanece
  em IaC `docs/decisions/` e não precisa de SHA de commit antes da futura migração dos
  projetos pessoais para GitHub da Positronic Bean Labs. Bill definiu o diretório de
  trabalho do índice como `/home/bill/Projects/pblabs-mcp-index`; trabalho local pode
  começar sem GitHub, e o repositório remoto será criado posteriormente.

#### E12 — revisão do VEX, extensão 0.2 e build TUI local (2026-10-29)

- **VEX / A-008:** JSON do draft OpenVEX em
  `/home/bill/.positronic/runtime/tmp/opencode/percival-stage2-20261029-51a5d382-gateway-openvex-draft.json`
  parseia. O fix `545294c` é ancestral do SHA/imagem exatos; `web_fetch` desativa
  redirects automáticos, valida cada destino antes da requisição e usa transporte
  DNS pinado. Os arquivos de implementação e regressão consultados não diferem entre
  o candidato `51a5d382` e o HEAD local `9735441c`. Isso sustenta tecnicamente a
  proposta `not_affected / vulnerable_code_not_present` apenas para o image ID
  `sha256:1fef7c37...`; os 18 testes focalizados são evidência histórica e não foram
  reexecutados nesta rodada (Python local sem `pytest`). Recomendação Positronic:
  Bill aprovou a disposição em 2026-10-29 para o image ID citado; decisão registrada
  no artefato owner-approved em
  `/home/bill/.positronic/runtime/tmp/opencode/percival-stage2-20261029-51a5d382-gateway-openvex-owner-approved.json`.
  O arquivo registra aprovação de owner, não assinatura criptográfica; não é waiver
  para outro artefato, aprovação de release ou promoção.
- **Extensão PBLabs 0.2 / A-009-X01:** os seis testes foram reexecutados no ambiente
  isolado; `python -m pytest -q` passou (6), `catalog.py --check` passou com catálogo
  vazio e os seis YAMLs parsearam. Revisão técnica recomenda aprovar o contrato de
  metadata proposto, mantendo explícitos os gates: verificar namespace/formato de
  `mcp_name` antes de qualquer status approved e implementar/testar enforcement e
  mapping no manager/broker. Bill aprovou o contrato em 2026-10-29; adoção pelo
  consumidor permanece pendente.
- **TUI / A-004:** Bun `1.4.4` (`38afee6c8`) instalado em `~/.bun/bin` pelo instalador
  oficial; `bun install --frozen-lockfile` não alterou lockfile; `bun run check`,
  `bun run test` (255), `bun run build` (Linux x64) e PTY smoke do binário passaram.
  SHA256 do executável local: `3db8dc6dc1ca528b223f6f8feb8e1013ca8ed017950360d64a4ba3806d282821`.
  `tui/` não difere do candidato `51a5d382`; build local não é release nem publicação.
- **CI remoto — estado naquela coleta:** a CLI não encontrou sessão autenticada no
  diretório de configuração herdado pelo ambiente e o run #52 ainda não havia sido
  reconciliado. A autenticação e consulta posterior estão registradas em E15.
- **A-007 / V-PILOT:** continuam adiados. Nenhuma página do manager foi aberta; nenhum
  `list()`/recovery, deploy, promoção ou mutação de runtime ocorreu. Retomada exige
  confirmar a nova imagem em execução e autorização operacional específica.

#### E13 — reconciliação do tracker com o código (2026-10-30)

Revisão do checkout em `main`, HEAD
`9735441c315b12a792476a629df1beeac1893fa8`. As alegações de implementação abaixo
foram confrontadas com código e testes versionados nesse SHA; isso confirma presença
do comportamento e de cobertura, não substitui execução dos testes nesta revisão.

| Item | Evidência no código | Reconciliação / limite |
|---|---|---|
| A-001 ownership | `nanobot/mcp_docker/broker.py::_inspect` valida `percival.mcp-docker.owner`, `managed-by`, `server-id` e identidade da instância antes de aceitar container; `tests/mcp_docker/test_broker.py::test_exclude_preserves_historical_container_without_complete_ownership` cobre recusa sem ownership completo. | Sustenta o fechamento local descrito na seção 6.1; não prova mutação segura de containers reais nem adoção de containers históricos. |
| A-002 transporte | `nanobot/mcp_docker/broker.py::_exchange_with_handshake` usa attach stdio sem socket de Engine no gateway; `.github/workflows/ci.yml` define o job `mcp-broker` e executa o smoke. | O comportamento implementado é consistente com a evidência CI E11. Resultado remoto continua atribuído ao run #64/SHA registrado em E11; não foi consultado novamente nesta revisão. |
| A-009/X01 e R-10 | `nanobot/mcp_docker/service.py` exige `mounts` explícito em `configure` (linhas 514–522), trata `None` como Full, e exige confirmação tipada ao ampliar mounts/rede (529–538), registrando enum `scope_change` no audit (412–456). `tests/mcp_docker/test_contract.py` cobre ausência, confirmação e audit. | Confirma o default amplo e que redução configurada não é ampliada silenciosamente. Não demonstra adoção por cada consumidor, nem muda configurações existentes/runtime. |
| A-010 bridge | `nanobot/mcp_docker/broker.py::_discover` descobre capabilities anunciadas e a bridge implementa discovery de resources/prompts; `tests/mcp_docker/test_broker.py` cobre paginação e registro. | Consistente com aceite sintético local; não equivale a homologação pós-deploy ou suporte a streaming/templates/cancelamento. |
| CI registrado | `.github/workflows/ci.yml` contém jobs de Python, Docker e `mcp-broker`, com Ruff `check`; a evidência de resultado do Actions foi posteriormente atualizada em E15. | Na revisão E13, #64 passou e TUI/WebUI foram skipped; naquele momento #52 continuava sem reconciliação. E15 registra a reconciliação de #52 e os runs posteriores #65/#67 que passaram TUI/WebUI. |

`git diff --check` passou. Não foi possível executar pytest nesta revisão porque o
Python selecionado não tem o módulo `pytest`; portanto, nenhuma suíte é reivindicada
como reexecutada. A inspeção foi documental e read-only em relação ao runtime.

#### E14 — A-009/X01 e revalidação local A-010 (2026-10-30)

Trabalho começou nos checkouts `/home/bill/Projects/nanobot` (HEAD-base `b3e25d73`)
e `/home/bill/Projects/pblabs-mcp-index` (HEAD-base `6a23188`, sem remote). Bill
autorizou commits locais separados após a verificação; não houve push.

- Bill confirmou a identidade oficial GitHub `p-bean-labs`, Docker Hub `pbeanlabs`,
  a continuidade local do índice, policy independente em arquivo read-only, uso do
  campo `secret` tipado para AgentMail até suporte a arquivo, e confirmação futura
  do alvo pós-deploy. MCP Registry documenta `io.github.orgname/*`; os seis manifests
  agora levam nomes candidatos `io.github.p-bean-labs/*`, mas a autenticação/claim
  não foi testada e o estado continua draft.
- O índice gera snapshot `catalog.schema.1.0`, com hash do catálogo, schemas e cada
  input; `--check` valida os seis perfis 0.2, restrições e nomes candidatos. A matriz
  confirma mounts `/app/reports`, `/data`, `/vault` e `[]` para os consumidores
  stateless/ephemeral; network/secrets são verificados por consumidor. Tests do índice:
  9 passed; `catalog.py --check`: catálogo válido com 0 entries.
- Percival implementa loader local read-only pinado por SHA, validação dos schemas
  PBLabs 0.2 e MCP `server.json`, inputs `environmentVariables` sem valores embutidos,
  mapeamento de mounts por instalação, consentimento local, aquisição broker por
  digest/plataforma sob policy independente, migração explícita schema 1→2 sob
  CAS/backup, rollback condicionado ao snapshot, e export atômico/redigido validado
  por `capabilities.schema.1.0.json`. O checker Compose exige read-only no índice e
  policy. O catálogo continua vazio, logo não houve aquisição OCI real.
- Suite focada Percival/manager/broker/rotas/Compose: 269 passed; A-010 bridge
  `test_broker.py`, `test_contract.py`, `test_mcp_tool.py`: 190 passed na árvore
  atual. Ruff passou; BasedPyright focado nos arquivos alterados: 0 errors. Recipes
  Compose `core-broker` e `core-catalog`: PASS. WebUI build/lint passaram; full Vitest
  anterior: 2.639 passed no container Node 24; após adicionar o fluxo do catálogo,
  `mcp-containers.test.tsx`: 18 passed. Builds locais gateway e broker passaram; os
  três schemas JSON foram confirmados no pacote gateway. Esses artefatos são validação
  local, não releases.
- Uma execução ampla anterior de pytest teve 8.658 passed, 66 skipped e 3 failures
  por dependências de ambiente ausentes (`nh3` do plugin Matrix e `npx` dos testes de
  MCP Presets); a verificação focada atual passou. BasedPyright global também encontra
  imports opcionais de canais ausentes neste ambiente. Nenhum desses resultados foi
  atribuído aos itens A-009/A-010.
- Limites restantes: não há remote do índice, entries `server.json` aprovadas ou OCI
  digests publicados; namespace Registry/claim ainda não autenticado; policy file não
  provisionado no runtime; CI remoto dos novos commits não foi repetido. Nenhum manager
  real foi consultado, container alterado ou deploy realizado. A-010 pós-deploy aguardará
  o alvo e a autorização operacional de Bill.

#### E15 — X02, A-011 e A-012 (2026-10-30)

- **X02 / GitHub Actions:** Bill forneceu evidência de autenticação em
  `/home/bill/.config/gh`; o ambiente de execução define `XDG_CONFIG_HOME` para outro
  diretório, portanto as consultas foram feitas com `GH_CONFIG_DIR=/home/bill/.config/gh`
  sem expor credenciais. Run #52 é `40862581288` (a referência anterior `4086251288`
  tinha transposição de dígitos), workflow_dispatch no SHA
  `feadab9d9d4f822353edca40a02d7a9a65d29d5d`, conclusão `startup_failure`; GitHub
  informa falha de arquivo/workflow antes de criar jobs, sem logs de job. Runs #53–#63
  tiveram conclusões `failure` em tentativas subsequentes; #64 e o agendado #65
  passaram no SHA `9735441c`. O push do commit de catálogo gerou run #67
  (`41069478879`) no SHA `5e6b2b68`, com todos os jobs aprovados, incluindo Terminal
  UI e WebUI; assim o skip por filtro observado em #64 foi superado em validação
  posterior. Runs #65 e #67 também passaram nos jobs TUI/WebUI. O Actions exibiu avisos
  não bloqueantes de depreciação Node 20 e indisponibilidade/restore de cache; a
  conclusão global foi sucesso. Nenhum workflow foi disparado manualmente nesta revisão.
- **A-011 / bootstrap canônico:** criado `bootstrap/install.sh` executável como
  entrypoint canônico do workspace; recebe ID e bundle local executável, delegando o
  payload ao `scripts/preflight.py` sob claim e lock. Teste IaC com Docker fake confirma
  encaminhamento de argumentos e recusa antes de executar para uma identidade diferente;
  a corrida existente segue coberta. `python -m unittest discover -s tests -p
  'test_preflight.py' -v`: 2 passed; `bash -n bootstrap/install.sh` e `git diff --check`
  passaram. O bootstrap não busca, autentica nem valida bundles, e não instala no host;
  essas funções P0-C não existem neste workspace.
- **A-012:** aceite sintético da seção E8 confirmado; encerrada nesta fase com a decisão
  de Bill de manter fixture-only até necessidade operacional concreta. Não foi feito
  ensaio real. Se necessário futuramente, a execução requer alvo, janela, carga, backup
  e critério de parada definidos antes do ensaio.

### 8.3 Decisões registradas e ações do owner

As decisões e respostas do owner registradas em 2026-10-29 substituem solicitações
anteriores incompatíveis. Permanecem abertas somente as ações técnicas indicadas:

1. **A-004 / TUI — origem decidida em 2026-10-29:** declarar o TUI como componente
   próprio do Percival, com código herdado e modificado que exige proveniência por
   arquivo/hunk e avisos atribuídos. Bill decidiu em 2026-10-29 atualizar o runtime
   para Bun 1.4.4; workflows e materiais de build/licença foram alinhados e passaram
   localmente. O SHA limpo `51a5d382` já existe; faltam mapa de proveniência por
   arquivo/hunk, build/ensaio TUI nesse SHA e revisão B13.
2. **A-007 — decisão atualizada por Bill:** realizar inventário do manager após o
   próximo ciclo de execução do plano. Então identificar a instalação e confirmar
   SHA/image ID em execução antes de abrir a página; registrar estado salvo/observado,
   conectividade e eventual recovery.
3. **A-008/X02 — abordagem decidida em 2026-10-29:** reconstruir e escanear o
   candidato exato, com SBOM e identificadores registrados. Se houver atualização
   corrigida compatível, preferi-la e repetir os gates. Scan do candidato `51a5d382`
   encontrou 1 MEDIUM `CVE-2026-49138` no gateway; avaliar evidência e decidir VEX
   justificado, correção/mitigação ou bloqueio para os image IDs informados em E10.
   VEX e promoção não estão aprovados antecipadamente; findings de outro image ID
   não se transferem. A assinatura do owner segue R-07.
4. **A-009/A-010 — decisão registrada em 2026-10-29:** usar Notes como app de
   referência para catálogo/consumidor e homologação da bridge. A escolha não
   substitui a aprovação de receita isolada nem a evidência de teste exigida.
5. **A-012 — decisão atualizada por Bill em 2026-10-29:** manter validação em
   fixtures até haver necessidade operacional concreta. O ensaio I8 isolado e
   descartável em daemon DinD exclusivo, com um broker e uma fixture MCP, chamada em
   voo, shutdown/restart e verificação de término/erro, reconciliação e ausência de
   duplicação foi executado e registrado em E8; Bill aprovou limite de drain de 25 s
   e 30 s de stop grace no Compose. Para eventual runtime real, delimitar alvo,
   janela, carga, backup e critério de parada antes do ensaio.
6. **E0 / trackers — decisão registrada em 2026-10-29:** declarar obsoletos os
   trackers L*/D* antigos e seguir somente os planos ativos vigentes. Não restaurar
   nem usar os trackers antigos como fontes de execução. Essa decisão não encerra
   automaticamente ações sem destino ou owner claro; elas permanecem abertas neste
   plano até encaminhamento rastreável.
7. **V-PILOT/publicação — decisão de método:** após deploy da imagem Percival,
   Bill quer executar teste completo do servidor MCP diretamente no agente por
   prompts de teste. Definir casos, resultados esperados e evidência antes desse
   teste. O push de código `51a5d382` não é deploy nem publicação de imagem; nenhuma
   publicação ocorreu nesta revisão.
8. **Mounts — decisão `R-10`, 2026-10-29:** Bill determinou manter o acesso amplo
   como default do broker Percival, supersedendo R-02 quanto ao default `[]`. Perfis
   explícitos `[]` (nenhum bind) e mounts estreitos continuam disponíveis; qualquer
    aumento de escopo a partir de um perfil mais restrito requer confirmação e
    auditoria. Nenhuma alteração de runtime foi autorizada.
9. **TUI / Bun — decisão de 2026-10-29:** atualizar para a última versão estável
   disponível, Bun 1.4.4; alinhar workflow CI/release, lockfile, relinking e notices.
   A decisão foi implementada e verificada localmente, sem autorização para publicar.
10. **C02 — decisão atualizada por Bill:** manter o ADR em IaC `docs/decisions/`;
    o workspace IaC não terá repositório GitHub até a migração posterior dos
    projetos pessoais para a Positronic Bean Labs. O ADR segue no workspace local,
    sem SHA de commit como pré-requisito de execução. A aprovação C02 não adota
    C01/C03 em deployments. O documento
    `docs/decisions/2026-10-29-iac-c02-percival-executor-transport.md` registra a
    decisão de implementar resources/prompts no Stage-2.
11. **CI privado / GitHub CLI — decisão de acesso:** Bill autorizou instalar o
      `github-cli` oficial e autenticá-lo pelo fluxo local. Em 2026-10-30 a sessão foi
      verificada e usada para inspecionar Actions; como o ambiente Positronic define
      `XDG_CONFIG_HOME` para outro diretório, as consultas apontaram explicitamente
      para `/home/bill/.config/gh` via `GH_CONFIG_DIR`. Nenhuma credencial foi lida ou
      registrada no plano.
12. **A-010 / capabilities Notes — decisão de Bill e resultado local:** implementar
    resources/list, resources/read, prompts/list e prompts/get para Notes; a allowlist
    de tools fica independente e o broker limita read/get ao conjunto anunciado.
    DinD Engine 27.5.1 e matriz local R-09 passaram conforme §6.2; 189 testes focados
    passaram. Resta CI remoto e revalidação da bridge em candidato limpo; static
    resources only. Templates, streaming e cancelamento seguem fora de escopo.

13. **Ownership PBLabs — informado por Bill em 2026-10-29:** Bill Kopp é o único
    owner e responsável pelo Percival, servidores MCP e infraestrutura IaC da
    Positronic Bean Labs; suas decisões são a aprovação final. Empresa: Positronic
    Bean Labs; site `labs.positronicbean.com` em desenvolvimento.
14. **Índice `pblabs-mcp-index` — decisão de Bill:** o owner é Bill e o diretório
    canônico de trabalho é `/home/bill/Projects/pblabs-mcp-index`, mesmo que ainda
    não esteja versionado no GitHub. Criar o projeto GitHub da Positronic Bean Labs
    depois, quando os projetos pessoais forem migrados. A ausência atual de remoto
    não bloqueia trabalho local no catálogo.
15. **A-009/X01 — perfis por app:** Bill confirmou que os perfis de execução dos
    consumidores podem ser definidos/implementados. Os valores concretos de mounts,
    init, secrets e lifecycle devem ser registrados por app conforme seus requisitos;
    esta confirmação não inventa nem amplia um perfil específico.
16. **R-11 / A-008:** Bill informou que instalou Trivy e autorizou usá-lo no scan do
    candidato exato, com SBOM e DB registrados. A decisão autorizava a verificação;
    a decisão posterior de VEX está registrada no item seguinte.
17. **A-008 / VEX:** Bill aprovou em 2026-10-29 a disposição
    `not_affected / vulnerable_code_not_present` para o gateway image ID
    `sha256:1fef7c37...`, limitado ao SHA `51a5d382`; o artefato owner-approved está
    em `/home/bill/.positronic/runtime/tmp/opencode/percival-stage2-20261029-51a5d382-gateway-openvex-owner-approved.json`.
    O artefato documenta aprovação do owner, não contém assinatura criptográfica e
    não autoriza release/promoção nem se aplica a outro image ID.
18. **S2-NB-X01 / perfis:** Bill aprovou a matriz de `docs/profile-proposals.md`
    como baseline de metadata draft dos seis consumidores. Em 2026-10-30 confirmou
    `AGENTMAIL_API_KEY` pelo campo `secret` tipado do manager até existir suporte a
    arquivo. Deep Research persiste somente `/app/reports`; OSM mantém cache ephemeral;
    restantes sources host continuam por instalação. Isso não aprova host paths fixos,
    release/manifests públicos nem mutação de runtime.
19. **Extensão PBLabs 0.2 / A-009-X01:** Bill aprovou o contrato em 2026-10-29 e
    confirmou em 2026-10-30 a identidade GitHub `p-bean-labs` e Docker Hub `pbeanlabs`.
    A sintaxe Registry atual suporta `io.github.orgname/*`, portanto os seis drafts
    usam candidatos `io.github.p-bean-labs/*`. Claim/autenticação não verificados; não
    marcar manifests approved. Schema 0.2, snapshots hash-pinned, integração manager/
    broker, policy/acquisition por digest, migração CAS, profile mapping e export foram
    implementados/testados localmente. A lista não tem remote, server.json/release
    entries ou digest real; nenhum pull/instalação foi autorizado ou executado.

**Pendências técnicas e condições de retomada:** X02 foi reconciliado em E15; run #52
falhou no startup por problema do arquivo de workflow, enquanto run #67 no SHA
`5e6b2b68` passou inclusive TUI/WebUI. A-011 integrou preflight ao entrypoint
`bootstrap/install.sh`; o bundle P0-C completo (aquisição/autenticação/validação) ainda
não existe e não foi instalado. A-012 está encerrada nesta fase em fixture-only pela
decisão de Bill. Permanecem abertas a revisão B13/proveniência do TUI, a homologação de
manager/V-PILOT após deploy autorizado, e os passos de A-009/X01: publicar/migrar o
índice quando autorizado, autenticar o claim Registry, incluir releases/digests reais e
provisionar overlay read-only de índice/policy antes de testar consumidores. C02 não
aguarda SHA de commit: o workspace IaC só será migrado para GitHub posteriormente.
Bill é o owner responsável pelas escolhas finais e pela IaC.

### 8.4 Critério de encerramento

S2-NB pode ser concluído quando cada ação A-001–A-012 e S2-NB-X01/X02 tiver um
resultado objetivo registrado: implementada/verificada com evidência suficiente,
limitação explicitamente aceita por Bill, ou dependência concretamente diferida.
Reutilizar evidência histórica ainda aplicável; revalidar apenas se candidato,
ambiente, código ou risco material mudou. Reconciliar V-* somente para gates que
forem aplicáveis ao resultado/candidato escolhido e atualizar o coordenador com um
resumo/link, sem duplicar os detalhes. V-PILOT continua necessário se o plano incluir
aceite end-to-end pós-deploy; push de código não é deploy nem publicação de imagem.

### 8.5 Decisão `R-10` — default amplo de mounts do broker Percival

**Decidido por Bill em 2026-10-29.** O Percival mantém o acesso amplo R/W ao host
como default de mounts, conforme a diretriz histórica B14 e sua revisão B22/B23–B25.
Esta decisão supersede R-02, de 2026-10-28, **somente quanto ao default restrito
`mounts=[]` e à exigência de tornar o Full uma operação excepcional**. O registro da
receita de execução restrita já vigente não é desfeito.

- Estado default equivale ao comportamento legado: bind da raiz do host com as
  exclusões/máscaras existentes para socket/superfícies de controle, estado e
  credenciais Percival; o gateway/MCP não recebe Docker socket. Isso não é isolamento
  total e preserva o risco indireto aceito em B23–B25.
- `mounts=[]` continua significando nenhum bind; paths explícitos continuam
  suportados e precisam ser estreitos. Apps stateless devem declarar/configurar
  explicitamente `[]`, sem depender do default amplo.
- Aumentar o escopo de um perfil já mais restrito para Full exige confirmação tipada
  e auditoria. Registros legados/existentes devem manter sua configuração efetiva;
  não migrar nem mutar runtime implicitamente.
- O contrato comum deve dizer que cada broker declara seu default; o default amplo é
  específico do broker Percival e não concede privilégios por metadata MCP. Bill define
  os perfis por app, inclusive Notes; não são necessários aceites separados por projeto.
- Atualizar C01, C03 quando descrevem perfis de execução, o plano coordenador e os
  planos consumidores. Preservar o relatório de 2026-10-28 como snapshot histórico e
  acrescentar a decisão posterior como adendo, sem reescrever as evidências coletadas.

R-10 decide a política, mas **não autoriza mudança de código/runtime, piloto,
publicação ou deploy**. A implementação permanece pendente de contrato versionado,
testes de broker/consumidores e autorização operacional específica.

### 8.6 Decisão `R-12` — ownership único e governança proporcional

**Decidido por Bill Kopp em 2026-10-30.** Bill é o único owner, trabalhador,
decisor e signatário do Percival, das aplicações MCP relacionadas e da infraestrutura
IaC da Positronic Bean Labs. Contato: `bill.kopp.dev@gmail.com`; website:
`labs.positronicbean.com` (em desenvolvimento). Positronic executa o trabalho técnico.

- Não há owner externo, transferência entre pessoas, revisão independente obrigatória
  ou aceite de terceiro a obter nesses projetos. Dependências entre repositórios são
  dependências técnicas sob o mesmo owner; registrar o artefato, a condição e o próximo
  passo, sem criar handoff/aceite duplicado.
- Uma decisão/assinatura de Bill registrada com escopo explícito vale para todos os
  artefatos e projetos nela listados. Reutilizá-la enquanto escopo, candidato, alvo e
  risco permanecerem os mesmos; pedir nova decisão somente se um desses elementos
  mudar materialmente ou se a ação tiver consequência operacional distinta.
- Preferir uma verificação suficiente e reutilizável. Repetir testes apenas quando
  código, dependência, ambiente, candidato ou risco relevante mudar, ou quando a
  evidência anterior não cobrir o critério. Não exigir validação cruzada por rotina.
- Essa simplificação remove aprovações redundantes, não critérios técnicos: marcar
  item como verificado exige evidência adequada; itens não executados permanecem
  pendentes ou são explicitamente diferidos/aceitos por Bill.
- R-12 não autoriza automaticamente publicação, deploy, mutação de runtime ou uso de
  dados reais; Bill pode autorizar uma operação concreta em um único registro claro,
  incluindo alvo e limites, sem repetir a mesma autorização em documentos paralelos.
