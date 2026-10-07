#!/usr/bin/env bash
# Percival F0 — disposable environment validation script.
#
# Replays the F0 measurements against a local Docker daemon.  This is the
# F0 deliverable that the plan asks for before F1 begins:
#   - bind-recursive=disabled + R/W /host and the socket is absent
#   - /var/lib/docker data-root is covered and its contents are not
#     visible to the MCP container
#   - a custom mount cannot re-introduce /var/run/docker.sock via
#     /host/var/run unless the broker accepts it
#   - the gateway container does not see /var/run/docker.sock
#   - the gateway can call the broker on the shared 127.0.0.1 only with
#     a valid token; the broker rejects calls that would expose the
#     daemon control plane
#
# This script does NOT touch the real VPS, does NOT install anything, and
# leaves no persistent state.  All containers are --rm; the broker image
# is built in /tmp and is rebuilt each run.
#
# Usage:
#   scripts/percival-f0-validate.sh
#
# Optional environment:
#   PERCIVAL_BROKER_PORT     default 18072
#   PERCIVAL_BROKER_TOKEN    default "percival-f0-test-token"
#   PERCIVAL_MCP_IMAGE       default "percival-weather-mcp:audit"
#   PERCIVAL_DOCKER_SOCK     default /var/run/docker.sock
#
# Exit codes:
#   0   all checks passed
#   1   unexpected failure
#   2   at least one security check failed (printed in summary)

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PORT="${PERCIVAL_BROKER_PORT:-18072}"
TOKEN="${PERCIVAL_BROKER_TOKEN:-percival-f0-test-token}"
MCP_IMAGE="${PERCIVAL_MCP_IMAGE:-percival-weather-mcp:audit}"
DOCKER_SOCK="${PERCIVAL_DOCKER_SOCK:-/var/run/docker.sock}"
DOCKER_GID="$(stat -c %g "${DOCKER_SOCK}" 2>/dev/null || echo 0)"

BROKER_DIR="$(mktemp -d -t percival-f0-broker-XXXXXX)"
trap 'rm -rf "${BROKER_DIR}"; docker rm -f $(docker ps -q --filter "label=percival-f0=1" 2>/dev/null) 2>/dev/null || true; docker image rm percival-f0-broker:dev 2>/dev/null || true' EXIT

# Build a minimal broker image that respects our ENTRYPOINT and argv.
cp "${REPO_ROOT}/scripts/percival_mcp_broker_f0.py" "${BROKER_DIR}/broker.py"
cat > "${BROKER_DIR}/Dockerfile" <<'EOF'
FROM python:3.12-slim
COPY broker.py /broker.py
EXPOSE 18072
ENTRYPOINT ["python", "-u", "/broker.py"]
EOF

note() { printf '\n=== %s ===\n' "$*"; }
fail_count=0
record() {
  local name="$1" expected="$2" actual="$3"
  if [[ "${expected}" == "${actual}" ]]; then
    printf '  [ok]   %-50s expected=%s actual=%s\n' "${name}" "${expected}" "${actual}"
  else
    printf '  [FAIL] %-50s expected=%s actual=%s\n' "${name}" "${expected}" "${actual}"
    fail_count=$((fail_count + 1))
  fi
}

note "Build broker image"
docker build -q -t percival-f0-broker:dev "${BROKER_DIR}" >/dev/null
echo "  percival-f0-broker:dev ready"

note "A1: bind-recursive=enabled exposes the socket (sanity baseline)"
out_a1="$(docker run --rm --pull=never --network=none --cap-drop=ALL \
  --security-opt=no-new-privileges --user 0 \
  --mount type=bind,src=/,dst=/host,bind-recursive=enabled \
  --entrypoint python "${MCP_IMAGE}" -c '
import os
for p in ("/host/run/docker.sock", "/host/var/run/docker.sock", "/host/proc/1/root/run/docker.sock"):
    print(p, os.path.exists(p))')"
echo "${out_a1}"
# The first awk match for /run/docker.sock is /host/run/docker.sock.
socket_visible="$(echo "${out_a1}" | head -1 | awk '{print $2}')"
if [[ "${socket_visible}" == "True" ]]; then
  record "A1 socket visible with bind-recursive=enabled (negative control)" "True" "True"
else
  record "A1 socket visible with bind-recursive=enabled (negative control)" "True" "${socket_visible}"
fi

note "A2: bind-recursive=disabled hides the socket and /proc"
out_a2="$(docker run --rm --pull=never --network=none --cap-drop=ALL \
  --security-opt=no-new-privileges --user 0 \
  --mount type=bind,src=/,dst=/host,bind-recursive=disabled \
  --entrypoint python "${MCP_IMAGE}" -c '
import os
for p in ("/host/run/docker.sock", "/host/var/run/docker.sock", "/host/proc/1/root/run/docker.sock", "/host/var/lib/docker/containers"):
    print(p, os.path.exists(p))')"
echo "${out_a2}"
a2_socket="$(echo "${out_a2}" | awk '/run\/docker.sock/ {print $2}')"
a2_var_run="$(echo "${out_a2}" | awk '/\/host\/var\/run\/docker.sock/ {print $2}')"
a2_proc="$(echo "${out_a2}" | awk '/\/host\/proc/ {print $2}')"
a2_dataroot="$(echo "${out_a2}" | awk '/\/host\/var\/lib\/docker/ {print $2}')"
# the awk on /host/run/docker.sock also matches /host/var/run/docker.sock; pull the first occurrence
a2_socket_first="$(echo "${out_a2}" | head -1 | awk '{print $2}')"
record "A2 /host/run/docker.sock absent"      "False" "${a2_socket_first}"
record "A2 /host/var/run/docker.sock absent"  "False" "${a2_var_run}"
record "A2 /host/proc/.../run absent"         "False" "${a2_proc}"
record "A2 /host/var/lib/docker/containers present (needs tmpfs cover)" "True" "${a2_dataroot}"

note "A3: covering /var/lib/docker with tmpfs hides the data-root"
out_a3="$(docker run --rm --pull=never --network=none --cap-drop=ALL \
  --security-opt=no-new-privileges --user 0 \
  --mount type=bind,src=/,dst=/host,bind-recursive=disabled \
  --tmpfs /host/var/lib/docker:rw,noexec,nosuid,nodev,mode=0700 \
  --entrypoint python "${MCP_IMAGE}" -c '
import os
for p in ("/host/run/docker.sock", "/host/var/lib/docker/containers"):
    print(p, os.path.exists(p))')"
echo "${out_a3}"
a3_socket="$(echo "${out_a3}" | awk '/run\/docker.sock/ {print $2}')"
a3_dataroot="$(echo "${out_a3}" | awk '/\/host\/var\/lib\/docker/ {print $2}')"
record "A3 socket still absent"                "False" "${a3_socket}"
record "A3 /host/var/lib/docker/containers covered" "False" "${a3_dataroot}"

note "A4: R/W root, R/W /host, write to /host/tmp succeeds"
out_a4="$(docker run --rm --pull=never --network=none --cap-drop=ALL \
  --security-opt=no-new-privileges --user 0 \
  --mount type=bind,src=/,dst=/host,bind-recursive=disabled \
  --tmpfs /host/var/lib/docker:rw,noexec,nosuid,nodev,mode=0700 \
  --entrypoint python "${MCP_IMAGE}" -c '
import os
write = "/host/tmp/percival-f0-write"
try:
    with open(write, "w") as f: f.write("ok\n")
    print("write_ok", os.path.exists(write))
    os.unlink(write)
except OSError as e:
    print("write_err", type(e).__name__, e.errno)')"
echo "${out_a4}"
a4_write="$(echo "${out_a4}" | awk '/write_ok/ {print $2}')"
record "A4 MCP can write a file under /host" "True" "${a4_write}"

note "A5: a custom mount CAN reintroduce the socket (broker must reject it)"
out_a5="$(docker run --rm --pull=never --network=none --cap-drop=ALL \
  --security-opt=no-new-privileges --user 0 \
  --mount type=bind,src=/,dst=/host,bind-recursive=disabled \
  --tmpfs /host/var/lib/docker:rw,noexec,nosuid,nodev,mode=0700 \
  --mount type=bind,src=/var/run,dst=/host/var/run \
  --entrypoint python "${MCP_IMAGE}" -c '
import os
print("reintroduced", os.path.exists("/host/var/run/docker.sock"))')"
echo "${out_a5}"
a5_reintro="$(echo "${out_a5}" | awk '{print $2}')"
record "A5 without broker gate, custom mount reintroduces the socket" "True" "${a5_reintro}"

note "B1: sidecar loopback without token must be rejected"
GATEWAY_CID="$(docker run -d --rm --pull=never --cap-drop=ALL \
  --security-opt=no-new-privileges --entrypoint python "${MCP_IMAGE}" -c 'import time; time.sleep(600)')"
docker run -d --rm --label percival-f0=1 --pull=never --cap-drop=ALL \
  --security-opt=no-new-privileges --network "container:${GATEWAY_CID}" \
  -e PERCIVAL_BROKER_TOKEN="${TOKEN}" -e HOST_DOCKER_SOCK="${DOCKER_SOCK}" \
  -e DOCKER_GID="${DOCKER_GID}" -v "${DOCKER_SOCK}:${DOCKER_SOCK}" \
  percival-f0-broker:dev --port "${PORT}" --token "${TOKEN}" >/dev/null
sleep 0.6

probe_anon="$(docker exec "${GATEWAY_CID}" python -c "
import urllib.request, urllib.error
B='http://127.0.0.1:${PORT}'
try:
    with urllib.request.urlopen(B+'/v1/ping', timeout=3) as r: print('ok', r.status)
except urllib.error.HTTPError as e: print('reject', e.code)")"
echo "${probe_anon}"
anon_code="$(echo "${probe_anon}" | awk '{print $2}')"
record "B1 broker rejects unauthenticated /v1/ping" "reject 401" "${probe_anon}"

probe_token="$(docker exec "${GATEWAY_CID}" python -c "
import urllib.request
r = urllib.request.Request('http://127.0.0.1:${PORT}/v1/ping', headers={'Authorization':'Bearer ${TOKEN}'})
with urllib.request.urlopen(r, timeout=3) as x: print('ok', x.status, x.read().decode('utf-8')[:120])")"
echo "${probe_token}"
ok_code="$(echo "${probe_token}" | awk '{print $2}')"
record "B1 broker accepts /v1/ping with valid token" "200" "${ok_code}"

sock_in_gw="$(docker exec "${GATEWAY_CID}" python -c 'import os; print(os.path.exists("/var/run/docker.sock"))')"
record "B1 gateway container has no /var/run/docker.sock" "False" "${sock_in_gw}"

note "B2: exec-tool simulation joining the gateway namespace cannot run containers without token"
exec_sim="$(docker run --rm --pull=never --cap-drop=ALL \
  --security-opt=no-new-privileges --network "container:${GATEWAY_CID}" \
  --entrypoint python "${MCP_IMAGE}" -c "
import urllib.request, urllib.error, json
B='http://127.0.0.1:${PORT}'
data = json.dumps({'container_image':'alpine:3.20','entrypoint':['echo','hi']}).encode()
r = urllib.request.Request(B + '/v1/run', data=data, headers={'Content-Type':'application/json'})
try:
    with urllib.request.urlopen(r, timeout=3) as x: print('ok', x.status)
except urllib.error.HTTPError as e: print('reject', e.code)")"
echo "${exec_sim}"
exec_code="$(echo "${exec_sim}" | awk '{print $2}')"
record "B2 exec-tool without token is rejected by broker" "reject 401" "${exec_sim}"

note "B3: token holder can request a denied command and is blocked by the broker"
denied="$(docker exec "${GATEWAY_CID}" python -c "
import urllib.request, urllib.error, json
B='http://127.0.0.1:${PORT}'
T='${TOKEN}'
data = json.dumps({'container_image':'alpine:3.20','entrypoint':['ls','/host/var/run']}).encode()
r = urllib.request.Request(B + '/v1/run', data=data, headers={'Content-Type':'application/json','Authorization':f'Bearer {T}'})
try:
    with urllib.request.urlopen(r, timeout=3) as x: print('ok', x.status, x.read().decode('utf-8')[:120])
except urllib.error.HTTPError as e: print('reject', e.code, e.read().decode('utf-8','replace')[:120])")"
echo "${denied}"
# The broker policy fires BEFORE the docker run; we expect HTTP 400 with
# an "error" field naming the rejected marker.  Strip the body and keep
# only the status code for the assertion so changes to error wording do
# not fail the check.
denied_code="$(echo "${denied}" | awk '{print $2}')"
if [[ "${denied_code}" == "400" || "${denied_code}" == "401" || "${denied_code}" == "403" ]]; then
  printf '  [ok]   %-50s expected=reject actual=%s\n' "B3 broker rejects command referencing /host/var/run" "${denied_code}"
else
  printf '  [FAIL] %-50s expected=reject actual=ok %s\n' "B3 broker rejects command referencing /host/var/run" "${denied_code}"
  fail_count=$((fail_count + 1))
fi

denied_mount="$(docker exec "${GATEWAY_CID}" python -c "
import urllib.request, urllib.error, json
B='http://127.0.0.1:${PORT}'
T='${TOKEN}'
data = json.dumps({'container_image':'alpine:3.20','entrypoint':['ls','/'],'mounts':['type=bind,src=/var/run/docker.sock,dst=/var/run/docker.sock']}).encode()
r = urllib.request.Request(B + '/v1/run', data=data, headers={'Content-Type':'application/json','Authorization':f'Bearer {T}'})
try:
    with urllib.request.urlopen(r, timeout=3) as x: print('ok', x.status, x.read().decode('utf-8')[:120])
except urllib.error.HTTPError as e: print('reject', e.code, e.read().decode('utf-8','replace')[:120])")"
echo "${denied_mount}"
denied_mount_code="$(echo "${denied_mount}" | awk '{print $2}')"
if [[ "${denied_mount_code}" == "400" || "${denied_mount_code}" == "401" || "${denied_mount_code}" == "403" ]]; then
  printf '  [ok]   %-50s expected=reject actual=%s\n' "B3 broker rejects mount of /var/run/docker.sock" "${denied_mount_code}"
else
  printf '  [FAIL] %-50s expected=reject actual=ok %s\n' "B3 broker rejects mount of /var/run/docker.sock" "${denied_mount_code}"
  fail_count=$((fail_count + 1))
fi

note "Summary"
if [[ "${fail_count}" -eq 0 ]]; then
  echo "  all checks passed"
  docker rm -f "${GATEWAY_CID}" 2>/dev/null || true
  exit 0
else
  echo "  ${fail_count} check(s) FAILED — see [FAIL] lines above"
  docker rm -f "${GATEWAY_CID}" 2>/dev/null || true
  exit 2
fi
