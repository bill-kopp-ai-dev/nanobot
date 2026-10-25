# Manual de operação e manutenção — MCP Docker Percival

- **Revisado em:** 2026-10-24 UTC; revisão 0.2 (D9).
- **Escopo:** procedimentos de operação, atualização, rollback, incidente, revisão e retenção para os servidores MCP Docker que o Percival consome (Notes, AgentMail, Weather, Khan Calendar, OSM e Deep Research) e para o gateway/broker. Este manual **não** substitui o [runbook de migração de estado `~/.nanobot`→`~/.percival`](../mcp-docker-f5-runbook.md), apenas convive com ele.
- **Autoridade:** qualquer mutação real (instalar/atualizar/rollback/parar/remover) exige a interface suportada do gestor correspondente e a aprovação específica do operador. Nada aqui é executado implicitamente.
- **Estado da padronização:** o documento nasce no fechamento F7. Os contratos F0–F5 que ele referencia estão registrados no [plano de padronização](../plans/2026-10-09-docker-standardization-refactor-plan.md) e no [plano de fechamento F7](../plans/closed/2026-10-10-f7-operations-acceptance-closure-plan.md).

## 1. Princípios

1. **Identidade antes da ação.** Toda mutação começa registrando `source SHA`/`worktree`, `image ID`/`RepoDigest`, alias/tag, labels `percival.mcp-docker.{owner,managed-by,server-id,instance-id}`, configuração, mounts/UID/GID, revisão atual, e o dono (Percival ou Positronic). Esses dados vão para o relatório de operação ou para a trilha de auditoria do gestor; nada vai para a composição da operação em si.
2. **Pin imutável.** O broker fixa imagens por ID/RepoDigest e usa `--pull=never`. Tags mutáveis (`:dev`, `:f3`, `:f7`) são alias de diagnóstico e não podem ser o identificador de execução. Promoção = novo image ID imutável, com alias humano atualizado em paralelo.
3. **Privilégio mínimo do broker.** O gateway e os MCPs não recebem `docker.sock`/CLI. Apenas o broker fala com o daemon. Limites efetivos de mount/rede e modelo de acesso ao host seguem B14–B25; este manual não os reescreve nem os afrouxa.
4. **Stdio e HTTP são contratos diferentes.** Stdio: stdout só JSON-RPC, sem TTY, sem porta, sem healthcheck HTTP. HTTP: profile/serviço dedicado, bind loopback por padrão, opt-in para exposição. Não usar uma única receita para os dois.
5. **Init único.** Apenas um `init: true` ou tini embutido por processo. Stdio usa `stdin_open: true`/`tty: false` e `docker run --init`. Duplo init cria falsa camada de supervisão.
6. **Reversibilidade antes de eficiência.** Toda operação destrutiva exige plano de retorno próprio, autorização específica e janela. `docker system prune`, `docker rm -f` cego e `docker image prune -a` são proibidos.
7. **Sem segredos em artefatos.** Inventário, logs e inventários redigem env, tokens, e o conteúdo integral de `docker inspect`. Apenas a estrutura e os labels são registrados.

## 2. Posições de execução

| Posição | Função | Bind/estado | Escrita e exposição |
| --- | --- | --- | --- |
| Gateway Compose | Gateway/WebUI e manager | Health em `127.0.0.1:18790/health`; estado em `~/.nanobot` | Um writer do estado; loopback por padrão, exposição exige decisão própria |
| API (`--profile api`) | API alternativa ao gateway | Health em `127.0.0.1:8900/health`; mesma raiz `~/.nanobot` | Iniciar em lugar do gateway, nunca como segundo writer simultâneo; requests protegidos exigem bearer API distinto da senha da instância |
| Broker MCP (sidecar) | Único cliente do Docker Engine | `127.0.0.1:18081` no namespace do gateway (`network_mode: service:nanobot-gateway`) | Token privado; sem porta publicada no host |
| Containers `percival-mcp-*` | MCPs gerenciados pelo Percival | Stdio sob demanda; sem porta publicada | Um init fornecido pelo gestor; nenhum healthcheck HTTP para stdio |
| Containers Positronic (sem label Percival) | MCPs gerenciados pelo Positronic | Conforme o runtime do Positronic | São outro owner; não operar pela configuração Percival |

CLI, gateway e API usam o bind de estado inventariado do mesmo deploy. **Somente um processo escritor** (gateway ou API) pode operar por vez. A API é um modo alternativo, não um segundo serviço a iniciar ao lado do gateway. `docker.sock` está montado apenas no broker. `nanobot auth init` cria o verificador em `~/.nanobot/auth/`; isso permite autenticação humana da WebUI, mas não configura provider nem prova readiness do modelo. A API exige sua própria chave para rotas protegidas; não reutilizar a senha humana. O antigo `PERCIVAL_DOCKER_GATEWAY_TOKEN_ISSUE_SECRET_FILE` foi removido.

## 3. Procedimentos por cenário

### 3.1 Inventário seguro antes de agir

- Usar `python -m nanobot.mcp_docker.inventory --format json` (ou `markdown`) no
  ambiente Python do Percival para capturar identidades, transporte e referências
  sem consultar `Config.Env`. O inventário preserva os esquemas
  `percival.mcp-docker.*` e `io.positronic.*`; `io.positronic.run` identifica a
  encarnação Positronic. Labels de build distinguem worktrees dirty; overrides
  Compose são referências declaradas, não prova de qual imagem está em execução.
- Ler `~/.nanobot/config.json` para o estado Percival e `~/.positronic/mcp/registry.json` + `~/.positronic/mcp/servers/<id>.json` para Positronic.
- Executar `docker ps --no-trunc --format '{{.ID}} {{.Names}} {{.Image}} {{.CreatedAt}}'` e cruzar com a lista de servidores do registry/config. Containers sem pai vivo ou sem label são órfãos (ver §3.7).
- `docker image inspect <id> --format '{{ index .Config.Labels "org.opencontainers.image.revision" }} | {{ index .Config.Labels "io.percival.build.source-diff-sha256" }}'` para confirmar a fonte da imagem.
- `git -C <repo> rev-parse HEAD; git -C <repo> status --short` em todos os repos de runtime envolvidos. Anotar a divergência.
- **Não imprimir** env, tokens, segredos ou o conteúdo de `Config.Env`/`Mounts`. Apenas os rótulos e paths públicos.


#### Exemplo de dry-run (fixture D9; sem mutação)

```text
mode: DRY-RUN — no manager action issued
owner: Percival (fixture `i2fixture`; confirm in manager before real work)
source: local fixture / synthetic images A and B
pin: image ID A → image ID B; revisions: reread from manager at execution time
transport: stdio; mounts/data: synthetic only; secrets: omitted
checks: MCP initialize → tools/list → safe ping; rollback image A retained
approval: not requested; next step: review plan, then request approval separately
```

This output is a planning record, not an authorization. For an HTTP-profile
operation, record bind/auth/probe separately and validate with an isolated HTTP
fixture; never infer MCP readiness from health alone.

### 3.2 Build de uma imagem

- Para o gateway/broker: `python scripts/percival-docker-build.py` no checkout Percival; passar `--worktree-candidate` quando a fonte incluir diff não commitado. Não usar `:dev` como release.
- Para os MCPs: `python scripts/percival-docker-build.py <service>` no checkout do MCP, com tag imutável `<semver>-<shortsha>`. Registrar `<semver>` de `pyproject.toml` e `<shortsha>` de `git rev-parse --short HEAD`. Falhar se o `0.0.0`/`unknown`/`local` aparecer.
- Pinar base/lock/canal conforme F3. Confirmar com `docker inspect <id>` que `org.opencontainers.image.{source,revision,licenses}` batem com o esperado.
- **Canais e extras entram no build.** `NANOBOT_CHANNELS` substitui o conjunto
  padrão (`whatsapp`): inclua todos os canais que a imagem deve habilitar. O
  build instala os channel-locks com `--require-hashes --no-deps`, valida o
  manifesto e roda `uv pip check`; pins conflitantes falham o build.
- **Imagens Docker são imutáveis em dependências.** Elas definem
  `NANOBOT_RUNTIME_PACKAGE_INSTALL=0`: o startup reporta canal ausente sem
  instalar e a WebUI recusa a instalação com 409 antes de alterar configuração.
  Para adicionar canal ou extra, reconstrua com `NANOBOT_CHANNELS` /
  `NANOBOT_EXTRAS` e promova a nova imagem. A instalação nativa continua
  disponível fora do Docker.
- **Auditar o contexto antes de promover:**
  `python scripts/check_docker_context.py --budget-bytes <bytes> --output <arquivo>`
  exporta o contexto efetivo pelo BuildKit, mede bytes e canários sintéticos de
  estado/segredo e falha se algum canário vazar ou exceder o orçamento. O
  arquivo de saída é evidência fora da fonte.
- Após o build, executar o smoke F1 (stdio) e, se aplicável, o profile HTTP. Para Khan, executar `khan_get_status` em fixture isolada para validar resposta, não apenas `tools/list`.

### 3.3 Atualização de servidor em Positronic

- Ler `mcp server show <id>` para revisão, `configurationId` e pin atual.
- Executar `mcp server update-image <id> <sha256:...>` com `expected_revision`. Após o update, o `configurationId` é invalidado; chamar `mcp server configure <id>` para reaplicar env/allowlist/escopo.
- Validar `tools/list` e um tool seguro de leitura (ex.: `khan_get_status`, `osm_get_health`, `weather_get_status`).
- Preservar o último image ID bom em uma fixture identificada, caso o rollback seja necessário (ver §3.5).

### 3.4 Atualização de servidor em Percival

- Confirmar que há exatamente um writer Percival para `~/.nanobot`: gateway Compose ou API alternativa. Não iniciar a API ao lado do gateway. `nanobot auth init` e `nanobot mcp-docker doctor` são passos de autenticação/diagnóstico, não autorização para mutar nem prova de MCP pronto.
- Pela UI/API autenticada suportada, abrir o detalhe do servidor e reler a revisão global, a revisão do servidor, o image ID e a configuração. Interromper se o CAS/configuração mudou desde a janela aprovada.
- Solicitar `update-image` com o image ID imutável e a revisão esperada. O gateway serializa a intenção; o broker executa a ação tipada e registra `preparing`→`committed`/`failed` em `transitions/<id>.json`. Não escrever `config.json`, transitions ou audit à mão.
- Verificar `initialize`→`tools/list` e uma chamada MCP de leitura segura pela mesma interface gestora. Ler `~/.nanobot/mcp-docker/audit.jsonl` (modo 0600), sem imprimir env/tokens, e reconciliar o resultado.
- Em falha, não inferir sucesso de health Docker. Preserve o pin A e use `update-image` para voltar ao ID A ou restore suportado de backup (com revisão/checksum/confirmação exigidos); depois repita handshake e chamada segura.

### 3.5 Rollback A→B→A

- **Fixture obrigatória:** manter, em host ou registro de fixture, dois image IDs imutáveis por servidor (A e B) já validados. A restauração dos quatro IDs antigos removidos no F6 não é recuperável sem reconstrução; registre essa limitação.
- **Positronic:** `update-image A→B`, `configure` com `expected_revision` atual, `tools/list` e leitura de fixture; depois `update-image B→A`, `configure`, `tools/list` e re-leitura. Esperar a revisão esperada antes de cada mutação.
- **Percival:** `update-image` pela mutação WebUI autenticada/elevada usa a revisão esperada. Para restore, primeiro exclua o servidor pelo gestor e preserve o backup. A mutação `restore` exige sessão WebUI elevada, `backup_id`, `expected_revision` global atual e `expected_confirmation` igual ao ID do servidor; valida checksum, só aceita backup direto sob `mcp-docker/backups/` e recusa sobrescrever servidor existente. A rota trata restore como mutação WebSocket autenticada; não use edição direta nem invoque endpoint anônimo.
- Em ambos os gestores, confirme `initialize`, `tools/list` e uma chamada segura depois do rollback/restore. O restore recupera configuração/pin, mas não baixa uma imagem ausente localmente.
- Não editar `config.json`, `transitions/`, `audit.jsonl` ou `registry.json` à mão. Use apenas a interface suportada; qualquer hand-edit invalida o gate.

### 3.6 Backup e restore de Notes/Khan

- Notes: o vault Positronic fica em `~/.positronic/mcp/data/notes-vault`; o Percival em `~/.local/share/percival-test-mcp/notes-vault`. Backup com checksum (sha256) preserva a hierarquia; restaurar somente em fixture antes de aplicar no vault real. Validar leitura com `notes_get_stats`/`notes_read`.
- Khan: o calendário fica em `~/.local/share/positronic-test-mcp/khan-calendar` e `~/.local/share/percival-test-mcp/khan-calendar`. Backup do diretório (khal.db, khal.conf, eventos `.ics`). Validar com `khal list` (CLI) e `khan_get_status` (MCP) em fixture.
- O restore Percival é uma mutação WebUI autenticada com elevação de sessão; o payload usa `backup_id`, `expected_revision` e `expected_confirmation` (server ID). A implementação valida o checksum do manifest e recusa overwrite; depois revalide o runtime. A fixture D9 exercitou a transação de domínio/broker com esses mesmos invariantes; a rota WebUI mantém sua própria autenticação/elevation.
- Restore **não** baixa imagem; o image ID anterior deve estar disponível localmente.

### 3.7 Containers órfãos

- Containers sem label `percival.mcp-docker.*` e sem pai vivo após encerramento do cliente MCP correspondente são candidatos a órfão.
- O Positronic inicia `docker run --rm` por tool/sessão. Encerrar o cliente (PID pai) e observar `docker ps -a` é o caminho para distinguir instância legítima de órfã.
- Cleanup só com autorização específica: listar IDs, escopo, estado, e remover via `docker rm <id>` (sem `-f`) depois da confirmação de zero referências em registry, config, mount e dependência externa.

### 3.8 Incidente: falso `unhealthy` em stdio

- **Sinal observado:** `docker inspect` mostra `State.Health.Status=unhealthy`, mas isso isoladamente não determina a readiness do MCP. Na walkthrough D9, uma imagem fixture stdio com probe HTTP falsa ficou `unhealthy` enquanto `initialize`/`tools/list` e `ping` MCP passaram.
- **Diagnóstico seguro:** `docker inspect <id> --format '{{json .Config.Healthcheck}} {{.State.Health.Status}}'` (não imprimir `Config.Env` nem `Mounts`). Confirme no contrato do servidor se o transporte é `stdio`; então execute o handshake e uma chamada segura através do gestor dono. Um healthcheck HTTP não tem semântica para stdio.
- **Ação:** remova a probe HTTP da imagem/receita stdio e mantenha `stdin_open: true`, `tty: false`, sem portas publicadas. Não reinicie nem altere o estado salvo para mascarar o resultado. Se o handshake falhar, investigue o MCP/broker; se passar, registre a probe como inválida e corrija a receita na próxima imagem aprovada.

### 3.9 Composição de probes e readiness

- Gateway `GET /health` prova processo e WebSocket requerido; não prova login, credenciais do provider, broker, tools ou KG.
- API `GET /health` prova processo; bearer `GET /v1/models` prova o caminho protegido da API, não uma completion nem acesso pago a provider. A chave API é distinta da senha humana.
- A probe sidecar `python3 -m nanobot.mcp_docker.probe` autentica `/v1/health` do broker e verifica Engine/política; um TCP aberto ou `doctor` aprovado não prova uma tool do MCP.
- Para readiness de MCP, execute `initialize`→`tools/list` e uma `tools/call` segura via o manager dono. Não escreva `state=running` manualmente. O manager observa e projeta o estado; mantenha falha de probe e falha de handshake como evidências distintas.
- `nanobot mcp-docker doctor` verifica token, transporte autenticado, Engine e política do host sem subir MCPs; ele não executa mutações nem prova readiness de cada servidor.

### 3.10 Encerramento por modo e SIGTERM

- **Gateway/API idle:** Compose envia SIGTERM; a observação local foi exit 0. Isso não garante drain completo durante trabalho ativo. `gateway` e `api` compartilham o estado, portanto pare o writer atual antes de iniciar o outro.
- **Broker:** SIGTERM encerra com exit 143. Não prometa drain de chamadas em voo; o store do broker é volátil, enquanto MCPs persistentes pertencentes ao Percival não são removidos pelo stop do broker. Para mudança de identidade/rede do gateway, recrie o par gateway+broker.
- **MCP stdio:** EOF fecha a sessão; o gestor fornece exatamente um `--init`/`init: true`, e a imagem não embute outro init. Sem TTY, sem porta e sem healthcheck HTTP. No Positronic, seu próprio manager é o owner; não aplique o procedimento Percival.
- **Diagnóstico:** `docker inspect <id> --format '{{.Config.Init}} {{.Config.StopSignal}} {{.State.ExitCode}}'`; leia `Entrypoint` separadamente se necessário. A prova é o comportamento observado: broker 143, gateway/API 0 em idle, fixture stdio por EOF 0; `SigCgt=0` do `docker-init` é normal porque ele encaminha o sinal.
- Não use SIGKILL como primeira ação nem interprete 143 como prova de drain. Em MCP persistente, interrompa pelo gestor dono e confirme estado/protocolo após a retomada.

## 4. Revisão trimestral e atualização urgente por vulnerabilidade

### 4.1 Trimestral (owner: operador; executor: agente)

- **Imagens-base e toolchains.** Listar digests atualmente em uso pelos Dockerfiles, cruzar com versões upstream e priorizar atualização. Janela típica: Arch base, Debian snapshot (`2026-10-09` atual), uv base, Alpine base.
- **Dependências Python/Node.** Reexecutar `uv lock --upgrade` (ou equivalente) por repo, validando testes. Releases de patch Python e Node têm fluxo semanal; LTS Python tem cadência específica.
- **Trivy e SBOM.** Reexecutar scans com DB atualizado. O [relatório F3 remediation/triage](../reports/2026-10-10-f3-remediation-triage.md) é a base: severidades bloqueadoras não recebem waiver implícito.
- **Inventário de imagens intermediárias.** Listar tags `:dev`, `:f3`, `:f7`, `:smoke`, etc. e decidir retenção. IDs sem container referenciando e sem expectativa de rollback são candidatos a remoção aprovada (lista explícita por image ID).
- **Capacidade do host.** Verificar `docker system df`, volumes órfãos, espaço em `~/.nanobot`, `~/.positronic`. Sem `docker system prune` em lote; somente itens com lista aprovada.
- **Saída e assinatura:** preencher a tabela abaixo, registrar decisão/owner/data e obter aprovação do operador antes de qualquer mutação. Revisar também a retenção §5; sem aprovação, nada muda.

| Repo/serviço | base/dependência | digest/versão atual | proposta | impacto/scan/SBOM | owner/janela | decisão do operador |
| --- | --- | --- | --- | --- | --- | --- |
| `<repo>` | `<item>` | `<atual>` | `<proposta>` | `<evidência>` | `<owner/data>` | `<aprovar/adiar/rejeitar + data>` |

### 4.2 Vulnerabilidade urgente (owner: operador)

- **Trigger:** CVE com score ≥ alto em runtime Debian, Alpine, Python, Node, OpenSSH, ou em pacote da aplicação (ex.: `openssl`, `curl`, `libxml2`).
- **Resposta em 24h:** triagem no relatório F3 por imagem, decisão por exceção (waiver individual com owner e expiração) ou fix; build + smoke + canário. Sem publicação externa.
- **OpenSSH do gateway (pendência #11):** corrigir em base Forky (teste local já feito com `OpenSSH_10.5p1`); reavaliar testes `tests/webui/test_remote_*`. Alternativa: waiver individual com expiração ≤ 30 dias, registrado em ADR/VEX restrito ao image ID.

## 5. Retenção

| Categoria | Política | Limite |
| --- | --- | --- |
| Pin em runtime | Apenas o último bom e o candidato atual por servidor | 2 IDs por servidor por gestor |
| Fixture A/B | Manter A e B identificados para Notes e Khan, em cada gestor | 4 IDs por serviço crítico |
| Imagens intermediárias (`:dev`, `:f3`, `:f7`, `:smoke`, `:audit`, `:fix-test`) | Manter até o aceite F7; remover por ID aprovado após cada release | Cada release remove imagens sem container ativo nem fixture |
| Imagens-base (Debian snapshot, Arch, Alpine, Python, Node, uv) | Manter digest pin atual e o digest anterior (rollback) | 2 digests por base por repo |
| Trivy DB | Atualizar a cada revisão; manter DB da execução anterior por 30 dias | 2 DBs |
| SBOM CycloneDX | Arquivar por SHA de release, indefinidamente enquanto o release for suportado | 1 SBOM por release |
| Backups de configuração | Manter últimos 10 e o mais recente antes de cada cutover | 11 backups |
| Transitions/Audit | Indefinido enquanto o servidor existir | — |
| Volumes Positronic/Percival | Preservar enquanto a configuração for válida; remover só com aprovação após migração confirmada | — |

### 5.1 Snapshot de retenção D8 (2026-10-24)

Este é um inventário, não uma autorização nem um procedimento de promoção. A
coluna **A** é o pin atualmente observado nos dois gestores; **B** é o candidato
Forky local. Nenhuma revisão de servidor foi alterada. As revisões abaixo são
apenas a fotografia desta data: antes de qualquer operação aprovada, reler a
revisão/CAS e o `configurationId` pelo gestor e interromper se diferirem.

O Percival estava em `schemaVersion=1`, revisão global `18`. O Positronic
mantém um `configurationId` por servidor. Os seis pins A e candidatos B são:

| Servidor | A: Percival image ID / revisão | A: Positronic image ID / revisão / `configurationId` | B: candidato image ID |
| --- | --- | --- | --- |
| AgentMail | `sha256:e104ac7549510d4fff5c103c66f60ddc105b297dc4ee430801cd0bb6e1ecc104` / `1` | mesmo ID / `16` / `84327292-15c1-4b92-8e14-4facb0614e90` | `sha256:9591d7786a5234b9a5635a5d9fb49d010c66233de25cdf955b4508063c8a53c1` |
| Weather | `sha256:e75fdd4abc8a0e34a76ff7fea790bffc4b4a7681396cccc393038b6478600aa6` / `1` | mesmo ID / `4` / `0e909f92-915c-494f-9fc3-5c45e3438654` | `sha256:b805919db8fb10af2dd5ea527402449aa743ebcb3762b4d84085f99f97b2d70f` |
| OSM | `sha256:67f8ada639897af9ca4ca8f02e38932376f73f454db76028a3920f076011cfeb` / `1` | mesmo ID / `4` / `8fb5cdec-f04a-4085-b9d2-f62265464bb0` | `sha256:ce6de5ccd164ec8c89d4f5b195b140f1dd12f1405f50919614aaf8f93252159b` |
| Deep Research | `sha256:265891c14514c809e9c05587549631426ef080219c03fde21e5d703623d3793d` / `1` | mesmo ID / `16` / `a766c34f-4166-4553-a7b5-293ab5fd5f3e` | `sha256:bab6d3ced1b3b20497f0ef61e36e14f2362eca3523b2492519d6596802eb30ff` |
| Notes | `sha256:ef4082ef13905cdaa0da23830bcc6c5b88ca3beb30074e11d56593d11a097460` / `4` | mesmo ID / `19` / `1d0880b8-d1f5-4e7f-8b04-19d66ea4f91c` | `sha256:3abd363f5a354a293b7c5ef5bf58a30cfd245800814f6b800c4545fba994822a` |
| Khan Calendar | `sha256:55cd5a038d22e253693d1d0681e108f57b41f060ecbeb231dad3e2f7edd51914` / `4` | mesmo ID / `10` / `9ee229c8-c6ce-4d5c-b030-e39028fb6349` | `sha256:9aa02922d5163b992032eafcdaef7f49e009d8e0c855b2f93c258b3bb881db1f` |

**Substituição de 2026-10-24 (fechamento D8):** a coluna B foi substituída
pelos candidatos reconstruídos após a reconciliação dos pins Python e a troca
da base do runtime do broker. Os image IDs B anteriores (`b8ed6f58fe6a`,
`e3537f2d2983`, `286fdfeb8327`, `af9c6fa28863`, `1bc3417de299`,
`020200378c99`, `2a0e5c342504`, `c6784ebbc29a`) estão **superados** e não
podem ser reutilizados como par B. A coluna A é a foto inicial dos seis MCPs e
foi reconfirmada por `docker ps` em 2026-10-24: os doze containers MCP dos dois
gestores seguem nos image IDs A.

**Correção de estado do core (2026-10-24):** a redação anterior desta seção
afirmava que o core ativo usava gateway `sha256:d06d8eedcc4e…` e broker
`sha256:c6e370a5d56c…`. Isso **não é mais verdade**: o deploy local da D11
substituiu o par core, e ambos os image IDs citados passaram a ser snapshots de
rollback preservados, não imagens ativas. O estado real, lido de `docker ps` e
dos labels OCI em 2026-10-24:

| Papel | Image ID | Revision (label) | Versão | Estado |
| --- | --- | --- | --- | --- |
| Gateway do Compose (ativo) | `sha256:ac62466dfd99ca60006890479d052550287609ec7726bdae81d1976393f289c6` | `29a482cec88506e579c4d5c0b32c6aec16e3fc55` | `0.3.5` | ativo (`percival-gateway:0.3.5-29a482c-d11-builtin-20261024`) |
| Broker do Compose (ativo) | `sha256:6ea63b38852cca47943562cfc695a08d23c68849a1d7cb97418766f88f324bd8` | `29a482cec88506e579c4d5c0b32c6aec16e3fc55` | `0.3.5` | ativo (`percival-mcp-broker:local`) |
| Gateway pré-D11 (rollback) | `sha256:d06d8eedcc4e41136119c154b8e0c9786d1aba3aed0a1b9726f822c7dda7bbc9` | `29a482cec88506e579c4d5c0b32c6aec16e3fc55` | `0.3.5` | preservado (`percival-gateway:rollback-d11-20261024`) |
| Broker pré-D11 (rollback) | `sha256:c6e370a5d56c74e0362f2adecd501b575c4246439a22e1451a800fb30f30b32c` | `c63b8b680d0f12ca1c2b6c271a56ea16ff4bd2d4` | `0.3.5` | preservado (`percival-mcp-broker:rollback-d11-broker-before-fix`) |

O par **A/B da D8** é outro e continua **retido localmente, sem estar ativo**:
A é o par do SHA `3daabe20f4c6a7b5f26f2158b97dc2591905507b` — gateway
`sha256:2a0e5c34250459bcc1861c3cd291333944f7b7451f65f3dbead0c562cb0ada9f` e
broker `sha256:c6784ebbc29a41c6591dfeec52528dbd19fb44be18591eadf4db8803141ccf2d`
— e B é o par do SHA `50e6ebd0ab8f62a9ed242030459ef0581f7da1a6` — gateway
`sha256:25f4ac0774e985378e9b8ac09b5eb851915a817fd0e6be2929276fbbab0a50c5` e
broker `sha256:1988f1771ab84b952e301cd1aa931af4e24e116c7a6fb8851b95be566c5be1c7`.
Consequência para a D8: o par core ativo **não** é o A da D8, portanto um
eventual rollback do core **tem** de voltar ao image ID `2a0e5c342504…`/`c6784ebbc29a…`
(A da D8), e não ao par `29a482c`/`c63b8b68` do deploy D11. O caminho A→B→A
foi exercitado no [walkthrough D9](../reports/2026-10-24-d9-runbook-walkthrough.md)
em fixture descartável, com os builds `0.1.0-3daabe2`. Os image IDs locais
não são digests OCI publicados. O core B foi enviado em `50e6ebd0` (precedido
por `297d4295`, `ce31e526` e `3daabe20`); o envio da **fonte** não publica nem
promove **imagem**.

**Retenção atual:** manter A e B localmente, sem retag destrutivo ou prune.
Retêm-se também o par core ativo do deploy D11
(`ac62466dfd99`/`6ea63b38852c`) e o par pré-D11
(`d06d8eedcc4e`/`c6e370a5d56c`), preservados pelos snapshots
`rollback-d11-20261024` e `rollback-d11-broker-before-fix`. O gateway
`percival-gateway:0.1.0-b49dd8b` no container nomeado `d6-nopip` também foi
observado ativo; é um fixture preexistente, não o gateway do Compose, e
permanece fora de qualquer limpeza. Os resultados do scanner e os
smoke/limites de cada B estão no [registro D8](../plans/closed/2026-10-23-fechamento-padronizacao-docker-f4-f5-f7-plan.md#29-d8--reconciliação-e-estado-de-promoção).

**Gates antes de qualquer promoção (2026-10-24):** os findings Python dos
seis MCPs e do broker foram corrigidos — os sete image IDs B reportam zero
findings no Trivy — e o smoke autenticado do AgentMail foi executado com
sucesso (24 tools e leitura HTTP 200), o que encerra os dois bloqueios
técnicos locais que restavam. O finding Medium `CVE-2026-49138` do gateway
permanece com avaliação `not_affected` restrita ao image ID e reancorada no
commit de correção `545294c`, ancestral da revisão candidata. Restam dois
bloqueios: **CI remoto** — os seis SHAs candidatos têm run e todos terminam em
failure; a comparação step a step contra o run anterior de cada repo mostra
que cinco falham no **mesmo step**, com o mesmo nome, sem relação com os pins,
e o único delta real (OSM, step 6) foi diagnosticado como flake preexistente do
harness legado `docker-smoke-test.sh`, que fecha stdin sem aguardar a resposta
de `initialize`; o core não tem run (`total_count: 0`) porque os workflows do
fork estão desabilitados — e **distribuição**, com I3 adiado e aquisição por
catálogo/digest não implementada. Portanto B **não** é atualmente elegível
para instalar. Depois
de candidatos aprovados, o operador deve confirmar a janela, CAS atual,
backup/configuração/dados compatíveis e rollback A→B→A em fixture independente
antes de autorizar canário. Nenhum comando de mutação é fornecido neste
snapshot. A evidência do fechamento local está no
[plano D8 arquivado](../plans/closed/2026-10-24-d8-promotion-readiness-closure-plan.md);
CI e distribuição permanecem sob o
[plano adicional B5/B6](../plans/2026-10-24-b5-b6-ci-distribution-closure-plan.md).

**Nunca** usar `docker image prune -a`, `docker system prune --volumes` ou `docker container prune --filter "until=..."` para liberar espaço. Cada remoção é uma lista explícita aprovada por ID/digest, com referência cruzada em registry, config e mounts.

### 5.2 Aprovação e calendário D9

A política de retenção da tabela §5 foi aprovada pelo operador nesta execução de D9, por solicitação explícita nesta sessão em **2026-10-24**. Este é um registro de aprovação textual; não representa assinatura criptográfica. A aprovação autoriza a política, **não** a remoção de imagens, containers, volumes ou dados. Nenhum prune ou cleanup foi executado.

| Registro | Data | Owner da decisão | Executor da revisão | Estado |
| --- | --- | --- | --- | --- |
| Aprovação inicial da política de retenção | 2026-10-24 | Operador | Agente | Aprovada; nenhuma limpeza autorizada |
| Próxima revisão trimestral | até 2027-01-24 | Operador | Agente | Pendente |

Em cada revisão, anexar tabela §4.1, inventário por image ID/digest, referências em pins/config/containers/volumes, decisão explícita de retenção e aprovação do operador. Não remova automaticamente artefatos fora do limite: apresente uma lista nominal e aguarde aprovação específica para cada limpeza.

### 5.3 Candidatos limpos F3 (2026-10-25)

Fotografia, **não** autorização: são artefatos **locais**, sem digest OCI
publicado, e nenhum pin foi alterado. Substituem funcionalmente o par B da D8
como candidatos de referência, mas continuam retidos sem promoção.

| Papel | Tag | Image ID |
| --- | --- | --- |
| Gateway | `percival-gateway:0.1.0-f2173bb` | `sha256:72195df6c5818e0b22d2bb5f5dcc349f38c70b787a5ed8db1935c39d88d32ee3` |
| MCP broker | `percival-mcp-broker:0.1.0-f2173bb` | `sha256:a3c469a0b6e5799ab322fea5ba7f3782b73e177d6dfbec3aadeab0f2ee1a4685` |
| Notes MCP | `percival-notes-mcp:0.1.5-c104735` (D8, reaproveitado) | `sha256:3abd363f5a354a293b7c5ef5bf58a30cfd245800814f6b800c4545fba994822a` |
| AgentMail MCP | `percival-agentmail-mcp:0.4.0-89acdf4` | `sha256:114f938fdcfca2832f661484a70b1fa24c37f783ea09c0d23af1de45d56d159c` |
| Weather MCP | `percival-weather-mcp:0.9.0-9583059` | `sha256:7e3c03db89a649afc82f3da156710c154abd29143dace6bde0ba9f07cf53a69f` |
| Khan Calendar | `percival-khan-calendar:0.4.0-4f4521a` | `sha256:620dbbc4b04d9e131c85e692fd1a6d44ee2a222977b0c65b53449abf33cca4c0` |
| OSM | `percival-osm:0.5.0-4204213` | `sha256:6d0e8e5f4aad13b4a98eb7f50cfeef32463f18b777b5c44dae325c045e0a2ab6` |
| Deep Research | `percival-deep-research:3.0.1-dd6451e` | `sha256:7d015e3359363df00db47f9b8678fb76d601f64fb471314a163a36f5a1e75e07` |

Postura: Trivy 0.67.2 com DB de 2026-10-25, **0 Critical/High** nos oito
candidatos; único Medium `CVE-2026-49138` no gateway com avaliação
`not_affected` restrita ao image ID do gateway
([OpenVEX F3](../reports/2026-10-25-f3-openvex-gateway.json)). Relatório, SBOMs
e hashes: [F3 2026-10-25](../reports/2026-10-25-f3-reproducibility-contexts-posture.md).
A base de vulnerabilidades usada expira em 2026-10-26: reexecutar scan e SBOM
antes de qualquer promoção.

## 6. Links e procedimentos vizinhos

- [Plano de padronização Docker](../plans/2026-10-09-docker-standardization-refactor-plan.md) — contratos F0–F5 e pendências numeradas.
- [Plano de fechamento F7](../plans/closed/2026-10-10-f7-operations-acceptance-closure-plan.md) — pacotes P0–P5 que precedem este manual.
- [Runbook F5 — migração/recuperação de estado `~/.nanobot`→`~/.percival`](../mcp-docker-f5-runbook.md) — procedimento de cutover do estado Compose sidecar.
- [Governança B10–B13](../percival-governance.md) — upstream/CI/release.
- [Plano MCP Docker first-class](../plans/closed/2026-10-06-mcp-docker-first-class-execution-plan.md) — gates VPS/Engine 27.x independentes.
- [Relatório F4/F5](../reports/2026-10-10-f4-f5-closure-report.md) — restore/rollback já exercitados em fixture.
- [Relatório F3 remediation/triage](../reports/2026-10-10-f3-remediation-triage.md) — base de findings e VEX.
- [Walkthrough D9 (runtime 1)](../reports/2026-10-24-d9-runbook-walkthrough.md) — update, rollback, health falso, restore e retenção assinada.

## 7. Limites desta revisão

- Procedimentos cobertos: build, atualização, rollback, backup/restore, incidentes de health/SIGTERM, revisão trimestral, urgência, retenção.
- Procedimentos fora: deploy em VPS, mudança de Engine, migração real de estado, rotação da credencial `operator-admin`, reescrita de histórico, publicação, release B13. Cada um tem plano próprio.
- A walkthrough D9 usa engine 27.5.1 dentro de Docker-in-Docker descartável e imagens locais do core; a fixture de update/rollback/restore é sintética, não promove nem homologa os seis MCPs de produção. CI GitHub, release/publicação, VPS e Engine do host continuam gates próprios. A retenção aprovada não autoriza prune nem cutover.
