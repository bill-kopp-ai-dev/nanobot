#!/usr/bin/env bash
# Local disposable F1 harness; never run on the deployment host as-is.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DOCKER_ROOT="$(docker info --format '{{.DockerRootDir}}')"
SOCK="/var/run/docker.sock"
GID="$(stat -c %g "$SOCK")"
IMAGE_WEATHER="$(docker image inspect --format '{{.Id}}' percival-f1-weather:source-b5032f4)"
IMAGE_OSM="$(docker image inspect --format '{{.Id}}' percival-f1-osm:source-ca3c397)"
WEATHER_PINNED="$(docker image inspect --format '{{json .RepoDigests}}' percival-f1-weather:source-b5032f4 | python3 -c 'import json,sys; print(next(d for d in json.load(sys.stdin) if d.startswith("localhost:5001/percival-f1/weather@sha256:")))')"
IMAGE_WEATHER_OLD="$(docker image inspect --format '{{.Id}}' percival-f1-weather:source-996302b)"
IMAGE_OSM_OLD="$(docker image inspect --format '{{.Id}}' percival-f1-osm:source-5f80a41)"
IMAGE_ALPINE="$(docker image inspect --format '{{.Id}}' alpine:3.20)"
TOKEN="$(python3 -c 'import secrets; print(secrets.token_hex(32))')"
[[ "$(findmnt -T /home -no TARGET)" == /home ]] || { echo 'Expected /home submount not found' >&2; exit 1; }
[[ "$(stat -c '%m' /home)" != "$(stat -c '%m' /)" ]] || { echo '/home is not a distinct mountpoint on this host' >&2; exit 1; }
STATE_DIR="$(mktemp -d -p /home/bill/.positronic/runtime/tmp/opencode percival-f1-XXXXXX)"
PROOF_DIR="$(mktemp -d -p /home/bill/.positronic/runtime/tmp/opencode percival-f1-proof-XXXXXX)"
GW=""
BROKER=""

cleanup() {
  docker ps -aq --filter label=percival-f1=1 | xargs -r docker rm -f >/dev/null 2>&1 || true
  if [[ -n "$BROKER" ]]; then docker rm -f "$BROKER" >/dev/null 2>&1 || true; fi
  if [[ -n "$GW" ]]; then docker rm -f "$GW" >/dev/null 2>&1 || true; fi
  docker image rm percival-f1-broker:dev 2>/dev/null || true
  rm -rf "$STATE_DIR"
  rm -rf "$PROOF_DIR"
}
trap cleanup EXIT

start_gateway() {
  GW="$(docker run -d --pull=never --name percival-f1-gateway --label percival-f1=gateway \
    --cap-drop=ALL --cap-add=CHOWN --cap-add=SETUID --cap-add=SETGID \
    --security-opt=no-new-privileges \
    --mount "type=bind,src=$STATE_DIR,dst=/home/nanobot/.nanobot" \
    --mount "type=bind,src=$ROOT/scripts/percival_mcp_f1_driver.py,dst=/f1_driver.py,readonly" \
    -e "F1_BROKER_TOKEN=$TOKEN" -e "F1_WEATHER_ID=$IMAGE_WEATHER" -e "F1_OSM_ID=$IMAGE_OSM" \
    -e "F1_WEATHER_OLD_ID=$IMAGE_WEATHER_OLD" -e "F1_OSM_OLD_ID=$IMAGE_OSM_OLD" \
    -e "F1_WEATHER_PINNED=$WEATHER_PINNED" \
    -e "F1_ALPINE_ID=$IMAGE_ALPINE" \
    percival-f1-gateway:dev gateway --foreground)"
  sleep 2
  if [[ "$(docker inspect -f '{{.State.Running}}' "$GW")" != true ]]; then
    docker logs "$GW" >&2
    exit 1
  fi
}

start_broker() {
  if [[ "$(docker inspect -f '{{.State.Running}}' "$GW")" != true ]]; then
    docker logs "$GW" >&2
    exit 1
  fi
  BROKER="$(docker run -d --pull=never --name percival-f1-broker --label percival-f1=broker \
    --network "container:$GW" --cap-drop=ALL --security-opt=no-new-privileges \
    --user 65532:65532 --group-add "$GID" --read-only \
    --tmpfs /tmp:rw,noexec,nosuid,nodev,mode=0700 \
    --mount "type=bind,src=$ROOT/scripts/percival_mcp_broker_f1.py,dst=/broker.py,readonly" \
    --mount type=bind,src=/usr/bin/docker,dst=/usr/bin/docker,readonly \
    --mount "type=bind,src=$SOCK,dst=/var/run/docker.sock" \
    -e "F1_BROKER_TOKEN=$TOKEN" -e "F1_DOCKER_ROOT=$DOCKER_ROOT" \
    -e "F1_HOME_SUBMOUNT=/home" -e "F1_PERSIST_ROOT=$STATE_DIR" \
    --entrypoint python percival-f1-weather:source-b5032f4 -u /broker.py)"
  for _ in {1..40}; do
    if docker logs "$BROKER" 2>&1 | grep -q 'f1 broker ready'; then return; fi
    sleep 0.25
  done
  docker logs "$BROKER" >&2
  exit 1
}

echo "F1 local: source images $IMAGE_WEATHER $IMAGE_OSM; Engine $(docker version --format '{{.Server.Version}}')"
start_gateway
start_broker
docker exec --user 1000:1000 "$GW" python /f1_driver.py run
docker exec --user 1000:1000 "$GW" python /f1_driver.py sdk
docker exec --user 1000:1000 "$GW" python /f1_driver.py probe
docker exec --user 1000:1000 "$GW" python /f1_driver.py reduce-host
for server in weather osm; do
  printf 'host-to-container\n' > "$PROOF_DIR/marker"
  docker exec -i --user 1000:1000 -e "F1_STATE_DIR=$STATE_DIR" \
    -e "F1_PROOF_PATH=/host$PROOF_DIR/marker" "percival-f1-$server" python - ro \
    < "$ROOT/scripts/percival_mcp_f1_access_probe.py"
  [[ "$(< "$PROOF_DIR/marker")" == 'host-to-container' ]]
done
docker exec --user 1000:1000 "$GW" python /f1_driver.py restore-host
for server in weather osm; do
  echo "root negative probe: $server"
  docker exec -i --user 0 -e "F1_STATE_DIR=$STATE_DIR" "percival-f1-$server" python - \
    < "$ROOT/scripts/percival_mcp_f1_access_probe.py"
  printf 'host-to-container\n' > "$PROOF_DIR/marker"
  docker exec -i --user 1000:1000 -e "F1_STATE_DIR=$STATE_DIR" \
    -e "F1_PROOF_PATH=/host$PROOF_DIR/marker" "percival-f1-$server" python - rw \
    < "$ROOT/scripts/percival_mcp_f1_access_probe.py"
  [[ "$(< "$PROOF_DIR/marker")" == 'container-to-host' ]]
  echo "$server host→MCP→host R/W verified on controlled file"
done

echo 'Recreating gateway and sidecar; retained config/audit under disposable state'
if [[ "$(docker inspect -f '{{.State.Running}}' "$GW")" != true ]]; then
  docker logs "$GW" >&2
  exit 1
fi
docker rm -f "$BROKER" "$GW" >/dev/null
BROKER=""; GW=""
# For F1 only: clean up owned MCP containers before a fresh broker starts.
docker ps -aq --filter label=percival-f1=1 | xargs -r docker rm -f >/dev/null
start_gateway
start_broker
docker exec --user 1000:1000 "$GW" python /f1_driver.py reconcile
docker exec --user 1000:1000 "$GW" python /f1_driver.py finish
docker exec --user 1000:1000 "$GW" python /f1_driver.py restore-checks
echo 'F1 local driver completed'
