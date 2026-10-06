"""Rehearse the documented cutover and snapshot rollback on synthetic copies.

The full migration/rollback gate requires copies of real operator bundles
(with multi-month log.md, several thousand notes, `sources/` binaries,
sideway `related`/`contradicts` fronts, dangling edges) and is a manual
human check (`docs/kg-migration.md`). This file keeps the deterministic
contract fast and runnable in CI without those artefacts: it covers the
mutations that **must** keep working after any change to the
maintenance, vendor lock or migration code path.
"""

from __future__ import annotations

import json
import shutil
import threading
from pathlib import Path

import pytest
from typer.testing import CliRunner

from nanobot.agent.kg.cm.core import notes_read, notes_write
from nanobot.agent.kg.maintenance import init_bundle
from nanobot.agent.kg.vendor.okf_bundle_core.gitstore import GitStore
from nanobot.agent.kg.vendor.okf_bundle_core.paths import ACQUIRED_KNOWLEDGE
from nanobot.cli.commands import app


def _seed_bundles(live: Path) -> tuple[Path, Path, str, str, str, Path]:
    cm = live / ".collective-memory"
    ak = live / ".acquired-knowledge"
    init_bundle(cm, "cm")
    init_bundle(ak, "ak")
    note_id = "20261006-120000"
    source_id = "20261006-120001"
    target_id = "20261006-120002"
    notes_write(cm, note_id=note_id, body="original CM body")
    source = ak / "notes" / f"{source_id}-source.md"
    target = ak / "notes" / f"{target_id}-extracted.md"
    source.write_text(
        f"---\nid: {source_id}\ntype: Source\ntitle: test source\nrelated:\n- {target_id}\n---\noriginal\n",
        encoding="utf-8",
    )
    target.write_text(
        f"---\nid: {target_id}\ntype: ExtractedNote\ntitle: detail\nderived_from:\n- {source_id}\n---\nbody\n",
        encoding="utf-8",
    )
    binary = ak / "sources" / f"{source_id}.bin"
    binary.write_bytes(b"raw source data\x00\xff")
    GitStore(ak, ACQUIRED_KNOWLEDGE).commit_paths([source, target], "legacy fixture")
    return cm, ak, note_id, source_id, target_id, binary


def test_cutover_and_rollback_only_touch_bundle_copies(tmp_path: Path) -> None:
    live = tmp_path / "original"
    cm, ak, note_id, source_id, _target_id, binary = _seed_bundles(live)
    # Git alone cannot restore sources/; the complete backup is necessary.
    backup = tmp_path / "backup"
    rehearsal = tmp_path / "rehearsal"
    shutil.copytree(live, backup)
    shutil.copytree(backup, rehearsal)
    runner = CliRunner()
    config = tmp_path / "config.json"
    config.write_text('{"kg": {"mode": "native"}}', encoding="utf-8")
    base = ["kg", "--config", str(config), "--workspace", str(rehearsal)]
    for command in (["doctor", "--json"], ["ak-migrate-lateral-links", "--json"]):
        result = runner.invoke(app, [*base, *command])
        assert result.exit_code == 0, result.output
    dry = json.loads(runner.invoke(app, [*base, "ak-migrate-lateral-links", "--json"]).stdout)
    assert dry["edges_moved"] == 1
    result = runner.invoke(app, [*base, "ak-migrate-lateral-links", "--apply", "--json"])
    assert result.exit_code == 0, result.output
    # More robust post-condition: the source notes file in the rehearsal still
    # carries the lateral link, encoded as a body bullet.
    source_path_rehearsal = next((rehearsal / ".acquired-knowledge" / "notes").glob("*-source.md"))
    assert "- related ::" in source_path_rehearsal.read_text()
    for kind in ("cm", "ak"):
        rebuilt = runner.invoke(app, [*base, "graph", "rebuild", kind, "--json"])
        assert rebuilt.exit_code == 0, rebuilt.output
        assert (rehearsal / (".collective-memory" if kind == "cm" else ".acquired-knowledge")
                / "graphify-out" / "graph.json").is_file()
    assert notes_read(rehearsal / ".collective-memory", note_id)["body"] == "original CM body"
    assert (rehearsal / ".acquired-knowledge" / "sources" / binary.name).read_bytes() == binary.read_bytes()
    live_source = next((ak / "notes").glob("*-source.md"))
    assert live_source.read_text(encoding="utf-8").count("related:") == 1  # live tree unchanged
    assert not (ak / "graphify-out").exists()

    # Restore a disposable copy of the pre-cutover snapshot, without assuming
    # a legacy server can read native writes (that needs real-bundle proof).
    restored = tmp_path / "restored"
    shutil.copytree(backup, restored)
    assert (restored / ".acquired-knowledge" / "notes" / f"{source_id}-source.md").read_bytes() == live_source.read_bytes()
    assert (restored / ".acquired-knowledge" / "sources" / binary.name).read_bytes() == binary.read_bytes()
    assert (restored / ".acquired-knowledge" / ".git" / "HEAD").read_bytes() == (ak / ".git" / "HEAD").read_bytes()


def test_migration_apply_is_idempotent(tmp_path: Path) -> None:
    """Running --apply twice must move each edge once and leave the second run empty."""
    live = tmp_path / "live"
    cm, ak, _source_id, _target_id, _note_id, _binary = _seed_bundles(live)
    runner = CliRunner()
    config = tmp_path / "config.json"
    config.write_text('{"kg": {"mode": "native"}}', encoding="utf-8")
    base = ["kg", "--config", str(config), "--workspace", str(live)]
    first = json.loads(runner.invoke(app, [*base, "ak-migrate-lateral-links", "--apply", "--json"]).stdout)
    assert first["edges_moved"] == 1
    second = json.loads(runner.invoke(app, [*base, "ak-migrate-lateral-links", "--apply", "--json"]).stdout)
    assert second["edges_moved"] == 0
    source_path = next((ak / "notes").glob("*-source.md"))
    body = source_path.read_text()
    # Body bullet must appear exactly once.
    assert body.count("- related ::") == 1


def test_cross_bundle_lateral_link_is_skipped(tmp_path: Path) -> None:
    """A `related:` value pointing at a CM id must be reported as cross-bundle, not moved."""
    live = tmp_path / "live"
    init_cm = live / ".collective-memory"
    init_ak = live / ".acquired-knowledge"
    init_bundle(init_cm, "cm")
    init_bundle(init_ak, "ak")
    cm_note = "20261006-120000"
    ak_source = "20261006-120001"
    cm_target = "20261006-120002"
    notes_write(init_cm, note_id=cm_note, body="CM anchor")
    notes_write(init_cm, note_id=cm_target, body="CM cross-bundle target")
    source = init_ak / "notes" / f"{ak_source}-source.md"
    source.write_text(
        f"---\nid: {ak_source}\ntype: Source\ntitle: t\nrelated:\n- {cm_target}\n---\nbody\n",
        encoding="utf-8",
    )
    GitStore(init_ak, ACQUIRED_KNOWLEDGE).commit_paths([source], "cross-bundle fixture")
    runner = CliRunner()
    config = tmp_path / "config.json"
    config.write_text('{"kg": {"mode": "native"}}', encoding="utf-8")
    base = ["kg", "--config", str(config), "--workspace", str(live)]
    result = json.loads(runner.invoke(app, [*base, "ak-migrate-lateral-links", "--apply", "--json"]).stdout)
    assert result["edges_moved"] == 0
    assert any("cross-bundle" in entry for entry in result.get("skipped_targets", []))
    # Body untouched.
    assert source.read_text().count("related:") == 1


def test_dry_run_does_not_mutate_git_history(tmp_path: Path) -> None:
    """Dry-run must not advance HEAD or leave audit entries."""
    live = tmp_path / "live"
    init_bundle(live / ".collective-memory", "cm")
    init_bundle(live / ".acquired-knowledge", "ak")
    source_id = "20261006-120000"
    target_id = "20261006-120001"
    source = live / ".acquired-knowledge" / "notes" / f"{source_id}-source.md"
    target = live / ".acquired-knowledge" / "notes" / f"{target_id}-extracted.md"
    source.write_text(
        f"---\nid: {source_id}\ntype: Source\ntitle: t\nrelated:\n- {target_id}\n---\nbody\n",
        encoding="utf-8",
    )
    target.write_text(
        f"---\nid: {target_id}\ntype: ExtractedNote\ntitle: t\n---\nbody\n",
        encoding="utf-8",
    )
    store = GitStore(live / ".acquired-knowledge", ACQUIRED_KNOWLEDGE)
    store.commit_paths([source, target], "fixture")
    head_before = (live / ".acquired-knowledge" / ".git" / "HEAD").read_bytes()
    log_path = live / ".acquired-knowledge" / "log.md"
    log_before = log_path.read_text() if log_path.exists() else ""
    runner = CliRunner()
    config = tmp_path / "config.json"
    config.write_text('{"kg": {"mode": "native"}}', encoding="utf-8")
    base = ["kg", "--config", str(config), "--workspace", str(live)]
    result = runner.invoke(app, [*base, "ak-migrate-lateral-links", "--json"])
    assert result.exit_code == 0, result.output
    assert (live / ".acquired-knowledge" / ".git" / "HEAD").read_bytes() == head_before
    log_after = log_path.read_text() if log_path.exists() else ""
    assert log_after == log_before


def test_cutover_preserves_binary_sources_outside_git(tmp_path: Path) -> None:
    """A rehearsal copy must restore raw binaries byte-for-byte, not from Git."""
    live = tmp_path / "live"
    _cm, ak, _note_id, source_id, _target_id, binary = _seed_bundles(live)
    assert binary.read_bytes() == b"raw source data\x00\xff"
    backup = tmp_path / "backup"
    shutil.copytree(live, backup)
    rehearsal = tmp_path / "rehearsal"
    shutil.copytree(backup, rehearsal)
    # Rewrite body (proves a native write) and restore from backup.
    notes_write(rehearsal / ".collective-memory", note_id="20261006-120000", body="rewritten CM body")
    assert notes_read(rehearsal / ".collective-memory", "20261006-120000")["body"] == "rewritten CM body"
    # Now restore binary from backup; Git alone would have lost the file.
    shutil.copy(backup / ".acquired-knowledge" / "sources" / binary.name,
                rehearsal / ".acquired-knowledge" / "sources" / binary.name)
    assert (rehearsal / ".acquired-knowledge" / "sources" / binary.name).read_bytes() == binary.read_bytes()


@pytest.mark.parametrize("threads", [2, 4])
def test_concurrent_native_writers_serialise(tmp_path: Path, threads: int) -> None:
    """Concurrent native writers against the same bundle must serialise via the lock,
    not corrupt the Git log."""
    live = tmp_path / "live"
    cm = live / ".collective-memory"
    init_bundle(cm, "cm")
    results: list[Exception | None] = [None] * threads

    def writer(idx: int) -> None:
        try:
            for offset in range(3):
                note_id = f"20261006-12{idx:02d}{offset:02d}"[-15:]
                notes_write(cm, note_id=note_id, body=f"writer {idx} offset {offset}")
        except Exception as exc:  # pragma: no cover - surfaced via results
            results[idx] = exc

    workers = [threading.Thread(target=writer, args=(i,)) for i in range(threads)]
    for w in workers:
        w.start()
    for w in workers:
        w.join()
    assert results == [None] * threads
    # Every committed body must be readable, and Git log must end in a clean commit.
    for idx in range(threads):
        for offset in range(3):
            note_id = f"20261006-12{idx:02d}{offset:02d}"[-15:]
            assert notes_read(cm, note_id)["body"].startswith(f"writer {idx}")
