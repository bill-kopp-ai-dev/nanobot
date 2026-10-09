#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "$0")/.." && pwd)"
fixture="$(mktemp -d "${RUNNER_TEMP:-/tmp}/percival-f5-${GITHUB_RUN_ID:-local}-XXXXXX")"
fixture_suffix="${fixture##*-}"
project="percival-f5-${GITHUB_RUN_ID:-local}-${fixture_suffix,,}"
cd "$repo_root"
export HOME="$fixture/home"
compose=(docker compose -p "$project" -f "$repo_root/docker-compose.yml")
api_key='ci-api-key-not-a-secret'
provider_key='ci-provider-key-not-a-secret'
webui_token_secret='ci-webui-token-issue-secret'
webui_token_file="$fixture/webui-token-issue"
export PERCIVAL_STATE_HOST_PATH="$HOME/.nanobot"
export PERCIVAL_DOCKER_SOCKET_GID=0
export PERCIVAL_BROKER_TOKEN_GID=1000
export PERCIVAL_BROKER_TOKEN_HOST_PATH="$HOME/.nanobot/broker-token"
export PERCIVAL_DOCKER_GATEWAY_TOKEN_ISSUE_SECRET_FILE="$webui_token_file"
export PERCIVAL_IMAGE_REVISION="${GITHUB_SHA:-$(git -C "$repo_root" rev-parse HEAD)}"
export PERCIVAL_IMAGE_VERSION="$(python3 -c 'import tomllib; print(tomllib.load(open("pyproject.toml", "rb"))["project"]["version"])')"

cleanup() {
    docker compose -p "$project" -f "$repo_root/docker-compose.yml" \
        -f "$repo_root/docker-compose.mcp-broker.yml" down --remove-orphans >/dev/null 2>&1 || true
    rm -rf "$fixture"
}
trap cleanup EXIT

mkdir -p "$HOME/.nanobot"
umask 077
printf '%s' "$webui_token_secret" > "$webui_token_file"
if [[ "$(id -u)" != 1000 ]]; then
    sudo chown 1000:1000 "$webui_token_file"
fi

"${compose[@]}" config --quiet
docker compose -p "$project" -f docker-compose.yml -f docker-compose.mcp-broker.yml config --quiet

# API must refuse the network bind before a key is configured.
printf '{"api":{"api_key":""}}\n' > "$HOME/.nanobot/config.json"
set +e
missing_key_output=$("${compose[@]}" run --rm --no-deps nanobot-api 2>&1)
missing_key_status=$?
set -e
if [[ "$missing_key_status" -eq 0 ]] || ! grep -qi 'api_key' <<<"$missing_key_output"; then
    printf 'API without key did not fail closed (exit=%s)\n' "$missing_key_status" >&2
    exit 1
fi
if grep -Fq "$api_key" <<<"$missing_key_output"; then
    echo 'API failure output leaked the configured key' >&2
    exit 1
fi

printf '{"agents":{"defaults":{"model":"openai/gpt-4o-mini","provider":"openai"}},"providers":{"openai":{"api_key":"%s","api_base":"http://127.0.0.1:9/v1"}},"api":{"api_key":"%s"}}\n' \
    "$provider_key" "$api_key" > "$HOME/.nanobot/config.json"
"${compose[@]}" up --build -d --no-deps nanobot-gateway nanobot-api

wait_http() {
    local url="$1" expected="$2" code=''
    for _ in $(seq 1 60); do
        code=$(curl -sS -o /dev/null -w '%{http_code}' --max-time 2 "$url" 2>/dev/null || true)
        if [[ "$code" == "$expected" ]]; then
            printf '[smoke] %s -> HTTP %s\n' "$url" "$code"
            return 0
        fi
        sleep 1
    done
    printf 'expected HTTP %s from %s, got %s\n' "$expected" "$url" "$code" >&2
    "${compose[@]}" ps >&2 || true
    "${compose[@]}" logs --no-color --tail 80 2>&1 | \
        sed -e "s/${api_key}/[redacted]/g" \
            -e "s/${provider_key}/[redacted]/g" \
            -e "s/${webui_token_secret}/[redacted]/g" >&2 || true
    return 1
}

echo '[smoke] gateway readiness and WebUI'
wait_http http://127.0.0.1:18790/health 200
wait_http http://127.0.0.1:8765/ 200
echo '[smoke] API health and authentication'
wait_http http://127.0.0.1:8900/health 200
wait_http http://127.0.0.1:8900/v1/models 401
auth_code=$(curl -sS -o "$fixture/models.json" -w '%{http_code}' \
    -H "Authorization: Bearer $api_key" --max-time 5 http://127.0.0.1:8900/v1/models || true)
printf '[smoke] authenticated /v1/models -> HTTP %s\n' "$auth_code"
if [[ "$auth_code" != 200 ]]; then
    printf 'authenticated /v1/models expected 200, got %s: ' "$auth_code" >&2
    python3 -c 'import sys; print(open(sys.argv[1]).read()[:1000])' "$fixture/models.json" >&2
    exit 1
fi
python3 -c 'import json,sys; assert isinstance(json.load(open(sys.argv[1])), dict)' "$fixture/models.json"

for service in nanobot-gateway nanobot-api; do
    id=$("${compose[@]}" ps -q "$service")
    [[ -n "$id" ]]
    status=''
    for _ in $(seq 1 60); do
        status=$(docker inspect --format '{{.State.Health.Status}}' "$id")
        [[ "$status" == healthy ]] && break
        [[ "$status" == unhealthy ]] && break
        sleep 1
    done
    if [[ "$status" != healthy ]]; then
        printf '%s health did not become healthy (got %s)\n' "$service" "$status" >&2
        "${compose[@]}" logs --no-color --tail 80 2>&1 | \
            sed -e "s/${api_key}/[redacted]/g" \
                -e "s/${provider_key}/[redacted]/g" >&2 || true
        exit 1
    fi
    docker inspect --format '{{json .HostConfig.PortBindings}}' "$id" | \
        python3 -c 'import json,sys; p=json.load(sys.stdin); assert all(binding["HostIp"] in ("127.0.0.1", "::1") for bindings in p.values() for binding in bindings)'
done

echo 'Percival F5 gateway/WebUI/API compose conformance passed'
