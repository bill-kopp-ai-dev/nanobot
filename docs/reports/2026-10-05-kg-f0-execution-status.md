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
   `flock` in a local test. The Percival release is **Linux-only** (operator
   decision 2026-10-06, §B4): the `msvcrt` backend remains in the vendor for
   Windows developers but is no longer exercised by CI, smoke scripts or
   release gates; macOS support is removed from `docs/plans/kg-integration-plan.md`
   and `.github/workflows/kg-platform.yml`.
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
import and POSIX locking (`flock` on Linux, the only platform Percival
supports). `tests/kg/test_bundle.py` verifies CAS writes, Git/layout isolation,
frontmatter/path errors, POSIX lock interoperability and snapshot hashes;
the `if os.name == "nt"` branch is documented as "vendor-only, not exercised".
`markdown-it-py` and `networkx` are declared in `pyproject.toml`. The
vendor's larger original test suite has not been migrated; this is the
only remaining parity uncertainty on the supported surface.

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
transport smoke, POSIX lock smoke, and a non-empty native registry before any
CM/AK MCP filtering. The browser smoke was subsequently executed below;
F0 and deploy remain **not approved**. (Windows locking was retired from
the gate on 2026-10-06 when the operator declared Percival Linux-only —
see §B4.)

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

The platform gate is closed by scope: the Percival release supports Linux
only (operator decision 2026-10-06, §B4). The Windows `msvcrt` backend
remains in the vendor for local development but is not exercised by CI
or release gates; macOS support has been removed from the plan and the
CI matrix. F0's active registry/mode gate also depends on registering
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

## F4: native AK ingest/read/multimodal

Eight native tools were ported from `percival-acquire-knowledge` into
`nanobot/agent/kg/ak/` plus three `ak_*.py` files under
`nanobot/agent/tools/`. The bundle layer reuses the same vendor primitives
as CM (`okf_bundle_core` GitStore / lock / frontmatter / path layout)
and the tool layer follows the F1/F2 contract (`asyncio.to_thread` for
filesystem-bound calls, `AKTool` base with `restrict_to_workspace`
plumbing via `nanobot/agent/kg/roots.py`).

Multimodal capability is now first-class on the LLM runtime: a new
`LLMProvider.supports_modality(modality, model)` hook with a `False`
default returns explicit `unsupported_capability` errors instead of a
stubbed answer. The OpenAI-compatible, Anthropic, Bedrock and Codex
backends declare `image` support; no backend currently declares `audio`
input, so `ak_audio_transcribe` and image ingest of audio files surface
the gap explicitly. `image_caption` sends a multimodal `chat` request
through `runtime.provider.chat_with_retry` with the captured model and
generation; the diskcache key is
`kind:provider:model:preset:parser_version:etag`, so a turn served by a
different runtime cannot reuse a stale caption. `diskcache` is now a
dev dependency in `pyproject.toml [project.optional-dependencies].dev`.

**Test evidence (2026-10-06):**

| Suite | Result |
| --- | --- |
| `tests/kg/test_ak_core.py` | 11 passed (paths, id, mimetype, asset containment, symlink rejection) |
| `tests/kg/test_ak_read.py` | 4 passed (source_list with partial atomisation, source_search, source_stats, get_laterally_isolated_notes grouping) |
| `tests/kg/test_ak_multimodal.py` | 8 passed (image_caption via runtime, image rejection, finish_reason error, invalid_output, audio gap, runtime missing, default modality) |
| `tests/kg/test_ak_ingest.py` | 7 passed (markitdown happy path, dedupe, unknown extension, parse rollback, image ingest via runtime, missing runtime) |
| `tests/kg/test_ak_registration.py` | 8 passed (8 ak_ tools in native/both, suppressed in mcp, per-tool feature flags, structured tool errors) |
| `tests/kg` overall | **85 passed, 2 skipped** |
| `pytest` global | **9175 passed, 49 skipped, 1 warning** (315.99 s) |
| `basedpyright nanobot` | 0 errors |
| `ruff check .` | passed |
| `git diff --check` | clean |

A live provider call was not made. The audio capability gap is the
only one the plan explicitly defers: while no backend supports audio
input via `LLMProvider.chat`, `ak_audio_transcribe` returns
`unsupported_capability` with a "replan F4 audio parity" message rather
than substituting a different model. F5 (write/link/graph/forget) and
F6 (gateway bridge + SPA contract) have not started.

## F4 review: bugs and fixes (2026-10-06)

Review found and corrected the following reachable issues in the initial
F4 implementation:

- **Workspace escape on ingestion:** `ak_source_ingest` accepted any
  absolute input path even with `restrict_to_workspace=True`. The tool
  now resolves paths against the active request workspace and applies
  the workspace policy before reading the source.
- **Symlink reads outside the AK bundle:** discovery operations checked
  the `notes/` directory but not each Markdown entry. AK path checks now
  validate each note and the critical `sources`, `.git`, `.gitignore`,
  lock, `.cache` and `.telemetry` roots before read/write operations.
- **Ingest audit/rollback:** the initial path committed the note before
  appending `log.md`, so the audit entry was not in the same commit; the
  rollback also did not retain the created note path. Ingest now appends
  the log before committing both explicit paths together, and removes the
  staged binary/note and restores the prior log if commit fails. A copy
  whose hash differs from the pre-copy hash is rejected. Cancellation
  waits for in-flight thread I/O and does not roll back files after a
  successful commit.
- **Model capability overclaim:** all models behind compatible protocols
  were initially treated as vision-capable. Support is now restricted to
  recognized image-input model families; unknown/text-only models return
  `unsupported_capability` before sending an image.
- **Optional-cache import and stale processing version:** `diskcache` was
  imported at module load despite being described as optional. It is now
  imported only by `get_cache`; tools remain importable and captioning
  proceeds without persistent cache. The cache key now includes an explicit
  `image-caption-v1` processor version, so prompt/schema changes can invalidate
  old captions deliberately.
- **Unbounded/invalid multimodal input/output:** image inputs are capped
  at 20 MiB; filesystem/cache work is moved off the event loop; caption
  JSON is validated against a bounded schema; malformed cache entries are
  evicted, and invalid model output is reported as `invalid_output`.

Regression coverage exercises workspace denial, external note symlink
rejection, copy-race detection, note+log commit rollback, model-specific
capability, cache identity across models, oversized images and absent
optional `diskcache`. Final gates after review: `tests/kg` **80 passed,
2 skipped**; full `pytest -q` **9185 passed, 49 skipped, 1 warning**
(312.74 seconds);
`basedpyright nanobot` **0 errors**; `ruff check .` passed; `git diff --check`
clean. No live provider call was made. The previously noted F0 gaps remain
open; F5 is not started.

## F5: AK atomization, links, graph queries and archive (2026-10-06)

Added six native AK tools (`ak_note_write_extracted`, `ak_note_link`,
`ak_note_batch_link`, `ak_graph_neighbors`, `ak_graph_shortest_path`,
`ak_source_forget`) for 14 AK tools total in native/both. The MCP-only mode
still suppresses them. The services are reusable from the gateway in F6.

Atomization uses an exclusive bundle lock and a single Git commit for the
ExtractedNote, its Source's `chunks_atomized` update, and `log.md`. It supports
optional Source `expected_content_hash` CAS, rejects out-of-range chunks,
deduplicates `(source_id, chunk_index)` on repeated calls, and repairs a
missing chunk flag on an existing extracted note. Rollback restores files and
audit history if a commit fails. Each batch link is independently committed
and returns per-edge applied/skipped/error. Forward refs must be canonical AK
IDs; prefixed CM references are refused. D65 relation storage and precedence
were checked against a built graph. Graph queries use exact IDs and validate
the artifact's symlink boundary; graph rebuild remains a separate F8 task.
Forget archives the Source note and its associated raw file under
`_archive/sources/YYYYMM/`, leaving derived notes active; binary files are
never staged in Git. A failed commit restores both paths and the audit log.
Archive, note and source paths are checked against symlink escapes. No real
bundle was mutated.

**Verification:** `tests/kg` 90 passed, 2 skipped; `pytest -q` 9195 passed,
49 skipped, 1 unrelated aiohttp deprecation warning (348.44 s);
`basedpyright nanobot` 0 errors;
`ruff check .` passed; `git diff --check` clean. F0 platform/distribution
remains open; F4 audio parity remains unsupported; F6 has not started.

### F5 review fixes (2026-10-06)

The focused adversarial review found and fixed three issues:

- Bundle containment alone allowed internal symlinks to redirect a graph
  read, note mutation, or archive operation into a different bundle area.
  F5 now rejects symlinks in the relevant path components, including links
  that resolve inside the bundle.
- The shared ID regex uses `$`, which can match before a terminal newline.
  F5 services now require a full ASCII `YYYYMMDD-HHMMSS` match before using
  IDs in note lookup, graph access, links or archive paths.
- Atomization's dedupe scan propagated malformed YAML from any unrelated
  note, blocking valid work. It now skips unreadable/malformed candidates
  and only reuses a note whose filename ID agrees with its frontmatter ID.
- Multiline `source_forget` reasons could add rows to the Markdown audit
  table. The reason is now collapsed to one line before logging/committing.

Regression tests cover internal symlink redirection, newline IDs, unrelated
malformed notes, and multiline audit reasons. Re-ran all gates after these
fixes. No real AK bundle was modified during the review.

## F6: gateway bridge and SPA contract (2026-10-06)

`nanobot/webui/kg_http.py` now owns a native KG bridge: authenticated HTTP
reads under `/kg-interface/api/{memory|acquire}/`, typed allowlisted WebUI WS
mutations via `webui_request`, explicit mode/root checks, and JSON errors.
Read routes cover health, lists, reads, source/chunks, search, stats, CM
history/storage, graph metadata and a new bounded (8 MiB) NetworkX node-link
`/graph/data`. Actions cover CM/AK body CAS and CM archive, protected,
lifecycle, review and storage maintenance. No inference action was exposed:
the bridge never manufactures a provider/runtime. It calls CM/AK services,
not Tool text results. No HTTP GET performs a write; unknown KG API paths
return JSON 404. Bearer-in-URL does not authenticate. WS requires an issued
WebUI-audience token; operations use the gateway's WebUI default workspace,
not a browser-provided root/session path. Configured external bundle roots
are denied when this scope restricts workspace access. F6 also hardened
internal CM symlink handling for note/archive paths and single-line CM archive
reasons (the new SPA route made these paths browser-accessible).

The sibling `spa` source now connects `GatewayKgTransport` to `api.ts`, keeps
the gateway key and issued tokens in memory, retries GET once on bearer
expiry, and reports uncertain WS timeouts/disconnects rather than replaying a
write. `KgClientProvider` prompts for a key when anonymous bootstrap cannot
grant browser tokens. Vite dev proxies `/webui/bootstrap` and the KG API to
`:8765`. `GraphDataSchema` validates graph payloads; the existing `GraphView`
still uses the legacy export iframe until F7. The bundled SPA snapshot in
`nanobot/web/kg-interface` has **not** been replaced; F7 owns reproducible
snapshot/wheel and the D3 view. Cross-host trusted-proxy bootstrap without
tokens is accepted for a same-origin WebSocket, but cross-origin WebSocket
URLs and multi-workspace selection remain outside this client contract.

**Evidence:** `tests/kg/test_gateway_f6.py` uses an in-process `websockets`
listener, temporary CM/AK bundles and the real bootstrap/bearer/WS channels;
checks 19 SPA GET contracts, eight WS action paths, CAS 409, anonymous GET
401, anonymous WS 401, invalid ID 400, missing graph/note 404, external root
and symlink 403, and JSON 404 rather than HTML fallback. SPA
`gateway-api-contract.test.ts` validates the same call inventory through
Zod and action mapping; `gateway-login.test.tsx` exercises in-memory key
handoff. Python `pytest -q`: **9196 passed, 49 skipped, 1 unrelated aiohttp
warning** (329.25 s); `basedpyright nanobot`: **0 errors**; `ruff check .`:
passed; SPA `bun run test`: **253 passed**, `bun run lint` and `bun run build`:
passed. `git diff --check` passed in both repos. No actual provider call or
real user bundle mutation was made. The F0 packaging/platform gates and F4
audio gap remain open; F7 is next for a browser/wheel smoke with the actual
new SPA snapshot.

A subsequent `tests/kg` run hit the minute boundary in the older
`test_new_id_bumps_one_second_when_candidate_already_used`: it expected
the next ID to have the same minute prefix, which is false at 12:59:59.
The test now freezes the clock at 12:59:59 and asserts the actual 13:00:00
collision result. The relevant gate passed after this test-only correction:
**91 passed, 2 skipped**, with typecheck, lint and diff check passing again.
The full Python suite above precedes only this deterministic test-fixture
change; it is not presented as a rerun after that edit.

### F6 review fixes (2026-10-06)

Review against the routes the SPA can reach found and fixed:

- CM and AK list/search could follow symlinks pointing to another path inside
  the same bundle. Their shared note-path scans now reject internal symlinks;
  gateway tests verify both list endpoints return 403.
- An oversized graph was mapped through generic `ValueError` to HTTP 400.
  Graph size violations now return HTTP 413 and have a listener test above 8
  MiB; graph metadata remains available and missing/corrupt graph payloads are
  distinct from data.
- Body CAS conflicts had status 409 but only a generic error message, so the
  SPA could not populate its three-way conflict resolver. The gateway now
  returns the base hash, current body/hash on 409; the SPA converts the WS
  error payload back into `ApiError.detail`, with regression coverage.
- Trusted-proxy bootstrap intentionally omits bearer and WS tokens because
  the proxy authenticates each request (and this bootstrap shape omits
  `expires_in`). The SPA transport now accepts that explicit credential-less
  bootstrap mode, caches it briefly and adds no fabricated token to GET or WS
  requests. A partial bootstrap (only one token) still fails closed.

Reverification after these changes: full Python `pytest -q` **9196 passed,
49 skipped, 1 unrelated aiohttp deprecation warning** (328.82 s);
`basedpyright nanobot` 0 errors; `ruff check .` passed. Focused KG tests:
**91 passed, 2 skipped**. SPA: **253 passed**, lint/build passed. The test
suite still emits its existing happy-dom aborted iframe-fetch diagnostics;
they do not fail the run. No real bundle or provider was used.

## F7: packaged SPA and native D3 GraphView (2026-10-06)

The SPA now reads `/graph` metadata and authenticated `/graph/data`, validates
node-link `nodes`/`links`, and renders an SVG graph with `d3-force` capped at
240 nodes and 600 links. Clicking a CM node opens `#/notes/:id`; AK
ExtractedNote and Source nodes open `#/extracted-notes/:id` and
`#/sources/:id`. A request generation guard discards obsolete CM responses
after switching to AK; missing, empty and invalid graph data have visible
states. The legacy export-HTML iframe, its HEAD probe, dev `graph.html`
middleware and graphify URL doctor check were removed from the active
client. Bundle selection remains available while data is loading. This is a
bounded visualization, not a graph rebuild (F8).

Hatch now verifies the old snapshot before replacing stale hashed assets,
then checks every new asset against `SOURCE.json`. A source build with
explicit `PERCIVAL_KG_SPA_SOURCE` and `PERCIVAL_FORCE_KG_SPA_BUILD=1`
produced `dist/nanobot_ai-0.3.5.tar.gz`; a wheel built **from that sdist**
without a SPA checkout produced `nanobot_ai-0.3.5-py3-none-any.whl`. A fresh
Python 3.12 venv installed the wheel and dependencies; `importlib.resources`
found WebUI and SPA, and all nine manifest assets matched their SHA-256
hashes. The gateway served the same-origin shell/assets and restricts HTML
fallback to SPA routes, leaving unknown assets/API as genuine 404 responses.
A real Chromium test on the in-process gateway opened the WebUI and SPA,
loaded the bundled graph for CM and AK, authenticated with the gateway key,
followed an AK node to its hash route, and checked that secrets were not
persisted. The browser test also passed with SPA assets taken from the clean
wheel installation; only temporary bundles were used and no inference
provider was invoked.

Final gates: SPA `bun run test` **250 passed** (36 files), `bun run lint` and
`bun run build` passed; Python `pytest -q` **9197 passed, 49 skipped, 1
unrelated aiohttp deprecation warning** (346.58 s), `basedpyright nanobot` 0
errors and `ruff check .` passed. After adding the optional wheel-asset
override to the browser test, that test, Ruff and `git diff --check` were
rerun successfully.

At the F7 validation, `SOURCE.json` recorded SPA revision
`2ac3c664e2bf821ad11775cd82fed68802cfa5e0` with **`dirty=true`**: the
hash-checked binary snapshot was in the fork but the new SPA source changes
had not yet been committed. Those changes were subsequently committed as
`f607d6a`; the snapshot's clean-source provenance has **not** been revalidated
against that commit. Rebuild/verify the snapshot from clean source before
claiming source-reproducible provenance. The independent F0 platform and F4
audio gaps are unchanged.

## F8: native `nanobot kg` CLI (2026-10-06)

The registered Typer group provides read-only `doctor --json` and `bundle path`,
confirmed `bundle init` (GitStore and layout, refusing nonempty destinations,
regular files, or invalid parents), atomic `graph rebuild` using the vendored
deterministic builder, P11 structural candidate discovery with dry-run/apply
and per-note CAS, and the one-shot AK lateral-link migration with
dry-run/apply, cross-bundle/broken-target reporting, Git commit and rollback
on failure. Parent/bundle `--bundle-root`, configured workspace, legacy env
root precedence and restricted-workspace policy are exercised with temporary
bundles. No model or legacy CLI is involved; community labeling and legacy
`graphify cluster-only` artifacts are not provided by this command.

A first review caught and fixed three defects before publishing the gate:

- `migrate_lateral_links` crashed during dry-run on a single unreadable note
  or a malformed sibling lookup. The scan tolerates `OSError` /
  `UnicodeDecodeError` and only requires a present `notes/` directory from
  the CM sibling — not a fully-initialized bundle.
- `init_bundle` accepted the parent of a regular file as a bundle location
  and only failed deep in `mkdir` with `Errno 20 Not a directory`. It now
  rejects regular files, regular-file parents and non-empty destinations up
  front with explicit messages.
- `bootstrap_p11 --apply` collected candidates under read-only authorization
  before validating write capability; the order was corrected.

`tests/kg/test_cli_kg.py` passed **9 tests** via `CliRunner` (including JSON,
exit codes, idempotence, env precedence, corrupt graph, init rejection of
regular files, partial CM sibling + non-UTF-8 note in AK migration, root
escape/symlink denial, and preservation of the previous graph on a failed
rebuild). Full Python `pytest` passed **9206, 49 skipped, 1 existing aiohttp
deprecation warning** (352.28 s), `basedpyright nanobot` 0 errors,
`ruff check .` and `git diff --check` passed. The actual console entrypoint
displayed `nanobot kg graph rebuild --help`. No real bundle, LLM provider,
packaging rebuild or upgrade/rollback data-copy smoke was used for F8. F0
distribution/platform and F4 audio remain independent open gates.

## F9: skills, operations docs and migration rehearsal (2026-10-06)

Six existing CM skills now refer to the native F8 CLI and turn runtime;
six AK guidance skills are new first-level `nanobot/skills/ak-*/SKILL.md`
entries. `tests/kg/test_f9_skills.py` verifies the real non-recursive
`SkillsLoader` loads all 12 with valid frontmatter and command help for
both graph rebuilds. The native SPA development wrapper starts gateway +
Vite with cleanup; the SPA doctor and contract-capture script address
the authenticated gateway rather than legacy :8001/:8002 adapters. Added an
ADR, copy-only migration/rollback guide, candidate release notes, snapshot
update workflow and a current upstream-sync runbook. Legacy repositories were
not frozen; D5/D10 require the later stabilization/approval decision.

`tests/kg/test_f9_migration_copy.py` exercises backup of both temporary
bundles including AK `sources/` bytes and `.git/`, dry-run, link migration,
graph rebuild and restoring a fresh copy of the pre-cutover snapshot. This
does **not** prove that actual operator bundles or the legacy MCP server can
read post-native writes. Full Python `pytest`: **9221 passed, 49 skipped,
1 existing aiohttp warning** (372.51 s); `basedpyright nanobot`: 0;
`ruff check .`: passed. SPA `bun run test`: **251 passed**, lint and build
passed; a mocked process test verified gateway/Vite shutdown on SIGTERM;
shell syntax/help and payload-capture help passed. No real provider,
live migration or browser session was exercised here.

**Distribution gate failed:** `uv build --sdist` stopped in
`hatch_build.py::_verify_kg_interface` because the tracked
`assets/index-BzJKk184.js` has SHA-256
`216eba00019761c9789397194092e48f117d2b4f8067cca3ac5ff2a29d41b69b`
while `SOURCE.json` and the current SPA build claim
`2ad21422561217fb441de6f3362d6fad938b0912b50cf7984ba2250aac733836`.
The discrepancy is present in HEAD, not introduced by the F9 edits.
Three older tracked assets were already deleted in the local worktree before
F9 and remain unstaged. The SPA source snapshot also reports `dirty=true`
with revision `2ac3c664`; neither a clean-source build nor wheel/sdist smoke
can be claimed. Reconcile the binary snapshot and obsolete tracked assets in
a reviewed candidate, then re-run sdist → wheel → clean-install/hash smoke
without a neighboring SPA. F0 platform support and F4 audio remain open;
release and EOL are not approved.

## F9 snapshot reconciliation (2026-10-06)

The previous failed sdist gate above is historical. In a detached, clean SPA
worktree at `f607d6a2f97d7a539170e99ec843c3cd02691b47`,
`bun install --frozen-lockfile`, lint and build passed. Vitest initially failed on the
current Node runtime's missing global localStorage file; with
`NODE_OPTIONS=--localstorage-file=<temporary-file>` the **250 tests passed**
without changing source. Clean-source output matches the nine manifest
assets, `index.html` and `bun.lock`: JS SHA-256
`2ad21422561217fb441de6f3362d6fad938b0912b50cf7984ba2250aac733836`,
HTML `a156846a059eb4a4064d74c658d8f7dcfbf6bec755158e99083dde47f55fa1d3`,
lock `1a10d3716ef28bac480cad7f36a0f26e009d0c8342a486af636bb6fa207f4dcf`.
The tracked JS in the fork had the wrong bytes (`216eba…`, 10 bytes shorter),
despite the manifest pointing at `2ad214…`. It was replaced with **only**
the corresponding clean-source build asset (verified by SHA); `SOURCE.json`
now names the source commit with `dirty=false`. Generated whitespace-only
license separator lines were preserved byte-for-byte; `.gitattributes`
disables only `blank-at-eol` warnings for bundled JS so `git diff --check`
passes without modifying the reviewed artifact. Three pre-existing deletions
of old hashed assets match the absence of those files in the clean build and
manifest; they remain unstaged, and must be included in any later snapshot
commit for a clean checkout to pass the hook.

With no explicit SPA source override, the corrected local fork produced
`nanobot_ai-0.3.5.tar.gz` (SHA-256
`8465851058c67dacf3ac5594978455d558772478e96758f7bbae3d14feff52dc`).
`uv build --wheel <sdist>` then ran from a temporary artifacts directory and
reported **no `webui/` source tree**, using only prebuilt contents from the
sdist. Wheel `nanobot_ai-0.3.5-py3-none-any.whl` SHA-256:
`1dbf2b4ec5262cd73d1b6fa1d1c8ce8a4ee0de8f16db8d9fc584619c5ad9d7a1`.
Archive inspection confirmed both distributions contain exactly the nine
manifest-listed KG assets with their hashes, all **12 KG skills**, matching
manifest bytes and vendored core license; no obsolete hashed assets.

Installed the wheel **with dependencies** into a fresh Python 3.12 venv
outside the checkout. From the temporary artifacts directory with no
`PYTHONPATH`, imports resolved under that venv's `site-packages`. Resource
hashes, skills and license matched; the installed CLI's
`nanobot kg graph rebuild --help` worked. An in-process gateway listener
served installed WebUI `/`, `/kg-interface/`, all three index asset references
and the hashed JS; unknown assets returned 404 and anonymous KG API returned
401. Focused `tests/kg/test_f7_browser.py` plus 14 F9 skill tests: **15 passed**.
`ruff check .`, `basedpyright nanobot` (0 errors) and `git diff --check` passed
after reconciliation. The broader Python suite's **9221 passed/49 skipped**
is carried from the preceding F9 step: runtime Python was not changed here.

These artifacts verify the current **working tree**, not an independently
cloned fork revision: JS, manifest and old-asset deletions are not committed.
Re-run from a clean checkout of the eventual commit before release. This
smoke does not validate real-bundle migration/rollback, audio, an approved
version/tag or public distribution. (Windows/macOS platform coverage is
out of scope for the Percival release — operator decision 2026-10-06,
§B4.) No commit, push, tag, publication or changes to legacy MCP repos
were performed.

## F9 close-out: A1–A10 audit follow-through (2026-10-06)

A1–A10 follow-through from the audit at the top of this report. All gates
ran against the uncommitted F9 working tree before this commit was created.

| Item | Result |
| --- | --- |
| A1 — full Python suite | `uv run --no-sync pytest -q` → **9221 passed, 49 skipped, 1 warning** in 341.72 s |
| A1 — typecheck | `uv run --no-sync basedpyright nanobot` → **0 errors, 0 warnings, 0 notes** |
| A1 — lint | `uv run --no-sync ruff check .` → **all checks passed** |
| A1 — whitespace | `git diff --check` → **clean** |
| A4 — gitignore | `.positronic/` added to `.gitignore`; `git check-ignore -v .positronic` confirms `gitignore:9:.positronic/` |
| A5 — endpoint inventory | `docs/kg-endpoint-inventory.md` written; 11 GET routes + 8 WS actions + status matrix cross-checked against `nanobot/webui/kg_http.py` and `nanobot/webui/kg_static.py` |
| A7 — platform CI | `.github/workflows/kg-platform.yml` reduced to `ubuntu-latest` (Linux-only, per operator decision 2026-10-06) plus `scripts/kg_platform_lock_smoke.py` and `scripts/kg_platform_modality_smoke.py`; YAML syntax validated locally; both smoke scripts pass on Linux |
| A8 — release gate | `docs/releasing.md` item 10 (KG platform gate) requires Linux-only smoke + KG focused tests green; the previous "matrix green on three runners" requirement is removed |
| A10 — migration/rollback coverage | `tests/kg/test_f9_migration_copy.py` grew from 1 → 7 tests; covers idempotent apply, cross-bundle skip, dry-run no-mutation, binary preservation and concurrent native writers (2 and 4 threads) |

### Re-estimate (A6)

The original 12-working-day / 6.5k LOC estimate from the 2026-10-05 plan is
explicitly invalidated by §1 of the plan and the four-day F0–F9 audit. The
recorded cadence here is 10 phases executed sequentially with frequent
re-review (F3 twice, F4 twice, F5 once, F6 once, F7 once, F8 once, F9
twice). Workload distribution by area:

| Area | Days | Source |
| --- | --- | --- |
| CM core (F1+F2) | ~2 | 4 + 15 tools, CAS/P11, vendor lock integration |
| CM inference (F3, original + correction) | ~1.5 | LLMProvider swap, two waves of regressions |
| AK ingest/read/multimodal (F4) | ~1 | vendor re-use + capability overlay |
| AK write/link/graph/forget (F5) | ~1 | atomisation + lateral-link migration |
| Gateway bridge (F6) | ~1 | listener seam, WS allowlist, mutation payloads |
| SPA bundle + D3 (F7) | ~1 | hatch hook rewrite + browser smoke |
| CLI (F8) | ~0.5 | typer group, 5 subcommands |
| Docs/migration/skills (F9) | ~1 | 12 skills, ADR, snapshot workflow, migration guide |
| Audit close-out (A1–A10, this commit) | ~0.5 | gates, CI matrix, inventory, re-estimated above |

Summed against an already-vendored core (`okf-bundle-core` shipped in the
fork), the realistic schedule to ship a tagged KG-capable version from this
commit is:

1. **B6/B7** — operator-supplied copies of real bundles → 1 day of cutover
   rehearsal; **human-driven**, not on the agent critical path. **Owner:
   the operator** (decision 2026-10-06 — B6/B7 will be executed by the
   operator personally: B6 produces an anonymised tarball (or authorises
   the agent to copy and anonymise one) of a real bundle, B7 runs
   `kg doctor --json`, `nanobot kg ak-migrate-lateral-links --apply`,
   and the legacy-MCP rollback read on a copy, then decides the
   `kg.mode="native"` cutover). The agent stays on standby for follow-up
   scripts but does **not** own the rehearsal or the cutover.
2. **B5** — provider/model decision for audio (F4) → 0.5 day of integration
   plus 0.5 day of regression; **decision-driven**, not on the agent
   critical path.
3. **B4** — Linux-only documented support → closed by operator decision
   2026-10-06. `.github/workflows/kg-platform.yml`, `tests/kg/test_bundle.py`,
   `docs/plans/kg-integration-plan.md` §2 item 7 and F0 bullet, `docs/kg-release-notes.md`
   distribution/plataformas, `docs/kg-migration.md` install notes, and the F0
   report (above) all reflect Linux-only. The `msvcrt` backend remains in the
   vendor as a courtesy for local Windows development; it is not part of any
   release gate.
4. **B1/B2/B8/B9** — commits/push e freeze/EOL concluídos em 2026-10-06;
   arquivamento no GitHub ainda é ação humana pelo console web.
5. **B10/B11/B12/B13** — decisões de governança confirmadas pelo operador
   em 2026-10-06; ver [política Percival](../percival-governance.md).
   Implementação do CI geral e empacotamento Linux-only e sign-off final
   do SHA candidato ainda pendentes.

**Atualização posterior:** a reconciliação F9 e a prova A3 em checkout
limpo não fecham os gates de release do Percival: o alinhamento do CI geral
e do empacotamento Linux-only, a validação operacional de áudio e B6/B7
continuam pendentes. Nenhuma tag KG está autorizada por este relatório.

## B10–B13 — política do Percival (decisão posterior, 2026-10-06)

Percival é independente do HKUDS/nanobot e continuará em repositório
privado até as alterações planejadas e a validação; o operador criará
repositório público separado após revisão de histórico, segredos, dados,
licenças e proveniência. B10: PR upstream somente para correção genérica
separável com aprovação de divulgação. B11: revisão mensal e extraordinária
para correções urgentes; importação seletiva por branch/patch ou cherry-pick
com proveniência e testes, merge amplo só como exceção justificada e sem
rebase de `main` publicado. B12: CI do Percival é a fonte de verdade,
reaproveitando checks úteis; o `ci.yml` ainda contém Windows e o
empacotamento TUI herdado presume cinco plataformas — falta implementação
Linux-only antes de fechar gate. B13: o agente prepara notas, changelog e
limitações; operador aprova a versão final no SHA candidato antes de tag ou
publicação. Procedimentos: [AGENTS](../../AGENTS.md),
[governança](../percival-governance.md), [runbook](../../RUNBOOK-sync-upstream.md),
[notas candidatas](../kg-release-notes.md).

## B5 — decisão e implementação de áudio AK (2026-10-06)

**Decisão do operador:** usar o serviço de áudio padrão do nanobot, Groq
Whisper. D12 registra a exceção explícita a D11: apenas áudio AK usa o serviço
de STT configurado; caption de imagem e enrich continuam no runtime do turno.
`ak_audio_transcribe` e `ak_source_ingest` de áudio chamam
`nanobot.audio.transcription.transcribe_audio_file` com provider Groq, modelo
configurado ou padrão `whisper-large-v3`, idioma configurado ou `pt`, e enviam
arquivo multipart à API da Groq. Falha/credencial ausente não gera transcript
falso nem nota parcial. O limite padrão é 25 MB; aumentar requer verificar o
plano Groq. Não foi enviado áudio real à API neste ciclo.

Fonte oficial consultada em 2026-10-06:
[Groq Speech to Text](https://console.groq.com/docs/speech-to-text.md):
`POST /openai/v1/audio/transcriptions`, modelos `whisper-large-v3` e
`whisper-large-v3-turbo`, campo `language` ISO-639-1, limite 25 MB free /
100 MB dev e formatos flac/mp3/mp4/mpeg/mpga/m4a/ogg/wav/webm.
Para encerrar a validação operacional, executar amostra autorizada com
credencial real e verificar custo, latência e qualidade antes da release.
Validação local após a integração: suíte KG + provider STT 201 passed /
2 skipped; `basedpyright nanobot` 0; `ruff check .` e `git diff --check`
passaram após regularizar newline final em três arquivos F9 preexistentes.
A suíte completa executada antes da correção de uma asserção do teste novo
teve 9231 passed / 49 skipped / 1 failure (o mock recebeu URL em `kwargs`,
não `args`); os testes focados passaram após a correção. A suíte completa
não foi repetida após essa alteração localizada.

## B8/B9 — freeze (D5) e EOL (D10) dos servidores MCP legados (2026-10-06)

**Decisão do operador:** descontinuar `percival-collective-memory` e
`percival-acquire-knowledge`. Os repos ficam disponíveis apenas para
rollback; não há mais desenvolvimento, PRs nem novos deployments.

**Status GitHub:** freeze/tag aplicados; arquivamento ainda é ação do
operador via console web (decisão posterior abaixo). Não presumir que o
estado público ou a flag de archive já foram verificados.

**Data de corte e tag final:** `legacy-final` em cada repo, apontando para o
último commit antes do banner EOL.

- `percival-collective-memory`: tag `legacy-final` em `7e3fb54`
  (2026-08-14, `fix(batch-link): mensagens de erro apontavam o caminho
  errado`); commit de EOL `ec4e95f docs(eol): freeze legacy CM MCP
  server — see MIGRATION.md` empurrado em `main`.
- `percival-acquire-knowledge`: tag `legacy-final` em `8171fd5`
  (2026-08-14, `docs: README.md refletia 18 tools, servidor já expõe 20
  (A4/A5)`); commit de EOL `a979902 docs(eol): freeze legacy AK MCP
  server — see MIGRATION.md` empurrado em `main`.

**Quem escreve e commita:** o operador autoriza o agente a escrever
diretamente nos repos legados, então o commit e push ficam locais em
`~/Projects/percival-{collective-memory,acquire-knowledge}` e são enviados
via SSH ao remoto `git@github.com:bill-kopp-ai-dev/...`.

**Mudanças em cada repo:**

- `MIGRATION.md` (novo, raiz): status congelado, data de corte,
  repositório substituto, mapeamento das 20 CM + 14 AK tools para as
  `cm_*` / `ak_*` nativas (com D6/D11/D12 quando aplicável), migração de
  `config.json`, rollback via tag `legacy-final`, licença.
- Banner no `README.md` logo após o título, apontando para `MIGRATION.md`
  e o fork Percival.
- `.gitignore` ganhou `.positronic/` (regra global do operador; já valia
  para o fork Percival).
- AK: o `AGENTS.md` local (untracked, com tabela de verificação e
  convenções) teve seu conteúdo preservado em `MIGRATION.md` §6
  "Legacy verification" e o arquivo permanece local sem ser versionado.

**Auditoria não automatizada:** não há CI em execução; o congelamento
documental é binário, sem teste de equivalência. O congelamento **não
afirma paridade funcional** — o que prova paridade são os gates A1–A10
do fork Percival (`docs/kg-migration.md` e `docs/kg-endpoint-inventory.md`).

**Próxima ação humana:** arquivar os dois repos pela opção "Archive this
repository" no console web do GitHub; não é necessário `gh auth login`.

**Decisão do operador (2026-10-06, posterior ao freeze):** arquivar via
**console web** do GitHub (Settings → General → Danger Zone → Archive
this repository) em vez de `gh auth login` + `gh repo archive`. Sequência
prevista: `percival-collective-memory` primeiro, `percival-acquire-knowledge`
em seguida. `gh auth login` permanece pendente, mas não é necessário para
esta escolha.
