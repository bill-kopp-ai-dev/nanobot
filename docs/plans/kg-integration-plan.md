# Plano de implementação — knowledge graph nativo do Percival

- **Data:** 2026-10-05; **revisão:** 2026-10-05 (confronto com o código-fonte).
- **Estado:** F0 permanece parcialmente aberto; implementação e gate local de F1 (4 tools CM) concluídos. Evidências e limites no [relatório de execução](../reports/2026-10-05-kg-f0-execution-status.md). F0 não foi liberada globalmente.
- **Origem:** [análise técnica](../reports/2026-10-05-native-kg-integration-analysis.md). Este plano prevalece onde o relatório ou a versão inicial divergirem do código atual.
- **Escopo:** CM, AK, core e SPA nativos no fork; preservar os formatos de bundle e a interface operacional existente. Docker-MCP genérico do Percival é outro trabalho.

## 1. Decisões mantidas e correções da revisão

| ID | Decisão da sessão | Interpretação executável |
| --- | --- | --- |
| D1 | Prefixos `cm_*`/`ak_*` | Prefixar os nomes públicos das **tools operacionais**; prompt primitives viram skills, não tools adicionais. |
| D2 | Vendorizar `okf-bundle-core` | Copiar código e licença com origem/revisão identificáveis; instalar as dependências reais do core e validar suporte a plataformas. |
| D3 | Embutir SPA usando o build Hatch | Incluir fonte versionada ou artefato prebuilt reproduzível no **sdist e wheel**; build sem fonte nem dist falha, não devolve wheel incompleto. |
| D4 | `kg.mode="native"` por padrão | `native`: tools nativas e exclusão **apenas** de CM/AK legados da configuração MCP; `mcp`: só os legados; `both`: ambos, com nomes distintos e aviso sobre escrita concorrente. Outros MCPs permanecem ativos. |
| D5 | Congelar os servidores MCP após migração | Manter versão legada recuperável; banner/EOL e tags somente após validação, com aprovação para publicação/tag/push. |
| D6 | `cm_memory_enrich` com PydanticAI próprio, MiniMax M3 default | Portar o contrato de `CM/enricher.py` (proposta tipada, CAS, retries, erro estruturado); ativar a tool sem exigir chave na inicialização. |
| D7 | `kg.cm_enrich_timeout_s=45` | Orçamento para a chamada ao modelo, incluindo tentativas; validar também o tempo total do handler. |
| D8 | `GraphView` React + D3 | Usar endpoint **novo** de dados do grafo; `/memory/graph` e `/acquire/graph` atuais retornam metadados `{exists,path,size_bytes}`, não nodes/edges. |
| D9 | Dev com gateway + Vite | Reescrever script **no repositório onde for encontrado ou criá-lo em `spa/scripts/`**; o clone `~/Projects/mcp-servers-percival/` não existe neste ambiente. |
| D10 | `AGENTS.md` dos 3 repos congelados → `MIGRATION.md` | Agendar renomeação nos repos de origem depois da paridade e preservar instruções úteis; `spa/AGENTS.md` continua guia de desenvolvimento. |

**Correções estruturais importantes:** o código atual tem **10 fases F0–F9**, não 9; `pyproject.toml` e `hatch_build.py` ficam na **raiz** do repo; o projeto instalado se chama `nanobot-ai` hoje (`percival-ai` depende de trabalho de publicação/branding separado). `tools.mcpServers` é o campo atual; não existe `mcpServers` na raiz. O gateway usa `websockets.process_request`, **não** FastAPI/ASGI, e não recebe corpos HTTP nesse caminho; mutações WebUI usam WebSocket autenticado. Não assumir cookie, `FastAPI.TestClient`, `StaticFiles` nem `app.include_router` como interfaces existentes.

### Inventário e paridade de contratos

- CM: `percival-collective-memory/src/percival_collective_memory/server.py` expõe **20 tools operacionais + 6 prompts**. Não expõe `notes_delete` nem `graph_build` como tools MCP: arquivar é `memory_forget`; rebuild é CLI/core. `tools.py` contém a lógica, mas **não é somente core** (policy, GitStore, proteção, enrich, stats).
- AK: `percival-acquire-knowledge/src/percival_acquire_knowledge/server.py` expõe **14 tools operacionais + 6 prompts**. `source_dump` existe em `tools.py` para diagnóstico, não como tool MCP.
- Portanto o alvo mínimo de paridade nativa é **34 tools operacionais (20 CM + 14 AK)**, mais **12 prompt primitives** convertidos em orientação descoberta pelo agente. Ferramentas novas fora dessa contagem exigem decisão e teste próprios.
- A SPA usa funções em `spa/src/lib/api.ts` e contratos Zod em `spa/src/lib/types.ts`; CM e AK possuem **17 e 10 rotas HTTP**, respectivamente (`http_server.py`). Não inferir cobertura por um número fixo de "16 endpoints": inventariar método, URL, request/response e erros para cada chamada efetivamente usada, inclusive rotas adaptadas por bundle, e acrescentar `/graph/data` para os dois bundles.

## 2. Limites de arquitetura e riscos impeditivos

1. **Ownership:** core vendorizado é Python determinístico; CM/AK ports moram em `nanobot/agent/kg/cm/` e `ak/`; registro na `ToolRegistry`, execução/política no gateway. O cliente não grava diretamente nos bundles.
2. **Ferramentas por contexto:** `AgentLoop._register_default_tools()` carrega `nanobot.agent.tools` com `ToolLoader` **não recursivo**; `nanobot.agent.kg` não é descoberto automaticamente. Uma factory explícita deve registrar tools nativas na registry compartilhada em `nanobot/nanobot.py`, `nanobot/cli/agent.py`, `nanobot/cli/commands.py`, `nanobot/cli/gateway_runtime.py`, e decidir o escopo de subagentes (`nanobot/agent/subagent.py`). Conferir reload de config e registros duplicados. Construção ocorre com o workspace efetivo, após overrides; usar `current_request_context()` para workspace por requisição quando aplicável, nunca cachear o workspace global de uma sessão em outra.
3. **Escopo de filesystem:** `okf_bundle_core.paths.resolve_safe_path` garante contenção no **bundle**, não no workspace do agente. Aplicar a política `restrict_to_workspace` de `nanobot/security/workspace_policy.py`/`agent/tools/path_utils.py` e distinguir leitura/escrita; roots explícitos externos só com autorização configurada. `ak_source_ingest` aceita path absoluto no legado, mas o port não pode contornar a política do Percival; `cm_asset_get_path` não deve expor path local para quem não tem leitura. Validar symlinks, `..`, roots opcionais e TOCTOU após resolução.
4. **Rede:** enrich/vision/transcribe usam SDKs externos. Respeitar o limite de SSRF em `nanobot/security/network.py`; configurar apenas endpoints de provider autorizados, sem aceitar URL arbitrária de argumento da tool; documentar o tratamento de `kg.cm_enrich_base_url` e proxies. Não bloquear o event loop com Git, ripgrep, markitdown ou filesystem intensivo: usar `asyncio.to_thread` onde a implementação for síncrona, com limites e timeout do subprocess.
5. **Cross-bundle:** selecionar layout/root **antes** de resolver ids ou paths. Operações de link sempre restringem as duas extremidades ao mesmo bundle, preservando forward references válidas da implementação legada; não exigir que `to_id` já exista se o contrato permitir dangling link. Idênticos IDs de CM/AK não são prova de pertença. Testar referência cruzada e permissões também nas rotas da SPA.
6. **HTTP/SPA é a dependência crítica:** `nanobot/webui/gateway_endpoint.py` despacha HTTP pelo `GatewayHTTPHandler` (`nanobot/webui/ws_http.py`), e mutações pelo `WebUICommandRouter`/`dispatch_webui_mutation` com conexão WS autenticada. A SPA hoje usa `fetch` + `credentials: "same-origin"`; isso **não** autentica no gateway (usa token bearer emitido por `/webui/bootstrap`, não cookie). Estratégia recomendada: GETs KG no mesmo listener com bearer verificado via `GatewayHTTPHandler.check_api_token` e mutações KG por ações `webui_request` allowlisted em WS autenticado; atualizar o cliente SPA para esta ponte, preservar semântica `409` CAS e payloads Zod. Testar a obtenção de bootstrap/token e a conexão WS da SPA real; se ela não for viável sem ampliar o protocolo, parar F0 e replanejar transporte antes de F6. Nunca abrir rota de escrita via GET nem retirar autenticação para fazer a UI funcionar.
7. **Portabilidade:** `okf_bundle_core/lock.py` importa `fcntl` (Linux); upstream nanobot publica em macOS/Windows. Definir implementação de lock equivalente ou restringir claramente o suporte do KG por plataforma, com gate de build/import no CI antes de anunciar `pip install` universal. Verificar compatibilidade de NetworkX, markdown-it-py e licença do core (`okf-bundle-core/LICENSE`).

### F0: provas curtas antes de portar funcionalidades

- Exercitar no listener atual, com teste in-process, uma rota GET autenticada sob `/kg-interface/api/memory/healthz` e uma ação WS de mutação que devolva status/payload ao SPA; chamadas anônimas devem falhar. Fazer um pequeno cliente SPA obter token/WS e repetir o fluxo; anotar contrato em `tests/kg/` + testes SPA.
- Exercitar build **isolado** wheel e sdist com SPA prebuilt (sem clone `spa/` disponível), instalar em ambiente limpo, localizar `nanobot/web/kg-interface/index.html` e servir um asset; verificar build com fonte quando incorporada. Sem esses dois gates, não declarar D3 alcançada.
- Medir/registrar a situação Windows/macOS (lock) e definir se há implementação equivalente ou uma limitação de distribuição. **Não** presumir que os 12 dias úteis/6.500 LOC da versão anterior ainda se aplicam; revisar estimativa após estas provas e o inventário de endpoints.

## 3. Estrutura proposta e configuração

```text
nanobot/agent/kg/
  __init__.py, _bundle.py, _errors.py, _registry.py
  vendor/__init__.py, vendor/okf_bundle_core/{__init__,...}.py
  cm/{core,links,policy,storage,stats,graph,enrich,enricher,forget}.py
  ak/{ingest,read,write,graph,multimodal,forget,_markitdown,_cache}.py
nanobot/config/kg.py                        # modelo Pydantic único
nanobot/webui/kg_http.py                    # leitura KG e estáticos na infra HTTP existente
nanobot/webui/kg_actions.py                 # mutações KG via WebUI WS autenticado
nanobot/cli/kg.py
nanobot/web/kg-interface/                  # dist embalado
nanobot/skills/kg/{SKILL.md,...}
tests/kg/                                  # testes no testpath existente
```

**Não** criar `nanobot/agent/kg/config.py` duplicado, FastAPI `nanobot/channels/websocket/kg_router.py` ou `kg_static.py` como ASGI, nem adicionar FastAPI/Uvicorn só para a SPA. Integrar estáticos no dispatch HTTP antes do fallback que hoje devolve `index.html` da WebUI para paths desconhecidos. Arquivos específicos de organização podem mudar se o seam de F0 revelar solução menor; não editar `agent/loop.py`/`runner.py` sem justificativa explícita.

**Modelo em `nanobot/config/kg.py`:** subclasse de `nanobot.config_base.Base` (aceita camelCase/snake_case), referenciada em `nanobot/config/schema.py` por `kg: PercivalKgConfig = Field(default_factory=PercivalKgConfig)`. `mode: Literal["native","mcp","both"]="native"`; `cm_root`/`ak_root`: path para **diretório pai**, `None` significa workspace ativo; `cm_enrich_enabled=True`, `cm_enrich_timeout_s=45` com validação positiva, `cm_enrich_model="MiniMax-M3"`, `cm_enrich_base_url: str|None=None`, `ak_image_caption_enabled=True`, `ak_audio_transcribe_enabled=True`. Sem `mcp_compat` redundante: modo define comportamento; sem `spa_path` arbitrário por default (override de desenvolvimento, se necessário, restrito e documentado). Opcionais de timeout de ingest só após validar necessidade em F4; não referir campos inexistentes no gate.

Config existente: `Config.tools.mcp_servers` (alias JSON `tools.mcpServers`). Filtrar servidores CM/AK **por identificador configurado e assinatura verificada** no ponto de composição e no reload (`agent/tools/mcp.py` e `agent/plugins.py`); não mexer em outros MCPs ou MCPs de sessão/preset por engano. Em `both`, testar namespace para colisões e documentação de concorrência; em `mcp`, ausência de CM/AK MCP configurado deve produzir diagnóstico explícito. O registro de tools não pode depender do bundle existir: tool ausente só por config desabilitada; bundle ausente gera erro útil na execução/doctor.

**Roots:** env legado `COLLECTIVE_MEMORY_ROOT`/`ACQUIRED_KNOWLEDGE_ROOT` (apontam ao pai), depois `kg.cm_root`/`kg.ak_root`, depois workspace efetivo (ou `NANOBOT_WORKSPACE` no CLI sem contexto). Preservar override explícito para quem migra; sinalizar divergências env/config. Não usar busca implícita por CWD/ancestrais no gateway multi-workspace; CLI pode aceitá-la explicitamente para compat. `resolve_bundle_arg` do core aceita pai ou bundle, mas persistir no config a convenção do pai e sempre passar o **bundle** para as funções core. `kg doctor`/`kg bundle init` diferenciam root ausente de root vazio; criação inicial prepara layout e GitStore com confirmação do destino, não só `mkdir`.

**Dependências:** `pyproject.toml` atual já tem `pydantic`, `pyyaml`, `dulwich`, `httpx`, `openai`, `typer`. Core requer ainda `markdown-it-py`, `networkx`. CM enrich e AK vision requerem `pydantic-ai>=2,<3`; AK pode requerer `diskcache`, `pydub`, `groq` (avaliar extras ou imports lazy, não exigir chaves nem ffmpeg no startup); `markitdown` continua **CLI externo** para ingest de documentos. `fastapi`/`uvicorn` não são necessários na estratégia recomendada. Declarar **somente** deps importadas em paths instaláveis e validar build/instalação limpa. Incluir licença/atribuição do vendor explicitamente no wheel/sdist, além de `nanobot/web/kg-interface/**/*` em `include` e `artifacts` do Hatch e `nanobot/web/kg-interface/` no sdist; hook em `hatch_build.py` (na raiz) com skip/force próprios e erro se faltarem fonte e prebuilt. Embutir snapshot pinado do SPA ou fonte sob `spa/` incorporada ao sdist, com origem, licença e atualização reprodutível: o Hatch não lê automaticamente `~/Projects/spa/` num build isolado. Editable instala sem build de frontend por design; smoke de wheel/sdist, não `pip install -e .`, valida D3.

## 4. Fases e gates (F0–F9: dez fases)

Todos os gates de código Python incluem `pytest` (configuração de cobertura e testpaths de `pyproject.toml`), `basedpyright nanobot`, `ruff check .` quando tocar integração ampla; o gate local acelera feedback mas não substitui o global no encerramento de cada fase. SPA: `bun run test`, `bun run lint`, `bun run build` em `~/Projects/spa/`. Testes com rede/chaves são **smokes opcionais supervisionados**, não substituem fixtures determinísticas. Não executar `ruff format`.

| Fase | Depende de | Resultado que libera a próxima |
| --- | --- | --- |
| F0 | — | Transporte e build viáveis; vendor, config e proteção de roots definidos. |
| F1 | F0 | CM leitura/escrita/CAS (4 tools). |
| F2 | F1 | Política, links, stats e manutenção CM (mais 15). |
| F3 | F2 | Enrich CM e total de 20 tools. |
| F4 | F0 | AK ingest/leitura/multimodal (8); pode avançar em paralelo a F1–F3. |
| F5 | F4 | AK escrita/link/graph/forget (mais 6; total 14). |
| F6 | F2, F5, F0 transporte | Leitura e mutações necessárias à SPA, incluindo GraphData autenticado. |
| F7 | F6 | SPA distribuível e grafo D3, sem adapters externos. |
| F8 | F2, F5 | CLI KG com doctor/bootstrap/rebuild verificáveis. |
| F9 | F3, F7, F8 | Skills, documentação, compatibilidade de upgrade/rollback e EOL aprovado. |

**Recursos e prazo:** implementar em um fork e no repo SPA; mudanças nos três repos legados são um pacote de trabalho de F9. A estimativa antiga de 12 dias úteis é **não validada** (transporte e distribuição não foram prototipados). Após F0, medir esforço restante e registrar responsável/prazo para cada trilha CM, AK, gateway e frontend antes de anunciar release.

### F0 — Fundação e viabilidade do transporte/empacotamento

1. Registrar SHA/origem do core e SPA, copiar `okf_bundle_core` + `LICENSE`; reescrever imports absolutos para `nanobot.agent.kg.vendor.okf_bundle_core`, preservar relativos, comparar resultados em fixtures do core. Migrar testes **relevantes** do core sem copiar dados de usuário. Instalar deps e confirmar `import nanobot.agent.kg.vendor.okf_bundle_core` em ambiente limpo; corrigir/decidir `fcntl` sem quebrar import em plataformas publicadas.
2. Criar `config/kg.py`, resolução de roots por workspace/escopo, política de paths e tradução de exceções (`errors.py` define classes em `paths.py`, `lock.py`, `zettel.py`, não presumir todas em `errors.py`). Criar registry factory **sem tools stubs**; provar que os quatro composition roots e subagentes previstos não geram import circular/duplicação. Planejar filtro MCP também no reload.
3. Executar provas da §2 para gateway/auth/body/cliente SPA e build wheel/sdist. Documentar contrato GET bearer + WS mutation e o inventário SPA com verb/path/schema; se incompatível, replanejar antes de F1. O frontend com source ausente deve ter dist incluído ou build falhar claramente.

**Saída:** testes `tests/kg/test_bundle.py`, `test_config.py`, `test_transport.py`, build/import e smoke de login/WS/estáticos; `pytest`, `basedpyright nanobot`, `ruff check .` passam. Config `native|mcp|both` testada com terceiro MCP inalterado. Estimativa refeita; não confundir teste de ferramenta inexistente com gate (`nanobot kg` vem na F8).

### F1 — CM read/write/search/history (4 tools)

Portar `tool_notes_read`, `tool_notes_write`, `tool_notes_search`, `tool_history` de `percival_collective_memory/tools.py` como `cm_notes_read`, `cm_notes_write`, `cm_notes_search`, `cm_note_history`; serializar respostas Pydantic sem expor `frontmatter_typed` à UI. Reaproveitar CAS de conteúdo/body e semântica de GitStore; testes para criação, conflitos, search sem `rg`, rollback, limits e workspace divergente. `memory_forget` pertence a F2; não inventar `notes_delete` idempotente. `@tool_parameters` + `Tool.create(ctx)`/registry conforme `nanobot/agent/tools/base.py`, chamadas síncronas fora do event loop. **Gate:** `pytest tests/kg/test_cm_core.py`, suite Python, typecheck e lint; smoke de criação num bundle temporário e registro via SDK/CLI/gateway (sem LLM externo obrigatório).

**Execução local (2026-10-05):** implementadas em `nanobot/agent/tools/cm_notes.py` e `nanobot/agent/kg/cm/core.py`; config KG chega ao `ToolContext` pelo `AgentLoop.from_config`. Criação/escrita reaproveita CAS/rollback/GitStore do vendor; read/search/history não inicializam Git. Busca case-insensitive implementada sobre `notes/*.md`, sem `rg`, com limite 1–200, query até 500 chars e resultados/snippets limitados. Respostas JSON não incluem `frontmatter_typed`. `asyncio.to_thread` executa I/O síncrono. Root por chamada respeita workspace ativo; com `restrict_to_workspace`, roots externos são negados (ainda não há grants externos configuráveis nas tools F1). Bundle e notas verificam contenção de symlinks antes de abrir conteúdo. ToolLoader e `AgentLoop.from_config` registram as quatro em modo `native`; em modo `mcp` não as registram. `tests/kg/test_cm_core.py`: **8 passed**, incluindo CAS stale, rollback por falha de commit, search sem subprocesso, histórico, isolamento workspace, negação de symlink e composição sem LLM. Gate global final: **9126 passed, 47 skipped, 1 warning** (344.88 s); `basedpyright nanobot` e `ruff check .` passaram. F0 ainda tem pendências de plataforma, snapshot limpo e registry/filtro de substituição; por isso F1 não fecha a autorização de release nem libera F2 automaticamente.

### F2 — CM links, policy, stats, storage, graph, forget (15 tools)

Portar `memory_link`, `memory_batch_link`, `memory_attach`, `memory_forget`, `memory_stats`, `asset_get_path`, `graph_neighbors`, `graph_shortest_path`, as quatro operações P11 (`set_protected`, `set_lifecycle`, `flag_for_review`, `resolve_review`) e três operações de storage (`storage_stats`, `repo_maintenance`, `aging_candidates`). F1+F2 = **19 CM operacionais**; F3 fecha a vigésima. `graph_build` continua operação de core/CLI, não tool histórica. Portar proteções, efeitos de locks, idempotência/partial success e parâmetros do `server.py`/`tools.py`, não apenas nomes. `repo_maintenance` deve respeitar permissão de escrita e dry-run; `asset_get_path` segue política de leitura. **Gate:** tests de comportamento (forward ref, links cross-bundle, CAS P11, proteção, gc dry-run, graph ausente, `rg` ausente), `pytest`, typecheck e lint; smoke de stats + lifecycle em bundle fixture.

### F3 — CM enrich e guidance (1 tool)

Portar `memory_enrich` e `enricher.py`: validar `note_id`/`fields`, proposta Pydantic tipada, campos protegidos, CAS body_hash, retry de transporte vs validação separados, `MINIMAX_API_KEY` só na execução, timeout 45s e erro estruturado. `OpenAIProvider(base_url=...)` não implica autenticação nem retries seguros: seguir o `AsyncOpenAI(timeout,max_retries)` já usado no CM, sem colar exemplo simplificado inválido. Reaproveitar os seis prompts do CM como **arquivos de skill**, não duplicá-los em `prompts.py` descartável; a descoberta é validada em F9. **Gate:** fakes do modelo para timeout/CAS/sem chave/resposta inválida + suites globais; smoke real opcional com chave, sem salvar segredo. Total CM registrado: **20**.

### F4 — AK ingest/read/multimodal (8 tools)

Portar `source_ingest`, `source_read`, `source_list`, `source_search`, `source_stats`, `get_laterally_isolated_notes`, `image_caption`, `audio_transcribe` do AK. Separar parser/vision/transcribe/cache em módulos sem transportar FastMCP; `markitdown` é CLI subprocess com timeout e sanitização, `ffmpeg` exigido somente onde usado. Ingest deve respeitar `restrict_to_workspace` e preservar dedupe por SHA, cópia atômica, telemetria/estado do bundle. Chave ausente mantém o comportamento stub **apenas se explicitamente fiel/visível no resultado**; diferenciar de sucesso real. **Gate:** PDF/DOCX com CLI disponível em teste de integração específico, fixtures sem rede para multimodal/cache (stub vs real isolados), path traversal/symlink/limite de arquivo, suite Python, typecheck e lint. Não testar `ak_source_forget` antes da F5.

### F5 — AK write/link/graph/forget (6 tools)

Portar `note_write_extracted`, `note_link`, `note_batch_link`, `graph_neighbors`, `graph_shortest_path`, `source_forget`; validar CAS/atualização atômica de `chunks_atomized`, respostas por edge, paridade com ordem de relações D65, path do archive, limites e forward refs. `source_dump` fica fora da lista de tools; considerar no CLI doctor. Seis prompts AK tornam-se workflows de skill em F9. **Gate:** tests de reingest + retomada parcial, batch não transacional, graph e isolamento CM/AK, suite Python, typecheck e lint. Total AK registrado: **14**; total KG **34** (em native, ambas as funções opcionais ligadas).

### F6 — Bridge do gateway e contrato SPA

Implementar leitura em `GatewayHTTPHandler` (ou helper composto) antes do fallback estático; autenticação por bearer existente, rota `/kg-interface/api/{memory|acquire}/...` com GETs necessários e `GET /kg-interface/api/{memory|acquire}/graph/data` novo. Mutação usa `WebUICommandRouter` + allowlist de `webui_request`, payload JSON tipado, tamanho limitado, verificação de autenticação do WS, escopo de workspace/bundle e resposta com status/código coerentes (`400/401/403/404/409/503/504`). Adaptar `spa/src/lib/api.ts`, `KgClientProvider.tsx` e bootstrap WS para transportar mutações sem expor token em URL/logs/localStorage; preservar `credentials` quando aplicável, mas incluir `Authorization` bearer em GET. O protocolo precisa contemplar reconexão/expiração, cancelamento/timeouts e equivalência ao Zod da SPA. Não converter `ToolResult` textual diretamente em HTTP/WS JSON: usar serviços tipados do KG compartilhados pelas Tools e bridge, sem registros da Tool como interface de transporte.

**Gate:** teste de cada função efetivamente chamada em `spa/src/lib/api.ts` com fixtures compatíveis com `src/lib/types.ts`, matriz CM/AK, bearer ausente → 401, WS não autenticado → rejeição, CAS → 409, erro de root → 404, graph metadata mantido e graph/data novo. Testes com listener `websockets` in-process (padrão de `nanobot/channels/websocket/tests/`), não `FastAPI.TestClient`; `pytest`, typecheck, lint e `bun run test` SPA. Verificar que `/kg-interface/api/*` nunca recebe `index.html` em vez de JSON/404.

### F7 — SPA empacotada e GraphView D3

Integrar snapshot/build da SPA no sdist/wheel via `hatch_build.py` e `pyproject.toml`; servir `/kg-interface/` e assets no dispatch do gateway com contenção de path, MIME, cache e fallback **somente** para rotas da SPA (nunca `/api/`). Em `~/Projects/spa/vite.config.ts`, trocar proxy de :8001/:8002 por gateway :8765 e remover plugin dev de `graph.html` depois da migração; preservar `base: "/kg-interface/"`, porta Vite 5174 e rewrite de assets. GraphView preserva seleção CM/AK, stats e rotas `#/notes/:id`, `#/extracted-notes/:id` (não `#/note/{id}`), cancela fetch obsoleto, limita grafo ou reduz carga de render; `GraphDataSchema` novo para NetworkX node-link com `links`. Adicionar `d3-force`/tipos (e zoom somente se implementado). Remover dependência runtime do iframe/export HTML **após** comparação visual e teste de grafo vazio/corrompido.

**Gate:** `bun run test && bun run lint && bun run build` no SPA; build wheel e sdist em checkout limpo sem repo irmão, instalar os dois e abrir WebUI + SPA + grafo sob mesmo origin; conferir URL de assets, rota hash em refresh, 404 real em asset inexistente, auth, browser smoke e resultados coerentes para CM/AK. `pip install -e .` não executa hook de frontend e não serve como teste de distribuição.

### F8 — CLI `nanobot kg`

Registrar subapp Typer único em `nanobot/cli/commands.py`/`nanobot/cli/kg.py`; escolher assinaturas explícitas: `nanobot kg doctor --json`, `nanobot kg bundle path cm`, `nanobot kg bundle init cm`, `nanobot kg graph rebuild cm`, `nanobot kg p11 bootstrap --dry-run [--json]` / `--apply`. Reutilizar funções core/CM/AK em vez de executar CLIs legadas via subprocess; incluir `ak-migrate-lateral-links` como comando de migração one-shot ou documentar caminho de migração antes do EOL. Testar opção `--bundle-root` pai/bundle, defaults de workspace, dry-run real, criação sem sobrescrever, outputs JSON e exit codes com `typer.testing.CliRunner`. **Gate:** `pytest tests/kg/test_cli_kg.py`, suite, typecheck, lint e smoke dos comandos; não remover entry points dos pacotes congelados, pois rollback precisa deles.

### F9 — Skills, documentação, migração e release

Portar **seis** prompts CM e **seis** AK para arquivos Markdown descobertos por `nanobot/agent/skills.py`/SkillsLoader (validar layout real, não presumir descoberta recursiva). Atualizar as referências de `cm-graph-rebuild`/`ak-graph-rebuild` para `nanobot kg graph rebuild`; manter proteção P11 e decisões sobre link. Documentar config, UX de auth, dados e backup, dependências opcionais, plataformas, workflow de update do vendor e do snapshot SPA. Criar ADR em `docs/Decisions/`, atualizar `RUNBOOK-sync-upstream.md` e notas de release. Nos três repos legados, só após estabilização: banner e `MIGRATION.md` preservando instruções úteis de `AGENTS.md`; nunca deletar binários/entry points necessários para rollback. Reescrever/criar `spa/scripts/dev-spa.sh` para gateway + Vite, com cleanup; atualizar `spa/AGENTS.md` e scripts que ainda usem adapters :8001/:8002. Tag/push/publicação/arquivamento precisam de aprovação explícita.

**Gate:** 12 orientações acessíveis por skill descoberta, teste de comandos citados nas skills, testes e build SPA, `pytest`, `basedpyright nanobot`, `ruff check .`, wheel/sdist smoke, migração e rollback testados com dados cópia (não em bundles reais), links relativos resolvidos. Somente então marcar D5/D10 como entregues.

## 5. Migration cookbook e rollback

1. **Novo workspace:** instalar o fork conforme o nome de distribuição **efetivamente publicado** (`nanobot-ai` hoje; `percival-ai` só depois do rename/release), configurar provider, rodar `nanobot kg bundle init cm` e `... ak` no workspace selecionado, `nanobot kg doctor`, subir `nanobot gateway`. Tools locais não exigem chave de LLM; enrich/vision/transcribe requerem as credenciais/configurações apropriadas na hora do uso.
2. **Deploy com MCP:** fazer backup verificável de config e bundles completos (incluindo `.git`, `sources`, `assets` e graph artifacts); registrar versão do core legado e testar fixture de compatibilidade on-disk antes de liberar escrita nativa. Config legada está em `tools.mcpServers`, incluindo possíveis referências de presets/sessões; modo `native` suprime **só** CM/AK legados, mostra aviso e mantém os outros. Resolver roots para os bundles existentes; testar leitura, CAS, listagem, navegação, enriquecimento opcional e link. Só então parar adapters CM/AK (reversível) e editar config.
3. **Rollback:** configurar `kg.mode="mcp"` com servidores legados ainda instalados/configurados em `tools.mcpServers`; desativar gateway nativo ou reiniciar antes de habilitar escrita MCP, evitar writers simultâneos. Testar leitura em cópia do bundle criado pelo core vendorizado; se houve mudança de schema/artefatos incompatível, restaurar snapshot em vez de prometer "nenhuma migração necessária". Separar rollback de binário/config de restauração de dados, e registrar efeitos de writes feitos durante a janela nativa.
4. **EOL:** após ao menos uma release estável com testes de upgrade/rollback, preparar banner/MIGRATION e tag local. Fazer push/tag remoto e mudar status de repos somente com autorização do operador; não pressupor que `~/Projects/mcp-servers-percival/` exista.

## 6. Critérios de aceite globais e evidências

| Critério | Evidência mínima |
| --- | --- |
| F0–F9 concluídas | Gates de cada fase com resultados registrados; **não** contar commits por mensagem. |
| Paridade operacional | Inventário 20 CM + 14 AK comparado com `server.py`; registry no SDK, CLI, gateway e decisão documentada para subagentes; parâmetros e resultados verificados. |
| Integração HTTP/SPA | Mesma origem/porta, GET com bearer e mutações autenticadas por WS, cobertura das chamadas `spa/src/lib/api.ts`, códigos de erro e contratos Zod; CM e AK realmente acessíveis. |
| Empacotamento | `pip wheel`/sdist + instalação limpa incluem vendor/licença, dependências, skills, SPA/asset e passam sem checkout do SPA vizinho; plataforma suportada explicitamente. |
| Dados preservados | Teste de upgrade/rollback em cópia de bundles reais com CAS, git, arquivos binários e permissão; sem cross-bundle ou escape de workspace. |
| Qualidade | `pytest`, `basedpyright nanobot`, `ruff check .` no Percival; `bun run test`, `bun run lint`, `bun run build` na SPA; testes de transporte sem chaves/serviços externos. |
| Operação e docs | CLI doctor e graph rebuild passam, skills CM/AK descobertas, ADR e guia de migração apontam ao caminho atual deste plano; repos congelados apenas após autorização e validação. |

**Fontes conferidas nesta revisão:** `pyproject.toml`, `hatch_build.py`, `nanobot/agent/tools/{base,loader,registry,context,mcp}.py`, `nanobot/agent/loop.py`, `nanobot/webui/{gateway_endpoint,ws_http,inbound_commands}.py`, `nanobot/config/{schema,paths}.py`, `okf-bundle-core/{pyproject.toml,src/okf_bundle_core/{paths,graph,lock}.py}`, `percival-{collective-memory,acquire-knowledge}/src/*/{server,tools,http_server,paths}.py`, `spa/{package.json,vite.config.ts,src/lib/{api,types,hash-route}.ts,src/components/kg/GraphView.tsx}`. Pendem execução de provas F0, inventário método-a-método e medição da estimativa; nenhuma fase de código foi implementada por esta revisão.
