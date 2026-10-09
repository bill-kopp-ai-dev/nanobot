# F5 — Conformance tests and per-repository CI

**Status:** implementation and local validation completed; F5 gate remains open.
**Date:** 2026-10-09. **Platform:** linux/amd64. No image publication or CI
workflow execution on GitHub was performed.

## Scope delivered

- Percival root CI extends its Docker job with Compose rendering, an isolated
  gateway/WebUI/API fixture, effective health checks, API missing-key/auth
  checks, loopback-only host port inspection, and build evidence for gateway
  and broker. The existing broker fixture still asserts Docker Engine 27.5.1.
- Added Docker build + stdio conformance jobs for Notes and Deep Research;
  expanded the existing AgentMail, Weather, Khan Calendar and OSM jobs.
- All six MCP Docker jobs target only `linux/amd64`, build locally on the
  checked-out workflow SHA, run stdio smoke without a TTY/host port or external
  network, inspect image identity/runtime user, render Compose, and upload a
  source/image manifest plus CycloneDX SBOM. No job publishes an image.
- Common stdio probes issue MCP `initialize`, `notifications/initialized`,
  and `tools/list`; require JSON-only stdout and non-empty expected tool sets;
  assert effective runtime UID plus the rendered Compose stdio contract, and
  check selected fake credentials for output leakage. AgentMail's
  startup inbox health call is routed to a mock service on an internal-only
  Docker network, so the protocol smoke uses no AgentMail API.
- Manifest writers record source SHA, image ID/RepoDigests, platform, version
  and revision labels, dependency-lock SHA-256s, and digest-pinned Dockerfile
  bases; they fail on SHA mismatch, placeholder version, wrong architecture,
  or unpinned base.
- Updated the OSM CI architecture regression test to match the approved
  linux/amd64-only F0 scope.
- Percival Compose binds gateway health and WebSocket listeners on the
  container interface for port forwarding while keeping host publications
  loopback-only. The WebSocket listener requires a persistent, read-only
  `PERCIVAL_DOCKER_GATEWAY_TOKEN_ISSUE_SECRET_FILE`; the secret value is mounted
  as a file rather than placed in container environment metadata. The runtime
  rejects non-regular or group/world-readable files; deployment and browser-login
  instructions identify the file path. Missing/invalid bind settings fail closed.
- The post-implementation review tightened the fixture to use a unique `mktemp`
  path/project, made stdio probes perform the request/response handshake in
  order (Khan passed five consecutive repetitions after the change), redacted
  fake secret values from error diagnostics, and made manifest lock inputs
  explicit in CI.
- WebUI lint/build and the focused auth-help tests passed. Two local full
  `bun run test:coverage` attempts each hit a timeout in an unrelated existing
  test (`settings-channels` once, `code-block` once); targeted `app-layout` and
  `code-block` tests passed on retry. The full WebUI suite therefore remains a
  remote-CI verification item.

## Local verification

- Percival: full `pytest` passed, **9,312 passed / 49 skipped / 6 warnings**
  (five Pydantic serialization warnings and one aiohttp deprecation warning);
  `basedpyright nanobot` reported **0 errors, 0 warnings, 0 notes**; CI Ruff
  command passed.
  Focused gateway command tests: **26 passed**.
- MCP canonical tests: Notes **45 passed**; AgentMail **230 passed / 1 skipped**
  (92.47% coverage); Weather **147 passed**; Khan **220 passed** (87.47%
  coverage); OSM **75 passed**; Deep Research **414 passed / 3 skipped**.
- Stdio conformance succeeded against locally available F4 candidate images:
  Notes **12 tools**, AgentMail **24**, Weather **9**, Khan **12**, OSM **37**,
  Deep Research **5**. AgentMail exercised its internal HTTP mock.
- HTTP profiles: Weather returned `/healthz` 200, unauthenticated MCP 401,
  loopback host publication and Docker `healthy`; Deep Research returned the
  expected health response (200/503 listener semantics), loopback publication
  and Docker `healthy` with dummy credentials and no external API operation.
- OSM's existing Docker smoke passed missing-environment rejection, MCP
  handshake/tool registration, authenticated HTTP initialize, loopback bind,
  health probe and single-tini shutdown.
- Percival Compose fixture passed gateway health, WebUI HTTP, API health,
  unauthenticated `/v1/models` 401, authenticated `/v1/models` 200, API startup
  refusal without an API key, healthy effective Docker probes, and loopback
  port-binding inspection. Broker overlay and all seven workflow YAML files
  parsed; Compose render checks passed when their documented test environment
  was supplied.

## Limitations and gate state

- Reviewed F5 changes were committed and pushed to `main`: Percival `a551c2f7`,
  Notes `efae9b6`, AgentMail `3dc76d1`, Weather `67dc188`, Khan `f2917a0`, OSM
  `cd4df41`, and Deep Research `d213fb3`. Existing untracked operator files
  (`.positronic/`, `AGENTS.md`) were preserved.
- Remote GitHub Actions status could not be queried because `gh` has no active
  authentication in this session. Remote runs and manifest/SBOM artifacts are
  therefore not observed. F5 cannot be declared closed until each repository's
  build + conformance CI passes at its exact pushed SHA.
- F3 remains blocked by untriaged Critical/High image findings and has no
  approved waivers. F4 remains open for persistence/restore and other remaining
  acceptance evidence. These prerequisite gates remain separate; this F5 work
  does not close them or authorize cutover.

## Next action

Review the local diff and authorize the required commit/PR/push path. After the
candidate SHA is available to GitHub Actions, inspect every per-repository CI
run and retain its manifest/SBOM artifacts; resolve failures before closing F5.
