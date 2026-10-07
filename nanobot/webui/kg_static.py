"""Serve the bundled KG browser shell on the WebUI gateway listener."""

from __future__ import annotations

import asyncio
import mimetypes
import re
from pathlib import Path
from urllib.parse import unquote

from websockets.http11 import Response

from nanobot.webui.http_utils import http_error, http_response

_SPA_ROUTES = {"notes", "extracted", "extracted-notes", "sources", "graph", "search", "stats"}


def kg_static_root() -> Path:
    return Path(__file__).resolve().parents[1] / "web" / "kg-interface"


async def serve_kg_static(path: str, *, root: Path, accepts_html: bool) -> Response | None:
    """Never use a SPA fallback for API requests or missing assets."""
    if path == "/kg-interface/api" or path.startswith("/kg-interface/api/"):
        return http_error(404, "KG API route not found")
    if path != "/kg-interface" and not path.startswith("/kg-interface/"):
        return None
    raw_relative = path.removeprefix("/kg-interface").lstrip("/")
    relative = unquote(raw_relative)
    if not relative:
        relative = "index.html"
    # Defense in depth against request-smuggling classes: a reverse proxy that
    # treats ``%2F`` literally while this server treats it as ``/`` would let a
    # crafted URL reach a different asset than the proxy thinks. Reject any
    # decoded form that introduced new ``/`` separators compared to the
    # raw URL.
    if relative.count("/") != raw_relative.count("/"):
        return http_error(403, "Forbidden")
    if "\x00" in relative or "\\" in relative or any(
        part in {".", ".."} or part.startswith(".") for part in Path(relative).parts
    ):
        return http_error(403, "Forbidden")
    root_resolved = root.resolve()
    candidate = (root_resolved / relative).resolve()
    if not candidate.is_relative_to(root_resolved):
        return http_error(403, "Forbidden")
    if not candidate.is_file():
        if accepts_html and relative.split("/", 1)[0] in _SPA_ROUTES and not Path(relative).suffix:
            candidate = root_resolved / "index.html"
        if not candidate.is_file():
            return http_error(404, "KG asset not found")

    mime, _ = mimetypes.guess_type(candidate.name)
    mime = mime or "application/octet-stream"
    if mime.startswith("text/") or mime in {"application/javascript", "application/json"}:
        mime += "; charset=utf-8"
    try:
        body = await asyncio.to_thread(candidate.read_bytes)
    except OSError:
        return http_error(500, "KG asset unavailable")
    cache = (
        "public, max-age=31536000, immutable"
        if re.search(r"-[A-Za-z0-9_-]{8}\.[^.]+$", candidate.name)
        else "no-cache"
    )
    return http_response(body, content_type=mime, extra_headers=[("Cache-Control", cache)])
