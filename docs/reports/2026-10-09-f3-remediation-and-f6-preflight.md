# F3 remediation attempt and F6 preflight

- **Observed:** 2026-10-09 local time / 2026-10-10 UTC.
- **Result:** Python dependency fixes, candidate builds and offline stdio/persistence
  smokes completed locally. **F3 remains open. F6 has since started under an
  explicit operator override; see the [F6 execution report](2026-10-10-f6-local-cutover.md).**
- **Policy:** [`Docker image security and maintenance policy`](../Decisions/2026-10-09-docker-image-posture-policy.md).
- **Scan:** Trivy 0.67.2, image digest
  `sha256:ac2f9d0197456a8ce460884b113e49d65b667f506c31d014c9955869a7a5d682`;
  local JSON outputs and image tars are under
  `/home/bill/.positronic/runtime/tmp/opencode/trivy-reports/`.

## Changes and validation

- Updated MCP SDK constraints to `mcp[cli]>=1.28.1,<2.0.0` where directly
  declared; locks resolve to 1.30.0. Updated affected Python locks for AnyIO,
  Starlette, `python-multipart`, h11, PyJWT, cryptography, urllib3, NLTK,
  aiohttp, langgraph-sdk, and pypdf. Percival's gateway lock moved Dulwich to
  1.2.17 and pypdf to 6.20.0; the pypdf constraints and corresponding metadata
  test were updated.
- Migrated the Bookworm-based candidate stages to digest-pinned Debian Trixie
  bases, set Debian snapshot inputs, and version-pinned direct apt/apk packages
  where available. This removes the previous Critical zlib finding, but does
  not clear all Trixie package findings.
- The broker candidate now uses Docker CLI 29.2.0 on Alpine 3.23, upgraded
  pinned Alpine packages, retained Python 3.12.15 and hash-locked broker
  dependencies. Its readiness check accepts Docker Client 27.x/29.x with
  Engine 27.x; the explicitly marked disposable Engine 29 fixture remains
  supported. **Compatibility with Engine 27.5.1 has not been exercised locally.**
- Built eight local candidates tagged `f3-remediation`. Their Docker image IDs:

  | Image | Image ID | Critical | High |
  |---|---|---:|---:|
  | Notes | `sha256:830c014d1c0c4c5f24ac21ff5d38b9d45038cfb7f3da40729ac9b7f614f7ce2b` | 0 | 44 |
  | AgentMail | `sha256:6af3c12ba1425f393dcd744bffd19b530968a27bd8c3a6724076d219a1fa0001` | 0 | 44 |
  | Weather | `sha256:bd1f231ef5f3d1526e004c8bc92f0e01ba28e069024dc0f768d44c6e76b04620` | 0 | 44 |
  | Khan Calendar | `sha256:aff5bce93923fe263be8d919546eabe14565a4475b229935b6df6fe2bff65904` | 0 | 44 |
  | OSM | `sha256:2ae01a346195ccc6f1f0ac88d391a3e15fbb0db525df95b0574c8ef11aa056f6` | 0 | 54 |
  | Deep Research | `sha256:c0c27be601955d2418e5f9cad6c5eefc12ab3753af9cce26e1737bc6989a2feb` | 0 | 60 |
  | Gateway | `sha256:26f86ec07656b40b3fd39f6b7e8eb6603815a407fb0a995b3ccf2a8fc942771a` | 1 | 64 |
  | MCP broker | `sha256:b7a11770d7dc6db3f245597c8280ee12ab7700c21ac7efb9c341f25e16f05561` | 5 | 132 |

  Trivy report SHA-256 values, in the table order above: Notes
  `f342c34c91ebd40e343b2c1bc5f6dd0df3346be1ab05dbe093a38c794ff63467`,
  AgentMail `a2a1d89ad89da3fd88ee0c1d14a170f3a0b45b950a10a944e391069d103e0f8f`,
  Weather `a79fed162fb9d453195f71345dbeed16398f2754d8af622482f8cae21dc8c1ba`,
  Khan `57cd954b8b9b0649dcfedd7691a525ea423c0bab9682f82133d7f691d701940b`,
  OSM `249ee15f63dfb3c8a3106700a91f487500c7bb7b16cacb6ca635aae472c5d7a3`,
  Deep Research `7bffe595740bd05bb318ef5b024b5e18de52814164e61f937a977c5d6ac3b296`,
  Gateway `8a05c602094c934535fa1962cb063361f860f33779566cfb0c124aa37a6d714f`,
  Broker `69051981c58b5bfc683fff91ef0fcc39806b7e94c974e237cb85f166906bc326`.

- Local tests passed: root `pytest` **9,312 passed / 49 skipped**, BasedPyright
  **0 errors / 0 warnings / 0 notes**, Ruff clean; MCP suites Notes 45,
  AgentMail 230/1 skipped, Weather 147, Khan 220, OSM 75, Deep Research
  414/3 skipped. The six MCP stdio conformance probes passed with tool counts
  Notes 12, AgentMail 24, Weather 9, Khan 12, OSM 37 and Deep Research 5.
  Notes' isolated bind-mount and named-volume persistence smoke passed; a Khan
  event created in a temporary bind mount remained visible after container
  restart. Notes Ruff reported 41 findings in source/test files untouched by
  this Docker/dependency change; the canonical Docker workflow does not run
  Notes Ruff. OSM's HTTP smoke passed auth, listener health, loopback binding,
  MCP initialize and shutdown; Weather's HTTP candidate returned `/healthz`
  200 and unauthenticated MCP 401; Deep Research's HTTP candidate returned
  `/health` 200 and shut down cleanly.

## Remaining blockers

1. **F3 is not closed.** The zero-waiver policy still blocks Critical/High.
   The broker has five Critical and 132 High observations, including Go stdlib
   1.25.6 and gRPC 1.76.0. The gateway retains Critical OpenSSH. Every Debian
   Trixie MCP image has High package findings. Debian's tracker currently lists
   relevant Trixie packages for CVE-2026-76642 (util-linux), CVE-2025-69720
   (ncurses), CVE-2026-60002 (OpenSSH), and CVE-2026-81726 (NLTK) as vulnerable
   or unfixed; moving to the current 20261010 snapshot does not change those
   package versions. No waiver was added. A newer Docker CLI 29.7.2 probe has
   zero Critical but still 48 High and is not a tested broker candidate.
2. **F4 remains partial.** Local stdio, Notes/Khan persistence and OSM/Weather/
   Deep Research HTTP evidence passed. Remaining restore and gateway/API
   acceptance evidence has not been completed as an F4 gate.
3. **F5 remains open.** `gh auth status` reports no authenticated GitHub host,
   so Actions runs/artifacts on the exact candidate SHAs could not be queried.
4. **F6 is partial under explicit operator override.** Four Positronic registry
   entries were repointed to local candidates. Percival gateway/broker consumers
   remain unchanged: gateway was stopped and its historical binding is
   non-loopback; Compose also lacks the token-issuance-secret path. Existing
   session containers and all old images remain. See the F6 report for revisions,
   candidate IDs, tests and remaining gates.

No commit, push, remote workflow run, publication or deploy was performed.
Candidate image and scan files remain local for follow-up.
