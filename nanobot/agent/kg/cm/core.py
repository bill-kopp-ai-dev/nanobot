"""Synchronous CM operations shared by native tools and later gateway adapters."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, cast

from nanobot.agent.kg.vendor.okf_bundle_core.errors import CASMismatchError, ZettelError
from nanobot.agent.kg.vendor.okf_bundle_core.frontmatter import split_frontmatter
from nanobot.agent.kg.vendor.okf_bundle_core.gitstore import GitStore
from nanobot.agent.kg.vendor.okf_bundle_core.paths import COLLECTIVE_MEMORY, PathEscapeError
from nanobot.agent.kg.vendor.okf_bundle_core.schema import validate_id
from nanobot.agent.kg.vendor.okf_bundle_core.zettel import WriteRequest
from nanobot.agent.kg.vendor.okf_bundle_core.zettel import notes_read as bundle_notes_read
from nanobot.agent.kg.vendor.okf_bundle_core.zettel import notes_write as bundle_notes_write

MAX_SEARCH_QUERY_CHARS = 500
MAX_SEARCH_RESULTS = 200
MAX_HISTORY_ENTRIES = 1000


def notes_list(root: Path, *, limit: int = 50) -> list[dict[str, Any]]:
    if not 1 <= limit <= MAX_SEARCH_RESULTS:
        raise ValueError("limit must be between 1 and 200")
    _check_bundle_paths(root, write=False)
    results: list[dict[str, Any]] = []
    for path in sorted((root / COLLECTIVE_MEMORY.notes_dir).glob("*.md")):
        if not path.resolve().is_relative_to(root.resolve()):
            raise PathEscapeError(str(path))
        match = re.match(r"^(\d{8}-\d{6})(?:-|$)", path.stem)
        if match is None:
            continue
        try:
            meta, _ = split_frontmatter(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, ZettelError):
            continue
        review = meta.get("review")
        entries = cast(list[object], review) if isinstance(review, list) else []
        pending = sum(1 for entry in entries if isinstance(entry, dict) and cast(dict[str, Any], entry).get("status") == "pending")
        results.append({
            "id": match.group(1), "path": path.relative_to(root).as_posix(),
            "title": meta.get("title"), "type": meta.get("type"),
            "tags": meta.get("tags") if isinstance(meta.get("tags"), list) else [],
            "protected": bool(meta.get("protected", False)),
            "lifecycle": meta.get("lifecycle") or "active",
            "pending_review_count": pending,
        })
        if len(results) >= limit:
            break
    return results


def _check_bundle_paths(root: Path, *, write: bool) -> None:
    """Refuse bundle-internal symlinks that would cross the authorized root."""
    resolved_root = root.resolve()
    paths = [root / "notes"]
    if write:
        paths.extend((root / "log.md", root / ".git", root / COLLECTIVE_MEMORY.lock_file))
    for path in paths:
        check_no_symlink_components(root, path)
        if path.exists() or path.is_symlink():
            if not path.resolve().is_relative_to(resolved_root):
                raise PathEscapeError(str(path))
    notes_dir = root / COLLECTIVE_MEMORY.notes_dir
    if notes_dir.is_dir():
        for path in notes_dir.glob(f"*{COLLECTIVE_MEMORY.notes_extension}"):
            check_no_symlink_components(root, path)


def check_no_symlink_components(root: Path, path: Path) -> None:
    """Reject even internal redirection of a bundle operation."""
    relative = path.relative_to(root)
    current = root
    for part in relative.parts:
        if part == "..":
            raise PathEscapeError(str(path))
        current = current / part
        if current.is_symlink():
            raise PathEscapeError(str(current))


def check_bundle_paths(root: Path, *, write: bool = False) -> None:
    """Public authorization check for other CM operations sharing this boundary."""
    _check_bundle_paths(root, write=write)


def _check_note_paths(root: Path, note_id: str) -> None:
    """Validate matching entries before the core can open a note or its body."""
    validate_id(note_id)
    notes_dir = root / COLLECTIVE_MEMORY.notes_dir
    for path in notes_dir.glob(f"{note_id}-*{COLLECTIVE_MEMORY.notes_extension}"):
        check_no_symlink_components(root, path)
        if not path.resolve().is_relative_to(root.resolve()):
            raise PathEscapeError(str(path))


def notes_read(root: Path, note_id: str) -> dict[str, Any]:
    _check_bundle_paths(root, write=False)
    _check_note_paths(root, note_id)
    result = bundle_notes_read(root, COLLECTIVE_MEMORY, note_id, gitstore=GitStore(root, COLLECTIVE_MEMORY))
    if not result.path.resolve().is_relative_to(root.resolve()):
        raise PathEscapeError(str(result.path))
    return {
        "id": result.id,
        "path": result.path.relative_to(root).as_posix(),
        "frontmatter": result.frontmatter.model_dump(mode="json", exclude_none=True),
        "body": result.body,
        "content_hash": result.content_hash,
        "body_hash": result.body_hash,
        "backlinks": result.backlinks,
    }


def notes_write(
    root: Path,
    *,
    note_id: str,
    body: str,
    frontmatter_patch: dict[str, Any] | None = None,
    expected_content_hash: str | None = None,
    expected_body_hash: str | None = None,
    reason: str = "edit",
) -> dict[str, Any]:
    _check_bundle_paths(root, write=True)
    _check_note_paths(root, note_id)
    result = bundle_notes_write(
        root,
        COLLECTIVE_MEMORY,
        WriteRequest(
            id=note_id,
            body=body,
            frontmatter_patch=frontmatter_patch,
            expected_content_hash=expected_content_hash,
            expected_body_hash=expected_body_hash,
            reason=reason,
        ),
    )
    return {
        "id": result.id,
        "path": result.path.relative_to(root).as_posix(),
        "content_hash": result.content_hash,
        "body_hash": result.body_hash,
        "frontmatter": result.new_frontmatter.model_dump(mode="json", exclude_none=True),
    }


def notes_search(root: Path, query: str, *, limit: int = 20,
                 kind: str | None = None) -> list[dict[str, Any]]:
    if not query.strip():
        raise ValueError("query must not be blank")
    if len(query) > MAX_SEARCH_QUERY_CHARS:
        raise ValueError(f"query must be at most {MAX_SEARCH_QUERY_CHARS} characters")
    if not 1 <= limit <= MAX_SEARCH_RESULTS:
        raise ValueError(f"limit must be between 1 and {MAX_SEARCH_RESULTS}")
    _check_bundle_paths(root, write=False)
    notes_dir = root / COLLECTIVE_MEMORY.notes_dir
    if not notes_dir.is_dir():
        return []
    needle = query.casefold()
    results: list[dict[str, Any]] = []
    for path in sorted(notes_dir.glob(f"*{COLLECTIVE_MEMORY.notes_extension}")):
        if not path.resolve().is_relative_to(root.resolve()):
            raise PathEscapeError(str(path))
        text = path.read_text(encoding="utf-8")
        if kind:
            try:
                frontmatter, _ = split_frontmatter(text)
            except ZettelError:
                continue
            if frontmatter.get("type") != kind:
                continue
        for line_no, line in enumerate(text.splitlines(), start=1):
            if needle in line.casefold():
                parts = path.stem.split("-", 2)
                results.append({
                    "id": "-".join(parts[:2]),
                    "path": path.relative_to(root).as_posix(),
                    "line": line_no,
                    "snippet": line[:200],
                })
                if len(results) >= limit:
                    return results
    return results


def note_history(root: Path, note_id: str, *, limit: int = 20) -> dict[str, Any]:
    validate_id(note_id)
    if not 1 <= limit <= MAX_HISTORY_ENTRIES:
        raise ValueError(f"limit must be between 1 and {MAX_HISTORY_ENTRIES}")
    note = notes_read(root, note_id)
    git_dir = root / ".git"
    if not git_dir.is_dir():
        history = []
    else:
        records = GitStore(root, COLLECTIVE_MEMORY).log_for(root / note["path"], limit=limit)
        history = [
            {
                "sha": item.sha,
                "author": item.author,
                "email": item.email,
                "timestamp": item.timestamp.isoformat(),
                "message": item.message,
                "paths": item.paths,
            }
            for item in records
        ]
    return {"id": note_id, "history": history}


def to_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


__all__ = ["CASMismatchError", "note_history", "notes_read", "notes_search", "notes_write", "to_json"]
