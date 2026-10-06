"""Native AK atomization, linking, graph queries and archival."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import Any, TypeVar

from nanobot.agent.kg.ak import forget as ak_forget
from nanobot.agent.kg.ak import graph as ak_graph
from nanobot.agent.kg.ak import to_json
from nanobot.agent.kg.ak import write as ak_write
from nanobot.agent.tools.ak_read import AKTool
from nanobot.agent.tools.base import tool_parameters

_T = TypeVar("_T")


async def _to_thread_complete(fn: Callable[..., _T], *args: Any) -> _T:
    """Do not abandon a running bundle transaction on turn cancellation."""
    task = asyncio.create_task(asyncio.to_thread(fn, *args))
    try:
        return await asyncio.shield(task)
    except asyncio.CancelledError:
        try:
            await task
        finally:
            raise

_ID = {"type": "string", "pattern": r"^[0-9]{8}-[0-9]{6}$", "minLength": 15, "maxLength": 15}
_RELATION = {"type": "string", "enum": sorted(ak_write.RELATIONS)}


@tool_parameters({"type": "object", "properties": {
    "source_id": _ID, "chunk_index": {"type": "integer", "minimum": 0, "maximum": 10000},
    "title": {"type": "string", "minLength": 1, "maxLength": 500},
    "body": {"type": "string", "minLength": 1, "maxLength": 200000},
    "tags": {"type": ["array", "null"], "items": {"type": "string", "maxLength": 64}, "maxItems": 50},
    "expected_content_hash": {"type": ["string", "null"], "pattern": "^[0-9a-f]{64}$"},
}, "required": ["source_id", "chunk_index", "title", "body"], "additionalProperties": False})
class AKNoteWriteExtractedTool(AKTool):
    @property
    def name(self) -> str:
        return "ak_note_write_extracted"

    @property
    def description(self) -> str:
        return "Atomize a Source chunk into an ExtractedNote; resume an existing chunk without duplicates."

    async def execute(self, **kwargs: Any) -> str:
        return to_json(await _to_thread_complete(ak_write.note_write_extracted, self._root(write=True),
                       kwargs["source_id"], kwargs["chunk_index"], kwargs["title"], kwargs["body"],
                       kwargs.get("tags"), kwargs.get("expected_content_hash")))


@tool_parameters({"type": "object", "properties": {
    "from_id": _ID, "to_id": _ID, "relation": _RELATION,
}, "required": ["from_id", "to_id", "relation"], "additionalProperties": False})
class AKNoteLinkTool(AKTool):
    @property
    def name(self) -> str:
        return "ak_note_link"

    @property
    def description(self) -> str:
        return "Add a semantic link between AK notes; forward references are allowed."

    async def execute(self, **kwargs: Any) -> str:
        return to_json(await _to_thread_complete(ak_write.note_link, self._root(write=True),
                       kwargs["from_id"], kwargs["to_id"], kwargs["relation"]))


@tool_parameters({"type": "object", "properties": {
    "from_ids": {"type": "array", "items": _ID, "minItems": 1, "maxItems": 100},
    "to_ids": {"type": "array", "items": _ID, "minItems": 1, "maxItems": 100},
    "relations": {"type": ["array", "null"], "items": _RELATION, "maxItems": 100},
}, "required": ["from_ids", "to_ids"], "additionalProperties": False})
class AKNoteBatchLinkTool(AKTool):
    @property
    def name(self) -> str:
        return "ak_note_batch_link"

    @property
    def description(self) -> str:
        return "Link up to 100 AK edges independently; report applied/skipped/error per edge."

    async def execute(self, **kwargs: Any) -> str:
        return to_json(await _to_thread_complete(ak_write.note_batch_link, self._root(write=True),
                       kwargs["from_ids"], kwargs["to_ids"], kwargs.get("relations")))


@tool_parameters({"type": "object", "properties": {
    "note_id": _ID,
    "relation_filter": {"type": ["array", "null"], "items": _RELATION, "maxItems": 4},
}, "required": ["note_id"], "additionalProperties": False})
class AKGraphNeighborsTool(AKTool):
    @property
    def name(self) -> str:
        return "ak_graph_neighbors"

    @property
    def description(self) -> str:
        return "Read immediate neighbors by exact ID from the AK graph artifact (requires rebuild)."

    @property
    def read_only(self) -> bool:
        return True

    async def execute(self, **kwargs: Any) -> str:
        return to_json(await asyncio.to_thread(ak_graph.graph_neighbors, self._root(),
                       kwargs["note_id"], kwargs.get("relation_filter")))


@tool_parameters({"type": "object", "properties": {
    "from_id": _ID, "to_id": _ID, "max_hops": {"type": ["integer", "null"], "minimum": 0, "maximum": 10000},
}, "required": ["from_id", "to_id"], "additionalProperties": False})
class AKGraphShortestPathTool(AKTool):
    @property
    def name(self) -> str:
        return "ak_graph_shortest_path"

    @property
    def description(self) -> str:
        return "Read shortest undirected path by exact IDs from the AK graph artifact."

    @property
    def read_only(self) -> bool:
        return True

    async def execute(self, **kwargs: Any) -> str:
        return to_json(await asyncio.to_thread(ak_graph.graph_shortest_path, self._root(),
                       kwargs["from_id"], kwargs["to_id"], kwargs.get("max_hops")))


@tool_parameters({"type": "object", "properties": {
    "source_id": _ID, "reason": {"type": "string", "minLength": 1, "maxLength": 1000},
}, "required": ["source_id"], "additionalProperties": False})
class AKSourceForgetTool(AKTool):
    @property
    def name(self) -> str:
        return "ak_source_forget"

    @property
    def description(self) -> str:
        return "Archive a Source note and its raw binary; derived notes remain in the bundle."

    async def execute(self, **kwargs: Any) -> str:
        return to_json(await _to_thread_complete(ak_forget.source_forget, self._root(write=True),
                       kwargs["source_id"], kwargs.get("reason", "forgotten by agent:percival")))
