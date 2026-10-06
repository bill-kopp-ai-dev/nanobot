"""Native AK ingest and chunk-read tools."""

from __future__ import annotations

import asyncio
from typing import Any

from nanobot.agent.kg.ak import ingest as ak_ingest
from nanobot.agent.kg.ak import to_json
from nanobot.agent.tools.ak_read import AKTool
from nanobot.agent.tools.base import tool_parameters
from nanobot.agent.tools.context import current_request_context
from nanobot.agent.tools.path_utils import resolve_workspace_path


@tool_parameters({
    "type": "object",
    "properties": {
        "src_path": {"type": "string", "minLength": 1, "maxLength": 4096},
        "title": {"type": ["string", "null"], "maxLength": 500},
        "tags": {"type": ["array", "null"], "items": {"type": "string", "maxLength": 64}, "maxItems": 50},
    },
    "required": ["src_path"],
    "additionalProperties": False,
})
class AKSourceIngestTool(AKTool):
    @property
    def name(self) -> str:
        return "ak_source_ingest"

    @property
    def description(self) -> str:
        return (
            "Ingest a file into the AK bundle: copy to sources/, parse, create a Source note. "
            "Document parsing uses the markitdown CLI; images use this turn's LLM runtime; "
            "audio is sent to the configured Groq Whisper service."
        )

    async def execute(self, **kwargs: Any) -> str:
        request = current_request_context()
        runtime = request.runtime if request is not None else None
        workspace = (request.workspace if request and request.workspace else self.workspace).resolve()
        source_path = resolve_workspace_path(
            kwargs["src_path"],
            workspace=workspace,
            allowed_dir=workspace if self.restrict_to_workspace else None,
            include_media_dir=False,
        )
        if not source_path.is_file():
            raise FileNotFoundError(source_path)
        result = await ak_ingest.source_ingest(
            self._root(write=True),
            str(source_path),
            title=kwargs.get("title"),
            tags=kwargs.get("tags"),
            runtime=runtime,
        )
        return to_json(result)


@tool_parameters({
    "type": "object",
    "properties": {
        "source_id": {"type": "string", "pattern": r"^\d{8}-\d{6}$"},
        "chunk_index": {"type": "integer", "minimum": 0, "maximum": 10000},
    },
    "required": ["source_id", "chunk_index"],
    "additionalProperties": False,
})
class AKSourceReadTool(AKTool):
    @property
    def name(self) -> str:
        return "ak_source_read"

    @property
    def description(self) -> str:
        return "Read chunk N of a previously-ingested Source note."

    @property
    def read_only(self) -> bool:
        return True

    async def execute(self, **kwargs: Any) -> str:
        result = await asyncio.to_thread(
            ak_ingest.source_read,
            self._root(),
            kwargs["source_id"],
            chunk_index=kwargs["chunk_index"],
        )
        return to_json(result)
