"""Authenticated HTTP seam for the native KG bridge.

Until native bundle services are installed, health is deliberately unavailable;
a transport probe must not advertise a working memory backend.
"""

from __future__ import annotations

from websockets.http11 import Response

from nanobot.webui.http_utils import http_json_response


def kg_http_probe(path: str, *, authenticated: bool) -> Response | None:
    if path != "/kg-interface/api" and not path.startswith("/kg-interface/api/"):
        return None
    if not authenticated:
        return http_json_response({"error": "Unauthorized"}, status=401)
    if path not in {
        "/kg-interface/api/memory/healthz",
        "/kg-interface/api/acquire/healthz",
    }:
        return http_json_response({"error": "KG API route not found"}, status=404)
    return http_json_response({"ok": False, "error": "native KG service unavailable"}, status=503)
