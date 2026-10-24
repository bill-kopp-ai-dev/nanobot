---
name: mcp-docker-operations
description: Inspect, troubleshoot, update, and roll back Percival-managed Docker MCP servers using their supported manager and isolated fixtures.
---

# Percival MCP Docker operations

Use this Local Skill only while working in the Percival project. The Positronic
consumer has a separate TUI/CLI and inventory; never apply Percival operations
to a Positronic-owned server. The central procedure is
`docs/operations/mcp-docker-local-runbook.md` in the Percival checkout.

## Default to read-only

Before any operation, identify the owner from the manager record and container
labels, then record repository/source SHA and worktree state, image ID or
RepoDigest, tag alias, global/server revisions, transport, effective mounts,
persistent data, consumers, and rollback image. Redact env, tokens and full
`docker inspect` output. Do not infer ownership from a name, age or health.

Use the Percival WebUI MCP Manager / its authenticated API for Percival state.
Use the Positronic `/mcp` TUI or its supported `positronic mcp server` command
for Positronic state. Never edit `config.json`, `mcp-docker/`, Positronic
`registry.json`, or server configuration files directly. Compose is for local
development/fixtures; it must not become a second owner of a manager-created
production MCP container. The broker alone receives Docker access.

## Diagnose by transport

- **stdio:** no TTY, published port or HTTP healthcheck; stdout carries only
  MCP JSON-RPC. Check the owner’s MCP `initialize`, `tools/list`, then a safe
  read-only tool call. Docker `unhealthy` from an HTTP probe is not evidence
  that stdio is unavailable.
- **HTTP:** verify the dedicated HTTP profile, loopback bind and configured
  authentication first. Check the documented health endpoint, then perform an
  authenticated MCP request. A healthy HTTP probe alone does not prove MCP
  readiness. Do not expose a listener or copy a token into commands/logs.
- Check single-writer ownership (gateway or API), broker health and manager
  audit/transition status separately. `doctor` is diagnostic, not readiness
  for a particular server or permission to mutate it.

## Dry-run and change control

Start with a proposed inventory and action plan; do not perform a mutation
during a dry-run. Resolve the exact server and image ID, compare current
global/server revisions (CAS), state expected effects, backup/data plan,
smokes, observation window and rollback. Stop if ownership, revision, image,
mount or state differs from the approved plan. No tag is an immutable pin.

An explicit operator approval is required for install, activate, configure,
update, restart, stop, restore, exclude/remove, image cleanup, publication or
deployment. Use only the manager’s supported action and its current revision
and confirmation fields. Preserve image A before changing to B; verify MCP
handshake plus a safe tool call after each change. Roll back to A through the
same manager with freshly read CAS revisions. Restore validates a backup but
does not download a missing image or undo data migrations.

Never run `docker system prune`, bulk prune, blind `docker rm`, or cleanup by
tag/name/age/`unhealthy`. Preserve external containers and persistent data.

## Required rehearsal

Use the disposable D9 runtime fixture, not live MCP instances, credentials,
vaults, calendars, inboxes or provider APIs. Exercise A→B→A using image IDs,
including a stdio MCP with a deliberately false HTTP healthcheck; prove the
safe MCP call succeeds while Docker reports `unhealthy`, then restore A and
verify the response. For HTTP mode, use a fixture with a failing health/readiness
probe and confirm the manager reports the failure without switching a live pin.
Record fixture IDs/results and cleanup; do not claim the rehearsal promotes,
publishes or accepts the production candidates.
