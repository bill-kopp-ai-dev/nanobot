# Plano de fechamento — autenticação de senha única e aceite Docker/VPS

- **Preparado em:** 2026-10-11; plano solicitado antes de retomar os gates pendentes.
- **Estado:** P0 concluído para fixação do candidato e preparação; P1 concluído e snapshot publicado em `d3b29843`. P2 adiado pelo operador; P3 aguarda autenticação do GitHub CLI; P4 aguarda seleção de VPS/staging. Closure global permanece aberta. Desde 2026-10-23 este plano também é o **único dono das pendências de aceite** da refatoração de senha única, cujo plano foi arquivado em `closed/` (ver §1.2).
- **Objetivo:** fechar, com evidência reproduzível, a proveniência do KG SPA embutido, a integração gateway+broker em Docker Server 27.x e os gates remotos de Actions/VPS da refatoração de senha única.
- **Autoridade:** o operador autorizou prosseguir com as pendências. Essa autorização não converte Engine 29.x em Engine 27.x, não autoriza enfraquecer o gate do broker, não seleciona um VPS ainda não identificado e não autoriza tag, release, publicação ou cutover de dados MCP reais.
- **Fora de escopo nesta closure:** implementar o login interativo do browser-proxy SSH remoto. Por decisão do operador, ele permanece fail-closed (`remote_auth_required`) e deve ser acompanhado como trabalho separado.
- **Plano de implementação de referência (arquivado):** [refatoração de senha única](closed/2026-10-11-percival-single-password-auth-refactor-plan.md); as etapas de implementação A–E estão concluídas e evidenciadas, e as pendências de aceite foram transferidas para a §1.2 deste plano em 2026-10-23. Gates F7 e VPS permanecem também sujeitos ao [plano F7](closed/2026-10-10-f7-operations-acceptance-closure-plan.md) e ao [plano MCP Docker](closed/2026-10-06-mcp-docker-first-class-execution-plan.md).

## 1. Baseline observado

| Item | Estado verificado | Consequência |
| --- | --- | --- |
| Percival | `nanobot/main` em `d773f8b5`, sincronizado com `origin/main`, working tree limpa. | SHA base para o próximo snapshot/CI. |
| Fonte SPA | `spa/main` em `8e4ff73`, commitado e sincronizado. Permanecem arquivos locais não rastreados preexistentes (`.positronic/`, `AGENTS.md`, `scripts/dev-spa.sh` e testes auxiliares); não fazem parte do código commitado. | Não usar o working tree atual para declarar proveniência limpa. Construir de um worktree temporário no SHA commitado. |
| Snapshot KG | Baseline anterior registrava `revision=f607d6a`, `dirty=true`; atualizado em P1 para `revision=8e4ff73fbe8d9f9966cf6853cca679b4e14e72de`, `dirty=false`, com hashes consistentes e commit Percival `d3b29843` publicado. | P1 concluído; browser gate real passou. |
| Docker disponível | Contexto ativo `default`: Client/Server **29.7.2**. Contexto `desktop-linux` não tem daemon disponível. O broker recusa Server 29.x quando `allow_engine29=false`. | Não repetir gateway+broker diretamente no Engine ativo. Não alterar o gate de compatibilidade. |
| Engine 27.x descartável | Imagem `docker:27.5.1-dind` no digest `sha256:aa3df78ecf320f5fafdce71c659f1629e96e9de0968305fe1de670e0ca9176ce` está disponível. `scripts/percival-f1-engine27-validate.sh` já a usa para provar o broker/fixtures no daemon 27.5.1, mas não exercita a nova autenticação WebUI com gateway+broker juntos. | Reutilizar a imagem e os controles do harness existente; estender o ensaio com uma fixture de senha e operação autenticada. |
| Fixtures Docker MCP | Os aliases `percival-f1-*`/`percival-f2-*` não aparecem na lista atual de imagens locais. | Confirmar os repositórios-fonte e construir/carregar fixtures a partir dos commits fixados em `scripts/percival-f2-build-fixtures.sh`, antes do ensaio; não puxar tags mutáveis durante a execução. |
| GitHub Actions | `gh auth status` informa que não há conta autenticada nesta sessão. `nanobot` possui `ci.yml`, `kg-platform.yml` e `tui-release.yml`; o repo `spa` não possui `.github/workflows/`. | Runs remotos não podem ser inspecionados até autenticação do operador. Não afirmar gate SPA remoto inexistente. |
| VPS | O plano F0/F7 requer inventário real e Engine Server 27.x, mas este baseline não identifica hostname, acesso SSH, projeto Compose nem volume-alvo. | Começar com inventário read-only; solicitar/confirmar o destino e ambiente de staging antes de qualquer escrita remota. |

## 1.1 Execução P0/P1 — 2026-10-11

- **P0:** Percival confirmado em `d773f8b5e9ec53fbecee4c8df0aa2efdbe6bfdc0` antes do rebuild e SPA em `8e4ff73fbe8d9f9966cf6853cca679b4e14e72de`; ambos alinhados com `origin/main`. Digest local `docker:27.5.1-dind` confirmado como `sha256:aa3df78ecf320f5fafdce71c659f1629e96e9de0968305fe1de670e0ca9176ce`. SHAs Weather `b5032f4fe4f0e89cc49556b62725ba598fb1c181` e OSM `ca3c3977fc124b649876900fc0c3ffb6fe7c87fb` existem nos clones locais. Checksums dos Dockerfiles: gateway `75dbfc7f79ce9c3ac4a4a8736aeb39e9c8f8d93a118810ca69e86533a28c0500`; broker `a5ba02a4939a16ac53bb54821cb5f1aa66f26831f9627ecb2901516fd599add5`. O harness F1 revisado usa `--network none`, não monta socket Docker do host e verifica ausência de caminhos diretos ao daemon no container MCP. O Engine ativo permanece 29.7.2; nenhum DIND foi iniciado nesta execução. Imagens gateway/broker locais preexistentes foram observadas (IDs `sha256:e78ae8c2c3e0e138984516bb8ef33591219d7febcc43602890334277eb520d3c` e `sha256:f222d8958c0fbace05075ebba0de53575826fc7c29362918c70c0593d4a77004`) e não são declaradas candidatas de P2.
- **P1:** worktree detached em `/home/bill/.positronic/runtime/tmp/opencode/spa-auth-clean-8e4ff73`, árvore limpa no SHA indicado. `bun install --frozen-lockfile`, `bun run test` (**250 passed / 36 arquivos**), `bun run lint` e `bun run build` passaram. O build mantém aviso de chunk principal acima de 500 KB (1.37 MB raw; 456 KB gzip). `uv build --sdist` com rebuild forçado e `uv build --wheel` de snapshot prebuilt passaram. `SOURCE.json` confirma `dirty=false`, lock SHA-256 `1a10d3716ef28bac480cad7f36a0f26e009d0c8342a486af636bb6fa207f4dcf`, hashes dos assets e index consistentes; os JS gerados não contêm `kg-gateway-secret` nem `X-Nanobot-Auth`. Testes `tests/kg/test_bundle.py tests/kg/test_f7_browser.py`: **5 passed, 1 skipped**; skip esperado do teste de paridade do core sem `PERCIVAL_KG_CORE_SOURCE`; Chromium executou e passou o login/browser gate. Commit separado `d3b29843` (`build(kg-spa): refresh snapshot from clean auth source`) foi enviado a `origin/main` (`d773f8b5..d3b29843`).
- **Escopo/limites:** P2 não foi executado, conforme decisão do operador; P3 não executado porque `gh` não está autenticado nesta máquina. P4 não executado: não há VPS/staging disponível. Nenhum Engine DIND, fixture, serviço MCP, estado persistente ou credencial real foi usado neste aceite.

## 1.2 Etapas herdadas da refatoração de senha única — 2026-10-23

- **Origem:** [plano de refatoração de senha única](closed/2026-10-11-percival-single-password-auth-refactor-plan.md), arquivado em 2026-10-23 com transferência integral das pendências para este plano. As etapas de implementação A–E (contrato compartilhado, núcleo do gateway, administração MCP, clientes, empacotamento/documentação) e os gates locais de 2026-10-11 (`pytest` 9348 passed / 49 skipped, `basedpyright nanobot` 0 erros, `ruff check .` limpo, SPA `251 passed` com lint e build, snapshot KG de fonte limpa `8e4ff73` publicado em `d3b29843`) permanecem como evidência encerrada. O plano arquivado **não** é reaberto.
- **Regra:** toda pendência abaixo é executada e evidenciada **neste** plano. Nenhuma delas se fecha por teste local, pelo campo `Client.Version`, por tag de imagem ou por ausência de runs. O plano arquivado exigia que os gates finais e o ensaio produzissem evidência antes de declarar a refatoração implementada; essa exigência passa a valer para P2–P4 aqui.

| # | Pendência herdada | Critério de aceite | Onde é executada | Estado |
| --- | --- | --- | --- | --- |
| A1 | Ensaio integrado gateway+broker em imagem Docker com volume limpo, incluindo elevação, mutação MCP reversível e auditoria sem senha | `docker version` **dentro** do daemon = Client 27.5.1 / Server 27.5.1; elevação pela UI executa a operação via broker; token humano distinto do token do broker; nenhuma mutação em estado real | P2 (itens 1–6) | **aberto** — adiado pelo operador |
| A2 | Negação de acesso remoto quando `allowRemoteAdmin=false` | Mutação com credencial `operator-admin` vinda de origem não-loopback é recusada; a mesma credencial funciona em loopback; o endpoint de bootstrap de admin permanece loopback-only | P2-B | **aberto** — não coberto por P2 |
| A3 | Acesso por túnel e por proxy TLS representativo de VPS | Login e renovação de token funcionam atrás de proxy TLS com cookies de sessão, sem senha ou token em URL, `localStorage`, payload ou log | P2-C e P4 item 4 | **aberto** — não coberto por P2 |
| A4 | Renovação e expiração de token, e revogação em WebSockets já abertos | Renovação silenciosa pela sessão; expiração rejeita novas requisições **e** encerra ou recusa operações nos WebSockets abertos; logout encerra a elevação | P2-D | **aberto** — não coberto por P2 |
| A5 | Senha criada e **alterada** pelo operador, sem recadastro | `nanobot auth init` e a troca de senha concluem no CLI; login com a senha nova; rotação anterior deixa de autenticar; nenhum segredo humano em `config.json`, arquivo WebUI, URL ou storage do navegador | P2-E | **aberto** — não coberto por P2 |
| A6 | Recriação de contêiner mantendo volume, e Compose após o corte | Mesmo volume e login sem recadastro; broker continua segregado; gateway sem socket nem CLI Docker; estado MCP, CAS e logs redigidos conferidos | P2 item 5 (recriar) e P5 | **aberto** — coberto por P2 |
| A7 | Cutover da instância real com backup e retorno preservados | Identificar volume e arquivos de credenciais **sem exibir conteúdo**; cópia privada do estado anterior; se o ensaio final falhar, restaurar a combinação **inteira** imagem/configuração/credenciais em ambiente privado, sem executar binário antigo sobre estado parcialmente convertido | P2-F | **aberto** — a execução de 2026-10-11 usou estado descartável |
| A8 | GitHub Actions no SHA final | Jobs obrigatórios verdes no SHA publicado, com `headSha` conferido; artefatos baixados e confrontados com fonte, locks e digests | P3 | **bloqueado** — `gh` sem autenticação |
| A9 | Inventário read-only e gate VPS | Inventário datado e redigido, Engine 27.x demonstrado no alvo, staging end-to-end aprovado, relatório separado do aceite local | P4 | **bloqueado** — sem host/staging identificado |

**Fora de escopo herdado:** o login interativo do browser-proxy SSH remoto permanece fail-closed
(`remote_auth_required`) e não é reaberto por esta transferência.

## 2. Estratégia e ordem de execução

### P0 — Fixar candidatos e fronteiras

**Responsável:** agente, em modo read-only.

1. Registrar `nanobot` HEAD/remote e `spa` HEAD/remote; validar que o candidato é `d773f8b5` e a fonte SPA é `8e4ff73` ou commits posteriores explicitamente aprovados.
2. Confirmar o digest do `docker:27.5.1-dind`, os checksums dos Dockerfiles/imagens gateway e broker e os SHAs das fixtures Weather/OSM. Confrontar com os pins já registrados em F1/F2; não reutilizar uma imagem somente pelo nome de tag.
3. Definir uma pasta scratch nova, única e descartável para checkout SPA, estado de gateway, token de broker, logs redigidos e arquivos de Compose. Nenhum caminho `~/.nanobot`, `~/.percival`, `~/.positronic` ou volume real pode ser montado no ensaio.
4. Confirmar que a execução interna Docker 27 será isolada: DIND sem rede externa e sem portas publicadas no host; nenhum bind do socket Docker do host dentro do DIND. Dentro do DIND, apenas o container broker recebe o socket do daemon DIND.

**Saída:** registro de baseline contendo SHA, digest e caminhos temporários; se o digest não corresponder, parar antes de iniciar qualquer daemon.

### P1 — Reconstruir snapshot SPA de fonte limpa

**Responsável:** agente. **Dependência:** P0.

1. Criar um `git worktree` detached temporário de `/home/bill/Projects/spa` no commit `8e4ff73` (ou SHA mais novo depois de revisar a diferença). Não copiar os arquivos locais untracked do checkout original.
2. No worktree, verificar `git status --porcelain` vazio; instalar exatamente pelo lockfile com `bun install --frozen-lockfile`; executar `bun run test`, `bun run lint` e `bun run build`.
3. Reconstruir o snapshot pelo hook oficial do Percival:

   ```bash
   PERCIVAL_FORCE_KG_SPA_BUILD=1 \
   PERCIVAL_KG_SPA_SOURCE=<worktree-limpo-spa> \
   uv build --sdist
   ```

   Gerar também o wheel pelo fluxo de build do projeto para exercitar a verificação do snapshot prebuilt. Não rodar o build a partir do working tree SPA com arquivos não rastreados.
4. Verificar `SOURCE.json`: `revision` igual ao SHA do worktree, `dirty=false`, `lock_sha256` válido e hashes dos assets exatamente iguais. Confirmar que `index-KWflHv27.js` (ou o hash resultante) não contém o prompt/contrato `kg-gateway-secret` nem o header `X-Nanobot-Auth` como fluxo de login.
5. Executar `tests/kg/test_bundle.py` e `tests/kg/test_f7_browser.py`; o browser gate deve executar, não pular por bundle legado. A verificação browser deve provar: bootstrap anônimo `401`, senha válida por `POST /auth/login`, cookie de sessão, bootstrap token-bound, carregamento CM/AK e ausência de senha/token em URL ou `localStorage`.
6. Revisar/stage apenas `nanobot/web/kg-interface/{SOURCE.json,index.html,assets/*}` gerados. Criar um commit separado de build do snapshot; push para `nanobot/main` só após os testes e revisão dos hashes. Revalidar `git status` e o SHA publicado.

**Critério de conclusão:** bundle reproduzível a partir do commit SPA publicado, manifesto `dirty=false`, browser gate real verde e snapshot versionado no Percival.

### P2 — Ensaio gateway+broker em Docker Server 27.5.1 descartável

**Responsável:** agente, usando o harness DIND já aprovado em F1. **Dependências:** P0 e imagens candidatas após P1.

1. Estender o harness, sem mudar `_supported_docker_versions` nem setar `PERCIVAL_DISPOSABLE_ENGINE29`, para iniciar `docker:27.5.1-dind` pelo digest fixado. Exigir no próprio daemon `Client=27.5.1` e `Server=27.5.1`; falhar fechado se divergir.
2. Construir gateway e broker dos SHAs candidatos em ambiente controlado, `docker save/load` para o daemon DIND e verificar IDs/digests lá. Construir/copiar uma fixture MCP imutável e conhecida (Weather preferida; OSM somente se os SHAs/licença/build forem confirmados). O ensaio não publica imagem em registry.
3. Criar estado descartável e senha fixture somente pelo `nanobot auth init` interativo no container CLI. Criar `broker-token` aleatório com ownership/mode requeridos. Nunca imprimir a senha/token, gravá-los no repo, ou reutilizar credenciais reais.
4. Subir gateway+broker na topologia sidecar aprovada (`network_mode: service:nanobot-gateway` ou harness equivalente). Confirmar pelo inspect redigido que o gateway não recebe socket/CLI e que o broker é o único container com socket do daemon DIND. O gateway e o broker não devem ter caminho de rede para fora do DIND.
5. Exercitar pela interface HTTP/WebSocket real — não chamar o domínio `DockerMcpService` diretamente:
   - verifier ausente: bootstrap e chamadas MCP negados, CLI orienta `auth init`;
   - após setup: senha errada dá `401`; login correto dá cookie; bootstrap e API bearer funcionam;
   - snapshot MCP é somente leitura sem elevação; mutação sem elevação e elevação com senha errada são recusadas;
   - `auth.elevate` com a mesma senha permite instalar uma fixture imutável, completar `initialize`/`tools/list` e uma chamada MCP de leitura; auditoria/outputs não contêm senha;
   - executar rollback/remoção da fixture via ação autenticada suportada, validando CAS e ausência de residual no registry;
   - recriar gateway e broker mantendo apenas o volume descartável; confirmar login, estado e operação após restart;
   - logout/rotação invalida API/WS tokens e sessão; verificar sessão antiga recusada.
6. Salvar logs redigidos, image IDs, SHA, versões, sequência de status HTTP/MCP e checks de mounts. Encerrar e remover containers, rede, volume DIND e diretório scratch; confirmar que não restaram nomes/volumes/fixtures do ensaio no Engine 29 do host.

**Etapas herdadas da refatoração de senha única (§1.2).** Executar em conjunto com os itens
1–6 acima, no mesmo daemon 27.5.1 e na mesma fixture descartável; registrar resultado
separado por item.

- **P2-B (A2 — negação de admin remoto):** com `tools.mcpDocker.allowRemoteAdmin=false` (default), repetir uma mutação autenticada a partir de uma origem não-loopback e confirmar recusa; repetir a mesma mutação em loopback e confirmar sucesso; chamar o endpoint de bootstrap de admin por origem não-loopback e confirmar recusa. Verificar que o valor real da credencial nunca aparece na resposta.
- **P2-C (A3 — túnel e proxy TLS):** repetir login e leitura autenticada através de um proxy TLS local representativo do da VPS, com `Secure`/cookie de sessão; confirmar renovação de token nesse caminho; inspecionar logs de acesso e o payload de mutação para garantir ausência de senha, token ou hash em URL, query, cabeçalho persistido e log.
- **P2-D (A4 — renovação, expiração e revogação):** forçar expiração do TTL de token (300 s por padrão, ou valor da configuração do candidato) e confirmar rejeição de novas requisições; com um WebSocket aberto no momento da revogação, confirmar que operações em curso ou subsequentes são recusadas; executar logout e confirmar encerramento da elevação e recusa da sessão anterior.
- **P2-E (A5 — senha criada e alterada):** criar a senha pelo `nanobot auth init` e depois alterá-la pelo comando de troca suportado no CLI; autenticar com a senha nova; confirmar que a anterior deixa de autenticar; inspecionar `config.json` e os arquivos WebUI em busca de qualquer segredo humano e confirmar ausência; confirmar ausência de senha ou token em `localStorage`, `sessionStorage`, cookie de sessão legada e URL.
- **P2-F (A7 — cutover da instância real, só após P2 aprovado):** em ambiente privado e com autorização específica do operador, identificar o volume e os arquivos de credenciais da instância real sem exibir conteúdo, registrar revisão do verificador e cópias privadas do estado necessário para retorno; o operador fornece a senha nova interativamente, sem registrá-la em plano, CI, chat ou histórico de shell; se o ensaio final falhar, restaurar a combinação inteira imagem/configuração/credenciais anteriores e registrar a falha antes de nova tentativa.

**Critério de conclusão:** o teste demonstra no Server 27.5.1 completo que a elevação da UI autentica uma operação MCP reversível via broker, com token humano separado do broker e sem mutação em estado real, e que A2–A5 foram exercitados com resultado registrado. Se o DIND não permitir a topologia aprovada ou o broker rejeitar Server 27.5.1, registrar a divergência e parar; não relaxar o gate.

### P3 — GitHub Actions no SHA final

**Responsáveis:** operador autentica `gh`; agente inspeciona evidências. **Dependência:** snapshot commitado e push para o candidato exato.

1. Pré-condição: `gh auth status` autenticado na conta autorizada. O push SSH já demonstrou acesso Git, mas não autentica o GitHub CLI.
2. Consultar, por SHA, os runs existentes de `ci.yml`, `kg-platform.yml` e demais workflows aplicáveis ao commit final do `nanobot`. Conferir `headSha` e job results; não considerar verde um run de outro SHA.
3. Se um workflow obrigatório não foi acionado, verificar o evento suportado no próprio YAML. Só usar `gh workflow run` para workflow que declare `workflow_dispatch` e cuja execução seja necessária; registrar URL, SHA e conclusão. Não editar workflows durante o gate sem revalidar os checks locais.
4. Baixar/inspecionar os artefatos que o workflow realmente publica (manifest/SBOM/scan); não alegar existência se o job não os gerar. O repo SPA não tem Actions configuradas: seus gates remotos permanecem inexistentes, portanto registrar somente `bun test/lint/build` local.

**Critério de conclusão:** todos os jobs obrigatórios do Percival passam no SHA final publicado; qualquer ausência, falha ou workflow sem disparo fica explicitamente aberta e não é substituída por teste local.

### P4 — Inventário read-only e gate VPS

**Responsáveis:** operador fornece/seleciona o host; agente prepara relatório e executa somente os passos autorizados. **Dependência:** P2 aprovado e VPS identificado.

1. Antes de conectar, confirmar hostname/alias SSH, conta, projeto Compose, diretório persistente, proxy TLS, janela, responsável operacional e se o alvo é staging descartável ou deployment ativo. Registrar backup/retorno esperado. A autorização geral para prosseguir não identifica, por si só, um destino remoto.
2. No primeiro acesso, executar apenas `scripts/percival-vps-inventory.sh` em modo read-only. Capturar separadamente Client/Server, data-root, socket/GID, submounts, portas, proxy e existência de diretórios; não transferir `.env`, config, token, `docker inspect` integral ou valores de secrets para relatório versionado.
3. Comparar Server.Version ao gate 27.x, bind/TLS, mount/GID/UID, Compose, persistência e protected paths com o plano F0/F7. Se qualquer requisito não bater, parar e pedir uma decisão; não usar Engine 29 como substituto nem editar mounts/firewall do host.
4. Se o alvo aprovado for **staging**, provisionar um projeto e volume descartáveis em porta privada, transferir apenas imagens candidatas fixadas e repetir o ensaio gateway+broker+WebUI/MCP, incluindo restart/recreate e rollback do próprio fixture. Validar HTTPS/proxy apenas com configuração representativa aprovada; não colocar senha/token em URL/log.
5. Não migrar o volume real `~/.nanobot`/`.percival`, não atualizar servidores MCP reais e não iniciar cutover de produção como parte do smoke. Isso exige plano de retorno próprio, backup verificado, inventário e confirmação específica do operador imediatamente antes da escrita.

**Critério de conclusão:** inventário datado e redigido, Engine 27.x demonstrado, staging end-to-end aprovado e relatório de VPS separado do aceite local. Se não houver hostname/acesso ou staging, o gate permanece bloqueado por dependência externa.

### P5 — Consolidação e handoff

1. Atualizar a seção de execução deste plano e o plano arquivado da refatoração de senha única (`closed/2026-10-11-percival-single-password-auth-refactor-plan.md`, sem reabertura) com SHAs, `SOURCE.json`, image IDs, `Server.Version`, comandos, URLs de Actions, resultados, skips, warnings e limites, marcando cada item A1–A9 da §1.2 como fechado ou ainda aberto.
2. Atualizar o quadro F7 apenas nos itens cobertos por evidência; separar `local source/browser`, `DIND Server 27`, `GitHub Actions`, `VPS staging` e `production cutover`. Não declarar release-ready sem B13.
3. Revisar `git status`, `git diff --check`, branch/remotes e commits; commit/push dos resultados de source snapshot/docs/test harness em commits Conventional Commits separados. Nenhuma tag/release/publicação autorizada.
4. Declarar concluído somente se P1–P4 alcançarem seus critérios. Caso um gate remoto permaneça bloqueado, entregar o restante com o blocker, dono e próxima ação explícitos.

## 3. Critérios globais de parada

- Server 27.x não fica comprovado pelo campo Client.Version, tag da imagem ou CI antigo; verificar `docker version` dentro do daemon sob teste.
- Não permitir ao broker DIND acesso ao Docker socket externo; somente o socket interno do DIND descartável.
- Não prosseguir se fixture, token, volume ou porta colidir com recursos existentes; names/volumes devem ser únicos e preflightados.
- Não efetuar escrita em VPS enquanto host, estado alvo e retorno não estiverem definidos e o primeiro inventário não passar.
- Não imprimir ou versionar segredos/estado MCP real; a senha usada no rehearsal é fixture efêmera.
- Preservar `remote_auth_required` no SSH browser-proxy nesta closure.

## 4. Dependências atuais e próxima ação

1. **Engine 27 local:** a imagem DIND 27.5.1 pinada está disponível e o harness F1 já comprovou um MCP em daemon descartável. O trabalho novo é compor esse daemon com as imagens gateway/broker do candidato e o fluxo de login/elevation.
2. **Actions:** operador precisa autenticar o GitHub CLI; a sessão atual não tem `gh` login.
3. **VPS:** ainda é necessário identificar/confirmar host e ambiente de staging; há somente um roteiro de inventário read-only, sem destino fornecido neste baseline.
4. **Proveniência:** um worktree temporário de `spa` em `8e4ff73` evita os arquivos locais não rastreados e permite gerar `SOURCE.json` com `dirty=false`.
5. **Itens herdados ainda sem qualquer evidência:** A2 (negação de admin remoto), A3 (proxy TLS), A4 (expiração/revogação em sockets abertos) e A5 (senha criada **e alterada** pelo operador) não possuem nenhum ensaio registrado — nem local nem em DIND. Ficam agrupados em P2-B..P2-F para que não sejam perdidos junto com o arquivamento do plano de origem.

**Próximas ações:** o operador executará P2 posteriormente no DIND Docker Server 27.5.1 conforme o harness e os critérios acima; autenticar `gh` antes de P3; retomar P4 somente quando um VPS/staging for disponibilizado e identificado. Nenhuma alteração de compatibilidade do broker, escrita remota ou deployment real está autorizada por este registro.
