# Plano de fechamento — autenticação de senha única e aceite Docker/VPS

> **Arquivado por consolidação em 2026-10-25, a pedido de bill.** AUTH-A1–A6 →
> [Plano 1, L03](../2026-10-25-01-product-readiness-plan.md); AUTH-A8/CI →
> [Plano 2, D03](../2026-10-25-02-qualification-distribution-plan.md);
> AUTH-A7/cutover e A9/VPS → [Plano 3, O06/O03/O08](../2026-10-25-03-deployment-operations-plan.md).
> P2 continua adiado; nenhuma pendência foi executada ou aceita por esta transferência.
> O restante é histórico/especificação; a precedência corrente e o mapa integral estão
> no [registro de consolidação](../../reports/2026-10-25-three-plan-consolidation.md).

- **Preparado em:** 2026-10-11; plano solicitado antes de retomar os gates pendentes.
- **Estado:** P0 concluído para fixação do candidato e preparação; P1 concluído e snapshot publicado em `d3b29843`. P2 adiado pelo operador; P3 aguarda autenticação do GitHub CLI; P4 aguarda seleção de VPS/staging. Closure global permanece aberta. Em 2026-10-23 as pendências A1–A9 foram reverificadas contra o código: **nenhum item foi executado**, mas os mecanismos de A2, A4 e A5 já existem no código e o baseline de Docker/`gh` estava desatualizado (§1 e §1.2). Ver
  [auditoria planos × código](../../reports/2026-10-23-auditoria-planos-vs-codigo.md) §3.5. Desde 2026-10-23 este plano também é o **único dono das pendências de aceite** da refatoração de senha única, cujo plano foi arquivado em `closed/` (ver §1.2).
- **Objetivo:** fechar a proveniência do KG SPA embutido, a integração gateway+broker
  em Docker Server 27.x e os gates Actions/VPS de senha única, com persistência e
  deployment compatíveis com o [plano de integração IaC](2026-10-23-iac-alignment-execution-plan.md).
- **Autoridade:** o operador autorizou prosseguir com as pendências. Essa autorização não converte Engine 29.x em Engine 27.x, não autoriza enfraquecer o gate do broker, não seleciona um VPS ainda não identificado e não autoriza tag, release, publicação ou cutover de dados MCP reais.
- **Fora de escopo nesta closure:** implementar o login interativo do browser-proxy SSH remoto. Por decisão do operador, ele permanece fail-closed (`remote_auth_required`) e deve ser acompanhado como trabalho separado.
- **Reconciliação 2026-10-25:** [continuidade Docker](2026-10-25-docker-standardization-continuation-plan.md)
  coordena os resíduos do plano F0–F8 agora arquivado. D1–D12/F7 estão fechados;
  A1–A9 abaixo continuam sob este dono. I2 e ensaios D9 provam partes do runtime,
  não o fluxo integrado de autenticação P2 nem o cutover real P2-F. C1 tem snapshot
  posterior em F5/C1, sem aceite remoto; tabelas de baseline antigas são datadas.
- **Plano de implementação de referência (arquivado):** [refatoração de senha única](2026-10-11-percival-single-password-auth-refactor-plan.md); implementação A–E e evidências preservadas, pendências em §1.2. Donos ativos: F7 no [fechamento Docker](2026-10-23-fechamento-padronizacao-docker-f4-f5-f7-plan.md), CI/VPS em C1–C4 do [plano integrado](2026-10-23-integracao-pendencias-kg-e-mcp-docker-plan.md) e contratos/distribuição em [I1–I9](2026-10-23-iac-alignment-execution-plan.md). Os planos arquivados são origem histórica, não donos concorrentes.

## 1. Baseline observado

| Item | Estado verificado | Consequência |
| --- | --- | --- |
| Percival | `nanobot/main` em `d773f8b5`, sincronizado com `origin/main`, working tree limpa. | SHA base para o próximo snapshot/CI. |
| Fonte SPA | `spa/main` em `8e4ff73`, commitado e sincronizado. Permanecem arquivos locais não rastreados preexistentes (`.positronic/`, `AGENTS.md`, `scripts/dev-spa.sh` e testes auxiliares); não fazem parte do código commitado. | Não usar o working tree atual para declarar proveniência limpa. Construir de um worktree temporário no SHA commitado. |
| Snapshot KG | Baseline anterior registrava `revision=f607d6a`, `dirty=true`; atualizado em P1 para `revision=8e4ff73fbe8d9f9966cf6853cca679b4e14e72de`, `dirty=false`, com hashes consistentes e commit Percival `d3b29843` publicado. | P1 concluído; browser gate real passou. |
| Docker disponível | Contexto ativo `default`: Client/Server **29.9.1** (o baseline de 2026-10-11 registrava 29.7.2). Contexto `desktop-linux` não tem daemon disponível. O broker recusa Server 29.x quando `allow_engine29=false`. | Não repetir gateway+broker diretamente no Engine ativo. Não alterar o gate de compatibilidade. A divergência entre 29.7.2 e 29.9.1 reforça que o host local não é o alvo do gate. |
| Engine 27.x descartável | Imagem `docker:27.5.1-dind` no digest `sha256:aa3df78ecf320f5fafdce71c659f1629e96e9de0968305fe1de670e0ca9176ce` está disponível. `scripts/percival-f1-engine27-validate.sh` já a usa para provar o broker/fixtures no daemon 27.5.1, mas não exercita a nova autenticação WebUI com gateway+broker juntos. | Reutilizar a imagem e os controles do harness existente; estender o ensaio com uma fixture de senha e operação autenticada. |
| Fixtures Docker MCP | Os aliases `percival-f1-*`/`percival-f2-*` não aparecem na lista atual de imagens locais. | Confirmar os repositórios-fonte e construir/carregar fixtures a partir dos commits fixados em `scripts/percival-f2-build-fixtures.sh`, antes do ensaio; não puxar tags mutáveis durante a execução. |
| GitHub Actions | **Reverificado em 2026-10-23:** o `gh` está instalado (2.102.1) e responde "You are not logged into any GitHub hosts"; o atalho `~/.local/bin/gh` falha antes disso porque o mise recusa `~/.config/mise/config.toml` como não confiável. `nanobot` possui `ci.yml`, `kg-platform.yml` e `tui-release.yml`; o repo `spa` não possui `.github/workflows/`. | O bloqueio é **autenticação**, não instalação. Ação: `gh auth login` na conta autorizada (ou `mise trust` para usar o atalho). Runs remotos não podem ser inspecionados até lá. Não afirmar gate SPA remoto inexistente. |
| VPS | O plano F0/F7 requer inventário real e Engine Server 27.x, mas este baseline não identifica hostname, acesso SSH, projeto Compose nem volume-alvo. Em 2026-10-23 confirmou-se que `~/.percival` não existe. | Começar com inventário read-only; solicitar/confirmar o destino e ambiente de staging antes de qualquer escrita remota. |

## 1.1 Execução P0/P1 — 2026-10-11

- **P0:** Percival confirmado em `d773f8b5e9ec53fbecee4c8df0aa2efdbe6bfdc0` antes do rebuild e SPA em `8e4ff73fbe8d9f9966cf6853cca679b4e14e72de`; ambos alinhados com `origin/main`. Digest local `docker:27.5.1-dind` confirmado como `sha256:aa3df78ecf320f5fafdce71c659f1629e96e9de0968305fe1de670e0ca9176ce`. SHAs Weather `b5032f4fe4f0e89cc49556b62725ba598fb1c181` e OSM `ca3c3977fc124b649876900fc0c3ffb6fe7c87fb` existem nos clones locais. Checksums dos Dockerfiles: gateway `75dbfc7f79ce9c3ac4a4a8736aeb39e9c8f8d93a118810ca69e86533a28c0500`; broker `a5ba02a4939a16ac53bb54821cb5f1aa66f26831f9627ecb2901516fd599add5`. O harness F1 revisado usa `--network none`, não monta socket Docker do host e verifica ausência de caminhos diretos ao daemon no container MCP. O Engine ativo permanece 29.7.2; nenhum DIND foi iniciado nesta execução. Imagens gateway/broker locais preexistentes foram observadas (IDs `sha256:e78ae8c2c3e0e138984516bb8ef33591219d7febcc43602890334277eb520d3c` e `sha256:f222d8958c0fbace05075ebba0de53575826fc7c29362918c70c0593d4a77004`) e não são declaradas candidatas de P2.
- **P1:** worktree detached em `/home/bill/.positronic/runtime/tmp/opencode/spa-auth-clean-8e4ff73`, árvore limpa no SHA indicado. `bun install --frozen-lockfile`, `bun run test` (**250 passed / 36 arquivos**), `bun run lint` e `bun run build` passaram. O build mantém aviso de chunk principal acima de 500 KB (1.37 MB raw; 456 KB gzip). `uv build --sdist` com rebuild forçado e `uv build --wheel` de snapshot prebuilt passaram. `SOURCE.json` confirma `dirty=false`, lock SHA-256 `1a10d3716ef28bac480cad7f36a0f26e009d0c8342a486af636bb6fa207f4dcf`, hashes dos assets e index consistentes; os JS gerados não contêm `kg-gateway-secret` nem `X-Nanobot-Auth`. Testes `tests/kg/test_bundle.py tests/kg/test_f7_browser.py`: **5 passed, 1 skipped**; skip esperado do teste de paridade do core sem `PERCIVAL_KG_CORE_SOURCE`; Chromium executou e passou o login/browser gate. Commit separado `d3b29843` (`build(kg-spa): refresh snapshot from clean auth source`) foi enviado a `origin/main` (`d773f8b5..d3b29843`).
- **Escopo/limites:** P2 não foi executado, conforme decisão do operador; P3 não executado porque `gh` não está autenticado nesta máquina. P4 não executado: não há VPS/staging disponível. Nenhum Engine DIND, fixture, serviço MCP, estado persistente ou credencial real foi usado neste aceite.

## 1.2 Etapas herdadas da refatoração de senha única — 2026-10-23

- **Origem:** [plano de refatoração de senha única](2026-10-11-percival-single-password-auth-refactor-plan.md), arquivado em 2026-10-23 com transferência integral das pendências para este plano. As etapas de implementação A–E (contrato compartilhado, núcleo do gateway, administração MCP, clientes, empacotamento/documentação) e os gates locais de 2026-10-11 (`pytest` 9348 passed / 49 skipped, `basedpyright nanobot` 0 erros, `ruff check .` limpo, SPA `251 passed` com lint e build, snapshot KG de fonte limpa `8e4ff73` publicado em `d3b29843`) permanecem como evidência encerrada. O plano arquivado **não** é reaberto.
- **Regra:** toda pendência abaixo é executada e evidenciada **neste** plano. Nenhuma delas se fecha por teste local, pelo campo `Client.Version`, por tag de imagem ou por ausência de runs. O plano arquivado exigia que os gates finais e o ensaio produzissem evidência antes de declarar a refatoração implementada; essa exigência passa a valer para P2–P4 aqui.

| # | Pendência herdada | Critério de aceite | Onde é executada | Estado |
| --- | --- | --- | --- | --- |
| A1 | Ensaio integrado gateway+broker em imagem Docker com volume limpo, incluindo elevação, mutação MCP reversível e auditoria sem senha | `docker version` **dentro** do daemon = Client 27.5.1 / Server 27.5.1; elevação pela UI executa a operação via broker; token humano distinto do token do broker; nenhuma mutação em estado real | P2 (itens 1–6) | **aberto** — adiado pelo operador. Mecanismos já no código: `nanobot/cli/auth.py:50` (`init`), `:77` (`change`), `:111` (`reset`), `:145` (`status`); falta o ensaio em 27.5.1 |
| A2 | Negação de acesso remoto quando `allowRemoteAdmin=false` | Mutação por WebSocket com sessão autenticada/elevada de origem não-loopback é recusada; a operação equivalente em loopback funciona. Sem reutilizar credencial/endpoint legado operator-admin | P2-B | **aberto** — default false e verificação de origem/elevação implementados em `nanobot/webui/settings_routes.py:397–421`. Falta ensaio real por origem. O antigo operator-bootstrap não faz parte das actions aceitas; não exigir um endpoint removido |
| A3 | Acesso por túnel e por proxy TLS representativo de VPS | Login e renovação funcionam atrás de proxy TLS com sessão; senha somente no request de login/elevação permitido, nunca em URL/storage/log ou payload de mutação MCP. Tokens só nos campos de autenticação suportados; sem persistência indevida | P2-C e P4 item 4 | **aberto** — sem ensaio registrado; P2-C abaixo define a fixture e P4 a extensão no alvo |
| A4 | Renovação e expiração de token, e revogação em WebSockets já abertos | Renovação silenciosa pela sessão; expiração rejeita novas requisições **e** encerra ou recusa operações nos WebSockets abertos; logout encerra a elevação | P2-D | **aberto** — mecanismo **parcial**: emissão com TTL e expiry existe (`nanobot/webui/gateway_tokens.py:79`-`:91`, com purge em `:71`) e há verificação de expiração para reaping de sockets (`nanobot/webui/gateway_auth.py:126`). **Não localizei renovação silenciosa da credencial de sessão** no código auditado; se ela não existir, "renovação silenciosa" é trabalho de engenharia, não só de evidência. Confirmar antes de P2-D |
| A5 | Senha criada e **alterada** pelo operador, sem recadastro | `nanobot auth init` e a troca de senha concluem no CLI; login com a senha nova; rotação anterior deixa de autenticar; nenhum segredo humano em `config.json`, arquivo WebUI, URL ou storage do navegador | P2-E | **aberto** — o comando de troca existe (`nanobot/cli/auth.py:77`, `auth change`); falta o ensaio de rotação com a senha antiga deixando de autenticar |
| A6 | Recriação de contêiner mantendo volume, e Compose após o corte | Mesmo volume e login sem recadastro; broker continua segregado; gateway sem socket nem CLI Docker; estado MCP, CAS e logs redigidos conferidos | P2 item 5 (recriar) e P5 | **aberto** — será exercitado em P2; não confundir roteiro com execução nem apenas persistência I2 com prova completa de login |
| A7 | Cutover da instância real com backup e retorno preservados | Identificar volume e arquivos de credenciais **sem exibir conteúdo**; cópia privada do estado anterior; se o ensaio final falhar, restaurar a combinação **inteira** imagem/configuração/credenciais em ambiente privado, sem executar binário antigo sobre estado parcialmente convertido | P2-F | **aberto** — a execução de 2026-10-11 usou estado descartável |
| A8 | GitHub Actions no SHA final | Jobs obrigatórios verdes no SHA publicado, com `headSha` conferido; artefatos baixados e confrontados com fonte, locks e digests | P3 | **bloqueado/pendente em C1** — [F5/C1](2026-10-25-f5-c1-remote-ci-closure-plan.md) registra Actions core indisponível e acesso autenticado ausente para logs/artifacts. Fixar SHA final atual; não repetir baseline d773f8b5 como candidato |
| A9 | Inventário read-only e gate VPS | Inventário datado e redigido, Engine 27.x demonstrado, destino/persistência definidos por I4/C2, staging end-to-end aprovado; relatório separado do aceite local e da publicação | P4, compartilhando C2–C4 | **bloqueado** — sem host/staging identificado; ausência de `~/.percival` não determina o layout IaC final |

**Fora de escopo herdado:** o login interativo do browser-proxy SSH remoto permanece fail-closed
(`remote_auth_required`) e não é reaberto por esta transferência.

## 1.3. Handoff para a IaC — revisão de planejamento 2026-10-23

- O ensaio local P2 continua descartável e não espera namespace/registry/host real.
  Gateway/manager e broker já existem; preservar autenticação, CAS e fronteira do
  socket, sem tratar a integração IaC como motivo para reimplementar o broker.
- P3/A8 e C1 verificam conformance remota do candidato; o CI de release/push/pull
  anônimo é I3, com B13 próprio. Usar Docker Hub como alvo não autoriza divulgar o
  repositório privado, seus commits ou credenciais.
- I2/I4 devem disponibilizar CLI de `auth init/change/status` no mesmo contrato de
  imagem e volume de runtime. O bootstrap não cria senha default nem copia a
  credencial real da máquina de desenvolvimento; o operador fornece-a pela interface
  suportada, e a aplicação deve ler os arquivos de secret realmente montados.
- I4/C2 mapeiam o estado atual `~/.nanobot` e a proposta histórica `.percival` para
  `/srv/pblabs/` ou destino homologado. `/home/nanobot/.nanobot` continua o path interno
  até migração explícita. P4/P2-F não renomeiam nem fragmentam estado automaticamente.
- Verificador de senha, token de emissão e token broker persistem em paths protegidos
  fora de imagens/locks públicos; `deployment.lock` e `capabilities.lock` registram
  identidades/versões/status, nunca seus valores. I8 cobre backup privado/restauração
  da combinação imagem/configuração/auth/dados, além do rollback da fixture MCP.
- P2/A6 deve provar que o login e a auditoria continuam após recriar gateway **e**
  sidecar no namespace compartilhado. Testar não-root/ownership efetivos, sem usar
  `chmod 777` ou UID presumido para resolver falhas de persistência.
- Para instalação pública em P4, consumir receita por tag+digest e imagens I3
  homologadas; build/save/load de P2 é só rehearsal. `--pull=never` do spawn atual não
  é modificado pelo teste de senha; aquisição por catálogo é trabalho I1/I6.
- Aceites de autenticação, F7 local, IaC I9, VPS e publicação permanecem distintos.
  Esta revisão não fecha A1–A9 nem modifica o contrato de senha.

## 2. Estratégia e ordem de execução

### P0 — Fixar candidatos e fronteiras

**Responsável:** agente, em modo read-only.

1. Registrar `nanobot` HEAD/remote e `spa` HEAD/remote; validar que o candidato é `d773f8b5` e a fonte SPA é `8e4ff73` ou commits posteriores explicitamente aprovados.
2. Confirmar o digest do `docker:27.5.1-dind`, os checksums dos Dockerfiles/imagens gateway e broker e os SHAs das fixtures Weather/OSM. Confrontar com os pins já registrados em F1/F2; não reutilizar uma imagem somente pelo nome de tag.
3. Definir scratch novo e descartável para checkout SPA, estado, token broker, logs
   redigidos e Compose. Não montar `~/.nanobot`, `~/.percival`, `~/.positronic`,
   `/srv/pblabs/` real ou outro volume/segredo de instalação no ensaio.
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

- **P2-B (A2 — negação de admin remoto):** com `tools.mcpDocker.allowRemoteAdmin=false`, repetir mutação via WebSocket com sessão válida/elevada de origem não-loopback e confirmar recusa; repetir equivalente em loopback e confirmar sucesso. Confirmar que rota/action legada de operator-bootstrap não concede acesso e nenhuma resposta revela credencial. O teste usa a senha única atual, não operator-admin separado.
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

**Responsáveis:** operador fornece/seleciona o host; agente prepara relatório e executa
somente os passos autorizados. **Dependência:** P2 aprovado e VPS identificado.
Inventário compartilha C2; antes de provisionar staging, adotar o contrato I4 e o
candidato aprovado. Para deployment público, exigir imagem homologada I3 e os ensaios
locais de recuperação I8. Não esperar a publicação para fazer inventário read-only.

1. Antes de conectar, confirmar hostname/alias SSH, conta, projeto Compose, diretório persistente, proxy TLS, janela, responsável operacional e se o alvo é staging descartável ou deployment ativo. Registrar backup/retorno esperado. A autorização geral para prosseguir não identifica, por si só, um destino remoto.
2. No primeiro acesso, executar apenas `scripts/percival-vps-inventory.sh` em modo read-only. Capturar separadamente Client/Server, data-root, socket/GID, submounts, portas, proxy e existência de diretórios; não transferir `.env`, config, token, `docker inspect` integral ou valores de secrets para relatório versionado.
3. Comparar Server.Version ao gate 27.x, bind/TLS, mount/GID/UID, Compose, persistência
   e protected paths com I4/C2 e os contratos F0/F7. Registrar o destino absoluto real,
   não inferi-lo do nome `.percival`. Se divergir, pedir decisão; não usar Engine 29
   como substituto nem editar mounts/firewall do host.
4. Se o alvo aprovado for **staging**, usar projeto/volume descartáveis e porta privada.
   Consumir a receita I4 e imagens candidatas por digest verificadas (I3 no fluxo
   público), sem build na VPS; repetir gateway+broker+WebUI/MCP, restart/recreate,
   persistência de login e rollback da fixture. Validar HTTPS/proxy representativo;
   não colocar senha/token em URL/log nem avançar lock de deployment em falha.
5. Não migrar o volume real `~/.nanobot`/`.percival`, não atualizar servidores MCP reais e não iniciar cutover de produção como parte do smoke. Isso exige plano de retorno próprio, backup verificado, inventário e confirmação específica do operador imediatamente antes da escrita.

**Critério de conclusão:** inventário datado e redigido, Engine 27.x demonstrado, staging end-to-end aprovado e relatório de VPS separado do aceite local. Se não houver hostname/acesso ou staging, o gate permanece bloqueado por dependência externa.

### P5 — Consolidação e handoff

1. Atualizar o registro **deste** plano com SHAs, `SOURCE.json`, image IDs/digests,
   `Server.Version`, comandos, URLs de Actions, resultados, skips/warnings e limites;
   marcar A1–A9 com evidência. O plano arquivado permanece snapshot e aponta para este
   dono ativo, sem reescrever sua execução passada.
2. Atualizar a projeção de autenticação no plano de continuidade apenas com evidência;
   separar `local source/browser`, `DIND Server 27`, `GitHub Actions`, `VPS staging`
   e `production cutover`. F7/D12 arquivado preserva o aceite local com ressalvas,
   sem nova assinatura presumida. Não declarar release-ready sem B13.
3. Revisar `git status`, `git diff --check`, branch/remotes e commits; preparar resultados
   separados de snapshot/docs/harness. Commit/push só quando explicitamente solicitados;
   nenhuma tag/release/publicação é autorizada pelo fechamento deste plano.
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
2. **Actions:** o `gh` está instalado (2.102.1) e sem login; a ação é `gh auth login`, não instalar o CLI. O atalho `~/.local/bin/gh` exige `mise trust` para `~/.config/mise/config.toml`.
3. **VPS:** ainda é necessário identificar/confirmar host e ambiente de staging; há somente um roteiro de inventário read-only, sem destino fornecido neste baseline.
4. **Proveniência:** um worktree temporário de `spa` em `8e4ff73` evita os arquivos locais não rastreados e permite gerar `SOURCE.json` com `dirty=false`.
5. **Itens herdados ainda sem qualquer ensaio registrado:** A2 (negação de admin remoto), A3 (proxy TLS), A4 (expiração/revogação em sockets abertos) e A5 (senha criada **e alterada** pelo operador) não possuem nenhum ensaio — nem local nem em DIND. Ficam agrupados em P2-B..P2-F para que não sejam perdidos junto com o arquivamento do plano de origem.
6. **Resultado da reverificação de 2026-10-23:** o que falta a A2 e A5 é **evidência de execução**, não engenharia — os mecanismos existem e são fail-closed. A4 é a única dos três em que a auditoria encontrou **mecanismo incompleto** (renovação silenciosa não localizada), e por isso exige confirmação antes do ensaio.

**Próximas ações:** o operador executará P2 posteriormente no DIND Docker Server 27.5.1 conforme o harness e os critérios acima; autenticar `gh` antes de P3; retomar P4 somente quando um VPS/staging for disponibilizado e identificado. Nenhuma alteração de compatibilidade do broker, escrita remota ou deployment real está autorizada por este registro.
