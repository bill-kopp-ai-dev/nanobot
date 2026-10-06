"""Native collective-memory read, write, search and history tools."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from nanobot.agent.kg.cm import core
from nanobot.agent.kg.roots import allowed_bundle_root
from nanobot.agent.tools.base import Tool, tool_parameters
from nanobot.agent.tools.context import ToolContext
from nanobot.config.kg import PercivalKgConfig

_NOTE_ID = r"^\d{8}-\d{6}$"


class _CMTool(Tool):
    _scopes = {"core"}

    def __init__(self, workspace: str, kg_config: PercivalKgConfig, restrict_to_workspace: bool):
        self.workspace = Path(workspace).expanduser().resolve()
        self.kg_config = kg_config
        self.restrict_to_workspace = restrict_to_workspace

    @classmethod
    def enabled(cls, ctx: ToolContext) -> bool:
        return ctx.kg_config is None or ctx.kg_config.mode in {"native", "both"}

    @classmethod
    def create(cls, ctx: ToolContext) -> _CMTool:
        return cls(
            ctx.workspace,
            ctx.kg_config or PercivalKgConfig(),
            ctx.config.restrict_to_workspace,
        )

    def _root(self, *, write: bool = False) -> Path:
        return allowed_bundle_root(
            "cm",
            self.kg_config,
            self.workspace,
            restrict_to_workspace=self.restrict_to_workspace,
            write=write,
        )


@tool_parameters({
    "type": "object",
    "properties": {"id": {"type": "string", "pattern": _NOTE_ID}},
    "required": ["id"],
    "additionalProperties": False,
})
class CMNotesReadTool(_CMTool):
    @property
    def name(self) -> str:
        return "cm_notes_read"

    @property
    def description(self) -> str:
        return "Read one collective-memory note by its YYYYMMDD-HHMMSS id; returns hashes for CAS updates."

    @property
    def read_only(self) -> bool:
        return True

    async def execute(self, **kwargs: Any) -> str:
        return core.to_json(await asyncio.to_thread(core.notes_read, self._root(), kwargs["id"]))


@tool_parameters({
    "type": "object",
    "properties": {
        "id": {"type": "string", "pattern": _NOTE_ID},
        "body": {"type": "string", "maxLength": 1000000},
        "frontmatter_patch": {"type": ["object", "null"]},
        "expected_content_hash": {"type": ["string", "null"], "maxLength": 64},
        "expected_body_hash": {"type": ["string", "null"], "maxLength": 64},
        "reason": {"type": "string", "maxLength": 500},
    },
    "required": ["id", "body"],
    "additionalProperties": False,
})
class CMNotesWriteTool(_CMTool):
    @property
    def name(self) -> str:
        return "cm_notes_write"

    @property
    def description(self) -> str:
        return "Create or update a collective-memory note, optionally using content/body hashes for compare-and-swap."

    async def execute(self, **kwargs: Any) -> str:
        result = await asyncio.to_thread(
            core.notes_write,
            self._root(write=True),
            note_id=kwargs["id"],
            body=kwargs["body"],
            frontmatter_patch=kwargs.get("frontmatter_patch"),
            expected_content_hash=kwargs.get("expected_content_hash"),
            expected_body_hash=kwargs.get("expected_body_hash"),
            reason=kwargs.get("reason", "edit"),
        )
        return core.to_json(result)


@tool_parameters({
    "type": "object",
    "properties": {
        "query": {"type": "string", "minLength": 1, "maxLength": core.MAX_SEARCH_QUERY_CHARS},
        "limit": {"type": "integer", "minimum": 1, "maximum": core.MAX_SEARCH_RESULTS},
    },
    "required": ["query"],
    "additionalProperties": False,
})
class CMNotesSearchTool(_CMTool):
    @property
    def name(self) -> str:
        return "cm_notes_search"

    @property
    def description(self) -> str:
        return "Search collective-memory note text case-insensitively without requiring ripgrep."

    @property
    def read_only(self) -> bool:
        return True

    async def execute(self, **kwargs: Any) -> str:
        return core.to_json(await asyncio.to_thread(
            core.notes_search, self._root(), kwargs["query"], limit=kwargs.get("limit", 20),
        ))


@tool_parameters({
    "type": "object",
    "properties": {
        "note_id": {"type": "string", "pattern": _NOTE_ID},
        "limit": {"type": "integer", "minimum": 1, "maximum": core.MAX_HISTORY_ENTRIES},
    },
    "required": ["note_id"],
    "additionalProperties": False,
})
class CMNoteHistoryTool(_CMTool):
    @property
    def name(self) -> str:
        return "cm_note_history"

    @property
    def description(self) -> str:
        return "Return the most recent Git commits that changed a collective-memory note."

    @property
    def read_only(self) -> bool:
        return True

    async def execute(self, **kwargs: Any) -> str:
        return core.to_json(
            await asyncio.to_thread(
                core.note_history,
                self._root(),
                kwargs["note_id"],
                limit=kwargs.get("limit", 20),
            )
        )
