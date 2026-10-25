#!/usr/bin/env python3
"""F4 structural contract checker for the Percival Docker Compose recipes.

The F4 phase of the Docker standardization plan defines a runtime contract for
every recipe in the fleet:

* **stdio** services: ``stdin_open: true``, no TTY, no published ports, no
  HTTP healthcheck, no persistent restart.
* **HTTP** services: a dedicated service/profile, an explicit transport
  variable, its own healthcheck, and a loopback host bind by default.
* **one init**: ``init: true`` from Compose, never a second init inside the
  image.
* **no fixed ``container_name``**: several instances of the same server may
  coexist under one daemon.
* **config/secrets**: a per-server environment prefix, an explicit
  ``required`` flag on every ``env_file``, safe defaults, and no credential
  materialized in the rendered ``docker compose config`` output.
* **persistence**: volumes only for data that must survive, with an explicit
  host path that must already exist, and an explicit UID/GID.

The checker reads two views of each recipe:

1. the **source** YAML, for the things Compose normalizes away (``env_file``
   entries, literal values, hardcoded container names);
2. the **rendered** ``docker compose config --format json``, for the
   effective configuration after interpolation and profile expansion.

It is read-only: it never starts a container, never mutates the live stack and
never prints a credential value -- a recipe that leaks one is reported by
variable name only.

The per-recipe expectations live in ``RECIPES`` below, so the whole fleet is
described in one place.

Usage:
    python scripts/check_compose_contract.py --repo . --name core
    python scripts/check_compose_contract.py --repo ../percival-osm --name osm
    python scripts/check_compose_contract.py --all --json
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:  # PyYAML is a nanobot dependency; the checker is also used standalone.
    import yaml
except ImportError:  # pragma: no cover - exercised only without PyYAML
    yaml = None  # type: ignore[assignment]

# Environment variable names that carry a credential. A rendered value for any
# of them is a leak: the rendered config is routinely pasted into logs, bug
# reports and inventories.
SECRET_NAME_RE = re.compile(r"(KEY|TOKEN|SECRET|PASSWORD|CREDENTIAL)", re.IGNORECASE)

# A variable that only names where a credential lives, or that carries a
# non-secret identifier, is not a credential.
SECRET_NAME_EXCLUSIONS = (
    "_FILE",
    "_PATH",
    "_HOST_PATH",
    "_ENV",
    "_GID",
    "_UID",
    "_ID",
    "_DIR",
)

# The transport variable may differ per server (``MODE`` is an explicitly
# documented adapter). Both spellings are accepted.
TRANSPORT_ENV_NAMES = ("MCP_TRANSPORT", "MODE")

STDIO_TRANSPORTS = {"stdio", "std"}

LOOPBACK_HOSTS = {"127.0.0.1", "::1", "localhost"}

# Values that never are a credential even when the name looks like one.
NON_SECRET_VALUE_RE = re.compile(r"^(\$\{[^}]*\}|[A-Za-z_][A-Za-z0-9_]*)$")

# --------------------------------------------------------------------------
# Per-recipe expectations
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class ServiceSpec:
    """Expected role of one service inside a recipe.

    ``restart`` states the expected policy explicitly, because the two HTTP
    shapes in the fleet differ on purpose: a long-running gateway restarts,
    while the API is an opt-in alternate runtime that must *not* loop when its
    mandatory credential is missing.

    ``transport`` is the transport value the service must select. ``None``
    means the server speaks exactly one transport (stdio) and needs no
    variable to say so.
    """

    role: str  # "stdio" | "http" | "core-http" | "core-cli" | "sidecar"
    transport: str | None = None  # required transport value for MCP servers
    restart: str = "none"  # "none" | "persistent"
    allow_no_read_only: bool = False
    require_user: bool = True
    # Host paths that are system mounts rather than data directories. They are
    # always present, so the "must exist" rule does not apply to them.
    system_mounts: tuple[str, ...] = ()


@dataclass(frozen=True)
class RecipeSpec:
    compose_files: tuple[str, ...]
    services: dict[str, ServiceSpec]
    # Prefixes owned by this server. A variable that carries server state must
    # use one of them, so two servers can share a daemon without colliding.
    env_prefixes: tuple[str, ...] = ()
    # Shared, transport-level variables every server may use.
    shared_env: tuple[str, ...] = ("MCP_TRANSPORT", "MODE", "PORT", "MCP_HOST", "PYTHONUNBUFFERED")
    # Variables that must exist for the recipe to render. The checker supplies
    # clearly synthetic placeholders so an opt-in overlay can be checked
    # without touching the operator's real host paths.
    required_vars: tuple[str, ...] = ()
    # Recipes whose services are only reachable through a profile.
    opt_in_overlay: bool = False


RECIPES: dict[str, RecipeSpec] = {
    "core": RecipeSpec(
        compose_files=("docker-compose.yml",),
        services={
            "nanobot-gateway": ServiceSpec(role="core-http", restart="persistent"),
            # The API is an alternate runtime over the same state, not a second
            # writer. `restart: "no"` is deliberate: without `api.api_key` the
            # runtime refuses a non-loopback bind, and a restart policy would
            # turn that into an endless crash loop.
            "nanobot-api": ServiceSpec(role="core-http", restart="none"),
            "nanobot-cli": ServiceSpec(role="core-cli", restart="none"),
        },
        env_prefixes=("PERCIVAL_", "NANOBOT_"),
    ),
    "core-broker": RecipeSpec(
        compose_files=("docker-compose.yml", "docker-compose.mcp-broker.yml"),
        services={
            "nanobot-gateway": ServiceSpec(role="core-http", restart="persistent"),
            "nanobot-api": ServiceSpec(role="core-http", restart="none"),
            "nanobot-cli": ServiceSpec(role="core-cli", restart="none"),
            # The broker shares the gateway network namespace and owns the only
            # Docker socket access in the stack. Its healthcheck is the
            # authenticated MCP probe, not an HTTP endpoint.
            "percival-mcp-broker": ServiceSpec(
                role="sidecar",
                restart="persistent",
                system_mounts=("/var/run/docker.sock", "/", "/proc/1/mountinfo"),
            ),
        },
        env_prefixes=("PERCIVAL_", "NANOBOT_"),
        required_vars=(
            "PERCIVAL_STATE_HOST_PATH",
            "PERCIVAL_BROKER_TOKEN_GID",
            "PERCIVAL_DOCKER_SOCKET_GID",
            "PERCIVAL_BROKER_TOKEN_HOST_PATH",
            "PERCIVAL_GATEWAY_CONTAINER_NAME",
        ),
        opt_in_overlay=True,
    ),
    "notes": RecipeSpec(
        compose_files=("docker-compose.yml",),
        # Notes is stdio-only: the image entrypoint starts the server directly,
        # so there is no transport variable to declare.
        services={"percival-notes": ServiceSpec(role="stdio")},
        env_prefixes=("PERCIVAL_NOTES_", "NOTES_"),
    ),
    "agentmail": RecipeSpec(
        compose_files=("docker-compose.yml",),
        services={"server": ServiceSpec(role="stdio")},
        env_prefixes=("AGENTMAIL_",),
    ),
    "weather": RecipeSpec(
        compose_files=("docker-compose.yml",),
        services={
            "percival-weather-stdio": ServiceSpec(role="stdio"),
            "percival-weather-http": ServiceSpec(role="http", transport="http", restart="persistent"),
        },
        env_prefixes=("MCP_WEATHER_",),
    ),
    "khan": RecipeSpec(
        compose_files=("docker-compose.yml",),
        # Khan is stdio-only: the CLI always speaks stdio.
        services={"server": ServiceSpec(role="stdio")},
        env_prefixes=("KHAN_",),
    ),
    "osm": RecipeSpec(
        compose_files=("docker-compose.yml",),
        services={
            "mcp-osm": ServiceSpec(role="stdio"),
            "mcp-osm-http": ServiceSpec(role="http", transport="streamable-http", restart="persistent"),
        },
        # `USER_AGENT`, `FROM_HEADER` and `ORS_API_KEY` are protocol-mandated
        # names (Nominatim usage policy and OpenRouteService); renaming them
        # would break the broker contract that already passes them.
        env_prefixes=("OSM_", "MCP_OSM_", "NOMINATIM_", "OVERPASS_"),
        shared_env=(
            "MCP_TRANSPORT",
            "MODE",
            "PORT",
            "MCP_HOST",
            "PYTHONUNBUFFERED",
            "USER_AGENT",
            "FROM_HEADER",
            "ORS_API_KEY",
            "ORS_REQUEST_TIMEOUT",
            "ALLOW_REMOTE_HTTP",
            "OSM_RESPONSE_MODE",
            "INSTRUCTION_ORIENTED_INTERPRETATION",
            "CAR_ONLY",
            "STATUS_INDICATORS",
            "OSM_HTTP_TIMEOUT_SECONDS",
            "OSM_HTTP_MAX_RETRIES",
            "OSM_HTTP_RETRY_BACKOFF_SECONDS",
            "OSM_HTTP_MAX_RESPONSE_BYTES",
            "OSM_HTTP_MAX_CONCURRENCY",
            "OSM_CACHE_TTL_SECONDS",
            "MCP_OSM_AUTH_TOKEN_ENV",
        ),
    ),
    "deep-research": RecipeSpec(
        compose_files=("docker-compose.yml",),
        services={
            "percival-deep-research-stdio": ServiceSpec(role="stdio"),
            "percival-deep-research-http": ServiceSpec(
                role="http", transport="streamable-http", restart="persistent"
            ),
            # Reverse proxy in front of the HTTP transport. It is an opt-in
            # profile that needs a reviewed, operator-provided configuration.
            "nginx": ServiceSpec(role="core-http", restart="persistent"),
        },
        env_prefixes=("INFERENCE_", "RETRIEVER", "BRAVE_"),
        shared_env=("MCP_TRANSPORT", "PORT", "MCP_HOST", "PYTHONUNBUFFERED"),
    ),
}

# --------------------------------------------------------------------------
# Findings
# --------------------------------------------------------------------------


@dataclass
class Finding:
    severity: str
    service: str
    rule: str
    detail: str

    def render(self) -> str:
        return f"[{self.severity}] {self.service}: {self.rule} - {self.detail}"


@dataclass
class Report:
    name: str
    repo: str
    findings: list[Finding] = field(default_factory=list)
    services_checked: int = 0

    @property
    def errors(self) -> list[Finding]:
        return [f for f in self.findings if f.severity == "error"]

    @property
    def warnings(self) -> list[Finding]:
        return [f for f in self.findings if f.severity == "warning"]

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "repo": self.repo,
            "services_checked": self.services_checked,
            "errors": [f.render() for f in self.errors],
            "warnings": [f.render() for f in self.warnings],
            "status": "fail" if self.errors else "pass",
        }


def _redact(text: str) -> str:
    """Strip anything that looks like an assigned value from a message.

    Compose error messages echo variable names, but a stray value would leak a
    credential into a log. Only the first line survives, and any ``name=value``
    pair is reduced to ``name``.
    """

    first = text.strip().splitlines()[0] if text.strip() else ""
    first = re.sub(r"([A-Za-z_][A-Za-z0-9_]*)=(\S+)", r"\1", first)
    return first[:300]


# --------------------------------------------------------------------------
# Loading
# --------------------------------------------------------------------------


def load_source(repo: Path, files: list[str]) -> dict[str, Any]:
    """Parse the recipe source files, merging Compose extension fields.

    Compose resolves ``<<: *anchor`` merges at render time; PyYAML does the
    same for mappings, so the source view matches the rendered one closely
    enough for the rules that only the source can answer.
    """

    merged: dict[str, Any] = {"services": {}}
    for name in files:
        path = repo / name
        if not path.exists():
            raise FileNotFoundError(f"recipe file not found: {path}")
        if yaml is None:  # pragma: no cover - only without PyYAML
            raise RuntimeError("PyYAML is required to inspect the recipe source")
        document = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        for service_name, service in (document.get("services") or {}).items():
            merged["services"].setdefault(service_name, {}).update(service or {})
    return merged


def render_config(repo: Path, files: list[str], env: dict[str, str]) -> dict[str, Any]:
    """Render the recipe with Compose and return the effective configuration."""

    cmd = ["docker", "compose"]
    for compose_file in files:
        cmd += ["-f", compose_file]
    # Render every profile: a service behind a profile is still part of the
    # contract, and a profile that hides a violation is not a fix.
    cmd += ["--profile", "*"]
    # A neutral env file keeps the operator's project `.env` out of the
    # interpolation, so the result depends on the recipe and not on local
    # state.
    cmd += ["--env-file", os.devnull]
    cmd += ["config", "--format", "json"]

    # Only a minimal environment is inherited: a shell export must not change
    # the rendered contract.
    clean_env = {k: v for k, v in os.environ.items() if k in ("PATH", "HOME", "DOCKER_HOST", "DOCKER_CONTEXT")}
    clean_env.update(env)

    proc = subprocess.run(
        cmd,
        cwd=repo,
        capture_output=True,
        text=True,
        env=clean_env,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"docker compose config failed in {repo}: {_redact(proc.stderr)}")
    return json.loads(proc.stdout)


# --------------------------------------------------------------------------
# Rules
# --------------------------------------------------------------------------


def _normalize_ports(ports: Any) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for entry in ports or []:
        if isinstance(entry, dict):
            result.append(entry)
        elif isinstance(entry, str):
            host_ip = None
            published = None
            target = None
            parts = entry.split(":")
            if len(parts) == 3:
                host_ip, published, target = parts
            elif len(parts) == 2:
                published, target = parts
            result.append(
                {
                    "host_ip": host_ip,
                    "published": published,
                    "target": target,
                    "mode": "ingress",
                    "protocol": "tcp",
                }
            )
    return result


def _transport_value(env: dict[str, Any]) -> tuple[str | None, Any]:
    upper = {str(k).upper(): v for k, v in (env or {}).items()}
    for key in TRANSPORT_ENV_NAMES:
        if key in upper:
            return key, upper[key]
    return None, None


def _is_secret_name(name: str) -> bool:
    upper = name.upper()
    # Inbox addresses are identifying account data even though the generic
    # `_ID` exclusion below allows harmless identifiers such as numeric GIDs.
    if upper.endswith("_INBOX_ID"):
        return True
    if upper.endswith(SECRET_NAME_EXCLUSIONS):
        return False
    return bool(SECRET_NAME_RE.search(upper))


def _env_file_keys(repo: Path, source: dict[str, Any]) -> set[str]:
    """Variable names contributed by the recipe's own ``env_file`` entries."""

    keys: set[str] = set()
    for service in (source.get("services") or {}).values():
        for entry in service.get("env_file") or []:
            path_value = entry.get("path") if isinstance(entry, dict) else entry
            if not path_value:
                continue
            path = Path(str(path_value)).expanduser()
            if not path.is_absolute():
                path = repo / path
            if not path.exists():
                continue
            for line in path.read_text(encoding="utf-8").splitlines():
                stripped = line.strip()
                if not stripped or stripped.startswith("#") or "=" not in stripped:
                    continue
                keys.add(stripped.split("=", 1)[0].strip())
    return keys


def check_service(
    *,
    service: str,
    rendered: dict[str, Any],
    source: dict[str, Any],
    expected: ServiceSpec,
    env_prefixes: tuple[str, ...],
    shared_env: tuple[str, ...],
    env_file_keys: set[str],
) -> list[Finding]:
    findings: list[Finding] = []

    def error(rule: str, detail: str) -> None:
        findings.append(Finding("error", service, rule, detail))

    # --- init: exactly one, owned by the launcher ------------------------
    if rendered.get("init") is not True:
        error("init", "service must declare 'init: true' (exactly one init, owned by the launcher)")

    # --- container identity ----------------------------------------------
    if rendered.get("container_name") or source.get("container_name"):
        error("container_name", "fixed container name blocks multiple instances of the same server")

    # --- restart policy ---------------------------------------------------
    restart = rendered.get("restart")
    if expected.restart == "persistent":
        if restart not in ("unless-stopped", "always", "on-failure"):
            error("restart", f"service must declare a persistent restart policy, got {restart!r}")
    elif restart not in (None, "no"):
        error("restart", f"service must not use a persistent restart policy, got {restart!r}")

    # --- hardening --------------------------------------------------------
    cap_drop = [str(c).upper() for c in (rendered.get("cap_drop") or [])]
    if "ALL" not in cap_drop:
        error("cap_drop", "service must drop all capabilities ('cap_drop: [ALL]')")
    security_opts = [str(s) for s in (rendered.get("security_opt") or [])]
    if not any("no-new-privileges" in s for s in security_opts):
        error("security_opt", "service must set 'no-new-privileges:true'")
    if rendered.get("read_only") is not True and not expected.allow_no_read_only:
        error("read_only", "service must run with a read-only root filesystem")

    # --- persistence identity ---------------------------------------------
    volumes = [v for v in (rendered.get("volumes") or []) if isinstance(v, dict)]
    user = str(rendered.get("user") or "")
    if expected.require_user and not re.fullmatch(r"\d+:\d+", user):
        error("user", "service must declare a numeric effective user as '<uid>:<gid>'")

    # --- transport surface ------------------------------------------------
    healthcheck = rendered.get("healthcheck")
    health_disabled = isinstance(healthcheck, dict) and healthcheck.get("disable") is True
    ports = _normalize_ports(rendered.get("ports"))

    if expected.role in ("http", "core-http"):
        if health_disabled or not healthcheck:
            error("healthcheck", "HTTP service must declare its own healthcheck")
        if not ports:
            error("ports", "HTTP service must publish a port")
        for port in ports:
            host_ip = port.get("host_ip")
            if host_ip is None:
                error(
                    "ports",
                    "published port must declare an explicit host bind; without it Docker "
                    "publishes on every interface",
                )
            elif str(host_ip) not in LOOPBACK_HOSTS:
                error(
                    "ports",
                    f"host bind {host_ip!r} is not loopback; external exposure needs an explicit opt-in",
                )
    else:
        if expected.role == "stdio":
            if rendered.get("stdin_open") is not True:
                error("stdin_open", "stdio service must set 'stdin_open: true'")
        # Compose omits `tty` from the rendered JSON when it is false, so the
        # contract is "never true", not "explicitly false".
        if rendered.get("tty") is True:
            error("tty", f"{expected.role} service must not allocate a TTY (stdout carries JSON-RPC)")
        if expected.role != "sidecar" and not health_disabled and healthcheck:
            error("healthcheck", f"{expected.role} service must not declare an HTTP healthcheck")
        if ports:
            error("ports", f"{expected.role} service must not publish a host port")

    # --- transport variable ------------------------------------------------
    env = rendered.get("environment") or {}
    transport_key, transport_value = _transport_value(env)
    if expected.transport is not None:
        # An HTTP service must state its transport explicitly.
        if transport_key is None:
            error("transport", "service must declare MCP_TRANSPORT (or a documented adapter such as MODE)")
        elif str(transport_value or "").strip().lower() != expected.transport:
            error(
                "transport",
                f"{transport_key} does not select the expected transport {expected.transport!r}",
            )
    elif expected.role == "stdio" and transport_key is not None:
        # A stdio-only server may declare the transport for clarity, but it
        # must never select an HTTP transport.
        if str(transport_value or "").strip().lower() not in STDIO_TRANSPORTS:
            error("transport", f"{transport_key} does not select the stdio transport")

    # --- environment prefix ------------------------------------------------
    allowed_prefixes = tuple(p for p in env_prefixes)
    allowed_shared = set(shared_env)
    for key in env:
        upper = str(key).upper()
        if upper in allowed_shared:
            continue
        if any(upper.startswith(prefix) for prefix in allowed_prefixes):
            continue
        error(
            "env_prefix",
            f"{key} does not use the {', '.join(allowed_prefixes) or 'server'} prefix; "
            "two servers sharing a daemon must not collide on variable names",
        )

    # --- secrets ------------------------------------------------------------
    for key, value in env.items():
        if not _is_secret_name(str(key)):
            continue
        text = "" if value is None else str(value)
        if not text.strip():
            continue
        if str(key).upper() in env_file_keys:
            error(
                "secret_in_config",
                f"{key} reaches the container through env_file and is materialized in "
                "'docker compose config'; deliver it as a mounted secret file instead",
            )
        elif NON_SECRET_VALUE_RE.match(text):
            # A bare reference such as "${OTHER}" is not a value.
            continue
        else:
            error(
                "secret_in_config",
                f"{key} is materialized in 'docker compose config'; deliver it as a mounted "
                "secret file when the server supports it",
            )

    # --- env_file ------------------------------------------------------------
    for entry in source.get("env_file") or []:
        if isinstance(entry, dict):
            if "required" not in entry:
                error("env_file", "every env_file entry must declare 'required: true|false' explicitly")
        else:
            error("env_file", "every env_file entry must use the long form with an explicit 'required' flag")

    # --- volumes --------------------------------------------------------------
    for volume in volumes:
        bind = volume.get("bind") or {}
        source = str(volume.get("source") or "")
        if source in expected.system_mounts:
            # A system mount (Docker socket, host inventory) is always present
            # and is not a data directory the daemon may create on demand.
            continue
        if volume.get("type") == "bind" and bind.get("create_host_path") is not False:
            error(
                "volumes",
                f"bind mount {volume.get('source')!r} must set 'create_host_path: false' so a missing "
                "data directory fails loudly instead of being created by the daemon",
            )

    return findings


def check_recipe(
    *,
    name: str,
    repo: Path,
    recipe: RecipeSpec,
    env: dict[str, str] | None = None,
) -> Report:
    report = Report(name=name, repo=str(repo))
    overrides = dict(env or {})
    for required in recipe.required_vars:
        if required.endswith("_GID"):
            synthetic = "23457" if "SOCKET" in required else "23456"
        elif required.endswith("_PATH"):
            synthetic = f"/tmp/f4-check/{required.lower()}"
        elif required.endswith("_NAME"):
            synthetic = "f4-check-gateway"
        else:
            synthetic = "f4-check"
        overrides.setdefault(required, synthetic)

    try:
        source = load_source(repo, list(recipe.compose_files))
    except (FileNotFoundError, RuntimeError) as exc:
        report.findings.append(Finding("error", name, "source", str(exc)))
        return report

    try:
        config = render_config(repo, list(recipe.compose_files), overrides)
    except RuntimeError as exc:
        report.findings.append(Finding("error", name, "compose_config", str(exc)))
        return report

    services = config.get("services") or {}
    report.services_checked = len(services)
    env_file_keys = _env_file_keys(repo, source)

    for service_name, rendered_spec in services.items():
        expected = recipe.services.get(service_name)
        if expected is None:
            report.findings.append(
                Finding(
                    "error",
                    service_name,
                    "undeclared_service",
                    "service is not declared in the F4 contract; add it to RECIPES or remove it",
                )
            )
            continue
        report.findings.extend(
            check_service(
                service=service_name,
                rendered=rendered_spec or {},
                source=(source.get("services") or {}).get(service_name) or {},
                expected=expected,
                env_prefixes=recipe.env_prefixes,
                shared_env=recipe.shared_env,
                env_file_keys=env_file_keys,
            )
        )

    for declared in recipe.services:
        if declared not in services:
            report.findings.append(
                Finding("error", declared, "missing_service", "service declared in the contract is absent from the recipe")
            )

    return report


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

# Default repository location of each recipe, relative to the nanobot checkout.
DEFAULT_REPO_ROOTS = {
    "core": ".",
    "core-broker": ".",
    "notes": "../percival-notes-mcp",
    "agentmail": "../percival-agentmail-mcp",
    "weather": "../percival-weather-mcp",
    "khan": "../percival-khan-calendar",
    "osm": "../percival-osm",
    "deep-research": "../percival-deep-research",
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repo", help="repository directory holding the recipe")
    parser.add_argument("--name", help=f"recipe name, one of: {', '.join(sorted(RECIPES))}")
    parser.add_argument("--all", action="store_true", help="check every known recipe")
    parser.add_argument("--set", action="append", default=[], metavar="KEY=VALUE", help="environment override")
    parser.add_argument("--json", action="store_true", help="emit JSON instead of text")
    args = parser.parse_args(argv)

    if shutil.which("docker") is None:
        print("docker is not available on PATH", file=sys.stderr)
        return 2
    if yaml is None:
        print("PyYAML is required to inspect the recipe source", file=sys.stderr)
        return 2

    env: dict[str, str] = {}
    for item in args.set:
        if "=" not in item:
            print(f"invalid --set value: {item!r}", file=sys.stderr)
            return 2
        key, value = item.split("=", 1)
        env[key] = value

    base = Path(__file__).resolve().parents[1]

    if args.all:
        targets = [(name, base / DEFAULT_REPO_ROOTS[name]) for name in sorted(RECIPES)]
    else:
        if not args.repo or not args.name:
            print("--repo and --name are required unless --all is given", file=sys.stderr)
            return 2
        if args.name not in RECIPES:
            print(f"unknown recipe {args.name!r}; known: {', '.join(sorted(RECIPES))}", file=sys.stderr)
            return 2
        targets = [(args.name, Path(args.repo).resolve())]

    reports: list[Report] = []
    for name, repo in targets:
        reports.append(check_recipe(name=name, repo=repo, recipe=RECIPES[name], env=env))

    if args.json:
        print(json.dumps([r.as_dict() for r in reports], indent=2))
    else:
        for report in reports:
            status = "FAIL" if report.errors else "PASS"
            print(f"{status} {report.name} ({report.repo}) - {report.services_checked} service(s) checked")
            for finding in report.findings:
                print("  " + finding.render())

    return 1 if any(r.errors for r in reports) else 0


if __name__ == "__main__":
    raise SystemExit(main())
