"""Read-only, separately provisioned policy for catalog image acquisition."""

from __future__ import annotations

import json
import os
import re
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from nanobot.mcp_docker.contracts import REPO_DIGEST

_REPOSITORY = re.compile(
    r"docker\.io/[a-z0-9]+(?:[._-][a-z0-9]+)*/[a-z0-9]+(?:(?:[._-]|/)[a-z0-9]+)*\Z"
)
_PLATFORMS = frozenset({"linux/amd64", "linux/arm64"})


class AcquisitionPolicyError(ValueError):
    """The independently provisioned broker trust policy is absent or invalid."""


@dataclass(frozen=True)
class AcquisitionPolicy:
    allowed_repositories: frozenset[str]
    allowed_platforms: frozenset[str]

    def authorize(self, reference: str, platform: str) -> None:
        if not REPO_DIGEST.fullmatch(reference) or "@sha256:" not in reference:
            raise AcquisitionPolicyError("acquisition requires an exact OCI repository digest")
        repository = reference.split("@", 1)[0]
        if repository not in self.allowed_repositories:
            raise AcquisitionPolicyError("OCI repository is not allowed by broker policy")
        if platform not in self.allowed_platforms:
            raise AcquisitionPolicyError("OCI platform is not allowed by broker policy")


def load_acquisition_policy(path_value: str | None = None) -> AcquisitionPolicy:
    """Read a small root-provisioned file; never infer policy from the catalog."""
    raw_path = path_value or os.environ.get("PERCIVAL_BROKER_POLICY_FILE")
    if not raw_path:
        raise AcquisitionPolicyError("broker acquisition policy is not provisioned")
    path = Path(raw_path)
    try:
        if path.is_symlink() or not path.is_file():
            raise AcquisitionPolicyError("broker acquisition policy file is unavailable")
        info = path.stat()
        if not stat.S_ISREG(info.st_mode) or stat.S_IMODE(info.st_mode) & 0o222:
            raise AcquisitionPolicyError("broker acquisition policy must be a non-writable regular file")
        if info.st_size < 1 or info.st_size > 64 * 1024:
            raise AcquisitionPolicyError("broker acquisition policy has invalid size")
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise AcquisitionPolicyError("broker acquisition policy cannot be read") from exc
    if not isinstance(document, dict):
        raise AcquisitionPolicyError("broker acquisition policy has an unsupported shape")
    document_object = cast(dict[str, object], document)
    if set(document_object) != {
        "schema_version", "allowed_repositories", "allowed_platforms",
    }:
        raise AcquisitionPolicyError("broker acquisition policy has an unsupported shape")
    value = cast(dict[str, Any], document_object)
    repositories = value.get("allowed_repositories")
    platforms = value.get("allowed_platforms")
    if (value.get("schema_version") != 1 or not isinstance(repositories, list) or
        not isinstance(platforms, list)):
        raise AcquisitionPolicyError("broker acquisition policy values are invalid")
    repository_values = cast(list[object], repositories)
    platform_values = cast(list[object], platforms)
    if (any(not isinstance(item, str) or not _REPOSITORY.fullmatch(item) for item in repository_values) or
        any(not isinstance(item, str) or item not in _PLATFORMS for item in platform_values)):
        raise AcquisitionPolicyError("broker acquisition policy values are invalid")
    repository_names = cast(list[str], repository_values)
    platform_names = cast(list[str], platform_values)
    if (len(repository_names) != len(set(repository_names)) or
        len(platform_names) != len(set(platform_names))):
        raise AcquisitionPolicyError("broker acquisition policy values are invalid")
    return AcquisitionPolicy(frozenset(repository_names), frozenset(platform_names))
