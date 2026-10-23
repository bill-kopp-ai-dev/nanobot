# Auditoria dos planos ativos contra o estado real do código — 2026-10-23

- **Preparado em:** 2026-10-23, por comparação item a item das pendências dos cinco planos ativos
  com o código, os testes, as imagens e o host nesta data.
- **Objetivo:** classificar cada pendência como **já executada**, **parcial**, **ainda válida** ou
  **sem sentido no estado atual do código**, e corrigir os planos que Ramiro.
- **Alvo:** `docs/plans/` sem `closed/` — padronização Docker, fechamento de senha única, plano
  integrado KG + MCP Docker, fechamento F4/F5/F7 e auditoria de status.
- **Método:** leitura e busca de código (`grep`, `sed`, `git log/show/status`) nos repositórios
  `nanobot`, `spa`, os seis MCP (`percival-notes-mcp`, `percival-khan-calendar`,
  `percival-agentmail-mcp`, `percival-weather-mcp`, `percival-osm`, `percival-deep-research`), os
  repositórios legados `percival-collective-memory`/`percival-acquire-knowledge` e o consumidor
  `alternative-positronic`. Inspeção read-only do host (`ls`, `find`, `docker version`, execução
  direta de `gh auth status`).
- **Natureza das evidências:** todas as afirmações abaixo são observações diretas do código ou do
  host, com `arquivo:linha`. Onde a ausência é afirmada, o texto registra onde se buscou.
- **Não verificado:** nenhum build, nenhum teste, nenhum container, nenhuma escrita remota e
  nenhuma rede foi executado. Não é possível, portanto, afirmar que a suíte passa hoje; só que a
  evidência exigida existe ou não existe no repositório. Itens que dependem de execução continuam
  abertos por definição de critério, independentemente desta auditoria.

## 1. Sumário dos veredictos

| Plano | Itens já executados | Parciais | Válidos | Sem sentido no estado atual |
| --- | --- | --- | --- | --- |
| Integrado, Onda A (KG) | 0 | A3, A4 | A1, A2, A7 | 0 |
| Integrado, Onda B (MCP Docker) | 0 | B3 | B1, B2, B4, B5, B6, B7 | 0 (B5 com premissa corrigida) |
| Integrado, Onda C (externo) | 0 | 0 | C1–C4 (bloqueados) | 0 |
| Senha única §1.2 | 0 | A2, A4, A5 | A1, A3, A6, A7, A8, A9 | 0 |
| Fechamento F4/F5/F7 | 0 | D4, D7, D8, D9, D11 | D1, D2, D3, D5, D6, D12 | **D10** |

Nenhuma pendência foi encontrada **integralmente executada** com evidência versionada. Isso é
consistente com o padrão já descrito na auditoria de status: quase todo item aberto tem um
componente de **execução** (rodar, no alvo, com registro) que nenhum teste local substitui.

A mudança relevante desta auditoria não é "fechar" itens, e sim **corrigir premissas e
dependências** que, mantidas, fariam o trabalho ser feito errado:

1. **D10 descreve um bug em um comando que não existe** nesta máquina (§4.1).
2. **B1, B4 e B6 dependem de um único recurso ausente**: não existe harness de browser real para a
   WebUI do Percival (§4.2). Sem ele, os três itens não são executáveis como escritos.
3. **A2 é irredutivelmente dependente de A5**: o benchmark de rebuild exige um conjunto
   representativo, e não há bundle nativo com conteúdo (§3.1).
4. **D7 está dividido entre dois caminhos que se contradizem**: o caminho Percival está correto e o
   caminho Positronic viola o init único (§3.4).
5. **O bloqueio de C1/A8 mudou de natureza**: `gh` não está mais "ausente"; está instalado e sem
   login, e o atalho do `mise` falha por configuração não confiável (§3.3).

## 2. Como ler esta auditoria

"Parcial" significa: parte do critério já tem evidência versionada e o resto depende de execução
ou de decisão. "Válido" significa: o critério continua correto e não encontrado. "Sem sentido"
significa: o objeto descrito pelo item não existe mais, ou existe de outra forma, e o texto do
plano levaria a uma intervenção inútil ou errada.

## 3. Achados por item

### 3.1 Onda A — KG nativo (A1–A7)

**A1 — smoke anônimo do aviso de bundle ausente. Válido, com escopo menor do que o texto supunha.**
O contrato de transporte está implementado e testado: `nanobot/webui/kg_http.py:110`, `:195` e
`:224` devolvem `503` com `bundle_uninitialized`, e
`tests/kg/test_gateway_f6.py:215` (`test_native_kg_health_distinguishes_uninitialized_bundle`)
comprova a negação anônima em `:244` e o `503` em `:255`. O que falta é exatamente o que o item
pede: prova em **Chromium real** de que a SPA exibe o aviso de setup, e não erro de rede nem `0`
fictício. O smoke real existente (`tests/kg/test_f7_browser.py`) prova `401` de bootstrap para
`/kg-interface/api/memory/graph/data` (`:96`), que é recusa de token, não o aviso de setup.
*Correção:* o item passa a ser "prova em browser da renderização do aviso", não "contrato de
transporte", que já está fechado.

**A2 — política de custo e benchmark de rebuild. Válido, mas dependente de A5.**
`nanobot/cli/kg.py:107` implementa `graph rebuild`. Não existe qualquer campo de reconstrução
automática em `nanobot/config/kg.py`: a reconstruição automática não está desligada por
configuração, **não está implementada**. Logo, a metade "decidir se habilita" é, hoje, um item de
projeto (proposta, limite, política) e não uma escolha de configuração. E a medição exigida — "em
conjunto representativo" — não tem dado: ver A5. Nenhum relatório mede duração de rebuild.
*Correção:* registrar a dependência A2 → A5 e separar "medição em fixture" (executável agora) de
"decisão sobre reconstrução automática" (exige desenho).

**A3 — lacunas residuais de F0. Parcial.**
Os três bullets de F0 têm estados distintos:
- bullet 3 (Windows/macOS) está **encerrado** por decisão do operador (Linux-only).
- bullet 1 (rota GET autenticada + ação WS de mutação devolvendo status/payload, chamadas
  anônimas falhando) está **provado**: `tests/kg/test_gateway_f6.py:36` cobre o contrato do
  listener com `memory/healthz` e `acquire/healthz` (`:99`, `:100`), mutações via `webui_request`
  (`:148`) e negação anônima (`:244`). Falta apenas o cliente SPA do bullet.
- bullet 2 (build de wheel/sdist com SPA prebuilt, sem fonte disponível, falhando fechado) está
  **implementado sem teste**: `hatch_build.py:186` aborta com "[kg-build] skip requested but
  prebuilt kg-interface/index.html is missing" e `:194` exige `bun` para build da fonte, mas
  nenhum teste em `tests/` exercita essa recusa (busca por `kg-build`, `prebuilt`, `hatch_build`,
  `WebUIBuildError` em `tests/` não retorna nenhum caso).
*Correção:* reduzir A3 ao que falta (cliente SPA e um teste que exija o build fail-closed) e
registrar o bullet 3 como encerrado.

**A4 — paridade de áudio AK. Parcial, e o critério mudou de natureza.**
O caminho Groq Whisper está implementado com recusa explícita: `UnsupportedCapabilityError` para
`transcription.enabled=false` e para provider diferente de Groq em
`nanobot/agent/kg/ak/multimodal.py:275` e `:278`, e `unsupported_capability` como payload de tool em
`nanobot/agent/tools/ak_multimodal.py:132`. Isso é testado
(`tests/kg/test_ak_multimodal.py:211`, "never substitutes other stt provider"). O que não existe é a
amostra real: o teste de sucesso substitui a transcrição por `fake_transcribe`
(`tests/kg/test_ak_multimodal.py:187`). Como a decisão D12 desacopla o ASR do par do turno, a
cláusula do critério sobre "par do turno que não suporta ASR" deixou de ser o caso aplicável.
*Correção:* o item passa a ter duas saídas — amostra real (exige `GROQ_API_KEY` e um arquivo de
áudio) ou aceitação formal de que a paridade de ASR não está provada. Contar o teste com stub como
paridade continua proibido.

**A5 — população autorizada dos bundles. Válido, bloqueado, e confirmado por inspeção.**
Não existe bundle nativo CM/AK com conteúdo no host. A única estrutura de memória presente é
`/home/bill/.nanobot/workspace/memory/` com dois arquivos (`MEMORY.md`, `history.jsonl`) e um diretório
`workspace/khalCalendar`; não há raiz de bundle nativa nem `acquire/`. Isso confirma o bloqueio por
dado autorizado, e mostra que não há insumo local para A2 nem para o ensaio A6.
*Correção:* nenhuma; apenas registrar a evidência do bloqueio.

**A6 — ensaio B6/B7 em cópia. Válido, bloqueado por A5.** Sem mudança; a dependência declarada está
correta e agora tem evidência de que o insumo não existe.

**A7 — EOL dos repos legados e tag. Válido.**
Não foi encontrado banner de EOL nem `MIGRATION.md` nos repositórios legados, nem tag de release
estável que sustente a tag local prevista. A entrega continua pendente de decisão do operador.

### 3.2 Onda B — capability MCP Docker (B1–B7)

**B1 — smoke em browser real das mutações. Válido, e hoje não executável como escrito.**
Não existe ferramenta de browser na WebUI: `webui/package.json` e `webui/bun.lock` não têm
`playwright` nem `puppeteer` (contagem zero), e o único teste da página é
`webui/src/tests/mcp-containers.test.tsx`, em `happy-dom`, com cliente mockado — ele afirma que
`requestMutation` foi chamado com `configuration` (`:105`-`:108`), mas não há rede, gateway nem
broker. O smoke real existente é um driver CLI
(`tests/mcp_docker/smoke_driver.py:1`, executado por `scripts/percival-f2-docker-smoke.sh:86`), e o
próprio relatório de origem admite que isso não fecha o gate
(`docs/reports/2026-10-08-mcp-docker-ui-refactor-execution.md:29`). Existe prior art reutilizável:
`tests/kg/test_f7_browser.py:104` dirige Chromium por CDP sem Playwright, e
`spa/src/tests/gateway-browser-probe.ts:1` é um probe de browser empacotado à parte, executado a
partir de `tests/kg/test_transport.py:206` e `:214`.
*Correção:* registrar que B1 exige antes um harness de browser para a WebUI do Percival, e apontar o
prior art do KG como caminho de menor custo.

**B2 — testes de UI dos critérios de aceite. Válido, com cobertura muito menor do que se supunha.**
Dos onze casos exigidos, **um** tem teste na UI: `stopped-persistent`, em
`webui/src/tests/mcp-containers.test.tsx:78`, com o ramo de render em
`webui/src/components/McpContainersPage.tsx:36`. Os outros dez existem apenas como código de
renderização ou como teste de backend: conflito 409 no install (handler em
`McpDockerManagement.tsx:220`, sem teste de UI; o 409 de backend em `tests/mcp_docker/test_contract.py:172`
é de update, não de install), falha no editor de host (o teste mais próximo,
`mcp-containers.test.tsx:153`, simula revisão nova por poll), `image-missing` e `container-missing`
(render em `McpContainersPage.tsx:35` e `:38`), "Data outdated; refresh failed" (render em `:33`),
cópia de digest (botão em `McpContainersPage.tsx:195`), senha rejeitada (handler em
`McpDockerManagement.tsx:244`), backup não restaurável (estado e botão desabilitado em `:453`-`:455`;
o teste em `mcp-containers.test.tsx:444` cobre só o caso restaurável), zero backups (o bloco só
renderiza se houver, `McpDockerManagement.tsx:449`) e viewport estreito (nenhum teste de largura nos
dois repositórios).
*Correção:* substituir "cobrir 11 casos" por uma lista com o estado real — um coberto, dez a
escrever — para que o item sejaPlanejável em vez de genérico.

**B3 — compatibilidade bidirecional. Parcial, e mais próximo do fechado do que o texto supunha.**
O tratamento de campo ausente como "não confirmado" está implementado e testado no domínio:
`nanobot/mcp_docker/service.py:93` (`"minimumMountsSupported": health.get(...) is True`) e `:94`
(rede cai para `["none"]`), com fixture de host antigo em `tests/mcp_docker/test_contract.py:253`
(`OldBroker` devolvendo apenas `{"ready": True}`) e teste de UI em
`mcp-containers.test.tsx:126`. O núcleo do contrato WebUI tem o mesmo padrão com fixture independente
(`tests/webui/test_client_contract.py:10` e `:33`, status `unknown` para metadados ausentes), e
`.agent/review-guide.md:20` exige "compatibility unconfirmed". Falta a direção "cliente antigo + host
novo" como fixture, uma matriz versionada e a faixa de protocolo declarada para esta capability.
*Correção:* o item vira "completar a terceira direção e versionar a matriz", porque o núcleo do
critério — nunca tratar ausência como autorização — já está satisfeito.

**B4 — acessibilidade e layout. Válido, e hoje não executável como escrito.**
Não há engine de a11y (`axe`/`jest-axe` ausentes em `webui` e `spa`) nem teste de viewport ou de
teclado/foco para esta página; `mcp-containers.test.tsx` não importa `userEvent`, e não há
`toHaveFocus`. Existem afordâncias de código não testadas (`role="alert"`, `aria-busy`,
`aria-labelledby` em `McpContainersPage.tsx:132`-`:217`). O ponto decisivo: `happy-dom` **não calcula
layout**, portanto nenhum teste de componente pode evidenciar largura estreita ou quebra de layout.
*Correção:* B4 passa a depender explicitamente do mesmo harness de browser de B1; a parte de teclado
e foco pode ser feita em componente, a parte de layout exige browser real.

**B5 — lacuna de UX do acesso ao host. Válido, com a premissa de repositório corrigida.**
A observação de mounts é binária: `webui/src/components/McpDockerManagement.tsx:489` mostra apenas
contagem ou `"unavailable"`, sem estado de divergência; não existe símbolo de comparação entre
configurado e observado. Não há destaque visual do modo Full (o `label` do radio em `:490` é texto
sem classe condicional; o único realce condicional existente, `:500`, é do diff pendente). A chave
`mcpDocker.networkFixed` está **morta**: presente em 10 locales
(`webui/src/i18n/locales/*/common.json`) e com **zero** referências em código de componente ou
biblioteca. Correção de premissa: a chave **não** está no repositório `spa` — a UI MCP Docker e suas
traduções vivem em `nanobot/webui/`.
*Correção:* corrigir a referência ao repositório e citar os dois estados ausentes por nome, para que
exista um critério verificável.

**B6 — matriz end-to-end das oito famílias. Válido, e hoje não executável como escrito.**
As oito famílias (instalar, configurar host, tools, servidor, atualizar imagem, reiniciar, excluir
registro, persistente) são exercitadas por três executores, nenhum deles browser: driver CLI com
gateway e broker reais (`tests/mcp_docker/smoke_driver.py` +
`scripts/percival-f2-docker-smoke.sh`), teste in-process com `FakeBroker`
(`tests/mcp_docker/test_contract.py:230`) e componente em `happy-dom`. O requisito "Weather/OSM e um
servidor preservado" foi atendido apenas como não-interferência passiva
(`docs/reports/2026-10-08-mcp-docker-f4-page-management.md:50`), não como terceiro registro
exercitado. *Correção:* registrar que B6 herda o bloqueio de harness de B1.

**B7 — revisão trimestral do pin Arch de CI. Válido, e agora com a Obligation correta.**
O pin está inalterado em `.github/workflows/ci.yml:415`:
`archlinux:base-20261004.0.606936@sha256:4e77cf2ea5f410e6f8be5abf93ccf17ce2436e87a138c167208356711a405dbd`.
É o único `archlinux:base` com digest em qualquer workflow. Não há automação de renovação
(`renovate`/`dependabot` ausentes; o agendamento existente em `ci.yml:5` reexecuta a suíte contra o
**mesmo** pin) nem registro de adiamento. O procedimento de revisão existe e está escrito no runbook
(`docs/operations/mcp-docker-local-runbook.md:101`, com saída exigida em `:111`), mas a tabela de
saída não existe.
*Correção:* o item permanece, e a evidência de que o pin não se moveu torna a revisão uma tarefa com
data-alvo, não uma intenção recorrente.

### 3.3 Onda C — dependências externas (C1–C4)

**C1 / A8 — GitHub Actions. Bloqueado, com o bloqueio agora descrito corretamente.**
O `gh` **existe e executa**: `/home/bill/.local/share/mise/installs/gh/2.102.1/gh_2.102.1_linux_amd64/bin/gh auth status`
responde "You are not logged into any GitHub hosts." O atalho `~/.local/bin/gh` **falha antes de
chegar ao binário**, porque o mise recusa a configuração local não confiável
(`Config files in ~/.config/mise/config.toml are not trusted`). O baseline do plano, que dizia "`gh`
não está instalado nesta sessão", estava errado quanto ao CLI e certo quanto à autenticação.
*Correção:* o bloqueio passa a ser "executar `gh auth login` (ou `mise trust` e usar o atalho)",
não "instalar o gh".

**C2 — inventário do VPS. Bloqueado, confirmado.** Não há host identificado; `~/.percival`, destino
de C3, não existe.

**C3 — migração e rollback no VPS. Bloqueado por C2.** Sem alteração. Vale registrar que o broker
exige Server 27.x e que o daemon ativo do host está em **29.9.1** (§5), o que torna qualquer
verificação local ainda menos equivalente ao alvo.

**C4 — aceite no alvo. Bloqueado por C2/C3.** Sem alteração.

### 3.4 Fechamento F4/F5/F7 (D1–D12)

**D1 — credencial exposta. Válido, e agora com o inventário que o item exige.**
O valor foi redigido da árvore corrente em `07f28314`, que também registra que "The value remains
in Git history and in the operator-password file on disk". O arquivo
`~/.nanobot/mcp-docker/operator-password` **existe** (9 bytes, modo 0600, 2026-10-10). O histórico
Git contém o literal removido em ao menos quatro commits
(`07f08314`, `07f28314`, `824b1db0`, `c17a4e23`, `a9ad9bf9`, `17ef2815`). A rotação foi adiada
explicitamente pelo operador (`docs/reports/2026-10-10-f7-p4-p5-blockers.md:15`).
*Correção:* registrar que o inventário de commits e o caminho do arquivo estão identificados; o que
falta é a rotação, que é do operador, e a decisão sobre histórico. **Não reproduzir o valor em
documento versionado** — é exatamente o que o item evita.

**D2 — proveniência. Válido, parcial por decisão.** O levantamento existe
(`docs/reports/2026-10-10-f7-provenance-and-identity.md`); falta a decisão de atribuição, que é do
operador.

**D3 — permissão do Khan. Válido, e o texto estava errado sobre uma das três opções.**
O servidor expõe, no código, dezessete identificadores `khan_*`, dos quais ao menos sete são
destrutivos ou de escrita: `khan_create_event`, `khan_delete_event`, `khan_delete_event_safe`,
`khan_delete_with_confirmation`, `khan_update_event`, `khan_update_workflow`,
`khan_quick_action_quick_create`. O canário observou 12 tools expostas
(`docs/reports/2026-10-10-f7-canary-execution.md`), então **existe discrepância a esclarecer** entre
identificadores no código e tools realmente publicadas. E, decisivo para o critério: **não existe
modo somente leitura no servidor** — a busca por `read_only`/`readonly`/`write_enabled` em
`percival-khan-calendar/src/` não retorna nada. Portanto "somente leitura ou subset nominal" não é
uma opção de configuração hoje; ou se aceita a superfície completa, ou se implementa um mecanismo de
restrição.
*Correção:* o item passa a dizer que a restrição exige engenharia, e a listagem efetiva por
consumidor precisa ser extraída do próprio protocolo, não de contagem em log.

**D4 — duplicatas por container ID. Parcial.**
O mapeamento por container **existe e é ferramenta**: `nanobot/mcp_docker/inventory.py:136` coleta o
`containerId`, e `:299` renderiza uma tabela com os rótulos `percival.mcp-docker.owner`,
`.managed-by`, `.server-id` e `.instance-id`. O que falta é o que o item realmente exige e que o
inventário não prova: ciclo de vida demonstrado e cardinalidade esperada documentada.
*Correção:* o item passa a exigir lifecycle e cardinalidade, usando o inventário existente como
ferramenta — trabalho substancialmente menor do que o texto sugere.

**D5 — regressão `tools/call` do Khan. Válido, com a investigação parcialmente respondida.**
Confirmado por varredura: **não existe** teste de protocolo em
`percival-khan-calendar/tests/` — buscas por `tools/call`, `call_tool`, `ClientSession`,
`stdio_client` e `jsonrpc` não retornam nada em `tests/` nem em `src/`. Todos os testes chamam a
função Python por trás do tool (`tests/_helpers.py:24`-`:34`, que extrai `tool.fn`). O isolamento do
calendário real está garantido (`tests/conftest.py:11` monkeypatcha `WORKSPACE_DIR`/`DATA_DIR`/`DB_FILE`
e desliga o lock). Versões resolvidas: `mcp` 1.30.0 e `fastmcp` 3.4.4 em `uv.lock`, com faixas
`mcp[cli]>=1.28.1,<2.0.0` e `fastmcp>=3.2.0` em `pyproject.toml:13`-`:14`.
*Correção:* o item pode registrar quais versões estão em jogo; a incompatibilidade em si ainda não
foi reproduzida, e nenhum teste atual a tornaria visível.

**D6 — OpenSSH `CVE-2026-60002` no gateway. Válido, e confirmado como o pior risco da lista.**
O runtime é `ghcr.io/astral-sh/uv:0.9.30-python3.12-trixie-slim@sha256:41eb2281…` (`Dockerfile:11`)
e instala `openssh-client=1:10.0p1-7+deb13u4` (`Dockerfile:32`), isto é **10.0p1**, abaixo do
exigido. `openssh-server` não é instalado, e o OpenVEX do gateway declara `not_affected` por
`component_not_present` para o componente servidor — o que é coerente e continua restrito ao image
ID do gateway (`docs/reports/2026-10-10-f3-openvex.json`), sem nenhuma declaração sobre `60002`.
A triagem de F3 já classificou o achado como "Critical não resolvido" e proposed waiver, sem aprovar
(`docs/reports/2026-10-10-f3-remediation-triage.md:168`). Não há waiver aprovado nem build do gateway
em base corrigida, e nenhum teste roda dentro da imagem.
*Correção:* nenhuma; o item continua íntegro e é o de maior severidade. Registrado aqui que a
sub-rotina "OpenSSH Forky 10.5p1 testado fora da imagem" citada no plano de fase **não** substitui o
build do gateway.

**D7 — evidência de runtime nos artefatos finais. Parcial, e dividido entre dois caminhos.**
O que está cumprido e testado: init único por tini em OSM e Deep Research
(`percival-osm/Dockerfile:146`, `percival-deep-research/Dockerfile:155`), forma exec de ENTRYPOINT em
todos os seis, healthcheck desabilitado no servidor stdio de OSM (`Dockerfile:142`,
`test_d6_docker.py:54`) e asserção de ausência de healthcheck em Deep Research
(`tests/test_docker.py:226`), forma exec verificada em Weather (`tests/test_dockerfile.py:60`).
O que está errado: o consumidor Positronic adiciona init de forma incondicional —
`alternative-positronic/packages/positronic-mcp-docker/src/managed.ts:640` monta
`"docker", "run", "--pull=never", "--rm", "--init", "--interactive"`. Como OSM e Deep Research já
entram por tini, **todo** lançamento stdio por esse consumidor empilha `docker-init` sobre `tini`:
é exatamente o achado de F6
(`docs/reports/2026-10-10-f6-local-cutover.md:49`), ainda vivo. O broker do Percival **não** faz
isso (`scripts/percival_mcp_broker_f0.py:370` passa apenas `--rm --pull=never --network=none
--cap-drop=ALL --security-opt=no-new-privileges`), e o runbook já prescreve a regra correta
(`docs/operations/mcp-docker-local-runbook.md:14` e `:96`). Além disso, três dos seis repositórios
(Notes, Khan, AgentMail) **não têm** teste de contrato de imagem.
*Correção:* o item deixa de ser "consolidar evidência" genérico e passa a ter duas partes: (a)
corrigir ou justificar o `--init` do consumidor Positronic, que é defeito de código, não de
evidência; (b) criar os testes de contrato de imagem que faltam em três repositórios.

**D8 — pins e builds de checkout limpo. Parcial, e metade do critério já existe.**
O gateway **já tem** o guard que o item pede: `scripts/percival-docker-build.py:71` lê
`git rev-parse HEAD`, `:75` detecta árvore suja rastreada e `:96`/`:98` **recusam** o build
inconsistente, rotulando `:157` `io.percival.build.worktree=dirty`. Nenhum dos seis MCP tem guard
equivalente — busca por `diff --quiet`, `--dirty`, `status --porcelain` nos `scripts/` dos seis não
retorna nada. As labels são divergentes: OSM usa SHA curto
(`percival-osm/scripts/docker-build.sh:80`, `git rev-parse --short HEAD`), enquanto o verificador de
manifesto exige igualdade com o SHA completo
(`percival-osm/scripts/write_docker_ci_manifest.py:28`), o que não pode ser satisfeito se a CI
passar `$GITHUB_SHA`. Não há manifest ou digest commitado em nenhum dos seis, logo não há prova
versionada de rebuild limpo.
*Correção:* o item passa a ter duas frentes independentes — Os seis MCP sem guard de árvore suja, e
um defeito novo (label curto do OSM incompatível com o verificador de manifesto) que **não constava
de nenhum plano**.

**D9 — walkthrough do manual e retenção. Parcial.**
O manual existe (`docs/operations/mcp-docker-local-runbook.md`) e os comandos que ele cita existem:
o runbook referencia apenas `nanobot auth init` e `nanobot mcp-docker doctor`, e ambos estão
registrados (`nanobot/cli/auth.py:50`, `nanobot/cli/mcp_docker_f1.py:23`, com o grupo montado em
`nanobot/cli/commands.py:108`). Falta o walkthrough em fixture e a política de retenção assinada; a
tabela de revisão trimestral exigida pelo próprio runbook (`:111`) não existe.
*Correção:* o item pode declarar a parte de consistência texto↔comando como **verificada**, o que
reduz o trabalho restante ao walkthrough e à assinatura.

**D10 — `mcp server install-local` do Positronic. Sem sentido no estado atual; reescrever.**
O comando **não existe nesta máquina**: não há binário `positronic` no PATH, o pacote de CLI do
fork é `packages/cli` (`packages/cli/package.json`, nome `@opencode-ai/cli`, bin `lildax`) e a busca
por `install-local` em todo o código TypeScript do fork, fora de `node_modules` e de
`positronic/docs/plans`, **não retorna nenhuma ocorrência**. Não há, portanto, "falha silenciosa" a
corrigir: não há comando. O que existe é documentação que promete o comando: a skill global
`mcp-docker-workflow` lista `positronic mcp server install-local <id> sha256:<image-id> --scope local`
(`SKILL.md:37`) e um bloco de recovery de 11 comandos (`:31`-`:43`), nenhum dos quais é
implementado no pacote de CLI. O estado real de registro é o registry do servidor,
`~/.positronic/mcp/registry.json`, com `schemaVersion` e 6 servidores.
*Correção:* reescrever o item. O problema real é (a) a skill documenta comandos inexistentes, o que
pode induzir a um caminho de recuperação que falha; (b) é preciso registrar qual é o caminho de
reinstalação suportado, com a interface suportada, e remover o workaround de edição direta do
registry. Não há bug de handler a corrigir.

**D11 — skill F8 e AGENTS.md. Parcial, com a matriz agora mensurável.**
A skill de gestão **não existe** para o Percival: as skills globais são `docker-desktop`,
`mcp-docker-workflow`, `journaling-*`, `memory-*`, `project-bootstrap` e `skill-creator`, e a única
de containers é a do Positronic (`mcp-docker-workflow`), que é justamente a que o plano de fase manda
comparar antes de decidir extensão ou skill separada. A matriz de `AGENTS.md` está quase completa:
global, raiz do Percival e do consumidor Positronic presentes; Khan, Weather, OSM e Deep Research
presentes; **Notes e AgentMail sem `AGENTS.md` na raiz** — exatamente os dois arquivos que o gate F8
exige criar. A raiz do Percival **não menciona MCP Docker** em seu `AGENTS.md`.
*Correção:* o item vira três tarefas concretas e verificáveis — criar os dois `AGENTS.md`, decidir
extensão versus skill separada **contra** a evidência da skill existente, e exercitar a skill em
fixture com dry-run.

**D12 — assinatura F7. Válido, bloqueado.** Sem mudança; a lista de antecessores só encolheu em
escopo, não em número.

### 3.5 Senha única (§1.2, A1–A9)

Os mecanismos de A2, A4 e A5 **existem no código**; o que falta é a evidência de execução exigida,
o que o próprio item já declara. A auditoria acrescenta precisão e um possível gap de engenharia:

- **A1 — mechanisms presentes:** `nanobot/cli/auth.py:50` (`auth init`), `:77` (`auth change`),
  `:111` (`auth reset`), `:145` (`auth status`). Ensaio em Server 27.5.1 ainda não executado.
- **A2 — fail-closed implementado:** `allow_remote_admin` existe com default `False`
  (`nanobot/mcp_docker/contracts.py:109`), é publicado no snapshot (`:166` de `service.py`) e é
  aplicado no acesso remoto (`nanobot/webui/settings_routes.py:411`). Falta a prova de recusa por
  origem não-loopback.
- **A3 — sem código novo necessário:** o ensaio de proxy TLS é de infraestrutura de teste.
- **A4 — mecanismo parcial, com possível lacuna:** há emissão de token com TTL e expiry
  (`nanobot/webui/gateway_tokens.py:79`-`:91`, com purge de expirados em `:71`) e verificação de
  expiração sem extensão da janela ociosa, usada para reaping de sockets
  (`nanobot/webui/gateway_auth.py:126`). **Não localizei renovação silenciosa da credencial de
  sessão** no código auditado; se ela não existir, o critério "renovação silenciosa pela sessão"
  é trabalho de engenharia e não apenas de evidência. Isso precisa ser confirmado antes de P2-D.
- **A5 — comando existe:** `auth change` (`nanobot/cli/auth.py:77`); falta o ensaio de rotação.
- **A6/A7 — sem alteração.** A6 continua coberto por P2 e, portanto, aberto.
- **A8 — bloqueado, causa agora identificada** (§3.3).
- **A9 — bloqueado, e `~/.percival` não existe** (§3.3).

## 4. Itens que não fazem mais sentido, ou cuja premissa estava errada

### 4.1 D10 — o comando objeto do item não existe

O item descreve um bug de handler em `mcp server install-local`. Não há CLI Positronic instalada,
nem o comando no pacote de CLI do fork. Manter o item induziria a depurar código inexistente. O
substituto correto é: verificar qual é o caminho de reinstalação **suportado** pelo servidor
(registry gerido pelo servidor), corrigir a skill que documenta comandos inexistentes, e remover o
workaround de edição direta.

### 4.2 B1, B4 e B6 — três itens, uma única capacidade ausente

Os três exigem browser real; nenhum deles é executável com o que existe. Somando A1 (browser do
aviso de setup) e D9 (falsa falha de health no walkthrough), **cinco** itens dependem de um harness
de browser que não existe para a WebUI do Percival. O plano de fase e o plano integrado tratam
esses itens como tarefas independentes, o que subestima o trabalho.

### 4.3 A5 → A2 — dependência não declarada

A2 exige medição em "conjunto representativo"; A5 é o que cria um. Sem declarar a dependência, A2
será medida em fixture vazia e produzirá uma decisão de política sem base.

### 4.4 B5 — repositório incorreto na premissa

A chave i18n e a UI MCP Docker estão em `nanobot/webui/`, não em `spa`. Auditoria feita no repositório
errado concluiria que a chave não existe.

### 4.5 D3 — "somente leitura" não existe como opção

O critério offers "somente leitura ou subset nominal" como se fossem alternativas de configuração.
Não há modo somente leitura no servidor Khan; a alternativa real é aceitar a superfície ou implementar
a restrição.

### 4.6 Baseline do plano de senha única — Engine e gh

O baseline afirma Client/Server 29.7.2 e "`gh` não está instalado". Hoje: **29.9.1**, e `gh` 2.102.1
instalado, executável e **sem login**. A conclusão prática (não prosseguir) é a mesma; a causa e a
ação mudam.

## 5. Defeitos novos, não registrados em nenhum plano

| # | Achado | Onde | Por que importa |
| --- | --- | --- | --- |
| N1 | `--init` incondicional do consumidor Positronic sobre imagens que já usam tini | `alternative-positronic/packages/positronic-mcp-docker/src/managed.ts:640` vs `percival-osm/Dockerfile:146` e `percival-deep-research/Dockerfile:155` | init duplo em todo lançamento stdio; o runbook já o proíbe |
| N2 | Label de revisão em SHA curto incompatível com o verificador de manifesto | `percival-osm/scripts/docker-build.sh:80` vs `write_docker_ci_manifest.py:28` | o build do OSM não passa na verificação de provenance se a CI passar o SHA completo |
| N3 | Skill global documenta 11 comandos `positronic mcp server` inexistentes no pacote de CLI | `~/.positronic/global-skills/mcp-docker-workflow/SKILL.md:31`-`:43` | caminho de recuperação que falha; confunde D10 |
| N4 | Três dos seis MCP sem teste de contrato de imagem | `percival-notes-mcp`, `percival-khan-calendar`, `percival-agentmail-mcp` | D7 não pode ser fechado por evidência desses repos |
| N5 | Chave i18n morta em 10 locales | `webui/src/i18n/locales/*/common.json` (`mcpDocker.networkFixed`) | dívida de tradução; item Known de B5 |
| N6 | `Notes` e `AgentMail` sem `AGENTS.md` na raiz | repositórios MCP | gate F8 exige os dois |
| N7 | Atalho `gh` do mise falha antes de executar o binário | `~/.local/bin/gh` + `~/.config/mise/config.toml` não confiável | bloqueia o CLI com uma mensagem que sugere problema de configuração, não de autenticação |

## 6. O que não foi verificado

- Não se a suíte de testes passa hoje: nenhum `pytest`, `vitest` ou `bun test` foi executado.
- Comportamento real de runtime (PID 1, sinal, init efetivo): exige daemon; o achado N1 é
  **derivado estaticamente** do par `managed.ts` + Dockerfile, não observado em container.
- Se houve execução manual de browser ou evidência fora do repositório (prints, notas do operador,
  CI): não tenho acesso e não afirmo ausência fora do repositório.
- Se existe waiver de `CVE-2026-60002` aprovado fora do repositório: o repositório diz "não aprovada".
- Imagem do gateway já construída em base corrigida em daemon local: a árvore não tem tal base, mas
  uma build local efêmera não é verificável por leitura.
- Os repositórios legados CM/AK foram verificados quanto a banner/tag apenas por observação de
  arquivos; não por API do GitHub, que exigiria autenticação.

## 7. Mudanças aplicadas nos planos

Esta auditoria mudou o texto dos planos, não o seu escopo. Resumo do que foi revisto:

- **Plano integrado:** A1 e A3 reduzidos ao que falta; A2 com dependência declarada de A5 e
 objeto de configuração; A4 com as duas saídas possíveis; B1, B4 e B6 com o bloqueio de harness
  declarado; B2 com a cobertura real (1 de 11); B3 com o que já está provado; B5 com o repositório
  correto e os dois estados ausentes nomeados; B7 com o pin verbatim; C1 com a causa correta do
  bloqueio; N1, N2, N4, N5 e N6 registrados.
- **Senha única:** baseline de Docker e `gh` corrigido; A2, A4 e A5 annotadas com a existência do
  mecanismo; A4 sinaliza a possível ausência de renovação silenciosa.
- **Fechamento F4/F5/F7:** D4 e D8 reduzidos ao que falta; D3 corrigido; D7 dividido em defeito de
  código e falta de teste; **D10 reescrito**; D9 com a consistência texto↔comando verificada; D11 em
  três tarefas; D1 com o inventário do histórico.
- **Padronização Docker (quadro histórico):** marcação de que os onze itens foram reverificados e de
  onde está o resultado, sem reescrever o snapshot.
- **Auditoria de status:** nova seção apontando para este relatório.