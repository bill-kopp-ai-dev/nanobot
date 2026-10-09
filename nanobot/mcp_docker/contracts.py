"""Shared typed contract for gateway and the isolated Docker broker."""

from __future__ import annotations

import re
from typing import Literal

from pydantic import ConfigDict, Field, field_validator, model_validator

from nanobot.config_base import Base

SERVER_ID = re.compile(r"[a-z][a-z0-9-]{0,39}\Z")
IMAGE_ID = re.compile(r"sha256:[0-9a-f]{64}\Z")
REPO_DIGEST = re.compile(r"[a-z0-9][a-z0-9._:/-]{0,199}@sha256:[0-9a-f]{64}\Z")
ENV_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")
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

    schema_version: Literal[1] = 1
    revision: int = Field(default=0, ge=0)
    allow_remote_admin: bool = False
    servers: dict[str, DockerServer] = Field(default_factory=dict)
    configurations: dict[str, DockerHostConfig] = Field(default_factory=dict)

    @model_validator(mode="after")
    def check_servers(self) -> McpDockerConfig:
        if set(self.servers) != set(self.configurations):
            raise ValueError("each server needs exactly one configuration")
        if any(key != server.server_id or not SERVER_ID.fullmatch(key) for key, server in self.servers.items()):
            raise ValueError("server ID and registry key disagree")
        return self
