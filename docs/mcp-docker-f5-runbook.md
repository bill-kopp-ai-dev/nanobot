# MCP Docker F5 runbook: state migration and recovery

This runbook prepares a **manual, reversible** migration of the host state
directory from `~/.nanobot` to `~/.percival` for the Compose sidecar overlay.
It does not perform the migration or authorize a VPS deployment. Use it only
after recording the VPS inventory and confirming the actual mount paths, UID/GID,
Docker Engine version, and maintenance window.

## Preconditions

- Record `git rev-parse HEAD`, `docker version`, and the output of
  `scripts/percival-vps-inventory.sh` in the deployment evidence.
- Confirm Engine Client and Server are in the approved 27.x line and the
  inventory's socket GID, Docker data-root, state path, and mounts match the
  reviewed broker policy. Stop if any value differs from the accepted design.
- Prepare the broker token as an independent file readable only by the gateway
  owner and the dedicated broker token group (`0640`); do not put it in a
  container environment, shell history, or migration report.
- Use one numeric `PERCIVAL_BROKER_TOKEN_GID` on the gateway, the broker's
  `group_add`, and the token file. A host-launched `nanobot-webui` does **not**
  start the broker: with a group-readable token and no GID override, its client
  expects GID 65532 and will reject a different group before HTTP. Do not
  run a host gateway concurrently with the Compose pair on the same state.
  The gateway entrypoint restores the configured token GID after normalizing
  state ownership; check the on-disk GID again after every gateway recreation.
- Ensure the host Docker daemon starts at boot, not only on socket demand:
  verify `systemctl is-enabled docker.service`. If policy allows, enable the
  service before relying on container restart policies:

  ```sh
  sudo systemctl enable docker.service
  ```

  `docker.socket` being enabled alone may leave the daemon stopped until a
  client connects, so containers with `restart: unless-stopped` would not
  recover autonomously.
- Confirm the target `$HOME/.percival` does not exist. Never merge two live
  state trees automatically.

## Copy and cutover

1. Stop any host-launched gateway/WebUI in the agreed maintenance window and
   verify its ports are free. Stop the current Compose stack without removing
   volumes (if running):

   ```sh
   docker compose -f docker-compose.yml -f docker-compose.mcp-broker.yml down
   ```

2. Make a protected archive on the same host or an approved backup target,
   preserving numeric ownership and metadata. Keep it outside both state trees.

   ```sh
   umask 077
   tar --acls --xattrs --numeric-owner -cpf "$HOME/percival-state-pre-migration.tar" -C "$HOME" .nanobot
   ```

3. Copy, do not move or rename, the stopped tree. Preserve ownership, ACLs,
   extended attributes, hard links and modes:

   ```sh
   install -d -m 0700 "$HOME/.percival"
   rsync -aHAX --numeric-ids "$HOME/.nanobot/" "$HOME/.percival/"
   diff -qr "$HOME/.nanobot" "$HOME/.percival"
   ```

   A nonzero `diff` requires inspection; do not proceed by ignoring it. Check
   that `config.json`, operator credential, broker token, audit, backups and
   transition journals retain their expected ownership and restrictive modes.
   The token may be stored outside this tree; use the inventoried actual path.

4. Set `PERCIVAL_STATE_HOST_PATH=$HOME/.percival` and the inventoried numeric
   socket/token GIDs and token-file path in the protected deployment
   environment. Also set `PERCIVAL_DOCKER_GATEWAY_TOKEN_ISSUE_SECRET_FILE` to a
   private, persistent file readable by container UID 1000; it authorizes WebUI
   token issuance on the container-bound WebSocket listener. Render and inspect the combined Compose
    model before starting. Do not print its raw environment section because it
    contains the token-issuance secret; emit only non-secret service, port and
    mount fields:

   ```sh
    docker compose -f docker-compose.yml -f docker-compose.mcp-broker.yml config --format json \
      | python3 -c 'import json,sys; d=json.load(sys.stdin); print(json.dumps({n:{"image":s.get("image"),"ports":s.get("ports",[]),"volumes":[v.get("target") for v in s.get("volumes",[])]} for n,s in d["services"].items()},indent=2))'
   ```

   Confirm only `percival-mcp-broker` mounts `/var/run/docker.sock`; the gateway
   and MCP containers must not gain the socket or Docker CLI. No broker port may
   be published.

5. Recreate the gateway and sidecar, then verify readiness and state:

   ```sh
   docker compose -f docker-compose.yml -f docker-compose.mcp-broker.yml build nanobot-gateway percival-mcp-broker
   docker compose -f docker-compose.yml -f docker-compose.mcp-broker.yml up -d --force-recreate nanobot-gateway percival-mcp-broker
   docker compose -f docker-compose.yml -f docker-compose.mcp-broker.yml ps
   docker compose -f docker-compose.yml -f docker-compose.mcp-broker.yml exec -T --user 1000:1000 nanobot-gateway nanobot mcp-docker doctor --config /home/nanobot/.nanobot/config.json
   ```

   In the authenticated UI/CLI, verify the expected config revision, server
   registry, redacted secrets, audit tail and backup list; then exercise both
   fixture servers and all eight operation families. Confirm broker reconnection
   after a gateway recreation and that protected mounts/network are observed.
   Record redacted output only.

   `doctor` checks token, authenticated broker transport, Docker Engine and
   protected-host policy without starting containers. If it fails, fix the
   reported dependency before attempting reconciliation. A broker health check
   runs independently in the sidecar; a gateway HTTP response alone does not
   prove MCP Docker readiness. Restart/recreate the sidecar **after** replacing
   the gateway container: `network_mode: service:nanobot-gateway` ties its
   loopback to that gateway's network namespace. `restart: unless-stopped`
   resumes a running stack after reboot, but does not start a stack deliberately
   removed with `docker compose down`.

   After an outage, compare persisted registry and pending journals with the
   actual Docker containers; only the managed runtime's typed reconciliation
   should recreate active missing containers. Do not treat stored `running`
   intent or saved tools as proof of availability. Verify inactive and
   `stopped-persistent` servers remain stopped, and verify each active server
   separately through Docker observation and MCP tools/list. A missing local
   image or unresolved broker environment reference requires explicit review.

## Rollback

If any comparison, permission, health or functional check fails, stop the new
stack with both Compose files and without `-v`, set
`PERCIVAL_STATE_HOST_PATH=$HOME/.nanobot`, and recreate the original
gateway/sidecar. Recheck config revision and audit, then keep both
the archive and `.percival` copy untouched for diagnosis. Do not delete
`~/.nanobot`, the archive, or Docker volumes as part of rollback. A rollback
after state has changed in `.percival` requires a deliberate reconciliation of
the newer config/audit before using the old copy; a raw overwrite would lose
operations performed after cutover.

## Recovery journal semantics

`runtime_data_dir/mcp-docker/transitions/<server_id>.json` is a mode-0600,
atomic per-server journal. `preparing` is written and fsynced before the broker
mutation; `committed` follows config persistence; handled failures end in
`failed`. On the next authenticated list/mutation or CLI restore, recovery
compares the config revision with the journal base revision and asks the broker
to reconcile the persisted server state, or to remove an owned orphan container
for an already-committed exclusion. An unresolved broker/error/revision state
remains `preparing`, is surfaced in the page, and blocks further mutations.
This is compensating recovery across two durability domains, not a distributed
transaction. Never hand-edit a journal or config file to clear a pending state;
retain the files and perform a reviewed recovery using the exact evidence.

Restore is available from the management page for an existing backup. It
requires operator authorization, the backup's server ID typed by the operator,
checksum validation, a current config revision, and refusal to overwrite an
existing server. Images and volumes are retained; restore does not fetch an
image.

## Evidence still required to close deployment readiness

Rehearse a clean boot, broker restart, gateway+sidecar recreation, and token
GID mismatch; capture `doctor`, Compose health, actual observation and tools
after each transition. Local tests, Compose rendering, and disposable Engine
smoke are not the F5 VPS gate. Attach the real inventory and record the actual
Client/Server 27.x stack, GID/mount verification, state migration and rollback
rehearsal, gateway/sidecar
recreation, both MCP fixtures, all operation families, direct-daemon negative
tests, indirect-risk statement, and an explicit operator acceptance on the
candidate SHA. Until those checks are performed, deployment readiness remains
open and no release/publication is implied.
