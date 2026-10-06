"""Synchronous AK helpers shared by native tools and gateway adapters.

The functions in this module are pure-Python and reusable from
``asyncio.to_thread``; none of them issue network calls.  Vendor code
from ``okf_bundle_core`` provides the lock, git store, schema and
frontmatter serialization.
"""

from __future__ import annotations

import hashlib
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

import yaml

from nanobot.agent.kg.vendor.okf_bundle_core.errors import ZettelError
from nanobot.agent.kg.vendor.okf_bundle_core.frontmatter import serialize, split_frontmatter
from nanobot.agent.kg.vendor.okf_bundle_core.gitstore import GitStore
from nanobot.agent.kg.vendor.okf_bundle_core.lock import BundleLock
from nanobot.agent.kg.vendor.okf_bundle_core.paths import (
    ACQUIRED_KNOWLEDGE,
    PathEscapeError,
    assert_asset_exists,
)
from nanobot.agent.kg.vendor.okf_bundle_core.schema import ZettelFrontmatter
from nanobot.agent.kg.vendor.okf_bundle_core.zettel import notes_read, write_atomic

from .parsers import mimetype_from_suffix

ID_PATTERN = re.compile(r"^(\d{8}-\d{6})")
MAX_LIST_NOTES = 10_000
MAX_SEARCH_RESULTS = 200
MAX_SEARCH_QUERY_CHARS = 500
INGEST_LOCK_TIMEOUT_S = 30.0
MAX_INGEST_BYTES = 200 * 1024 * 1024  # 200MB
_UNKNOWN_LOG_STATE = object()


def gitstore(root: Path) -> GitStore:
    instance = GitStore(root, ACQUIRED_KNOWLEDGE)
    instance.ensure_repo()
    return instance


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def validate_note_id(note_id: str) -> str:
    """Validate a canonical ID without ``$`` accepting a trailing newline."""
    if re.fullmatch(r"[0-9]{8}-[0-9]{6}", note_id) is None:
        raise ValueError(f"id {note_id!r} is not canonical YYYYMMDD-HHMMSS")
    return note_id


def _slug(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower())[:50].rstrip("-")
    return slug or "untitled"


def note_path(root: Path, note_id: str, title: str) -> Path:
    return (
        root
        / ACQUIRED_KNOWLEDGE.notes_dir
        / f"{note_id}-{_slug(title)}{ACQUIRED_KNOWLEDGE.notes_extension}"
    )


def check_bundle_paths(root: Path, *, write: bool = False) -> None:
    """Refuse bundle components and note symlinks that escape the root."""
    del write  # Read-side notes_read currently ensures GitStore, too.
    resolved_root = root.resolve()
    paths: list[Path] = [
        root / "notes",
        root / "sources",
        root / ".cache",
        root / ".telemetry",
        root / "log.md",
        root / ".git",
        root / ".gitignore",
        root / ACQUIRED_KNOWLEDGE.lock_file,
    ]
    for path in paths:
        if path.exists() or path.is_symlink():
            if not path.resolve().is_relative_to(resolved_root):
                raise PathEscapeError(str(path))
    notes_dir = root / ACQUIRED_KNOWLEDGE.notes_dir
    if notes_dir.is_dir():
        for path in notes_dir.glob(f"*{ACQUIRED_KNOWLEDGE.notes_extension}"):
            if not path.resolve().is_relative_to(resolved_root):
                raise PathEscapeError(str(path))


def check_no_symlink_components(root: Path, path: Path) -> None:
    """Reject symlinks at every bundle-relative component, including internal ones.

    Containment alone is insufficient for destructive operations: an internal
    symlink can redirect an archive or a note write into another bundle area.
    """
    resolved_root = root.resolve()
    candidate = path if path.is_absolute() else resolved_root / path
    try:
        relative = candidate.relative_to(resolved_root)
    except ValueError as exc:
        raise PathEscapeError(str(path)) from exc
    if ".." in relative.parts:
        raise PathEscapeError(str(path))
    current = resolved_root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise PathEscapeError(str(current))


def note_paths(root: Path) -> list[Path]:
    """Return note files only after validating each resolved path boundary."""
    check_bundle_paths(root)
    notes_dir = root / ACQUIRED_KNOWLEDGE.notes_dir
    if not notes_dir.is_dir():
        return []
    resolved_root = root.resolve()
    paths = sorted(notes_dir.glob(f"*{ACQUIRED_KNOWLEDGE.notes_extension}"))
    for path in paths:
        if not path.resolve().is_relative_to(resolved_root):
            raise PathEscapeError(str(path))
    return paths


def resolve_asset_path(root: Path, asset_path: str) -> Path:
    """Resolve ``asset_path`` accepting absolute or bundle-relative paths.

    Uses realpath comparison so that symlinks cannot bypass the bundle
    boundary.  The order of errors matters: ``ValueError`` ("outside the
    bundle") takes precedence over ``FileNotFoundError`` ("not on
    disk") so callers see a security diagnosis first.
    """
    candidate = Path(asset_path).expanduser()
    if not candidate.is_absolute():
        candidate = root / candidate
    asset_real = os.path.realpath(candidate)
    root_real = os.path.realpath(root)
    if not asset_real.startswith(root_real + os.sep) and asset_real != root_real:
        raise ValueError(
            f"asset {asset_path!r} (realpath={asset_real}) "
            f"outside bundle root (realpath={root_real})"
        )
    if not Path(asset_real).is_file():
        raise FileNotFoundError(f"asset {asset_path!r} not found")
    return Path(asset_real)


def ingested_path(root: Path, source_id: str, suffix: str) -> Path:
    """``<root>/sources/<source_id><suffix>`` — gitignored by D33."""
    sources_dir = root / "sources"
    sources_dir.mkdir(parents=True, exist_ok=True)
    return sources_dir / f"{source_id}{suffix.lower()}"


def find_note_path(root: Path, note_id: str) -> Path | None:
    for path in note_paths(root):
        match = ID_PATTERN.match(path.stem)
        if match and match.group(1) == note_id:
            return path
    return None


def new_id(root: Path) -> str:
    """Generate a unique ``YYYYMMDD-HHMMSS`` id, bumping 1s on collision."""
    from datetime import timedelta

    notes = root / ACQUIRED_KNOWLEDGE.notes_dir
    notes.mkdir(parents=True, exist_ok=True)
    candidate = datetime.now(timezone.utc)
    max_gap = timedelta(hours=1)
    while True:
        id_str = candidate.strftime("%Y%m%d-%H%M%S")
        if (
            not list(notes.glob(f"{id_str}*{ACQUIRED_KNOWLEDGE.notes_extension}"))
            and not list(notes.glob(f"{id_str}{ACQUIRED_KNOWLEDGE.notes_extension}"))
        ):
            return id_str
        if candidate - datetime.now(timezone.utc) > max_gap:
            raise RuntimeError(
                f"new_id: no free id within {max_gap} of now (last tried {id_str})"
            )
        candidate += timedelta(seconds=1)


def read_note_meta(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    try:
        raw_frontmatter, _ = split_frontmatter(text)
    except ZettelError:
        raise
    frontmatter: dict[str, Any] = raw_frontmatter or {}
    match = ID_PATTERN.match(path.stem)
    if "id" not in frontmatter and match:
        frontmatter["id"] = match.group(1)
    return frontmatter


def read_note_meta_by_id(root: Path, note_id: str) -> dict[str, Any]:
    for path in note_paths(root):
        match = ID_PATTERN.match(path.stem)
        if match and match.group(1) == note_id:
            return read_note_meta(path)
    raise FileNotFoundError(f"no note with id {note_id}")


def find_existing_source_by_sha256(
    root: Path, content_sha256: str
) -> tuple[str, str, int, int] | None:
    for path in note_paths(root):
        try:
            frontmatter = read_note_meta(path)
        except (OSError, ValueError, yaml.YAMLError, ZettelError):
            continue
        if frontmatter.get("type") != "Source":
            continue
        if frontmatter.get("content_sha256") != content_sha256:
            continue
        return (
            frontmatter["id"],
            frontmatter.get("file_path", ""),
            int(frontmatter.get("chunks_total", 0) or 0),
            int(frontmatter.get("parsed_chars", 0) or 0),
        )
    return None


def read_note(root: Path, note_id: str) -> dict[str, Any]:
    check_bundle_paths(root)
    for path in note_paths(root):
        match = ID_PATTERN.match(path.stem)
        if match and match.group(1) == note_id and not path.resolve().is_relative_to(root.resolve()):
            raise PathEscapeError(str(path))
    note = notes_read(root, ACQUIRED_KNOWLEDGE, note_id, gitstore=gitstore(root))
    if not note.path.resolve().is_relative_to(root.resolve()):
        raise PathEscapeError(str(note.path))
    return {
        "id": note.id,
        "path": note.path.relative_to(root).as_posix(),
        "frontmatter": note.frontmatter.model_dump(mode="json", exclude_none=True),
        "body": note.body,
        "content_hash": note.content_hash,
        "body_hash": note.body_hash,
        "backlinks": note.backlinks,
    }


def hash_file(path: Path, *, max_bytes: int | None = None) -> str:
    """Hash a file incrementally, optionally enforcing the ingestion limit."""
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            size += len(chunk)
            if max_bytes is not None and size > max_bytes:
                raise ValueError(f"file exceeds {max_bytes} byte limit")
            digest.update(chunk)
    return digest.hexdigest()


def cache_stats(root: Path) -> dict[str, Any]:
    cache_dir = root / ".cache"
    if not cache_dir.exists():
        return {"exists": False}
    total_bytes = 0
    for child in cache_dir.rglob("*"):
        if child.is_file():
            try:
                total_bytes += child.stat().st_size
            except OSError:
                pass
    return {
        "exists": True,
        "size_bytes": total_bytes,
        "path": str(cache_dir.relative_to(root)),
    }


def ensure_within_bundle(path: Path, root: Path, *, hint: str = "") -> None:
    if not path.exists() or not path.is_file():
        suffix = f" ({hint})" if hint else ""
        raise FileNotFoundError(f"asset {path}{suffix} not on filesystem")
    if not path.resolve().is_relative_to(root.resolve()):
        raise PathEscapeError(str(path))


def write_source_note(
    root: Path,
    *,
    source_id: str,
    title: str,
    body: str,
    note_type: Literal["Source", "ExtractedNote"] = "Source",
    source_kind: str,
    file_path: str,
    content_sha256: str,
    media_type: str,
    size_bytes: int,
    chunks_total: int,
    parsed_chars: int,
    page_count: int | None,
    tags: list[str] | None,
    extra: dict[str, Any] | None = None,
) -> Path:
    """Atomically write the Source note and return its final path."""
    frontmatter_data: dict[str, Any] = {
        "type": note_type,
        "id": source_id,
        "title": title,
        "source_kind": source_kind,
        "file_path": file_path,
        "content_sha256": content_sha256,
        "media_type": media_type,
        "size_bytes": size_bytes,
        "generated": {"by": "process:source_ingest", "at": now_iso()},
        "status": "stable",
        "chunks_total": chunks_total,
        "parsed_chars": parsed_chars,
    }
    if page_count is not None:
        frontmatter_data["pages"] = page_count
    if tags:
        frontmatter_data["tags"] = tags
    if extra:
        for key, value in extra.items():
            if value is not None and key not in frontmatter_data:
                frontmatter_data[key] = value
    frontmatter = ZettelFrontmatter(**frontmatter_data)
    text = serialize(frontmatter, body)
    target = note_path(root, source_id, title)
    target.parent.mkdir(parents=True, exist_ok=True)
    write_atomic(target, text)
    return target


__all__ = [
    "ACQUIRED_KNOWLEDGE",
    "BundleLock",
    "ID_PATTERN",
    "INGEST_LOCK_TIMEOUT_S",
    "MAX_INGEST_BYTES",
    "MAX_LIST_NOTES",
    "MAX_SEARCH_QUERY_CHARS",
    "MAX_SEARCH_RESULTS",
    "assert_asset_exists",
    "cache_stats",
    "check_bundle_paths",
    "check_no_symlink_components",
    "ensure_within_bundle",
    "find_existing_source_by_sha256",
    "find_note_path",
    "gitstore",
    "hash_file",
    "ingested_path",
    "mimetype_from_suffix",
    "new_id",
    "note_paths",
    "note_path",
    "now_iso",
    "read_note",
    "read_note_meta",
    "read_note_meta_by_id",
    "resolve_asset_path",
    "write_atomic",
    "write_source_note",
    "validate_note_id",
]
