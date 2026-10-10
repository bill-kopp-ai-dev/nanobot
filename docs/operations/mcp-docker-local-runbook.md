# Manual de operação e manutenção — MCP Docker Percival

- **Preparado em:** 2026-10-10 UTC; revisão 0.1.
- **Escopo:** procedimentos de operação, atualização, rollback, incidente, revisão e retenção para os servidores MCP Docker que o Percival consome (Notes, AgentMail, Weather, Khan Calendar, OSM e Deep Research) e para o gateway/broker. Este manual **não** substitui o [runbook de migração de estado `~/.nanobot`→`~/.percival`](../mcp-docker-f5-runbook.md), apenas convive com ele.
- **Autoridade:** qualquer mutação real (instalar/atualizar/rollback/parar/remover) exige a interface suportada do gestor correspondente e a aprovação específica do operador. Nada aqui é executado implicitamente.
- **Estado da padronização:** o documento nasce no fechamento F7. Os contratos F0–F5 que ele referencia estão registrados no [plano de padronização](../plans/2026-10-09-docker-standardization-refactor-plan.md) e no [plano de fechamento F7](../plans/2026-10-10-f7-operations-acceptance-closure-plan.md).

## 1. Princípios

1. **Identidade antes da ação.** Toda mutação começa registrando `source SHA`/`worktree`, `image ID`/`RepoDigest`, alias/tag, labels `percival.mcp-docker.{owner,managed-by,server-id,instance-id}`, configuração, mounts/UID/GID, revisão atual, e o dono (Percival ou Positronic). Esses dados vão para o relatório de operação ou para a trilha de auditoria do gestor; nada vai para a composição da operação em si.
2. **Pin imutável.** O broker fixa imagens por ID/RepoDigest e usa `--pull=never`. Tags mutáveis (`:dev`, `:f3`, `:f7`) são alias de diagnóstico e não podem ser o identificador de execução. Promoção = novo image ID imutável, com alias humano atualizado em paralelo.
3. **Privilégio mínimo do broker.** O gateway e os MCPs não recebem `docker.sock`/CLI. Apenas o broker fala com o daemon. Limites efetivos de mount/rede e modelo de acesso ao host seguem B14–B25; este manual não os reescreve nem os afrouxa.
4. **Stdio e HTTP são contratos diferentes.** Stdio: stdout só JSON-RPC, sem TTY, sem porta, sem healthcheck HTTP. HTTP: profile/serviço dedicado, bind loopback por padrão, opt-in para exposição. Não usar uma única receita para os dois.
5. **Init único.** Apenas um `init: true` ou tini embutido por processo. Stdio usa `stdin_open: true`/`tty: false` e `docker run --init`. Duplo init cria falsa camada de supervisão.
6. **Reversibilidade antes de eficiência.** Toda operação destrutiva exige plano de retorno próprio, autorização específica e janela. `docker system prune`, `docker rm -f` cego e `docker image prune -a` são proibidos.
7. **Sem segredos em artefatos.** Inventário, logs e inventários redigem env, tokens, e o conteúdo integral de `docker inspect`. Apenas a estrutura e os labels são registrados.

## 2. Posições de execução

| Posição | Função | Endereço típico | Exposição |
| --- | --- | --- | --- |
| `nanobot-gateway` (Compose) | Gateway Python | 127.0.0.1:8765 (HTTP), 127.0.0.1:18790 (WS) | Loopback; opt-in explícito para expor |
| `nanobot-percival-mcp-broker-1` | Broker MCP (Compose sidecar) | 127.0.0.1:18081 dentro do namespace do gateway (`network_mode: service:nanobot-gateway`) | Loopback via gateway; sem porta no host |
| Containers `percival-mcp-*` | MCPs do Percival | Rede do gateway | Sem portas publicadas |
| Containers Positronic (sem label) | MCPs do Positronic | Ponte | Sem portas publicadas |
| Engine local | 29.7.2 (overlay descartável) | — | Fora do gate VPS Engine 27.x |

`docker.sock` está montado **apenas** no broker. O gateway pode receber `PERCIVAL_DOCKER_GATEWAY_TOKEN_ISSUE_SECRET_FILE` (modo 0600) para autorizar a UI Web a emitir tokens; nada além disso.

## 3. Procedimentos por cenário

### 3.1 Inventário seguro antes de agir

- Ler `~/.nanobot/config.json` para o estado Percival e `~/.positronic/mcp/registry.json` + `~/.positronic/mcp/servers/<id>.json` para Positronic.
- Executar `docker ps --no-trunc --format '{{.ID}} {{.Names}} {{.Image}} {{.CreatedAt}}'` e cruzar com a lista de servidores do registry/config. Containers sem pai vivo ou sem label são órfãos (ver §3.7).
- `docker image inspect <id> --format '{{ index .Config.Labels "org.opencontainers.image.revision" }} | {{ index .Config.Labels "io.percival.build.source-diff-sha256" }}'` para confirmar a fonte da imagem.
- `git -C <repo> rev-parse HEAD; git -C <repo> status --short` em todos os repos de runtime envolvidos. Anotar a divergência.
- **Não imprimir** env, tokens, segredos ou o conteúdo de `Config.Env`/`Mounts`. Apenas os rótulos e paths públicos.

### 3.2 Build de uma imagem

- Para o gateway/broker: `python scripts/percival-docker-build.py` no checkout Percival; passar `--worktree-candidate` quando a fonte incluir diff não commitado. Não usar `:dev` como release.
- Para os MCPs: `python scripts/percival-docker-build.py <service>` no checkout do MCP, com tag imutável `<semver>-<shortsha>`. Registrar `<semver>` de `pyproject.toml` e `<shortsha>` de `git rev-parse --short HEAD`. Falhar se o `0.0.0`/`unknown`/`local` aparecer.
- Pinar base/lock/canal conforme F3. Confirmar com `docker inspect <id>` que `org.opencontainers.image.{source,revision,licenses}` batem com o esperado.
- Após o build, executar o smoke F1 (stdio) e, se aplicável, o profile HTTP. Para Khan, executar `khan_get_status` em fixture isolada para validar resposta, não apenas `tools/list`.

### 3.3 Atualização de servidor em Positronic

- Ler `mcp server show <id>` para revisão, `configurationId` e pin atual.
- Executar `mcp server update-image <id> <sha256:...>` com `expected_revision`. Após o update, o `configurationId` é invalidado; chamar `mcp server configure <id>` para reaplicar env/allowlist/escopo.
- Validar `tools/list` e um tool seguro de leitura (ex.: `khan_get_status`, `osm_get_health`, `weather_get_status`).
- Preservar o último image ID bom em uma fixture identificada, caso o rollback seja necessário (ver §3.5).

### 3.4 Atualização de servidor em Percival

- Pela UI/API autenticada, abrir o detalhe do servidor. Confirmar revisão atual e imagem atual.
- `update-image` para o ID novo, com `expected_revision`. O broker aplica CAS, registra `preparing`→`committed`/`failed` em `transitions/<id>.json` e move o container.
- Validar `tools/list`, ler `~/.nanobot/mcp-docker/audit.jsonl` (modo 0600) e reconciliar com a expectativa.
- Em caso de falha observada, o broker expõe o estado pendente. A correção usa a página de restore ou um novo `update-image` (ver §3.5).

### 3.5 Rollback A→B→A

- **Fixture obrigatória:** manter, em host ou registro de fixture, dois image IDs imutáveis por servidor (A e B) já validados. A restauração dos quatro IDs antigos removidos no F6 não é recuperável sem reconstrução; registre essa limitação.
- **Positronic:** `update-image A→B`, `configure` com `expected_revision` atual, `tools/list` e leitura de fixture; depois `update-image B→A`, `configure`, `tools/list` e re-leitura. Esperar a revisão esperada antes de cada mutação.
- **Percival:** pela UI/API, `update-image` com `expected_revision`, ou `restore` a partir de backup (operator-admin, `configurationId` digitado, checksum, recusa de sobrescrita). Confirmar `tools/list` e estado do dado.
- Não editar `config.json`, `transitions/`, `audit.jsonl` ou `registry.json` à mão. Use apenas a interface suportada; qualquer hand-edit invalida o gate.

### 3.6 Backup e restore de Notes/Khan

- Notes: o vault Positronic fica em `~/.positronic/mcp/data/notes-vault`; o Percival em `~/.local/share/percival-test-mcp/notes-vault`. Backup com checksum (sha256) preserva a hierarquia; restaurar somente em fixture antes de aplicar no vault real. Validar leitura com `notes_get_stats`/`notes_read`.
- Khan: o calendário fica em `~/.local/share/positronic-test-mcp/khan-calendar` e `~/.local/share/percival-test-mcp/khan-calendar`. Backup do diretório (khal.db, khal.conf, eventos `.ics`). Validar com `khal list` (CLI) e `khan_get_status` (MCP) em fixture.
- O gateway expõe uma UI de restore que exige autorização, nome do servidor digitado, checksum, revisão atual, e recusa sobrescrita. Esse é o caminho suportado.
- Restore **não** baixa imagem; o image ID anterior deve estar disponível localmente.

### 3.7 Containers órfãos

- Containers sem label `percival.mcp-docker.*` e sem pai vivo após encerramento do cliente MCP correspondente são candidatos a órfão.
- O Positronic inicia `docker run --rm` por tool/sessão. Encerrar o cliente (PID pai) e observar `docker ps -a` é o caminho para distinguir instância legítima de órfã.
- Cleanup só com autorização específica: listar IDs, escopo, estado, e remover via `docker rm <id>` (sem `-f`) depois da confirmação de zero referências em registry, config, mount e dependência externa.

### 3.8 Incidente: falso `unhealthy` em stdio

- **Causa típica:** healthcheck HTTP aplicado a container stdio. Stdio não tem HTTP, então qualquer probe HTTP resulta em `unhealthy` falso.
- **Diagnóstico:** `docker inspect <id> --format '{{.State.Health.Status}} {{.Config.Healthcheck.Test}}'`. Se `Health.Test` contém `curl http`, e o serviço é declarado `stdio`, a receita precisa de `stdin_open: true; tty: false` e `healthcheck: []` (ausente), e o container real não deve receber `--health-cmd` HTTP.
- **Correção:** alterar a receita Compose para separar o profile HTTP do serviço stdio. O serviço stdio é invocado sob demanda por `docker compose run --rm -T` (ou equivalente do cliente MCP). Reiniciar o container não conserta a receita; consertar a receita é o que evita reincidência.

### 3.9 Incidente: readiness HTTP falha mesmo com `healthy`

- HTTP `healthy` no Docker ≠ readiness do MCP. Em `http://127.0.0.1:18081/v1/...` (loopback) o broker responde, mas o MCP só está pronto quando o handshake MCP (`initialize`, `tools/list`) passa.
- Procedimento: `docker logs <id> --tail 50` (redigido); `tools/list` via cliente MCP; se passar, marcar `state=running` no registry/config e seguir.
- Em Percival, o `doctor` (`nanobot mcp-docker doctor`) confirma token, transporte autenticado, Engine e política de host, sem subir containers. Se `doctor` passa mas o MCP não responde, o problema é da imagem, não do gateway/broker.

### 3.10 Incidente: SIGTERM não para o container

- Esperado: o container responde a SIGTERM, sai em ≤ 10s e `docker ps` mostra `Exited (143)`. Não usar `SIGKILL` por padrão.
- Diagnóstico: o processo é o PID 1; se houver `tini` e `init: true` juntos, o init duplicado pode mascarar o sinal. Conferir `docker inspect --format '{{.Config.Init}}'` e `docker inspect <image> --format '{{json .Config.Entrypoint}}'`. Manter apenas um.
- Se o MCP travar, encerrar a sessão cliente (que para o `docker run --rm`) é a primeira ação; só então considerar o container.

## 4. Revisão trimestral e atualização urgente por vulnerabilidade

### 4.1 Trimestral (owner: operador; executor: agente)

- **Imagens-base e toolchains.** Listar digests atualmente em uso pelos Dockerfiles, cruzar com versões upstream e priorizar atualização. Janela típica: Arch base, Debian snapshot (`2026-10-09` atual), uv base, Alpine base.
- **Dependências Python/Node.** Reexecutar `uv lock --upgrade` (ou equivalente) por repo, validando testes. Releases de patch Python e Node têm fluxo semanal; LTS Python tem cadência específica.
- **Trivy e SBOM.** Reexecutar scans com DB atualizado. O [relatório F3 remediation/triage](../reports/2026-10-10-f3-remediation-triage.md) é a base: severidades bloqueadoras não recebem waiver implícito.
- **Inventário de imagens intermediárias.** Listar tags `:dev`, `:f3`, `:f7`, `:smoke`, etc. e decidir retenção. IDs sem container referenciando e sem expectativa de rollback são candidatos a remoção aprovada (lista explícita por image ID).
- **Capacidade do host.** Verificar `docker system df`, volumes órfãos, espaço em `~/.nanobot`, `~/.positronic`. Sem `docker system prune` em lote; somente itens com lista aprovada.
- **Saída da revisão:** tabela `imagem-base | digest antes | digest proposto | impacto | owner | janela` e ações aprovadas. Sem aprovação, nada muda.

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

**Nunca** usar `docker image prune -a`, `docker system prune --volumes` ou `docker container prune --filter "until=..."` para liberar espaço. Cada remoção é uma lista explícita aprovada por ID/digest, com referência cruzada em registry, config e mounts.

## 6. Links e procedimentos vizinhos

- [Plano de padronização Docker](../plans/2026-10-09-docker-standardization-refactor-plan.md) — contratos F0–F5 e pendências numeradas.
- [Plano de fechamento F7](../plans/2026-10-10-f7-operations-acceptance-closure-plan.md) — pacotes P0–P5 que precedem este manual.
- [Runbook F5 — migração/recuperação de estado `~/.nanobot`→`~/.percival`](../mcp-docker-f5-runbook.md) — procedimento de cutover do estado Compose sidecar.
- [Governança B10–B13](../percival-governance.md) — upstream/CI/release.
- [Plano MCP Docker first-class](../plans/2026-10-06-mcp-docker-first-class-execution-plan.md) — gates VPS/Engine 27.x independentes.
- [Relatório F4/F5](../reports/2026-10-10-f4-f5-closure-report.md) — restore/rollback já exercitados em fixture.
- [Relatório F3 remediation/triage](../reports/2026-10-10-f3-remediation-triage.md) — base de findings e VEX.

## 7. Limites desta revisão

- Procedimentos cobertos: build, atualização, rollback, backup/restore, incidentes de health/SIGTERM, revisão trimestral, urgência, retenção.
- Procedimentos fora: deploy em VPS, mudança de Engine, migração real de estado, rotação da credencial `operator-admin`, reescrita de histórico, publicação, release B13. Cada um tem plano próprio.
- Limitações conhecidas: (a) `mcp server install-local` Positronic falha silenciosamente; workaround usado em F4 é edição direta do registry, e este manual recomenda investigar o handler antes de usar em produção. (b) Khan `tools/call` no FastMCP 3.4.4 não devolve frame JSON-RPC; verificação no nível de filesystem + stderr é proxy até fix. (c) Engine local 29.7.2 com overlay `docker-compose.engine29-override.yml`; gate VPS Engine 27.x é independente.
