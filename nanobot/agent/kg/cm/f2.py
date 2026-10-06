"""CM link, policy, graph, stats, storage and archive operations."""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, cast

from nanobot.agent.kg.cm import core
from nanobot.agent.kg.vendor.okf_bundle_core import storage as bundle_storage
from nanobot.agent.kg.vendor.okf_bundle_core.errors import CASMismatchError
from nanobot.agent.kg.vendor.okf_bundle_core.frontmatter import extract_links, split_frontmatter
from nanobot.agent.kg.vendor.okf_bundle_core.gitstore import GitStore
from nanobot.agent.kg.vendor.okf_bundle_core.graph_query import neighbors, shortest_path
from nanobot.agent.kg.vendor.okf_bundle_core.lock import BundleLock, LockTimeout
from nanobot.agent.kg.vendor.okf_bundle_core.paths import (
    COLLECTIVE_MEMORY,
    PathEscapeError,
    ReservedPathError,
    assert_asset_exists,
    resolve_safe_path,
)
from nanobot.agent.kg.vendor.okf_bundle_core.schema import (
    ReviewKind,
    validate_frontmatter,
    validate_id,
)
from nanobot.agent.kg.vendor.okf_bundle_core.storage import (
    COLD_TTL_DAYS_DEFAULT,
    ISOLATION_TTL_DAYS_DEFAULT,
    find_aging_candidates,
    get_storage_summary,
)
from nanobot.agent.kg.vendor.okf_bundle_core.zettel import write_atomic

VALID_RELATIONS = frozenset({"related", "supersedes", "contradicts", "derived_from"})
REVIEW_KINDS = frozenset(ReviewKind.__args__)
CONFIDENCE_ORDER = {"low": 0, "medium": 1, "high": 2}
RESOLUTIONS = frozenset({"acknowledge", "resolve_keep", "resolve_cold", "resolve_forget", "reopen"})
MAX_BATCH_LINKS = 100
_UNKNOWN_LOG_STATE = object()


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _read(root: Path, note_id: str) -> dict[str, Any]:
    return core.notes_read(root, note_id)


def _write(
    root: Path,
    note: dict[str, Any],
    *,
    reason: str,
    body: str | None = None,
    patch: dict[str, Any] | None = None,
    expected_content_hash: str | None = None,
    expected_body_hash: str | None = None,
) -> dict[str, Any]:
    return core.notes_write(
        root,
        note_id=str(note["id"]),
        body=str(note["body"] if body is None else body),
        frontmatter_patch=patch,
        expected_content_hash=(
            expected_content_hash if expected_content_hash is not None
            else (None if expected_body_hash is not None else str(note["content_hash"]))
        ),
        expected_body_hash=expected_body_hash,
        reason=reason,
    )


def memory_link(root: Path, from_id: str, to_id: str, *, relation: str = "related", reason: str = "manual link") -> dict[str, Any]:
    validate_id(from_id)
    validate_id(to_id)
    if relation not in VALID_RELATIONS:
        raise ValueError(f"invalid relation {relation!r}; expected one of {sorted(VALID_RELATIONS)}")
    if from_id == to_id:
        raise ValueError("self-link is not allowed")
    if not reason.strip():
        raise ValueError("reason must not be blank")
    note = _read(root, from_id)
    fm = note["frontmatter"]
    if relation in {"supersedes", "derived_from"}:
        existing = list(fm.get(relation, []))
        if to_id in existing:
            return {**_unchanged_write_result(note), "changed": False}
        existing.append(to_id)
        result = _write(root, note, patch={relation: existing}, reason=f"link {relation} -> {to_id}: {reason}")
    else:
        body = str(note["body"])
        if re.search(rf"\[\[{re.escape(to_id)}(?:\||\])", body):
            return {**_unchanged_write_result(note), "changed": False}
        entry = f"- {relation} :: [[{to_id}]]"
        body = body.rstrip() + ("\n\n## Links\n\n" if "## Links" not in body else "\n") + entry + "\n"
        result = _write(root, note, body=body, expected_body_hash=str(note["body_hash"]), reason=f"link {relation} -> {to_id}: {reason}")
    return {**result, "changed": True}


def _unchanged_write_result(note: dict[str, Any]) -> dict[str, Any]:
    return {key: note[key] for key in ("id", "path", "content_hash", "body_hash", "frontmatter")}


def memory_batch_link(root: Path, edges: list[dict[str, str]], *, reason: str = "batch link") -> dict[str, Any]:
    if not edges or len(edges) > MAX_BATCH_LINKS:
        raise ValueError(f"edges must contain 1..{MAX_BATCH_LINKS} items")
    if not reason.strip():
        raise ValueError("reason must not be blank")
    items: list[dict[str, Any]] = []
    for edge in edges:
        from_id, to_id = edge["from_id"], edge["to_id"]
        relation = edge.get("relation", "related")
        try:
            result = memory_link(root, from_id, to_id, relation=relation, reason=reason)
            items.append({"from_id": from_id, "to_id": to_id, "relation": relation,
                          "status": "applied" if result.get("changed") else "skipped",
                          "content_hash": result.get("content_hash")})
        except LockTimeout:
            raise
        except Exception as exc:
            items.append({"from_id": from_id, "to_id": to_id, "relation": relation,
                          "status": "error", "error": str(exc) or type(exc).__name__})
    return {"applied_count": sum(i["status"] == "applied" for i in items),
            "skipped_count": sum(i["status"] == "skipped" for i in items),
            "error_count": sum(i["status"] == "error" for i in items), "items": items}


def memory_attach(root: Path, note_id: str, asset_path: str, *, reason: str = "manual attach") -> dict[str, Any]:
    note = _read(root, note_id)
    try:
        asset = resolve_safe_path(root, asset_path, COLLECTIVE_MEMORY)
    except (PathEscapeError, ReservedPathError) as exc:
        raise ValueError(f"asset path is not permitted: {asset_path}") from exc
    assert_asset_exists(asset, hint=f"asset_path={asset_path}")
    rel = asset.relative_to(root).as_posix()
    attachments = list(note["frontmatter"].get("attachments", []))
    if rel in attachments:
        return {**_unchanged_write_result(note), "changed": False}
    attachments.append(rel)
    result = _write(root, note, patch={"attachments": attachments}, reason=f"attach {rel}: {reason}")
    return {**result, "changed": True}


def memory_forget(root: Path, note_id: str, reason: str) -> dict[str, Any]:
    core.check_bundle_paths(root, write=True)
    validate_id(note_id)
    if not reason.strip() or "\n" in reason or "\r" in reason:
        raise ValueError("reason must be a nonblank single line")
    note = _read(root, note_id)
    src = root / str(note["path"])
    archive = root / "_archive" / datetime.now(timezone.utc).strftime("%Y%m")
    core.check_no_symlink_components(root, src)
    core.check_no_symlink_components(root, archive)
    if not archive.resolve().is_relative_to(root.resolve()):
        raise PathEscapeError(str(archive))
    archive.mkdir(parents=True, exist_ok=True)
    gitstore = GitStore(root, COLLECTIVE_MEMORY)
    gitstore.ensure_repo()
    log_file = root / "log.md"
    previous_log: str | None | object = _UNKNOWN_LOG_STATE
    with BundleLock(root, COLLECTIVE_MEMORY, exclusive=True):
        dst = archive / src.name
        if dst.exists():
            stamp = datetime.now(timezone.utc).strftime("%H%M%S")
            dst = archive / f"{src.stem}-{stamp}{src.suffix}"
            collision = 1
            while dst.exists():
                dst = archive / f"{src.stem}-{stamp}-{collision}{src.suffix}"
                collision += 1
        os.rename(src, dst)
        try:
            previous_log = log_file.read_text(encoding="utf-8") if log_file.exists() else None
            gitstore.append_log({"kind": note["frontmatter"].get("type", "Note"), "op": "forget",
                                 "path": dst.relative_to(root).as_posix(), "by": "agent:percival", "note": reason})
            gitstore.commit_paths([src, dst], f"mem(percival): forget {note_id} — {reason}")
        except Exception:
            os.rename(dst, src)
            if previous_log is None:
                log_file.unlink(missing_ok=True)
            elif isinstance(previous_log, str):
                write_atomic(log_file, previous_log)
            raise
    return {"archived": dst.relative_to(root).as_posix()}


def _iter_note_data(root: Path) -> list[tuple[Path, dict[str, Any], str]]:
    core.check_bundle_paths(root, write=False)
    notes_dir = root / "notes"
    if not notes_dir.is_dir():
        return []
    output: list[tuple[Path, dict[str, Any], str]] = []
    for path in sorted(notes_dir.glob("*.md")):
        if not path.resolve().is_relative_to(root.resolve()):
            raise PathEscapeError(str(path))
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        raw, body = split_frontmatter(text)
        if not raw or "type" not in raw:
            continue
        output.append((path, raw, body))
    return output


def memory_stats(root: Path, *, include_storage: bool = False) -> dict[str, Any]:
    rows = _iter_note_data(root)
    ids: list[str] = []
    referenced: set[str] = set()
    outgoing: dict[str, bool] = {}
    tags: dict[str, int] = {}
    types: dict[str, int] = {}
    protected = cold = 0
    cold_ids: set[str] = set()
    flagged_by_kind: dict[str, int] = {}
    pending: set[str] = set()
    recent_writes: list[tuple[float, dict[str, str]]] = []
    recent_cutoff = datetime.now(timezone.utc).timestamp() - 7 * 24 * 60 * 60
    recent_writes_7d = 0
    dev_orphans = frozenset(item.strip() for item in os.environ.get(
        "CM_DEV_ORPHAN_IDS", "20260730-120000,20260730-120001,20260730-130000,20260730-130001"
    ).split(",") if item.strip())
    for path, fm, body in rows:
        validated, _ = validate_frontmatter(fm)
        if validated is None:
            continue
        fm = validated.model_dump(mode="json", exclude_none=True)
        match = re.match(r"^(\d{8}-\d{6})", path.stem)
        note_id = match.group(1) if match else f"__draft__:{path.stem}"
        ids.append(note_id)
        kind = str(fm.get("type", "Note"))
        types[kind] = types.get(kind, 0) + 1
        raw_tags = fm.get("tags", [])
        for tag in cast(list[Any], raw_tags) if isinstance(raw_tags, list) else []:
            tags[str(tag)] = tags.get(str(tag), 0) + 1
        links = [link for link in extract_links(body) if not link.is_external]
        referenced.update(link.target for link in links)
        referenced.update(fm.get("supersedes", []))
        referenced.update(fm.get("derived_from", []))
        outgoing[note_id] = bool(links or fm.get("supersedes") or fm.get("derived_from"))
        protected += bool(fm.get("protected", False))
        is_cold = fm.get("lifecycle", "active") == "cold"
        cold += is_cold
        if is_cold:
            cold_ids.add(note_id)
        raw_review = fm.get("review", [])
        review_entries = cast(list[dict[str, Any]], raw_review)
        for entry in review_entries:
            if entry.get("status") == "pending":
                kind_name = str(entry.get("kind", "unknown"))
                flagged_by_kind[kind_name] = flagged_by_kind.get(kind_name, 0) + 1
                pending.add(note_id)
        try:
            mtime = path.stat().st_mtime
        except OSError:
            continue
        if mtime > recent_cutoff:
            recent_writes_7d += 1
        recent_writes.append((mtime, {"id": note_id, "path": path.relative_to(root).as_posix(),
                                      "modified_at": datetime.fromtimestamp(mtime, timezone.utc).isoformat()}))
    orphan_ids = [n for n in ids if not outgoing.get(n) and n not in referenced and n not in cold_ids]
    excluded_permanent = sum(note_id in dev_orphans for note_id in orphan_ids)
    orphans = sorted(n for n in orphan_ids if n not in dev_orphans)
    graph_path = root / "graphify-out" / "graph.json"
    graph_health: dict[str, Any] = {}
    if graph_path.is_file():
        if not graph_path.resolve().is_relative_to(root.resolve()):
            raise PathEscapeError(str(graph_path))
        try:
            graph = cast(dict[str, Any], json.loads(graph_path.read_text(encoding="utf-8")))
            links = cast(list[dict[str, Any]], graph.get("links", []))
            graph_health = {"nodes": len(graph.get("nodes", [])), "edges": len(links),
                            "edge_types": {relation: sum(1 for edge in links if edge.get("relation") == relation)
                                           for relation in sorted(VALID_RELATIONS)},
                            "last_build": datetime.fromtimestamp(graph_path.stat().st_mtime, timezone.utc).isoformat()}
        except (OSError, json.JSONDecodeError):
            graph_health = {"error": "graph.json invalid"}
    result: dict[str, Any] = {
        "notes_total": len(list((root / "notes").glob("*.md"))),
        "orphans": orphans, "excluded_permanent": excluded_permanent,
        "untriaged_inbox": [],
        "recent_writes": [entry for _, entry in sorted(recent_writes, key=lambda item: item[0], reverse=True)[:50]],
        "recent_writes_7d": recent_writes_7d,
        "tags_distribution": tags, "types_distribution": types, "graph_health": graph_health,
        "protected_count": protected, "cold_count": cold, "flagged_count": sum(flagged_by_kind.values()),
        "flagged_by_kind": flagged_by_kind, "pending_review_ids": sorted(pending), "storage_summary": None,
    }
    inbox = root / "assets" / "_inbox"
    if inbox.is_dir():
        if not inbox.resolve().is_relative_to(root.resolve()):
            raise PathEscapeError(str(inbox))
        result["untriaged_inbox"] = sorted(p.name for p in inbox.iterdir() if p.is_file() and not p.name.startswith("."))
    if include_storage:
        result["storage_summary"] = storage_stats(root)
    return result


def asset_get_path(root: Path, asset_ref: str) -> dict[str, str]:
    if "/" in asset_ref or asset_ref.startswith("."):
        try:
            full = resolve_safe_path(root, asset_ref, COLLECTIVE_MEMORY)
        except (PathEscapeError, ReservedPathError) as exc:
            raise ValueError(f"asset path is not permitted: {asset_ref}") from exc
        assert_asset_exists(full, hint=f"asset_ref={asset_ref}")
        return {"abs_path": str(full), "rel_path": full.relative_to(root).as_posix(), "source": "path"}
    note = _read(root, asset_ref)
    attachments = note["frontmatter"].get("attachments", [])
    if not attachments:
        raise ValueError(f"note {asset_ref} has no attachments")
    try:
        full = resolve_safe_path(root, str(attachments[0]), COLLECTIVE_MEMORY)
    except (PathEscapeError, ReservedPathError) as exc:
        raise ValueError("attachment path is not permitted") from exc
    assert_asset_exists(full, hint=f"attachment={asset_ref}")
    return {"abs_path": str(full), "rel_path": full.relative_to(root).as_posix(), "source": "note_attachment"}


def graph_neighbors(root: Path, note_id: str, relation_filter: list[str] | None = None) -> dict[str, Any]:
    validate_id(note_id)
    _check_graph_path(root)
    result = neighbors(root, note_id, relation_filter=relation_filter)
    return {"node_id": result.node_id, "label": result.label,
            "neighbors": [{"id": n.id, "label": n.label, "direction": n.direction, "relation": n.relation}
                          for n in result.neighbors]}


def graph_shortest_path(root: Path, from_id: str, to_id: str, max_hops: int | None = None) -> dict[str, Any]:
    validate_id(from_id)
    validate_id(to_id)
    if max_hops is not None and max_hops < 0:
        raise ValueError("max_hops must be >= 0")
    _check_graph_path(root)
    result = shortest_path(root, from_id, to_id, max_hops=max_hops)
    return {"found": result.found, "source_id": result.source_id, "target_id": result.target_id,
            "hops": result.hops, "path": result.path, "labels": result.labels}


def memory_set_protected(root: Path, note_id: str, protected: bool, *, reason: str = "manual toggle",
                          expected_content_hash: str | None = None) -> dict[str, Any]:
    note = _read(root, note_id)
    current = bool(note["frontmatter"].get("protected", False))
    if current == protected:
        if expected_content_hash is not None and expected_content_hash != note["content_hash"]:
            raise CASMismatchError(f"content_hash mismatch for {note_id}")
        return {"id": note_id, "protected": current, "changed": False,
                "cas_matched": expected_content_hash is not None}
    expected_hash = expected_content_hash if expected_content_hash is not None else str(note["content_hash"])
    result = _write(root, note, patch={"protected": protected}, reason=f"{'protect' if protected else 'unprotect'}: {reason}",
                    expected_content_hash=expected_hash)
    return {"id": note_id, "protected": protected, "changed": True, "cas_matched": True,
            "content_hash": result["content_hash"], "body_hash": result["body_hash"]}


def memory_set_lifecycle(root: Path, note_id: str, lifecycle: str, *, reason: str = "lifecycle transition",
                          expected_content_hash: str | None = None, force: bool = False) -> dict[str, Any]:
    if lifecycle not in {"active", "cold"}:
        raise ValueError("lifecycle must be active or cold")
    note = _read(root, note_id)
    fm = note["frontmatter"]
    current = fm.get("lifecycle", "active")
    if current == lifecycle:
        if expected_content_hash is not None and expected_content_hash != note["content_hash"]:
            raise CASMismatchError(f"content_hash mismatch for {note_id}")
        return {"id": note_id, "lifecycle": current, "cooled_at": fm.get("cooled_at"), "changed": False,
                "cas_matched": expected_content_hash is not None}
    if lifecycle == "cold" and fm.get("protected") and not force:
        raise ValueError(f"{note_id} is protected; unprotect or pass force=true")
    cooled_at = _utc_now_iso() if lifecycle == "cold" else None
    expected_hash = expected_content_hash if expected_content_hash is not None else str(note["content_hash"])
    result = _write(root, note, patch={"lifecycle": lifecycle, "cooled_at": cooled_at},
                    reason=f"lifecycle {current}->{lifecycle}: {reason}",
                    expected_content_hash=expected_hash)
    return {"id": note_id, "lifecycle": lifecycle, "cooled_at": cooled_at, "changed": True,
            "cas_matched": True, "content_hash": result["content_hash"], "body_hash": result["body_hash"]}


def memory_flag_for_review(root: Path, note_id: str, kind: str, confidence: str, reason: str, *,
                           related_actions: list[str] | None = None,
                           flagged_by: str = "agent:memory-maintenance") -> dict[str, Any]:
    if kind not in REVIEW_KINDS:
        raise ValueError(f"invalid review kind: {kind}")
    if confidence not in CONFIDENCE_ORDER or not reason.strip():
        raise ValueError("confidence must be low/medium/high and reason must not be blank")
    note = _read(root, note_id)
    entries = [dict(e) for e in note["frontmatter"].get("review", [])]
    old = next((e for e in entries if e.get("kind") == kind), None)
    if old and old.get("status") != "pending":
        return {"id": note_id, "applied": False, "kind": kind, "existing_status": old.get("status"),
                "reason": "review already resolved; reopen it first"}
    if old:
        old_confidence = str(old.get("confidence", "low"))
        if CONFIDENCE_ORDER[confidence] <= CONFIDENCE_ORDER.get(old_confidence, 0):
            return {"id": note_id, "applied": False, "kind": kind, "existing_confidence": old_confidence,
                    "reason": "confidence did not increase"}
        old.update(confidence=confidence, reason=reason, flagged_at=_utc_now_iso(),
                   flagged_by=flagged_by)
        if related_actions is not None:
            old["related_actions"] = related_actions
    else:
        entries.append({"status": "pending", "kind": kind, "confidence": confidence, "reason": reason,
                        "flagged_at": _utc_now_iso(), "flagged_by": flagged_by,
                        "related_actions": related_actions or []})
    result = _write(root, note, patch={"review": entries}, reason=f"flag {kind} ({confidence})")
    return {"id": note_id, "applied": True, "kind": kind, "confidence": confidence,
            "review": result["frontmatter"].get("review", []), "content_hash": result["content_hash"]}


def memory_resolve_review(root: Path, note_id: str, kind: str, resolution: str, *, reason: str = "manual resolve") -> dict[str, Any]:
    if resolution not in RESOLUTIONS or kind not in REVIEW_KINDS:
        raise ValueError("invalid review kind or resolution")
    note = _read(root, note_id)
    entries = [dict(e) for e in note["frontmatter"].get("review", [])]
    target = next((e for e in entries if e.get("kind") == kind), None)
    if target is None:
        raise ValueError(f"note {note_id} has no review kind={kind}")
    if resolution == "reopen":
        target.update(status="pending", reopened_at=_utc_now_iso())
    elif resolution == "acknowledge":
        target["status"] = "acknowledged"
    else:
        target["status"] = "resolved"
    result = _write(root, note, patch={"review": entries}, reason=f"resolve review {kind} -> {resolution}: {reason}")
    side_effect: dict[str, Any] | None = None
    if resolution == "resolve_cold":
        side_effect = memory_set_lifecycle(root, note_id, "cold", reason=f"resolve review {kind}")
    elif resolution == "resolve_forget":
        side_effect = memory_forget(root, note_id, f"resolve review {kind}: {reason}")
    return {"id": note_id, "kind": kind, "resolution": resolution, "status": target["status"],
            "side_effect": side_effect, "content_hash": result["content_hash"] if side_effect is None else None}


def storage_stats(root: Path) -> dict[str, Any]:
    core.check_bundle_paths(root, write=False)
    _check_contained(root, root / ".git")
    _check_contained(root, root / "_archive")
    _check_contained(root, root / "graphify-out")
    _check_contained(root, root / "assets")
    _check_contained(root, root / "diary")
    summary = cast(Any, get_storage_summary(
        root,
        COLLECTIVE_MEMORY,
        cold_ttl_days=_positive_env_int("CM_COLD_TTL_DAYS", COLD_TTL_DAYS_DEFAULT),
        warn_bytes=_positive_env_int("CM_STORAGE_WARN_BYTES", 500 * 1024 * 1024),
        crit_bytes=_positive_env_int("CM_STORAGE_CRIT_BYTES", 750 * 1024 * 1024),
    ))
    return cast(dict[str, Any], summary.to_dict())


def memory_repo_maintenance(root: Path, *, dry_run: bool = True, reason: str = "scheduled maintenance") -> dict[str, Any]:
    core.check_bundle_paths(root, write=not dry_run)
    _check_contained(root, root / ".git")
    maintenance_operation: Any = cast(Any, bundle_storage).repo_maintenance
    if dry_run:
        return cast(dict[str, Any], maintenance_operation(root, COLLECTIVE_MEMORY, dry_run=True))
    GitStore(root, COLLECTIVE_MEMORY).ensure_repo()
    with BundleLock(root, COLLECTIVE_MEMORY, exclusive=True):
        result = cast(dict[str, Any], maintenance_operation(root, COLLECTIVE_MEMORY, dry_run=False))
    result["reason"] = reason
    return result


def aging_candidates(root: Path, *, isolation_ttl_days: int | None = None,
                     cold_ttl_days: int | None = None) -> dict[str, Any]:
    rows = _iter_note_data(root)
    known_ids = {str(fm.get("id") or path.stem) for path, fm, _ in rows}
    connected: set[str] = set()
    for path, fm, body in rows:
        note_id = str(fm.get("id") or path.stem)
        links = [link for link in extract_links(body) if not link.is_external]
        targets = set(fm.get("supersedes", [])) | set(fm.get("derived_from", [])) | {link.target for link in links}
        if targets:
            connected.add(note_id)
            connected.update(target for target in targets if target in known_ids)
    candidates = find_aging_candidates(root, COLLECTIVE_MEMORY, connected_ids=connected,
                                       isolation_ttl_days=(isolation_ttl_days or _positive_env_int(
                                           "CM_ISOLATION_TTL_DAYS", ISOLATION_TTL_DAYS_DEFAULT)),
                                       cold_ttl_days=(cold_ttl_days or _positive_env_int(
                                           "CM_COLD_TTL_DAYS", COLD_TTL_DAYS_DEFAULT)))
    return {"to_cold": [cast(dict[str, Any], cast(Any, c).to_dict()) for c in candidates if c.target == "cold"],
            "to_archive": [cast(dict[str, Any], cast(Any, c).to_dict()) for c in candidates if c.target == "archive"],
            "total": len(candidates), "protected_skipped": sum(c.protected for c in candidates)}


def _positive_env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    try:
        value = int(raw) if raw else default
    except ValueError:
        return default
    return value if value > 0 else default


def _check_contained(root: Path, path: Path) -> None:
    if path.exists() or path.is_symlink():
        if not path.resolve().is_relative_to(root.resolve()):
            raise PathEscapeError(str(path))


def _check_graph_path(root: Path) -> None:
    core.check_bundle_paths(root, write=False)
    _check_contained(root, root / "graphify-out")
    _check_contained(root, root / "graphify-out" / "graph.json")
