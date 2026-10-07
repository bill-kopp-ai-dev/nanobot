"""Authenticated KG reads and allowlisted WebUI mutations on the gateway listener.

Only the gateway chooses a workspace and bundle. No caller-supplied root or
arbitrary tool name is accepted, and HTTP cannot carry mutation bodies here.
"""

from __future__ import annotations

import asyncio
import json
import re
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal
from urllib.parse import parse_qs, unquote, urlsplit

from loguru import logger
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from websockets.http11 import Response

from nanobot.agent.kg.ak import core as ak_core
from nanobot.agent.kg.ak import ingest as ak_ingest
from nanobot.agent.kg.ak import read as ak_read
from nanobot.agent.kg.cm import core as cm_core
from nanobot.agent.kg.cm import f2 as cm_f2
from nanobot.agent.kg.graph_data import GraphTooLargeError, graph_artifact
from nanobot.agent.kg.roots import BundleKind, bundle_root
from nanobot.agent.kg.vendor.okf_bundle_core.errors import CASMismatchError, ZettelError
from nanobot.agent.kg.vendor.okf_bundle_core.lock import LockTimeout
from nanobot.agent.kg.vendor.okf_bundle_core.paths import PathEscapeError
from nanobot.security.workspace_policy import WorkspaceBoundaryError, resolve_allowed_path
from nanobot.webui.http_utils import http_json_response

if TYPE_CHECKING:
    from nanobot.webui.settings_services import WebUISettingsServices
    from nanobot.webui.workspaces import WebUIWorkspaceController

PREFIX = "/kg-interface/api/"
_ID = re.compile(r"\d{8}-\d{6}\Z")
_MAX_PAYLOAD_BYTES = 2 * 1024 * 1024 + 4096


class _Input(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class BodyEdit(_Input):
    body: str = Field(min_length=1, max_length=2 * 1024 * 1024)
    base_body_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    reason: str = Field(default="edit body", min_length=1, max_length=500)


class Protected(_Input):
    protected: bool
    reason: str = Field(default="manual toggle", min_length=1, max_length=500)
    expected_content_hash: str | None = None


class Lifecycle(_Input):
    lifecycle: Literal["active", "cold"]
    reason: str = Field(default="lifecycle transition", min_length=1, max_length=500)
    expected_content_hash: str | None = None
    force: bool = False


class Flag(_Input):
    kind: str = Field(max_length=100)
    confidence: Literal["low", "medium", "high"]
    reason: str = Field(min_length=1, max_length=500)
    related_actions: list[str] | None = None
    flagged_by: str = Field(default="human:ui", max_length=100)


class Resolve(_Input):
    kind: str = Field(max_length=100)
    resolution: Literal["acknowledge", "resolve_keep", "resolve_cold", "resolve_forget", "reopen"]
    reason: str = Field(default="manual resolve", min_length=1, max_length=500)


class Forget(_Input):
    reason: str = Field(min_length=1, max_length=500)


class Maintenance(_Input):
    dry_run: bool = True
    reason: str = Field(default="manual maintenance", min_length=1, max_length=500)


def _error(status: int, code: str) -> Response:
    return http_json_response({"error": code}, status=status)


_ZETTEL_ERROR_MAP: dict[str, tuple[int, str]] = {
    "graph_query_missing": (404, "graph_query_missing"),
    "graph_query_node_not_found": (404, "graph_query_node_not_found"),
}


def _failure(exc: Exception) -> Response:
    if isinstance(exc, GraphTooLargeError):
        return _error(413, "graph_too_large")
    if isinstance(exc, CASMismatchError):
        return _error(409, "cas_mismatch")
    if isinstance(exc, (WorkspaceBoundaryError, PathEscapeError)):
        return _error(403, "workspace_forbidden")
    if isinstance(exc, (FileNotFoundError, IndexError)):
        return _error(404, "not_found")
    if isinstance(exc, LockTimeout):
        return _error(503, "bundle_busy")
    if isinstance(exc, ZettelError):
        if exc.code and exc.code in _ZETTEL_ERROR_MAP:
            status, code = _ZETTEL_ERROR_MAP[exc.code]
            return _error(status, code)
        if exc.code:
            logger.warning("Unknown ZettelError code: %r", exc.code)
        return _error(400, "invalid_note")
    if isinstance(exc, (ValueError, ValidationError)):
        return _error(400, "invalid_request")
    logger.exception("KG gateway operation failed")
    return _error(503, "kg_unavailable")


def _id(raw: str) -> str:
    value = unquote(raw)
    if _ID.fullmatch(value) is None:
        raise ValueError("invalid note id")
    return value


def _limit(query: dict[str, list[str]], key: str = "limit", default: int = 50, maximum: int = 200) -> int:
    values = query.get(key, [])
    if len(values) > 1:
        raise ValueError("duplicate limit")
    number = int(values[0]) if values else default
    if not 1 <= number <= maximum:
        raise ValueError("invalid limit")
    return number


def _one(query: dict[str, list[str]], key: str) -> str | None:
    values = query.get(key, [])
    if len(values) > 1:
        raise ValueError("duplicate parameter")
    return values[0] if values else None


class KgGatewayBridge:
    def __init__(self, settings: WebUISettingsServices, workspaces: WebUIWorkspaceController):
        self.settings = settings
        self.workspaces = workspaces

    def _root(self, kind: BundleKind, *, write: bool = False) -> Path:
        config = self.settings.config.load().kg
        if config.mode == "mcp":
            raise RuntimeError("native KG disabled")
        # The SPA has no project selector: it acts on the gateway's WebUI
        # default scope, never a path or session key from the browser.
        scope = self.workspaces.default_scope()
        root = bundle_root(kind, config, scope.project_path, use_request_context=False)
        if scope.restrict_to_workspace:
            root = resolve_allowed_path(root, allowed_root=scope.project_path)
        if not root.is_dir() or not (root / "notes").is_dir():
            raise FileNotFoundError("KG bundle not initialized")
        return root

    async def read(self, path: str, *, authenticated: bool) -> Response:
        if not authenticated:
            return _error(401, "Unauthorized")
        try:
            relative = urlsplit(path).path.removeprefix(PREFIX)
            adapter, _, route = relative.partition("/")
            if adapter not in {"memory", "acquire"}:
                return _error(404, "kg_route_not_found")
            kind: BundleKind = "cm" if adapter == "memory" else "ak"
            query = parse_qs(urlsplit(path).query, keep_blank_values=True)
            root = await asyncio.to_thread(self._root, kind)
            if route == "healthz":
                return http_json_response({"ok": True, "server": "percival-native-" + adapter})
            result = await asyncio.to_thread(self._read, kind, root, route, query)
            if result is None:
                return _error(404, "kg_route_not_found")
            return http_json_response(result, extra_headers=[("Cache-Control", "no-store")])
        except FileNotFoundError:
            if path.endswith("/healthz"):
                return http_json_response({"ok": False, "error": "kg_unavailable"}, status=503)
            return _error(404, "bundle_or_note_not_found")
        except Exception as exc:
            return _failure(exc)

    @staticmethod
    def _read(kind: BundleKind, root: Path, route: str,
              query: dict[str, list[str]]) -> dict[str, Any] | None:
        if route == "notes":
            q = _one(query, "q")
            limit = _limit(query)
            if kind == "cm":
                rows = cm_core.notes_search(root, q, limit=limit) if q else cm_core.notes_list(root, limit=limit)
            else:
                rows = ak_read.source_search(root, q, limit=limit) if q else ak_read.source_list(root, kind="ExtractedNote", limit=limit)
            return {"results": rows, "count": len(rows)}
        note_match = re.fullmatch(r"notes/([^/]+)(?:/(history))?", route)
        if note_match:
            note_id = _id(note_match.group(1))
            if note_match.group(2):
                return cm_core.note_history(root, note_id, limit=_limit(query, default=20, maximum=1000)) if kind == "cm" else None
            return cm_core.notes_read(root, note_id) if kind == "cm" else ak_core.read_note(root, note_id)
        if route == "search":
            q = _one(query, "q")
            if not q:
                raise ValueError("missing search query")
            limit = _limit(query)
            rows = (cm_core.notes_search(root, q, limit=limit, kind=_one(query, "kind"))
                    if kind == "cm" else ak_read.source_search(root, q, kind=_one(query, "kind"), limit=limit))
            return {"results": rows, "count": len(rows)}
        if route == "stats":
            return cm_f2.memory_stats(root) if kind == "cm" else ak_read.source_stats(root)
        if route == "storage/stats" and kind == "cm":
            return cm_f2.storage_stats(root)
        if route == "graph":
            return graph_artifact(root)
        if route == "graph/data":
            return graph_artifact(root, data=True)
        if kind == "ak" and route == "sources":
            rows = ak_read.source_list(root, kind="Source", limit=_limit(query))
            return {"results": rows, "count": len(rows)}
        source_match = re.fullmatch(r"sources/([^/]+)(?:/chunks/(\d+))?", route)
        if kind == "ak" and source_match:
            source_id = _id(source_match.group(1))
            if source_match.group(2) is not None:
                return ak_ingest.source_read(root, source_id, chunk_index=int(source_match.group(2)))
            chunk = ak_ingest.source_read(root, source_id, chunk_index=0)
            return {"id": source_id, "frontmatter": ak_core.read_note(root, source_id)["frontmatter"],
                    "first_chunk": {key: value for key, value in chunk.items() if key != "source_id"}}
        return None

    async def mutate(self, action: str, payload: dict[str, Any], *, authenticated: bool = True) -> Response:
        if not authenticated:
            return _error(401, "Unauthorized")
        payload_size = len(json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
        if payload_size > _MAX_PAYLOAD_BYTES:
            return _error(413, "payload_too_large")
        operation = ""
        kind: BundleKind | None = None
        root: Path | None = None
        try:
            adapter, _, operation = action.removeprefix("kg.").partition(".")
            if not action.startswith("kg.") or adapter not in {"memory", "acquire"}:
                return _error(404, "kg_action_not_found")
            requested_kind: BundleKind = "cm" if adapter == "memory" else "ak"
            kind = requested_kind
            root = await asyncio.to_thread(self._root, requested_kind, write=True)
            result = await asyncio.to_thread(self._mutate, requested_kind, root, operation, payload)
            if result is None:
                return _error(404, "kg_action_not_found")
            return http_json_response(result, extra_headers=[("Cache-Control", "no-store")])
        except Exception as exc:
            if isinstance(exc, CASMismatchError) and operation == "notes.body" \
                    and kind is not None and root is not None:
                try:
                    note_id = _id(str(payload.get("note_id", "")))
                    current = await asyncio.to_thread(
                        cm_core.notes_read if kind == "cm" else ak_core.read_note,
                        root,
                        note_id,
                    )
                    conflict = {
                        "status": "conflict",
                        "base_body_hash": str(payload.get("base_body_hash", "")),
                        "current_body_hash": current["body_hash"],
                        "server_body": current["body"],
                    }
                    return http_json_response(conflict, status=409)
                except Exception as conflict_error:
                    return _failure(conflict_error)
            return _failure(exc)

    @staticmethod
    def _mutate(kind: BundleKind, root: Path, operation: str,
                payload: dict[str, Any]) -> dict[str, Any] | None:
        if operation == "notes.body":
            note_id = _id(str(payload.get("note_id", "")))
            req = BodyEdit.model_validate({k: v for k, v in payload.items() if k != "note_id"})
            if kind == "cm":
                # Body edit updates an existing note only.
                cm_core.notes_read(root, note_id)
                return cm_core.notes_write(root, note_id=note_id, body=req.body,
                                           expected_body_hash=req.base_body_hash, reason=req.reason)
            return ak_core.write_note_body(root, note_id, req.body, req.base_body_hash, req.reason)
        if kind != "cm":
            return None
        if operation == "notes.forget":
            note_id = _id(str(payload.get("note_id", "")))
            req = Forget.model_validate({k: v for k, v in payload.items() if k != "note_id"})
            return cm_f2.memory_forget(root, note_id, req.reason)
        if operation == "storage.maintenance":
            req = Maintenance.model_validate(payload)
            return cm_f2.memory_repo_maintenance(root, dry_run=req.dry_run, reason=req.reason)
        if operation in {"notes.protected", "notes.lifecycle", "notes.flag", "notes.resolve"}:
            note_id = _id(str(payload.get("note_id", "")))
            data = {k: v for k, v in payload.items() if k != "note_id"}
            if operation == "notes.protected":
                value = Protected.model_validate(data)
                return cm_f2.memory_set_protected(root, note_id, value.protected, reason=value.reason,
                                                   expected_content_hash=value.expected_content_hash)
            if operation == "notes.lifecycle":
                value = Lifecycle.model_validate(data)
                return cm_f2.memory_set_lifecycle(root, note_id, value.lifecycle, reason=value.reason,
                                                   expected_content_hash=value.expected_content_hash, force=value.force)
            if operation == "notes.flag":
                value = Flag.model_validate(data)
                return cm_f2.memory_flag_for_review(root, note_id, value.kind, value.confidence,
                                                     value.reason, related_actions=value.related_actions,
                                                     flagged_by=value.flagged_by)
            value = Resolve.model_validate(data)
            return cm_f2.memory_resolve_review(root, note_id, value.kind, value.resolution, reason=value.reason)
        return None
