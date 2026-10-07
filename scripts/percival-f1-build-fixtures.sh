#!/usr/bin/env bash
# Build F1 fixtures from clean commit trees; no checkout/worktree edits.
set -euo pipefail
WEATHER="${F1_WEATHER_REPO:-/home/bill/Projects/percival-weather-mcp}"
OSM="${F1_OSM_REPO:-/home/bill/Projects/percival-osm}"
REGISTRY=""
cleanup() {
  if [[ -n "$REGISTRY" ]]; then docker rm -f "$REGISTRY" >/dev/null 2>&1 || true; fi
  # Also clean up any pre-existing registry container from a previous failed run.
  docker ps -aq --filter name=^/percival-f1-local-registry$ | xargs -r docker rm -f >/dev/null 2>&1 || true
}
trap cleanup EXIT
if [[ -n "$(docker ps -aq --filter name=^/percival-f1-local-registry$)" ]]; then
  echo 'precival-f1-local-registry is already running' >&2
  exit 1
fi

build() {
  local repo="$1" sha="$2" tag="$3"
  [[ "$(git -C "$repo" rev-parse "$sha")" == "$sha" ]]
  echo "build $tag from $sha"
  git -C "$repo" archive "$sha" | docker build --pull=false -q -t "$tag" -
}

build "$WEATHER" b5032f4fe4f0e89cc49556b62725ba598fb1c181 percival-f1-weather:source-b5032f4
build "$WEATHER" 996302bbd5af08a3e17f9d5e292697c8d9c03912 percival-f1-weather:source-996302b
build "$OSM" ca3c3977fc124b649876900fc0c3ffb6fe7c87fb percival-f1-osm:source-ca3c397
build "$OSM" 5f80a41c977e4f044c76ccfa43c1d6efa73a1afa percival-f1-osm:source-5f80a41

REGISTRY="$(docker run -d --rm --name percival-f1-local-registry \
  --label percival-f1=registry -p 127.0.0.1:5001:5000 registry:2)"
docker tag percival-f1-weather:source-b5032f4 localhost:5001/percival-f1/weather:source-b5032f4
docker tag percival-f1-osm:source-ca3c397 localhost:5001/percival-f1/osm:source-ca3c397
docker push localhost:5001/percival-f1/weather:source-b5032f4
docker push localhost:5001/percival-f1/osm:source-ca3c397
docker image inspect --format '{{.Id}} {{json .RepoDigests}}' \
  localhost:5001/percival-f1/weather:source-b5032f4 \
  localhost:5001/percival-f1/osm:source-ca3c397
