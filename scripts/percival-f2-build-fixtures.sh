#!/usr/bin/env bash
# Build the two reviewed MCP fixture versions and rollback images from immutable commits.
set -euo pipefail

WEATHER_REPO="${F2_WEATHER_REPO:-/home/bill/Projects/percival-weather-mcp}"
OSM_REPO="${F2_OSM_REPO:-/home/bill/Projects/percival-osm}"

build() {
  local repo="$1" sha="$2" tag="$3"
  git -C "$repo" cat-file -e "$sha^{commit}"
  printf 'building %s from %s\n' "$tag" "$sha"
  git -C "$repo" archive "$sha" | docker build --pull=false -q -t "$tag" -
}

build "$WEATHER_REPO" b5032f4fe4f0e89cc49556b62725ba598fb1c181 percival-f2-weather:source-b5032f4
build "$WEATHER_REPO" 996302bbd5af08a3e17f9d5e292697c8d9c03912 percival-f2-weather:source-996302b
build "$OSM_REPO" ca3c3977fc124b649876900fc0c3ffb6fe7c87fb percival-f2-osm:source-ca3c397
build "$OSM_REPO" 5f80a41c977e4f044c76ccfa43c1d6efa73a1afa percival-f2-osm:source-5f80a41
docker pull alpine:3.20
