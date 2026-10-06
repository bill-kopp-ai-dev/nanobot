"""F4 ingest: source_ingest and source_read preserve bundle contracts.

The legacy markitdown subprocess is replaced with a fake to keep the
suite deterministic; the path under test is the lock/rollback discipline
and the source-read chunking, not markitdown itself.  Image and audio
ingest take the runtime from the request context and surface
``unsupported_capability`` errors as structured results.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from nanobot.agent.kg.ak import ingest as ak_ingest
from nanobot.agent.kg.ak.parsers import ParseResult
from nanobot.agent.kg.vendor.okf_bundle_core.gitstore import GitStore
from nanobot.agent.kg.vendor.okf_bundle_core.paths import ACQUIRED_KNOWLEDGE
from nanobot.agent.tools.ak_ingest import AKSourceIngestTool
from nanobot.agent.tools.context import ToolContext
from nanobot.config.kg import PercivalKgConfig
from nanobot.config.schema import ToolsConfig
from nanobot.providers.base import GenerationSettings, LLMProvider, LLMResponse
from nanobot.security.workspace_policy import WorkspaceBoundaryError
from nanobot.utils.llm_runtime import LLMRuntime


def _init_bundle(tmp_path: Path) -> Path:
    bundle = tmp_path / ".acquired-knowledge"
    (bundle / "notes").mkdir(parents=True)
    return bundle


def _patch_markitdown(monkeypatch: pytest.MonkeyPatch, *, text: str = "Parsed body") -> None:
    def fake_parse(path: Path, *, timeout: float = 60.0) -> ParseResult:
        return ParseResult(
            text=text, is_scanned_pdf=False, page_count=1, warning=None,
        )
    monkeypatch.setattr(ak_ingest, "parse_document", fake_parse)


def _vision_runtime() -> LLMRuntime:
    provider = MagicMock(spec=LLMProvider)
    provider.provider_name = "openai"
    provider.supports_modality = MagicMock(return_value=True)
    provider.generation = GenerationSettings()
    provider.chat_with_retry = AsyncMock(return_value=LLMResponse(
        content=json.dumps({
            "caption": "imagem qualquer para o teste de ingest",
            "ocr": "",
            "tags": ["fake"],
            "description": "Descrição longa o bastante para satisfazer o limite mínimo.",
        }),
    ))
    return LLMRuntime.capture(provider, "vision", context_window_tokens=4096)


@pytest.mark.asyncio
async def test_source_ingest_writes_note_copies_binary_and_returns_chunks(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_markitdown(monkeypatch, text="Paragraph one.\n\nParagraph two.")
    bundle = _init_bundle(tmp_path)
    src = tmp_path / "paper.pdf"
    src.write_bytes(b"PDF content")
    result = await ak_ingest.source_ingest(bundle, str(src))
    assert result["reused_existing"] is False
    assert result["chunks_total"] >= 1
    assert result["parsed_chars"] == len("Paragraph one.\n\nParagraph two.")

    note_path = bundle / "notes" / f"{result['source_id']}-paper.md"
    assert note_path.is_file()
    binary_path = bundle / "sources" / f"{result['source_id']}.pdf"
    assert binary_path.is_file() and binary_path.read_bytes() == b"PDF content"
    history = GitStore(bundle, ACQUIRED_KNOWLEDGE).log_for(bundle / "log.md", limit=5)
    assert len(history) == 1
    assert "source_ingest" in (bundle / "log.md").read_text(encoding="utf-8")

    chunk = ak_ingest.source_read(bundle, result["source_id"], chunk_index=0)
    assert chunk["source_id"] == result["source_id"]
    assert chunk["chunk_index"] == 0
    assert "Paragraph" in chunk["text"]
    with pytest.raises(IndexError):
        ak_ingest.source_read(bundle, result["source_id"], chunk_index=999)


@pytest.mark.asyncio
async def test_source_ingest_dedupes_existing_source_by_sha256(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_markitdown(monkeypatch, text="same text")
    bundle = _init_bundle(tmp_path)
    src = tmp_path / "paper.pdf"
    src.write_bytes(b"PDF content")
    first = await ak_ingest.source_ingest(bundle, str(src))
    second = await ak_ingest.source_ingest(bundle, str(src))
    assert second["reused_existing"] is True
    assert second["source_id"] == first["source_id"]
    binaries = list((bundle / "sources").iterdir())
    assert len([b for b in binaries if not b.name.startswith(".")]) == 1


@pytest.mark.asyncio
async def test_source_ingest_rejects_unknown_extension(tmp_path: Path) -> None:
    bundle = _init_bundle(tmp_path)
    src = tmp_path / "mystery.xyz"
    src.write_text("n/a")
    with pytest.raises(ValueError, match="unsupported"):
        await ak_ingest.source_ingest(bundle, str(src))


@pytest.mark.asyncio
async def test_source_ingest_rolls_back_note_and_binary_on_parse_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    def boom(path: Path, *, timeout: float = 60.0) -> ParseResult:
        raise RuntimeError("markitdown failed")
    monkeypatch.setattr(ak_ingest, "parse_document", boom)
    bundle = _init_bundle(tmp_path)
    src = tmp_path / "broken.pdf"
    src.write_bytes(b"unparseable")
    with pytest.raises(RuntimeError, match="markitdown failed"):
        await ak_ingest.source_ingest(bundle, str(src))
    assert list((bundle / "notes").glob("*.md")) == []
    assert list((bundle / "sources").iterdir()) == []


@pytest.mark.asyncio
async def test_source_ingest_detects_source_change_during_copy_and_cleans_staging(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    bundle = _init_bundle(tmp_path)
    source = tmp_path / "paper.pdf"
    source.write_bytes(b"original bytes")

    def changed_copy(_source: Path, destination: Path) -> None:
        destination.write_bytes(b"changed bytes")

    monkeypatch.setattr(ak_ingest, "_copy_source_atomically", changed_copy)
    with pytest.raises(RuntimeError, match="source changed while ingest was copying"):
        await ak_ingest.source_ingest(bundle, str(source))
    assert list((bundle / "sources").iterdir()) == []
    assert list((bundle / "notes").glob("*.md")) == []


@pytest.mark.asyncio
async def test_source_ingest_image_uses_request_runtime(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    bundle = _init_bundle(tmp_path)
    src = tmp_path / "shot.png"
    src.write_bytes(b"\x89PNG\r\n\x1a\nfakepng")
    runtime = _vision_runtime()
    result = await ak_ingest.source_ingest(bundle, str(src), runtime=runtime)
    assert result["source_kind"] == "image"
    assert result["chunks_total"] >= 1
    runtime.provider.chat_with_retry.assert_awaited_once()


@pytest.mark.asyncio
async def test_source_ingest_image_without_runtime_raises_unsupported(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    bundle = _init_bundle(tmp_path)
    src = tmp_path / "shot.png"
    src.write_bytes(b"\x89PNG\r\n\x1a\nfakepng")
    with pytest.raises(Exception) as exc:
        await ak_ingest.source_ingest(bundle, str(src), runtime=None)
    assert "runtime" in str(exc.value).lower() or "unsupported" in str(exc.value).lower()


@pytest.mark.asyncio
async def test_source_ingest_commit_failure_rolls_back_note_binary_and_log(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_markitdown(monkeypatch)
    bundle = _init_bundle(tmp_path)
    old_log = "existing audit history\n"
    (bundle / "log.md").write_text(old_log, encoding="utf-8")
    source = tmp_path / "paper.pdf"
    source.write_bytes(b"PDF bytes")

    def fail_commit(self: GitStore, paths: list[Path], message: str) -> str:
        raise OSError("simulated AK commit failure")

    monkeypatch.setattr(GitStore, "commit_paths", fail_commit)
    with pytest.raises(OSError, match="simulated AK commit failure"):
        await ak_ingest.source_ingest(bundle, str(source))
    assert list((bundle / "notes").glob("*.md")) == []
    assert list((bundle / "sources").iterdir()) == []
    assert (bundle / "log.md").read_text(encoding="utf-8") == old_log


@pytest.mark.asyncio
async def test_ingest_tool_rejects_source_outside_restricted_workspace(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    outside = tmp_path / "outside.pdf"
    outside.write_bytes(b"private")
    ctx = ToolContext(
        config=ToolsConfig(restrict_to_workspace=True),
        workspace=str(workspace),
        kg_config=PercivalKgConfig(),
    )
    tool = AKSourceIngestTool.create(ctx)
    with pytest.raises(WorkspaceBoundaryError):
        await tool.execute(src_path=str(outside))


def test_source_read_rejects_non_source_note(tmp_path: Path) -> None:
    bundle = _init_bundle(tmp_path)
    extracted_id = "20261005-130000"
    (bundle / "notes").mkdir(parents=True, exist_ok=True)
    (bundle / "notes" / f"{extracted_id}-note.md").write_text(
        "---\ntype: ExtractedNote\nid: 20261005-130000\n---\nbody\n", encoding="utf-8",
    )
    with pytest.raises(ValueError, match="not a Source"):
        ak_ingest.source_read(bundle, extracted_id, chunk_index=0)
