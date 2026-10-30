"""Shared typed contract for gateway and the isolated Docker broker."""

from __future__ import annotations

import re
from pathlib import PurePosixPath
from typing import Literal

from pydantic import ConfigDict, Field, field_validator, model_validator

from nanobot.config_base import Base

SERVER_ID = re.compile(r"[a-z][a-z0-9-]{0,39}\Z")
IMAGE_ID = re.compile(r"sha256:[0-9a-f]{64}\Z")
REPO_DIGEST = re.compile(r"[a-z0-9][a-z0-9._:/-]{0,199}@sha256:[0-9a-f]{64}\Z")
ENV_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")
CATALOG_ID = re.compile(r"[a-z][a-z0-9-]{0,39}\Z")
SHA256 = re.compile(r"[a-f0-9]{64}\Z")
REDACTED_SECRET = "_REDACTED_MCP_ENV_SECRET"


class DockerImageSource(Base):
    model_config = ConfigDict(extra="forbid")

    type: Literal["local-image", "pinned-image"]
    reference: str

    @model_validator(mode="after")
    def check_reference(self) -> DockerImageSource:
        pattern = IMAGE_ID if self.type == "local-image" else REPO_DIGEST
        if not pattern.fullmatch(self.reference):
            raise ValueError("image must be a complete local ID or a locally present RepoDigest")
        return self


class DockerEnvValue(Base):
    model_config = ConfigDict(extra="forbid")

    kind: Literal["plain", "secret", "reference"]
    value: str = Field(repr=False)

    @model_validator(mode="after")
    def check_value(self) -> DockerEnvValue:
        if self.kind == "reference" and not re.fullmatch(r"\$\{[A-Za-z_][A-Za-z0-9_]*\}", self.value):
            raise ValueError("reference must be ${VAR}")
        if self.kind == "secret" and self.value == REDACTED_SECRET:
            raise ValueError("secret sentinel cannot be persisted")
        if "\x00" in self.value:
            raise ValueError("environment value contains NUL")
        return self


class DockerAppMount(Base):
    """Installation-specific host source mapped to a catalog-declared target."""

    model_config = ConfigDict(extra="forbid")

    source: str
    target: str
    read_only: bool
    kind: Literal["data", "cache", "secret"]

    @model_validator(mode="after")
    def check_mapping(self) -> DockerAppMount:
        source = PurePosixPath(self.source)
        target = PurePosixPath(self.target)
        reserved = ("/proc", "/sys", "/dev", "/run", "/var/run", "/host")
        if (not self.source.startswith("/") or str(source) != self.source or self.source == "/" or
            ".." in self.source.split("/") or not self.target.startswith("/") or
            str(target) != self.target or self.target == "/" or ".." in self.target.split("/") or
            any(self.target == path or self.target.startswith(path + "/") for path in reserved)):
            raise ValueError("app mount source/target must be canonical and target must not be a control path")
        return self


class TrustedCatalogConfig(Base):
    model_config = ConfigDict(extra="forbid")

    catalog_id: str
    root: str
    snapshot_sha256: str
    registered_at: str

    @model_validator(mode="after")
    def check_pin(self) -> TrustedCatalogConfig:
        if not CATALOG_ID.fullmatch(self.catalog_id):
            raise ValueError("invalid catalog ID")
        root = PurePosixPath(self.root)
        if not self.root.startswith("/") or str(root) != self.root or ".." in self.root.split("/"):
            raise ValueError("catalog root must be a canonical absolute path")
        if not SHA256.fullmatch(self.snapshot_sha256):
            raise ValueError("invalid catalog snapshot SHA-256")
        return self


class ManagedAppReference(Base):
    model_config = ConfigDict(extra="forbid")

    catalog_id: str
    snapshot_sha256: str
    app_id: str
    mcp_name: str
    version: str
    source_class: Literal["official", "community"]
    repository_digest: str
    platform: str
    manifest_sha256: str
    server_json_sha256: str
    consent_revision: int = Field(ge=0)
    consented_at: str

    @model_validator(mode="after")
    def check_identity(self) -> ManagedAppReference:
        if (not CATALOG_ID.fullmatch(self.catalog_id) or not SHA256.fullmatch(self.snapshot_sha256) or
            not SHA256.fullmatch(self.manifest_sha256) or not SHA256.fullmatch(self.server_json_sha256) or
            not REPO_DIGEST.fullmatch(self.repository_digest) or self.platform != "linux/amd64"):
            raise ValueError("invalid managed app release identity")
        return self


class DockerHostConfig(Base):
    model_config = ConfigDict(extra="forbid")

    persistent: bool = False
    # None = full host file access; [] = no host binds; a nonempty list =
    # selected paths. Covers are required only when a bind reaches them.
    mounts: list[str] | None = None
    # ``none`` keeps the container off every Docker network (and the host's
    # loopback, by inheritance); ``bridge`` enables the default bridge for
    # servers that must reach external APIs (AgentMail, Open-Meteo, OSM,
    # LLM providers). State and Docker data-root covers still apply, so the
    # container cannot reach the gateway's mcp-docker state or the Docker
    # daemon. The default stays ``none`` so a missing field is always safe.
    network: Literal["none", "bridge"] = "none"
    env: dict[str, DockerEnvValue] = Field(default_factory=dict)
    app_mounts: list[DockerAppMount] = Field(default_factory=list)

    @field_validator("mounts")
    @classmethod
    def check_mounts(cls, value: list[str] | None) -> list[str] | None:
        if value is not None and any(not p.startswith("/") or p == "/" or ".." in p.split("/") for p in value):
            raise ValueError("mount reductions must be absolute host paths")
        return value

    @field_validator("env")
    @classmethod
    def check_env(cls, value: dict[str, DockerEnvValue]) -> dict[str, DockerEnvValue]:
        if any(not ENV_NAME.fullmatch(key) for key in value):
            raise ValueError("invalid environment variable name")
        return value

    @field_validator("app_mounts")
    @classmethod
    def check_app_mounts(cls, value: list[DockerAppMount]) -> list[DockerAppMount]:
        targets = [mount.target for mount in value]
        for index, target in enumerate(targets):
            for other in targets[index + 1:]:
                if target == other or target.startswith(other.rstrip("/") + "/") or other.startswith(target.rstrip("/") + "/"):
                    raise ValueError("overlapping app mount targets")
        return value

    def broker_payload(self) -> dict[str, object]:
        """Keep schema-1 broker DTOs byte-compatible when app mounts are unused."""
        payload = self.model_dump(mode="json")
        if not self.app_mounts:
            payload.pop("app_mounts", None)
        return payload


class DockerServer(Base):
    model_config = ConfigDict(extra="forbid")

    server_id: str
    source: DockerImageSource
    revision: int = Field(default=0, ge=0)
    active: bool = True
    tools_disabled: list[str] = Field(default_factory=list)
    tools: list[str] = Field(default_factory=list)
    state: Literal[
        "installed", "configured-disabled", "starting", "running", "restarting",
        "updating", "stopped-persistent", "pending-broker", "image-missing",
        "config-invalid", "updating-failed",
    ] = "installed"

    @field_validator("server_id")
    @classmethod
    def check_id(cls, value: str) -> str:
        if not SERVER_ID.fullmatch(value):
            raise ValueError("invalid server_id")
        return value


class McpDockerConfig(Base):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1, 2] = 1
    revision: int = Field(default=0, ge=0)
    allow_remote_admin: bool = False
    servers: dict[str, DockerServer] = Field(default_factory=dict)
    configurations: dict[str, DockerHostConfig] = Field(default_factory=dict)
    installation_id: str | None = None
    trusted_catalogs: dict[str, TrustedCatalogConfig] = Field(default_factory=dict)
    app_releases: dict[str, ManagedAppReference] = Field(default_factory=dict)

    @model_validator(mode="after")
    def check_servers(self) -> McpDockerConfig:
        if set(self.servers) != set(self.configurations):
            raise ValueError("each server needs exactly one configuration")
        if any(key != server.server_id or not SERVER_ID.fullmatch(key) for key, server in self.servers.items()):
            raise ValueError("server ID and registry key disagree")
        if set(self.app_releases) - set(self.servers):
            raise ValueError("app release references must belong to installed servers")
        if self.schema_version == 1 and (
            self.installation_id is not None or self.trusted_catalogs or self.app_releases or
            any(host.app_mounts for host in self.configurations.values())
        ):
            raise ValueError("catalog features require MCP config schema version 2")
        if self.schema_version == 2 and (self.installation_id is None or not re.fullmatch(r"[0-9a-f-]{36}", self.installation_id)):
            raise ValueError("MCP config schema version 2 requires an installation ID")
        if any(key != catalog.catalog_id for key, catalog in self.trusted_catalogs.items()):
            raise ValueError("catalog ID and registry key disagree")
        return self
