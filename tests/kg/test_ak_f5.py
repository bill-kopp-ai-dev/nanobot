"""F5: atomization, edge semantics, graph queries and archival."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from nanobot.agent.kg.ak import forget, graph, ingest, read, write
from nanobot.agent.kg.ak.core import gitstore, read_note, write_source_note
from nanobot.agent.kg.ak.parsers import ParseResult
from nanobot.agent.kg.vendor.okf_bundle_core.errors import CASMismatchError
from nanobot.agent.kg.vendor.okf_bundle_core.gitstore import GitStore
from nanobot.agent.kg.vendor.okf_bundle_core.graph import build_graph
from nanobot.agent.kg.vendor.okf_bundle_core.paths import ACQUIRED_KNOWLEDGE, PathEscapeError
from nanobot.agent.tools.ak_f5 import AKNoteWriteExtractedTool, AKSourceForgetTool
from nanobot.agent.tools.context import ToolContext
from nanobot.config.kg import PercivalKgConfig
from nanobot.config.schema import ToolsConfig


def _bundle(tmp_path: Path) -> tuple[Path, str]:
    root = tmp_path / ".acquired-knowledge"
    (root / "notes").mkdir(parents=True)
    (root / "sources").mkdir()
    source_id = "20261006-120000"
    (root / "sources" / f"{source_id}.txt").write_text("raw source")
    path = write_source_note(
        root, source_id=source_id, title="Test source", body="## Conteúdo extraído\n\ntext\n",
        source_kind="document", file_path=f"sources/{source_id}.txt", content_sha256="a" * 64,
        media_type="text/plain", size_bytes=10, chunks_total=2, parsed_chars=4,
        page_count=None, tags=None,
    )
    store = gitstore(root)
    store.commit_paths([path], "fixture source")
    return root, source_id


def test_atomize_resume_and_reingest(tmp_path: Path) -> None:
    root, source_id = _bundle(tmp_path)
    (root / "notes" / "20261006-120001-malformed.md").write_text("---\ntype: [\n")
    current_hash = read_note(root, source_id)["content_hash"]
    first = write.note_write_extracted(root, source_id, 0, "finding", "Extracted finding",
                                       expected_content_hash=current_hash)
    assert first["applied"] is True
    with pytest.raises(CASMismatchError):
        write.note_write_extracted(root, source_id, 1, "stale", "body",
                                   expected_content_hash=current_hash)
    assert read_note(root, source_id)["frontmatter"]["chunks_atomized"] == [0]
    assert read.source_stats(root)["partially_atomized"] == 1
    second = write.note_write_extracted(root, source_id, 0, "duplicate", "Ignored")
    assert second["reused_existing_id"] == first["extracted_id"]
    assert len(list((root / "notes").glob("*.md"))) == 3
    src_path = next((root / "notes").glob(f"{source_id}-*.md"))
    text = src_path.read_text()
    src_path.write_text(text.replace("chunks_atomized:\n- 0", "chunks_atomized: []"))
    resumed = write.note_write_extracted(root, source_id, 0, "duplicate", "Ignored")
    assert resumed["applied"] is False
    assert read_note(root, source_id)["frontmatter"]["chunks_atomized"] == [0]
    third = write.note_write_extracted(root, source_id, 1, "second", "More")
    assert third["extracted_id"] != first["extracted_id"]
    assert read_note(root, source_id)["frontmatter"]["chunks_atomized"] == [0, 1]
    with pytest.raises(IndexError):
        write.note_write_extracted(root, source_id, 2, "out", "No")
    with pytest.raises(ValueError, match="canonical"):
        write.note_link(source_id, source_id + "\n", "20261006-200000", "related")


@pytest.mark.asyncio
async def test_reingest_reuses_atomized_source(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / ".acquired-knowledge"
    (root / "notes").mkdir(parents=True)
    original = tmp_path / "paper.txt"
    original.write_text("document bytes")
    monkeypatch.setattr(ingest, "parse_document", lambda path: ParseResult(
        text="A parsed document", is_scanned_pdf=False, page_count=None, warning=None))
    first = await ingest.source_ingest(root, str(original))
    extracted = write.note_write_extracted(root, first["source_id"], 0, "finding", "body")
    second = await ingest.source_ingest(root, str(original))
    assert second["reused_existing"] is True
    assert second["source_id"] == first["source_id"]
    assert read_note(root, first["source_id"])["frontmatter"]["chunks_atomized"] == [0]
    resumed = write.note_write_extracted(root, first["source_id"], 0, "finding", "body")
    assert resumed["reused_existing_id"] == extracted["extracted_id"]


def test_atomize_commit_failure_restores_source_note_and_log(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, source_id = _bundle(tmp_path)
    old_source = read_note(root, source_id)
    (root / "log.md").write_text("existing audit\n")

    def fail(self: GitStore, paths: list[Path], message: str) -> str:
        raise OSError("commit failed")

    monkeypatch.setattr(GitStore, "commit_paths", fail)
    with pytest.raises(OSError, match="commit failed"):
        write.note_write_extracted(root, source_id, 0, "finding", "body")
    assert len(list((root / "notes").glob("*.md"))) == 1
    assert read_note(root, source_id)["content_hash"] == old_source["content_hash"]
    assert (root / "log.md").read_text() == "existing audit\n"


def test_links_batch_and_graph_d65(tmp_path: Path) -> None:
    root, source_id = _bundle(tmp_path)
    child = write.note_write_extracted(root, source_id, 0, "finding", "body")["extracted_id"]
    # Existing derived_from is visible; a second relation on the same pair
    # changes the selected graph edge only according to D65 precedence.
    assert write.note_link(root, child, source_id, "related")["written_to"] == "body"
    assert write.note_link(root, child, source_id, "related")["applied"] is False
    assert write.note_link(root, child, source_id, "contradicts")["applied"] is True
    assert write.note_link(root, child, source_id, "supersedes")["applied"] is True
    forward = "20261006-200000"
    batch = write.note_batch_link(root, [child, child, child],
                                  [forward, forward, "cm:20261006-200001"],
                                  ["related", "related", "related"])
    assert [item["status"] for item in batch["items"]] == ["applied", "skipped", "error"]
    assert (batch["applied_count"], batch["skipped_count"], batch["error_count"]) == (1, 1, 1)
    with pytest.raises(ValueError):
        write.note_batch_link(root, [child], [])
    build_graph(root, ACQUIRED_KNOWLEDGE)
    adjacent = graph.graph_neighbors(root, child)
    assert any(n["id"] == source_id and n["relation"] == "supersedes"
               for n in adjacent["neighbors"])
    assert graph.graph_neighbors(root, child, ["derived_from"])["neighbors"] == []
    assert graph.graph_shortest_path(root, child, source_id)["path"] == [child, source_id]
    assert graph.graph_shortest_path(root, child, source_id, max_hops=0)["found"] is False


def test_forget_archives_note_and_binary_without_moving_derived(tmp_path: Path) -> None:
    root, source_id = _bundle(tmp_path)
    child = write.note_write_extracted(root, source_id, 0, "finding", "body")["extracted_id"]
    result = forget.source_forget(root, source_id, reason="test\nretirement")
    assert result["archived"].startswith("_archive/sources/")
    assert result["archived_binary"].startswith("_archive/sources/")
    assert (root / result["archived"]).is_file()
    assert (root / result["archived_binary"]).read_text() == "raw source"
    assert read_note(root, child)["frontmatter"]["derived_from"] == [source_id]
    assert read.source_stats(root)["orphan_extracted"] == 1
    assert "test retirement" in (root / "log.md").read_text()
    assert len((root / "log.md").read_text().splitlines()) == 2
    with pytest.raises(FileNotFoundError):
        read_note(root, source_id)


def test_forget_rolls_back_and_rejects_malicious_binary_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, source_id = _bundle(tmp_path)
    (root / "log.md").write_text("before\n")
    original = next((root / "notes").glob("*.md"))
    original.write_text(original.read_text().replace(
        f"sources/{source_id}.txt", "../outside.txt"))
    with pytest.raises(ValueError, match="file_path"):
        forget.source_forget(root, source_id)
    original.write_text(original.read_text().replace("../outside.txt", f"sources/{source_id}.txt"))

    def fail(self: GitStore, paths: list[Path], message: str) -> str:
        raise OSError("commit failed")

    monkeypatch.setattr(GitStore, "commit_paths", fail)
    with pytest.raises(OSError, match="commit failed"):
        forget.source_forget(root, source_id)
    assert original.is_file() and (root / "sources" / f"{source_id}.txt").is_file()
    assert (root / "log.md").read_text() == "before\n"


def test_graph_and_archive_reject_external_symlinks(tmp_path: Path) -> None:
    root, source_id = _bundle(tmp_path)
    outside = tmp_path / "external"
    outside.mkdir()
    (root / "graphify-out").symlink_to(outside)
    with pytest.raises(PathEscapeError):
        graph.graph_neighbors(root, source_id)
    (root / "graphify-out").unlink()
    (root / "_archive").symlink_to(outside)
    with pytest.raises(PathEscapeError):
        forget.source_forget(root, source_id)


@pytest.mark.asyncio
async def test_f5_tools_use_workspace_bundle_and_return_json(tmp_path: Path) -> None:
    root, source_id = _bundle(tmp_path)
    ctx = ToolContext(config=ToolsConfig(), workspace=str(tmp_path),
                      kg_config=PercivalKgConfig(mode="native"))
    extracted = json.loads(await AKNoteWriteExtractedTool.create(ctx).execute(
        source_id=source_id, chunk_index=0, title="finding", body="body"))
    assert extracted["applied"] is True
    archived = json.loads(await AKSourceForgetTool.create(ctx).execute(
        source_id=source_id, reason="done"))
    assert archived["archived_binary"] is not None
    assert not list((root / "sources").glob(f"{source_id}.*"))


def test_forget_refuses_symlink_to_other_internal_source(tmp_path: Path) -> None:
    root, source_id = _bundle(tmp_path)
    binary = root / "sources" / f"{source_id}.txt"
    binary.unlink()
    another = root / "sources" / "other.txt"
    another.write_text("keep")
    binary.symlink_to(another)
    with pytest.raises(PathEscapeError):
        forget.source_forget(root, source_id)
    assert another.read_text() == "keep"


def test_f5_refuses_internal_symlink_redirections(tmp_path: Path) -> None:
    root, source_id = _bundle(tmp_path)
    notes = root / "notes"
    notes.rename(root / "notes-real")
    notes.symlink_to(root / "notes-real", target_is_directory=True)
    with pytest.raises(PathEscapeError):
        write.note_link(root, source_id, "20261006-200000", "related")
    notes.unlink()
    (root / "notes-real").rename(notes)

    graph_target = root / "elsewhere"
    graph_target.mkdir()
    (graph_target / "graph.json").write_text("{}")
    (root / "graphify-out").symlink_to(graph_target, target_is_directory=True)
    with pytest.raises(PathEscapeError):
        graph.graph_neighbors(root, source_id)
    (root / "graphify-out").unlink()

    archive_target = root / "other-area"
    archive_target.mkdir()
    (root / "_archive").symlink_to(archive_target, target_is_directory=True)
    with pytest.raises(PathEscapeError):
        forget.source_forget(root, source_id)
    assert (root / "notes" / f"{source_id}-test-source.md").is_file()
