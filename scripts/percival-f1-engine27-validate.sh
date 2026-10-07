#!/usr/bin/env bash
# Engine 27.x semantics in an isolated daemon. Requires local pinned images.
# Privileged dind has no host Docker socket, network, or published ports.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
NAME=percival-f1-engine27
DIN_DOCKER=docker:27.5.1-dind
DIN_DIGEST=docker@sha256:aa3df78ecf320f5fafdce71c659f1629e96e9de0968305fe1de670e0ca9176ce
[[ "$(docker image inspect --format '{{index .RepoDigests 0}}' "$DIN_DOCKER")" == "$DIN_DIGEST" ]]
[[ -z "$(docker ps -aq --filter "name=^/${NAME}$")" ]] || { echo 'F1 dind name occupied' >&2; exit 1; }
created=0
cleanup() {
  if [[ "$created" == 1 ]]; then docker rm -fv "$NAME" >/dev/null 2>&1 || true; fi
}
trap cleanup EXIT

# Use an anonymous, executable Docker data volume: Docker defaults tmpfs
# mounts to noexec and runc cannot launch images from a noexec data-root.
docker run -d --pull=never --name "$NAME" --label percival-f1=engine27 \
  --privileged --network none --mount type=volume,dst=/var/lib/docker \
  --entrypoint dockerd "$DIN_DOCKER" --host=unix:///var/run/docker.sock \
  --iptables=false --bridge=none --storage-driver=vfs >/dev/null
created=1
ready=0
for _ in {1..80}; do
  if client=$(docker exec "$NAME" docker version --format '{{.Client.Version}}' 2>/dev/null) \
      && server=$(docker exec "$NAME" docker version --format '{{.Server.Version}}' 2>/dev/null) \
      && [[ "$client" == "27.5.1" && "$server" == "27.5.1" ]]; then
    ready=1
    break
  fi
  sleep 0.25
done
[[ "$ready" == 1 ]] || { docker logs "$NAME" >&2; exit 1; }

docker save percival-f1-weather:source-b5032f4 percival-f1-osm:source-ca3c397 \
  | docker exec -i "$NAME" docker load
docker exec "$NAME" docker version --format 'Engine27 Client={{.Client.Version}} Server={{.Server.Version}}'
docker exec "$NAME" docker info --format 'Engine27 data-root={{.DockerRootDir}} driver={{.Driver}}'
python3 "$ROOT/scripts/percival_mcp_f1_engine27_probe.py"
docker exec "$NAME" docker run --rm --pull=never --network=none --cap-drop=ALL \
  --security-opt=no-new-privileges \
  --mount type=bind,src=/,dst=/host,bind-recursive=disabled \
  --tmpfs /host/run:rw,noexec,nosuid,nodev,mode=0700 \
  --tmpfs /host/var/lib/docker:rw,noexec,nosuid,nodev,mode=0700 \
  --user 0 --entrypoint python percival-f1-weather:source-b5032f4 -c \
  'import os; paths=("/host/run/docker.sock", "/host/var/run/docker.sock", "/host/var/lib/docker/containers"); assert all(not os.path.exists(p) for p in paths); print("Engine27 root direct-daemon paths absent")'
echo 'Engine27 disposable validation passed'
