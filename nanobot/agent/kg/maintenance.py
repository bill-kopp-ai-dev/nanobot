"""Local, deterministic KG maintenance operations used by the CLI."""

from __future__ import annotations

import re
import tempfile
from pathlib import Path
from typing import Any, cast

from nanobot.agent.kg.ak import core as ak_core
from nanobot.agent.kg.cm import core as cm_core
from nanobot.agent.kg.cm.f2 import memory_set_protected
from nanobot.agent.kg.vendor.okf_bundle_core.errors import ZettelError
from nanobot.agent.kg.vendor.okf_bundle_core.frontmatter import (
    extract_links,
    serialize,
    split_frontmatter,
)
from nanobot.agent.kg.vendor.okf_bundle_core.gitstore import GitStore
from nanobot.agent.kg.vendor.okf_bundle_core.graph import build_graph
from nanobot.agent.kg.vendor.okf_bundle_core.lock import BundleLock
from nanobot.agent.kg.vendor.okf_bundle_core.paths import (
    ACQUIRED_KNOWLEDGE,
    COLLECTIVE_MEMORY,
    BundleLayout,
    PathEscapeError,
)
from nanobot.agent.kg.vendor.okf_bundle_core.schema import ZettelFrontmatter, validate_frontmatter
from nanobot.agent.kg.vendor.okf_bundle_core.zettel import write_atomic

LAYOUTS = {"cm": COLLECTIVE_MEMORY, "ak": ACQUIRED_KNOWLEDGE}
_ID = re.compile(r"^([0-9]{8}-[0-9]{6})(?:-|$)")
_BODY_RELATIONS = ("contradicts", "related")


def require_bundle(root: Path, kind: str, *, write: bool = False) -> BundleLayout:
    """Reject absent/partial bundles and redirected paths before maintenance."""
    layout = LAYOUTS[kind]
    if not root.is_dir() or not (root / "notes").is_dir() or not (root / ".git").is_dir():
        raise FileNotFoundError(f"bundle not initialized: {root}; run nanobot kg bundle init {kind}")
    if kind == "cm":
        cm_core.check_bundle_paths(root, write=write)
    else:
        ak_core.check_bundle_paths(root, write=write)
    for path in (root / "graphify-out", root / "graphify-out" / "graph.json"):
        if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
            raise PathEscapeError(str(path))
    return layout


def init_bundle(root: Path, kind: str) -> dict[str, str]:
    """Initialize a new or empty root, never modifying an existing bundle."""
    layout = LAYOUTS[kind]
    if root.exists():
        if not root.is_dir():
            raise FileExistsError(f"destination is not a directory: {root}")
        if any(root.iterdir()):
            raise FileExistsError(f"destination is not empty: {root}")
    if root.parent != root and root.parent.exists() and not root.parent.is_dir():
        # The bundle's parent must itself be a directory; a regular file or
        # device path surfaces as Errno 20 ("Not a directory") deep in
        # ``mkdir`` without this guard.
        raise FileExistsError(f"parent is not a directory: {root.parent}")
    root.mkdir(parents=True, exist_ok=True)
    # Hold the bundle lock for the whole init so two concurrent CLI invocations
    # cannot both pass the ``any(root.iterdir())`` check and race on
    # ``ensure_repo()``. The lock's own ``_open`` creates the lock file on
    # demand, so it is safe to take before any bundle subdirectories exist.
    lock = root / layout.lock_file
    if lock.is_symlink():
        raise PathEscapeError(str(lock))
    with BundleLock(root, layout, exclusive=True):
        for name in (layout.notes_dir, *layout.extra_dirs):
            (root / name).mkdir(exist_ok=True)
        GitStore(root, layout).ensure_repo()
    return {"bundle": kind, "path": str(root), "result": "initialized"}


def rebuild_graph(root: Path, kind: str) -> dict[str, Any]:
    """Rebuild the graph artifact atomically, with no graphify/LLM side effects."""
    layout = require_bundle(root, kind, write=True)
    lock = root / layout.lock_file
    if lock.is_symlink():
        raise PathEscapeError(str(lock))
    with BundleLock(root, layout, exclusive=True):
        output_dir = root / "graphify-out"
        if output_dir.is_symlink() or not output_dir.resolve().is_relative_to(root.resolve()):
            raise PathEscapeError(str(output_dir))
        output_dir.mkdir(exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=output_dir, suffix=".json", delete=False) as handle:
            temporary = Path(handle.name)
        try:
            result = build_graph(root, layout, output=temporary)
            temporary.replace(output_dir / "graph.json")
        finally:
            temporary.unlink(missing_ok=True)
    return {"bundle": kind, "path": str(output_dir / "graph.json"),
            "nodes": result.nodes, "edges": result.edges,
            "edges_collapsed": result.edges_collapsed,
            "edges_dangling": result.edges_dangling,
            "dangling_edges": result.dangling_edges}


def p11_candidates(root: Path, *, top_degree: int = 10) -> list[dict[str, Any]]:
    """Legacy P11 structural signals: top-degree hubs and canonical references."""
    require_bundle(root, "cm")
    degree: dict[str, int] = {}
    canonical: set[str] = set()
    meta: dict[str, tuple[Path, str | None, bool]] = {}
    for path in sorted((root / "notes").glob("*.md")):
        cm_core.check_no_symlink_components(root, path)
        match = _ID.match(path.stem)
        if not match:
            continue
        try:
            raw, body = split_frontmatter(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, ZettelError):
            continue
        fm, _ = validate_frontmatter(raw)
        if fm is None:
            continue
        note_id = match.group(1)
        meta[note_id] = (path, fm.title, bool(fm.protected))
        targets = [link.target for link in extract_links(body) if not link.is_external]
        degree[note_id] = degree.get(note_id, 0) + len(targets)
        for target in targets:
            degree[target] = degree.get(target, 0) + 1
        for ref in [*(fm.derived_from or []), *(fm.supersedes or [])]:
            canonical.add(ref)
            degree[ref] = degree.get(ref, 0) + 1
    hubs = {note_id for note_id, count in sorted(degree.items(), key=lambda item: (-item[1], item[0]))[:top_degree] if count > 0}
    candidates: list[dict[str, Any]] = []
    for note_id, (path, title, protected) in meta.items():
        reasons: list[str] = []
        if note_id in hubs:
            reasons.append(f"god node (degree {degree[note_id]})")
        if note_id in canonical:
            reasons.append("referenced by derived_from/supersedes")
        if reasons:
            candidates.append({"id": note_id, "title": title, "path": path.relative_to(root).as_posix(),
                               "degree": degree.get(note_id, 0), "already_protected": protected,
                               "reason": " + ".join(reasons)})
    return sorted(candidates, key=lambda item: (-item["degree"], item["id"]))


def bootstrap_p11(root: Path, *, apply: bool = False, top_degree: int = 10) -> dict[str, Any]:
    if apply:
        require_bundle(root, "cm", write=True)
    candidates = p11_candidates(root, top_degree=top_degree)
    result: dict[str, Any] = {"bundle_root": str(root), "dry_run": not apply,
                              "candidates": candidates, "total": len(candidates),
                              "pending": sum(not item["already_protected"] for item in candidates)}
    if apply:
        applied: list[dict[str, Any]] = []
        for item in candidates:
            if item["already_protected"]:
                continue
            try:
                outcome = memory_set_protected(root, item["id"], True, reason=f"p11 bootstrap: {item['reason']}")
                applied.append({"id": item["id"], "changed": outcome["changed"]})
            except (OSError, ValueError, ZettelError) as exc:
                applied.append({"id": item["id"], "error": f"{type(exc).__name__}: {exc}"})
        result["applied"] = applied
    return result


def migrate_lateral_links(root: Path, *, apply: bool = False) -> dict[str, Any]:
    """Move AK lateral frontmatter edges into graph-visible body links."""
    require_bundle(root, "ak", write=apply)
    layout = ACQUIRED_KNOWLEDGE
    cm_ids: set[str] = set()
    sibling = root.parent / ".collective-memory"
    if sibling.is_symlink():
        raise PathEscapeError(str(sibling))
    if sibling.is_dir():
        # The sibling's read access must not require a fully initialized
        # CM bundle — AK users may have only an empty ``.collective-memory``
        # directory. We only need its canonical IDs to classify
        # cross-bundle references.
        cm_notes = sibling / "notes"
        if not cm_notes.is_symlink():
            cm_ids = {m.group(1) for path in cm_notes.glob("*.md") if (m := _ID.match(path.stem))}

    def scan() -> tuple[dict[Path, tuple[str, str]], dict[str, Any]]:
        paths = ak_core.note_paths(root)
        ids = {m.group(1) for path in paths if (m := _ID.match(path.stem))}
        updates: dict[Path, tuple[str, str]] = {}
        skipped: list[tuple[str, str, str, str]] = []
        moved = already = 0
        for path in paths:
            match = _ID.match(path.stem)
            if match is None:
                continue
            try:
                original = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            try:
                raw, body = split_frontmatter(original)
            except ZettelError:
                continue
            if not raw:
                continue
            changed = False
            for relation in _BODY_RELATIONS:
                values = raw.get(relation)
                if not values:
                    continue
                targets: object = [values] if isinstance(values, str) else values
                if not isinstance(targets, list) or not all(isinstance(t, str) for t in cast(list[object], targets)):
                    raise ValueError(f"invalid {relation} in {path}")
                valid_targets = cast(list[str], targets)
                remaining: list[str] = []
                for target in valid_targets:
                    target = target.strip()
                    if target not in ids:
                        remaining.append(target)
                        skipped.append((match.group(1), relation, target,
                                        "cross-bundle" if target in cm_ids else "true-broken"))
                        continue
                    changed = True
                    if re.search(rf"\[\[{re.escape(target)}(?:\||\])", body):
                        already += 1
                        continue
                    entry = f"- {relation} :: [[{target}]]"
                    body = body.rstrip() + ("\n" if "## Links" in body else "\n\n## Links\n\n") + entry + "\n"
                    moved += 1
                if remaining:
                    raw[relation] = remaining
                else:
                    raw.pop(relation)
            if changed:
                updates[path] = (original, serialize(ZettelFrontmatter(**raw), body))
        return updates, {"bundle_root": str(root), "applied": apply,
                         "notes_touched": len(updates), "edges_moved": moved,
                         "already_in_body": already, "edges_skipped": len(skipped),
                         "skipped_targets": skipped}

    if not apply:
        return scan()[1]
    ak_core.check_no_symlink_components(root, root / layout.lock_file)
    for name in (".git", ".gitignore", "log.md"):
        ak_core.check_no_symlink_components(root, root / name)
    with BundleLock(root, layout, exclusive=True):
        updates, report = scan()
        if not updates:
            return report
        store = GitStore(root, layout)
        log = root / "log.md"
        old_log = log.read_text(encoding="utf-8") if log.exists() else None
        try:
            for path, (_, new) in updates.items():
                write_atomic(path, new)
            log_path = store.append_log({"kind": "Bundle", "op": "migrate", "path": "notes",
                                         "by": "agent:percival", "note":
                                         f"migrate lateral links fm->body: {report['edges_moved']} edges in {len(updates)} notes"})
            store.commit_paths([*updates, log_path], "migrate(percival): lateral links fm->body")
        except Exception:
            for path, (original, _) in updates.items():
                write_atomic(path, original)
            if old_log is None:
                log.unlink(missing_ok=True)
            else:
                write_atomic(log, old_log)
            raise
        return report
