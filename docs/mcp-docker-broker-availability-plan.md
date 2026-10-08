# MCP Docker: broker availability and restart recovery

**Status (2026-10-08):** Work packages 1–4 implemented locally; deployment
cutover performed on the local host with Engine 29 override. Token preflight,
broker health, WebSocket HTTP, gateway managed-MCP connection log and observed
Docker/MCP state passed after initial start and gateway+broker recreation. A
fresh host reboot/browser workflow remains pending operator verification.
`docker.service` and `docker.socket` are both enabled for boot startup.
Focused MCP/agent tests, WebUI tests, lint/build, touched-file typecheck and
Compose model validation passed. A disposable gateway container running the
updated entrypoint preserved token owner/group/mode `1000:65532:640` after
its recursive state ownership fix. The full Python test run timed out with a
Matrix dependency (`nh3`) missing from this environment; the global typecheck
also needs optional channel dependencies. These are not deployment evidence.

**Incident (2026-10-08):** Four registered servers showed `unknown`/`unknown` and
`Docker MCP broker unavailable`. The browser was served by a host-launched
gateway; the gateway+broker Compose stack was absent. The persisted token was
owned by UID/GID 1000:1000 with mode 0640, while that gateway had no
`PERCIVAL_BROKER_TOKEN_GID` and expected 65532. Token validation fails before
any HTTP call. None of the four managed Docker containers exists in the current
daemon. The cause of their removal has not been established.

## Intended result and boundaries

One reviewed gateway+sidecar deployment is the operating unit for MCP Docker.
The browser identifies failure at the common broker boundary, while saved
intent is never mistaken for a live container or MCP connection. When the
broker returns, active managed servers may be reconciled through the existing
typed broker operation; pending transitions and deliberately stopped or inactive
servers remain protected. Health/doctor must never start a container. The
existing `list()` can recover a previously journaled transition; that
pre-existing recovery contract is not changed by this work.
No Docker socket/CLI is added to the gateway. No real deployment cutover,
container recreation, state migration, or release is authorized by this plan.

## Implementation work packages

1. **Typed diagnostics.** Classify token absence, token permissions, transport,
   server error and invalid response in the broker client without exposing
   credentials or raw Docker stderr. Add an authenticated, read-only broker
   health action that verifies its Docker/host policy readiness. Report one
   broker readiness result in the list response, including the empty-registry
   case; still distinguish individual observation errors. Preserve redaction
   and gateway ownership of config.
2. **Operator preflight and visibility.** Add a read-only `mcp-docker doctor`
   CLI command using the same token and health path as the gateway. Expose a
   top-level WebUI status with actionable, bounded error text; preserve per
   server `unknown` for unverified state. A health check must not reconcile,
   write journals, or create containers.
3. **Reconnect.** Ensure managed server definitions omitted on startup due to
   invalid/missing token can be loaded when the token becomes valid, without
   making the list endpoint mutating. The existing managed reconcile path must
   continue to honor `active`, `stopped-persistent`, and unresolved journals.
   No Docker writes in the new health/preflight path; a list can still recover
   an already-journaled transition as specified in the F5 runbook.
4. **Lifecycle contract.** Add sidecar health check in Compose; preserve the
   dedicated token group after the gateway entrypoint's state ownership fix
   (which previously reset it to the gateway's primary GID on restart). Document the
   canonical gateway+broker startup/cutover, consistent numeric token group,
   sidecar recreation after gateway replacement, enabled host `docker.service`
   for boot-start, and reboot/recovery evidence.
   Keep the Engine 29 override disposable and do not claim VPS Engine 27 gate
   from a local test.

## Acceptance evidence

- In a fixture, missing broker reports transport failure; GID mismatch reports
  token-permissions failure even with broker absent; healthy broker reports
  readiness. No token, environment secret, or host path leaks to HTTP or CLI.
- Empty and populated registry show broker readiness; doctor/health cause no
  broker mutations. Failed observations do not label tools as live.
- An initial token failure followed by restored token and broker triggers a
  managed reload/reconcile on a subsequent runtime readiness check; unchanged
  generic MCP servers retain their previous behavior.
- Compose config renders a gateway without Docker socket and a broker with it;
  health check checks the real broker/daemon, not merely a gateway HTTP port.
- The host daemon is enabled and starts at boot; gateway and sidecar containers
  use restart policies and recover MCP servers after boot.
- After the container gateway starts/restarts, the shared token remains readable
  by the configured broker group despite the state-tree ownership fix.
- Focused tests, `ruff check .`, `basedpyright nanobot`, applicable WebUI tests,
  and a reviewed diff pass locally. Browser+gateway+broker, fresh boot,
  gateway/sidecar recreation and real four-server recovery remain deployment
  gates requiring an operator-approved maintenance window.

## Order, ownership and remaining risk

Implement and test work packages 1–3 in code, then update Compose/runbook for
package 4. Operator owns final reboot/browser verification: inventory host/Engine/token GIDs,
stop the host gateway, start the reviewed Compose pair using the same persisted
state, inspect pending transitions, reconcile one fixture at a time and verify
observations/tools, then rehearse reboot and rollback. Do not clear journals by
hand or assume missing images and broker `reference` variables will recover.
The incident's historical container removal remains unresolved until the
deployment evidence is collected.

**Local runtime verification:** the Compose gateway and broker currently run
with `PERCIVAL_DISPOSABLE_ENGINE29=1`; all four managed MCP observations report
Docker `running`, MCP `connected`, and tool counts 24/9/37/5. This does not close
the VPS Engine 27.x gate. The deep-research and OSM images currently report
Docker health `unhealthy` because their image health checks expect an HTTP
`/health` endpoint and `pgrep`, respectively; the actual MCP `tools/list` calls
work. Their image-level health checks are a separate issue and were not
modified here. A host reboot was not performed while unrelated OpenCode MCP
stdio containers/sessions were active.
