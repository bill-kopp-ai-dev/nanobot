"""Transactional AK atomization and per-edge links."""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import yaml

from nanobot.agent.kg.ak.core import (
    ACQUIRED_KNOWLEDGE,
    ID_PATTERN,
    BundleLock,
    check_bundle_paths,
    check_no_symlink_components,
    gitstore,
    new_id,
    note_path,
    note_paths,
    now_iso,
    read_note_meta,
    validate_note_id,
    write_atomic,
)
from nanobot.agent.kg.vendor.okf_bundle_core.errors import CASMismatchError, ZettelError
from nanobot.agent.kg.vendor.okf_bundle_core.frontmatter import serialize, split_frontmatter
from nanobot.agent.kg.vendor.okf_bundle_core.graph import LINKS_SECTION_RE
from nanobot.agent.kg.vendor.okf_bundle_core.lock import LockTimeout
from nanobot.agent.kg.vendor.okf_bundle_core.paths import PathEscapeError
from nanobot.agent.kg.vendor.okf_bundle_core.schema import ZettelFrontmatter
from nanobot.agent.kg.vendor.okf_bundle_core.zettel import notes_read

RELATIONS = frozenset({"supersedes", "contradicts", "derived_from", "related"})
MAX_BATCH_LINKS = 100


def _restore(path: Path, original: str | None) -> None:
    if original is None:
        path.unlink(missing_ok=True)
    else:
        write_atomic(path, original)


def _commit(root: Path, paths: list[Path], *, kind: str, op: str, detail: str,
            message: str, audit_path: Path | None = None) -> None:
    """Caller holds the bundle lock and restores files on failure."""
    store = gitstore(root)
    log_path = store.append_log({
        "timestamp": now_iso(), "kind": kind, "op": op,
        "path": (audit_path or paths[-1]).relative_to(root).as_posix(),
        "by": "agent:percival", "note": detail,
    })
    store.commit_paths([*paths, log_path], message)


def _existing_chunk(root: Path, source_id: str, chunk_index: int) -> str | None:
    for path in note_paths(root):
        match = ID_PATTERN.match(path.stem)
        if match is None or path.is_symlink():
            continue
        try:
            meta = read_note_meta(path)
        except (OSError, ValueError, yaml.YAMLError, ZettelError):
            continue
        if (str(meta.get("id") or match.group(1)) == match.group(1)
                and meta.get("type") == "ExtractedNote"
                and meta.get("derived_from") == [source_id]
                and meta.get("source_locator") == f"chunk #{chunk_index}"):
            return validate_note_id(str(meta["id"]))
    return None


def note_write_extracted(root: Path, source_id: str, chunk_index: int, title: str,
                         body: str, tags: list[str] | None = None,
                         expected_content_hash: str | None = None) -> dict[str, Any]:
    validate_note_id(source_id)
    if not title.strip() or len(title) > 500 or not body.strip() or len(body) > 200_000:
        raise ValueError("title and body must be nonblank and within their size limits")
    if tags is not None and (len(tags) > 50 or any(len(tag) > 64 for tag in tags)):
        raise ValueError("tags exceed size limits")
    check_bundle_paths(root, write=True)
    check_no_symlink_components(root, root / "notes")
    with BundleLock(root, ACQUIRED_KNOWLEDGE, exclusive=True, timeout=30):
        store = gitstore(root)
        src = notes_read(root, ACQUIRED_KNOWLEDGE, source_id, gitstore=store)
        if src.path.is_symlink():
            raise PathEscapeError(str(src.path))
        check_no_symlink_components(root, src.path)
        if expected_content_hash is not None and src.content_hash != expected_content_hash:
            raise CASMismatchError(f"content_hash mismatch for Source {source_id}")
        if src.frontmatter.type != "Source":
            raise ValueError(f"{source_id} is not a Source")
        total_value = (src.frontmatter.model_extra or {}).get("chunks_total", 0)
        if not isinstance(total_value, int) or isinstance(total_value, bool) or total_value < 0:
            raise ValueError(f"invalid chunks_total on Source {source_id}")
        total = total_value
        if not 0 <= chunk_index < total:
            raise IndexError(f"chunk_index {chunk_index} out of range (0..{total - 1})")

        src_text = src.path.read_text(encoding="utf-8")
        raw, src_body = split_frontmatter(src_text)
        atomized_value = cast(object, raw.get("chunks_atomized") or [])
        if not isinstance(atomized_value, list) or any(
            not isinstance(n, int) or isinstance(n, bool) or not 0 <= n < total
            for n in cast(list[object], atomized_value)
        ):
            raise ValueError("invalid chunks_atomized on Source")
        atomized = cast(list[int], atomized_value)
        old_id = _existing_chunk(root, source_id, chunk_index)
        if old_id is not None:
            old = notes_read(root, ACQUIRED_KNOWLEDGE, old_id, gitstore=store)
            # Resume interrupted/legacy atomization without creating a second note.
            if chunk_index not in atomized:
                _update_atomized(root, src.path, src_text, raw, src_body, chunk_index,
                                 [src.path], old_id, "resume")
            return {
                "extracted_id": old_id, "path": old.path.relative_to(root).as_posix(),
                "derived_from": [source_id], "source_locator": f"chunk #{chunk_index}",
                "content_hash": old.content_hash, "body_hash": old.body_hash,
                "applied": False, "reused_existing_id": old_id,
                "reused_existing_path": old.path.relative_to(root).as_posix(),
            }

        extracted_id = new_id(root)
        target = note_path(root, extracted_id, title)
        fm_data: dict[str, Any] = {
            "type": "ExtractedNote", "id": extracted_id, "title": title,
            "extraction_kind": "manual", "derived_from": [source_id],
            "source_locator": f"chunk #{chunk_index}",
            "generated": {"by": "agent:percival", "at": now_iso()}, "status": "stable",
        }
        if tags:
            fm_data["tags"] = tags
        fm = ZettelFrontmatter(**fm_data)
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            write_atomic(target, serialize(fm, body))
            _update_atomized(root, src.path, src_text, raw, src_body, chunk_index,
                             [target, src.path], extracted_id, "atomize")
        except Exception:
            target.unlink(missing_ok=True)
            raise
        result = notes_read(root, ACQUIRED_KNOWLEDGE, extracted_id, gitstore=store)
        return {
            "extracted_id": extracted_id, "path": target.relative_to(root).as_posix(),
            "derived_from": [source_id], "source_locator": f"chunk #{chunk_index}",
            "content_hash": result.content_hash, "body_hash": result.body_hash,
            "applied": True,
        }


def _update_atomized(root: Path, src_path: Path, src_text: str, raw: dict[str, Any],
                     body: str, chunk_index: int, paths: list[Path], extracted_id: str,
                     operation: str) -> None:
    old_log = (root / "log.md").read_text(encoding="utf-8") if (root / "log.md").exists() else None
    try:
        raw["chunks_atomized"] = sorted(set(raw.get("chunks_atomized") or []) | {chunk_index})
        raw["generated"] = {"by": "process:atomize", "at": now_iso()}
        write_atomic(src_path, serialize(ZettelFrontmatter(**raw), body))
        _commit(root, paths, kind="extracted_note", op=operation,
                detail=f"from {raw['id']} chunk {chunk_index}",
                message=f"atomize(percival): {extracted_id} from {raw['id']} chunk {chunk_index}",
                audit_path=paths[0])
    except Exception:
        _restore(src_path, src_text)
        _restore(root / "log.md", old_log)
        raise


def note_link(root: Path, from_id: str, to_id: str, relation: str = "related") -> dict[str, Any]:
    validate_note_id(from_id)
    validate_note_id(to_id)  # Forward refs within AK are allowed; cross-bundle IDs are not.
    if relation not in RELATIONS:
        raise ValueError(f"invalid relation {relation!r}")
    if from_id == to_id:
        raise ValueError("cannot link note to itself")
    check_bundle_paths(root, write=True)
    check_no_symlink_components(root, root / "notes")
    with BundleLock(root, ACQUIRED_KNOWLEDGE, exclusive=True, timeout=30):
        src = notes_read(root, ACQUIRED_KNOWLEDGE, from_id, gitstore=gitstore(root))
        if src.path.is_symlink():
            raise PathEscapeError(str(src.path))
        check_no_symlink_components(root, src.path)
        original = src.path.read_text(encoding="utf-8")
        raw, body = split_frontmatter(original)
        destination = "body" if relation in {"related", "contradicts"} else "frontmatter"
        if destination == "body":
            # Only the same relation is idempotent; stronger relations can coexist
            # in the source and graph D65 precedence chooses the visible edge.
            present = any(
                (match := LINKS_SECTION_RE.match(line)) is not None
                and match.group(1) == relation
                and (match.group("wiki") or match.group("mdhref")) == to_id
                for line in body.splitlines()
            )
            if not present:
                entry = f"- {relation} :: [[{to_id}]]"
                body = body.rstrip() + ("\n" if "## Links" in body else "\n\n## Links\n") + f"\n{entry}\n"
        else:
            targets: Any = raw.get(relation) or []
            if not isinstance(targets, list):
                raise ValueError(f"invalid {relation} on note {from_id}")
            present = to_id in targets
            if not present:
                raw[relation] = [*targets, to_id]
        if not present:
            log = root / "log.md"
            old_log = log.read_text(encoding="utf-8") if log.exists() else None
            try:
                write_atomic(src.path, serialize(ZettelFrontmatter(**raw), body))
                _commit(root, [src.path], kind=src.frontmatter.type, op="link",
                        detail=f"link {relation}: {from_id} -> {to_id}",
                        message=f"link(percival): {from_id} -{relation}-> {to_id}")
            except Exception:
                _restore(src.path, original)
                _restore(log, old_log)
                raise
    return {"from_id": from_id, "to_id": to_id, "relation": relation,
            "applied": not present, "written_to": destination}


def note_batch_link(root: Path, from_ids: list[str], to_ids: list[str],
                    relations: list[str] | None = None) -> dict[str, Any]:
    if not 1 <= len(from_ids) <= MAX_BATCH_LINKS or len(from_ids) != len(to_ids):
        raise ValueError(f"from_ids/to_ids must have the same length (1..{MAX_BATCH_LINKS})")
    if relations is None:
        relations = ["related"] * len(from_ids)
    if len(relations) != len(from_ids):
        raise ValueError("relations must have the same length as from_ids")
    items: list[dict[str, Any]] = []
    for from_id, to_id, relation in zip(from_ids, to_ids, relations):
        item: dict[str, Any] = {"from_id": from_id, "to_id": to_id, "relation": relation}
        try:
            result = note_link(root, from_id, to_id, relation)
            item.update(status="applied" if result["applied"] else "skipped",
                        written_to=result["written_to"])
        except (LockTimeout, PathEscapeError):
            raise
        except Exception as exc:
            item.update(status="error", error=str(exc) or type(exc).__name__)
        items.append(item)
    return {
        "applied_count": sum(i["status"] == "applied" for i in items),
        "skipped_count": sum(i["status"] == "skipped" for i in items),
        "error_count": sum(i["status"] == "error" for i in items), "items": items,
    }
