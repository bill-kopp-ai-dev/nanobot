# F5 implementation closure and C1 remote Actions verification

- **Prepared:** 2026-10-25, by the agent after bill requested closure of F5 and transfer of its remaining remote work.
- **Status:** active follow-up. The **local implementation scope of F5 is closed** in the master plan; **C1 is open** until exact-SHA Actions and artifact acceptance are proven.
- **Acceptance owner:** C1 remains owned by the [integrated pending-work plan](2026-10-23-integracao-pendencias-kg-e-mcp-docker-plan.md). This plan is its execution checklist, not a second acceptance gate.
- **Related plan:** B6 distribution remains in [B5/B6 CI-distribution closure](2026-10-24-b5-b6-ci-distribution-closure-plan.md); this plan does not authorize B6 publication/acquisition.
- **Authority:** bill authorized six MCP corrective commits/pushes to `main` in this campaign. That is not blanket authorization for later source pushes, repository settings changes, login, registry access, publication, promotion or deployment. Actions enablement and GitHub authentication remain operator-owned.

## 1. Outcome and boundary

F5 implementation now provides per-repository Docker build/conformance workflows for the six MCPs and the Percival core workflow. The follow-up MCP fixes were pushed to `main`; five MCPs have green remote workflows, while Deep Research's latest Python test job failed. The core SHA has no current Actions run. CI artifacts are listed for some green MCP runs, but manifests/SBOMs have not been downloaded or compared with their source/build inputs.

This plan closes only the **implementation phase** F5 in the 2026-10-09 master plan. It does not claim remote C1 acceptance. No job in this plan publishes/pushes an image or tag to a registry, and no release, pin change, manager action, canary, cutover or VPS deployment is included.

## 2. Candidate and Actions snapshot

Snapshot after the corrective MCP pushes of 2026-10-25. Before relying on any result, reread the current default-branch SHA and verify `headSha` exactly; a new commit invalidates prior-run acceptance for that repository.

| Repository | Candidate SHA | Latest observed Actions result | Required evidence still to collect |
|---|---|---|---|
| `nanobot` (gateway + broker) | `f3ad1590f36af054e1babaf97fdac82c5fb9a9ff` | No check-runs found for this SHA; the latest visible run is on an older SHA. Historical records say Actions was disabled for this fork. | Owner enables/runs required workflows; green core checks, `results.json`, gateway/broker manifests and CycloneDX SBOMs. |
| Notes MCP | `83980418b3239be5476f6d347ceb8dad32d90e8e` | CI run #10 success. | Download manifest/SBOM and compare source, lock/base digests, labels, platform and image identity. |
| AgentMail MCP | `68751b696b62b53fdcf893c3add9cf9e648e4391` | CI run #30 success, Python 3.11/3.12 and Docker. | Download manifest/SBOM and compare source, lock/base digests, labels, platform and image identity. |
| Weather MCP | `144dd44078bea4c7ba35111e15442cfc6bf14398` | CI run #29 success, Python matrix and Docker HTTP/stdio workflow. | Download manifest/SBOM and compare source, lock/base digests, labels, platform and image identity. |
| Khan Calendar MCP | `919b6ab9bb1b12d3ee48aa95c4d97f9463a738d0` | CI run #31 success, Python 3.11/3.12 and Docker. | Download manifest/SBOM and compare source, lock/base digests, labels, platform and image identity. |
| OSM MCP | `06484259a3bb5371c5c1551dcab0c23ccc166479` | Docker workflow run #22 success; run #21 also passed after explicit Python setup. | Download manifest/SBOM and compare source, lock/base digests, labels, platform and image identity. |
| Deep Research MCP | `defc9434487be4db7dbc13003db1709047297471` | CI run #15 failed in pytest; run #14 also failed in pytest. Local suite passes, but the failing remote test is not identified. | Obtain authenticated logs, reproduce the exact failing test/environment, fix only the demonstrated cause, push a new SHA when authorized, and rerun all required jobs. Then download manifest/SBOM. |

The detailed initial diagnosis, local verification and intermediate run history are in [F5 revalidation report](../reports/2026-10-25-f5-ci-conformance-revalidation.md). The local Engine was 29.9.2 linux/amd64; it is not the approved Engine 27.5.1 CI/target proof.

## 3. Work packages

### WP1 — Enable and authenticate remote verification

**Owner:** bill. **Status:** pending.

1. Enable/authorize GitHub Actions for `bill-kopp-ai-dev/nanobot` in the repository settings or otherwise provide an approved run for candidate SHA `f3ad1590…`.
2. Complete GitHub CLI authentication in the operator's terminal using the supported interactive login flow. Never paste the token/device credential into chat, a shell command, a workflow, a plan or a report.
3. Confirm authenticated, read-only access to Actions logs/artifacts for all seven repositories. Do not change the mise trust configuration as a workaround without separate approval.

**Exit evidence:** `gh auth status` succeeds for the expected account; the core workflow has a run whose `headSha` equals the candidate SHA; run and artifact APIs are readable. If any item is unavailable, stop and keep C1 open.

### WP2 — Diagnose the Deep Research failure

**Owner:** agent after WP1. **Status:** blocked on authenticated logs.

1. Download the failing run #15 logs from the exact current SHA, identify job/test, Python/uv versions, and the first failing assertion/traceback.
2. Reproduce the failure locally using the same locked dependencies, Python version, runtime patch and command. Keep credentials and provider calls synthetic/offline.
3. If the failure is a workflow/environment issue, fix that narrowly and verify the full affected checks. If it is an application/test failure, add a reachable regression test and run the canonical suite.
4. Any source change requires a new commit/SHA and a fresh Actions run for that SHA. Prior successful build/run artifacts do not transfer to a different SHA.

**Exit evidence:** root cause linked to a log step, local reproduction or reasoned non-reproduction; correction and local tests recorded; remote run green on the final SHA.

### WP3 — Verify all seven final runs

**Owner:** agent; operator owns core Actions availability. **Status:** pending WP1 and WP2.

For each repository, record the run URL/ID, `headSha`, workflow/job conclusions, target platform, and whether every required job completed successfully. A skipped, cancelled, absent or different-SHA run is not PASS. Core acceptance must cover the current CI's Docker build/runtime conformance and preserve `results.json` diagnostics.

**Exit evidence:** seven green exact-SHA runs, including the core. No workflow in this conformance stage may publish an image.

### WP4 — Download and compare evidence artifacts

**Owner:** agent after WP1. **Status:** blocked on authenticated artifact access.

Download artifacts for every accepted run. Verify archive integrity and retain the original artifacts unchanged. Compare each manifest against the exact source SHA, image ID, OCI labels, platform, lock hashes and pinned base digests; check CycloneDX SBOM identity corresponds to the built image. For the core, also verify runtime `results.json` and gateway/broker manifest/SBOM pairs. Redact secrets; do not treat local image IDs as OCI RepoDigests.

**Exit evidence:** per-repository table links the accepted run and artifact names/digests, records each comparison result and any missing field, and identifies the exact candidate SHA. Missing/mismatched artifacts keep C1 open.

### WP5 — Reconcile the durable handoff

**Owner:** agent; bill resolves service access if needed. **Status:** pending.

The global handoff note `20261025-193252-f5-conformance-ci-revalidation-local-fix-254a6f58-1d5` still reflects the pre-push state. An attempted supported `journal_update` returned `JournalNoteError`; a subsequent read confirmed the revision was unchanged. Retry only through the authorized Journal API, using a freshly read CAS revision and a signed update request. Do not edit journal files directly or append a duplicate handoff. If policy/service rejects the update again, record the failure and ask the owner to resolve access.

**Exit evidence:** the existing handoff reflects the six MCP push SHAs, current exact-SHA Actions state, unclosed core/Deep/artifact dependencies and the next action; no duplicate note.

## 4. Gate and completion

**C1 remains the sole acceptance gate** in the integrated plan. Close it only when:

- all seven required workflows are green at their exact final `headSha`;
- required manifest/SBOM artifacts (and core `results.json`) are downloaded, integrity checked and compared with their exact source/build inputs;
- Deep Research's failure is resolved and the final run is green;
- the core Actions run exists on the candidate SHA; and
- this plan, the master plan, integrated C1 row, and durable handoff agree on the verified state and residuals.

Closing the F5 implementation phase in the master plan does **not** close C1, approve B13, publish images, authorize image promotion or complete F6/VPS acceptance.

## 5. Stop conditions

- No authenticated access or Actions unavailable on the core: stop; operator enables/provides the approved access/run. No run is not PASS.
- Logs/artifacts inaccessible: stop at the relevant item; do not infer remote root cause or artifact contents from local builds.
- Any remote test/build failure: inspect the exact failure and fix only a demonstrated cause; never weaken or skip a required gate to obtain green.
- Any request to publish, push an image, promote, change pins/managers, alter real data or deploy: stop; it requires its own explicit authorization and plan.
