"""F4 read-only discovery: source_list, source_search, source_stats, isolation scan."""

from __future__ import annotations

from pathlib import Path

import pytest

from nanobot.agent.kg.ak import read as ak_read
from nanobot.agent.kg.ak.core import PathEscapeError, write_source_note
from nanobot.agent.kg.ak.parsers import mimetype_from_suffix


def _init_bundle(tmp_path: Path) -> Path:
    bundle = tmp_path / ".acquired-knowledge"
    (bundle / "notes").mkdir(parents=True)
    return bundle


def _ingest(bundle: Path, note_id: str, title: str, body: str, *,
            source_kind: str = "document", extra: dict | None = None) -> None:
    write_source_note(
        bundle,
        source_id=note_id,
        title=title,
        body=body,
        source_kind=source_kind,
        file_path="sources/file.pdf",
        content_sha256="x" * 64,
        media_type=mimetype_from_suffix(".pdf"),
        size_bytes=10,
        chunks_total=1,
        parsed_chars=len(body),
        page_count=None,
        tags=None,
        extra=extra,
    )


def test_source_list_filters_by_kind_and_reports_partial_atomisation(tmp_path: Path) -> None:
    bundle = _init_bundle(tmp_path)
    write_source_note(
        bundle, source_id="20261005-100000", title="Source A", body="body",
        source_kind="document", file_path="sources/file.pdf",
        content_sha256="a" * 64, media_type="application/pdf", size_bytes=10,
        chunks_total=2, parsed_chars=4, page_count=None, tags=None,
        extra={"chunks_atomized": [0]},
    )
    write_source_note(
        bundle, source_id="20261005-100001", title="Source B", body="body",
        source_kind="image", file_path="sources/photo.png",
        content_sha256="b" * 64, media_type="image/png", size_bytes=1,
        chunks_total=1, parsed_chars=4, page_count=None, tags=None,
    )
    extracted_id = "20261005-100002"
    write_source_note(
        bundle,
        source_id=extracted_id,
        title="Extracted A",
        body="extracted",
        note_type="ExtractedNote",
        source_kind="image",
        file_path="sources/photo.png",
        content_sha256="c" * 64,
        media_type="image/png",
        size_bytes=1,
        chunks_total=0,
        parsed_chars=0,
        page_count=None,
        tags=None,
        extra={"derived_from": ["20261005-100000"]},
    )

    all_items = ak_read.source_list(bundle, limit=10)
    assert {item["type"] for item in all_items} == {"Source", "ExtractedNote"}
    only_sources = ak_read.source_list(bundle, kind="Source", limit=10)
    assert all(item["type"] == "Source" for item in only_sources)
    only_extracted = ak_read.source_list(bundle, kind="ExtractedNote", limit=10)
    assert len(only_extracted) == 1
    assert only_extracted[0]["id"] == extracted_id
    assert only_extracted[0]["derived_from"] == ["20261005-100000"]
    partial = next(item for item in only_sources if item["id"] == "20261005-100000")
    assert partial["partially_atomized"] is True
    full = next(item for item in only_sources if item["id"] == "20261005-100001")
    assert full["partially_atomized"] is False


def test_source_search_is_case_insensitive_and_respects_limit(tmp_path: Path) -> None:
    bundle = _init_bundle(tmp_path)
    _ingest(bundle, "20261005-100003", "Paper", "The Hypothesis of Everything")
    _ingest(bundle, "20261005-100004", "Notes", "The theory of nothing")
    results = ak_read.source_search(bundle, "hypotHesis", limit=10)
    assert len(results) == 1
    assert results[0]["id"] == "20261005-100003"
    with pytest.raises(ValueError, match="non-empty"):
        ak_read.source_search(bundle, "", limit=1)
    with pytest.raises(ValueError, match="limit"):
        ak_read.source_search(bundle, "hypothesis", limit=0)


def test_source_stats_reports_partial_atomisation_orphans_and_isolation(tmp_path: Path) -> None:
    bundle = _init_bundle(tmp_path)
    write_source_note(
        bundle, source_id="20261005-110000", title="Source", body="body",
        source_kind="document", file_path="sources/file.pdf",
        content_sha256="a" * 64, media_type="application/pdf", size_bytes=10,
        chunks_total=2, parsed_chars=4, page_count=None, tags=None,
        extra={"chunks_atomized": [0]},
    )
    write_source_note(
        bundle,
        source_id="20261005-110001",
        title="Isolated",
        body="## Links\n\nNo outgoing edges here.\n",
        note_type="ExtractedNote",
        source_kind="image",
        file_path="sources/x.png",
        content_sha256="z" * 64,
        media_type="image/png",
        size_bytes=1,
        chunks_total=0,
        parsed_chars=0,
        page_count=None,
        tags=None,
        extra={"derived_from": ["20261005-110000"]},
    )
    stats = ak_read.source_stats(bundle)
    assert stats["sources_total"] == 1
    assert stats["extracted_total"] == 1
    assert stats["partially_atomized"] == 1
    # Both notes are laterally isolated: no `## Links` block in either and
    # the Source is not back-referenced from any other note.
    assert stats["laterally_isolated"] == 2
    assert stats["orphan_extracted"] == 0
    assert stats["notes_total"] == 2


def test_get_laterally_isolated_notes_groups_by_source(tmp_path: Path) -> None:
    bundle = _init_bundle(tmp_path)
    for idx, (nid, derived) in enumerate(
        (
            ("20261005-120000", ["20261005-110000"]),
            ("20261005-120001", ["20261005-110000"]),
        ),
    ):
        write_source_note(
            bundle,
            source_id=nid,
            title=f"Isolated {idx}",
            body="isolated body without outgoing links",
            note_type="ExtractedNote",
            source_kind="image",
            file_path="sources/x.png",
            content_sha256=str(idx) * 64,
            media_type="image/png",
            size_bytes=1,
            chunks_total=0,
            parsed_chars=0,
            page_count=None,
            tags=None,
            extra={"derived_from": derived},
        )
    result = ak_read.get_laterally_isolated_notes(bundle)
    assert result["count"] == 2
    assert {note["source_id"] for note in result["isolated_notes"]} == {"20261005-110000"}
    assert result["by_source"] == {"20261005-110000": 2}


def test_note_discovery_rejects_external_symlink_instead_of_reading_it(tmp_path: Path) -> None:
    bundle = _init_bundle(tmp_path)
    outside = tmp_path / "private.md"
    outside.write_text(
        "---\ntype: Source\nid: 20261005-130000\ntitle: private\n---\nsecret needle\n",
        encoding="utf-8",
    )
    (bundle / "notes" / "20261005-130000-private.md").symlink_to(outside)
    with pytest.raises(PathEscapeError):
        ak_read.source_list(bundle)
    with pytest.raises(PathEscapeError):
        ak_read.source_search(bundle, "secret")
    with pytest.raises(PathEscapeError):
        ak_read.source_stats(bundle)
