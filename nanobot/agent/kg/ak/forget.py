"""Archive AK Sources and their raw binaries without deleting history."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path

from nanobot.agent.kg.ak.core import (
    ACQUIRED_KNOWLEDGE,
    BundleLock,
    check_bundle_paths,
    check_no_symlink_components,
    gitstore,
    now_iso,
    validate_note_id,
    write_atomic,
)
from nanobot.agent.kg.vendor.okf_bundle_core.paths import PathEscapeError
from nanobot.agent.kg.vendor.okf_bundle_core.zettel import notes_read


def _contained(root: Path, path: Path) -> None:
    if not path.resolve().is_relative_to(root.resolve()):
        raise PathEscapeError(str(path))


def _vacant(path: Path) -> Path:
    if not path.exists() and not path.is_symlink():
        return path
    stamp = datetime.now(timezone.utc).strftime("%H%M%S")
    for number in range(10000):
        candidate = path.with_name(f"{path.stem}-{stamp}-{number}{path.suffix}")
        if not candidate.exists() and not candidate.is_symlink():
            return candidate
    raise FileExistsError(f"archive destination unavailable: {path}")


def source_forget(root: Path, source_id: str, reason: str = "forgotten by agent:percival") -> dict[str, str | None]:
    validate_note_id(source_id)
    if len(reason) > 1000:
        raise ValueError("reason must be nonblank and at most 1000 characters")
    reason = " ".join(reason.split())
    if not reason:
        raise ValueError("reason must be nonblank and at most 1000 characters")
    check_bundle_paths(root, write=True)
    check_no_symlink_components(root, root / "notes")
    check_no_symlink_components(root, root / "sources")
    archive = root / ACQUIRED_KNOWLEDGE.archive_dir / "sources" / datetime.now(timezone.utc).strftime("%Y%m")
    _contained(root, archive)
    check_no_symlink_components(root, archive)
    with BundleLock(root, ACQUIRED_KNOWLEDGE, exclusive=True, timeout=30):
        store = gitstore(root)
        src = notes_read(root, ACQUIRED_KNOWLEDGE, source_id, gitstore=store)
        if src.frontmatter.type != "Source":
            raise ValueError(f"{source_id} is not a Source")
        if src.path.is_symlink():
            raise PathEscapeError(str(src.path))
        raw = src.frontmatter.model_extra or {}
        file_path = raw.get("file_path")
        binary: Path | None = None
        if isinstance(file_path, str) and file_path:
            candidate = Path(file_path)
            # The ingester owns sources/<id>.<ext>; metadata is not authority
            # to move a different source or an arbitrary bundle file.
            if (not candidate.is_absolute() and len(candidate.parts) == 2
                    and candidate.parts[0] == "sources"
                    and candidate.stem == source_id and candidate.suffix):
                binary = root / candidate
                _contained(root, binary)
                if binary.is_symlink():
                    raise PathEscapeError(str(binary))
                if not binary.is_file():
                    binary = None
            else:
                raise ValueError(f"invalid Source file_path: {file_path!r}")
        _contained(root, src.path)
        check_no_symlink_components(root, src.path)
        archive.mkdir(parents=True, exist_ok=True)
        note_dst = _vacant(archive / src.path.name)
        bin_dst = _vacant(archive / binary.name) if binary is not None else None
        log = root / "log.md"
        old_log = log.read_text(encoding="utf-8") if log.exists() else None
        moved_note = moved_binary = False
        try:
            os.rename(src.path, note_dst)
            moved_note = True
            if binary is not None and bin_dst is not None:
                os.rename(binary, bin_dst)
                moved_binary = True
            store.append_log({
                "timestamp": now_iso(), "kind": "source", "op": "forget",
                "path": note_dst.relative_to(root).as_posix(), "by": "agent:percival",
                "note": f"{reason} (source_id={source_id})",
            })
            # Raw sources are D33 inbox: do not stage either binary path.
            store.commit_paths([src.path, note_dst, log],
                               f"forget(percival): {source_id} — {reason}")
        except Exception:
            if moved_binary and binary is not None and bin_dst is not None:
                os.rename(bin_dst, binary)
            if moved_note:
                os.rename(note_dst, src.path)
            if old_log is None:
                log.unlink(missing_ok=True)
            else:
                write_atomic(log, old_log)
            raise
    return {"archived": note_dst.relative_to(root).as_posix(),
            "archived_binary": bin_dst.relative_to(root).as_posix() if bin_dst is not None else None}
