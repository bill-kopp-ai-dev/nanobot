# Percival: upstream, CI and release governance

**Operator decision:** 2026-10-06. Percival is an independent project derived
from HKUDS/nanobot. Development continues in the current private repository;
after the planned changes and validation, the operator will create a separate
public Percival repository. A public release, repository creation and transfer
of private history require separate operator approval. I2 aligns local `nanobot-ai`
metadata to 0.1.0; **no published Percival release** follows from that change.
The inherited 0.3.5 remains historical artifact metadata. The future Python distribution name remains undecided;
open Docker/OCI distribution and the account/naming contracts are decided in the
[I1 ADR](Decisions/2026-10-23-open-iac-contracts.md).

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
Linux only. The 2026-10-25 static review of `.github/workflows/ci.yml`,
`kg-platform.yml` and `tui-release.yml` found no Windows/macOS jobs; the earlier
statement that CI still contained them is superseded. This is source inspection,
not a successful workflow run. Candidate-specific remote conformance remains C1;
packaging/publication and supported image platforms keep their own release gates.

## Manual de operação e manutenção

O [manual operacional dos MCPs Docker locais](operations/mcp-docker-local-runbook.md)
concentra inventário seguro, build, atualização, rollback, backup/restore de
Notes/Khan, contenção de incidentes (falso `unhealthy` em stdio, SIGTERM/PID 1),
revisão trimestral, gatilho urgente por CVE e política de retenção de imagens
intermediárias. Este manual não substitui o [runbook F5 de migração/recuperação
de estado `~/.nanobot`→`~/.percival`](mcp-docker-f5-runbook.md); os dois
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

## I1: open distribution contracts and release sequencing

**Operator confirmations:** 2026-10-23. The current GitHub owner is
`bill-kopp-ai-dev`; the future Positronic Bean Labs owner is `p-bean-labs`.
Docker Hub uses `pbeanlabs`, independently of that future GitHub migration.
Local access is not configured yet, per the operator; permissions and image/repository
availability have not been checked remotely.

Subsequent evidence: the private repository's SSH commit/push to `main` succeeded
for `eb4e3555` (I1 documentation). This does not verify Actions credentials,
Docker Hub push authorization, public repository creation or registry availability.

The private development repository stays `bill-kopp-ai-dev/nanobot`. The separate
reviewed public source repository will be named `percival`, under the current owner
if published before migration, then under `p-bean-labs`. A migration of ownership is
not approval to disclose private history or publish an image. The decision creates
no remote repository and changes no remote URL.

The [ADR](Decisions/2026-10-23-open-iac-contracts.md) and
[handoff](iac-p0-contract-handoff.md) fix the P0 contracts, restricted broker acquisition,
catalog consent, one-instance-per-daemon limit and the bill-owned contract reviews.
They add to the historical local-only/B20 decisions without activating repository
sources, changing current server permissions or implementing the new schemas/API.

For the first public release, B13 reviews the exact final source/version, completed
scope, applicable local/Actions evidence, image scans and recovery plan **before**
publication. Public anonymous pulls and registry smoke tests necessarily follow
publication and gate **homologation/promotion**, not permission to publish. A published
image failing those checks is not homologated and cannot enter the deployment bundle.
No Critical/High waiver or bypass of candidate-specific product gates is implied.

Public C3/C4 and I9 are not prerequisites for the first publication; they remain
distinct target-specific deployment/acceptance gates after homologation. Any required
earlier private staging/transfer needs its own authorization. Source publication,
image publication, registry homologation and real-data cutover keep separate evidence
and approvals. No operational release/deploy authorization was granted by I1.
