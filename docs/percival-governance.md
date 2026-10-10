# Percival: upstream, CI and release governance

**Operator decision:** 2026-10-06. Percival is an independent project derived
from HKUDS/nanobot. Development continues in the current private repository;
after the planned changes and validation, the operator will create a separate
public Percival repository. A public release, repository creation and transfer
of private history require separate operator approval. `nanobot-ai` 0.3.5 is
the current package metadata, **not** a published Percival release; Percival's
intended first version is 0.1.0. Distribution name and format are undecided.

## B10: contributions to HKUDS/nanobot

Upstream PRs are selective, not the default way to develop Percival. Propose
only general-purpose, separable fixes that the operator approves for public
disclosure and wants to maintain in common. Keep Percival branding, UI,
memory, Docker-packaged MCP integration and project-specific behavior in
Percival. Do not send proprietary or private-project material upstream.
Always preserve applicable licenses and attribution when reusing code.

## B11: selective upstream intake

Review upstream releases/changes monthly and out of cycle for relevant
security fixes or serious bugs. This is a review cadence, not an automatic
merge or an obligation to take every release or follow a particular version.
Record the reviewed upstream revision and decision, including deferred
changes. For each selected change, work in an integration branch, identify
its original commit/release and license, adapt deliberately, run affected
gates and review the resulting diff before integrating into Percival. Prefer
isolated patches or cherry-picks; use a broad merge only when its benefits
outweigh the conflicts and full revalidation. Do not rebase published `main`.
See [sync runbook](../RUNBOOK-sync-upstream.md) for the procedure.

## B12: Percival-owned verification

Percival's own CI and release gates, on the exact candidate commit, are the
source of truth; a green HKUDS run is not evidence that Percival passes. Keep
useful upstream checks where they cover supported Percival behavior, adding
Python, UI, KG, packaging and, when implemented, Docker-MCP checks. Run
affected checks after each upstream import and the full release gate before
tagging. Document any changed gate and its reason. Supported platform is
Linux only. Current `.github/workflows/kg-platform.yml` runs on Ubuntu, but
`.github/workflows/ci.yml` still contains Windows Python/process/TUI jobs,
and upstream TUI packaging/release documentation assumes additional targets.
CI and packaging must be reconciled with Linux-only before claiming that the
Percival release gate is complete. A CI policy decision alone does not close
that implementation gap.

## Manual de operação e manutenção

O [manual operacional dos MCPs Docker locais](../operations/mcp-docker-local-runbook.md)
concentra inventário seguro, build, atualização, rollback, backup/restore de
Notes/Khan, contenção de incidentes (falso `unhealthy` em stdio, SIGTERM/PID 1),
revisão trimestral, gatilho urgente por CVE e política de retenção de imagens
intermediárias. Este manual não substitui o [runbook F5 de migração/recuperação
de estado `~/.nanobot`→`~/.percival`](../mcp-docker-f5-runbook.md); os dois
convivem. O aceite F7 não fecha sem que o manual esteja revisado e vinculado
a partir deste parágrafo.

## B13: release authority

The agent can draft `docs/kg-release-notes.md` and the canonical changelog,
known limitations, migration/rollback guidance and cross-references. The
operator reviews the final version and explicitly signs off the exact release
candidate before any tag push, public repository publication, GitHub Release
or package upload. Cite test/CI evidence from that commit and distinguish
synthetic from real-bundle/provider validation. B6/B7 real-bundle rehearsal
and production cutover remain operator-owned; neither is implied by a
documentation update. Unfinished planned features are not advertised as
shipped. The public repository should use reviewed history, with secrets,
private data, dependency licenses and provenance checked before publication;
do not assume that all private commits will be published.
