"""Deterministic text chunking for AK sources.

Same shape as ``percival-acquire-knowledge/chunking.py`` so that
``source_read(chunk_index=k)`` returns the same content the original
``source_ingest`` produced (D63).  Locators are derived from form-feed
page boundaries left by markitdown when extracting PDFs.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+(?=[A-ZÁÉÍÓÚÂÊÔÃÕÇ])")
_TRIM_CHARS = " \t\n\r\x0b"
DEFAULT_TARGET_CHARS = 1500
DEFAULT_MAX_CHARS = 2500
DEFAULT_OVERLAP = 100


@dataclass(frozen=True)
class Chunk:
    index: int
    text: str
    locator: str
    char_count: int


def chunk_text(
    text: str,
    *,
    strategy: str = "paragraph",
    target_chars: int = DEFAULT_TARGET_CHARS,
    max_chars: int = DEFAULT_MAX_CHARS,
    overlap: int = DEFAULT_OVERLAP,
) -> list[Chunk]:
    """Split ``text`` into chunks.  Empty/whitespace input returns ``[]``."""
    if not text or not text.strip():
        return []

    if strategy == "paragraph":
        units = _split_paragraphs(text)
    elif strategy == "sentence":
        units = _SENTENCE_RE.split(text)
    elif strategy == "fixed":
        return _chunk_fixed(text, target_chars)
    else:
        raise ValueError(f"unknown strategy: {strategy!r}")

    return _chunk_with_overlap(units, max_chars=max_chars, overlap=overlap)


def _split_paragraphs(text: str) -> list[str]:
    return [para for para in re.split(r"\n\s*\n", text) if para.strip()]


def _chunk_with_overlap(units: list[str], *, max_chars: int, overlap: int) -> list[Chunk]:
    chunks: list[Chunk] = []
    buf = ""
    for unit in units:
        unit = unit.strip(_TRIM_CHARS)
        if not unit:
            continue
        candidate = (buf + "\n\n" + unit).strip(_TRIM_CHARS) if buf else unit
        if len(candidate) > max_chars and buf:
            chunks.append(_make_chunk(chunks, buf))
            if overlap > 0:
                buf = (buf[-overlap:] + "\n\n" + unit).strip(_TRIM_CHARS)
            else:
                buf = unit
        else:
            buf = candidate
    if buf.strip(_TRIM_CHARS):
        chunks.append(_make_chunk(chunks, buf))
    return chunks


def _chunk_fixed(text: str, target_chars: int) -> list[Chunk]:
    chunks: list[Chunk] = []
    for offset in range(0, len(text), target_chars):
        chunks.append(_make_chunk(chunks, text[offset : offset + target_chars]))
    return chunks


def _make_chunk(chunks_so_far: list[Chunk], text: str) -> Chunk:
    prior_form_feeds = sum(chunk.text.count("\f") for chunk in chunks_so_far)
    return Chunk(
        index=len(chunks_so_far),
        text=text,
        locator=_build_locator(text, prior_form_feeds),
        char_count=len(text),
    )


def _build_locator(text: str, prior_form_feeds: int) -> str:
    char_count = len(text)
    form_feeds = text.count("\f")
    if form_feeds == 0 and prior_form_feeds == 0:
        return f"{char_count} chars"
    start_page = prior_form_feeds + 1
    end_page = start_page + form_feeds
    if end_page == start_page:
        return f"p. {start_page}, {char_count} chars"
    return f"p. {start_page}-{end_page}, {char_count} chars"


__all__ = ["DEFAULT_MAX_CHARS", "DEFAULT_OVERLAP", "DEFAULT_TARGET_CHARS", "Chunk", "chunk_text"]
