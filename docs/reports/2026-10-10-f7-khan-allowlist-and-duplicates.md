# F7 — Khan allowlist e duplicatas Positronic (P2, diagnóstico)

- **Data:** 2026-10-10 UTC.
- **Escopo:** pacotes P2 do [plano de fechamento F7](../plans/2026-10-10-f7-operations-acceptance-closure-plan.md), pendências #7 e #8 do plano principal.
- **Método:** leitura read-only de configurações Positronic e Percival, mapeamento de containers MCP por PID pai e por janela de início, comparação com clientes ativos. Nenhuma mutação em registries, em containers, no broker ou nos pinos.
- **Limitação:** a atribuição por PID pai é uma inferência estrutural. Containers órfãos seriam PIDs cujo pai já morreu; no snapshot atual, todos os PIDs pai estão vivos, então não há evidência de órfão. O encerramento dos clientes MCP é o que reciclaria os containers `--rm`; enquanto a sessão Positronic (PID 3758) estiver ativa, esses containers persistem por design.

## 1. Khan allowlist — estado atual

| Cliente | Onde está a allowlist | Conteúdo | Conclusão |
| --- | --- | --- | --- |
| Positronic | `~/.positronic/mcp/servers/khan-calendar.json` (`schemaVersion: 2`, `revision: 1`, `configurationId: fb8ba208-…`) | `allowedTools` com **12 tools** incluindo `khan_create_event`, `khan_update_event`, `khan_delete_event` e `khan_delete_event_safe` | Sem allowlist restritiva. Escrita/exposição habilitadas. |
| Positronic | `~/.positronic/mcp/registry.json` (entrada `khan-calendar`, `revision: 8`) | Não controla tools; mantém escopo/ativação/allowedProjects/config | Ativado global; `allowedProjects: []`. |
| Percival | `~/.nanobot/config.json` (`tools.mcpDocker.servers["khan-calendar"]`, `revision: 4`) | `tools`: 12 entradas, `toolsDisabled: []` | Sem allowlist restritiva. Mesma superfície de 12 tools. |

**Diagnóstico:** a allowlist efetiva do Khan é idêntica nos dois clientes. Ambos expõem leitura e escrita, com `khan_delete_event` (sem preview) e `khan_delete_event_safe` (com dry-run). O [relatório F4/F5](../reports/2026-10-10-f4-f5-closure-report.md) documentou a inconsistência Khan no ensaio de fixture (`tools/list` com 6 tools em uma fase; `khan_get_status` no canário final, todos com a mesma imagem 0.4.0). Isso sugere variação de comportamento entre clientes MCP/Python e a versão 3.4.4 do FastMCP, não divergência entre gestor.

**Decisão pendente (operador):**

1. **Manter 12 tools.** Compatível com o uso atual; expõe mutação. Documentar em ADR ou `docs/percival-governance.md` o conjunto aceito.
2. **Somente leitura.** Restringir `allowedTools` a 6 ferramentas (list/get/view). Exige atualizar o config e o registry com `configurationId` novo e CAS Positronic. `khan_*_delete*` ficam fora.
3. **Subset nominal.** Escolher lista explícita (por exemplo, leitura + `khan_create_event` para agendar). Exige mesma migração CAS.

**Recomendação:** registrar a decisão como ADR (P2 do plano) e aplicar via `update`/`configure` por gestor, com revisão atual e `tools/list` de confirmação. O F4/F5 não fecha sem isso; sem escolha registrada, o gate F7 fica em "all-or-nothing", o que provavelmente não é o pretendido pelo operador.

## 2. Duplicatas Positronic — mapeamento por PID pai

A árvore de processos do snapshot mostra **uma única sessão cliente** (PID 3758 = `bun run … /home/bill/Projects/alternative-positronic/source/opencode/packages/opencode src/index.ts /home/bill`, pts/0, em execução há 11h15). Esse processo é o `positronic-mcp-docker` indiretamente: o opencode-cli instancia o módulo, que faz `Bun.spawn([...docker run --rm --init --interactive...])` para cada tool MCP por chamada persistente.

| Janela de início | Containers iniciados | Origem inferida | Justificativa |
| --- | --- | --- | --- |
| 2026-10-10 13:29:46 → 13:30:11 | 5 (AgentMail, Deep Research, Khan, Notes, Weather) | `docker run` filhos diretos de PID 3758 (lançados pelo opencode 5h45 atrás) | `ppid=3758`, mounts Positronic; pre-canário, ainda sob revisão F3. |
| 2026-10-10 15:26:00 → 15:27:10 | 4 (`percival-mcp-agentmail`, `osm`, `weather`, `deep-research`) | Broker Percival (via gateway) | `com.docker.compose.service=…`, labels `percival.mcp-docker.*`, pre-canário. |
| 2026-10-10 17:08:19 → 17:08:37 | 5 (AgentMail, Khan, Deep Research, Notes, Weather) | `docker run` filhos diretos de PID 3758 (lançados 2h06 atrás) | Mesma sessão aberta; segundo conjunto após reconfiguração. |
| 2026-10-10 18:30:04 → 18:32:27 | 2 (Khan, Notes) | Broker Percival (canário F7) | `com.docker.compose.service=…`; segundo conjunto broker, posts installs de Notes/Khan. |
| 2026-10-10 18:55:05 → 18:55:12 | 6 (Khan, Deep Research, AgentMail, Notes, Weather, OSM) | `docker run` filhos diretos de PID 3758 (lançados ~1h atrás) | Pós-canário; nova leva MCP Positronic para todas as 6 tools. |
| 2026-10-10 19:00:11 → 19:00:25 | 6 (AgentMail, Khan, Deep Research, Notes, Weather, OSM) | `docker run` filhos diretos de PID 3758 (lançados <5min) | Mais recente, em execução agora; sessão MCP ativa. |

Total: **12 containers `docker run` filhos do PID 3758** (2x AgentMail, 2x Deep Research, 2x Khan, 2x Notes, 2x Weather, 1x OSM — o OSM só foi descoberto recentemente e tem apenas uma instância). Esses 12 são as "duplicatas" aparentes: cada `docker run --rm` foi feito em uma janela distinta, mas a sessão cliente (PID 3758) nunca morreu, então eles coexistem.

**Conclusão sobre órfãos:** no snapshot atual, **não há containers órfãos**. Todos os 12 `docker run` têm PID pai vivo (3758) e PPID `containerd-shim` esperado pelo Docker. Os 6 `percival-mcp-*` são geridos pelo broker Compose e estão marcados com `percival.mcp-docker.*`. Nenhum container sem pai e sem label foi observado.

A "duplicação" do F0 era real e a causa é **comportamento normal do cliente MCP por sessão**: o Positronic, ao iniciar uma sessão, abre um `docker run` por tool ativa. Cada `mcp server configure`/`update-image`/reinício de cliente gera um novo `docker run`, e o anterior só sai quando o cliente original encerra. Em 11h de sessão contínua, com reconfigurações, é esperada uma população de 10+ containers por gestor.

## 3. Lifecycle esperado e critério de "limpo"

- **Encerrar o cliente** (PID 3758) levaria os 12 containers `docker run --rm` a sair pelo flag `--rm` no `docker stop`/`docker kill`. Esse é o caminho suportado.
- **Não destruir containers ativos** sem mapear o cliente. O `docker rm -f` aplicado a uma instância em uso derrubaria a tool MCP e quebraria o `mcp-docker` sem aviso, com risco de corromper o estado Positronic.
- **Após o encerramento do cliente, recontar.** Se algum container persistir sem pai, esse é o conjunto candidato a limpeza. Até lá, qualquer "limpeza" é prematura e falsificaria a métrica.

## 4. Achado adicional relevante

A árvore de processos também mostra **dois clusters de containers em paralelo** que não pertencem ao PID 3758: os PIDs `2291468`, `2294184`, `2295417`, `2296579` (3h47–3h48 de idade) iniciados por um **containerd-shim cujo pai não é PID 3758**. Esses são o conjunto de containers `percival-mcp-*` em execução, mas no snapshot o **broker Compose não tem filhos `docker run` diretos** — eles foram iniciados pelo gateway/CLI, o que é compatível com a topologia gateway → broker → docker. Verificação adicional exigiria correlacionar o `containerd-shim` com o broker, o que não foi feito nesta sessão (read-only).

## 5. Recomendações para fechamento

1. **Khan allowlist:** aplicar decisão formal do operador via ADR/nota em `docs/percival-governance.md`. A escolha padrão "manter 12 tools" é defensável, mas não é o padrão seguro; se mantida, registrar a justificativa. Se alterada, usar `update-image` + `configure` com CAS atual e `tools/list` para confirmar.
2. **Duplicatas Positronic:** não destruir. Em vez disso:
   a. Encerrar a sessão MCP Positronic (PID 3758) **quando ela não estiver em uso** e observar `docker ps -a` para confirmar que `--rm` limpou o que deveria.
   b. Recontar containers. Se sobrarem órfãos verdadeiros, listar por ID, escopo e estado antes de qualquer `docker rm`.
   c. Documentar a cardinalidade esperada por sessão MCP (uma instância por `server_id` por sessão cliente ativa) como **não-órfão por construção**, em ADR ou em `docs/percival-governance.md`.
3. **F4 — Khan `tools/call` no fixture:** investigar FastMCP 3.4.4 com o cliente Python `mcp[cli]` para separar bug de versão de problema de pin ou de config. Não fechar F4 sem essa distinção.
4. **Não acoplar a limpeza ao aceite F7** sem a decisão do operador. F4/F5 podem fechar com a coexistência documentada.

## 6. Ações executadas e limites desta sessão

- Inspeção de registries Positronic/Percival e do `config.json` do broker.
- Mapeamento de containers MCP por PID pai e idade.
- Nenhuma mutação em `config.json`, registry, transitions/audit/operator-password. Nenhum `docker stop`/`docker rm`/`docker kill`. Nenhum `update-image`/`configure`.
- A decisão sobre o Khan e a confirmação do critério de "limpo" permanecem com o operador.

