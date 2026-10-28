# Percival Agent Runtime Contract

- **Contract:** runtime 1; **product metadata:** `0.1.0`; Linux `amd64` only in this
  conformance run. Python distribution/import/CLI remain `nanobot-ai` / `nanobot` /
  `nanobot`. This is a local development contract, not a published release.
- **Authority:** [I1 ADR](Decisions/2026-10-23-open-iac-contracts.md),
  [handoff](iac-p0-contract-handoff.md), and executable product interfaces below.
- **Evidence:** [I2 execution report](reports/2026-10-23-i2-runtime-contract-conformance.md).
  Changes to persisted config or wire contracts require a compatibility review.

## 1. Runtime modes and lifecycle ownership

Compose gateway + broker is the canonical Docker-MCP topology. The main image is
multimode; its default command is the finite `status`, so it has no image-wide HTTP
healthcheck. `EXPOSE` is documentation, not a port publication or readiness check.

| Mode | Image / command after entrypoint | State and writers | Effective identity / process | Health, network and exit |
| --- | --- | --- | --- | --- |
| Gateway | main / `gateway` (foreground by default; `--foreground` is explicit) | Config, sessions, workspace, cron, auth/session state, WebUI, KG and MCP manager; sole agent writer for this instance | Compose: UID/GID `1000:1000` by default; one Docker init, one gateway child | `GET :18790/health`: 200 when required WebSocket runs, otherwise 503; WebUI/WS `:8765`; idle SIGTERM observed exit 0 |
| API | main / `serve --host 0.0.0.0 -w /home/nanobot/.nanobot/api-workspace` | Same instance config/auth root; separate workspace does **not** separate shared sessions/config/MCP state; run instead of gateway on this state | Same Compose user and init; opt-in `api` profile | `GET :8900/health` for process, authenticated `GET /v1/models` for API access; missing `api.api_key` refuses non-loopback bind, exit 1; idle SIGTERM exit 0 |
| Inspection/setup CLI | main / `status`, `onboard --refresh`, `auth init`, `auth change`, `auth status`, `mcp-docker doctor` | Same bind/config as gateway. `status`/auth status inspect; onboard and auth commands write. Setup/refresh/rotation rehearsed with gateway stopped | One-shot; Compose user defaults `1000:1000`; no second gateway or service installation | No HTTP probe; use exit code. Inspection/status: 0 even if no password; init refuses an existing verifier, exit 1. Password prompts read terminal; no password flag |
| Broker | broker / `python3 -m nanobot.mcp_docker.broker [--port 18081]` | In-memory executor registry; owns Docker MCP container lifecycle, not gateway config. Hydrates from the gateway after loss of process state | UID/GID `65532:65532`, supplementary socket/token GIDs, one init; root filesystem read-only; writable private tmpfs | Loopback-only `:18081` in gateway namespace; authenticated POST health. SIGTERM exit 143, SIGKILL exit 137: no application drain; MCP containers are separately owned resources |

Gateway, API and broker continue with stdin closed; EOF is not their shutdown API.
CLI commands terminate when complete; missing interactive password input is not an
automatic setup. A stdio MCP fixture terminates with exit 0 on EOF. During a broker
exchange, unexpected MCP EOF/timeout is an error, not a successful tool result.

The product gateway owns execution and policy, WebUI/TUI own client presentation,
and only the broker has Docker socket/CLI access. Initial support is **one Percival
instance per Docker daemon**, because MCP names are `percival-mcp-<server_id>`.
Compose project names do not namespace those MCP names. Test daemons are separate.

### Single writer

`nanobot-api` is an opt-in profile so plain `compose up` does not start it beside
the gateway. Explicit service selection can still start both: orchestration must
prevent that on shared state. Do not use `gateway --background`, `install-service`
or another gateway beside Compose on the same state. API-only deployments can
reuse the image and CLI but must quiesce the gateway first. I4's deployment preflight
must enforce this topology; there is no new cross-process lock for every CLI/API writer.

## 2. Config, filesystem and credentials

Container `HOME=/home/nanobot`; default config is
`/home/nanobot/.nanobot/config.json`. Runtime data follows the **config parent**;
the default workspace is `$HOME/.nanobot/workspace`, or the explicit configured
workspace / `--workspace`. An arbitrary `--config` does not move the workspace.

| Path / surface | Reader/writer and retention contract |
| --- | --- |
| `config.json`, provider/API credentials | Gateway/config admin; validated JSON, atomically saved mode 0600 on every replace (including legacy permissive files); backup privately before migration |
| `auth/verifier.json` and auth/session files | Instance credential controller; `auth init/change/status` use the selected config parent; plaintext password is not persisted |
| `sessions/`, `webui/`, `media/`, `logs/`, gateway runtime metadata | Instance data; preserve with config; clients do not become a second agent writer |
| `workspace/` (memory, KG and other work), cron/trigger data | Agent/runtime-owned; explicit external workspace paths require their own persistence and backup |
| `mcp-docker/audit.jsonl`, `transitions/`, `backups/` | Gateway manager owns audit/recovery/backups and canonical `tools.mcpDocker`; backup directories are 0700 and manifests 0600; backup may contain secrets and is not a public lock |
| `mcp-docker/broker-token` | Gateway reads as owner; broker reads through a dedicated group/file mount; owner gateway UID, mode 0640 with approved token GID (or private owner-readable file in gateway-only contexts) |
| `/app/nanobot`, `/app/scripts`, channel locks | Image-supplied readable code/data, not mutable runtime state |
| `/app/.venv` | Readable by supported non-root users; writable by built-in UID 1000, **not** arbitrary UID 1001. F3 candidates disable application-driven package installation at runtime; bake enabled channels/extras into the image |
| Broker `/tmp` | Ephemeral tmpfs UID/GID 65532, mode 0700, `noexec,nosuid,nodev`; lost on recreation |

The base Compose binds `~/.nanobot`. With `docker-compose.mcp-broker.yml`, **all
three main-image services** bind `PERCIVAL_STATE_HOST_PATH` at the internal state
path. The broker verifies that exactly one gateway state bind matches its host
inventory. Its token must be beneath that verified state. I2 does not split state
or rename `~/.nanobot` to `.percival` / `/srv/pblabs`; I4 owns that host layout.

The broker's mandatory deployment inputs are the absolute state/token host paths,
real gateway container name, socket GID and token GID, read-only host-root inventory
and host mount table. Its local socket is writable through the Docker API; `:ro`
would not make that API read-only. Gateway and ordinary MCPs never mount the socket.
Broad host R/W still has the indirect risks accepted in B23–B25, not total isolation.

### Bootstrap and exposure order

1. Prepare an owned private **fixture or approved instance** state directory and the
   broker's dedicated token/group. Include the same `-p`, `-f` files and environment
   on every Compose command; do not accidentally run setup on the base-only bind.
2. With writers stopped, run `nanobot-cli onboard --refresh`; configure provider/model
   through the documented JSON configuration or wizard. Refresh validates and preserves
   existing values; it is not a byte-identical no-op and can add defaults.
3. Run `nanobot-cli auth init` interactively, then `auth status`. Init on an existing
   verifier refuses to overwrite it. Rotation uses `auth change` and the current password.
4. If API mode is selected, configure its **distinct** `api.api_key`. A human password
   is not an API bearer. Do not enable API merely to probe a gateway deployment.
5. Start the selected runtime and broker; check all relevant probes before allowing
   non-loopback **host** exposure. Compose publishes to host loopback by default.

Without a verifier, the gateway can serve its unauthenticated sign-in page and even
report process readiness; protected `/webui/bootstrap` and WS access reject unauthenticated
requests (401). It does **not** refuse every wildcard listener. Missing provider setup
may intentionally leave WebUI available for setup. Neither state proves LLM readiness.
The API refuses a non-loopback bind without its API key. Tests use fake provider keys
and a dead loopback provider endpoint; no model request or paid service is needed.

## 3. UID/GID, init, capabilities and signals

- Compose defaults `NANOBOT_UID/GID=1000`; an explicitly owned UID/GID `1001:1001`
  was checked for CLI, Compose gateway/auth/health/SIGTERM and offline imports. Every parent must be traversable and the
  bind must be writable by the chosen UID. Do not use `chmod 777` as remediation.
- The image normalizes shipped code/dependency readability and `/home/nanobot`
  traversal; it does not change permissions on an existing non-root host bind.
  Wrong ownership fails with exit 1 and an actionable error.
- The main Dockerfile starts root for plain Docker/Render compatibility. Entrypoint
  repairs state ownership, preserves the configured broker token group, verifies
  `setpriv`, then `exec`s the CLI as UID/GID 1000. Drop failure exits 1; no root fallback.
  Restricted root cannot always traverse an existing UID-1000 private tree; canonical
  Compose avoids this path and requires correct initial ownership.
- `init: true` belongs to Compose. Images do not embed a second init; long-running
  plain Docker/root-drop tests use `--init`. Root init needs `CAP_KILL` to signal the
  child after UID drop, in addition to entrypoint `CHOWN,SETUID,SETGID` bootstrap caps.
  Without KILL the constrained root init was observed to fail forwarding SIGTERM.
- Compose drops ALL and adds those four bootstrap caps, sets `no-new-privileges`;
  broker drops ALL. Gateway/API/broker children were checked in `/proc`: effective,
  permitted, inheritable and ambient capabilities zero; `NoNewPrivs=1`.
  A root init's bootstrap caps are not agent caps. Bwrap is a separate opt-in profile.
- Both images declare `STOPSIGNAL SIGTERM`. Gateway/API Compose grace is 60 seconds;
  broker uses Docker's default stop grace. Idle stop samples were approximately
  1–3 seconds, exit 0 for gateway/API, 143 for broker. Docker's hard grace is not a
  guarantee of full application drain under active work; test in-flight work in I8.
- Broker crash loses its in-memory registry. Existing **owned** persistent MCPs are
  not automatically deleted; gateway hydrate validates their state and reconnects.
  Request-local `docker attach` processes are killed/waited after exchanges. Recreate
  the **gateway and broker together** when gateway identity changes, to rejoin its
  new network namespace; `restart gateway` is not the same as pair recreation.

## 4. Probes and readiness composition

| Probe | What it proves | What it does not prove |
| --- | --- | --- |
| Gateway `GET http://127.0.0.1:18790/health` | Process + required WebSocket running; 503 if degraded | Login, provider credentials, broker, tool discovery/call, KG readiness |
| API `GET http://127.0.0.1:8900/health` then bearer `GET /v1/models` | Process + configured API auth path; anonymous protected request 401 | A successful completion or paid provider access |
| Sidecar `python3 -m nanobot.mcp_docker.probe` | Reads mounted private token; authenticates `POST /v1/health`, requires `ready: true`; broker checks Engine, state and mount policy | Per-server MCP handshake/tools; an open TCP port alone is insufficient |
| Gateway `nanobot mcp-docker doctor [--config ...]` | Gateway-side token ownership/group/mode, real loopback transport and broker host readiness | Manager mutation or a particular app/tool |
| MCP initialize → initialized → tools/list → safe tools/call | Tested per-server protocol and actual reply through manager/provider/broker | Universal MCP transport, publication or permissions not enforced by the executor |

Deployment readiness composes these checks **externally**, without making gateway
health depend on broker health or broker startup depend on a healthy gateway. The
broker depends only on gateway existence/network namespace. Gateway retries MCP
startup misses every 30 seconds and before a turn; I2 also tested explicit provider
reconnection after delay/crash. Process `healthy` does not mean all tools are ready.

## 5. Compatibility matrix (runtime contract 1)

Compatibility is tied to wire/schema support and reviewed revisions, not SemVer
ordering. Baseline means private source `eb4e3555e76e35f52171c61c965d55aa5450dcda`
with inherited metadata `0.3.5`; it is **not** a claim about all upstream 0.3.5 builds.
Current means that baseline plus the I2 working-tree changes in the report.

| Producer / consumer | Supported boundary and evidence |
| --- | --- |
| Current gateway + current broker | Config schema 1; typed `/v1/*`, local image ID/locally present RepoDigest; real initialize/list/call + restart/hydrate in Engine 27.5.1 |
| Current gateway + baseline broker | Real baseline image built from archived source; same config/DTOs and MCP call path pass. This is **wire** compatibility; old image lacks the new probe module and needs its matching older probe/bundle, not the current healthcheck blindly applied |
| Initial v1 caller + current broker | Independent frozen HTTP request fixture accepted by real broker; legacy operations/DTOs unchanged. `test_client_contract.py` separately checks initial WebUI protocol-1 requirements against the current producer |
| Current gateway + older minimal health declaration | Independent test returns only `ready: true`; minimum mounts remain unconfirmed/false and networks fall back to `none`; absent fields grant no features |
| Client/host WebUI | Protocol **1**, required `webui.core.v1`; initial/current, missing/malformed/future declarations tested in `tests/webui/test_client_contract.py`. Version `0.1.0` does not force a wire downgrade from baseline `0.3.5` |
| Persisted config | `tools.mcpDocker.schemaVersion=1`, strict extra-field validation. Schema 2/repository/catalog metadata are not enabled; unsupported schema rejected. I6/I7 own explicit migration and downgrade snapshots |
| Engine/platform | Actual broker Docker CLI 29.9.0 + rootful Server 27.5.1, Linux/amd64. Code also accepts Client 27.x and Server 27.x; those ranges are not proof of every patch. Unsupported Server decision tested with injected 28.0.0; no Engine29 override used in the positive run |

Broker HTTP client timeout is 30 seconds. Docker commands default to 35 seconds;
stdio exchange waits up to 18 seconds per handshake/response read and waits up to
5 seconds for attach cleanup. Slow/partial-line/sessionful MCP behavior beyond this
tested boundary is not homologated. I6 must address long acquisitions explicitly.

### Transport limits and channel inventory

The broker HTTP surface is a small authenticated JSON bridge, not a generic MCP
server transport implementation: `/mcp/<server_id>` accepts `initialize`,
`notifications/initialized`, `tools/list`, `tools/call`. Each exchange attaches to
container stdio and performs an initialize handshake. No production promise for
notifications/streaming, cancellation, resources/prompts, pagination, arbitrary HTTP
MCP containers or multi-session servers follows from it. I6 validates selected apps.
Spawn remains `--pull=never`; acquisition/catalog API are not implemented by I2.

The default image preinstalls WhatsApp's `neonize` and `segno`; built-in WebSocket
uses core dependencies. `NANOBOT_CHANNELS` selects the comma-separated build-time
channel set (include `whatsapp` explicitly when adding others). The image build
validates the channel lock manifest, installs the union with `--require-hashes
--no-deps`, and runs `uv pip check`. Missing or conflicting pins fail the build;
satisfied version ranges do not bypass exact channel pins.

**F3 extension (2026-10-24):** Docker candidates set
`NANOBOT_RUNTIME_PACKAGE_INSTALL=0`. Startup reports a missing channel dependency
without launching an installer; WebUI install/enable requiring new packages returns
409 with rebuild guidance, before changing configuration. Preinstalled channels
remain enableable. Use `NANOBOT_CHANNELS` / `NANOBOT_EXTRAS` and deploy a new reviewed
image for additional dependencies. Native Python retains optional installation
(variable absent defaults to `1`). Explicitly overriding it to `1` in Docker opts
back into mutable development behavior and invalidates the fixed dependency-set
claim. This is application policy, not a filesystem/shell isolation boundary;
UID 1000 still owns the venv. Alternate UID/offline operation requires all enabled
dependencies preinstalled. I2's recorded startup-install behavior is historical
evidence for the earlier candidate, not the default of F3 candidates.

## 6. Conformance and downstream handoff

Build the two local images using the version read from `pyproject.toml`, preserve their
identity and identify a dirty worktree as such. Then run from this repository:

```bash
python3 scripts/percival-i2-runtime-smoke.py \
  --gateway-image <local-gateway-reference> \
  --broker-image <local-broker-reference> \
  --scratch-parent <existing-private-evidence-parent>
```

`--old-broker-image` optionally adds independently built baseline replay. The rehearsal
creates only a unique disposable dind container on the outer daemon, with its Engine
API bound to an ephemeral host-loopback port; it removes that daemon and its anonymous
volumes in cleanup. Product containers, socket access, host inventory, fixtures and
failure injection are inside it. It retains fixture evidence under the supplied
scratch parent, never live state. Requires Docker/Compose supporting `!reset` overrides
(the observed host version was v5.6.0), not a tested
minimum range. This command runs a privileged **test daemon**, not a deployment recipe.

`scripts/percival-f5-compose-smoke.sh` remains a compatibility wrapper: it can build
local images or accept `PERCIVAL_GATEWAY_SMOKE_IMAGE` / `PERCIVAL_BROKER_SMOKE_IMAGE`,
then invokes the isolated rehearsal. CI uses prebuilt images directly and uploads
`results.json`. Local checks do not stand in for a remote Actions run.

Render's `RENDER=true` entrypoint was exercised locally with fresh and existing state;
no Render service was deployed, and `render.yaml` is not certified by this test.
Host `install-service` remains a separate Linux compatibility/development path, never
a second writer on Compose state. ARM64, public registry artifacts, I3 distribution,
I4 host bootstrap, I6 app homologation, I8 loaded recovery and VPS acceptance retain
their own evidence and owners.
