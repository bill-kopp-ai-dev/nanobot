"""F4 core: AK helpers, paths, id, asset resolution, dedupe."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from nanobot.agent.kg.ak import core as ak_core
from nanobot.agent.kg.ak import paths as ak_paths
from nanobot.agent.kg.ak.cache import CacheUnavailableError, get_cache
from nanobot.agent.kg.ak.parsers import detect_kind, mimetype_from_suffix
from nanobot.agent.kg.vendor.okf_bundle_core.paths import (
    PathEscapeError,
)


def _init_bundle(tmp_path: Path) -> Path:
    bundle = tmp_path / ".acquired-knowledge"
    (bundle / "notes").mkdir(parents=True)
    return bundle


def test_find_bundle_root_prefers_env_over_config_over_workspace(tmp_path: Path) -> None:
    parent = tmp_path / "parent"
    bundle = parent / ".acquired-knowledge"
    bundle.mkdir(parents=True)
    (bundle / "notes").mkdir(parents=True)
    workspace = tmp_path / "ws"
    workspace.mkdir()

    assert ak_paths.find_bundle_root(
        env_parent=str(parent), config_parent=None, workspace=workspace,
    ) == bundle.resolve()


def test_find_bundle_root_uses_config_parent_when_no_env(tmp_path: Path) -> None:
    parent = tmp_path / "cfg"
    bundle = parent / ".acquired-knowledge"
    bundle.mkdir(parents=True)
    (bundle / "notes").mkdir(parents=True)
    assert ak_paths.find_bundle_root(
        env_parent=None, config_parent=str(parent), workspace=tmp_path,
    ) == bundle.resolve()


def test_find_bundle_root_uses_workspace_when_no_env_or_config(tmp_path: Path) -> None:
    workspace = tmp_path / "ws"
    bundle = workspace / ".acquired-knowledge"
    bundle.mkdir(parents=True)
    (bundle / "notes").mkdir(parents=True)
    assert ak_paths.find_bundle_root(
        env_parent=None, config_parent=None, workspace=workspace,
    ) == bundle.resolve()


def test_find_bundle_root_raises_when_no_candidate(tmp_path: Path) -> None:
    with pytest.raises(ak_paths.BundleNotFoundError):
        ak_paths.find_bundle_root(
            env_parent=None, config_parent=None, workspace=tmp_path / "empty",
        )


def test_detect_kind_and_mimetype_mapping() -> None:
    assert detect_kind(Path("paper.pdf")) == "document"
    assert detect_kind(Path("notes.md")) == "document"
    assert detect_kind(Path("photo.png")) == "image"
    assert detect_kind(Path("clip.webp")) == "image"
    assert detect_kind(Path("voice.mp3")) == "audio"
    assert detect_kind(Path("strange.xyz")) == "unknown"
    assert mimetype_from_suffix(".png") == "image/png"
    assert mimetype_from_suffix(".webp") == "image/webp"
    assert mimetype_from_suffix(".docx") == (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
    assert mimetype_from_suffix(".unknown") == "application/octet-stream"


def test_new_id_creates_unique_id_within_one_second_window(tmp_path: Path) -> None:
    bundle = _init_bundle(tmp_path)
    first = ak_core.new_id(bundle)
    parsed = datetime.strptime(first, "%Y%m%d-%H%M%S").replace(tzinfo=timezone.utc)
    assert (datetime.now(timezone.utc) - parsed).total_seconds() < 5


def test_new_id_bumps_one_second_when_candidate_already_used(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A collision at 12:59:59 must advance to 13:00:00, not reuse the id."""
    class FixedDatetime(datetime):
        @classmethod
        def now(cls, tz: timezone | None = None) -> datetime:
            return datetime(2026, 10, 6, 12, 59, 59, tzinfo=tz)

    monkeypatch.setattr(ak_core, "datetime", FixedDatetime)
    bundle = _init_bundle(tmp_path)
    from nanobot.agent.kg.ak.core import note_path

    first = ak_core.new_id(bundle)
    note_path(bundle, first, "pre-existing").write_text(
        "---\ntype: Source\nid: " + first + "\n---\nbody\n", encoding="utf-8",
    )
    second = ak_core.new_id(bundle)
    assert first == "20261006-125959"
    assert second == "20261006-130000"


def test_resolve_asset_path_blocks_escape_via_symlink(tmp_path: Path) -> None:
    bundle = _init_bundle(tmp_path)
    outside = tmp_path / "outside.md"
    outside.write_text("secret", encoding="utf-8")
    notes = bundle / "notes"
    notes.mkdir(parents=True, exist_ok=True)
    link = notes / "escape.md"
    link.symlink_to(outside)
    with pytest.raises(ValueError, match="outside bundle root"):
        ak_core.resolve_asset_path(bundle, str(link.relative_to(bundle)))
    with pytest.raises(FileNotFoundError):
        ak_core.resolve_asset_path(bundle, "notes/does-not-exist.md")


def test_resolve_asset_path_accepts_absolute_inside_bundle(tmp_path: Path) -> None:
    bundle = _init_bundle(tmp_path)
    sources = bundle / "sources"
    sources.mkdir(parents=True, exist_ok=True)
    image = sources / "ok.png"
    image.write_bytes(b"fake")
    resolved = ak_core.resolve_asset_path(bundle, str(image))
    assert resolved == image.resolve()


def test_check_bundle_paths_blocks_symlink_escape_on_log(tmp_path: Path) -> None:
    """A symlink pointing ``log.md`` outside the bundle is rejected on write paths."""
    bundle = _init_bundle(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    (bundle / "log.md").symlink_to(outside / "data.md")
    with pytest.raises(PathEscapeError):
        ak_core.check_bundle_paths(bundle, write=True)


def test_check_bundle_paths_allows_symlink_inside_bundle(tmp_path: Path) -> None:
    bundle = _init_bundle(tmp_path)
    inside = bundle / "notes" / "real.md"
    inside.write_text("---\ntype: Source\nid: 20261006-000000\n---\nbody\n", encoding="utf-8")
    sibling = bundle / "notes" / "link.md"
    sibling.symlink_to(inside)
    ak_core.check_bundle_paths(bundle, write=False)


def test_note_paths_rejects_file_symlink_escape(tmp_path: Path) -> None:
    bundle = _init_bundle(tmp_path)
    outside = tmp_path / "private.md"
    outside.write_text("private content", encoding="utf-8")
    link = bundle / "notes" / "20261006-000001-secret.md"
    link.symlink_to(outside)
    with pytest.raises(PathEscapeError):
        ak_core.note_paths(bundle)


def test_bundle_checks_reject_external_cache_and_telemetry_roots(tmp_path: Path) -> None:
    bundle = _init_bundle(tmp_path)
    external = tmp_path / "external"
    external.mkdir()
    (bundle / ".cache").symlink_to(external, target_is_directory=True)
    with pytest.raises(PathEscapeError):
        ak_core.check_bundle_paths(bundle)


def test_ak_cache_dependency_is_loaded_only_when_cache_is_requested(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    import importlib

    original_import = importlib.import_module

    def missing_optional(name: str, package: str | None = None):
        if name == "diskcache":
            raise ImportError("optional dependency absent")
        return original_import(name, package)

    monkeypatch.setattr(importlib, "import_module", missing_optional)
    with pytest.raises(CacheUnavailableError, match="not installed"):
        get_cache(tmp_path)
