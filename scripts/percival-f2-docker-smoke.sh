#!/usr/bin/env bash
# Disposable gateway + socket-owning broker smoke; local Engine 29 is opt-in
# and never counts as Engine 27 compatibility or deployment evidence.
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
DOCKER_ROOT="$(docker info --format '{{.DockerRootDir}}')"
SOCKET=/var/run/docker.sock
SOCKET_GID="${F2_DOCKER_SOCKET_GID:-$(stat -c %g "$SOCKET")}" # daemon socket GID
# The gateway's nanobot user has primary GID 1000; the broker joins that group
# to read the shared token without granting access to the daemon socket.
TOKEN_GID="${F2_BROKER_TOKEN_GID:-1000}"
[[ "$TOKEN_GID" == 1000 ]] || { echo "fixture requires the gateway's token GID 1000" >&2; exit 2; }
GATEWAY=percival-f2-smoke-gateway
BROKER=percival-f2-smoke-broker
PARENT="${F2_SMOKE_PARENT:-/home/bill/.positronic/runtime/tmp/opencode}"
[[ -d "$PARENT" ]] || { echo "approved scratch parent missing: $PARENT" >&2; exit 2; }
STATE="$(mktemp -d "$PARENT/percival-f2-state-XXXXXX")"
TOKEN_FILE="$STATE/mcp-docker/broker-token"
mkdir -p "$STATE/mcp-docker"
chmod 700 "$STATE" "$STATE/mcp-docker"
python3 -c 'import secrets,sys; open(sys.argv[1],"w").write(secrets.token_hex(32))' "$TOKEN_FILE"
if [[ "$EUID" == 0 || "$(id -g)" == "$TOKEN_GID" ]]; then
  chgrp "$TOKEN_GID" "$TOKEN_FILE"
else
  sudo chgrp "$TOKEN_GID" "$TOKEN_FILE"
fi
chmod 640 "$TOKEN_FILE"
# The gateway runs as UID 1000, while GitHub-hosted runners commonly create
# scratch paths as UID 1001. Give the fixture state to the gateway before the
# bind mount; keep the broker token's separate group/mode above.
if [[ "$EUID" == 0 || "$(id -u)" == 1000 ]]; then
  chown 1000:1000 "$STATE" "$STATE/mcp-docker"
else
  sudo chown 1000:1000 "$STATE" "$STATE/mcp-docker"
fi
WEATHER="$(docker image inspect percival-f2-weather:source-b5032f4 --format '{{.Id}}')"
OSM="$(docker image inspect percival-f2-osm:source-ca3c397 --format '{{.Id}}')"
WEATHER_OLD="$(docker image inspect percival-f2-weather:source-996302b --format '{{.Id}}')"
OSM_OLD="$(docker image inspect percival-f2-osm:source-5f80a41 --format '{{.Id}}')"
if ! docker image inspect alpine:3.20 --format '{{.Id}}' >/dev/null 2>&1; then docker pull alpine:3.20 >/dev/null; fi
FAIL_IMAGE="$(docker image inspect alpine:3.20 --format '{{.Id}}')"

cleanup() {
  docker rm -f "$BROKER" "$GATEWAY" >/dev/null 2>&1 || true
  docker rm -f percival-mcp-f2weather percival-mcp-f2osm >/dev/null 2>&1 || true
  if [[ "$EUID" == 0 || "$(id -u)" == 1000 ]]; then
    rm -rf "$STATE"
  else
    sudo rm -rf "$STATE"
  fi
}
trap cleanup EXIT
docker rm -f "$BROKER" "$GATEWAY" >/dev/null 2>&1 || true
docker rm -f percival-mcp-f2weather percival-mcp-f2osm >/dev/null 2>&1 || true

# Force the 29.x exception only on this local isolated harness.
PERCIVAL_DISPOSABLE_ENGINE29=1 docker run -d --name "$GATEWAY" \
  --cap-drop=ALL --cap-add=CHOWN --cap-add=SETUID --cap-add=SETGID \
  --security-opt=no-new-privileges \
  --mount "type=bind,src=$STATE,dst=/home/nanobot/.nanobot" \
  -e PERCIVAL_BROKER_TOKEN_GID="$TOKEN_GID" \
  -e F2_WEATHER_ID="$WEATHER" -e F2_OSM_ID="$OSM" -e F2_FAIL_IMAGE_ID="$FAIL_IMAGE" \
  -e F2_WEATHER_OLD_ID="$WEATHER_OLD" -e F2_OSM_OLD_ID="$OSM_OLD" \
  -e F2_STATE_HOST_PATH="$STATE" \
  "${F2_GATEWAY_IMAGE:-percival-f2-gateway:dev}" gateway --foreground >/dev/null

for _ in {1..40}; do
  [[ "$(docker inspect -f '{{.State.Running}}' "$GATEWAY")" == true ]] && break
  sleep 0.25
done
[[ "$(docker inspect -f '{{.State.Running}}' "$GATEWAY")" == true ]] || { docker logs "$GATEWAY" >&2; exit 1; }
docker exec --user 1000:1000 "$GATEWAY" python -c 'import os,stat; from pathlib import Path; s=Path("/home/nanobot/.nanobot/mcp-docker/broker-token").stat(); group=int(os.environ.get("PERCIVAL_BROKER_TOKEN_GID","65532")); mode=stat.S_IMODE(s.st_mode); print("token uid={} gid={} mode={:04o} expected_gid={} allowed={}".format(s.st_uid,s.st_gid,mode,group,s.st_uid in {os.getuid(),0} and not mode & 0o027 and (not mode & 0o040 or s.st_gid == group)))'

BROKER_ID="$(PERCIVAL_DISPOSABLE_ENGINE29=1 docker run -d --name "$BROKER" \
  --network "container:$GATEWAY" --cap-drop=ALL --security-opt=no-new-privileges \
  --user 65532:65532 --group-add "$SOCKET_GID" --group-add "$TOKEN_GID" \
  --read-only --tmpfs /tmp:rw,noexec,nosuid,nodev,mode=0700 \
  --mount "type=bind,src=$SOCKET,dst=/var/run/docker.sock" \
  --mount type=bind,src=/,dst=/host-inventory,readonly \
  --mount type=bind,src=/proc/1/mountinfo,dst=/run/host-mountinfo,readonly \
  --mount "type=bind,src=$TOKEN_FILE,dst=/run/secrets/percival-broker-token,readonly" \
  -e PERCIVAL_DISPOSABLE_ENGINE29=1 \
  -e PERCIVAL_GATEWAY_CONTAINER_NAME="$GATEWAY" \
  -e PERCIVAL_BROKER_TOKEN_FILE=/run/secrets/percival-broker-token \
  -e PERCIVAL_HOST_MOUNTINFO=/run/host-mountinfo \
  -e PERCIVAL_HOST_INVENTORY=/host-inventory \
  -e PERCIVAL_STATE_HOST_PATH="$STATE" \
  -e PERCIVAL_TOKEN_HOST_PATH="$TOKEN_FILE" \
  -e PERCIVAL_BROKER_TOKEN_GID="$TOKEN_GID" \
  "${F2_BROKER_IMAGE:-percival-mcp-broker:f2}")"

READY=0
for _ in {1..80}; do
  if docker logs "$BROKER" 2>&1 | grep -q "ready"; then READY=1; break; fi
  [[ "$(docker inspect -f '{{.State.Running}}' "$BROKER")" == true ]] || { docker logs "$BROKER" >&2; exit 1; }
  sleep 0.25
done
if [[ "$READY" != 1 ]]; then docker logs "$BROKER" >&2; exit 1; fi
docker exec "$GATEWAY" python -c 'import socket; s=socket.create_connection(("127.0.0.1",18081),3); s.close()' || {
  docker logs "$BROKER" >&2
  docker inspect "$BROKER" >&2
  exit 1
}

docker cp "$ROOT/tests/mcp_docker/smoke_driver.py" "$GATEWAY:/tmp/percival_f2_smoke.py"
docker exec --user 1000:1000 "$GATEWAY" python /tmp/percival_f2_smoke.py "$WEATHER" "$OSM"

BROKER_ENGINE="$(docker exec "$BROKER" /usr/bin/docker version --format '{{.Client.Version}}/{{.Server.Version}}')"
echo "Docker MCP smoke passed with broker Docker Client/Server $BROKER_ENGINE."
