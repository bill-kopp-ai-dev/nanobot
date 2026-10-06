"""``markitdown`` CLI subprocess wrapper for AK document ingestion.

``markitdown`` is invoked as a CLI on purpose — installing
``markitdown[all]`` as a Python package would pull ~80MB of optional
parsers.  The wrapper raises clear errors when the CLI is missing, the
return code is non-zero, or the timeout elapses.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

MARKITDOWN_TIMEOUT_S = 60.0
SCANNED_PDF_CHARS_PER_PAGE = 100

SUPPORTED_DOCS = frozenset(
    {
        ".pdf",
        ".docx",
        ".pptx",
        ".html",
        ".htm",
        ".md",
        ".txt",
        ".csv",
        ".xlsx",
        ".epub",
    }
)
SUPPORTED_IMAGES = frozenset({".png", ".jpg", ".jpeg", ".webp", ".gif"})
SUPPORTED_AUDIO = frozenset({".wav", ".mp3", ".m4a", ".ogg", ".flac"})


@dataclass
class ParseResult:
    text: str
    is_scanned_pdf: bool
    page_count: int | None
    warning: str | None
    parser: str = "markitdown"


def resolve_markitdown_cli() -> str | None:
    """Return the resolved path of the ``markitdown`` executable."""
    found = shutil.which("markitdown")
    if found:
        return found
    return shutil.which("markitdown", path=str(Path(sys.executable).parent))


def detect_kind(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in SUPPORTED_DOCS:
        return "document"
    if suffix in SUPPORTED_IMAGES:
        return "image"
    if suffix in SUPPORTED_AUDIO:
        return "audio"
    return "unknown"


def parse_document(path: Path, *, timeout: float = MARKITDOWN_TIMEOUT_S) -> ParseResult:
    """Run ``markitdown PATH`` via subprocess and return the extracted text."""
    suffix = path.suffix.lower()
    if suffix not in SUPPORTED_DOCS:
        raise ValueError(f"unsupported document type: {suffix!r}")

    executable = resolve_markitdown_cli()
    if executable is None:
        raise FileNotFoundError(
            "markitdown CLI not found; install with: uv pip install 'markitdown[all]>=0.1.5'"
        )
    if not path.exists():
        raise FileNotFoundError(path)

    proc = subprocess.run(
        [executable, str(path)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )
    if proc.returncode != 0:
        stderr = (proc.stderr or "")[:300]
        raise RuntimeError(f"markitdown failed (rc={proc.returncode}): {stderr!r}")

    text = proc.stdout or ""
    is_scanned, page_count, warning = _heuristic_pdf(path, text)
    return ParseResult(
        text=text,
        is_scanned_pdf=is_scanned,
        page_count=page_count,
        warning=warning,
    )


def _heuristic_pdf(path: Path, text: str) -> tuple[bool, int | None, str | None]:
    if path.suffix.lower() != ".pdf":
        return False, None, None
    if not text.strip():
        return (
            True,
            None,
            "PDF provavelmente escaneado (sem texto extraído). "
            "Use OCR externo (tesseract) ou agent vision.",
        )
    form_feeds = text.count("\f")
    trailer_pages = _pdf_page_count_from_trailer(path)
    if trailer_pages is not None:
        pages = trailer_pages
    else:
        pages = max(1, form_feeds) if form_feeds > 0 else 1
    pages = max(1, pages)
    chars_per = len(text) / pages
    is_scanned = chars_per < SCANNED_PDF_CHARS_PER_PAGE
    warning = None
    if is_scanned:
        warning = (
            f"PDF provavelmente escaneado (~{chars_per:.0f} chars por página). "
            "Use OCR externo (tesseract) ou agent vision."
        )
    return is_scanned, pages, warning


def _pdf_page_count_from_trailer(path: Path) -> int | None:
    try:
        with path.open("rb") as handle:
            handle.seek(-4096, 2) if path.stat().st_size > 4096 else handle.seek(0)
            tail = handle.read()
    except OSError:
        return None
    candidates = re.findall(
        rb"/Type\s*/Pages[^>]{0,400}?/Count\s+(\d+)",
        tail,
        flags=re.DOTALL,
    )
    if not candidates:
        return None
    return max(int(candidate) for candidate in candidates)


_MIMETYPE_BY_SUFFIX: dict[str, str] = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".html": "text/html",
    ".htm": "text/html",
    ".md": "text/markdown",
    ".txt": "text/plain",
    ".csv": "text/csv",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".epub": "application/epub+zip",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".gif": "image/gif",
    ".wav": "audio/wav",
    ".mp3": "audio/mpeg",
    ".m4a": "audio/mp4",
    ".ogg": "audio/ogg",
    ".flac": "audio/flac",
}


def mimetype_from_suffix(suffix: str) -> str:
    return _MIMETYPE_BY_SUFFIX.get(suffix.lower(), "application/octet-stream")


__all__ = [
    "MARKITDOWN_TIMEOUT_S",
    "ParseResult",
    "SUPPORTED_AUDIO",
    "SUPPORTED_DOCS",
    "SUPPORTED_IMAGES",
    "detect_kind",
    "mimetype_from_suffix",
    "parse_document",
    "resolve_markitdown_cli",
]
