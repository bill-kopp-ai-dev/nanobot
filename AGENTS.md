# Working on Percival

Percival is an independent project derived from HKUDS/nanobot. Development
currently takes place in a private repository; a separate public Percival
repository is planned after the agreed features and gates are complete. The
current `nanobot-ai` metadata and upstream documentation do not constitute a
Percival release. The intended first Percival version is 0.1.0; its package
name/distribution remains undecided. Read the [project governance
decision](docs/percival-governance.md) before sync, contribution, CI or
publication work.

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
  nanobot` and `ruff check .`, plus affected UI, KG, packaging and future
  Docker-MCP gates. Supported release platform: Linux only. The inherited
  general CI still has Windows jobs; reconcile it and packaging before
  claiming Linux-only release readiness. Upstream CI success is not a
  substitute for tests on the exact Percival commit.
- An agent may draft release notes, but the operator approves the final
  changelog, known limitations and links to evidence for the exact candidate.
  No tag, public repository, package publication or release is authorized by
  a green local test or by a draft. B6/B7 real-bundle rehearsal/cutover are
  personally owned by the operator.
