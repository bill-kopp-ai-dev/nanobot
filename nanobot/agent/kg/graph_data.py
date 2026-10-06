"""Bounded, read-only graph artifact shared by KG HTTP metadata and data routes."""

from __future__ import annotations

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
