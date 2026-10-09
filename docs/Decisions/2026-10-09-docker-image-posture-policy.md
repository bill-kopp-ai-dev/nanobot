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
