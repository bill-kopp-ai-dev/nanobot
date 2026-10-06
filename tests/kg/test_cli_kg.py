"""F8 CLI gates: isolation, dry runs, Git initialization and graph artifacts."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from nanobot.agent.kg import maintenance
from nanobot.agent.kg.cm.core import notes_read, notes_write
from nanobot.agent.kg.vendor.okf_bundle_core.gitstore import GitStore
from nanobot.agent.kg.vendor.okf_bundle_core.paths import ACQUIRED_KNOWLEDGE
from nanobot.cli.commands import app

runner = CliRunner()
A = "20261006-120000"
B = "20261006-120001"


@pytest.fixture
def kg_cli(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, list[str]]:
    for name in ("COLLECTIVE_MEMORY_ROOT", "ACQUIRED_KNOWLEDGE_ROOT"):
        monkeypatch.delenv(name, raising=False)
    config = tmp_path / "config.json"
    config.write_text("{}", encoding="utf-8")
    workspace = tmp_path / "workspace"
    return workspace, ["kg", "--config", str(config), "--workspace", str(workspace)]


def test_init_doctor_paths_graph_and_no_overwrite(kg_cli: tuple[Path, list[str]], tmp_path: Path) -> None:
    workspace, base = kg_cli
    missing = runner.invoke(app, [*base, "doctor", "--json"])
    assert missing.exit_code == 1
    assert [item["status"] for item in json.loads(missing.stdout)] == ["fail", "fail"]
    for kind, name in (("cm", ".collective-memory"), ("ak", ".acquired-knowledge")):
        root = workspace / name
        path = runner.invoke(app, [*base, "bundle", "path", kind])
        assert path.exit_code == 0 and path.stdout.strip() == str(root)
        rejected = runner.invoke(app, [*base, "bundle", "init", kind], input="n\n")
        assert rejected.exit_code == 1 and not root.exists()
        initialized = runner.invoke(app, [*base, "bundle", "init", kind, "--yes", "--json"])
        assert initialized.exit_code == 0, initialized.output
        assert json.loads(initialized.stdout)["result"] == "initialized"
        assert (root / "notes").is_dir() and (root / ".git" / "HEAD").is_file()
        assert (root / ".gitignore").is_file()
        again = runner.invoke(app, [*base, "bundle", "init", kind, "--yes"])
        assert again.exit_code == 1 and "not empty" in again.output
        parent = runner.invoke(app, [*base, "bundle", "path", kind, "--bundle-root", str(workspace)])
        direct = runner.invoke(app, [*base, "bundle", "path", kind, "--bundle-root", str(root)])
        assert parent.stdout == direct.stdout == path.stdout

    doctor = runner.invoke(app, [*base, "doctor", "--json"])
    assert doctor.exit_code == 0
    assert [item["status"] for item in json.loads(doctor.stdout)] == ["warn", "warn"]
    assert not (workspace / ".collective-memory" / "graphify-out").exists()
    notes_write(workspace / ".collective-memory", note_id=A, body=f"see [[{B}]]")
    notes_write(workspace / ".collective-memory", note_id=B, body="hub")
    for kind in ("cm", "ak"):
        rebuilt = runner.invoke(app, [*base, "graph", "rebuild", kind, "--json"])
        assert rebuilt.exit_code == 0, rebuilt.output
        payload = json.loads(rebuilt.stdout)
        assert payload["nodes"] == (2 if kind == "cm" else 0)
        assert payload["edges"] == (1 if kind == "cm" else 0)
        assert runner.invoke(app, [*base, "graph", "rebuild", kind, "--json"]).stdout == rebuilt.stdout
    assert [item["status"] for item in json.loads(runner.invoke(app, [*base, "doctor", "--json"]).stdout)] == ["ok", "ok"]

    # An empty parent and an explicitly named bundle both select the same new root.
    external = tmp_path / "different"
    result = runner.invoke(app, [*base, "bundle", "init", "cm", "--bundle-root", str(external), "--yes"])
    assert result.exit_code == 0 and (external / ".collective-memory" / ".git").exists()


def test_p11_bootstrap_is_dry_by_default_and_apply_is_idempotent(kg_cli: tuple[Path, list[str]]) -> None:
    workspace, base = kg_cli
    assert runner.invoke(app, [*base, "bundle", "init", "cm", "--yes"]).exit_code == 0
    root = workspace / ".collective-memory"
    notes_write(root, note_id=A, body=f"See [[{B}]]")
    notes_write(root, note_id=B, body="hub")
    dry = runner.invoke(app, [*base, "p11", "bootstrap", "--dry-run", "--json"])
    assert dry.exit_code == 0, dry.output
    report = json.loads(dry.stdout)
    assert report["pending"] == 2 and report["dry_run"] is True
    assert notes_read(root, B)["frontmatter"]["protected"] is False
    applied = runner.invoke(app, [*base, "p11", "bootstrap", "--apply", "--json"])
    assert applied.exit_code == 0, applied.output
    assert len(json.loads(applied.stdout)["applied"]) == 2
    assert notes_read(root, B)["frontmatter"]["protected"] is True
    repeated = runner.invoke(app, [*base, "p11", "bootstrap", "--apply", "--json"])
    assert repeated.exit_code == 0 and json.loads(repeated.stdout)["applied"] == []
    assert runner.invoke(app, [*base, "p11", "bootstrap", "--apply", "--dry-run"]).exit_code != 0


def test_ak_migration_dry_run_cross_bundle_and_commit(kg_cli: tuple[Path, list[str]]) -> None:
    workspace, base = kg_cli
    for kind in ("cm", "ak"):
        assert runner.invoke(app, [*base, "bundle", "init", kind, "--yes"]).exit_code == 0
    notes_write(workspace / ".collective-memory", note_id="20261006-120003", body="cross")
    root = workspace / ".acquired-knowledge"
    source = root / "notes" / f"{A}-source.md"
    target = root / "notes" / f"{B}-target.md"
    source.write_text(
        f"---\ntype: Source\nid: {A}\ntitle: source\nrelated:\n- {B}\n- 20261006-120003\n"
        f"contradicts:\n- 20261006-120004\n---\noriginal body\n", encoding="utf-8",
    )
    target.write_text(f"---\ntype: ExtractedNote\nid: {B}\ntitle: target\n---\nbody\n", encoding="utf-8")
    store = GitStore(root, ACQUIRED_KNOWLEDGE)
    store.commit_paths([source, target], "fixture")
    before = source.read_text()
    dry = runner.invoke(app, [*base, "ak-migrate-lateral-links", "--json"])
    assert dry.exit_code == 0, dry.output
    report = json.loads(dry.stdout)
    assert (report["notes_touched"], report["edges_moved"], report["edges_skipped"]) == (1, 1, 2)
    assert {item[3] for item in report["skipped_targets"]} == {"cross-bundle", "true-broken"}
    assert source.read_text() == before and not (root / "log.md").exists()
    applied = runner.invoke(app, [*base, "ak-migrate-lateral-links", "--apply", "--json"])
    assert applied.exit_code == 0, applied.output
    assert "- related :: [[20261006-120001]]" in source.read_text()
    assert "20261006-120003" in source.read_text() and "20261006-120004" in source.read_text()
    assert (root / "log.md").is_file() and len(store.log_for(source)) == 2
    second = runner.invoke(app, [*base, "ak-migrate-lateral-links", "--apply", "--json"])
    assert second.exit_code == 0 and json.loads(second.stdout)["notes_touched"] == 0


def test_root_boundary_and_graph_symlink_do_not_write(kg_cli: tuple[Path, list[str]], tmp_path: Path) -> None:
    workspace, base = kg_cli
    config = Path(base[2])
    config.write_text('{"tools": {"restrictToWorkspace": true}}')
    outside = tmp_path / "outside"
    outside.mkdir()
    denied = runner.invoke(app, [*base, "bundle", "init", "cm", "--bundle-root", str(outside), "--yes"])
    assert denied.exit_code == 1 and not list(outside.iterdir())
    assert runner.invoke(app, [*base, "bundle", "init", "cm", "--yes"]).exit_code == 0
    root = workspace / ".collective-memory"
    (root / "graphify-out").symlink_to(outside, target_is_directory=True)
    denied_graph = runner.invoke(app, [*base, "graph", "rebuild", "cm"])
    assert denied_graph.exit_code == 1 and not list(outside.iterdir())
    checks = json.loads(runner.invoke(app, [*base, "doctor", "--json"]).stdout)
    assert checks[0]["status"] == "fail"


def test_rebuild_failure_preserves_served_graph(
    kg_cli: tuple[Path, list[str]], monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace, base = kg_cli
    assert runner.invoke(app, [*base, "bundle", "init", "cm", "--yes"]).exit_code == 0
    root = workspace / ".collective-memory"
    assert runner.invoke(app, [*base, "graph", "rebuild", "cm"]).exit_code == 0
    graph = root / "graphify-out" / "graph.json"
    original = graph.read_bytes()

    def fail_build(*args: object, **kwargs: object) -> None:
        Path(kwargs["output"]).write_text("truncated")
        raise OSError("disk failure")

    monkeypatch.setattr(maintenance, "build_graph", fail_build)
    failed = runner.invoke(app, [*base, "graph", "rebuild", "cm"])
    assert failed.exit_code == 1 and "disk failure" in failed.output
    assert graph.read_bytes() == original
    assert sorted(p.name for p in graph.parent.iterdir()) == ["graph.json"]


def test_migration_commit_failure_restores_notes_and_log(
    kg_cli: tuple[Path, list[str]], monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace, base = kg_cli
    assert runner.invoke(app, [*base, "bundle", "init", "ak", "--yes"]).exit_code == 0
    root = workspace / ".acquired-knowledge"
    source = root / "notes" / f"{A}-source.md"
    target = root / "notes" / f"{B}-target.md"
    source.write_text(f"---\ntype: Source\nid: {A}\nrelated: [{B}]\n---\nbody\n")
    target.write_text(f"---\ntype: ExtractedNote\nid: {B}\n---\nbody\n")
    original = source.read_bytes()
    (root / "log.md").write_text("previous audit\n")

    def fail_commit(self: GitStore, paths: list[Path], message: str) -> str:
        raise OSError("commit failure")

    monkeypatch.setattr(GitStore, "commit_paths", fail_commit)
    failed = runner.invoke(app, [*base, "ak-migrate-lateral-links", "--apply"])
    assert failed.exit_code == 1 and "commit failure" in failed.output
    assert source.read_bytes() == original
    assert (root / "log.md").read_text() == "previous audit\n"


def test_legacy_env_precedence_and_doctor_corrupt_graph(
    kg_cli: tuple[Path, list[str]], monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace, base = kg_cli
    config_parent = workspace / "configured"
    env_parent = workspace / "legacy"
    Path(base[2]).write_text(json.dumps({"kg": {"cmRoot": str(config_parent)}}))
    monkeypatch.setenv("COLLECTIVE_MEMORY_ROOT", str(env_parent))
    chosen = runner.invoke(app, [*base, "bundle", "path", "cm"])
    root = env_parent / ".collective-memory"
    assert chosen.exit_code == 0 and chosen.stdout.strip() == str(root)
    assert runner.invoke(app, [*base, "bundle", "init", "cm", "--yes"]).exit_code == 0
    graph = root / "graphify-out" / "graph.json"
    graph.parent.mkdir()
    graph.write_text("not JSON")
    before = graph.read_bytes()
    doctor = runner.invoke(app, [*base, "doctor", "--json"])
    assert doctor.exit_code == 1
    checks = json.loads(doctor.stdout)
    assert checks[0]["bundle"] == "cm" and checks[0]["status"] == "fail"
    assert any("overrides kg.cm_root" in item["detail"] for item in checks)
    assert graph.read_bytes() == before


def test_bundle_init_refuses_regular_file_path(kg_cli: tuple[Path, list[str]], tmp_path: Path) -> None:
    workspace, base = kg_cli
    conflict = tmp_path / "stays_file"
    conflict.write_text("i'm a file, not a bundle", encoding="utf-8")
    denied = runner.invoke(app, [*base, "bundle", "init", "cm", "--bundle-root", str(conflict), "--yes"])
    assert denied.exit_code == 1
    assert "not a directory" in denied.output
    assert conflict.read_text(encoding="utf-8") == "i'm a file, not a bundle"


def test_ak_migration_tolerates_partial_cm_sibling_and_unreadable_note(
    kg_cli: tuple[Path, list[str]],
) -> None:
    workspace, base = kg_cli
    assert runner.invoke(app, [*base, "bundle", "init", "ak", "--yes"]).exit_code == 0
    cm = workspace / ".collective-memory"
    (cm / "notes").mkdir(parents=True)
    (cm / "notes" / "20261006-120003-target.md").write_text(
        "---\ntype: Note\nid: 20261006-120003\ntitle: cm target\n---\nbody\n", encoding="utf-8",
    )
    root = workspace / ".acquired-knowledge"
    source = root / "notes" / f"{A}-source.md"
    target = root / "notes" / f"{B}-target.md"
    source.write_text(
        f"---\ntype: Source\nid: {A}\ntitle: source\nrelated:\n- 20261006-120003\n"
        f"- {B}\n---\nbody\n", encoding="utf-8",
    )
    target.write_text(f"---\ntype: ExtractedNote\nid: {B}\n---\nbody\n", encoding="utf-8")
    (root / "notes" / "20261006-130000-unreadable.md").write_bytes(b"\xff\xfe\x00not utf-8")
    report = json.loads(runner.invoke(app, [*base, "ak-migrate-lateral-links", "--json"]).stdout)
    assert (report["edges_moved"], report["edges_skipped"], report["notes_touched"]) == (1, 1, 1)
    assert report["skipped_targets"][0][3] == "cross-bundle"
    applied = json.loads(runner.invoke(
        app, [*base, "ak-migrate-lateral-links", "--apply", "--json"]
    ).stdout)
    assert applied["edges_moved"] == 1
    assert "- related :: [[20261006-120001]]" in source.read_text(encoding="utf-8")
    assert "20261006-120003" in source.read_text(encoding="utf-8")
    assert not (cm / ".git").exists()
