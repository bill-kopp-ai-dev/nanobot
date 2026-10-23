#!/usr/bin/env bash
# Compatibility entrypoint: the I2 rehearsal supersedes the old host-port smoke.
set -euo pipefail
repo_root="$(git rev-parse --show-toplevel)"
version="$(python3 -c 'import sys,tomllib; print(tomllib.load(open(sys.argv[1],"rb"))["project"]["version"])' "$repo_root/pyproject.toml")"
revision="${GITHUB_SHA:-$(git rev-parse HEAD)}"
if ! git diff --quiet HEAD; then revision="${revision}-dirty"; fi
gateway="${PERCIVAL_GATEWAY_SMOKE_IMAGE:-percival-f5-gateway:fixture-$$}"
broker="${PERCIVAL_BROKER_SMOKE_IMAGE:-percival-f5-broker:fixture-$$}"
if [[ -z "${PERCIVAL_GATEWAY_SMOKE_IMAGE:-}" ]]; then
  docker build --platform linux/amd64 --build-arg VERSION="$version" \
    --build-arg GIT_SHA="$revision" -t "$gateway" -f "$repo_root/Dockerfile" "$repo_root"
fi
if [[ -z "${PERCIVAL_BROKER_SMOKE_IMAGE:-}" ]]; then
  docker build --platform linux/amd64 --build-arg VERSION="$version" \
    --build-arg GIT_SHA="$revision" -t "$broker" -f "$repo_root/Dockerfile.mcp-broker" "$repo_root"
fi
exec python3 "$repo_root/scripts/percival-i2-runtime-smoke.py" \
  --gateway-image "$gateway" --broker-image "$broker" \
  --scratch-parent "${RUNNER_TEMP:-${TMPDIR:-/tmp}}"
