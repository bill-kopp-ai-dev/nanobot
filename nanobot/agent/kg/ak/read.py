"""AK read-only discovery helpers — list, search, stats, isolation scan.

Mirrors the read-only tools in ``percival-acquire-knowledge/tools.py``
without depending on FastMCP.  All helpers here are best-effort:
corrupted frontmatter, permission errors, or partial bundles are
skipped instead of taking the whole call down.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import yaml

from nanobot.agent.kg.ak.core import (
    ID_PATTERN,
    MAX_LIST_NOTES,
    MAX_SEARCH_QUERY_CHARS,
    MAX_SEARCH_RESULTS,
    cache_stats,
    check_bundle_paths,
    note_paths,
    read_note_meta,
)
from nanobot.agent.kg.ak.telemetry import stats as telemetry_stats
from nanobot.agent.kg.vendor.okf_bundle_core.errors import ZettelError
from nanobot.agent.kg.vendor.okf_bundle_core.frontmatter import extract_links
from nanobot.agent.kg.vendor.okf_bundle_core.paths import ACQUIRED_KNOWLEDGE


def _notes_dir(root: Path) -> Path:
    return root / ACQUIRED_KNOWLEDGE.notes_dir


def _coerce_int(value: Any) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, float)):
        return int(value)
    return 0


def _coerce_int_list(value: Any) -> list[int]:
    if not isinstance(value, list):
        return []
    values: list[Any] = cast(list[Any], value)
    result: list[int] = []
    for candidate in values:
        if isinstance(candidate, bool):
            continue
        if isinstance(candidate, (int, float)):
            result.append(int(candidate))
    return result


def _coerce_str_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    values: list[Any] = cast(list[Any], value)
    result: list[str] = []
    for candidate in values:
        if isinstance(candidate, str):
            result.append(candidate)
    return result


def source_list(
    root: Path,
    *,
    kind: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """List Sources and/or ExtractedNotes with their main metadata."""
    if not 1 <= limit <= MAX_LIST_NOTES:
        raise ValueError(f"limit must be between 1 and {MAX_LIST_NOTES}")
    out: list[dict[str, Any]] = []
    for path in note_paths(root):
        match = ID_PATTERN.match(path.stem)
        if not match:
            continue
        try:
            data = read_note_meta(path)
        except (OSError, ValueError, yaml.YAMLError, ZettelError):
            continue
        if kind and data.get("type") != kind:
            continue
        atomized = _coerce_int_list(data.get("chunks_atomized"))
        total = _coerce_int(data.get("chunks_total"))
        out.append({
            "id": data["id"],
            "path": str(path.relative_to(root)),
            "type": data.get("type"),
            "title": data.get("title"),
            "source_kind": data.get("source_kind"),
            "media_type": data.get("media_type"),
            "size_bytes": data.get("size_bytes"),
            "chunks_total": total,
            "chunks_atomized": atomized,
            "partially_atomized": bool(atomized) and len(atomized) < total,
            "tags": data.get("tags", []),
            "derived_from": data.get("derived_from", []),
        })
        if len(out) >= limit:
            break
    return out


def source_search(
    root: Path,
    query: str,
    *,
    kind: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Case-insensitive substring search across all notes."""
    if not query:
        raise ValueError("query must be non-empty")
    if len(query) > MAX_SEARCH_QUERY_CHARS:
        raise ValueError(f"query must be at most {MAX_SEARCH_QUERY_CHARS} characters")
    if not 1 <= limit <= MAX_SEARCH_RESULTS:
        raise ValueError(f"limit must be between 1 and {MAX_SEARCH_RESULTS}")
    out: list[dict[str, Any]] = []
    needle = query.lower()
    for path in note_paths(root):
        match = ID_PATTERN.match(path.stem)
        if not match:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if needle not in text.lower():
            continue
        try:
            meta = read_note_meta(path)
        except (OSError, ValueError, yaml.YAMLError, ZettelError):
            continue
        if kind and meta.get("type") != kind:
            continue
        out.append({
            "id": meta["id"],
            "path": str(path.relative_to(root)),
            "type": meta.get("type"),
            "title": meta.get("title"),
            "tags": meta.get("tags", []),
        })
        if len(out) >= limit:
            break
    return out


def source_stats(root: Path) -> dict[str, Any]:
    """Bundle health: counts, partial atomisation, orphans, cache, telemetry."""
    check_bundle_paths(root, write=False)
    notes_dir = _notes_dir(root)
    sources = 0
    extracted = 0
    partially_atomized = 0
    broken_file_path = 0
    known_ids: set[str] = set()
    if notes_dir.exists():
        for path in note_paths(root):
            match = ID_PATTERN.match(path.stem)
            if not match:
                continue
            try:
                data = read_note_meta(path)
            except (OSError, ValueError, yaml.YAMLError, ZettelError):
                continue
            if data.get("type") == "Source":
                sources += 1
                known_ids.add(data["id"])
                atomized = _coerce_int_list(data.get("chunks_atomized"))
                total = _coerce_int(data.get("chunks_total"))
                if atomized and len(atomized) < total:
                    partially_atomized += 1
                file_path = data.get("file_path")
                if file_path and not (root / file_path).exists():
                    broken_file_path += 1
            elif data.get("type") == "ExtractedNote":
                extracted += 1
                known_ids.add(data["id"])

    orphan_extracted = 0
    has_outgoing: dict[str, bool] = {}
    referenced: set[str] = set()
    if notes_dir.exists():
        for path in note_paths(root):
            match = ID_PATTERN.match(path.stem)
            if not match:
                continue
            try:
                from nanobot.agent.kg.vendor.okf_bundle_core.frontmatter import split_frontmatter
                text = path.read_text(encoding="utf-8")
                raw_fm, body = split_frontmatter(text)
            except (OSError, ValueError, yaml.YAMLError, ZettelError):
                continue
            frontmatter_map: dict[str, Any] = raw_fm
            note_id = str(frontmatter_map.get("id") or match.group(1))
            targets = {link.target for link in extract_links(body) if not link.is_external}
            has_outgoing[note_id] = bool(targets)
            referenced.update(targets)

            if frontmatter_map.get("type") != "ExtractedNote":
                continue
            derived_ids = _coerce_str_list(frontmatter_map.get("derived_from"))
            if any(source not in known_ids for source in derived_ids):
                orphan_extracted += 1

    laterally_isolated = sum(
        1 for note_id, outgoing in has_outgoing.items()
        if not outgoing and note_id not in referenced
    )
    return {
        "notes_total": sources + extracted,
        "sources_total": sources,
        "extracted_total": extracted,
        "partially_atomized": partially_atomized,
        "orphan_extracted": orphan_extracted,
        "laterally_isolated": laterally_isolated,
        "broken_file_path": broken_file_path,
        "cache": cache_stats(root),
        "telemetry": telemetry_stats(root),
    }


def get_laterally_isolated_notes(root: Path) -> dict[str, Any]:
    """Return notes with no lateral edges (no out-links and not back-referenced)."""
    notes_dir = _notes_dir(root)
    id_to_meta: dict[str, dict[str, Any]] = {}
    has_outgoing: dict[str, bool] = {}
    referenced: set[str] = set()
    if notes_dir.exists():
        for path in note_paths(root):
            match = ID_PATTERN.match(path.stem)
            if not match:
                continue
            try:
                from nanobot.agent.kg.vendor.okf_bundle_core.frontmatter import split_frontmatter
                text = path.read_text(encoding="utf-8")
                raw_fm, body = split_frontmatter(text)
            except (OSError, ValueError, yaml.YAMLError, ZettelError):
                continue
            frontmatter_map: dict[str, Any] = raw_fm
            note_id = str(frontmatter_map.get("id") or match.group(1))
            derived_ids: list[str] = _coerce_str_list(frontmatter_map.get("derived_from"))
            id_to_meta[note_id] = {
                "title": frontmatter_map.get("title", "(sem título)"),
                "type": frontmatter_map.get("type", "unknown"),
                "derived_from": derived_ids,
            }
            targets = {link.target for link in extract_links(body) if not link.is_external}
            has_outgoing[note_id] = bool(targets)
            referenced.update(targets)

    isolated_notes: list[dict[str, Any]] = []
    by_source: dict[str, int] = {}
    for note_id, outgoing in has_outgoing.items():
        if outgoing or note_id in referenced:
            continue
        meta = id_to_meta.get(note_id, {})
        derived_parent: list[str] = _coerce_str_list(meta.get("derived_from"))
        source_id = derived_parent[0] if derived_parent else None
        isolated_notes.append({
            "id": note_id,
            "title": meta.get("title", "(sem título)"),
            "source_id": source_id,
            "type": meta.get("type", "unknown"),
        })
        if source_id:
            by_source[source_id] = by_source.get(source_id, 0) + 1
    return {
        "isolated_notes": isolated_notes,
        "count": len(isolated_notes),
        "by_source": by_source,
    }


__all__ = [
    "get_laterally_isolated_notes",
    "source_list",
    "source_search",
    "source_stats",
]
