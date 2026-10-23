# Working on Percival

Percival is an independent project derived from HKUDS/nanobot. Development
currently takes place in a private repository; a separate public Percival
repository is planned after the agreed features and gates are complete. The
`nanobot-ai` metadata is aligned locally to 0.1.0 by I2 (committed at
`0e7ff072`); neither metadata nor
upstream documentation constitutes a Percival release. The intended first version is 0.1.0; its Python
package name remains undecided. The proposed open distribution uses Docker/OCI
as described below. Read the [project governance
decision](docs/percival-governance.md) before sync, contribution, CI or
publication work.

I1's [open IaC decision](docs/Decisions/2026-10-23-open-iac-contracts.md) fixes the
current GitHub owner as `bill-kopp-ai-dev`, future owner as `p-bean-labs`, and Docker
Hub namespace as `pbeanlabs` (operator-confirmed; publication access not yet verified).
The private development remote stays `bill-kopp-ai-dev/nanobot`; the separately reviewed
public source repository is named `percival`. Account migration and public disclosure
are separate actions. Read the [contract handoff](docs/iac-p0-contract-handoff.md) for
owners, schemas, source snapshots and downstream implementation gates.

On 2026-10-23 the operator deferred I3, so no implementation work package is open.
Before the first public publication (I3.4), migrate the repository to `p-bean-labs`:
the `org.opencontainers.image.source` label is baked into the published image digest,
and the plan forbids repointing an already published SemVer tag at different bytes.
Docker Hub push credentials belong to the protected release environment; anonymous
pull needs no local login.

The Python gateway owns agent execution, sessions, tools, memory, and security policy. WebUI and TUI share that runtime; keep execution and policy out of the clients.

## Task-specific guidance

| When working on | Read |
| --- | --- |
| Core boundaries, extensions, or internal types | [`.agent/design.md`](.agent/design.md) |
| Refactoring, fallbacks, or test selection | [`.agent/simplify.md`](.agent/simplify.md) |
| Path permissions, HTTP/MCP, or shell isolation | [`.agent/security.md`](.agent/security.md) |
| Dependency setup, WebUI transport, config, Windows, prompts, or persistence | [`.agent/gotchas.md`](.agent/gotchas.md) |
| Reusing verification evidence | [`.agent/workflow.md`](.agent/workflow.md) |
| WebUI/host compatibility | [`.agent/review-guide.md`](.agent/review-guide.md) |
| Upstream intake or contribution | [`docs/percival-governance.md`](docs/percival-governance.md), [`RUNBOOK-sync-upstream.md`](RUNBOOK-sync-upstream.md) |
| Percival release or publication | [`docs/percival-governance.md`](docs/percival-governance.md), [`docs/kg-release-notes.md`](docs/kg-release-notes.md), [`docs/releasing.md`](docs/releasing.md) |
| Docker/IaC architecture, distribution, or deployment contracts | [I1 ADR](docs/Decisions/2026-10-23-open-iac-contracts.md), [contract handoff](docs/iac-p0-contract-handoff.md), [IaC integration plan (I1–I9)](docs/plans/2026-10-23-iac-alignment-execution-plan.md), [Docker standardization phases](docs/plans/2026-10-09-docker-standardization-refactor-plan.md) |
| Core runtime modes, UID/init/probes or gateway↔broker compatibility | [Runtime contract 1](docs/agent-runtime-contract.md), [I2 local conformance](docs/reports/2026-10-23-i2-runtime-contract-conformance.md) |
| Docker runtime, provenance, MCP/browser or VPS acceptance | [Docker closure (D1–D12)](docs/plans/2026-10-23-fechamento-padronizacao-docker-f4-f5-f7-plan.md), [integrated backlog (A/B/C)](docs/plans/2026-10-23-integracao-pendencias-kg-e-mcp-docker-plan.md) |
| Instance authentication or persistent credentials | [Single-password acceptance](docs/plans/2026-10-11-single-password-acceptance-closure-plan.md) |

## Docker-first IaC boundaries

- Treat the [IaC integration plan](docs/plans/2026-10-23-iac-alignment-execution-plan.md)
  as the map of target contracts, source references and remaining implementation.
  I1's ADR/handoff decide P0 conflicts; separate approved direction, target interfaces
  and verified implementation. Examples are not real endpoints, namespaces, schemas
  or digests. Reports are evidence, not ADRs.
- This repository owns Percival code, production Dockerfiles/entrypoints, runtime
  contracts, tests and image CI. A separate IaC workspace owns OpenTofu, host bootstrap,
  deployment Compose, schemas and deploy/recovery tooling; the MCP index and individual
  MCPs have their own repositories. Share external contracts, not copies of product
  code or assumptions that Percival and Positronic have identical paths/CLIs.
- Target distribution: GitHub holds source/IaC/curation; protected GitHub Actions
  publishes approved releases once the I3/I5 pipelines are implemented and validated.
  Docker Hub is the target primary registry for official open images:
  `docker.io/pbeanlabs/percival-gateway` and `docker.io/pbeanlabs/percival-mcp-broker`.
  Weather and OSM are the first selected official MCPs; I3/I5 still must verify account
  permissions, publication and actual digests. Curated third parties use their
  verified upstream OCI registry, without mandatory mirroring. The GitHub MCP index
  is separate from Docker MCP Catalog; Catalog and GitHub Pages are optional.
- OpenTofu provisions infrastructure; idempotent cloud-init/bootstrap prepares the host;
  Compose owns the core, including the broker sidecar. The gateway's native MCP Manager
  owns its MCP containers through that broker. One lifecycle owner per container;
  Compose/WUD must not recreate native-managed MCPs. External management is explicit;
  WUD, if validated, is core-only. The core updater is external to the agent.
- Reuse the existing Python broker and manager. Only the broker receives Docker socket/CLI;
  gateway/LLM and ordinary MCPs do not. Preserve typed authorization, CAS, journal,
  backups and mount protections. No generic Docker execution tool or manifest-granted
  privileges. Socket separation does not prove total isolation: retain B23–B25's
  indirect-risk limits and target-specific acceptance.
- Current MCP execution accepts local IDs or locally present RepoDigests and uses
  `--pull=never`. I1 selects restricted broker acquisition; I6 implements and verifies
  it before spawn. Do not enable arbitrary pulls, reserved `repository` sources or
  catalog trust implicitly.
  Preserve current clients/pins/policies until a compatible change is approved.
- Local builds/worktree candidates and `:dev` are development artifacts. Production
  consumes approved version tags plus real OCI digests, not builds from a VPS checkout.
  Image IDs are not manifest digests. Image CI must distinguish PR conformance without
  push from approved publication, recording source/version/platform/SBOM/scan and a
  clean anonymous pull/smoke. I1 chooses `pyproject.toml` as product version authority;
   I2 aligned inherited metadata/locks/defaults with Percival 0.1.0 locally; a release
   candidate still needs its exact clean SHA and I3 evidence.
- I1 limits initial P0 support to one Percival instance per Docker daemon. New catalog
  installs require explicit local consent; missing mounts never inherit Full. Existing
  configured servers retain their settings. Unsupported mandatory isolation is rejected,
  not claimed as enforced. Render/install-service stay separate compatibility paths;
  never run a second gateway writer on the Compose instance's state.
- I4/C2 map `~/.nanobot`, the historical `.percival` proposal and host layout
  `/srv/pblabs/`; preserve supported internal paths until explicit migration. Never
  rename/split state automatically or copy live config/fixture paths into templates.
  Validate effective UID/GID, secret files, init/signals and probes for each runtime
  mode; do not invent HTTP healthchecks for CLI or stdio. Server 27.x remains the
  current broker compatibility gate; the Engine 29 override is disposable-only.
- Desired state is `deployment.yaml`; external deployment tooling writes
  `deployment.lock` atomically after verified acquisition/start/readiness/persistence.
  The MCP Manager exports `capabilities.lock` from canonical `tools.mcpDocker` state;
  IaC/WUD must not write it or introduce a second registry. These exports remain
  planned work, contain no secrets, and must not be advertised as implemented.
- Publishing a release never silently updates a host. Classify runtime-only versus
  migration-bearing changes; preserve compatible image/config/auth/data backups and
  rehearse restore. Image rollback does not undo data migration. Existing vulnerability
  policy applies to the exact candidate; documented triage is not a waiver.
  I1 separates pre-publication B13 approval from post-publication anonymous pull/smoke
  homologation; only homologated artifacts enter deployment. VPS C2–C4/I9 remain separate.
- P0 is open infrastructure only; premium GCP, entitlement, billing, marketplace,
  Kubernetes, private customer delivery and a proprietary registry need separate scope.
  Track new integration work in I1–I9 and residual product gates in their linked plans.
  `docs/plans/closed/` is historical; transferring a gate or editing a plan does not close it.

## Development constraints

- Analyze the required behavior, state ownership, and root cause before extending existing code. Refactor when the structure causes the problem; a smaller diff does not justify another fallback.
- Do not add defensive tests for hypothetical internal states or unsupported combinations. Each new test needs a reachable path and a meaningful contract to protect.
- Do not run `ruff format`; mechanical formatting obscures git blame and creates unrelated diffs. This constraint takes precedence over the optional touched-file formatting in `CONTRIBUTING.md`.

## Project boundaries and gates

- Treat HKUDS/nanobot as a source of selected improvements, not an automatic
  authority for Percival's `main`. Review releases monthly and relevant urgent
  fixes out of cycle; document accepted, deferred and rejected changes with
  their source revisions. Import on a review branch by isolated patch or
  cherry-pick where feasible. A broad merge needs a specific justification
  and full revalidation. Never rebase published `main` or fast-forward it to
  upstream. Follow the [runbook](RUNBOOK-sync-upstream.md).
- Send upstream PRs only for separable, generic fixes after the operator
  approves disclosure. Keep Percival-specific UI, memory, Docker-MCP work and
  branding in this project. Preserve third-party attribution and licenses.
- Percival's CI is the verification authority: `pytest`, `basedpyright
  nanobot` and `ruff check .`, plus affected UI, KG, packaging and Docker-MCP
  gates. Supported release platform is Linux; Docker images initially target
  `linux/amd64`, with ARM64 only after its own build/smoke evidence. Inspect the
  current workflows rather than repeating historical platform claims. Reuse
  unaffected evidence per `.agent/workflow.md`; documentation-only changes need
  link/consistency checks and `git diff --check`, not an unrelated runtime rebuild.
  Upstream CI success or local tests do not close candidate-specific remote gates.
- An agent may draft release notes, but the operator approves the final
  changelog, known limitations and links to evidence for the exact candidate.
  No tag, public repository, package publication or release is authorized by
  a green local test or by a draft. B6/B7 real-bundle rehearsal/cutover are
  personally owned by the operator. Local acceptance, IaC integration, VPS deployment
  and public release are distinct gates; a requested source commit/push authorizes
  that operation only, not image publication, deployment or real-data cutover.
