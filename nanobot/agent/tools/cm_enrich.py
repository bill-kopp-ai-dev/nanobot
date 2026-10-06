"""Native CM enrichment tool using the selected runtime for this request."""

from __future__ import annotations

from typing import Any

from nanobot.agent.kg.cm import core, enrich
from nanobot.agent.tools.base import tool_parameters
from nanobot.agent.tools.cm_notes import NOTE_ID_PATTERN, CMTool
from nanobot.agent.tools.context import ToolContext, current_request_context


@tool_parameters({
    "type": "object",
    "properties": {
        "note_id": {"type": "string", "pattern": NOTE_ID_PATTERN},
        "fields": {"type": ["array", "null"], "items": {"type": "string", "enum": sorted(enrich.FIELDS)}, "maxItems": 3},
        "force_regen": {"type": "boolean"},
        "reason": {"type": "string", "maxLength": 500},
    },
    "required": ["note_id"], "additionalProperties": False,
})
class CMMemoryEnrichTool(CMTool):
    @classmethod
    def enabled(cls, ctx: ToolContext) -> bool:
        return super().enabled(ctx) and (ctx.kg_config is None or ctx.kg_config.cm_enrich_enabled)

    @property
    def name(self) -> str:
        return "cm_memory_enrich"

    @property
    def description(self) -> str:
        return "Propose typed CM summary/tags/supersedes with this turn's model and provider; write metadata with body-hash CAS."

    async def execute(self, **kwargs: Any) -> str:
        request = current_request_context()
        runtime = request.runtime if request is not None else None
        return core.to_json(await enrich.memory_enrich(
            self._root(write=True), kwargs["note_id"], config=self.kg_config, runtime=runtime,
            fields=kwargs.get("fields"), force_regen=kwargs.get("force_regen", False),
            reason=kwargs.get("reason", "nightly enrich"),
        ))
