"""Exact-ID graph queries against the AK graph artifact."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from nanobot.agent.kg.ak.core import (
    check_bundle_paths,
    check_no_symlink_components,
    validate_note_id,
)
from nanobot.agent.kg.vendor.okf_bundle_core.graph_query import neighbors, shortest_path

from .write import RELATIONS


def _check_graph(root: Path) -> None:
    check_bundle_paths(root)
    check_no_symlink_components(root, root / "graphify-out")
    check_no_symlink_components(root, root / "graphify-out" / "graph.json")


def graph_neighbors(root: Path, note_id: str,
                    relation_filter: list[str] | None = None) -> dict[str, Any]:
    validate_note_id(note_id)
    if relation_filter is not None and any(r not in RELATIONS for r in relation_filter):
        raise ValueError("invalid relation_filter")
    _check_graph(root)
    result = neighbors(root, note_id, relation_filter=relation_filter)
    return {"node_id": result.node_id, "label": result.label,
            "neighbors": [{"id": n.id, "label": n.label, "direction": n.direction,
                           "relation": n.relation} for n in result.neighbors]}


def graph_shortest_path(root: Path, from_id: str, to_id: str,
                        max_hops: int | None = None) -> dict[str, Any]:
    validate_note_id(from_id)
    validate_note_id(to_id)
    if max_hops is not None and not 0 <= max_hops <= 10000:
        raise ValueError("max_hops must be between 0 and 10000")
    _check_graph(root)
    result = shortest_path(root, from_id, to_id, max_hops=max_hops)
    return {"found": result.found, "source_id": result.source_id,
            "target_id": result.target_id, "hops": result.hops,
            "path": result.path, "labels": result.labels}
