# Docker image security and maintenance policy

- **Status:** local policy established for F3; no publication or deployment
  authorized.
- **Scope:** Percival gateway, MCP broker, and six MCP server images on
  `linux/amd64`.
- **Owner:** each repository maintainer owns its image and dependency updates;
  bill is the coordinating operator for the Percival gateway/broker and this
  cross-repository gate.

## Vulnerability handling

- Generate an SBOM for every candidate image and scan the image itself, not
  only its source dependency lock.
- **Critical or High findings block the F3 gate.** A waiver requires an
  individually identified finding, applicability/exploitability review,
  compensating control, named owner, reason, and expiration date. No waiver is
  implied by this policy; no waivers were recorded in the 2026-10-09 scan.
- Medium/Low findings are retained in the scan report and reviewed during the
  regular update cycle or when exploitation/context materially changes.
- Scanner, database timestamp, image ID/digest, platform and report hashes are
  recorded with each scan. Scanner findings are triage signals and do not
  independently establish exploitability or non-applicability.

## Base and dependency maintenance

- Review base-image digests, Debian snapshot, APK inputs, uv/Python/Node
  toolchains, and dependency locks at least quarterly.
- Update sooner when an applicable Critical vulnerability, known exploitation,
  or other urgent security advisory affects an image. Rebuild and rescan the
  candidate after any update; retain the previous local artifact for rollback
  until the candidate is accepted.
- Keep upgrades explicit: move the base digest or snapshot date and lock
  versions/hashes in reviewed source changes. Do not silently refresh an
  immutable candidate or `:dev` alias as a security fix.

## Exception record

There is no standing allowlist or blanket waiver. An accepted exception must
record the image/source revision, finding IDs, affected package and version,
applicability, mitigation, approving owner, creation date, and expiry. Expired
exceptions block promotion until they are renewed or resolved. The local F3
scan found findings above the blocking threshold; they remain unwaived and the
F3 gate remains open.

## F3 execution of 2026-10-25

- Candidates were rebuilt from **committed, clean checkouts** and rescanned with
  Trivy 0.67.2 (`aquasec/trivy` pinned by digest, DB `UpdatedAt`
  2026-10-25T01:20:33Z). Result: **0 Critical and 0 High** on all eight image
  IDs, so no waiver was required or granted.
- The single remaining Medium, `CVE-2026-49138` on the gateway, carries a
  `not_affected` assessment anchored to that image ID in
  [`OpenVEX F3 do gateway`](../reports/2026-10-25-f3-openvex-gateway.json). It
  is a technical draft, not a waiver, and it expires with the image ID: a
  rebuild from another revision requires a fresh assessment.
- Findings and waivers do **not** transfer between images. The per-image
  evidence (scan JSON, CycloneDX SBOM, scanner digest, DB timestamp and
  SHA-256 of each artifact) lives outside the repository and is referenced from
  [`F3 2026-10-25`](../reports/2026-10-25-f3-reproducibility-contexts-posture.md).
- Immutable dependency sets are part of the posture: a candidate must install
  channel dependencies from the reviewed hash-locked files at build time, and
  runtime installation stays disabled in images
  (`NANOBOT_RUNTIME_PACKAGE_INSTALL=0`). Enabling installation at runtime
  invalidates the fixed dependency-set claim and requires a new candidate.

## Exception record (superseded)

The record above describes the 2026-10-09 scan, which found Critical/High
findings above the blocking threshold and left the F3 gate open. The 2026-10-25
execution above closed the local F3 gate; the statement is kept for history
because the 2026-10-09 findings were remediated rather than waived.
