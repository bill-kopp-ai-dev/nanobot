"""F3: CM enrichment shares the selected turn runtime and preserves CAS."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from nanobot.agent.kg.cm.enricher import ProposedEnrichment
from nanobot.agent.kg.vendor.okf_bundle_core.zettel import CASMismatchError
from nanobot.agent.skills import SkillsLoader, valid_skill_metadata
from nanobot.agent.tools.cm_enrich import CMMemoryEnrichTool
from nanobot.agent.tools.cm_notes import CMNotesReadTool, CMNotesWriteTool
from nanobot.agent.tools.context import RequestContext, ToolContext, request_context
from nanobot.agent.tools.loader import ToolLoader
from nanobot.agent.tools.registry import ToolRegistry
from nanobot.config.kg import PercivalKgConfig
from nanobot.config.schema import ToolsConfig
from nanobot.providers.base import GenerationSettings, LLMProvider, LLMResponse
from nanobot.utils.llm_runtime import LLMRuntime

NOTE = "20261005-120000"


def tools(workspace: Path, config: PercivalKgConfig | None = None):
    ctx = ToolContext(config=ToolsConfig(), workspace=str(workspace), kg_config=config or PercivalKgConfig())
    return CMNotesWriteTool.create(ctx), CMNotesReadTool.create(ctx), CMMemoryEnrichTool.create(ctx)


def proposal(**kwargs: object) -> ProposedEnrichment:
    return ProposedEnrichment(summary="A sufficiently detailed summary of the note.",
                              tags_add=["New-Tag"], reasoning="Evidence in the body.", **kwargs)


def runtime(model: str = "selected-model", *, preset: str | None = None) -> LLMRuntime:
    provider = MagicMock(spec=LLMProvider)
    provider.generation = GenerationSettings(temperature=0.2, max_tokens=384, reasoning_effort="low")
    provider.chat_with_retry = AsyncMock(return_value=LLMResponse(content=proposal().model_dump_json()))
    return LLMRuntime.capture(provider, model, context_window_tokens=8192, model_preset=preset)


def turn(selected: LLMRuntime) -> RequestContext:
    return RequestContext(channel="websocket", chat_id="one", runtime=selected)


@pytest.mark.asyncio
async def test_missing_runtime_fails_without_inference_and_deterministic_tools_work(tmp_path: Path) -> None:
    write, read, enrich = tools(tmp_path)
    await write.execute(id=NOTE, body="Original contents of the note")
    before = json.loads(await read.execute(id=NOTE))
    missing = json.loads(await enrich.execute(note_id=NOTE))
    assert missing["status"] == "error" and missing["error_kind"] == "runtime_unavailable"
    with pytest.raises(ValueError, match="fields"):
        await enrich.execute(note_id=NOTE, fields=["verified"])
    assert json.loads(await read.execute(id=NOTE))["content_hash"] == before["content_hash"]
    ctx = ToolContext(config=ToolsConfig(), workspace=str(tmp_path), kg_config=PercivalKgConfig(cm_enrich_enabled=False))
    assert "cm_memory_enrich" not in ToolLoader().load(ctx, ToolRegistry())


@pytest.mark.asyncio
async def test_typed_proposal_fields_cas_and_skip_without_special_key(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("MINIMAX_API_KEY", raising=False)
    write, read, enrich = tools(tmp_path)
    selected = runtime()
    await write.execute(id=NOTE, body="Original contents of the note")
    with request_context(turn(selected)):
        result = json.loads(await enrich.execute(note_id=NOTE, fields=["tags"]))
        assert result["status"] == "written"
        note = json.loads(await read.execute(id=NOTE))
        assert note["body"] == "Original contents of the note"
        assert note["frontmatter"]["tags"] == ["new-tag"]
        assert not note["frontmatter"].get("summary")
        assert json.loads(await enrich.execute(note_id=NOTE, fields=["tags"]))["reason"].startswith("no-op")
        with pytest.raises(ValueError, match="fields"):
            await enrich.execute(note_id=NOTE, fields=["sources"])
        with pytest.raises(ValueError):
            ProposedEnrichment.model_validate({**proposal().model_dump(), "verified": True})
        assert json.loads(await enrich.execute(note_id=NOTE))["status"] == "written"
        calls = selected.provider.chat_with_retry.call_count
        assert json.loads(await enrich.execute(note_id=NOTE))["status"] == "skipped"
        assert selected.provider.chat_with_retry.call_count == calls

        async def concurrent_edit(**kwargs: object) -> LLMResponse:
            await write.execute(id=NOTE, body="Human updated body")
            return LLMResponse(content=ProposedEnrichment(
                summary="A newly proposed summary that differs from the previous one.",
                reasoning="Evidence in the body.",
            ).model_dump_json())

        selected.provider.chat_with_retry.side_effect = concurrent_edit
        with pytest.raises(CASMismatchError):
            await enrich.execute(note_id=NOTE, force_regen=True)
    assert json.loads(await read.execute(id=NOTE))["body"] == "Human updated body"


@pytest.mark.asyncio
async def test_same_tool_uses_each_turn_model_provider_and_captured_generation(tmp_path: Path) -> None:
    write, _, enrich = tools(tmp_path)
    await write.execute(id=NOTE, body="One note")
    first = runtime("session-preset-model", preset="session-preset")
    second = runtime("override-model")
    first.provider.generation = GenerationSettings(temperature=0.9, max_tokens=999)

    with request_context(turn(first)):
        assert json.loads(await enrich.execute(note_id=NOTE, fields=["tags"]))["status"] == "written"
    first_kwargs = first.provider.chat_with_retry.call_args.kwargs
    assert first_kwargs["model"] == "session-preset-model"
    assert (first_kwargs["temperature"], first_kwargs["max_tokens"], first_kwargs["reasoning_effort"]) == (0.2, 384, "low")
    assert first_kwargs["provider_context"].conversation_state is None
    assert first_kwargs["provider_context"].session_id is None
    assert len(first_kwargs["messages"]) == 2

    with request_context(turn(second)):
        assert json.loads(await enrich.execute(note_id=NOTE, fields=["tags"]))["status"] == "written"
    assert first.provider.chat_with_retry.call_count == 1
    assert second.provider.chat_with_retry.call_count == 1
    assert second.provider.chat_with_retry.call_args.kwargs["model"] == "override-model"


@pytest.mark.asyncio
async def test_validation_retry_and_provider_error_do_not_write(tmp_path: Path) -> None:
    write, read, enrich = tools(tmp_path)
    await write.execute(id=NOTE, body="An original note")
    before = json.loads(await read.execute(id=NOTE))["content_hash"]
    selected = runtime()
    selected.provider.chat_with_retry.side_effect = [
        LLMResponse(content='{"summary": "too short"}'),
        LLMResponse(content="not JSON"),
        LLMResponse(content=proposal().model_dump_json()),
    ]
    with request_context(turn(selected)):
        assert json.loads(await enrich.execute(note_id=NOTE, fields=["tags"]))["status"] == "written"
    assert selected.provider.chat_with_retry.call_count == 3
    assert len(selected.provider.chat_with_retry.call_args.kwargs["messages"]) == 6

    after = json.loads(await read.execute(id=NOTE))["content_hash"]
    assert after != before
    selected.provider.chat_with_retry.reset_mock()
    selected.provider.chat_with_retry.side_effect = None
    selected.provider.chat_with_retry.return_value = LLMResponse(content="bad JSON")
    with request_context(turn(selected)):
        assert json.loads(await enrich.execute(note_id=NOTE, fields=["tags"]))["error_kind"] == "invalid_output"
    assert selected.provider.chat_with_retry.call_count == 3
    assert json.loads(await read.execute(id=NOTE))["content_hash"] == after

    selected.provider.chat_with_retry.reset_mock()
    selected.provider.chat_with_retry.return_value = LLMResponse(
        content=None, finish_reason="error", error_kind="connection",
    )
    with request_context(turn(selected)):
        assert json.loads(await enrich.execute(note_id=NOTE, fields=["tags"]))["error_kind"] == "connection"
    assert selected.provider.chat_with_retry.call_count == 1
    assert json.loads(await read.execute(id=NOTE))["content_hash"] == after


@pytest.mark.asyncio
async def test_model_timeout_is_structured(tmp_path: Path) -> None:
    write, _, enrich = tools(tmp_path, PercivalKgConfig(cm_enrich_timeout_s=0.05))
    await write.execute(id=NOTE, body="Original body")
    selected = runtime()

    async def slow(**kwargs: object) -> LLMResponse:
        await asyncio.sleep(1)
        return LLMResponse(content=proposal().model_dump_json())

    selected.provider.chat_with_retry.side_effect = slow
    with request_context(turn(selected)):
        assert json.loads(await enrich.execute(note_id=NOTE))["error_kind"] == "timeout"


@pytest.mark.asyncio
async def test_git_write_finishes_if_budget_expires_after_start(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    import time

    from nanobot.agent.kg.cm import core

    write, read, enrich = tools(tmp_path, PercivalKgConfig(cm_enrich_timeout_s=0.25))
    await write.execute(id=NOTE, body="Original body")
    actual_write = core.notes_write

    def slow_write(*args: object, **kwargs: object):
        time.sleep(0.3)
        return actual_write(*args, **kwargs)

    monkeypatch.setattr(core, "notes_write", slow_write)
    with request_context(turn(runtime())):
        result = json.loads(await enrich.execute(note_id=NOTE))
    assert result["status"] == "written" and result["deadline_exceeded_after_write"] is True
    assert json.loads(await read.execute(id=NOTE))["frontmatter"]["summary"] == proposal().summary


def test_six_cm_guides_are_discoverable(tmp_path: Path) -> None:
    loader = SkillsLoader(tmp_path)
    names = {"cm-overview", "cm-notes-write", "cm-link", "cm-capture-session", "cm-audit-health", "cm-rebuild-graph"}
    assert names <= {entry["name"] for entry in loader.list_skills()}
    for name in names:
        assert valid_skill_metadata(loader.get_skill_metadata(name) or {}, name)
        assert loader.load_skill(name)


def test_native_registry_has_twenty_cm_operations(tmp_path: Path) -> None:
    ctx = ToolContext(config=ToolsConfig(), workspace=str(tmp_path), kg_config=PercivalKgConfig())
    registered = set(ToolLoader().load(ctx, ToolRegistry()))
    f1 = {"cm_notes_read", "cm_notes_write", "cm_notes_search", "cm_note_history"}
    f2 = {"memory_link", "memory_batch_link", "memory_attach", "memory_forget", "memory_stats",
          "asset_get_path", "graph_neighbors", "graph_shortest_path", "memory_set_protected",
          "memory_set_lifecycle", "memory_flag_for_review", "memory_resolve_review",
          "memory_storage_stats", "memory_repo_maintenance", "memory_aging_candidates"}
    assert f1 | f2 | {"cm_memory_enrich"} <= registered
    assert len(f1 | f2 | {"cm_memory_enrich"}) == 20
    assert "cm_memory_enrich" not in ToolLoader().load(
        ToolContext(config=ToolsConfig(), workspace=str(tmp_path), kg_config=PercivalKgConfig(mode="mcp")), ToolRegistry())
