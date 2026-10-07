"""Native collective-memory link, policy, graph and storage tools."""

from __future__ import annotations

import asyncio
from typing import Any, cast

from nanobot.agent.kg.cm import f2
from nanobot.agent.kg.vendor.okf_bundle_core.errors import CASMismatchError, ZettelError
from nanobot.agent.kg.vendor.okf_bundle_core.lock import LockTimeout
from nanobot.agent.tools.base import tool_parameters
from nanobot.agent.tools.cm_notes import NOTE_ID_PATTERN, CMTool


class _CMF2Tool(CMTool):
    async def _run(self, operation: Any, *args: Any, write: bool = False, **kwargs: Any) -> str:
        try:
            result = await asyncio.to_thread(operation, self._root(write=write), *args, **kwargs)
        except LockTimeout as exc:
            return f2.core.to_json({"status": "error", "error_kind": "lock_timeout",
                                     "error": str(exc) or "bundle is locked"})
        except CASMismatchError as exc:
            return f2.core.to_json({"status": "error", "error_kind": "cas_mismatch",
                                     "error": str(exc)})
        except ZettelError as exc:
            return f2.core.to_json({"status": "error", "error_kind": exc.code or "invalid_note",
                                     "error": str(exc)})
        return f2.core.to_json(result)


@tool_parameters({"type": "object", "properties": {
    "from_id": {"type": "string", "pattern": NOTE_ID_PATTERN}, "to_id": {"type": "string", "pattern": NOTE_ID_PATTERN},
    "relation": {"type": "string", "enum": ["related", "supersedes", "contradicts", "derived_from"]},
    "reason": {"type": "string", "maxLength": 500}}, "required": ["from_id", "to_id"], "additionalProperties": False})
class MemoryLinkTool(_CMF2Tool):
    @property
    def name(self) -> str: return "memory_link"
    @property
    def description(self) -> str: return "Add an idempotent relation from one CM note to another; forward target references are allowed."
    async def execute(self, **kwargs: Any) -> str:
        return await self._run(f2.memory_link, kwargs["from_id"], kwargs["to_id"], write=True,
                               relation=kwargs.get("relation", "related"), reason=kwargs.get("reason", "manual link"))


@tool_parameters({"type": "object", "properties": {
    "edges": {"type": "array", "minItems": 1, "maxItems": f2.MAX_BATCH_LINKS, "items": {"type": "object",
        "properties": {"from_id": {"type": "string", "pattern": NOTE_ID_PATTERN}, "to_id": {"type": "string", "pattern": NOTE_ID_PATTERN},
                       "relation": {"type": "string", "enum": ["related", "supersedes", "contradicts", "derived_from"]}},
        "required": ["from_id", "to_id"], "additionalProperties": False}},
    "from_ids": {"type": "array", "minItems": 1, "maxItems": f2.MAX_BATCH_LINKS,
                  "items": {"type": "string", "pattern": NOTE_ID_PATTERN}},
    "to_ids": {"type": "array", "minItems": 1, "maxItems": f2.MAX_BATCH_LINKS,
                "items": {"type": "string", "pattern": NOTE_ID_PATTERN}},
    "relations": {"type": "array", "maxItems": f2.MAX_BATCH_LINKS,
                  "items": {"type": "string", "enum": ["related", "supersedes", "contradicts", "derived_from"]}},
    "reason": {"type": "string", "maxLength": 500}}, "additionalProperties": False})
class MemoryBatchLinkTool(_CMF2Tool):
    @property
    def name(self) -> str: return "memory_batch_link"
    @property
    def description(self) -> str: return "Apply up to 100 CM links sequentially; returns per-edge applied, skipped or error status (not atomic)."
    async def execute(self, **kwargs: Any) -> str:
        raw_edges = kwargs.get("edges")
        edges: list[dict[str, str]] | None = None
        if raw_edges is not None:
            if not isinstance(raw_edges, list):
                raise ValueError("edges must be a list")
            edges = cast(list[dict[str, str]], raw_edges)
        arrays_supplied = any(key in kwargs for key in ("from_ids", "to_ids", "relations"))
        if edges is not None and arrays_supplied:
            raise ValueError("pass edges or parallel arrays, not both")
        if arrays_supplied:
            raw_from_ids, raw_to_ids = kwargs.get("from_ids"), kwargs.get("to_ids")
            raw_relations = kwargs.get("relations")
            from_ids = cast(list[str], raw_from_ids) if isinstance(raw_from_ids, list) else None
            to_ids = cast(list[str], raw_to_ids) if isinstance(raw_to_ids, list) else None
            relations = cast(list[str], raw_relations) if isinstance(raw_relations, list) else None
            if not isinstance(from_ids, list) or not isinstance(to_ids, list) or len(from_ids) != len(to_ids):
                raise ValueError("from_ids and to_ids must be parallel arrays of equal length")
            if raw_relations is not None and (relations is None or len(relations) != len(from_ids)):
                raise ValueError("relations must align with from_ids and to_ids")
            edges = [{"from_id": source, "to_id": target,
                      **({"relation": relations[index]} if relations is not None else {})}
                     for index, (source, target) in enumerate(zip(from_ids, to_ids, strict=True))]
        if edges is None:
            raise ValueError("edges or from_ids/to_ids are required")
        return await self._run(f2.memory_batch_link, edges, write=True, reason=kwargs.get("reason", "batch link"))


@tool_parameters({"type": "object", "properties": {
    "note_id": {"type": "string", "pattern": NOTE_ID_PATTERN}, "asset_path": {"type": "string", "minLength": 1, "maxLength": 2048},
    "kind": {"type": "string", "enum": ["reference", "primary"]}, "reason": {"type": "string", "maxLength": 500}},
    "required": ["note_id", "asset_path"], "additionalProperties": False})
class MemoryAttachTool(_CMF2Tool):
    @property
    def name(self) -> str: return "memory_attach"
    @property
    def description(self) -> str: return "Attach an existing in-bundle asset to a CM note's attachments metadata."
    async def execute(self, **kwargs: Any) -> str:
        return await self._run(f2.memory_attach, kwargs["note_id"], kwargs["asset_path"], write=True, reason=kwargs.get("reason", "manual attach"))


@tool_parameters({"type": "object", "properties": {
    "note_id": {"type": "string", "pattern": NOTE_ID_PATTERN}, "reason": {"type": "string", "minLength": 1, "maxLength": 500}},
    "required": ["note_id", "reason"], "additionalProperties": False})
class MemoryForgetTool(_CMF2Tool):
    @property
    def name(self) -> str: return "memory_forget"
    @property
    def description(self) -> str: return "Archive a CM note under _archive/YYYYMM; this preserves rather than deletes it."
    async def execute(self, **kwargs: Any) -> str:
        return await self._run(f2.memory_forget, kwargs["note_id"], kwargs["reason"], write=True)


@tool_parameters({"type": "object", "properties": {"include_storage": {"type": "boolean"}}, "additionalProperties": False})
class MemoryStatsTool(_CMF2Tool):
    @property
    def name(self) -> str: return "memory_stats"
    @property
    def description(self) -> str: return "Summarize CM notes, orphans, tags, lifecycle/review policy and graph health."
    @property
    def read_only(self) -> bool: return True
    async def execute(self, **kwargs: Any) -> str:
        return await self._run(f2.memory_stats, include_storage=kwargs.get("include_storage", False))


@tool_parameters({"type": "object", "properties": {"asset_ref": {"type": "string", "minLength": 1, "maxLength": 2048}},
                 "required": ["asset_ref"], "additionalProperties": False})
class AssetGetPathTool(_CMF2Tool):
    @property
    def name(self) -> str: return "asset_get_path"
    @property
    def description(self) -> str: return "Resolve an in-bundle asset path or the first attachment of a CM note."
    @property
    def read_only(self) -> bool: return True
    async def execute(self, **kwargs: Any) -> str:
        return await self._run(f2.asset_get_path, kwargs["asset_ref"])


@tool_parameters({"type": "object", "properties": {
    "note_id": {"type": "string", "pattern": NOTE_ID_PATTERN},
    "relation_filter": {"type": ["array", "null"], "items": {"type": "string", "enum": ["related", "supersedes", "contradicts", "derived_from"]}, "maxItems": 4}},
    "required": ["note_id"], "additionalProperties": False})
class GraphNeighborsTool(_CMF2Tool):
    @property
    def name(self) -> str: return "graph_neighbors"
    @property
    def description(self) -> str: return "Return one-hop incoming and outgoing neighbors by exact CM note id from the existing graph."
    @property
    def read_only(self) -> bool: return True
    async def execute(self, **kwargs: Any) -> str:
        return await self._run(f2.graph_neighbors, kwargs["note_id"], kwargs.get("relation_filter"))


@tool_parameters({"type": "object", "properties": {
    "from_id": {"type": "string", "pattern": NOTE_ID_PATTERN}, "to_id": {"type": "string", "pattern": NOTE_ID_PATTERN},
    "max_hops": {"type": ["integer", "null"], "minimum": 0, "maximum": 10000}},
    "required": ["from_id", "to_id"], "additionalProperties": False})
class GraphShortestPathTool(_CMF2Tool):
    @property
    def name(self) -> str: return "graph_shortest_path"
    @property
    def description(self) -> str: return "Return the undirected shortest path between exact CM note ids using the existing graph."
    @property
    def read_only(self) -> bool: return True
    async def execute(self, **kwargs: Any) -> str:
        return await self._run(f2.graph_shortest_path, kwargs["from_id"], kwargs["to_id"], kwargs.get("max_hops"))


@tool_parameters({"type": "object", "properties": {
    "note_id": {"type": "string", "pattern": NOTE_ID_PATTERN}, "protected": {"type": "boolean"},
    "reason": {"type": "string", "maxLength": 500}, "expected_content_hash": {"type": ["string", "null"], "maxLength": 64}},
    "required": ["note_id", "protected"], "additionalProperties": False})
class MemorySetProtectedTool(_CMF2Tool):
    @property
    def name(self) -> str: return "memory_set_protected"
    @property
    def description(self) -> str: return "Set or clear the human lifecycle-protection flag, optionally guarded by content-hash CAS."
    async def execute(self, **kwargs: Any) -> str:
        return await self._run(f2.memory_set_protected, kwargs["note_id"], kwargs["protected"], write=True,
                               reason=kwargs.get("reason", "manual toggle"), expected_content_hash=kwargs.get("expected_content_hash"))


@tool_parameters({"type": "object", "properties": {
    "note_id": {"type": "string", "pattern": NOTE_ID_PATTERN}, "lifecycle": {"type": "string", "enum": ["active", "cold"]},
    "reason": {"type": "string", "maxLength": 500}, "expected_content_hash": {"type": ["string", "null"], "maxLength": 64},
    "force": {"type": "boolean"}}, "required": ["note_id", "lifecycle"], "additionalProperties": False})
class MemorySetLifecycleTool(_CMF2Tool):
    @property
    def name(self) -> str: return "memory_set_lifecycle"
    @property
    def description(self) -> str: return "Set a note lifecycle to active or cold; protected notes require force=true to cool."
    async def execute(self, **kwargs: Any) -> str:
        return await self._run(f2.memory_set_lifecycle, kwargs["note_id"], kwargs["lifecycle"], write=True,
                               reason=kwargs.get("reason", "lifecycle transition"),
                               expected_content_hash=kwargs.get("expected_content_hash"), force=kwargs.get("force", False))


@tool_parameters({"type": "object", "properties": {
    "note_id": {"type": "string", "pattern": NOTE_ID_PATTERN}, "kind": {"type": "string", "enum": sorted(f2.REVIEW_KINDS)},
    "confidence": {"type": "string", "enum": ["low", "medium", "high"]}, "reason": {"type": "string", "minLength": 1, "maxLength": 1000},
    "related_actions": {"type": "array", "items": {"type": "string", "enum": ["move_to_cold", "set_protected_true", "keep_as_is", "forget", "move_to_archive", "run_repo_maintenance"]}, "maxItems": 10},
    "flagged_by": {"type": "string", "maxLength": 200}}, "required": ["note_id", "kind", "confidence", "reason"], "additionalProperties": False})
class MemoryFlagForReviewTool(_CMF2Tool):
    @property
    def name(self) -> str: return "memory_flag_for_review"
    @property
    def description(self) -> str: return "Add a structured review flag; repeated flags only update when confidence increases."
    async def execute(self, **kwargs: Any) -> str:
        return await self._run(f2.memory_flag_for_review, kwargs["note_id"], kwargs["kind"], kwargs["confidence"], kwargs["reason"], write=True,
                               related_actions=kwargs.get("related_actions"), flagged_by=kwargs.get("flagged_by", "agent:memory-maintenance"))


@tool_parameters({"type": "object", "properties": {
    "note_id": {"type": "string", "pattern": NOTE_ID_PATTERN}, "kind": {"type": "string", "enum": sorted(f2.REVIEW_KINDS)},
    "resolution": {"type": "string", "enum": sorted(f2.RESOLUTIONS)}, "reason": {"type": "string", "maxLength": 500}},
    "required": ["note_id", "kind", "resolution"], "additionalProperties": False})
class MemoryResolveReviewTool(_CMF2Tool):
    @property
    def name(self) -> str: return "memory_resolve_review"
    @property
    def description(self) -> str: return "Resolve, acknowledge or reopen a review flag; resolve_cold/resolve_forget also enact the requested transition."
    async def execute(self, **kwargs: Any) -> str:
        return await self._run(f2.memory_resolve_review, kwargs["note_id"], kwargs["kind"], kwargs["resolution"], write=True, reason=kwargs.get("reason", "manual resolve"))


@tool_parameters({"type": "object", "properties": {}, "additionalProperties": False})
class MemoryStorageStatsTool(_CMF2Tool):
    @property
    def name(self) -> str: return "memory_storage_stats"
    @property
    def description(self) -> str: return "Measure bundle storage usage, including Git objects, assets, archive and graph artifacts."
    @property
    def read_only(self) -> bool: return True
    async def execute(self, **kwargs: Any) -> str:
        del kwargs
        return await self._run(f2.storage_stats)


@tool_parameters({"type": "object", "properties": {
    "dry_run": {"type": "boolean"}, "reason": {"type": "string", "maxLength": 500}}, "additionalProperties": False})
class MemoryRepoMaintenanceTool(_CMF2Tool):
    @property
    def name(self) -> str: return "memory_repo_maintenance"
    @property
    def description(self) -> str: return "Inspect Git compaction by default; run non-destructive git gc only when dry_run=false."
    async def execute(self, **kwargs: Any) -> str:
        dry_run = kwargs.get("dry_run", True)
        return await self._run(f2.memory_repo_maintenance, write=not dry_run, dry_run=dry_run,
                               reason=kwargs.get("reason", "scheduled maintenance"))


@tool_parameters({"type": "object", "properties": {
    "isolation_ttl_days": {"type": "integer", "minimum": 1, "maximum": 36500},
    "cold_ttl_days": {"type": "integer", "minimum": 1, "maximum": 36500}}, "additionalProperties": False})
class MemoryAgingCandidatesTool(_CMF2Tool):
    @property
    def name(self) -> str: return "memory_aging_candidates"
    @property
    def description(self) -> str: return "List disconnected or cold CM notes that reached their lifecycle age thresholds; does not mutate them."
    @property
    def read_only(self) -> bool: return True
    async def execute(self, **kwargs: Any) -> str:
        return await self._run(f2.aging_candidates, isolation_ttl_days=kwargs.get("isolation_ttl_days"),
                               cold_ttl_days=kwargs.get("cold_ttl_days"))
