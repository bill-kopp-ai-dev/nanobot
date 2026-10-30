# Native MCP Manager — catalog, profiles and export contract

**Status:** local implementation for PBLabs app metadata 0.2; no catalog release
is currently curated or installable. The manager does not fetch remote catalog
URLs.

## Trust and catalog snapshots

- The index repository is the metadata source of truth. The gateway reads a local
  checkout mounted at `PERCIVAL_MCP_INDEX_ROOT`; the optional Compose overlay
  mounts it read-only. Trust is recorded by explicit local operator action as a
  catalog ID and SHA-256 of `public/catalog.json` in `tools.mcpDocker` schema 2.
- `catalog.json` contains SHA-256 pins for each `server.json`, `pblabs.app.yaml`
  and documentation input, plus the exact PBLabs 0.2 and MCP Registry schema pins.
  The manager verifies the snapshot, file hashes, schemas, release status, identity,
  version and OCI digest before returning an install candidate. Paths must remain
  inside the pinned index; symlinked release inputs are rejected.
- The `pblabs-mcp-index` checkout currently has no remote and its generated catalog
  is empty. Local snapshot registration is therefore testable, but it yields no
  installable apps. Remote fetch and publication require a later source/release
  decision.

## Policy, consent and image acquisition

- The broker's acquisition policy is independent of catalog metadata and gateway
  config. `docker-compose.mcp-catalog.yml` mounts the provisioned policy file
  read-only at `/run/secrets/percival-mcp-acquisition-policy.json`. The policy lists
  exact allowed Docker Hub repositories and supported platforms; absence, malformed
  content, writable file mode, tags, unlisted repositories or unsupported platforms
  fail closed. Provisioned files must have no write bits (for example `0444`) as
  well as a read-only bind. The example policy is empty by default; populate exact
  repository names only after their published identity is established.
- Only the new broker `acquire` operation performs a pull. It accepts a repo digest
  and platform, executes `docker pull --platform ...` only when that exact digest is
  not already present, then verifies the local RepoDigest, image ID and platform.
  Existing install/update paths retain `--pull=never` behavior.
- Catalog installation requires a schema-2 config, a registered local snapshot,
  broker feature support, an exact per-install confirmation string, elevated local
  WebUI consent, and a matching config revision (CAS). Acquisition happens before
  manager config commit. If CAS loses after acquisition, the immutable image may
  remain cached but no server is installed.

## App profiles and private state

- `pblabs.app.yaml` schema 0.2 is validated in the gateway. It declares requirements,
  never host paths or runtime grants. Required host data sources are supplied at
  install time and mapped to the declared container targets. The manager forces an
  explicit reduced host-access profile; `mounts: null`/Full cannot be used for a
  catalog app. Sources cannot also be exposed under `/host`; destinations cannot
  overlap or target control paths. Read-only requirements stay read-only.
- `needs_network: false` forbids bridge networking; `true` permits the operator to
  choose `bridge` or the stricter `none`. Required secrets must use the typed
  `secret` configuration and never enter manifests or generated exports. Other
  runtime environment prompts come from the pinned `server.json` package's
  `environmentVariables`; the manager cross-checks required secret names against
  PBLabs metadata, rejects undeclared values and rejects embedded `value` fields
  in registry environment declarations. AgentMail's API key uses this
  env-secret path because that app currently consumes an env var; file-secret
  delivery remains future work.
- `tools.mcpDocker` schema 1 remains readable/writable in its historical shape.
  Schema 2 is opt-in through `migrate-schema`, which requires the exact typed
  confirmation, expected revision, writer lock, no unresolved transition and a
  mode-0600 pre-migration config snapshot. Schema 2 adds a stable installation ID,
  trusted catalog pins, app release provenance and installation-specific mount maps.
- Schema rollback is exposed only for the exact migration snapshot and only while
  no catalog/app data has been committed and server/config state still matches the
  snapshot. Otherwise it is refused; stopping/restoring a deployment remains an
  operator-controlled operation.

## `capabilities.lock`

`export-capabilities` validates against `nanobot/mcp_docker/capabilities.schema.1.0.json`
and atomically writes a derived `mcp-docker/capabilities.lock` under mode 0600. It
includes installation ID, global revision, manager ownership,
configured server/image identities, app provenance and declared mount targets.
It excludes environment values, host source paths and private index roots. Runtime
observation is reported as `unknown`; export does not run manager recovery, inspect
Docker or claim readiness. This file is a projection, never a second source of
installation intent.

## Current validation boundary

Unit and fixture tests validate schema, local snapshot hash checks, policy enforcement,
mount/network/secret mapping, schema migration/rollback, CAS and export redaction.
No public catalog release/digest exists, so no real OCI acquisition or consumer
container install has been performed. No running Percival manager was queried or
mutated by these tests.
