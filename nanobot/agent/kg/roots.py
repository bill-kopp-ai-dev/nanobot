"""Per-request bundle root resolution and workspace capability boundary."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

from nanobot.agent.tools.context import current_request_context
from nanobot.config.kg import PercivalKgConfig
from nanobot.security.workspace_policy import resolve_allowed_path

BundleKind = Literal["cm", "ak"]

_BUNDLE_NAMES: dict[BundleKind, str] = {
    "cm": ".collective-memory",
    "ak": ".acquired-knowledge",
}
_ENV_ROOTS: dict[BundleKind, str] = {
    "cm": "COLLECTIVE_MEMORY_ROOT",
    "ak": "ACQUIRED_KNOWLEDGE_ROOT",
}


def bundle_root(kind: BundleKind, config: PercivalKgConfig, workspace: Path,
                *, use_request_context: bool = True) -> Path:
    """Resolve a root without searching the process CWD or parent directories.

    Legacy env overrides are intentional for migrated deployments. Call for
    every request so different WebUI workspaces never share a cached root.
    """
    request = current_request_context() if use_request_context else None
    active_workspace = (request.workspace if request and request.workspace else workspace).resolve()
    parent = os.environ.get(_ENV_ROOTS[kind]) or getattr(config, f"{kind}_root")
    candidate = Path(parent).expanduser() if parent else active_workspace
    if not candidate.is_absolute():
        candidate = active_workspace / candidate
    return (candidate / _BUNDLE_NAMES[kind]).resolve()


def allowed_bundle_root(
    kind: BundleKind,
    config: PercivalKgConfig,
    workspace: Path,
    *,
    restrict_to_workspace: bool,
    extra_read_roots: tuple[Path, ...] = (),
    extra_write_roots: tuple[Path, ...] = (),
    write: bool = False,
) -> Path:
    """Apply the same read/write capability policy as filesystem tools.

    A configured external root is *not* implicitly an authorization to escape
    a restricted workspace; the relevant capability must be granted explicitly.
    """
    root = bundle_root(kind, config, workspace)
    if not restrict_to_workspace:
        return root
    request = current_request_context()
    active_workspace = request.workspace if request and request.workspace else workspace
    return resolve_allowed_path(
        root,
        allowed_root=active_workspace,
        extra_allowed_roots=extra_write_roots if write else extra_read_roots,
    )
