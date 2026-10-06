# KG endpoint inventory — gateway bridge × SPA

**Date:** 2026-10-06 · **Project:** Percival · **Scope:** Every route the SPA
can reach via the gateway, paired with the typed Zod schema it expects and the
backend service that fulfils it. Read this before changing CM/AK HTTP
contracts, the SPA `api.ts`, or the `KgGatewayBridge`.

Source of truth:

- HTTP: `nanobot/webui/kg_http.py::KgGatewayBridge.read`
- WS mutations: `nanobot/webui/kg_http.py::KgGatewayBridge.mutate`
- Static fallback policy: `nanobot/webui/kg_static.py`
- SPA minified client: `nanobot/web/kg-interface/assets/index-BzJKk184.js`
  (built from `~/Projects/spa`; the rebuilt snapshot lives there).
- SPA Zod contracts: `nanobot/web/kg-interface/assets/index-*.js` (compiled
  from `spa/src/lib/types.ts`).

## 1. Prefix and conventions

| Aspect | Value |
| --- | --- |
| HTTP base | `/kg-interface/api/` |
| Static shell | `/kg-interface/` (HTML/CSS/JS) and `/kg-interface/brand/*` |
| Bundle selector in URL | First segment: `memory` (CM) or `acquire` (AK) |
| Auth | GET requires `Authorization: Bearer` issued by `/webui/bootstrap`. WS mutations require an issued WebUI-audience token. Bearer-in-URL is rejected. |
| ID validation | Note/Source ID must match `\d{8}-\d{6}\Z` (full match, not prefix) |
| Result type | JSON; `no-store` cache for reads and mutations |
| ID semantics | The SPA never selects a project/session; the gateway uses its WebUI default scope. |
| `Path-Control` | `/kg-interface/api` and `/kg-interface/api/*` never fall back to `index.html`. Unknown API routes return JSON 404. |

## 2. GET routes

| Adapter | Route | Query | Backend | SPA call sites | Errors |
|---|---|---|---|---|---|
| both | `/healthz` | — | static `{"ok": True, "server": "percival-native-…"}` | `api.healthz()` | 503 when bundle missing |
| both | `/notes` | `q?`, `limit?` (1–200) | CM: `cm_core.notes_search` or `notes_list`; AK: `ak_read.source_search` (no `q`) or `source_list(kind=ExtractedNote)` | `api.listNotes()` | 400 on invalid `limit`, 403 on workspace escape |
| both | `/notes/{id}` | — | CM: `cm_core.notes_read`; AK: `ak_core.read_note` | `api.getNote()` | 400 invalid id, 403 symlink escape, 404 missing |
| memory | `/notes/{id}/history` | `limit?` (1–1000, default 20) | `cm_core.note_history` | `api.noteHistory()` | AK returns 404 |
| both | `/search` | `q` (required), `kind?`, `limit?` | CM: `cm_core.notes_search(kind=…)`; AK: `ak_read.source_search(kind=…)` | `api.search()` | 400 missing/invalid query |
| both | `/stats` | — | CM: `cm_f2.memory_stats`; AK: `ak_read.source_stats` | `api.stats()` | 403 workspace escape |
| memory | `/storage/stats` | — | `cm_f2.storage_stats` | `api.storageStats()` | AK returns 404 |
| both | `/graph` | — | `agent.kg.graph_data.graph_artifact()` | `api.graphMetadata()` | 404 when graph absent or corrupt |
| both | `/graph/data` | — | `graph_artifact(data=True)` (bounded 8 MiB) | `api.graphData()` (Zod `GraphDataSchema`) | 413 when > 8 MiB; 404 when artifact missing |
| acquire | `/sources` | `limit?` | `ak_read.source_list(kind=Source)` | `api.listSources()` | CM returns 404 |
| acquire | `/sources/{id}` | — | frontmatter from `ak_core.read_note` + first chunk | `api.getSource()` | 400 invalid id, 403 symlink escape, 404 missing |
| acquire | `/sources/{id}/chunks/{n}` | — | `ak_ingest.source_read(chunk_index=n)` | `api.getSourceChunk()` | 400 invalid index, 404 missing |

## 3. WS mutations (`kg.<adapter>.<operation>`)

The WS path is `kg.<memory|acquire>.<operation>` submitted as an allowlisted
`webui_request` action. The bridge rejects anything else with
`kg_action_not_found` (404). Maximum payload: 2 MiB + 4 KiB envelope.

| Action | Adapter | Body | Backend | Notes |
|---|---|---|---|---|
| `kg.memory.notes.body` | memory | `BodyEdit` (`body`, `base_body_hash`, `reason`) | `cm_core.notes_write` | CAS conflict → 409 + `{base_body_hash, current_body_hash, server_body}` |
| `kg.acquire.notes.body` | acquire | `BodyEdit` | `ak_core.write_note_body` | CAS conflict handled symmetrically |
| `kg.memory.notes.forget` | memory | `Forget` (`reason`) | `cm_f2.memory_forget` | Archive, not delete; Git rollback on failure |
| `kg.memory.notes.protected` | memory | `Protected` (`protected`, `reason`, `expected_content_hash?`) | `cm_f2.memory_set_protected` | P11 CAS preserved |
| `kg.memory.notes.lifecycle` | memory | `Lifecycle` (`lifecycle`, `reason`, `expected_content_hash?`, `force?`) | `cm_f2.memory_set_lifecycle` | |
| `kg.memory.notes.flag` | memory | `Flag` (`kind`, `confidence`, `reason`, `related_actions?`, `flagged_by?`) | `cm_f2.memory_flag_for_review` | |
| `kg.memory.notes.resolve` | memory | `Resolve` (`kind`, `resolution`, `reason`) | `cm_f2.memory_resolve_review` | `resolution` enum: `acknowledge` / `resolve_keep` / `resolve_cold` / `resolve_forget` / `reopen` |
| `kg.memory.storage.maintenance` | memory | `Maintenance` (`dry_run=true`, `reason`) | `cm_f2.memory_repo_maintenance` | Default dry-run; real GC requires write authorization |

## 4. Status / error code matrix

| Status | When |
|---|---|
| 200 | Successful read or mutation |
| 400 | Invalid id, payload, or query; `kg_unavailable` not from a missing bundle |
| 401 | Anonymous GET / WS, no bearer |
| 403 | Workspace escape, symlink redirect, restricted workspace forbids external root |
| 404 | Unknown route, missing note/source/graph, AK-only route hit on CM |
| 409 | Body CAS mismatch (with conflict payload for SPA merge UI) |
| 413 | Graph payload > 8 MiB; mutation payload > 2 MiB |
| 503 | Bundle missing/uninitialized, lock timeout, kg_unavailable |

## 5. Static / brand assets

| Path | Notes |
|---|---|
| `/kg-interface/` | SPA shell, served only on HTML-accepting client; unknown paths under `/kg-interface/{notes,extracted,extracted-notes,sources,graph,search,stats}` fall back to `index.html` |
| `/kg-interface/assets/index-*.js` | Hashed bundle; long-lived cache |
| `/kg-interface/assets/index-*.css` | Hashed bundle; long-lived cache |
| `/kg-interface/brand/percival_*.png` | Branding icons |
| `/kg-interface/kg-interface_logo.svg` | Legacy icon (no longer referenced by HTML) |
| `/kg-interface/SOURCE.json` | Provenance manifest; **not served** by `kg_static.py` (intentional) |
| `/kg-interface/LICENSE` | License file for the bundled SPA |

## 6. Open inventory gaps

These are routes or behaviours that the SPA schema implies but that are not
yet exercised or have a known limitation:

1. AK `noteHistory`/`forgetNote` — TS adapter accepts `adapter="acquire"` but
   AK does not expose history. `ExtractedNoteView` avoids calling them.
2. No native `/notes/search` route name; SPA uses `/search` with adapter
   prefix. Cross-checked: `api.ts` calls `/memory/search` and `/acquire/search`.
3. GraphView relies entirely on `/graph/data`; metadata route is kept for
   capability probes and the home view's "Last build" widget.
4. Inference actions (`memory_enrich`, `image_caption`, `audio_transcribe`) are
   **not** exposed via the gateway bridge. They run only from `AgentLoop` so
   that the runtime of the current turn is honored and never resolved silently.

## 7. Compatibility with the legacy MCP servers

`kg.mode="mcp"` routes traffic to `percival-collective-memory` and
`percival-acquire-knowledge` MCP servers configured under
`tools.mcpServers`. The SPA transport does not change in this mode; the
gateway either proxies the request (current behaviour) or returns 503 with
`kg_unavailable`. Native tools are suppressed in `mcp` mode and registered
in `native`/`both` only.