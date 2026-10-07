"""Source ingestion and chunk retrieval for AK native tools.

Mirrors the legacy ``percival-acquire-knowledge/tools.py:tool_source_ingest``
and ``:tool_source_read`` without transporting FastMCP or its
dependencies.  Document parsing happens via the ``markitdown`` CLI
subprocess wrapper in ``ak.parsers``; image and audio go through
``ak.multimodal``; vision uses the turn runtime and ASR uses nanobot's
configured Groq Whisper transcription service.

The Source note is committed atomically with its ``sources/<id>.<ext>``
binary under an exclusive ``BundleLock`` so a parse failure cannot
leave an orphan file in ``sources/`` or an uncommitted note in
``notes/`` (AK-1).
"""

from __future__ import annotations

import asyncio
import os
import shutil
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import Any, TypeVar

from nanobot.agent.kg.ak import UnsupportedCapabilityError
from nanobot.agent.kg.ak.chunking import chunk_text
from nanobot.agent.kg.ak.core import (
    ACQUIRED_KNOWLEDGE,
    INGEST_LOCK_TIMEOUT_S,
    MAX_INGEST_BYTES,
    BundleLock,
    check_bundle_paths,
    find_existing_source_by_sha256,
    gitstore,
    hash_file,
    ingested_path,
    new_id,
    note_path,
    now_iso,
    read_note,
    write_source_note,
)
from nanobot.agent.kg.ak.multimodal import audio_transcribe, image_caption
from nanobot.agent.kg.ak.parsers import detect_kind, parse_document
from nanobot.agent.kg.ak.telemetry import track
from nanobot.utils.llm_runtime import LLMRuntime

_UNKNOWN_LOG_STATE = object()
_T = TypeVar("_T")


async def _to_thread_complete(function: Callable[..., _T], *args: Any, **kwargs: Any) -> _T:
    """Keep an in-flight filesystem operation from outliving its bundle lock."""
    task = asyncio.create_task(asyncio.to_thread(function, *args, **kwargs))
    try:
        return await asyncio.shield(task)
    except asyncio.CancelledError:
        try:
            await task
        finally:
            raise


async def source_ingest(
    root: Path,
    src_path: str,
    *,
    title: str | None = None,
    tags: list[str] | None = None,
    runtime: LLMRuntime | None = None,
) -> dict[str, Any]:
    """Ingest a file: copy to ``sources/``, parse, create a Source note."""
    source = Path(src_path)
    if not source.is_file():
        raise FileNotFoundError(source)

    kind = detect_kind(source)
    if kind == "unknown":
        raise ValueError(f"unsupported file type: {source.suffix!r}")

    await _to_thread_complete(check_bundle_paths, root, write=True)
    size = await _to_thread_complete(lambda: source.stat().st_size)
    if size > MAX_INGEST_BYTES:
        raise ValueError(
            f"file {size} bytes exceeds ingest limit {MAX_INGEST_BYTES}; "
            "reingest after splitting (D38)"
        )

    content_sha = await _to_thread_complete(hash_file, source, max_bytes=MAX_INGEST_BYTES)

    lock = BundleLock(root, ACQUIRED_KNOWLEDGE, exclusive=True, timeout=INGEST_LOCK_TIMEOUT_S)
    try:
        await _to_thread_complete(lock.acquire)
        existing = await _to_thread_complete(find_existing_source_by_sha256, root, content_sha)
        if existing is not None:
            existing_id, existing_path, existing_chunks, existing_parsed = existing
            return {
                "source_id": existing_id,
                "file_path": existing_path,
                "content_sha256": content_sha,
                "chunks_total": existing_chunks,
                "parsed_chars": existing_parsed,
                "warning": None,
                "reused_existing": True,
            }

        source_id = await _to_thread_complete(new_id, root)
        destination = await _to_thread_complete(ingested_path, root, source_id, source.suffix)
        try:
            await _to_thread_complete(_copy_source_atomically, source, destination)
        except Exception:
            await _to_thread_complete(destination.unlink, missing_ok=True)
            raise
        copied_sha = await _to_thread_complete(hash_file, destination, max_bytes=MAX_INGEST_BYTES)
        if copied_sha != content_sha:
            await _to_thread_complete(destination.unlink, missing_ok=True)
            raise RuntimeError("source changed while ingest was copying it; retry ingestion")

        log_path = root / "log.md"
        log_prev: str | None | object = _UNKNOWN_LOG_STATE
        note_target: Path | None = None
        committed = False

        try:
            log_prev = await _to_thread_complete(_read_optional_text, log_path)

            parsed_text = ""
            warning: str | None = None
            page_count: int | None = None
            extracted_tags: list[str] = []

            if kind == "document":
                result = await _to_thread_complete(parse_document, destination)
                parsed_text = result.text
                warning = result.warning
                page_count = result.page_count
            elif kind == "image":
                if runtime is None:
                    raise UnsupportedCapabilityError(
                        "image ingest requires a request runtime; no LLM runtime available"
                    )
                caption = await image_caption(root, str(destination), runtime=runtime)
                parsed_text = (
                    f"# {caption['caption']}\n\n"
                    f"**Descrição:** {caption['description']}\n\n"
                    f"**OCR:** {caption['ocr'] or '(nenhum)'}\n\n"
                    f"**Tags:** {' '.join('#' + t for t in caption['tags'])}\n"
                )
                extracted_tags = list(caption["tags"])
                await _to_thread_complete(
                    track,
                    root,
                    "source_ingest_image",
                    asset=str(destination),
                    cache_hit=caption.get("cached", False),
                    provider=caption.get("provider"),
                    model=caption.get("model"),
                )
            else:  # audio
                transcript = await audio_transcribe(
                    root, str(destination),
                )
                parsed_text = transcript["text"]
                await _to_thread_complete(
                    track, root, "source_ingest_audio", asset=str(destination),
                    provider=transcript["provider"], model=transcript["model"],
                )

            chunks = chunk_text(parsed_text)
            title_val = title or source.stem
            merged_tags = sorted(set((tags or []) + extracted_tags))
            note_target = await _to_thread_complete(note_path, root, source_id, title_val)
            written_note = await _to_thread_complete(
                write_source_note,
                root,
                source_id=source_id,
                title=title_val,
                body=f"## Conteúdo extraído\n\n{parsed_text}\n",
                source_kind=kind,
                file_path=str(destination.relative_to(root)),
                content_sha256=content_sha,
                media_type=_media_type(source.suffix),
                size_bytes=await _to_thread_complete(lambda: destination.stat().st_size),
                chunks_total=len(chunks),
                parsed_chars=len(parsed_text),
                page_count=page_count,
                tags=merged_tags or None,
            )
            note_target = written_note
            store = await _to_thread_complete(gitstore, root)
            log_target = await _to_thread_complete(
                store.append_log,
                {
                    "timestamp": now_iso(),
                    "kind": "source",
                    "op": "ingest",
                    "path": str(written_note.relative_to(root)),
                    "by": "process:source_ingest",
                    "note": f"chunks_total={len(chunks)}",
                },
            )
            commit_task = asyncio.create_task(asyncio.to_thread(
                store.commit_paths,
                [written_note, log_target],
                f"ingest(percival): {source_id} — {source.name} [{kind}]",
            ))
            try:
                await asyncio.shield(commit_task)
            except asyncio.CancelledError:
                # Once the worker may have committed, never roll back files
                # without knowing the commit outcome. Finish the atomic
                # boundary, then let cancellation propagate without undoing it.
                await commit_task
                committed = True
                raise
            committed = True
            return {
                "source_id": source_id,
                "file_path": str(destination.relative_to(root)),
                "content_sha256": content_sha,
                "chunks_total": len(chunks),
                "parsed_chars": len(parsed_text),
                "warning": warning,
                "reused_existing": False,
                "source_kind": kind,
            }
        except BaseException:
            if committed:
                raise
            if note_target is not None:
                await _to_thread_complete(note_target.unlink, missing_ok=True)
            await _to_thread_complete(destination.unlink, missing_ok=True)
            if log_prev is not _UNKNOWN_LOG_STATE:
                if log_prev is None:
                    await _to_thread_complete(log_path.unlink, missing_ok=True)
                elif isinstance(log_prev, str):
                    from nanobot.agent.kg.vendor.okf_bundle_core.zettel import write_atomic
                    await _to_thread_complete(write_atomic, log_path, log_prev)
            raise
    finally:
        await _to_thread_complete(lock.release)


def _copy_source_atomically(source: Path, destination: Path) -> None:
    with tempfile.NamedTemporaryFile(
        dir=destination.parent, prefix=f".{destination.name}.", delete=False,
    ) as tmp:
        tmp_path = Path(tmp.name)
    try:
        shutil.copy2(source, tmp_path)
        os.replace(tmp_path, destination)
    except Exception:
        tmp_path.unlink(missing_ok=True)
        raise


def _read_optional_text(path: Path) -> str | None:
    return path.read_text(encoding="utf-8") if path.exists() else None


def source_read(
    root: Path,
    source_id: str,
    *,
    chunk_index: int,
) -> dict[str, Any]:
    """Return chunk ``chunk_index`` of a previously-ingested Source."""
    note = read_note(root, source_id)
    if note["frontmatter"].get("type") != "Source":
        raise ValueError(f"{source_id} is not a Source (type={note['frontmatter'].get('type')!r})")

    body = note["body"]
    prefix = "## Conteúdo extraído\n\n"
    if body.startswith(prefix):
        body = body[len(prefix):]
    if body.endswith("\n"):
        body = body[:-1]
    chunks = chunk_text(body)
    if chunk_index < 0 or chunk_index >= len(chunks):
        raise IndexError(f"chunk_index {chunk_index} out of range (0..{len(chunks) - 1})")
    chunk = chunks[chunk_index]
    return {
        "source_id": source_id,
        "chunk_index": chunk_index,
        "text": chunk.text,
        "locator": chunk.locator,
        "char_count": chunk.char_count,
    }


def _media_type(suffix: str) -> str:
    from nanobot.agent.kg.ak.parsers import mimetype_from_suffix
    return mimetype_from_suffix(suffix)


__all__ = ["source_ingest", "source_read"]
