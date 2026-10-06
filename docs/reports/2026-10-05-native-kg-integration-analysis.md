# Integração nativa do knowledge graph no Percival — análise e plano

- **Data:** 2026-10-05
- **Autor:** Positronic (sessão `ses_ef233f3f2fferZO1dVyPyYx3p1`)
- **Projeto ativo:** Percival (`/home/bill/Projects/nanobot`)
- **Status:** análise concluída; decisões em aberto listadas em §9
- **Escopo lido:** `okf-bundle-core`, `percival-collective-memory`, `percival-acquire-knowledge`, `spa`, e os arquivos relevantes do nanobot (`docs/architecture.md`, `docs/memory.md`, `nanobot/agent/tools/{base,registry,loader,mcp}.py`, `nanobot/agent/{loop,memory}.py`, `nanobot/nanobot.py`, `nanobot/config/schema.py`, `webui/src/components/percival/PercivalSidebar.tsx`, `webui/src/lib/kg-interface.ts`, `pyproject.toml`, `hatch_build.py`).

## 1. Resumo executivo

Hoje o "cérebro" do Percival é composto por quatro projetos irmãos que conversam via MCP stdio/HTTP: o **bundle core** (`okf-bundle-core`, biblioteca determinística), dois **servidores MCP** que são apenas adaptadores de transporte sobre o core (`percival-collective-memory`, `percival-acquire-knowledge`), e uma **SPA React** que consome os adapters HTTP. A análise dos quatro projetos revela um fato estrutural decisivo:

> **Toda a lógica de domínio é puro Python puro, e o transporte MCP é um invólucro descartável.** As 26 + 20 ferramentas MCP expostas pelos dois servidores são funções Python tipadas em `tools.py` que recebem dataclasses e devolvem dataclasses, sem nenhum acoplamento ao MCP. O FastMCP só cola JSON-RPC ↔ essas funções.

Isso torna a integração nativa no Percival uma refatoração de **baixo risco e alto retorno**: criam-se subclasses `Tool` (a classe base abstrata em `nanobot/agent/tools/base.py`) que chamam diretamente as funções de domínio já existentes. O transporte MCP (subprocesso, JSON-RPC, timeouts, reconexão) sai do caminho crítico. Os servidores MCP podem ser aposentados como opt-in para compatibilidade, e a SPA passa a ser servida pelo próprio WebUI do nanobot em `/kg-interface/`, consumindo endpoints HTTP expostos pelo gateway.

Resultado esperado:

- **Zero configuração para o operador** — `pip install nanobot-ai` (ou a imagem Docker) já entrega o sistema de memória completo. Sem `enabledTools`, sem `mcpServers`, sem portas extras, sem dois processos a mais.
- **Bundle versionado em git e versionado com a aplicação** — a sincronização de versão (atualmente um problema em três pacotes separados) desaparece.
- **Mesma observabilidade e mesma segurança** — as ferramentas nativas vivem dentro do gateway, que já tem logging estruturado, política de workspace, autenticação de channel e auditoria.
- **SPA continua externa** — o build dela continua sendo Vite + Bun, e o `dist/` é embarcado na wheel do nanobot via um hatch hook (mesmo padrão do WebUI atual).

## 2. Estado atual — os quatro projetos e seus papéis

### 2.1. `okf-bundle-core` (biblioteca determinística)

Camada de domínio pura. **Sem transporte**, **sem MCP**, **sem I/O de rede**. Composta por:

| Módulo | Responsabilidade |
|---|---|
| `zettel.py` | `notes_read`, `notes_write` (CAS duplo D47), `notes_search` (ripgrep), `notes_delete`, escrita atômica, rollback em falha de I/O |
| `graph.py` | `build_graph` (extrai edges de frontmatter e body, NetworkX node-link) |
| `envelope.py` | `from_file`/`from_mcp` — envelope tipado com hashes SHA-256 |
| `gitstore.py` | `GitStore` (dulwich), `ensure_repo`, `commit_paths` (rejeita path-escape), `append_log` (markdown table) |
| `lock.py` | `BundleLock` (flock exclusivo com retry/timeout — Linux-only) |
| `schema.py` | `ZettelFrontmatter`, `SkillFrontmatter`, `SourceFrontmatter`, etc. (pydantic v2 com `extra="forbid"`) |
| `paths.py` | `BundleLayout` (frozen dataclass), `COLLECTIVE_MEMORY` e `ACQUIRED_KNOWLEDGE` pré-configurados, `resolve_safe_path` (anti path-traversal), `assert_asset_exists` |
| `storage.py` (P11) | `find_aging_candidates` (TTL de lifecycle), `get_storage_summary` (disco do bundle inteiro, `.git` incluso), `repo_maintenance` (`git gc` via dulwich) |
| `frontmatter.py` | `split_frontmatter` (BOM-safe), `serialize` (YAML `sort_keys=True`), `extract_links` (markdown-it AST — wikilinks em code fence são ignorados) |
| `validators.py` | `assert_not_blank`, `not_blank_validator`, `validate_id` |
| `errors.py` | `ZettelError` (com `code` discriminável), `CASMismatchError`, `PathEscapeError`, `ReservedPathError` |

É 261 testes passando, Pydantic v2 estrito, datetime em UTC, valores congelados. Tem uma API Python estável que o Percival pode chamar diretamente sem reescrever nada.

### 2.2. `percival-collective-memory` (servidor MCP de notas autorais)

Adiciona sobre o core: 7 de leitura (`notes_read`, `notes_search`, `note_history`, `memory_stats`, `asset_get_path`, `graph_neighbors`, `graph_shortest_path`), 4 de escrita (`notes_write`, `memory_link`, `memory_batch_link`, `memory_attach`, `memory_forget`), 1 de enriquecimento (`memory_enrich` via PydanticAI/MiniMax M3), 7 de policy/lifecycle (P11: `memory_set_protected`, `memory_set_lifecycle`, `memory_flag_for_review`, `memory_resolve_review`, `memory_storage_stats`, `memory_repo_maintenance`, `memory_aging_candidates`), 6 prompt primitives (`prompt_cm_overview`, `prompt_runbook_write_note`, `prompt_runbook_link`, `prompt_workflow_capture_session`, `prompt_audit_health`, `prompt_runbook_rebuild_graph`). Total: 26 ferramentas.

A regra arquitetural registrada no `tools.py:5-12` é explícita:

> "`tools.py` é função Python pura que recebe args tipados e devolve um Pydantic model. Testável sem MCP — só pytest. `server.py` é a cola FastMCP: converte args MCP → args Python, chama `tools.py`, devolve via MCP. Burocracia."

Esse é o ponto-chave para a integração nativa: a "burocracia" do FastMCP é literalmente um `@mcp.tool()` decorator e uma chamada JSON-RPC.

### 2.3. `percival-acquire-knowledge` (servidor MCP de aquisição multimodal)

Mesma arquitetura. 14 ferramentas de ingest/query/graph + 6 prompt primitives: `source_ingest`, `source_read`, `note_write_extracted`, `source_list`, `source_search`, `source_stats`, `get_laterally_isolated_notes`, `graph_neighbors`, `graph_shortest_path`, `source_forget`, `note_link`, `note_batch_link`, `image_caption`, `audio_transcribe`, mais os prompts `prompt_runbook_atomize`, `prompt_runbook_link`, `prompt_workflow_onboard_source`, `prompt_audit_health`, `prompt_guardrails_commit_policy`, `prompt_runbook_rebuild_graph`. Total: 20 ferramentas.

Diferença do CM: depende de **markitdown CLI** (subprocesso para PDF/DOCX/EPUB) e de **APIs externas** (MiniMax M3 para `image_caption`, Groq Whisper-large-v3 para `audio_transcribe`). Estas ferramentas de I/O de rede são o **único** motivo pelo qual o MCP server não é pura library — para a integração nativa, isso vira uma classe de Tool com subprocesso interno (mesmo padrão de `shell.py` no nanobot) e dois clientes HTTP/PydanticAI.

### 2.4. `spa` (SPA React de visualização)

React 18 + TypeScript + Vite + Tailwind 3 + Radix UI + Zod. 206 testes em Vitest + happy-dom. 432 KB gzipped. Hash routing manual (sem React Router). 16 endpoints HTTP consumidos via `src/lib/api.ts` com validação Zod-root `.passthrough()` (defesa contra feature drift) + `warnDiscardedFields` em DEV.

Endpoints consumidos hoje (todos MCP-only, com auth no edge via Cloudflare Access):

- **CM (porta 8001):** `/health`, `/memory/stats`, `/memory/notes`, `/memory/notes/:id`, `/memory/notes/:id/history`, `PUT /memory/notes/:id/body` (CAS D47), `DELETE /memory/notes/:id`, `/memory/search`, `/memory/graph`
- **AK (porta 8002):** `/health`, `/acquire/stats`, `/acquire/notes`, `/acquire/search`, `/acquire/sources`, `/acquire/sources/:id`, `/acquire/sources/:id/chunks/:idx`

### 2.5. Como o Percival consome isso hoje

```text
nanobot (cliente MCP)            SPA /kg-interface
        │ JSON-RPC stdio                  │ HTTP REST
        ▼                                ▼
  ┌─────────────────────┐    ┌─────────────────────┐
  │ CM MCP server :8001 │    │ http_server.py CM   │
  │ AK MCP server :8002 │    │ http_server.py AK   │
  └─────────┬───────────┘    └─────────┬───────────┘
            └──────────┬──────────────┘
                       ▼
            ┌──────────────────────┐
            │   okf-bundle-core    │
            │   (.collective-memory│
            │   .acquired-knowledge│
            │   + dulwich + ripgrep│
            └──────────────────────┘
```

O nanobot atual tem três pontos de entrada para MCP:

- `nanobot/nanobot.py:135` — `mcp_provider = MCPProvider.from_config(config, tools)` em `Nanobot.from_config`
- `nanobot/cli/{agent,commands,gateway_runtime}.py` — instanciam `MCPProvider.from_config` para `nanobot agent` e `nanobot gateway`
- `nanobot/webui/mcp_presets_api.py:1109` e `nanobot/webui/mcp_oauth_api.py:301` — sobem `MCPProvider` ad-hoc para inspeção de presets

A configuração fica em `config.tools.mcpServers` (`nanobot/config/schema.py:420`).

A WebUI atual do Percival (`webui/src/components/percival/PercivalSidebar.tsx`) já tem um link "Knowledge Graph" no sidebar que aponta para `/kg-interface/` (resolvido por `webui/src/lib/kg-interface.ts` em três níveis: build-time env, runtime detection para dev local em :8765/:5173, e default relativo `/kg-interface/`). Em produção (P10/Caddy) isso funciona porque o reverse-proxy serve a SPA e os adapters sob o mesmo origin.

## 3. A chave da integração: o transporte MCP é descartável

A arquitetura do MCP wrapper no nanobot (`nanobot/agent/tools/mcp.py:597-712`) é simples:

```python
class MCPToolWrapper(_MCPWrapperBase):
    def __init__(self, session, server_name, tool_def, ...):
        self._name = f"mcp_{server_name}_{tool_def.name}"  # sanitizado
        self._description = tool_def.description
        self._parameters = _normalize_schema_for_openai(tool_def.inputSchema)
        ...

    async def execute(self, **kwargs):
        result = await self._session.call_tool(self._original_name, arguments=kwargs)
        return self._render_call_result(result.content, kwargs)
```

E a base abstrata do nanobot (`nanobot/agent/tools/base.py:186-256`):

```python
class Tool(ABC):
    @property @abstractmethod
    def name(self) -> str: ...
    @property @abstractmethod
    def description(self) -> str: ...
    @property @abstractmethod
    def parameters(self) -> dict[str, Any]: ...
    async def execute(self, **kwargs) -> Any: ...
    def to_schema(self) -> dict[str, Any]: ...   # OpenAI function schema
```

As ferramentas MCP **são** Tools — o `MCPToolWrapper` é só uma `Tool` que serializa chamadas via JSON-RPC. Se escrevermos uma `Tool` que chame `tool_X` do pacote `percival_collective_memory.tools` diretamente, o resultado é indistinguível do ponto de vista do `AgentRunner`, com **zero transporte**.

A descoberta de Tools no nanobot é feita por varredura de pacote (`nanobot/agent/tools/loader.py:36-68`): `pkgutil.iter_modules` sobre `nanobot.agent.tools`, importa cada um, instancia cada subclasse de `Tool` que tenha um factory `Tool.create(ctx)` ou similar, e chama `registry.register(tool)`. **Adicionar tools nativas é só escrever arquivos novos nesse diretório.**

O `ToolRegistry` (`nanobot/agent/tools/registry.py:19-147`) ordena built-ins primeiro e MCP depois (`get_definitions` linhas 86-108), cacheia o resultado, e oferece `prepare_call` que faz cast/validate/execute. Tudo isso funciona do mesmo jeito se o tool for nativo.

`AgentLoop.from_config` (`nanobot/agent/loop.py:452-517`) recebe `tool_registry` injetado pelo caller e usa-o como application-owned. O caller (composition root) é quem decide o que registrar. **O caller vai simplesmente passar um registry com as tools nativas em vez do registry vazio que será populado pelo `MCPProvider`.**

## 4. Plano de integração nativa

A integração é uma refatoração incremental. Em nenhum momento o operador precisa reconfigurar nada para começar a usar — as ferramentas nativas entram **enabled by default** e os servidores MCP podem ser aposentados como opt-in (`enabled_mcp_servers: list[str]` no config) para quem já tinha deployments montados.

### 4.1. Dependências e empacotamento

A escolha entre **workspace member** e **dependência publicada** afeta quem faz o lock e quem é a fonte de verdade do versionamento. Os números do `okf-bundle-core/README.md:45-83` mostram que ele nasceu para ser workspace member do monorepo `mcp-servers-percival`; no Percival a decisão se inverte — ou ele vira dependência publicada, ou vira submódulo/vendor dentro do nanobot.

**Recomendação:** começar como **vendored copy** sob `nanobot/agent/kg/vendor/okf_bundle_core/` (mover o código com um único commit, atualizando imports relativos para o novo caminho) — a superfície é estável, o versionamento fica atrelado ao nanobot, e elimina a fricção de manter três repos sincronizados. Subir `okf-bundle-core` para PyPI público é uma decisão posterior — útil quando outros projetos fora do Percival quiserem consumir, mas não é pré-requisito.

Os pacotes consumidores (`percival_collective_memory`, `percival_acquire_knowledge`) **não** precisam ser vendorizados. Eles expõem funções de ferramentas que já são wrappers sobre o core. Para a integração nativa, escrevemos `Tool` subclasses que chamam essas funções diretamente (importando de `okf_bundle_core` direto), reaproveitando a lógica de `tools.py` por copy-paste gradual. Manter os pacotes como opcionais (no PyPI, para quem quiser usá-los via MCP) preserva o ecossistema atual.

### 4.2. Camada de Tools nativos (substituindo os wrappers MCP)

Novo módulo `nanobot/agent/kg/` (Knowledge Graph — nome neutro que reflete o domínio, não os nomes dos pacotes):

```
nanobot/agent/kg/
├── __init__.py                 # registra todas as tools no ToolRegistry
├── _bundle.py                  # descoberta do bundle (env, workspace, cwd/ancestral)
├── _layout.py                  # COLLECTIVE_MEMORY / ACQUIRED_KNOWLEDGE / path safe
├── _errors.py                  # tradução okf_bundle_core.errors → ToolResult.error
├── _registry.py                # factories para injeção no ToolRegistry
├── cm/
│   ├── __init__.py
│   ├── core.py                 # notes_read, notes_search, notes_write, notes_delete
│   ├── links.py                # memory_link, memory_batch_link, memory_attach
│   ├── history.py              # note_history
│   ├── stats.py                # memory_stats, asset_get_path
│   ├── graph.py                # graph_build, graph_neighbors, graph_shortest_path
│   ├── policy.py               # memory_set_protected, memory_set_lifecycle,
│   │                           # memory_flag_for_review, memory_resolve_review
│   ├── storage.py              # memory_storage_stats, memory_repo_maintenance,
│   │                           # memory_aging_candidates
│   ├── enrich.py               # memory_enrich (LLM via PydanticAI, MiniMax M3)
│   ├── forget.py               # memory_forget
│   └── prompts.py              # 6 prompt primitives (mesma estratégia do AK)
├── ak/
│   ├── __init__.py
│   ├── ingest.py               # source_ingest (markitdown subprocess)
│   ├── read.py                 # source_read, source_list, source_search,
│   │                           # source_stats, get_laterally_isolated_notes
│   ├── write.py                # note_write_extracted, note_link, note_batch_link
│   ├── graph.py                # graph_neighbors, graph_shortest_path
│   ├── multimodal.py           # image_caption (MiniMax M3), audio_transcribe (Whisper)
│   ├── forget.py               # source_forget
│   └── prompts.py              # 6 prompt primitives
└── config.py                   # dataclass PercivalKgConfig (read-only, defaults sensatos)
```

Cada tool é uma `Tool` subclass com o decorator `@tool_parameters({...})` (existente em `nanobot/agent/tools/base.py:381-413`) e método `async def execute(...)` que delega para a função pura do core. O exemplo abaixo é ilustrativo:

```python
# nanobot/agent/kg/cm/core.py (esboço)

@tool_parameters({
    "type": "object",
    "properties": {
        "id": {"type": "string", "pattern": r"^\d{8}-\d{6}$"},
    },
    "required": ["id"],
    "additionalProperties": False,
})
class CmNotesReadTool(Tool):
    """Lê uma nota do bundle .collective-memory."""

    @property
    def name(self) -> str: return "cm_notes_read"
    @property
    def description(self) -> str: return "Read a zettel note by id (YYYYMMDD-HHMMSS)."
    @property
    def parameters(self) -> dict[str, Any]: ...  # injetado pelo decorator

    async def execute(self, *, id: str) -> str:
        root = cm_bundle_root()        # _bundle.py
        layout = COLLECTIVE_MEMORY
        try:
            r = notes_read(root, layout, id)
        except FileNotFoundError as e:
            return ToolResult.error(f"nota não encontrada: {e}")
        except ZettelError as e:
            return ToolResult.error(f"{e.message} [{e.code}]")
        return json.dumps({
            "id": r.id, "path": str(r.path),
            "frontmatter": r.frontmatter.model_dump(by_alias=True, exclude_unset=True),
            "body": r.body,
            "content_hash": r.content_hash, "body_hash": r.body_hash,
            "backlinks": r.backlinks,
        }, ensure_ascii=False)
```

Naming: o prefixo `cm_` / `ak_` no nome da tool reflete a origem do bundle e preserva a correspondência 1-pra-1 com os nomes dos servidores MCP antigos, o que ajuda a migração de skills já escritas (uma skill que diz `notes_read(id=...)` no MCP continua funcionando se a skill for atualizada para chamar `cm_notes_read(id=...)`). Nomes alternativos discutidos em §9.

**Onde mora `memory_enrich`:** é a única tool que faz I/O de rede. Mantém o cliente `OpenAI` (MiniMax M3 é OpenAI-compat) instanciado por `nanobot/agent/kg/cm/enricher.py` e respeita o `tool_timeout` do registry. O `CM_ENRICH_TIMEOUT_S` (default 45s) do CM vira default no `Tool.timeout` da classe.

### 4.3. Descoberta do bundle

O helper `_bundle.py` replica a lógica de `percival_collective_memory/paths.py:51-94` e `percival_acquire_knowledge/paths.py`, mas com fallback adicional para o **workspace do nanobot** (já carregado por `AgentLoop`):

```python
def cm_bundle_root(workspace: Path) -> Path:
    # 1. PERCIVAL_CM_ROOT (env) — pai; helper devolve <pai>/.collective-memory
    # 2. <workspace>/.collective-memory  (NANOBOT_WORKSPACE já é conhecido)
    # 3. cwd/ancestral procurando .collective-memory
    raise BundleNotFoundError(...)  # se nenhum casar
```

A diferença em relação à versão MCP é que `_bundle.py` recebe o `workspace` do nanobot injetado via `Tool.create(ctx)` (vide `nanobot/agent/tools/base.py:246-247` — `Tool.create(ctx)` é o ponto de injeção), o que elimina uma consulta à env. O comportamento continua compatível com `NANOBOT_WORKSPACE` para casos em que o bundle vive em workspace diferente do agent workspace.

A função `_resolve_bundle_arg` do `okf_bundle_core.paths.py:77-111` já normaliza bundle-vs-pai — é o que os dois servidores chamam via wrapper. Reaproveitar diretamente.

### 4.4. API HTTP para a SPA

A SPA consome 16 endpoints hoje. Para a integração nativa, expostos pelo **gateway do nanobot** (que já é FastAPI/Starlette) sob `/kg-interface/api/`:

| Método | Rota (SPA) | Equivalente nativo |
|---|---|---|
| GET | `/memory/stats` | `_kg_stats_cm()` |
| GET | `/memory/notes` | `_kg_list_cm()` |
| GET | `/memory/notes/{id}` | `_kg_read_cm(id)` |
| GET | `/memory/notes/{id}/history` | `_kg_history_cm(id)` |
| PUT | `/memory/notes/{id}/body` | `_kg_update_body_cm(id, body, base_body_hash)` |
| DELETE | `/memory/notes/{id}` | `_kg_archive_cm(id, reason)` |
| GET | `/memory/search?q=` | `_kg_search_cm()` |
| GET | `/memory/graph` | `_kg_graph_metadata_cm()` |
| POST | `/memory/notes/{id}/enrich` | `_kg_enrich_cm()` |
| PUT | `/memory/notes/{id}/protected` | `_kg_set_protected_cm()` |
| PUT | `/memory/notes/{id}/lifecycle` | `_kg_set_lifecycle_cm()` |
| POST | `/memory/notes/{id}/flag` | `_kg_flag_cm()` |
| POST | `/memory/notes/{id}/resolve` | `_kg_resolve_cm()` |
| GET | `/memory/storage/stats` | `_kg_storage_stats_cm()` |
| POST | `/memory/storage/maintenance` | `_kg_repo_maintenance_cm()` |
| GET | `/memory/lifecycle/candidates` | `_kg_aging_candidates_cm()` |
| (e os 7 do AK: `/acquire/stats`, `/acquire/notes`, `/acquire/search`, `/acquire/sources`, `/acquire/sources/{id}`, `/acquire/sources/{id}/chunks/{idx}`) | | |

Os endpoints moram em `nanobot/channels/websocket/kg_router.py` (mesmo padrão do WebSocket channel). O roteamento para `/kg-interface/api/memory/*` ↔ `/kg-interface/api/acquire/*` continua o mesmo — o que muda é que **não há mais reverse proxy externo**: o gateway do nanobot serve a SPA estática, roteia `/kg-interface/{rest}` para o SPA `dist/`, e `/kg-interface/api/*` para o `kg_router` interno.

A camada `http_server.py` dos dois pacotes MCP vira obsoleta. A lógica que ela continha (validação Pydantic dos bodies, conversão para o dataclass de `tools.py`) migra para o `kg_router` do nanobot, usando os mesmos `BaseModel`s que já existem em `percival_collective_memory/server.py` — eles continuam válidos como contrato HTTP, mesmo que o transporte MCP não esteja.

**Pontos a considerar:**

- **Auth.** Hoje a SPA é protegida no edge (Cloudflare Access, D51). Quando o gateway serve a SPA internamente, a autenticação migra para o próprio gateway — o WebUI já tem canal de autenticação (loopback-only por default, LAN-configurável). A mesma política se aplica: localhost não exige nada, LAN requer o mesmo gate que o WebUI exige hoje.
- **CORS.** O gateway serve SPA e API no mesmo origin (`/kg-interface/*`), então CORS some. O proxy de dev (`vite.config.ts:server.proxy` em `webui/`) continua útil mas o alvo vira o próprio gateway em `127.0.0.1:8765`.
- **Limites de payload.** O CM já tem `WriteBodyRequest` com `max_length=2 MiB`; a defesa continua.
- **Timeouts.** `memory_enrich` precisa do teto de 45s. Outros endpoints ficam abaixo do `toolTimeout` default (30s). O gateway tem `ReadTimeout` próprio e o roteador FastAPI precisa de timeout explícito por rota (`asyncio.wait_for` ou `TimeoutMiddleware`).

### 4.5. Empacotamento da SPA no WebUI

O WebUI atual do nanobot já tem um hatch hook (`hatch_build.py`) que constrói `webui/` em `nanobot/web/dist/` durante o `pip install`. Para a SPA, o padrão se replica:

- `nanobot/web/kg-interface/` é o destino do `bun run build` da SPA (`spa/` → `nanobot/web/kg-interface/`).
- Hook detecta se `nanobot/kg-interface-source/package.json` existe (repositório SPM opcional para a SPA dentro do nanobot) e roda `bun install && bun run build`.
- Sem source tree, usa `nanobot/web/kg-interface/` pré-built (idem ao WebUI).
- O `nanobot/channels/websocket/runtime.py` (ou um novo `nanobot/web/kg_router.py`) monta o `StaticFiles` para `/kg-interface/{rest}` e o roteador FastAPI para `/kg-interface/api/*`.

A SPA continua sendo desenvolvida no repositório separado `https://github.com/bill-kopp-ai-dev/spa.git`. **Não** é um submódulo do nanobot — o lockfile (`bun.lock`) é gerenciado pela SPA, e o nanobot só consome o `dist/` final.

A consequência é que **desenvolvedores da SPA** continuam trabalhando em `~/Projects/spa` com `bun run dev` (apontando para `127.0.0.1:8765`/`/kg-interface/api/*` que o gateway serve com as tools nativas — fim dos dois adapters HTTP laterais no `dev-spa.sh`). **Desenvolvedores do nanobot** que mexem nas tools nativas rodam o gateway e abrem a SPA servida por ele; ou, se quiserem hot-reload da SPA, montam um script que copia `spa/dist/` para `nanobot/web/kg-interface/` em watch.

### 4.6. CLI de diagnóstico

As três CLIs atuais (`cm-doctor`, `ak-doctor`, `cm-graph-rebuild`, `ak-graph-rebuild`, `cm-p11-bootstrap`) viram sub-comandos de uma CLI única `nanobot kg`:

```bash
nanobot kg doctor              # checa bundle roots, rg, API keys, enabled_tools nativo
nanobot kg doctor --json
nanobot kg graph rebuild cm    # reconstrói graph.json do CM
nanobot kg graph rebuild ak    # reconstrói graph.json do AK
nanobot kg graph rebuild all
nanobot kg p11 bootstrap --dry-run --apply    # P11 da CM
nanobot kg bundle path cm      # mostra o bundle root resolvido
nanobot kg bundle path ak
```

Isso elimina o versionamento de quatro binários (`cm-doctor`, `ak-doctor`, `cm-graph-rebuild`, `ak-graph-rebuild`, `cm-p11-bootstrap`) e simplifica a documentação. As skills do agente que hoje chamam `cm-doctor` no shell passam a chamar `nanobot kg doctor` (com fallback para o binário externo se o servidor MCP estiver habilitado).

### 4.7. Skills do agente

O diretório `workspace/skills/collective-memory/SKILL.md` e `workspace/skills/acquire-knowledge/SKILL.md` (referenciados nos READMEs dos servidores) viram skills built-in do nanobot em `nanobot/skills/`:

```
nanobot/skills/
├── kg/
│   ├── SKILL.md                 # visão unificada do sistema de memória
│   ├── cm/
│   │   ├── SKILL.md             # disciplina de uso do CM
│   │   └── workflows/
│   │       ├── capture-session.md
│   │       ├── write-note.md
│   │       ├── maintenance.md   # memory-care: aging + protected + lifecycle
│   │       └── graph-rebuild.md
│   └── ak/
│       ├── SKILL.md
│       └── workflows/
│           ├── onboard-source.md
│           ├── atomize.md
│           └── graph-rebuild.md
```

Esses skills substituem os prompts (`prompt_*`) que os dois servidores MCP expunham como ferramentas de guidance. Hoje eles são funções Python (`@mcp.tool()` retornando Markdown estático) chamadas pelo agente antes de operações pesadas; no modelo nativo, eles viram **arquivos SKILL.md** descobertos pelo `SkillsLoader` (`nanobot/agent/context.py:99` já instancia `SkillsLoader`), e o agente os lê sob demanda via a tool `read_skill` ou via SystemPrompt (mesmo esquema do `nanobot/skills/memory/SKILL.md` atual).

**Decisão de arquitetura registrada:** `@mcp.tool()` retornando string Markdown foi o "delegate non-spec do MCP" usado pelos dois servidores porque a allowlist `enabledTools` do nanobot não pegava `@mcp.prompt()`. No modelo nativo, essa desculpa some: SKILL.md é o veículo canônico, e o agente já sabe consumir.

## 5. Estrutura de arquivos proposta

Resumo das adições (sem contar testes, que replicam o padrão `tests/`):

```
nanobot/
├── agent/
│   └── kg/                              # NOVO — tools nativas
│       ├── __init__.py
│       ├── _bundle.py
│       ├── _layout.py
│       ├── _errors.py
│       ├── _registry.py
│       ├── config.py
│       ├── cm/  (10 arquivos)
│       └── ak/  (7 arquivos)
├── skills/
│   └── kg/                              # NOVO — substitui workspace/skills/{collective,acquire}-memory
│       ├── SKILL.md
│       ├── cm/
│       └── ak/
├── cli/
│   └── kg.py                            # NOVO — `nanobot kg` subcomandos
├── web/
│   └── kg-interface/                    # NOVO — embedded SPA dist (managed by hatch hook)
├── channels/websocket/
│   ├── kg_router.py                     # NOVO — FastAPI router para /kg-interface/api/*
│   └── kg_static.py                     # NOVO — StaticFiles mount para /kg-interface/{rest}
└── config/
    └── kg.py                            # NOVO — PercivalKgConfig dataclass + schema entry

nanobot/hatch_build.py                   # MODIFICADO — hook adicional para SPA
nanobot/agent/tools/loader.py            # (SEM EDITAR, descoberta automática)
nanobot/nanobot.py                       # MODIFICADO — ToolRegistry com KG tools registradas por padrão
nanobot/cli/{agent,commands,gateway_runtime}.py
                                        # MODIFICADO — passa KG tools ao ToolRegistry
nanobot/config/schema.py                 # MODIFICADO — kg: PercivalKgConfig | None (default habilitado)
webui/src/components/percival/PercivalSidebar.tsx  # (SEM EDITAR — link já existe)
webui/src/lib/kg-interface.ts            # (SEM EDITAR — URL já relativa)
```

Pacotes de fora que ficam **inalterados** mas viram opcionais (movidos para `[kg]` extra opcional no `pyproject.toml`):

- `percival-collective-memory` → `[project.optional-dependencies].kg-mcp`
- `percival-acquire-knowledge` → `[project.optional-dependencies].kg-mcp`
- `spa` → não é Python; continua repo externo, o `dist/` é só consumido pelo hatch hook

## 6. Fases de implementação

| Fase | Entrega | Critério de aceite |
|---|---|---|
| **0. Fundação** | `pyproject.toml` ganha `[kg]` extra com `okf-bundle-core` (workspace/path dep); vendor in `agents/kg/vendor/okf_bundle_core/` ou dep declarada; hatch hook novo para SPA; `nanobot/kg-interface-source/` é mesmo material do `spa/`. | `uv sync --extra kg` instala o core e builda a SPA; `nanobot --version` reporta versão do KG; `nanobot kg doctor` (mesmo antes das tools) responde com diagnóstico mínimo |
| **1. Tools CM core (read/write/search/delete/history)** | `nanobot/agent/kg/cm/core.py` com `cm_notes_read`, `cm_notes_write`, `cm_notes_search`, `cm_notes_delete`, `cm_note_history`; `_bundle.py` para CM | `pytest tests/test_kg_cm_core.py` cobre happy path, CAS, rollback, link edges. Integração via `Nanobot.from_config(...)` + `agent -m "cria nota 20261005-100000 sobre X"` resulta em nota commitada no bundle |
| **2. Tools CM links/stats/policy/storage** | `cm_memory_link`, `cm_memory_batch_link`, `cm_memory_attach`, `cm_memory_stats`, `cm_memory_set_protected`, `cm_memory_set_lifecycle`, `cm_memory_flag_for_review`, `cm_memory_resolve_review`, `cm_memory_storage_stats`, `cm_memory_repo_maintenance`, `cm_memory_aging_candidates` | skill `memory-care` portada para `nanobot/skills/kg/cm/workflows/maintenance.md` chama essas tools e roda em CI |
| **3. Tools CM enrich + prompts** | `cm_memory_enrich` (PydanticAI/MiniMax M3), 6 prompt primitives movidas para SKILL.md | chamada `cm_memory_enrich(note_id=...)` retorna tags/summary; SKILL.md visível no WebUI Skills → Installed |
| **4. Tools AK ingest/read/multimodal** | `ak_source_ingest`, `ak_source_read`, `ak_source_list`, `ak_source_search`, `ak_source_stats`, `ak_image_caption`, `ak_audio_transcribe`; markitdown subprocess gerenciado pelo mesmo padrão de `shell.py` | `nanobot agent -m "ingere /tmp/foo.pdf e cria 3 notas"` produz 3 `ExtractedNote` em `.acquired-knowledge/notes/` |
| **5. Tools AK write/links/forget + graph** | `ak_note_write_extracted`, `ak_note_link`, `ak_note_batch_link`, `ak_get_laterally_isolated_notes`, `ak_source_forget`, `ak_graph_neighbors`, `ak_graph_shortest_path` | skill `memory-graph-rebuild` roda fim-a-fim com ambas as tools |
| **6. kg_router FastAPI** | `nanobot/channels/websocket/kg_router.py` expõe os 16 endpoints (CM + AK) sob `/kg-interface/api/*`; `kg_static.py` serve `/kg-interface/{rest}` | `curl http://127.0.0.1:8765/kg-interface/api/memory/stats` devolve JSON; `curl http://127.0.0.1:8765/kg-interface/index.html` devolve o HTML da SPA |
| **7. SPA embarcada** | hatch hook builda `nanobot/web/kg-interface/`; `vite.config.ts` da SPA ganha `outDir` para `nanobot/web/kg-interface/`; build do nanobot sem source da SPA usa prebuilt | `pip install nanobot-ai` num venv novo e `nanobot gateway` já servem `/kg-interface/` funcional |
| **8. CLI `nanobot kg`** | unifica `cm-doctor`, `ak-doctor`, `cm-graph-rebuild`, `ak-graph-rebuild`, `cm-p11-bootstrap` | `nanobot kg doctor --json` retorna mesmo output que `cm-doctor --json` |
| **9. Skills + deprecation path** | `nanobot/skills/kg/` SKILL.md; documentação em `docs/reports/`; `mcpServers` URL `mcpServers["percival-collective-memory"].enabled = false` por default mas ainda funcional | guia de migração publicado; deploy existente continua funcionando se setar `kg.mcpServers.compat = true` |

## 7. Compatibilidade com MCP servers existentes

A integração nativa **não quebra** o uso dos servidores MCP antigos — ela só adiciona um caminho mais simples. Três opções de coexistência:

| Modo | Comportamento | Quando usar |
|---|---|---|
| `kg.mode = "native"` (default) | Tools nativos registrados, MCP servers ignorados | Default para novos deploys |
| `kg.mode = "mcp"` | Tools nativos **não** carregados, MCP servers (config `mcpServers`) registrados como antes | Migração gradual, de quem já tem o stack MCP completo em produção |
| `kg.mode = "both"` | Ambos registrados; tools nativos ganham `mcp_native_` prefix para evitar colisão com `mcp_{server}_{tool}` do wrapper | A/B testing, transição segura |

O campo `kg` em `nanobot/config/schema.py` ganha uma entrada no schema `Config`:

```python
class PercivalKgConfig(Base):
    mode: Literal["native", "mcp", "both"] = "native"
    # Resolução dos bundles. None = auto-discovery; str = path explícito (pai).
    cm_root: str | None = None
    ak_root: str | None = None
    # Enriquecimento (P11 + LLM tools) — opt-out para deploys que não têm LLM.
    cm_enrich_enabled: bool = True
    ak_image_caption_enabled: bool = True
    ak_audio_transcribe_enabled: bool = True
    # Compatibilidade MCP — quando True, mantém o bloco mcpServers funcional.
    mcp_compat: bool = True
```

Quando `kg.mode = "native"` e o operador deixou o bloco `mcpServers` com os dois servidores configurados (caso típico de quem está migrando), o `Nanobot.from_config` loga um warning e ignora as entradas CM/AK — `mcp_cm_*` e `mcp_ak_*` não aparecem. Quando `mcp_compat = false`, qualquer entrada `mcpServers` para os dois vira erro duro de validação.

O `mcp_presets_api.py` do WebUI continua funcional para outros servidores MCP (`percival-osm`, `percival-weather-mcp`, etc.) — só CM e AK migram pra nativo; o resto segue MCP.

## 8. Riscos e trade-offs

**Risco 1 — Superfície de testes duplicada.** O `okf-bundle-core` tem 261 testes, CM tem 184, AK tem 213 — total de ~660 testes em três pacotes que, na nova arquitetura, são cobertos pelo `nanobot/kg/` nativo. **Mitigação:** rodar a suite nativa contra os mesmos fixtures (golden CM, golden AK em `okf_bundle_core/tests/fixtures/`), e portar gradualmente os tests específicos do CM/AK que cobrem regras de policy (P11, CAS avançado, batch_link) que o core não cobre. Tests do HTTP server MCP viram tests do `kg_router` (mesmo fixtures, mesmo `http` client).

**Risco 2 — Distribuição do `okf-bundle-core`.** Se virar dep publicada no PyPI, ganha barreira de release (qualquer bugfix no core exige bump de versão + publicação). Se virar vendored, qualquer melhoria upstream precisa de cherry-pick. **Mitigação:** começar vendored (mais simples, menos partes móveis); avaliar publicação no PyPI se outros projetos (não-Percival) aparecerem consumindo. **Atualização 2026-10-06:** a política posterior em [`docs/percival-governance.md`](../percival-governance.md) e no `RUNBOOK-sync-upstream.md` prefere patches/cherry-picks selecionados; merge amplo é exceção.

**Risco 3 — Autenticação/authz da SPA.** Cloudflare Access cobre a SPA atual no edge. Quando a SPA migra para dentro do gateway do nanobot, a auth precisa ser imposta pelo gateway. O WebUI do nanobot já tem autenticação por canal (loopback-only default), mas a SPA não passa pelo canal — ela é servida como estático. **Mitigação:** o gateway exige o mesmo cookie/auth do WebUI para `/kg-interface/api/*` (mesmo middleware `nanobot/security/network.py` + auth do WebSocket channel). O `/kg-interface/{rest}` (estático da SPA) só é exposto se a sessão WebUI está autenticada; caso contrário, devolve 401 com redirect para o WebUI.

**Risco 4 — Cross-bundle edits (P11 C17).** A SPA atual proíbe edits cross-bundle na UI. As tools nativas também precisam recusar (ex.: `cm_memory_link(from_id=cm_note, to_id=ak_extracted_note)` é uma violação do contrato). **Mitigação:** uma invariante em `_bundle.py` que rejeita `from_id` cujo prefixo do bundle não bate o bundle ativo da tool; testes parametrizados em `tests/test_kg_cross_bundle.py`.

**Risco 5 — Single-user vs multi-tenant.** `okf-bundle-core` é local-filesystem com flock — funciona para um único agente por workspace. Para multi-tenant (vários usuários no mesmo gateway), o flock não basta. **Mitigação:** a restrição já existe no WebUI do nanobot (uma sessão por usuário, isolation por `workspace_id`). Documentar explicitamente que o KG nativo herda essa restrição; deployments multi-tenant com KG compartilhado precisam de isolamento via workspaces separados (mesma estratégia atual).

**Risco 6 — Bundle root permission.** O `_bundle.py` precisa ser resiliente a `PermissionError`, `OSError`, e a workspaces que somem. **Mitigação:** erros tipados do `okf_bundle_core` (`BundleNotFoundError`, `FileNotFoundError`, `ZettelError`) traduzidos para `ToolResult.error` com mensagens úteis + sugestão (`"verifique PERCIVAL_CM_ROOT ou crie .collective-memory no workspace"`).

**Trade-off — Tamanho da wheel.** Adicionar a SPA dist aumenta a wheel em ~430 KB gzipped. A wheel atual já inclui o WebUI (~ mesmo tamanho), então o delta é marginal. Trade-off favorável.

**Trade-off — Acoplamento entre nanobot e o core.** O core tem seus próprios D-numbers (D33, D47, D65, D105, D-Prompt-1, P9, P11) que viram comentários em código e testes. Misturar com a documentação do nanobot cria ruído. **Mitigação:** seção `docs/architecture.md` ganha um parágrafo "Knowledge Graph nativo" referenciando `docs/kg/` (sub-pasta nova); o core vendorizado mantém seu `README.md` e `CHANGELOG.md` próprios, e as D-rules ficam onde nasceram.

## 9. Perguntas em aberto (precisam de decisão antes da F0)

1. **Naming dos tools.** Prefixo `cm_` / `ak_` (preserva correspondência com MCP, exige atualizar skills), ou prefixo neutro `note_` / `source_` (mais limpo, diverge dos servidores MCP, exige alias mapping)? Trade-off: simplicidade vs continuidade.
2. **Empacotamento do core.** Vendored (`nanobot/agent/kg/vendor/okf_bundle_core/`) ou dep publicada (PyPI `okf-bundle-core`, atualizada pelo monorepo `mcp-servers-percival`)? Trade-off: autonomia do Percival vs manutenção upstream.
3. **Empacotamento da SPA.** Hatch hook que builda de `spa/` no momento do `pip install` (precisa do source tree), ou só consome `nanobot/web/kg-interface/` prebuilt (rebuild manual pelos mantenedores da SPA)? Trade-off: praticidade para o dev do Percival vs complexidade do build.
4. **Default habilitado ou opt-in?** `kg.mode = "native"` por default (força migração imediata, exige cuidado com deploys existentes) ou `kg.mode = "mcp"` por default (preserva comportamento atual, migração explícita)? Trade-off: convenience vs safety. Recomendação: `native` por default, `mcp` opt-in.
5. **Compatibilidade dos pacotes MCP no PyPI.** Manter `percival-collective-memory` e `percival-acquire-knowledge` publicados como servidores MCP standalone (para usuários fora do Percival) ou descontinuar (foco total no Percival)? Trade-off: comunidade vs foco. Recomendação: manter publicados como v0.x com aviso de EOL.
6. **CM enrich: MiniMax M3 ou abstração?** Hoje o core depende de OpenAI-compat (MiniMax M3). Generalizar para "qualquer provedor configurado em `providers` no nanobot" simplifica deploys que já têm provider configurado, mas amarra o KG ao registry de providers do nanobot. Trade-off: reuso vs isolamento.
7. **`memory_enrich` timeout.** Manter 45s hardcoded, expor via `kg.cm_enrich_timeout_s`, ou ler de `agents.defaults.llm_runtime.timeout`? Trade-off: previsibilidade vs coerência com config de provider.
8. **Graph export para o `GraphView` da SPA.** Hoje o `graphify` exporta `graph.html` que a SPA serve via iframe sandbox. O `GraphView` já tolera `graph.html` ausente (overlay de 404 no README da SPA). Solução: `nanobot kg graph export` empacota `graph.html` no diretório `nanobot/web/kg-interface/graphify/` em build time; ou a SPA migra para visualizador nativo (D3/cytoscape) que consome `graph.json` direto. Trade-off: simplicidade vs esforço de reescrita da SPA.
9. **Testes do dev-spa.sh.** Hoje o script sobe CM e AK como processos separados. Com a integração nativa, o script vira opcional (só útil para quem ainda usa os MCP servers). Trade-off: cleanup vs retrocompatibilidade do tooling.
10. **`AGENTS.md` dos quatro projetos.** Os três repos Python têm `AGENTS.md` próprio (escritos pelo upstream). Manter (referência útil), absorver (uma fonte só), ou descontinuar (não fazem sentido sem MCP)? Trade-off: clareza vs centralização.

## 10. Verificação proposta

Esta análise não roda nenhuma verificação (é só leitura). As verificações concretas entram nas fases 0–9 do §6. Resumo do que precisa ser executável ao final:

| Comando | Cobertura | Fonte do gate |
|---|---|---|
| `pytest tests/test_kg_*.py` | Tools nativos (CM, AK, cm_enrich, cross-bundle) | `pyproject.toml [tool.pytest.ini_options]` |
| `pytest` (suite completa) | Não-regressão | igual ao upstream |
| `basedpyright nanobot` | Typecheck estrito | igual ao upstream |
| `ruff check .` | Lint (NÃO `ruff format` — regra do AGENTS.md) | igual ao upstream |
| `bun run test` na SPA | Não-regressão do frontend | `spa/` repo |
| `bun run build` na SPA | SPA empacotável em `nanobot/web/kg-interface/` | hatch hook |
| `nanobot kg doctor --json` em smoke | Integração end-to-end | novo |

## 11. Apêndice — referências cruzadas

- `nanobot/agent/tools/base.py:186-256` — `Tool` classe base abstrata (a integração nativa só precisa dela).
- `nanobot/agent/tools/registry.py:19-147` — `ToolRegistry` (registro, dispatch, schema cache).
- `nanobot/agent/tools/loader.py:36-68` — discovery por varredura de pacote (zero cerimônia para adicionar tools).
- `nanobot/agent/tools/mcp.py:597-712` — `MCPToolWrapper` (o que deixa de ser necessário para CM/AK).
- `nanobot/agent/loop.py:452-517` — `AgentLoop.from_config` injeta o registry (composition root onde a decisão `native` vs `mcp` se aplica).
- `nanobot/nanobot.py:135` — onde o `MCPProvider.from_config(config, tools)` é chamado hoje.
- `nanobot/config/schema.py:420` — `mcp_servers: dict[str, MCPServerConfig]` (ganha `kg: PercivalKgConfig`).
- `nanobot/hatch_build.py` — hook que builda webui (replicar para SPA).
- `okf_bundle_core/src/okf_bundle_core/zettel.py:1-820` — API Python pura a ser chamada pelas tools nativas.
- `okf_bundle_core/src/okf_bundle_core/paths.py:47-74` — `COLLECTIVE_MEMORY` e `ACQUIRED_KNOWLEDGE` (reaproveitar).
- `percival_collective_memory/src/percival_collective_memory/tools.py:1-200` — padrão `tools.py` puro Python que reescrevemos em `nanobot/agent/kg/cm/`.
- `webui/src/components/percival/PercivalSidebar.tsx` — link "Knowledge Graph" no sidebar (já existe; vira 100% funcional sem MCP).
- `webui/src/lib/kg-interface.ts` — resolução de URL `/kg-interface/` (já relativa; funciona com gateway servindo a SPA).
- `docs/Decisions/2026-10-05-merge-percival-branding.md` — decisão recente de branding que se alinha naturalmente com esta integração (o link KG já existe na Sidebar Percival).
- `RUNBOOK-sync-upstream.md` — integração seletiva de melhorias do `HKUDS/nanobot` em branch do Percival (política atualizada 2026-10-06; merge amplo apenas excepcionalmente).

## 12. Recomendação operacional

Seguir o plano das fases 0–9 em ordem, com **gate explícito** entre cada fase: cada bloco precisa rodar a suite completa (`pytest`, `basedpyright`, `ruff`, `bun run test`) antes de avançar. A fase 0 (fundação) é a única que afeta infra fora de `nanobot/agent/kg/` (mudança no `pyproject.toml`, hatch hook); as fases 1–5 são puramente adições dentro de `nanobot/agent/kg/`; a fase 6 introduz o `kg_router` que será gradualmente promovido a default; a fase 7 substitui o deploy atual; a fase 8 unifica CLIs; a fase 9 fecha a migração com skills + deprecation guide.

**Marcar este relatório como ADR-pendente** até que as 10 perguntas abertas em §9 sejam respondidas — várias delas têm impacto não-trivial (especialmente 1, 2 e 4) e moldam a forma final da fase 0.

---

**Versão:** 0.1 (draft para revisão)
**Próximos passos sugeridos:** discutir §9 em sequência com o operador; abrir ADR (em `docs/Decisions/`) com as decisões consolidadas antes de iniciar a fase 0.
