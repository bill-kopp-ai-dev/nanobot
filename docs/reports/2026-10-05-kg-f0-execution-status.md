# KG integration execution: F0 transport checkpoint

Date: 2026-10-05. Scope: partial F0 of
[`../plans/kg-integration-plan.md`](../plans/kg-integration-plan.md). This is
**not** an F0 exit or a native KG release.

## Evidence acquired

- The gateway's real `websockets` listener accepted a credentialed
  `/webui/bootstrap`, authenticated a WebUI-audience socket, delivered an
  allowlisted `settings.runtime_config.update` via `webui_request` and returned
  a `webui_response` with a persisted result. Anonymous socket upgrade was
  rejected (401). `tests/kg/test_transport.py` reproduces this without a model.
- A separate `/kg-interface/api/{memory|acquire}/healthz` HTTP dispatch seam
  rejects missing/URL-only credentials (401); it accepts a bearer but returns
  **503** until real KG services are wired. Unknown API routes return JSON 404
  instead of WebUI `index.html`. The KG API must not be presented as available
  to the SPA while it returns 503.
- `kg` is parsed as a Pydantic config with camelCase/snake_case aliases.
  `allowed_bundle_root()` chooses legacy env, configured parent, then active
  request workspace, and enforces separate read/write roots when workspace
  restriction is enabled. It is a foundation, not yet wired into tools.
- After installing channel dependencies as prescribed by `.agent/gotchas.md`:
  `pytest -q` reported **9110 passed, 47 skipped** (343.43s);
  `basedpyright nanobot` and `ruff check .` reported zero errors.
  A subsequent bearer-only patch passed `pytest tests/kg` (5 tests), full
  typecheck and lint; full pytest was not repeated for that patch.

## SPA calls to migrate

From `spa/src/lib/api.ts` (base `/kg-interface/api`; path prefix is `memory`
unless marked `acquire`). Response schemas live in `spa/src/lib/types.ts`.

| Method | Relative URL | Schema or result | Adapter |
| --- | --- | --- | --- |
| GET | `/{adapter}/healthz` | `HealthResponseSchema` | both |
| GET | `/{adapter}/notes?q=&limit=` | `NoteListResponseSchema` | both |
| GET | `/{adapter}/notes/{id}` | `NoteReadResponseSchema` | both |
| PUT | `/{adapter}/notes/{id}/body` | `WriteResultResponseSchema` | both |
| DELETE | `/memory/notes/{id}?reason=` | `{archived}` | memory only |
| GET | `/memory/notes/{id}/history?limit=` | `NoteHistoryResponseSchema` | memory only |
| GET | `/{adapter}/search?q=&kind=&limit=` | `SearchResponseSchema` | both |
| GET | `/{adapter}/stats` | `StatsResponseSchema` | both |
| PUT | `/memory/notes/{id}/protected` | `ProtectedResultSchema` | memory only |
| PUT | `/memory/notes/{id}/lifecycle` | `LifecycleResultSchema` | memory only |
| POST | `/memory/notes/{id}/flag` | `FlagResultSchema` | memory only |
| POST | `/memory/notes/{id}/resolve` | `ResolveResultSchema` | memory only |
| GET | `/memory/storage/stats` | `StorageSummarySchema` | memory only |
| POST | `/memory/storage/maintenance` | `MaintenanceResultSchema` | memory only |
| GET | `/{adapter}/graph` | `GraphResponseSchema` (file metadata) | both |
| GET | `/acquire/sources?limit=` | `SourceListResponseSchema` | acquire |
| GET | `/acquire/sources/{id}` | `SourceReadResponseSchema` | acquire |
| GET | `/acquire/sources/{id}/chunks/{index}` | `ChunkResponseSchema` | acquire |

The TS functions `forgetNote` and `noteHistory` accept `adapter="acquire"`
but AK's legacy `http_server.py` does **not** expose those routes. Current
`ExtractedNoteView.tsx` avoids calling them. The planned graph/data endpoint is
new; the existing `/graph` returns only file metadata. Follow the actual
component call sites, not just the optional TS adapter parameter.

## Open gates at the F0 checkpoint (historical snapshot before F1)

1. The vendored core is packaged at SHA `ad047aa80a849bc4038daf6efcea63e954008be9`
   with license and declared dependencies. POSIX locking interoperates with
   `flock` in a local test, and an `msvcrt` backend exists for Windows; its
   actual cross-process behavior still requires a Windows runner. macOS was
   not exercised separately. Cross-platform compatibility is not yet proven.
2. Register and compare 20 CM + 14 AK operational contracts, with workspace
   authorization at all read/write entry points and strict bundle selection
   before ID resolution. The current config default is `native`, but it does
   **not yet** filter legacy MCPs or register native tools; suppressing legacy
   MCP servers before replacement tools are registered would break existing
   KG users. Do not deploy as KG.
3. The browser SPA **transport probe** now exercises bootstrap, bearer GET and
   a real allowlisted WS mutation on the listener in Chromium. It requires an
   in-memory bootstrap secret on a password-protected gateway. The production
   SPA still does **not** use this transport: its credential prompt/handoff,
   actual CM/AK routes, reconnect, CAS 409 and end-to-end payload schemas
   need the F6/F7 service/UI work. The probe's mutation is an existing WebUI
   settings action, not a KG write.
4. The SPA dist and vendor notices are included in isolated sdist/wheel and
   passed a clean wheel-install/asset smoke with all assets hash-checked. The
   dist is **untracked** and was built
   from a dirty SPA tree, so a clean checkout without a supplied SPA source
   fails to build and reproducibility is still open. The SPA still targets two
   external HTTP adapters and a graph iframe.

Owner and schedule for CM, AK, gateway and frontend remain to be agreed after
these F0 gates. No release, EOL, migration or rollback claim is supported yet.

## Continuation: packaging and client probe

The SPA repo now contains `src/lib/gateway-transport.ts` (in-memory bootstrap,
bearer GET, authenticated WS mutation with correlation/status/timeout), with
four fixture tests. This module is not yet connected to `src/lib/api.ts` or a
browser session. `bun run test` passed **245 tests** after the localStorage
setup fix; `bun run lint` and `bun run build` passed. The initially observed
test failure was the existing setup's attempt to access `localStorage.setItem`
when Node supplied `localStorage` as `undefined`.

An explicit `PERCIVAL_KG_SPA_SOURCE=/home/bill/Projects/spa` source build
generated a prebuilt `nanobot/web/kg-interface/` snapshot. The Hatch hook
ships its `index.html`, assets, MIT license and `SOURCE.json`, and fails
without source or a prebuilt snapshot. An isolated `uv build --sdist` followed
by `uv build dist/nanobot_ai-0.3.5.tar.gz --wheel` **without the SPA source
setting** passed; both archives contain the snapshot. A clean `--no-deps`
wheel installation located `index.html`, `LICENSE` and `SOURCE.json` using
`importlib.resources`. Gateway dispatch serves the SPA shell and assets with
path containment and never falls back to the WebUI index for KG assets/API.
`tests/kg` now has **7 passing tests**; full Python typecheck and lint passed.

Build provenance: SPA revision `70c05663d838f2131b5c04cefb188a4a60b3166b`,
`SOURCE.json` marks the tree **dirty** (the transport module and test setup
have uncommitted changes). The generated dist remains untracked until the
operator chooses a versioning strategy; don't claim reproducibility from the
SHA alone. At this checkpoint F0 still lacked core vendoring, platform lock
decision, native tools, MCP mode filtering and real-browser transport smoke.
The packaged SPA still uses the legacy adapters; this proves only the
packaging/static seam, not F7. Core vendoring was subsequently added below.

## Continuation: vendored core and distribution check

The core is copied into `nanobot/agent/kg/vendor/okf_bundle_core/` with its MIT
license, `SOURCE.json` containing upstream and vendor Python file hashes, and
`PATCHES.md` identifying the two local patches: a package-relative frontmatter
import and portable locking (`flock` on POSIX, exclusive byte-range locking on
Windows). `tests/kg/test_bundle.py` verifies CAS writes, Git/layout isolation,
frontmatter/path errors, POSIX lock interoperability and snapshot hashes.
`markdown-it-py` and `networkx` are declared in `pyproject.toml`. Windows
locking has **not** been run on Windows, and the vendor's larger original test
suite has not been migrated; these are remaining platform/parity uncertainties.

The Hatch hook now **rejects a vendor snapshot whose file hashes differ from
`SOURCE.json`**, instead of silently updating its manifest, and rejects a SPA
`index.html` that differs from the prebuilt manifest. Updating either snapshot
requires a deliberate rebuild or review. After installing the optional channel
dependencies (the preceding `uv sync` had removed them), the following checks
were run on this state:

- `uv run --no-sync pytest -q tests/kg -o addopts=''`: **11 passed**.
- `uv run --no-sync pytest -q`: **9116 passed, 47 skipped, 1 warning**
  (aiohttp `BasicAuth` deprecation from Discord; 336.37 seconds).
- `uv run --no-sync basedpyright nanobot`: **0 errors**.
- `uv run --no-sync ruff check .`: **all checks passed**.
- `uv build --sdist` followed by `uv build dist/nanobot_ai-0.3.5.tar.gz --wheel`
  without a sibling SPA checkout: **both succeeded**. A separate Python 3.12
  environment installed the wheel with dependencies, then reinstalled the
  rebuilt wheel `--no-deps` and imported `WriteRequest`; `importlib.resources`
  found the vendor license, patch notes, all hash-matching vendor Python files
  and the SPA `index.html`, license and manifest.

At this checkpoint, the next steps were a reproducible SPA snapshot, browser
transport smoke, Windows locking, and a non-empty native registry before any
CM/AK MCP filtering. The browser smoke was subsequently executed below;
F0 and deploy remain **not approved**.

## Continuation: local F0 work closed on Linux

The SPA transport now accepts the gateway bootstrap credential in its
constructor, adds `X-Nanobot-Auth` **only** to `/webui/bootstrap`, and keeps it
in memory. This corrects a real incompatibility: when `tokenIssueSecret` is
configured, an anonymous bootstrap is rejected with 401. Its mutation sender
also rejects frames exceeding the advertised WS frame limit before sending.
The credential's UX/handoff remains an F6/F7 task, not an implemented login.
`spa/src/tests/gateway-browser-probe.ts` is an isolated smoke entry, not part
of the shipped SPA bundle. `tests/kg/test_transport.py` compiles it with Bun,
serves it using the actual gateway listener, and runs it in headless Chromium.
The test observes 401 without bootstrap credentials, authenticated GET 503,
then a real WebUI settings mutation persisted through WS; it checks no secret
was placed in page URL or browser localStorage. Run explicitly with
`PERCIVAL_KG_SPA_SOURCE=/home/bill/Projects/spa` plus Bun and Chromium.

The SPA build manifest now hashes **every** distributed asset, including its
license, and the Hatch hook rejects changed/missing/extra assets and stale
files on source refresh. `uv build --sdist` with
`PERCIVAL_FORCE_KG_SPA_BUILD=1` and `PERCIVAL_KG_SPA_SOURCE` rebuilt the
snapshot; the wheel built from that sdist without a sibling SPA repo. A clean
wheel environment resolved every manifest asset and served a JavaScript asset
through `serve_kg_static` with status 200. This proves the local snapshot,
**not** clean-checkout provenance: the SPA source still has uncommitted changes
and the packaged snapshot is not tracked.

An opt-in parity test compares CAS/write/read outputs from the pinned
`okf-bundle-core` checkout with the vendor snapshot in two isolated processes,
and checks the vendor license against the source. Run with
`PERCIVAL_KG_CORE_SOURCE=/home/bill/Projects/okf-bundle-core` (at SHA
`ad047aa80a849bc4038daf6efcea63e954008be9`). On this checkout:

- `PERCIVAL_KG_CORE_SOURCE=... PERCIVAL_KG_SPA_SOURCE=... uv run --no-sync pytest -q tests/kg -o addopts=''`: **13 passed** (includes Chromium and core parity).
- The full `pytest -q` with both source variables set: **9118 passed, 47 skipped, 9 deprecation warnings** (317.38 seconds). This replaces the earlier full-suite result for the current tree.
- SPA `bun run test`: **248 passed**; `bun run lint` and `bun run build`: passed.
- `uv run --no-sync basedpyright nanobot` and `uv run --no-sync ruff check .`: passed.

The platform gate cannot be closed locally: no macOS/Windows runner was used,
so the Windows `msvcrt` backend remains experimental despite import/build
checks on Linux. F0's active registry/mode gate also depends on registering
real native tools first. Filtering existing CM/AK MCP servers now would
silently remove working legacy capabilities while all 34 native replacements
are absent; keep the filter pending until the registry is non-empty and
verified. No KG release or claim of complete F0 follows from these probes.

## F1: native CM note tools

Implemented the first four native CM operations:

- `cm_notes_read` returns note body, plain JSON frontmatter, backlinks and
  content/body hashes; it omits the internal typed-frontmatter object.
- `cm_notes_write` creates or edits using the vendored core's body/content
  CAS, atomic write, GitStore commit/log and rollback semantics.
- `cm_notes_search` is case-insensitive and uses Python text scanning rather
  than requiring `rg`; it caps query length at 500 characters and result count
  at 200.
- `cm_note_history` reports recent commits for one validated note ID, capped
  at 1000 entries.

Tool I/O runs via `asyncio.to_thread`. CM tool configuration is passed from
`Config.kg` through `AgentLoop.from_config` into `ToolContext`. Each operation
resolves its root against the current request workspace; when workspace
restriction is enabled, an external configured root is denied. F1 does not
yet expose configuration for granting external KG roots. Bundle and matching
note paths are checked against symlink escape before content is opened.
ToolLoader discovers the four built-ins in `native`/`both`, and suppresses
them in `mcp` mode without changing legacy MCP configuration.

Evidence on 2026-10-05:

- `uv run --no-sync pytest -q tests/kg/test_cm_core.py -o addopts=''`: **8
  passed**. Includes create/read, stale CAS conflict, commit-failure rollback,
  bounded search without subprocess, history, workspace isolation, pre-open
  symlink containment and `AgentLoop.from_config` registry composition without
  an external model call.
- Full Python suite with pinned core and SPA source variables:
  **9126 passed, 47 skipped, 1 deprecation warning** (344.88 seconds).
- `uv run --no-sync basedpyright nanobot`: passed (0 errors).
- `uv run --no-sync ruff check .`: passed.

This closes the F1 implementation and local code gates. It does not close the
F0 cross-platform/distribution provenance gaps above.

## F2: native CM links, policy, stats, storage, graph and forget

Implemented the remaining 15 CM operational tools, bringing the native CM
surface to 19 tools (the twentieth, `memory_enrich`, remains F3):

- Links: `memory_link`, `memory_batch_link` (per-edge partial success), and
  `memory_attach`; forward target references and the legacy parallel-array
  batch form are supported.
- Lifecycle/review: `memory_forget` archives with a Git commit and rollback;
  `memory_set_protected`, `memory_set_lifecycle`,
  `memory_flag_for_review`, and `memory_resolve_review` preserve P11 CAS,
  protection, lifecycle and review semantics.
- Read-only inspection: `memory_stats`, `asset_get_path`,
  `graph_neighbors`, `graph_shortest_path`, `memory_storage_stats`, and
  `memory_aging_candidates`.
- `memory_repo_maintenance` defaults to dry-run. Actual Git GC resolves the CM
  root with write authorization and holds the exclusive bundle lock.

All tools are suppressed in `mcp` mode and registered in `native`/`both`.
Filesystem paths are checked against bundle containment, and configured roots
outside a restricted workspace are rejected for both read and write
capabilities. Tool I/O runs outside the asyncio event loop.

Evidence on 2026-10-05:

- `uv run --no-sync pytest -q tests/kg -o addopts=''`: **24 passed, 2
  skipped**. The F2 cases cover forward-reference and partial batch results,
  archive-not-delete, safe asset resolution, P11 CAS/protection/review,
  storage dry-run, lifecycle candidates, missing/present graph behavior,
  registry mode and external-root denial.
- Full `uv run --no-sync pytest -q`: **9129 passed, 49 skipped, 1 warning**
  (332.41 seconds).
- `uv run --no-sync basedpyright nanobot`: passed (0 errors).
- `uv run --no-sync ruff check .`: passed.

F2 is implemented and its local code gates pass. The full F0 release gate is
still open; F3 (CM enrich) has not started.

## F3: native CM enrichment and guidance

Implemented `cm_memory_enrich` with a typed PydanticAI proposal and 45-second
pre-write/model budget; absent `MINIMAX_API_KEY` returns `missing_key` without
writing. The model may only propose summary, tags and supersedes; writes use
body-hash CAS. The outbound client validates the endpoint and pins DNS for
each request and redirect without using ambient proxies. Six legacy prompts
were adapted as built-in skills, not registered as additional operational tools.

Evidence on 2026-10-06: `tests/kg` **31 passed, 2 skipped**; full `pytest -q`
**9136 passed, 49 skipped, 1 warning** (355.80 seconds); `basedpyright nanobot`
zero errors and `ruff check .` passed. A real-key smoke was not run. See the
[F3 implementation note](../plans/kg-integration-plan.md#f3--cm-enrich-e-guidance-1-tool)
for operational limits. The F0 gates above remain open; F9 skill usage and
graph CLI validation remain pending.

## F3 correction: use the agent's selected inference runtime

On 2026-10-06 the CM enrichment tool was changed to consume the requesting
turn's immutable `LLMRuntime`. It calls the existing `LLMProvider` with the
captured model/generation and validates the returned proposal with Pydantic.
It no longer constructs a PydanticAI/MiniMax client or reads a CM-specific key.
Missing runtime gives `runtime_unavailable` without a write. The previous F3
evidence above is historical, not evidence for this changed contract.

F0 already binds the admitted runtime to `RequestContext`; F1/F2 are
deterministic and required no code changes. Test fakes cover two consecutive
turns using different providers/models, captured generation, output retries,
timeout, CAS, no-op and error paths. `tests/kg`: **32 passed, 2 skipped**;
full Python suite: **9137 passed, 49 skipped, 1 warning** (330.78 seconds);
`basedpyright nanobot` zero errors, `ruff check .` passed. A live provider call
was not made. The guarantee applies to native tools; `kg.mode=mcp` remains a
legacy rollback path with its own inference client, and `both` exposes both.
F0 platform/distribution gaps and later SPA/AK phases remain open.
