#!/usr/bin/env bash
# Percival F0 — VPS inventory script.
#
# Run on the actual VPS as the operator (or with sudo) before the F0
# gate is opened.  Collects the topology facts the plan needs:
#   - Docker Client/Server versions, data-root, socket path and GID
#   - Submounts and aliases that could re-expose the daemon control
#     plane from inside a container with /:/host
#   - Existing /root/.percival and /home/nanobot/.nanobot data
#   - Reverse proxy / public port configuration
#   - Where the operator stores WebUI bearer tokens, provider keys and
#     other sensitive material
#
# Output is JSON on stdout.  Re-runnable; idempotent; read-only.
#
# Usage:
#   scripts/percival-vps-inventory.sh
#   scripts/percival-vps-inventory.sh > vps-inventory.json
#
# Exit codes:
#   0   inventory completed (warnings are non-fatal)
#   1   docker CLI missing or not in the docker group

set -euo pipefail

warn() { printf 'WARN: %s\n' "$*" >&2; }
die()  { printf 'ERROR: %s\n' "$*" >&2; exit 1; }

command -v docker >/dev/null 2>&1 || die "docker CLI not found in PATH"
docker info >/dev/null 2>&1 || die "docker info failed (is the daemon reachable?)"

client_version="$(docker version --format '{{.Client.Version}}' 2>/dev/null || echo '?')"
server_version="$(docker version --format '{{.Server.Version}}' 2>/dev/null || echo '?')"
data_root="$(docker info --format '{{.DockerRootDir}}' 2>/dev/null || echo '?')"
# ClientInfo.SocketPath is empty for some daemons; fall back to /var/run/docker.sock
socket_path="$(docker info --format '{{.ClientInfo.SocketPath}}' 2>/dev/null || true)"
if [[ -z "${socket_path}" ]]; then
  socket_path="/var/run/docker.sock"
fi
socket_gid="$(stat -c '%g' "${socket_path}" 2>/dev/null || echo '?')"

# The default /var/run is a tmpfs symlink on most distros; list what is
# actually mounted there so we know what a /host bind would expose.
# -n suppresses the header row; the result is flattened to a single line
# so it can be embedded in a JSON string without escaping newlines.
host_mounts="$(findmnt -T "${socket_path:-/var/run/docker.sock}" -no TARGET,SOURCE,FSTYPE,OPTIONS 2>/dev/null | tr '\n\t' '  ' | sed 's/ $//' || true)"
if [[ -z "${host_mounts}" ]]; then
  host_mounts="(no mount info available)"
fi

# Existing runtime data locations.
existing_nanobot="$({ [ -d "${HOME}/.nanobot" ] && du -sb "${HOME}/.nanobot" 2>/dev/null; } | awk '{print $1}' || true)"
existing_percival="$({ [ -d "${HOME}/.percival" ] && du -sb "${HOME}/.percival" 2>/dev/null; } | awk '{print $1}' || true)"

# Public listening ports on the host (excluding loopback).
public_ports="$(ss -ltnH 2>/dev/null | awk '$4 !~ /^(127\.|::1)/ {print $4}' | sort -u | paste -sd, -)"
if [[ -z "${public_ports}" ]]; then
  public_ports="(none detected)"
fi

# Reverse proxy / TLS terminator guesses.  Best-effort: detect nginx,
# caddy, traefik containers, and any process bound to 80/443 that the
# gateway should be aware of.  Flattened to a single line for JSON.
proxy_hits="$(docker ps --format '{{.Image}}\t{{.Names}}\t{{.Ports}}' 2>/dev/null \
  | awk -F'\t' 'tolower($1) ~ /nginx|caddy|traefik|haproxy/ {print $1, $2, $3}' \
  | tr '\n' ';' | sed 's/;$//' || true)"
if [[ -z "${proxy_hits}" ]]; then
  proxy_hits="(no proxy container detected)"
fi

# Candidate .percival location chosen by the operator at VPS setup.
# The script does NOT create it; it just records the absence.
candidate_percival="${PERCIVAL_DATA_DIR:-/srv/percival/.percival}"
candidate_percival_present="false"
[ -d "${candidate_percival}" ] && candidate_percival_present="true"

# Sensitive paths that the broker must keep out of MCP mounts.
# Operator can override with PERCIVAL_SENSITIVE_PATHS env (colon list).
IFS=':' read -r -a sensitive_paths <<< "${PERCIVAL_SENSITIVE_PATHS:-/etc/ssh:/etc/shadow:/root/.ssh:/root/.gnupg:/var/lib/docker:${candidate_percival}}"
sensitive_json="["
first=1
for sp in "${sensitive_paths[@]}"; do
  [[ -z "${sp}" ]] && continue
  exists="false"; [ -e "${sp}" ] && exists="true"
  if [[ ${first} -eq 1 ]]; then first=0; else sensitive_json+=","; fi
  sensitive_json+="{\"path\":\"${sp}\",\"exists\":${exists}}"
done
sensitive_json+="]"

# All host submounts affect the effective coverage of bind-recursive=disabled,
# not just Docker paths: /home may be a separate filesystem. findmnt exposes
# actual mount targets; mountinfo field $2 is the *parent ID*, not the target.
submounts="$(findmnt -rn -o TARGET,SOURCE,FSTYPE 2>/dev/null \
  | awk '$1 != "/" {print}' | sort -u | tr '\n' ';' | sed 's/;$//' || true)"
if [[ -z "${submounts}" ]]; then
  submounts="(no relevant submounts detected)"
fi

# Tokens / keys already on disk (read-only, just stat the files).
declare -a secret_paths=(
  "${HOME}/.nanobot/config.json"
  "${HOME}/.nanobot/auth"
  "${HOME}/.percival/config.json"
  "${HOME}/.percival/mcp-docker/operator.json"
  "/etc/nginx/sites-enabled"
  "/etc/caddy"
)
secrets_json="["
first=1
for s in "${secret_paths[@]}"; do
  exists="false"; [ -e "${s}" ] && exists="true"
  if [[ ${first} -eq 1 ]]; then first=0; else secrets_json+=","; fi
  secrets_json+="{\"path\":\"${s}\",\"exists\":${exists}}"
done
secrets_json+="]"

printf '{\n'
printf '  "docker": {\n'
printf '    "client_version": "%s",\n'   "${client_version}"
printf '    "server_version": "%s",\n'   "${server_version}"
printf '    "data_root": "%s",\n'        "${data_root}"
printf '    "socket_path": "%s",\n'      "${socket_path}"
printf '    "socket_gid": %s,\n'         "${socket_gid}"
printf '    "host_mount_at_socket": "%s",\n' "${host_mounts//\"/\\\"}"
printf '    "submounts": "%s",\n'        "${submounts//\"/\\\"}"
printf '    "public_listening_ports": "%s",\n' "${public_ports}"
printf '    "proxy_containers": "%s"\n'  "${proxy_hits//\"/\\\"}"
printf '  },\n'
printf '  "persistence": {\n'
printf '    "candidate_percival_path": "%s",\n' "${candidate_percival}"
printf '    "candidate_percival_present": %s,\n' "${candidate_percival_present}"
printf '    "existing_nanobot_bytes": %s,\n'     "${existing_nanobot:-0}"
printf '    "existing_percival_bytes": %s\n'    "${existing_percival:-0}"
printf '  },\n'
printf '  "sensitive_paths": %s,\n' "${sensitive_json}"
printf '  "candidate_secret_paths": %s,\n' "${secrets_json}"
printf '  "notes": [\n'
printf '    "client/server versions verified individually: docker version --format prints the Server.Version line; --version only checks the CLI.",\n'
printf '    "socket_gid is read from stat on the host socket; the broker Compose must use this numeric GID (not the docker group name).",\n'
printf '    "candidate_percival_path is the F0 default; the operator may move it by exporting PERCIVAL_DATA_DIR before running the script.",\n'
printf '    "PERCIVAL_SENSITIVE_PATHS accepts a colon-separated list; the broker mount policy must refuse to mount any of these (or their children) into a managed MCP container."\n'
printf '  ],\n'
printf '  "inventory_at": "%s"\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
printf '}\n'
