"""Native AK read, search, list, stats and isolation tools."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from nanobot.agent.kg.ak import read as ak_read
from nanobot.agent.kg.roots import allowed_bundle_root
from nanobot.agent.tools.base import Tool, tool_parameters
from nanobot.agent.tools.context import ToolContext
from nanobot.config.kg import PercivalKgConfig


class AKTool(Tool):
    """Base class for native AK tools. Mirrors CMTool contract."""

    _scopes = {"core"}

    def __init__(self, workspace: str, kg_config: PercivalKgConfig, restrict_to_workspace: bool):
        self.workspace = Path(workspace).expanduser().resolve()
        self.kg_config = kg_config
        self.restrict_to_workspace = restrict_to_workspace

    @classmethod
    def enabled(cls, ctx: ToolContext) -> bool:
        return ctx.kg_config is None or ctx.kg_config.mode in {"native", "both"}

    @classmethod
    def create(cls, ctx: ToolContext) -> "AKTool":
        return cls(
            ctx.workspace,
            ctx.kg_config or PercivalKgConfig(),
            ctx.config.restrict_to_workspace,
        )

    def _root(self, *, write: bool = False) -> Path:
        return allowed_bundle_root(
            "ak",
            self.kg_config,
            self.workspace,
            restrict_to_workspace=self.restrict_to_workspace,
            write=write,
        )


@tool_parameters({
    "type": "object",
    "properties": {
        "kind": {"type": ["string", "null"], "enum": ["Source", "ExtractedNote"]},
        "limit": {"type": "integer", "minimum": 1, "maximum": 10000},
    },
    "additionalProperties": False,
})
class AKSourceListTool(AKTool):
    @property
    def name(self) -> str:
        return "ak_source_list"

    @property
    def description(self) -> str:
        return "List Sources and/or ExtractedNotes with metadata (no body)."

    @property
    def read_only(self) -> bool:
        return True

    async def execute(self, **kwargs: Any) -> str:
        from nanobot.agent.kg.ak import to_json
        result = await asyncio.to_thread(
            ak_read.source_list,
            self._root(),
            kind=kwargs.get("kind"),
            limit=kwargs.get("limit", 50),
        )
        return to_json(result)


@tool_parameters({
    "type": "object",
    "properties": {
        "query": {"type": "string", "minLength": 1, "maxLength": 500},
        "kind": {"type": ["string", "null"], "enum": ["Source", "ExtractedNote"]},
        "limit": {"type": "integer", "minimum": 1, "maximum": 200},
    },
    "required": ["query"],
    "additionalProperties": False,
})
class AKSourceSearchTool(AKTool):
    @property
    def name(self) -> str:
        return "ak_source_search"

    @property
    def description(self) -> str:
        return "Case-insensitive substring search across all notes in the AK bundle."

    @property
    def read_only(self) -> bool:
        return True

    async def execute(self, **kwargs: Any) -> str:
        from nanobot.agent.kg.ak import to_json
        result = await asyncio.to_thread(
            ak_read.source_search,
            self._root(),
            kwargs["query"],
            kind=kwargs.get("kind"),
            limit=kwargs.get("limit", 50),
        )
        return to_json(result)


@tool_parameters({
    "type": "object",
    "properties": {},
    "additionalProperties": False,
})
class AKSourceStatsTool(AKTool):
    @property
    def name(self) -> str:
        return "ak_source_stats"

    @property
    def description(self) -> str:
        return "Bundle health: counts, partial atomisation, orphans, cache, telemetry."

    @property
    def read_only(self) -> bool:
        return True

    async def execute(self, **kwargs: Any) -> str:
        del kwargs
        from nanobot.agent.kg.ak import to_json
        result = await asyncio.to_thread(ak_read.source_stats, self._root())
        return to_json(result)


@tool_parameters({
    "type": "object",
    "properties": {},
    "additionalProperties": False,
})
class AKGetLaterallyIsolatedNotesTool(AKTool):
    @property
    def name(self) -> str:
        return "ak_get_laterally_isolated_notes"

    @property
    def description(self) -> str:
        return "Return notes with no lateral edges and not back-referenced; candidates for backfill."

    @property
    def read_only(self) -> bool:
        return True

    async def execute(self, **kwargs: Any) -> str:
        del kwargs
        from nanobot.agent.kg.ak import to_json
        result = await asyncio.to_thread(
            ak_read.get_laterally_isolated_notes, self._root()
        )
        return to_json(result)
