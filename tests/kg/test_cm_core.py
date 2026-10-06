"""F1 native CM note tools preserve bundle and workspace contracts."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

import pytest

from nanobot.agent.kg.vendor.okf_bundle_core.gitstore import GitStore
from nanobot.agent.kg.vendor.okf_bundle_core.paths import PathEscapeError
from nanobot.agent.kg.vendor.okf_bundle_core.zettel import CASMismatchError
from nanobot.agent.tools.cm_notes import (
    CMNoteHistoryTool,
    CMNotesReadTool,
    CMNotesSearchTool,
    CMNotesWriteTool,
)
from nanobot.agent.tools.context import RequestContext, ToolContext, request_context
from nanobot.agent.tools.registry import ToolRegistry
from nanobot.config.kg import PercivalKgConfig
from nanobot.config.schema import ToolsConfig
from nanobot.security.workspace_policy import WorkspaceBoundaryError

NOTE_ID = "20261005-120000"


def _tools(workspace: Path, *, config: PercivalKgConfig | None = None, restricted: bool = False):
    ctx = ToolContext(
        config=ToolsConfig(restrict_to_workspace=restricted),
        workspace=str(workspace),
        kg_config=config or PercivalKgConfig(),
    )
    return (
        CMNotesReadTool.create(ctx),
        CMNotesWriteTool.create(ctx),
        CMNotesSearchTool.create(ctx),
        CMNoteHistoryTool.create(ctx),
    )


@pytest.mark.asyncio
async def test_cm_write_read_cas_and_json_excludes_typed_frontmatter(tmp_path: Path) -> None:
    read, write, _, _ = _tools(tmp_path)
    created = json.loads(await write.execute(id=NOTE_ID, body="F1 content", frontmatter_patch={"title": "F1"}))
    assert created["id"] == NOTE_ID
    assert len(created["content_hash"]) == 64

    result = json.loads(await read.execute(id=NOTE_ID))
    assert result["body"] == "F1 content"
    assert result["frontmatter"]["title"] == "F1"
    assert "frontmatter_typed" not in result

    updated = json.loads(await write.execute(
        id=NOTE_ID,
        body="updated body",
        expected_body_hash=result["body_hash"],
    ))
    assert updated["body_hash"] != result["body_hash"]
    with pytest.raises(CASMismatchError):
        await write.execute(id=NOTE_ID, body="stale", expected_body_hash=result["body_hash"])
    assert json.loads(await read.execute(id=NOTE_ID))["body"] == "updated body"


@pytest.mark.asyncio
async def test_cm_write_rolls_back_note_and_log_when_git_commit_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, write, _, _ = _tools(tmp_path)

    def fail_commit(self: GitStore, paths: list[Path], message: str) -> str:
        raise OSError("simulated commit failure")

    monkeypatch.setattr(GitStore, "commit_paths", fail_commit)
    with pytest.raises(OSError, match="simulated commit failure"):
        await write.execute(id=NOTE_ID, body="must roll back")
    bundle = tmp_path / ".collective-memory"
    assert not list((bundle / "notes").glob("*.md"))
    assert not (bundle / "log.md").exists()


@pytest.mark.asyncio
async def test_cm_search_is_case_insensitive_bounded_and_does_not_call_rg(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, write, search, _ = _tools(tmp_path)
    await write.execute(id=NOTE_ID, body="A searchable Needle")

    def fail_subprocess(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        raise AssertionError("search must not invoke an external process")

    monkeypatch.setattr(subprocess, "run", fail_subprocess)
    hits = json.loads(await search.execute(query="needle", limit=1))
    assert len(hits) == 1
    assert hits[0]["id"] == NOTE_ID
    assert hits[0]["snippet"] == "A searchable Needle"
    with pytest.raises(ValueError, match="limit"):
        await search.execute(query="needle", limit=201)


@pytest.mark.asyncio
async def test_cm_history_returns_note_commits(tmp_path: Path) -> None:
    _, write, _, history = _tools(tmp_path)
    await write.execute(id=NOTE_ID, body="first")
    await write.execute(id=NOTE_ID, body="second")
    result = json.loads(await history.execute(note_id=NOTE_ID))
    assert result["id"] == NOTE_ID
    assert len(result["history"]) == 2
    assert result["history"][0]["message"].startswith(f"mem(percival): write {NOTE_ID}")


@pytest.mark.asyncio
async def test_cm_note_symlink_cannot_read_or_overwrite_outside_bundle(tmp_path: Path) -> None:
    read, write, search, _ = _tools(tmp_path)
    external = tmp_path / "outside.md"
    external.write_text("---\ntype: Note\nid: 20261005-120000\n---\nsecret", encoding="utf-8")
    bundle = tmp_path / ".collective-memory"
    notes_dir = bundle / "notes"
    notes_dir.mkdir(parents=True)
    (notes_dir / f"{NOTE_ID}-external.md").symlink_to(external)

    with pytest.raises(PathEscapeError):
        await read.execute(id=NOTE_ID)
    with pytest.raises(PathEscapeError):
        await search.execute(query="secret")
    with pytest.raises(PathEscapeError):
        await write.execute(id=NOTE_ID, body="overwrite")
    assert external.read_text(encoding="utf-8").endswith("secret")


@pytest.mark.asyncio
async def test_cm_root_follows_request_workspace_and_restricts_external_write(tmp_path: Path) -> None:
    first, second = tmp_path / "first", tmp_path / "second"
    read, write, _, _ = _tools(first)
    await write.execute(id=NOTE_ID, body="first workspace")
    with request_context(RequestContext(channel="websocket", chat_id="two", workspace=second)):
        await write.execute(id=NOTE_ID, body="second workspace")
        assert json.loads(await read.execute(id=NOTE_ID))["body"] == "second workspace"
    assert json.loads(await read.execute(id=NOTE_ID))["body"] == "first workspace"

    outside = tmp_path / "external"
    restricted_read, restricted_write, _, _ = _tools(
        first,
        config=PercivalKgConfig(cm_root=outside),
        restricted=True,
    )
    with pytest.raises(WorkspaceBoundaryError):
        await restricted_write.execute(id=NOTE_ID, body="denied")
    with pytest.raises(WorkspaceBoundaryError):
        await restricted_read.execute(id=NOTE_ID)


def test_loader_registers_exact_four_cm_tools_and_obeys_mode(tmp_path: Path) -> None:
    from nanobot.agent.tools.loader import ToolLoader

    native = ToolRegistry()
    ctx = ToolContext(
        config=ToolsConfig(), workspace=str(tmp_path), kg_config=PercivalKgConfig(mode="native")
    )
    registered = ToolLoader().load(ctx, native)
    cm_tools = {name for name in registered if name.startswith("cm_") or name == "cm_note_history"}
    assert cm_tools == {"cm_notes_read", "cm_notes_write", "cm_notes_search", "cm_note_history"}

    mcp_only = ToolRegistry()
    mcp_ctx = ToolContext(
        config=ToolsConfig(), workspace=str(tmp_path), kg_config=PercivalKgConfig(mode="mcp")
    )
    ToolLoader().load(mcp_ctx, mcp_only)
    assert not (set(mcp_only.tool_names) & cm_tools)


def test_agent_loop_from_config_exposes_cm_tools_without_external_llm(tmp_path: Path) -> None:
    from unittest.mock import MagicMock

    from nanobot.agent.loop import AgentLoop
    from nanobot.bus.queue import MessageBus
    from nanobot.config.schema import Config

    provider = MagicMock()
    provider.get_default_model.return_value = "test-model"
    registry = ToolRegistry()
    config = Config.model_validate({
        "agents": {"defaults": {"workspace": str(tmp_path)}},
        "kg": {"mode": "native"},
    })
    AgentLoop.from_config(config, MessageBus(), tool_registry=registry, provider=provider)
    assert {name for name in registry.tool_names if name.startswith("cm_")} >= {
        "cm_notes_read", "cm_notes_write", "cm_notes_search", "cm_note_history",
    }
