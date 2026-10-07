"""F2 CM links, policy, storage and graph tools preserve bundle contracts."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest

from nanobot.agent.kg.vendor.okf_bundle_core.gitstore import GitStore
from nanobot.agent.tools.cm_notes import (
    CMNoteHistoryTool,
    CMNotesReadTool,
    CMNotesSearchTool,
    CMNotesWriteTool,
)
from nanobot.agent.tools.cm_policy import (
    AssetGetPathTool,
    GraphNeighborsTool,
    GraphShortestPathTool,
    MemoryAgingCandidatesTool,
    MemoryAttachTool,
    MemoryBatchLinkTool,
    MemoryFlagForReviewTool,
    MemoryForgetTool,
    MemoryLinkTool,
    MemoryRepoMaintenanceTool,
    MemoryResolveReviewTool,
    MemorySetLifecycleTool,
    MemorySetProtectedTool,
    MemoryStatsTool,
    MemoryStorageStatsTool,
)
from nanobot.agent.tools.context import ToolContext
from nanobot.config.kg import PercivalKgConfig
from nanobot.config.schema import ToolsConfig
from nanobot.security.workspace_policy import WorkspaceBoundaryError

NOTE_A = "20200101-010101"
NOTE_B = "20200102-020202"
TOOLS = (
    MemoryLinkTool, MemoryBatchLinkTool, MemoryAttachTool, MemoryForgetTool, MemoryStatsTool,
    AssetGetPathTool, GraphNeighborsTool, GraphShortestPathTool, MemorySetProtectedTool,
    MemorySetLifecycleTool, MemoryFlagForReviewTool, MemoryResolveReviewTool,
    MemoryStorageStatsTool, MemoryRepoMaintenanceTool, MemoryAgingCandidatesTool,
)
ALL_CM_TOOLS = (CMNoteHistoryTool, CMNotesReadTool, CMNotesSearchTool, CMNotesWriteTool, *TOOLS)


def _instances(workspace: Path, *, restricted: bool = False) -> dict[str, Any]:
    context = ToolContext(config=ToolsConfig(restrict_to_workspace=restricted), workspace=str(workspace),
                          kg_config=PercivalKgConfig(mode="native"))
    instances = [tool.create(context) for tool in ALL_CM_TOOLS]
    return {tool.name: tool for tool in instances}


async def _write(tools: dict[str, Any], note_id: str, body: str = "note") -> dict[str, Any]:
    return json.loads(await tools["cm_notes_write"].execute(id=note_id, body=body))


@pytest.mark.asyncio
async def test_links_allow_forward_refs_are_idempotent_and_batch_reports_partial_success(tmp_path: Path) -> None:
    tools = _instances(tmp_path)
    await _write(tools, NOTE_A, "Source")
    linked = json.loads(await tools["memory_link"].execute(from_id=NOTE_A, to_id=NOTE_B, relation="related"))
    assert linked["changed"] is True
    assert "related :: [[20200102-020202]]" in json.loads(await tools["cm_notes_read"].execute(id=NOTE_A))["body"]
    skipped = json.loads(await tools["memory_link"].execute(from_id=NOTE_A, to_id=NOTE_B, relation="related"))
    assert skipped["changed"] is False

    batch = json.loads(await tools["memory_batch_link"].execute(edges=[
        {"from_id": NOTE_A, "to_id": NOTE_B, "relation": "supersedes"},
        {"from_id": NOTE_A, "to_id": NOTE_A},
        {"from_id": NOTE_B, "to_id": NOTE_A},
    ]))
    assert (batch["applied_count"], batch["error_count"]) == (1, 2)
    assert batch["items"][1]["status"] == "error"
    flat_batch = json.loads(await tools["memory_batch_link"].execute(
        from_ids=[NOTE_A], to_ids=[NOTE_B], relations=["supersedes"],
    ))
    assert flat_batch["skipped_count"] == 1
    result = json.loads(await tools["cm_notes_read"].execute(id=NOTE_A))
    assert result["frontmatter"]["supersedes"] == [NOTE_B]


@pytest.mark.asyncio
async def test_attach_asset_path_policy_and_forget_archives_instead_of_deleting(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    tools = _instances(tmp_path)
    await _write(tools, NOTE_A)
    bundle = tmp_path / ".collective-memory"
    asset = bundle / "assets" / "paper.pdf"
    asset.parent.mkdir(parents=True)
    asset.write_bytes(b"pdf")
    attached = json.loads(await tools["memory_attach"].execute(note_id=NOTE_A, asset_path="assets/paper.pdf"))
    assert attached["changed"] is True
    resolved = json.loads(await tools["asset_get_path"].execute(asset_ref=NOTE_A))
    assert resolved["rel_path"] == "assets/paper.pdf"
    with pytest.raises(ValueError):
        await tools["memory_attach"].execute(note_id=NOTE_A, asset_path="../outside")

    source = next((bundle / "notes").glob(f"{NOTE_A}-*.md"))
    month = datetime.now(timezone.utc).strftime("%Y%m")
    previous_archive = bundle / "_archive" / month / source.name
    previous_archive.parent.mkdir(parents=True)
    previous_archive.write_text("previous archive revision", encoding="utf-8")
    forgotten = json.loads(await tools["memory_forget"].execute(note_id=NOTE_A, reason="obsolete"))
    assert (bundle / forgotten["archived"]).is_file()
    assert (bundle / forgotten["archived"]) != previous_archive
    assert previous_archive.read_text(encoding="utf-8") == "previous archive revision"
    with pytest.raises(FileNotFoundError):
        await tools["cm_notes_read"].execute(id=NOTE_A)

    await _write(tools, NOTE_B)
    log_path = bundle / "log.md"
    log_before = log_path.read_text(encoding="utf-8")

    def fail_commit(self: GitStore, paths: list[Path], message: str) -> str:
        raise OSError("simulated archive commit failure")

    monkeypatch.setattr(GitStore, "commit_paths", fail_commit)
    with pytest.raises(OSError, match="simulated archive commit failure"):
        await tools["memory_forget"].execute(note_id=NOTE_B, reason="rollback check")
    assert json.loads(await tools["cm_notes_read"].execute(id=NOTE_B))["id"] == NOTE_B
    assert log_path.read_text(encoding="utf-8") == log_before


@pytest.mark.asyncio
async def test_p11_cas_protection_lifecycle_and_review_transitions(tmp_path: Path) -> None:
    tools = _instances(tmp_path)
    await _write(tools, NOTE_A)
    initial = json.loads(await tools["cm_notes_read"].execute(id=NOTE_A))
    protected = json.loads(await tools["memory_set_protected"].execute(
        note_id=NOTE_A, protected=True, expected_content_hash=initial["content_hash"],
    ))
    assert protected["changed"] is True
    with pytest.raises(ValueError, match="protected"):
        await tools["memory_set_lifecycle"].execute(note_id=NOTE_A, lifecycle="cold")

    flagged = json.loads(await tools["memory_flag_for_review"].execute(
        note_id=NOTE_A, kind="isolation_90d", confidence="low", reason="check it",
    ))
    assert flagged["applied"] is True
    no_escalation = json.loads(await tools["memory_flag_for_review"].execute(
        note_id=NOTE_A, kind="isolation_90d", confidence="low", reason="same signal",
    ))
    assert no_escalation["applied"] is False
    escalation = json.loads(await tools["memory_flag_for_review"].execute(
        note_id=NOTE_A, kind="isolation_90d", confidence="high", reason="stronger signal",
    ))
    assert escalation["applied"] is True
    reopened = json.loads(await tools["memory_resolve_review"].execute(
        note_id=NOTE_A, kind="isolation_90d", resolution="acknowledge",
    ))
    assert reopened["status"] == "acknowledged"
    cas_mismatch = json.loads(await tools["memory_set_protected"].execute(
        note_id=NOTE_A, protected=False, expected_content_hash="0" * 64,
    ))
    assert cas_mismatch["error_kind"] == "cas_mismatch"
    cold = json.loads(await tools["memory_set_lifecycle"].execute(
        note_id=NOTE_A, lifecycle="cold", force=True,
    ))
    assert cold["lifecycle"] == "cold" and cold["cooled_at"]

    await _write(tools, NOTE_B)
    await tools["memory_flag_for_review"].execute(
        note_id=NOTE_B, kind="storage_maintenance_due", confidence="medium", reason="cold it",
    )
    resolved_cold = json.loads(await tools["memory_resolve_review"].execute(
        note_id=NOTE_B, kind="storage_maintenance_due", resolution="resolve_cold",
    ))
    assert resolved_cold["side_effect"]["lifecycle"] == "cold"

    note_c = "20200103-030303"
    await _write(tools, note_c)
    await tools["memory_flag_for_review"].execute(
        note_id=note_c, kind="needs_human_forget", confidence="high", reason="archive it",
    )
    resolved_forget = json.loads(await tools["memory_resolve_review"].execute(
        note_id=note_c, kind="needs_human_forget", resolution="resolve_forget",
    ))
    assert (tmp_path / ".collective-memory" / resolved_forget["side_effect"]["archived"]).is_file()


@pytest.mark.asyncio
async def test_stats_storage_aging_and_graph_missing_then_queries(tmp_path: Path) -> None:
    tools = _instances(tmp_path)
    await _write(tools, NOTE_A, f"Link [[{NOTE_B}]]")
    await _write(tools, NOTE_B, "Target")
    await _write(tools, "20200103-030303", "Isolated old note")
    (tmp_path / ".collective-memory" / "notes" / "manual-draft.md").write_text("draft", encoding="utf-8")
    stats = json.loads(await tools["memory_stats"].execute(include_storage=True))
    assert stats["notes_total"] == 4
    assert stats["protected_count"] == 0
    assert "storage_summary" in stats
    assert json.loads(await tools["memory_stats"].execute())["storage_summary"] is None
    storage = json.loads(await tools["memory_storage_stats"].execute())
    assert storage["total_bytes"] >= 0 and ".git/" in storage["by_dir"]
    maintenance = json.loads(await tools["memory_repo_maintenance"].execute())
    assert maintenance["dry_run"] is True and maintenance["backend"] is None
    candidates = json.loads(await tools["memory_aging_candidates"].execute(isolation_ttl_days=1))
    assert candidates["total"] >= 1
    no_graph = json.loads(await tools["graph_neighbors"].execute(note_id=NOTE_A))
    assert no_graph["error_kind"] == "graph_query_missing"

    graph = tmp_path / ".collective-memory" / "graphify-out" / "graph.json"
    graph.parent.mkdir()
    graph.write_text(json.dumps({"directed": True, "multigraph": False,
                                 "graph": {}, "nodes": [{"id": NOTE_A, "label": "A"}, {"id": NOTE_B, "label": "B"}],
                                 "links": [{"source": NOTE_A, "target": NOTE_B, "relation": "related"}]}), encoding="utf-8")
    neighbors = json.loads(await tools["graph_neighbors"].execute(note_id=NOTE_A))
    assert neighbors["neighbors"][0]["id"] == NOTE_B
    path = json.loads(await tools["graph_shortest_path"].execute(from_id=NOTE_A, to_id=NOTE_B, max_hops=1))
    assert path["found"] is True and path["path"] == [NOTE_A, NOTE_B]
    assert json.loads(await tools["memory_stats"].execute())["graph_health"]["edge_types"]["related"] == 1


@pytest.mark.asyncio
async def test_f2_tools_obey_registry_mode_and_workspace_read_write_restrictions(tmp_path: Path) -> None:
    from nanobot.agent.tools.loader import ToolLoader
    from nanobot.agent.tools.registry import ToolRegistry

    native_context = ToolContext(config=ToolsConfig(), workspace=str(tmp_path), kg_config=PercivalKgConfig(mode="native"))
    native_registry = ToolRegistry()
    ToolLoader(test_classes=list(ALL_CM_TOOLS)).load(native_context, native_registry)
    expected_names = {tool.create(native_context).name for tool in TOOLS}
    assert expected_names <= set(native_registry.tool_names)
    mcp_context = ToolContext(config=ToolsConfig(), workspace=str(tmp_path), kg_config=PercivalKgConfig(mode="mcp"))
    mcp_registry = ToolRegistry()
    ToolLoader(test_classes=list(ALL_CM_TOOLS)).load(mcp_context, mcp_registry)
    assert not (expected_names & set(mcp_registry.tool_names))

    external = tmp_path.parent / f"{tmp_path.name}-external"
    external.mkdir()
    restricted_context = ToolContext(config=ToolsConfig(restrict_to_workspace=True), workspace=str(tmp_path),
                                     kg_config=PercivalKgConfig(mode="native", cm_root=str(external)))
    read_tool = MemoryStatsTool.create(restricted_context)
    with pytest.raises(WorkspaceBoundaryError):
        await read_tool.execute()
    write_tool = MemoryForgetTool.create(restricted_context)
    with pytest.raises(WorkspaceBoundaryError):
        await write_tool.execute(note_id=NOTE_A, reason="denied")
