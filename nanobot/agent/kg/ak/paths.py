"""AK bundle discovery and safe resolution.

Mirrors ``percival-acquire-knowledge/paths.py`` but uses the Percival
configuration model and the unified ``BundleLayout`` from
``okf_bundle_core.paths``.  Resolution precedence:

1. environment variable ``ACQUIRED_KNOWLEDGE_ROOT`` (parent directory)
2. ``PercivalKgConfig.ak_root`` (parent directory, may be ``None``)
3. workspace effective at the request

The function never walks the CWD or parent directories; the plan forbids
implicit discovery in the multi-workspace gateway.  CLI compatibility
flows call this directly and may opt into discovery by passing an
explicit bundle_root argument.
"""

from __future__ import annotations

from pathlib import Path

from nanobot.agent.kg.vendor.okf_bundle_core.paths import (
    ACQUIRED_KNOWLEDGE,
    resolve_bundle_arg,
)

BUNDLE_NAME = ".acquired-knowledge"


class BundleNotFoundError(FileNotFoundError):
    """Dedicated to distinguish "bundle not found" from other IOErrors."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


def resolve_bundle_arg_path(value: str | Path) -> Path:
    """Normalize a ``--bundle-root`` CLI argument to the bundle itself."""
    return resolve_bundle_arg(value, bundle_name=BUNDLE_NAME, layout=ACQUIRED_KNOWLEDGE)


def find_bundle_root(
    *,
    env_parent: str | None = None,
    config_parent: str | Path | None = None,
    workspace: Path | None = None,
) -> Path:
    """Resolve the path of the ``.acquired-knowledge`` bundle.

    Precedence (no implicit CWD/parent walk when ``workspace`` is provided):

    1. ``env_parent`` (``ACQUIRED_KNOWLEDGE_ROOT``) — must point to the
       bundle's **parent** directory.
    2. ``config_parent`` (``PercivalKgConfig.ak_root``) — same convention.
    3. ``workspace`` — the bundle must already live at
       ``<workspace>/.acquired-knowledge``.

    The function always returns the bundle path, never the parent.
    """
    for parent in (env_parent, str(config_parent) if config_parent is not None else None):
        if not parent:
            continue
        parent_path = Path(parent).expanduser().resolve()
        bundle = (parent_path / BUNDLE_NAME).resolve()
        if bundle.is_dir():
            return bundle
        if env_parent is not None and parent is env_parent:
            raise BundleNotFoundError(
                f"ACQUIRED_KNOWLEDGE_ROOT={env_parent} but {BUNDLE_NAME}/ not found"
            )
        if config_parent is not None and parent == str(config_parent):
            raise BundleNotFoundError(
                f"kg.ak_root={config_parent} but {BUNDLE_NAME}/ not found"
            )

    if workspace is not None:
        bundle = (Path(workspace).expanduser().resolve() / BUNDLE_NAME).resolve()
        if bundle.is_dir():
            return bundle
        raise BundleNotFoundError(
            f"workspace={workspace} but {BUNDLE_NAME}/ not found"
        )

    raise BundleNotFoundError(
        f"could not find {BUNDLE_NAME}/; configure kg.ak_root or set ACQUIRED_KNOWLEDGE_ROOT"
    )


__all__ = ["BUNDLE_NAME", "BundleNotFoundError", "find_bundle_root", "resolve_bundle_arg_path"]
