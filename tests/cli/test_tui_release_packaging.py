"""Keep TUI runtime notices aligned with the pinned runtime."""

import importlib.util
import io
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("package_release", ROOT / "tui/scripts/package-release.py")
assert SPEC is not None and SPEC.loader is not None
packager = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(packager)


def test_current_notices_match_pinned_opentui():
    root = ROOT / "tui"
    version = json.loads((root / "package.json").read_text())["dependencies"]["@opentui/core"]
    packager._validate_opentui_version(root, f"===== @opentui/core {version} (MIT) =====")


def test_source_archive_does_not_reintroduce_removed_documents():
    source = packager._source_archive(ROOT / "tui")
    with packager.tarfile.open(fileobj=io.BytesIO(source), mode="r:gz") as archive:
        names = {Path(member.name).name for member in archive.getmembers()}
    assert "SOURCE_OFFER.md" not in names
    assert "RELINKING.md" not in names


@pytest.mark.parametrize(
    ("version", "notices", "error"),
    [
        ("^0.5.10", "0.5.10", "exact release version"),
        ("0.5.10", "0.5.3", "third-party notices"),
    ],
)
def test_rejects_stale_runtime_materials(tmp_path, version, notices, error):
    (tmp_path / "package.json").write_text(json.dumps({"dependencies": {"@opentui/core": version}}))
    with pytest.raises(ValueError, match=error):
        packager._validate_opentui_version(tmp_path, f"===== @opentui/core {notices} (MIT) =====")
