# Stage-2 — Remediação do Percival (`nanobot`)

**Data / revisão:** 2026-10-29 / 1.6.
**ID / estado:** S2-NB / em execução; aceite local parcial.
**Checkout executor:** `/home/bill/Projects/nanobot`.
**Responsável:** executor técnico local; decisões de produto/operação com bill.

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
não como trackers ativos. A decisão não fecha automaticamente ações sem destino/owner:
mantê-las abertas neste plano até atribuição rastreável, sem recriar trackers.

## 2. Preparação obrigatória da execução

- [x] Ler `AGENTS.md`, `.agent/workflow.md`, runtime contract, runbook e handoff;
  reconciliar com bill os trackers L*/D* localmente excluídos. A leitura foi feita;
  Bill decidiu em 2026-10-29 que os trackers antigos são obsoletos e que somente os
  planos ativos vigentes serão usados. Arquivos ausentes não foram restaurados.
- [x] Registrar SHA/worktree, ambiente e owner técnico. Baseline de execução:
  HEAD `8c2ac64b68e8428dd1ed38e4474a7e4c91f26720`, worktree dirty preexistente;
  Python 3.12.14 em `nanobot-stage2-env`; owner executor técnico local, decisões
  com bill. O caso 143 foi reproduzido antes da correção; alterações de produto/teste
  foram commitadas em `a51802103a1cfac26e394e469f757fff1072784b`.
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
  instalado. O agente pode executá-lo autonomamente quando necessário em
  candidatos locais, cobrindo todas as severidades, atualizando a Vulnerability
  DB e registrando versão, data da DB, SHA e image ID; preferir TAR do candidato
  sem montar Docker socket.
  O scan não aprova VEX, release ou promoção, que seguem os gates de `R-07`.

## 3. Backlog integral e critérios de aceite

O estado por ação após esta execução está na seção 6. Condições externas indicadas
continuam pendentes. Prioridade é a da ação de origem, não uma nova classificação.
Áreas abaixo são as apontadas pelo relatório; caminhos foram conferidos no SHA executor.

| Ação | Achado / P | Trabalho no dono e áreas previstas | Dependência / owner externo | Evidência necessária para verificar |
|---|---|---|---|---|
| A-001 | F-001 / P0 | Corrigir predicado de ownership em `nanobot/mcp_docker/broker.py`, incluindo inspect/mutate/hydrate/recover/start/exclude; vínculo de instância compatível | L06/D08; decidir adoção de containers históricos | Labels owner/managed-by/server-id ausentes ou divergentes recusadas antes de mutar; ID, estado e dados de fixture alheia preservados; fluxo próprio positivo |
| A-002 | F-002 / P1 | Segregar transporte de controle do Engine em `scripts/percival-i2-runtime-smoke.py`/harness e CI; não apenas retirar socket | L02; receita autorizada, IaC D-05 se aplicável | Unix e TCP negados de gateway/MCP; controlador e broker autorizados operam; Engine 27.x continua gate, sem override para esconder falha |
| A-003 | F-003 / P1 | Retirar conteúdo do pedido e argumentos dos logs INFO em loop/progress hook; metadados operacionais e transcript privado separados | Política de opt-in/retencão com bill | Canários sintéticos de pedido e argumentos ausentes de stderr/log operacional; sessão privada suportada permanece íntegra |
| A-004 | F-004 / P2 | Empacotar cliente TUI matching ou declarar TUI externa/origem aprovada em launcher/packaging; impedir download implícito do upstream como produto | B13/D01/D04 históricos | Cliente da revisão compatível, launcher e PTY reais; offline se alegar imagem completa; fallback classic explícito |
| A-005 | F-005 / P2 | Aplicar regra de permissão de config sensível no owner do config, sem mudar todos os writers genéricos | Decisão para arquivos existentes e backups; S2-C01 | Criação e replace com 0600 ou recusa documentada; backup restrito; fixture 0644 não preserva exposição inadvertidamente |
| A-006 | F-006 / P1 | Investigar readiness curta, igualdade de floats, branding WebUI e símbolos indefinidos em `scripts/d11/d9_rehearsal.py`; alinhar comando Ruff/CI | L14/L15/D03; ambiente lock/SDK/toolchains | Suíte, CLI, typecheck, lint e frontend pertinentes verdes no candidato; causas e scope de Ruff explicados; sem mascarar skips/retries; sem `ruff format` |
| A-007 | F-007 / P2 | Manter inventário fonte→imagem→instância, separando saved/observed/connectivity; preparar reconciliação no manager existente | D01/D03; owner e janela próprios para runtime real | Inventário datado e sanitizado; imagem e revisão efetivas identificadas; stopped sob demanda não vira falha por inferência |
| A-008 | F-008 / P2 | Reancorar triagem do Medium no candidato exato, hashes/código/testes e SBOM/scan com Trivy (`R-11`) | Vulnerability DB atualizada; candidato identificado; gate `R-07` | Scan Trivy de todas as severidades ligado a SHA/image ID e DB; decisão por CVE e VEX assinado pelo owner; CVEs herdados da imagem base seguem a postura por herança; sem mudar metadata para ocultar finding ou reaproveitar waiver de outra imagem |
| A-009 | F-009 / P2 | Integrar catálogo, aquisição, policy independente e export no manager/broker existentes; CAS/migração explícita | D07/D08/D09; S2-C01/C02/C03; etapas 2/4/5 IaC | Matriz negativa de origem/digest/policy; export atômico sem segredo; estado canônico único; local-only permanece até contrato aprovado |
| A-010 | F-010 / P2 | Homologar bridge por app, método e deadline; erro/cancelamento/EOF e attach em `broker.py`/client/MCPProvider | D08; Notes, receita isolada; etapa 5 IaC; formato `R-09` | Correlação de respostas, calls concorrentes, EOF/timeout sem attach órfão. Bill decidiu implementar `resources/list/read` e `prompts/list/get` para Notes (recurso estático e prompts anunciados); gate por server ativo e capability descoberta. Streaming, resource templates e cancelamento ficam fora deste escopo salvo requisito separado. |
| A-011 | F-011 / P2 | Especificar restrições do produto e entregar requisito de preflight de writers/instâncias à IaC; produto testa o contrato que controla | Dono IaC implementa bundle/preflight na etapa 3; runtime 1 | Fixture recusa segundo writer e segunda instância no daemon antes de mutar; mudar nome Compose não é isolamento de instalação |
| A-012 | F-012 / P2 | Definir e ensaiar shutdown/recovery carregado no broker, preservando store/journal e dados | Escopo I8 carregado a reautorizar; S2-C01 | Calls ativas têm término/erro limitado documentado; restart reconcilia operação sem duplicação; não confundir idle/crash sintético com recovery real |

### 3.1. Dependências recebidas de outros projetos

Estas subtarefas complementares não alteram as 12 ações de origem.

| ID | Origem / execução aqui | Aceite compartilhado |
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
4. Piloto Percival + Notes só em plano próprio, depois da implementação e
   evidência do perfil de mounts conforme `R-10`/C01, das condições Notes e das autorizações operacionais
   aplicáveis. `R-03` remove qualquer requisito de dimensionamento prévio; este
   documento não cria receita operacional de piloto.

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
  foi executada (detalhes em E3 abaixo); CI remoto ainda não tem resultado verificado
  para o SHA pertinente. O run `Test Suite` #52 foi reportado como falho por Bill,
  mas falta conferir a execução concluída, SHA e job/log.
- [x] Build e smoke com fixtures sintéticas; imagens gateway/broker separadas e
  proveniência local registrada. Sem push/publicação.
- [ ] Reconciliar `V-BUILD`, `V-RUN`, `V-CONFIG`, `V-DATA` e limites
  `V-MCP`/`V-FUNC`/`V-REUSE` no plano final; inventário/aceite de cada app e CI
  remoto ainda não foram revalidados. `V-PILOT` permanece não avaliado.
- [ ] Runtime real só pela interface do owner, após leitura do runbook operacional,
  revisão/CAS, autorização e backup; sem deploy, push ou publicação implícitos.

Aceite local pode ser entregue antes dos externos. Ações transferidas, sem
evidência de seu dono, continuam abertas; remediação integral não está concluída.

## 6. Penúltima etapa — documentar a execução neste plano

- [x] Atualizar ações/lotes, mapeamento L*/D* disponível, comandos/ambiente, testes,
  SHA inicial/candidato, resultados e limites; evidências sintéticas ficam no scratch
  privado indicado abaixo. Alterações de produto e documentação desta revisão
  permanecem no worktree, sem commit/push solicitado. A limpeza documental de 85
  arquivos foi commitada anteriormente em `c185b51a`; referências quebradas no
  `AGENTS.md` e `.positronic/PROJECT.md` foram alinhadas ao tracker vigente nesta revisão.
- [ ] Registrar revalidação à seção 9 do relatório de origem após revisão de bill;
  preservar baseline e veredito histórico. Decisões/pendências e respectivos owners
  já constam no estado por ação desta revisão.

| Data / owner | Ações / achados | SHA inicial → final | Mudança e evidências locais | Resultado / V-* / pendências |
|---|---|---|---|---|
| 2026-10-28 / executor local + bill | A-001/A-002/A-003/A-004/A-005/A-006/A-008 verificadas localmente; A-007 parcial por escolha do owner | HEAD inicial `8c2ac64b68e8428dd1ed38e4474a7e4c91f26720`; alterações de produto commitadas em `a51802103a1cfac26e394e469f757fff1072784b`. O candidato F2 foi construído antes do commit, em worktree dirty, com source-diff `3cf4719bf4bdf7b2fd35ae77f7e5aa071bfbc3b8e5ff53563c45d29883577b1a`; não é release/clean-SHA candidate. | Gateway `sha256:301d1a58d6e6e6682c728facc60df47bef72370017e7d7bcec99f1ef898367ac`; broker `sha256:e9343df917b971a6a907670f8029bbff3aabb1ef09d0cf669339802c30636d88`; smoke Engine 27.5.1 completo em `~/.positronic/runtime/tmp/opencode/percival-stage2-8c2ac64/i2-_pclfmoo/results.json`; pytest 9.209 + CLI 160, BasedPyright/Ruff/WebUI/TUI gates verdes | A-007 foi deixada parcial por Bill; A-009–A-012 dependentes/abertas; sem piloto, CI remoto, release, push ou runtime real |
| 2026-10-29 / executor local + bill | E5/S2-NB-X01 parcial; A-004 atualizado; A-012 verificada em fixture | HEAD `c185b51a9df72dca1c52dd4db1c391adfe9a12af` mais worktree modificado; sem candidato limpo. Notes consumido a partir do checkout local HEAD `7101caea83f74ed97f975df22aef2e587978d944`, preservando a exclusão documental preexistente `docs/search-benchmark.md`. | `tests/mcp_docker`: 98 passed; BasedPyright 0 erros; Ruff passou; WebUI MCP 17 passed, lint/build passaram. Bun 1.4.4 oficial: `check`, 255 testes, build, PTY smoke, notices e archive Linux x64 passaram; testes wheel/launcher/package: 49 passed. A-012 DinD Engine 27.5.1: chamada em voo completou; SIGTERM/drain exit 0 em 4,40 s; restart reconciliou mesma instância (ID estável, RestartCount 0). Notes profile DinD: 12 tools registradas, `notes_write`/`notes_read` passaram, mount protegido recusado e vault sintético limpo ao remover DinD. | A-004 continua parcial: proveniência por arquivo/hunk, SHA limpo, B13 e CI remoto abertos. A-007 segue adiada. A-009/A-010/A-011 e outros consumidores X01 continuam dependentes de contrato/índice/ADR. A-012 tem aceite local sintético, não runtime real/piloto. Sem alteração dos containers Percival ativos, publicação ou release. |
| 2026-10-29 / executor local | A-010 implementada e homologada em fixture descartável; C02 aprovado por Bill | HEAD `c185b51a9df72dca1c52dd4db1c391adfe9a12af`; worktree sem commit/candidato limpo. ADR C02 aprovado em conteúdo, ainda sem SHA commitado. Tags locais de smoke e image IDs estão no resultado I2; labels `GIT_SHA` apontam para HEAD-base e não constituem identidade de release. | Broker encaminha `resources/list/read` e `prompts/list/get`, descobre capacidades anunciadas/paginadas, valida IDs de resposta e restringe `read/get` a URI/nome descoberto. MCPProvider mantém allowlist de tools independente, registra extras para managed servers explicitamente configurados, e wrappers revalidam active/running/source. Notes DinD exercitou tool read/write, recurso estático e dois prompts em chamadas concorrentes; cleanup pelo manager. `tests/mcp_docker/test_broker.py`, `test_contract.py` e `tests/tools/test_mcp_tool.py`: 189 passed; Ruff e BasedPyright dos módulos alterados sem erros. | A-010 passou localmente em Engine descartável 27.5.1; streaming, resource templates e cancelamento seguem fora do escopo acordado. Permanecem sem SHA limpo, CI remoto e homologação de release/runtime/piloto. |

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
- **CI remoto:** run #52/`4086251288` não foi verificado. O endpoint GitHub retorna
  404 para este repositório privado; o `gh` local é wrapper do mise que para diante
  da configuração global não confiada. Não foi alterada nem confiada configuração
  global para contornar isso. A-002 permanece aberta até obter link/logs autenticados,
  SHA completo, resultado por job e artifacts.

### 6.1. Estado por ação em 2026-10-28

| Ação | Estado nesta execução | Evidência / dependência restante |
|---|---|---|
| A-001 | Verificada localmente | `_inspect()` falha fechado sem owner/managed-by/server-id/UUID; testes negativos e `exclude` preservam fixture sem ownership; smoke exercitou o broker em Engine 27.5.1. Nenhum container real foi alterado. |
| A-002 | Verificada localmente | Causa do 143: `docker exec` externo não encaminhava stdin ao `python -`, então `wait()` aceitava EOF/exit 0 sem executar probes e o gateway era parado durante startup. `-i` agora é encaminhado nos níveis externo/interno; env Compose é reescrito do estado corrente. Smoke final completo: TCP Engine negado no gateway, broker/controlador operantes; sem endpoint TCP publicado no host. |
| A-003 | Verificada localmente | Logs INFO só registram metadados; canários de argumentos/conteúdo ausentes; full pytest preserva transcript privado e resultados de tool. Política bill: sem opt-in de conteúdo. |
| A-004 | Verificada localmente — wheel Percival | Fallback/download HKUDS removido; wheel candidate Linux x64 inclui binário matching (source archive verificado contra checkout) e launcher resolve o binário empacotado offline; source distribution exige `NANOBOT_TUI_BIN` explícito ou `--classic`. Wheel local `nanobot_ai-0.1.0-py3-none-manylinux_2_17_x86_64.whl`, SHA256 `ccda285d1213b349f0130814b6acebe28ec9e6b764d9fac57596974351dfd566`, binary PTY smoke passou. Build local usou Bun 1.4.2 (CI pin 1.3.13); sem publicação/B13. |
| A-005 | Verificada localmente | `save_config` força 0600 em toda substituição, inclusive config existente permissiva; backup root/diretórios 0700 e manifest 0600. Fixture validou 0644→0600 e modos de backup; smoke final verificou reparo do config sintético; nenhum arquivo real foi alterado. |
| A-006 | Verificada localmente | Corrigidos timeout de startup do teste concorrente, igualdade float de TTL, dois títulos de documento rebrandados para `Percival` e lint do D9; CI alinhado para `ruff check .`. Gates e detalhes acima; Python local 3.12, não 3.14 nem Actions remoto. |
| A-007 | Parcial — Bill escolheu deixar parcial | Inventário read-only 2026-10-28 reportou 45 imagens/14 containers/21 referências; config salva revision 18/schema 1 e seis MCPs Percival com estado salvo `running`/image ID local correspondendo aos containers `running` e labels próprios. Bill decidiu não prosseguir com `list()` nesta sessão. MCP handshake/conectividade seguem desconhecidos; gateway/broker ativos são revisions anteriores, sem troca de pins. |
| A-008 | Verificada localmente — escopo candidato | Bill aprovou `not affected` apenas para o image ID final `sha256:301d1a58d6e6e6682c728facc60df47bef72370017e7d7bcec99f1ef898367ac`. Trivy 0.76.1/DB 2026-10-28: gateway 1 Medium `CVE-2026-49138` (`nanobot-ai 0.1.0`, scanner sugere 0.2.1), broker 0. NVD descreve SSRF via auto-redirect; código valida redirects manualmente e pinna DNS, fix commit `545294c` é ancestral e 3 testes de redirect privado passaram. Sem aprovação de publicação nem waiver de release. Evidência em `~/.positronic/runtime/tmp/opencode/percival-stage2-8c2ac64/scan-summary.json`. |
| A-009 | Não iniciada | Aguardando contratos/ADR, S2-C01/C02/C03, D07–D09 e etapas 2/4/5; local-only permanece. |
| A-010 | Aceite local sintético; pendente fora do ambiente local | Notes e bridge resources/prompts exercitados em DinD isolado; sem SHA limpo/CI autenticado nem release, runtime ou piloto. Streaming, resource templates e cancelamento fora do escopo aprovado. |
| A-011 | Investigação concluída; implementação pendente | Bill é o owner IaC. A árvore atual não contém preflight ou fixture executáveis; especificar identidade do daemon e coordenação atômica antes de implementar. A prova deve cobrir corrida e nomes Compose distintos no daemon descartável. |
| A-012 | Aceite local sintético; runtime real pendente | DinD isolado validou chamada em voo, SIGTERM/drain e restart/reconcile da instância; ver §6.2. Sem runtime real ou piloto. |

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

**Revisão:** 2026-10-29. **Owner do produto e das decisões:** Bill Kopp
(`bill.kopp.dev@gmail.com`). **Executor técnico:** Positronic, sob autorização
específica para operações externas ou runtime real. Este plano detalha a execução
dos resíduos identificados em S2-NB e não substitui este tracker nem o plano
coordenador IaC. O relatório de itens abertos de 2026-10-28 é uma fonte de contexto;
onde divergir deste estado local, os critérios e a evidência serão revalidados antes
de declarar aceite. Para providências do owner que destravam CI, manager, contratos
e preflight da IaC, ver o [guia de ações do owner](2026-10-29-stage-2-owner-actions-guide.md).

### 8.1 Regras de execução e fronteiras

- Fechar primeiro as decisões/documentos comuns que destravam vários itens; executar
  em paralelo somente tarefas independentes e locais. Não inferir implementação a
  partir de um contrato aprovado, nem aceite remoto a partir de testes locais.
- Escopo deste plano: A-007 e resíduos de A-002/A-004/A-008; A-009–A-012;
  S2-NB-X01/X02; reconciliação dos trackers L*/D*; revalidação da seção 9 do
  relatório de origem; atualização do plano coordenador IaC. A-001/A-003/A-005/A-006
  e o aceite local já registrado de A-004/A-008 são preservados, sem repetição
  desnecessária de testes se as fontes/evidências permanecerem aplicáveis.
- Nenhuma publicação, push, release, criação de repositório remoto, alteração de
  credenciais, mudança de pin em runtime, adoção/remoção de container real ou piloto
  está autorizada por este plano. Cada operação requer autorização específica,
  janela e procedimento do owner; D-05/R-02/R-10 registram a política/receita, não
  autorizam uma execução operacional.
- A-011 é um requisito entregue à IaC, não uma tarefa cujo aceite pertença somente
  ao Percival. A-012 exige ensaio carregado/recovery real apenas após contrato,
  escopo e autorização; fixtures sintéticas não fecham esse aceite.

### 8.2 Sequência de trabalho e aceites

| Lote | Itens | Trabalho / aceite verificável | Dependências e dono |
|---|---|---|---|
| E0 — Reconciliação | Preparação, L*/D*, estado atual | Relê `AGENTS.md`, workflow, contratos, runbook, handoff e Git; a decisão de Bill em 2026-10-29 declara obsoletos os trackers L*/D* antigos e mantém somente os planos ativos vigentes. Referências históricas servem como proveniência, não como fonte de execução; qualquer ação ainda sem destino/owner permanece aberta neste plano até encaminhamento rastreável. Atualiza baseline SHA/worktree e separa evidência local, externa e histórica. | Decisão de obsolescência registrada. Não restaurar trackers; não inferir que itens sem owner/destino foram resolvidos. Mudança futura de owner exige atualização de um plano ativo, sem criar cópia concorrente. |
| E1 — Contratos e ADR | S2-C01, S2-C02, S2-C03; habilita A-009/A-010/X01 | Conteúdo C01/C03 aprovado por Bill em 2026-10-29 conforme commit IaC `bf9c25201453f1f9c89b9a49030def4b2a053599`; vincular esse SHA imutável aos consumidores e verificar schemas/compatibilidade. Bill aprovou em conteúdo o ADR C02 em `docs/decisions/2026-10-29-iac-c02-percival-executor-transport.md`; arquivo alterado localmente, ainda sem SHA imutável. `~/.nanobot` foi verificado e não é Git checkout; Bill decidiu deferir o índice até identificar owner/path de `pblabs-mcp-index`; `~/Projects/pblabs-mcp-index` não existe localmente. Não reabrir R-06/R-09/R-10. | C02 aprovado como decisão, mas SHA ainda indisponível e adoção/deployments não verificados. C01/C03 sem adoção formal. Índice continua diferido por decisão do owner; não criar repo por inferência. |
| E2 — A-007 + trackers | A-007, NB-11 | A consulta do manager foi adiada por Bill em 2026-10-29 até as atualizações do agente Percival estarem concluídas e a instalação alvo estar efetivamente rodando a nova imagem. Antes de retomar, identificar instalação e verificar versão/SHA ou image ID em execução; então usar a página autenticada Contêineres MCP, revisar estado salvo/observado/conectividade e registrar qualquer recovery de `list()`. Recursos históricos sem ownership comprovado ficam recusados/não adotados até decisão explícita. | Não abrir nem atualizar a página ainda: `list()` é chamado automaticamente ao carregar e a cada 30 s, podendo executar `recover_pending()` e acionar o broker. A autorização anterior para a consulta não é instrução para fazê-la agora. Localização e procedimento estão no guia do owner; inventário read-only abaixo não substitui o manager. Não editar config/audit/registry. |
| E3 — A-004 residual + A-002 residual | A-004/B13; A-002/CI | Bill decidiu usar a última release estável, Bun 1.4.4; os dois workflows, lockfile, `@types/bun`, licença e referências de relinking foram alinhados. Checks TUI locais passaram com 1.4.4. Ainda documentar proveniência por arquivo/hunk, executar B13 e empacotar em SHA limpo; concluir CI remoto `main`/Python 3.14 e reconciliar V-BUILD/V-RUN/V-CONFIG/V-DATA/V-MCP/V-FUNC/V-REUSE sem mascarar skips/retries. | O run Actions `Test Suite` #52 (`4086251288`) tem falha reportada por Bill, mas falta resultado concluído, SHA completo, job/log e artifacts; não inferir causa. O endpoint público retorna 404 para este repositório privado e o wrapper local de `gh` bloqueia o uso por configuração mise não confiável. Bun 1.4.4 passou localmente; CI remoto, provenance map, candidato limpo e B13 continuam abertos. |
| E4 — A-008 + S2-NB-X02 | Gate de segurança/distribuição | Decisão de Bill em 2026-10-29: reconstruir e escanear primeiro o candidato exato, registrando SBOM e identificadores; se houver atualização corrigida compatível, preferi-la e repetir os gates; caso contrário, avaliar a vulnerabilidade no candidato e então decidir VEX justificado, correção/mitigação ou bloqueio. Integrar scan/manifest e evidência VEX no gate de CI; não reutilizar o parecer `not_affected` do image ID anterior. | O candidato limpo `d0687402` foi construído e escaneado localmente; há 1 finding MEDIUM no gateway e nenhum finding no broker. O finding está reancorado à fonte/code-fix do SHA atual, mas nenhuma postura/VEX foi assinada para os novos image IDs. Evidência abaixo; decisão R-07, gates remotos e promoção permanecem abertos. Sem push ou promoção implícitos. |
| E5 — Broker e consumidor | S2-NB-X01; A-009 | O broker mantém default host amplo R/W conforme R-10/B23, com máscaras obrigatórias e sem socket direto; perfis explícitos `[]` e binds estreitos seguem disponíveis. Esta revisão adicionou confirmação obrigatória no backend para ampliar mounts a Full ou rede `none`→`bridge`, com audit de enum da mudança, sem persistir paths/secrets. Perfil Notes foi testado com vault sintético, mount estreito explícito e env para `/host/<mount>`; ferramenta de escrita/leitura funcionou e caminho protegido foi recusado. Ainda materializar/testar metadata por app. Depois iniciar A-009: policy independente, catálogo/aquisição sob pin aprovado, CAS/migração e export atômico do único estado canônico. | C01/C03 foram aprovados em conteúdo no SHA IaC `bf9c25201453f1f9c89b9a49030def4b2a053599`; falta vincular SHA, provar schemas/adoção. Bill aprovou C02 em conteúdo; índice `pblabs-mcp-index` foi explicitamente diferido. Os ensaios foram locais em fixtures; sem mutação de runtime ativo. |
| E6 — A-010 bridge | A-010 | Broker/MCPProvider implementam `resources/list/read` e `prompts/list/get` para Notes, com descoberta paginada condicionada a capabilities anunciadas, validação de IDs correlacionados, gate por estado/source e allowlist de URI/nome descoberto. C01/C03 continuam sem adoção; C02 foi aprovado por Bill; índice canônico diferido. | 189 testes focados passaram. I2 DinD Engine 27.5.1 concluído com Notes: tools `notes_write`/`notes_read`, resource estático e dois prompts em chamadas concorrentes; vault sintético estreito, cleanup pelo manager, restart/hydrate e verificação de ausência de attach órfão passaram. EOF/timeout de `_exchange` cobertos em teste subprocesso simulado. Evidência: `/home/bill/.positronic/runtime/tmp/opencode/i2-wx29as0p/results.json`. Streaming, resource templates e cancelamento seguem fora do escopo; sem CI remoto, runtime ativo, piloto ou release. |
| E7 — A-011 preflight | A-011 | Bill já é o owner/responsável pela IaC; não há handoff/nomeação adicional. Implementar no dono IaC o preflight: no mesmo daemon, segunda instalação/writer deve ser recusada antes de mutação; Compose project name não prova isolamento. Implementar fixture/teste consumidor no Percival, integrar ao bundle/preflight da etapa 3 e vincular SHAs/resultados. | Na inspeção de 2026-10-29 não havia preflight executável na IaC nem fixture A-011 específica no Percival; portanto ainda não há comando para rodar. Usar somente fixture descartável/ambiente isolado e provar estado inalterado após recusas. |
| E8 — A-012 shutdown/recovery | A-012 | Ensaio autorizado executado em DinD descartável com broker e fixture MCP sintética: chamada em voo, SIGTERM, drain, restart/reconcile e verificação de uma única instância. Nenhum container/runtime ativo do Percival foi tocado. | Conteúdo C01 aprovado no SHA IaC `bf9c25201453f1f9c89b9a49030def4b2a053599`; evidência local de fixture agora registrada abaixo. Permanece sem homologar runtime real; o timeout máximo de 25 s não foi consumido integralmente no ensaio. |
| E9 — Gate de piloto e retorno | V-PILOT, seção 9, coordenador | Reconciliar V-* no SHA/image ID candidato e por app; resolver dependências de Notes, CI e autorizações operacionais. O índice `pblabs-mcp-index` permanece diferido por decisão de Bill e precisa ser retomado/definido antes de manifests/piloto. Só então redigir plano próprio de piloto Percival + Notes para revisão/autorização separada. Acrescentar revalidação à seção 9 do relatório de origem sem alterar baseline; registrar evidência, owners e pendências no plano local e atualizar S2-NB nas seções 3/7 do coordenador. | Aprovação explícita de Bill para piloto e operações correspondentes; owners dos projetos dependentes; CI e gates da distribuição concluídos. Não iniciar deploy/VPS/cutover ou I3/B13 por inferência. |

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
| Python 3.14 / suíte | Em Python `3.14.8`, após `uv sync --all-extras --dev` e instalação das dependências de canais, `pytest -k 'not test_test_mcp_preset_connects_and_reports_tools and not test_test_mcp_preset_inspects_tools_outside_the_enabled_allowlist'`: 9.365 passed, 51 skipped, 2 deselected; `uv pip check` sem conflitos (170 pacotes). O teste de contrato Matrix que falhou antes por `nh3` passou após instalar as dependências de canal. | Os dois testes excluídos exigem `npx`, ausente no host; sem exclusão, falham por precondição ambiental `npx` ausente, não por teste de protocolo. Isso é execução local, não CI remoto. O wrapper `gh` é bloqueado pela configuração mise não confiada; a página pública da API retorna 404 para o repositório privado. Não houve verificação independente do Actions; o guia do owner registra run #52 iniciado e falha reportada, ainda sem logs/artifacts verificados. |

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
`4086251288`), mas o resultado reportado como falho ainda não foi confirmado nos logs
do Actions.

#### Reconciliação do guia do owner — 2026-10-29

- **CI:** Bill iniciou `Test Suite` em `main`; run `4086251288` (#52) apareceu
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
- **Índice e ADR:** o owner e checkout canônicos de `pblabs-mcp-index` seguem sem
  confirmação inequívoca; confirmar também com a coordenação IaC onde ficará o ADR
  C02. Não criar repositório remoto nem publicar sem autorização própria.

### 8.3 Decisões e ações requeridas de Bill

As decisões abaixo são gates específicos; até serem resolvidas, somente os lotes
independentes e não mutacionais podem avançar:

1. **A-004 / TUI — origem decidida em 2026-10-29:** declarar o TUI como componente
   próprio do Percival, com código herdado e modificado que exige proveniência por
   arquivo/hunk e avisos atribuídos. Bill decidiu em 2026-10-29 atualizar o runtime
   para Bun 1.4.4; workflows e materiais de build/licença foram alinhados e passaram
   localmente. Proveniência, SHA limpo e review B13 continuam pendentes.
2. **A-007 — status atualizado pelo guia de 2026-10-29:** embora tenha havido
   autorização anterior para consultar `list()` e aceitar recovery incidental, Bill
   adiou a execução até as atualizações do agente estarem concluídas e a nova imagem
   estar efetivamente em execução. Essa instrução posterior prevalece: não abrir nem
   atualizar a página Contêineres MCP antes de confirmar o alvo e image ID/SHA em
   execução. Depois, registrar estado salvo/observado, conectividade e recovery; itens
   sem ownership comprovado continuam recusados/não adotados.
3. **A-008/X02 — abordagem decidida em 2026-10-29:** reconstruir e escanear o
   candidato exato, com SBOM e identificadores registrados. Se houver atualização
   corrigida compatível, preferi-la e repetir os gates. Se não houver ou não for
   apropriada, avaliar a vulnerabilidade nesse candidato e então escolher entre VEX
   justificado, correção/mitigação ou bloqueio. A postura final continua pendente
   dos resultados; VEX e promoção não estão aprovados antecipadamente. A herança e
   assinatura do owner seguem R-07; pareceres de outros image IDs não se transferem.
4. **A-009/A-010 — decisão registrada em 2026-10-29:** usar Notes como app de
   referência para catálogo/consumidor e homologação da bridge. A escolha não
   substitui a aprovação de receita isolada nem a evidência de teste exigida.
5. **A-012 — decisão registrada em 2026-10-29:** autorizado ensaio I8 isolado e
   descartável em daemon DinD exclusivo, com um broker e uma fixture MCP, chamada em
   voo, shutdown/restart e verificação de término/erro, reconciliação e ausência de
   duplicação. Bill aprovou limite máximo de drain de 25 s, com 30 s de stop grace
   no Compose. Ensaio sintético executado em 2026-10-29 e registrado em E8; a
   autorização não inclui runtime real.
6. **E0 / trackers — decisão registrada em 2026-10-29:** declarar obsoletos os
   trackers L*/D* antigos e seguir somente os planos ativos vigentes. Não restaurar
   nem usar os trackers antigos como fontes de execução. Essa decisão não encerra
   automaticamente ações sem destino ou owner claro; elas permanecem abertas neste
   plano até encaminhamento rastreável.
7. **V-PILOT/publicação:** decidir em etapa própria se autoriza o piloto e, em
   separado, publicação/push. A autorização de DinD descartável já registrada não
   cobre nenhuma dessas operações.
8. **Mounts — decisão `R-10`, 2026-10-29:** Bill determinou manter o acesso amplo
   como default do broker Percival, supersedendo R-02 quanto ao default `[]`. Perfis
   explícitos `[]` (nenhum bind) e mounts estreitos continuam disponíveis; qualquer
    aumento de escopo a partir de um perfil mais restrito requer confirmação e
    auditoria. Nenhuma alteração de runtime foi autorizada.
9. **TUI / Bun — decisão de 2026-10-29:** atualizar para a última versão estável
   disponível, Bun 1.4.4; alinhar workflow CI/release, lockfile, relinking e notices.
   A decisão foi implementada e verificada localmente, sem autorização para publicar.
10. **C02 — decisão aprovada por Bill em 2026-10-29:** IaC `docs/decisions/` é o
     destino canônico do ADR de executor/transporte. O documento
     `docs/decisions/2026-10-29-iac-c02-percival-executor-transport.md` registra a
     decisão de implementar resources/prompts no Stage-2; ainda não tem SHA commitado
     para vínculo imutável. Aprovação de C02 não adota C01/C03 em deployments.
11. **CI privado / GitHub CLI — decisão de acesso:** Bill autorizou instalar o
    `github-cli` oficial; pacote Arch `github-cli 2.102.1-1` foi verificado, mas
    `sudo pacman -S` não pôde prosseguir porque a sessão não tem TTY/senha sudo.
    `/usr/bin/gh` continua ausente; não se passou senha/token nem se confiou a
    configuração mise global. Bill precisa instalar/autenticar localmente pelo
    fluxo de navegador, ou fornecer evidência autenticada do run #52.
 12. **A-010 / capabilities Notes — decisão de Bill e resultado local:** implementar
      resources/list, resources/read, prompts/list e prompts/get para Notes; a allowlist
      de tools fica independente e o broker limita read/get ao conjunto anunciado.
      DinD Engine 27.5.1 e matriz local R-09 passaram conforme §6.2; 189 testes focados
      passaram. Resta CI remoto e candidato limpo; static resources only. Templates,
      streaming e cancelamento seguem fora de escopo.

**Bloqueadores e condições de retomada:** resultado verificável do run Actions
`4086251288` (SHA completo, conclusão, jobs/logs e artifacts); retomar manager só após
agente atualizado e imagem identificada em execução; vincular C01/C03 aprovado aos
consumidores e verificar implementação; confirmar checkout/owner de
`pblabs-mcp-index` (deferido até haver owner/path); vincular C02 ao SHA commitado;
implementar/testar A-011, com Bill como
responsável pela IaC; concluir proveniência/B13 do TUI e resolver VEX para image IDs
exatos conforme R-07. Se algum recurso estiver indisponível, registrar owner e
condição de retomada, sem converter transferência em aceite.

### 8.4 Critério de encerramento

S2-NB só poderá ser marcado concluído quando cada ação A-001–A-012 e S2-NB-X01/X02
tiver resultado rastreável (verificada, limitação aceita ou transferência com dono,
aceite e dependência explicitados), os V-* aplicáveis estiverem reconciliados para
os candidatos exatos, a revalidação histórica estiver anexada e o retorno às seções
3/7 do coordenador estiver atualizado. Transferência sem evidência do dono permanece
pendente; publicação, runtime real e piloto são gates separados e não serão inferidos
do aceite local.

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
  específico do broker Percival e não concede privilégios por metadata MCP. Owners
  dos consumidores devem confirmar seus perfis por app, inclusive Notes.
- Atualizar C01, C03 quando descrevem perfis de execução, o plano coordenador e os
  planos consumidores. Preservar o relatório de 2026-10-28 como snapshot histórico e
  acrescentar a decisão posterior como adendo, sem reescrever as evidências coletadas.

R-10 decide a política, mas **não autoriza mudança de código/runtime, piloto,
publicação ou deploy**. A implementação permanece pendente de contrato versionado,
testes de broker/consumidores e autorização operacional específica.
