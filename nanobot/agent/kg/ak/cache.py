"""AK diskcache wrapper with provider/model/preset-aware keys.

The cache must distinguish between (a) the same file processed by two
different runtimes and (b) the same file processed by the same runtime
across two different markitdown versions.  Without that separation we
would either return a stale caption when the model changes, or evict
the entire cache on every markitdown upgrade.

``diskcache`` is an optional dependency: this module imports it lazily
so the rest of the AK surface remains usable in environments where
multimodal caching is not desired.  ``cache_key`` is the cheap path
that callers always need; ``get_cache`` raises a clear error when
diskcache is missing.
"""

from __future__ import annotations

import hashlib
import importlib
import subprocess
import threading
from collections.abc import Callable
from pathlib import Path
from typing import Protocol, cast

from .parsers import resolve_markitdown_cli

_SIZE_LIMIT = int(1e9)  # 1GB
CACHE_SUBDIR = Path(".cache") / "percival-acquire-knowledge"

class CacheStore(Protocol):
    """Small runtime surface used from the optional diskcache backend."""

    def get(self, key: str) -> object | None: ...

    def set(self, key: str, value: object, *, expire: int) -> bool: ...

    def delete(self, key: str) -> bool: ...

    def close(self) -> None: ...


_by_root: dict[str, CacheStore] = {}
_registry_lock = threading.RLock()
_markitdown_version_cache: str | None = None


class CacheUnavailableError(RuntimeError):
    """Raised when ``diskcache`` is not installed in the active environment."""


def get_cache(root: Path) -> CacheStore:
    """Return the diskcache instance for the AK bundle at ``root``."""
    try:
        module = importlib.import_module("diskcache")
    except ImportError as exc:
        raise CacheUnavailableError(
            "diskcache is not installed; AK captioning will run without persistent cache"
        ) from exc
    factory = cast(Callable[..., CacheStore], getattr(module, "Cache"))
    key = str(root.resolve())
    with _registry_lock:
        cached = _by_root.get(key)
        if cached is not None:
            return cached
        cache_dir = root / CACHE_SUBDIR
        cache_dir.mkdir(parents=True, exist_ok=True)
        instance = factory(str(cache_dir), size_limit=_SIZE_LIMIT)
        _by_root[key] = instance
        return instance


def reset_cache(root: Path | None = None) -> None:
    if root is None:
        for instance in _by_root.values():
            try:
                instance.close()
            except Exception:
                pass
        _by_root.clear()
        return
    key = str(Path(root).resolve())
    instance = _by_root.pop(key, None)
    if instance is not None:
        try:
            instance.close()
        except Exception:
            pass


def file_etag(path: Path) -> str:
    """Stable short hash over path + mtime + size."""
    h = hashlib.sha256()
    h.update(str(path.resolve()).encode())
    stat = path.stat()
    h.update(str(stat.st_mtime_ns).encode())
    h.update(str(stat.st_size).encode())
    return h.hexdigest()[:16]


def _markitdown_version() -> str:
    """Return the installed ``markitdown --version`` string (or ``"unknown"``)."""
    global _markitdown_version_cache
    if _markitdown_version_cache is not None:
        return _markitdown_version_cache
    executable = resolve_markitdown_cli()
    if executable is None:
        _markitdown_version_cache = "unknown"
        return _markitdown_version_cache
    try:
        proc = subprocess.run(
            [executable, "--version"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=5,
        )
        _markitdown_version_cache = (proc.stdout or proc.stderr or "").strip() or "unknown"
    except (OSError, subprocess.TimeoutExpired):
        _markitdown_version_cache = "unknown"
    return _markitdown_version_cache


def cache_key(
    kind: str,
    etag: str,
    *,
    provider: str | None,
    model: str | None,
    preset: str | None,
    parser_version: str | None = None,
) -> str:
    """Compose ``f"{kind}:{provider}:{model}:{preset}:{parser_version}:{etag}"``.

    ``provider`` and ``model`` are mandatory because the multimodal tools run
    under the requesting turn's runtime — caching a MiniMax M3 caption
    under a key that doesn't mention the provider would let a later turn
    served by a different model return stale output.  ``parser_version`` is
    only consulted for ``document`` operations and defaults to the
    installed markitdown version (or ``"n/a"`` for vision/audio).  Missing
    values are substituted with the ``"unknown"`` sentinel so the key
    always carries a stable identity tuple.
    """
    if parser_version is None:
        parser_version = _markitdown_version() if kind == "document" else "n/a"
    preset_token = preset or "default"
    provider_token = provider or "unknown"
    model_token = model or "unknown"
    return f"{kind}:{provider_token}:{model_token}:{preset_token}:{parser_version}:{etag}"


__all__ = [
    "cache_key",
    "file_etag",
    "get_cache",
    "reset_cache",
]
