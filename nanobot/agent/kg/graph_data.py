"""Bounded, read-only graph artifact shared by KG HTTP metadata and data routes."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, cast

from nanobot.agent.kg.ak.core import check_no_symlink_components
from nanobot.agent.kg.vendor.okf_bundle_core.paths import PathEscapeError

MAX_GRAPH_BYTES = 8 * 1024 * 1024


class GraphTooLargeError(ValueError):
    """The graph artifact exceeds the bridge's declared response limit."""


def graph_artifact(root: Path, *, data: bool = False) -> dict[str, Any]:
    path = root / "graphify-out" / "graph.json"
    check_no_symlink_components(root, path)
    if not path.resolve().is_relative_to(root.resolve()):
        raise PathEscapeError(str(path))
    if not path.is_file():
        if data:
            raise FileNotFoundError("graph.json is missing; rebuild the graph")
        return {"exists": False}
    size = path.stat().st_size
    if not data:
        return {"exists": True, "path": "graphify-out/graph.json", "size_bytes": size}
    if size > MAX_GRAPH_BYTES:
        raise GraphTooLargeError("graph exceeds the 8 MiB API limit")
    with path.open("rb") as stream:
        raw = stream.read(MAX_GRAPH_BYTES + 1)
    if len(raw) > MAX_GRAPH_BYTES:
        raise GraphTooLargeError("graph exceeds the 8 MiB API limit")
    try:
        parsed: object = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("graph.json is invalid") from exc
    if not isinstance(parsed, dict):
        raise ValueError("graph.json has no node-link data")
    graph = cast(dict[str, object], parsed)
    if not isinstance(graph.get("nodes"), list) or not isinstance(graph.get("links"), list):
        raise ValueError("graph.json has no node-link data")
    return cast(dict[str, Any], parsed)


def graph_status(root: Path) -> str:
    """Return the bounded validation state of the derived graph artifact."""
    try:
        graph = graph_artifact(root, data=True)
        fingerprint = notes_fingerprint(root)
    except FileNotFoundError:
        return "missing"
    except (GraphTooLargeError, ValueError, OSError, PathEscapeError):
        return "invalid"
    if graph.get("source_fingerprint") != fingerprint:
        return "stale"
    return "valid"


def notes_fingerprint(root: Path) -> str:
    """Hash note paths and bytes so graph freshness includes external edits."""
    digest = hashlib.sha256()
    notes = root / "notes"
    check_no_symlink_components(root, notes)
    if not notes.is_dir() or not notes.resolve().is_relative_to(root.resolve()):
        raise PathEscapeError(str(notes))
    for path in sorted(notes.glob("*.md"), key=lambda item: item.name):
        check_no_symlink_components(root, path)
        if not path.resolve().is_relative_to(root.resolve()):
            raise PathEscapeError(str(path))
        digest.update(path.name.encode("utf-8"))
        digest.update(b"\0")
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(64 * 1024), b""):
                digest.update(chunk)
        digest.update(b"\0")
    return digest.hexdigest()
