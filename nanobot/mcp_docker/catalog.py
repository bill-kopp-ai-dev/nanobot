"""Read and validate a pinned, local PBLabs MCP index snapshot.

Catalog contents are untrusted data. Only a byte-pinned catalog entry whose app
metadata is approved and whose package is an exact OCI digest can be returned
as an install candidate. This module never fetches URLs or mutates Docker.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, cast

import yaml
from jsonschema import Draft7Validator, Draft202012Validator

from nanobot.mcp_docker.contracts import (
    ENV_NAME,
    REPO_DIGEST,
    DockerAppMount,
    DockerEnvValue,
    DockerHostConfig,
)

APP_SCHEMA = Path(__file__).with_name("pblabs-mcp-app.schema.0.2.json")
CATALOG_SCHEMA = Path(__file__).with_name("catalog.schema.1.0.json")
SERVER_SCHEMA_ID = "https://static.modelcontextprotocol.io/schemas/2025-12-11/server.schema.json"
SERVER_SCHEMA_SHA256 = "3fba09590c99f61735d234822279f4223fab9e300c0a81e81c91ab62a4114de0"
NAME_PATTERN = re.compile(r"^[a-zA-Z0-9.-]+/[a-zA-Z0-9._-]+$")
SHA256_PATTERN = re.compile(r"^[a-f0-9]{64}$")


class CatalogError(ValueError):
    """A catalog snapshot is untrusted, stale, or violates the app contract."""


@dataclass(frozen=True)
class CatalogMount:
    target: str
    kind: Literal["data", "cache", "secret"]
    access: Literal["read-only", "read-write"]
    required: bool


@dataclass(frozen=True)
class CatalogEnvironmentVariable:
    name: str
    required: bool
    secret: bool


@dataclass(frozen=True)
class CatalogApp:
    app_id: str
    mcp_name: str
    version: str
    source_class: Literal["official", "community"]
    repository_digest: str
    platform: str
    needs_network: bool
    required_secrets: tuple[str, ...]
    environment_variables: tuple[CatalogEnvironmentVariable, ...]
    mounts: tuple[CatalogMount, ...]
    manifest_sha256: str
    server_json_sha256: str
    snapshot_sha256: str


def _read_relative(root: Path, relative: object, expected_hash: object, label: str) -> bytes:
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
        raise CatalogError(f"invalid {label} path")
    candidate = root / relative
    if candidate.is_symlink():
        raise CatalogError(f"symlink is not allowed for {label}")
    resolved = candidate.resolve(strict=True)
    if not resolved.is_relative_to(root) or not resolved.is_file():
        raise CatalogError(f"{label} path escapes the pinned index")
    content = resolved.read_bytes()
    if not isinstance(expected_hash, str) or not SHA256_PATTERN.fullmatch(expected_hash):
        raise CatalogError(f"missing {label} hash")
    if not hashlib.sha256(content).hexdigest() == expected_hash:
        raise CatalogError(f"{label} does not match its catalog hash")
    return content


def _object(value: object, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise CatalogError(f"{label} must be an object")
    return cast(dict[str, Any], value)


def _load_schema(path: Path, *, expected_hash: str | None = None) -> dict[str, Any]:
    try:
        raw = path.read_bytes()
        if expected_hash and hashlib.sha256(raw).hexdigest() != expected_hash:
            raise CatalogError(f"pinned schema checksum mismatch: {path.name}")
        schema = json.loads(raw)
    except (OSError, json.JSONDecodeError) as exc:
        raise CatalogError(f"cannot load pinned schema: {path.name}") from exc
    return _object(schema, f"{path.name} schema")


def _validate(validator: Any, value: Any, label: str) -> None:
    errors = sorted(validator.iter_errors(value), key=lambda error: list(map(str, error.absolute_path)))
    if errors:
        first = errors[0]
        location = ".".join(str(part) for part in first.absolute_path)
        suffix = f" at {location}" if location else ""
        raise CatalogError(f"invalid {label}{suffix}: {first.message}")


def load_catalog_snapshot(root_path: Path, expected_snapshot_sha256: str) -> tuple[CatalogApp, ...]:
    """Validate one read-only index directory pinned by `public/catalog.json` hash."""
    if not SHA256_PATTERN.fullmatch(expected_snapshot_sha256):
        raise CatalogError("expected catalog SHA-256 is invalid")
    if root_path.is_symlink():
        raise CatalogError("catalog root must not be a symlink")
    try:
        root = root_path.resolve(strict=True)
        raw_catalog = (root / "public" / "catalog.json").read_bytes()
    except OSError as exc:
        raise CatalogError("pinned local catalog is unavailable") from exc
    if not root.is_dir() or hashlib.sha256(raw_catalog).hexdigest() != expected_snapshot_sha256:
        raise CatalogError("catalog snapshot does not match its trusted SHA-256")
    try:
        catalog = json.loads(raw_catalog)
    except json.JSONDecodeError as exc:
        raise CatalogError("catalog snapshot is not valid JSON") from exc
    catalog_obj = _object(cast(object, catalog), "catalog")
    app_schema_pin = _object(catalog_obj.get("app_schema"), "app schema pin")
    server_schema_pin = _object(catalog_obj.get("server_schema"), "server schema pin")
    if app_schema_pin.get("version") != "0.2" or not isinstance(app_schema_pin.get("sha256"), str):
        raise CatalogError("unsupported PBLabs app schema pin")
    if (server_schema_pin.get("path") != "schemas/server.schema.2025-12-11.json" or
        server_schema_pin.get("sha256") != SERVER_SCHEMA_SHA256):
        raise CatalogError("unsupported MCP server schema pin")
    app_schema = _load_schema(APP_SCHEMA, expected_hash=cast(str, app_schema_pin["sha256"]))
    server_schema_bytes = _read_relative(
        root, server_schema_pin.get("path"), server_schema_pin.get("sha256"), "server schema",
    )
    try:
        server_schema = _object(cast(object, json.loads(server_schema_bytes)), "server schema")
    except json.JSONDecodeError as exc:
        raise CatalogError("pinned MCP server schema is malformed") from exc
    catalog_schema = _load_schema(CATALOG_SCHEMA)
    app_validator = Draft202012Validator(app_schema)
    app_validator.check_schema(app_schema)
    server_validator = Draft7Validator(server_schema)
    server_validator.check_schema(server_schema)
    catalog_validator = Draft202012Validator(catalog_schema)
    catalog_validator.check_schema(catalog_schema)
    _validate(catalog_validator, catalog_obj, "catalog snapshot")
    entries = cast(list[object], catalog_obj["entries"])
    result: list[CatalogApp] = []
    seen_ids: set[str] = set()
    seen_names: set[str] = set()
    for raw_entry in entries:
        entry = _object(raw_entry, "catalog entry")
        app_bytes = _read_relative(root, entry.get("manifest"), entry.get("manifest_sha256"), "app manifest")
        server_bytes = _read_relative(root, entry.get("server_json"), entry.get("server_json_sha256"), "server.json")
        _read_relative(root, entry.get("documentation"), entry.get("documentation_sha256"), "documentation")
        try:
            app_value = yaml.safe_load(app_bytes)
            server_value = json.loads(server_bytes)
        except (yaml.YAMLError, json.JSONDecodeError) as exc:
            raise CatalogError("catalog app data is malformed") from exc
        _validate(app_validator, app_value, "PBLabs app manifest")
        app = _object(app_value, "app manifest")
        server = _object(server_value, "server.json")
        _validate(server_validator, server, "MCP server.json")
        app_id = app.get("id")
        mcp_name = app.get("mcp_name")
        version = app.get("version")
        source_class = app.get("source_class")
        review = _object(app.get("review"), "app review")
        if (not isinstance(app_id, str) or not isinstance(mcp_name, str) or
            not NAME_PATTERN.fullmatch(mcp_name) or not isinstance(version, str) or
            source_class not in {"official", "community"} or
            review.get("status") != "approved" or review.get("approved_release") != version):
            raise CatalogError("catalog entry is not an approved app release")
        if app_id != entry.get("id") or source_class != entry.get("source_class") or version != entry.get("version"):
            raise CatalogError("catalog entry identity does not match its app manifest")
        if (app_id in seen_ids or mcp_name in seen_names or server.get("name") != mcp_name or
            server.get("version") != version or server.get("$schema") != SERVER_SCHEMA_ID):
            raise CatalogError("duplicate or inconsistent server identity")
        seen_ids.add(app_id)
        seen_names.add(mcp_name)
        packages = server.get("packages")
        if not isinstance(packages, list):
            raise CatalogError("server.json packages must be an array")
        package_items = cast(list[object], packages)
        if any(not isinstance(package, dict) for package in package_items):
            raise CatalogError("server.json package entries must be objects")
        package_objects = [cast(dict[str, Any], package) for package in package_items]
        oci_packages = [package for package in package_objects if package.get("registryType") == "oci"]
        if len(package_objects) != 1 or len(oci_packages) != 1:
            raise CatalogError("catalog app must have exactly one OCI package")
        image_ref = oci_packages[0].get("identifier")
        if not isinstance(image_ref, str) or not REPO_DIGEST.fullmatch(image_ref) or "@sha256:" not in image_ref:
            raise CatalogError("catalog OCI package must use an exact repository digest")
        transport = oci_packages[0].get("transport")
        if not isinstance(transport, dict) or cast(dict[str, object], transport).get("type") != "stdio":
            raise CatalogError("catalog app transport is not supported by this manager")
        raw_environment = oci_packages[0].get("environmentVariables", [])
        if not isinstance(raw_environment, list):
            raise CatalogError("catalog app environmentVariables must be an array")
        environment_variables: list[CatalogEnvironmentVariable] = []
        for raw_variable in cast(list[object], raw_environment):
            variable = _object(raw_variable, "server environment variable")
            name = variable.get("name")
            required = variable.get("isRequired", False)
            secret = variable.get("isSecret", False)
            if (not isinstance(name, str) or not ENV_NAME.fullmatch(name) or
                type(required) is not bool or type(secret) is not bool or "value" in variable):
                raise CatalogError("catalog app environment variable declaration is invalid")
            if any(existing.name == name for existing in environment_variables):
                raise CatalogError("catalog app environment variable names must be unique")
            environment_variables.append(CatalogEnvironmentVariable(name, required, secret))
        runtime = _object(app.get("runtime"), "runtime")
        if runtime.get("container") is not True or runtime.get("transport") != "stdio":
            raise CatalogError("catalog app runtime is not supported by this manager")
        compatibility = _object(app.get("compatibility"), "compatibility")
        products = compatibility.get("products")
        platforms = compatibility.get("platforms")
        if (not isinstance(products, list) or "percival" not in cast(list[object], products) or
            not isinstance(platforms, list) or "linux/amd64" not in cast(list[object], platforms)):
            raise CatalogError("catalog app has no supported linux/amd64 build")
        security = _object(app.get("security"), "security")
        app_config = _object(app.get("configuration"), "configuration")
        required_secrets = app_config.get("required_secrets")
        mounts_value = app.get("mounts")
        if not isinstance(required_secrets, list) or not isinstance(mounts_value, list):
            raise CatalogError("catalog app configuration is malformed")
        declared_environment = {item.name: item for item in environment_variables}
        for secret_name in cast(list[str], required_secrets):
            declaration = declared_environment.get(secret_name)
            if declaration is None or not declaration.secret or not declaration.required:
                raise CatalogError("PBLabs required_secrets must match required secret inputs in server.json")
        mounts = tuple(
            CatalogMount(
                target=cast(str, mount["target"]),
                kind=cast(Literal["data", "cache", "secret"], mount["kind"]),
                access=cast(Literal["read-only", "read-write"], mount["access"]),
                required=cast(bool, mount["required"]),
            )
            for mount in cast(list[dict[str, object]], mounts_value)
        )
        result.append(CatalogApp(
            app_id=app_id,
            mcp_name=mcp_name,
            version=version,
            source_class=cast(Literal["official", "community"], source_class),
            repository_digest=image_ref,
            platform="linux/amd64",
            needs_network=security.get("needs_network") is True,
            required_secrets=tuple(cast(list[str], required_secrets)),
            environment_variables=tuple(environment_variables),
            mounts=mounts,
            manifest_sha256=cast(str, entry["manifest_sha256"]),
            server_json_sha256=cast(str, entry["server_json_sha256"]),
            snapshot_sha256=expected_snapshot_sha256,
        ))
    return tuple(result)


def resolve_app_profile(
    app: CatalogApp,
    *,
    mount_sources: dict[str, str],
    environment: dict[str, DockerEnvValue],
    host_mounts: list[str] | None = None,
    network: str | None = None,
) -> DockerHostConfig:
    """Resolve draft metadata to a least-privilege installation-specific config."""
    requirements = {mount.target: mount for mount in app.mounts}
    if len(requirements) != len(app.mounts):
        raise CatalogError("app manifest has duplicate mount targets")
    unknown_targets = set(mount_sources) - set(requirements)
    missing_targets = {mount.target for mount in app.mounts if mount.required} - set(mount_sources)
    if unknown_targets or missing_targets:
        raise CatalogError("installation mount mappings do not match the app profile")
    resolved_mounts: list[DockerAppMount] = []
    for target, source in mount_sources.items():
        requirement = requirements[target]
        resolved_mounts.append(DockerAppMount(
            source=source,
            target=target,
            read_only=requirement.access == "read-only",
            kind=requirement.kind,
        ))
    environment_requirements = {item.name: item for item in app.environment_variables}
    if set(environment) - set(environment_requirements):
        raise CatalogError("installation environment contains undeclared app variables")
    missing_environment = {item.name for item in app.environment_variables if item.required} - set(environment)
    invalid_environment = [
        name for name, value in environment.items()
        if (environment_requirements[name].secret and value.kind != "secret") or
        (not environment_requirements[name].secret and value.kind == "secret") or
        (environment_requirements[name].required and not value.value)
    ]
    if missing_environment or invalid_environment:
        raise CatalogError("required app environment values must match their typed registry declarations")
    selected_network = network if network is not None else ("bridge" if app.needs_network else "none")
    if selected_network not in {"none", "bridge"} or (selected_network == "bridge" and not app.needs_network):
        raise CatalogError("installation network would exceed the app profile")
    if host_mounts is None:
        raise CatalogError("catalog apps require an explicit host access profile")
    try:
        return DockerHostConfig(
            mounts=host_mounts,
            network=cast(Literal["none", "bridge"], selected_network),
            env=environment,
            app_mounts=resolved_mounts,
        )
    except ValueError as exc:
        raise CatalogError("installation profile is invalid") from exc
