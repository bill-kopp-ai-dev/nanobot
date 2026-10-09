# MCP Docker UI/service refactor — local execution status

- Base: `ca9634ae` (`main`); implementation committed and pushed. The plan at `docs/plans/2026-10-08-mcp-docker-ui-service-refactor-plan.md` also reflects the implementation status.
- Scope implemented locally: operational status from observed Docker/MCP state; saved-versus-observed tools; contextual install/update-image flows; network `none`/`bridge` selection; typed environment validation/redaction; draft conflict and read-after-write feedback; grouped management; full/minimum/customized host file access.
- Contract: `mounts=null` means full, `mounts=[]` means no host binds, nonempty list means customized. Broker checks for unexpected binds in minimum mode; broker health advertises support, the gateway forwards `minimumMountsSupported`/`supportedNetworks` only from a ready broker, and a newer UI does not emit unsupported modes when support is unconfirmed. Existing clients ignore the additive fields; schema version remains 1. An old snapshot without `savedTools` cannot prove tools saved when the broker reported none.
- Domain: reject identical `(type, reference)` update before backup/journal, also reject it in broker before removal. Block `configure` and `update-image` on a stopped persistent server until a contract can preserve its stopped state. `configure` now requires an explicit `mounts` value to prevent silent privilege escalation when a client omits the field.

## Bug fixes reviewed before commit

- **B1 (security):** `configure` payloads that omit `mounts` previously fell back to `mounts=null` (Full host access) via the Pydantic default. The domain now returns `DomainError(400, "mounts is required for configure; pass null, [] or a list")` so an existing mount reduction cannot be silently widened by a stale or buggy client. `install` keeps the documented default (Full access is an explicit installer choice).
- **B2:** `hasDraft` is now reset on `snapshot.revision` change in `McpContainersPage` so a stale draft cannot silently lock navigation behind a misleading confirm dialog.
- **B3:** Indentation in `McpDockerManagement.tsx` (lines 188–216) normalized to six spaces.
- **B4:** `setDraftDirty(false)` and `setDraftConflict(false)` are now reset on global revision changes, matching the surrounding confirmation state.
- **B5:** `operationalStatus` now treats `starting`, `restarting`, and `updating` as intent-mismatch triggers when the Docker state is `stopped` or `container-missing`, so transient transitions are no longer classified as a successful running state.
- **B6:** The `mountMode`/`network` gating on the Save configuration button is split into named locals (`hostSupportsMinimum`, `currentlyMinimum`, `switchingToMinimumWithoutSupport`, `switchingToBridgeWithoutSupport`) so widening a minimum server without host support remains allowed while narrowing into minimum is still blocked.
- **B7:** The `verified` expression in `invoke` is now linear (`revisionOk` and `serverOk` locals) instead of a nested ternary.
- **B8:** New regression test ensures `update-image` with the same image identity is rejected (HTTP 409 "unchanged") right after `install`, preventing accidental no-op broker removals.
- **B9:** New test asserts `mount_policy.docker_args([])` returns no bind or cover arguments for the minimum-access path.

## Verification at this worktree

- `bun run test --reporter=dot` in `webui/`: **155 files, 2641 tests passed** (was 2638; +3 new UI tests). Focused `mcp-containers.test.tsx` now runs 19 tests, all green. `bun run lint`, `bunx tsc --noEmit -p tsconfig.build.json`, and `bun run build` all pass.
- `uv run --no-sync pytest tests/mcp_docker -q`: **65 passed** (was 62; +3 new tests: `test_configure_rejects_missing_mounts`, `test_update_image_with_same_identity_is_rejected_for_fresh_server`, `test_docker_args_empty_mounts_returns_no_args`). `uv run --no-sync basedpyright nanobot/mcp_docker`: 0 errors. `uv run --no-sync ruff check .`: All checks passed. The pre-existing test `test_secret_roundtrip_reference_and_rollback` was updated to include `mounts: ["/srv/data"]` so the new "mounts is required" guard correctly fires only on truly-missing payloads.
- After `uv sync --all-extras --dev` and `uv run --no-sync python -m scripts.install_channel_dependencies --all-channels`, `uv run --no-sync pytest -q -n 4`: **9298 passed, 49 skipped** (was 9295; +3 from the new tests). `uv run --no-sync basedpyright nanobot`: 0 errors.
- Disposable Docker smoke: re-ran `F2_GATEWAY_IMAGE=percival-f2-gateway:ui-test F2_BROKER_IMAGE=percival-mcp-broker:ui-test bash scripts/percival-f2-docker-smoke.sh` and observed the F5 message plus the broker Client/Server **27.5.1/29.7.2** line. The smoke continues to check that `mounts=[]` yields zero observed Docker bind mounts after configure, restart, update-image and restore. The script's disposable gateway, broker and both managed fixture containers were absent after cleanup; the four installed real servers were not mutated.

## Acceptance still open

- Browser WebUI + gateway + broker mutation smoke in a disposable fixture (including full/minimum/customized mount inspection, no host control paths, bridge/none, restart, update, restore and secrets). The disposable real gateway+broker smoke verifies domain operations and minimum-mode bind behavior, but runs from a CLI driver, not a browser, so it does not close this gate.
- Browser layout/accessibility inspection at narrow/wide viewport and keyboard focus; compatibility proof with independent older client/host fixtures per `.agent/review-guide.md` beyond the new UI's absent-capability fallback.
- Actions on a candidate SHA and VPS/deployment gates from the main MCP Docker execution plan. No real-server mutations or deployment performed here.

Next: build a disposable gateway+broker+image browser fixture and exercise the acceptance matrix, then run Actions on the candidate SHA. Do not classify this as release-ready on the basis of local tests.

