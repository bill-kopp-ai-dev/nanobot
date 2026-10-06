"""Vendored OKF core retains the on-disk CAS and flock contracts."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from nanobot.agent.kg.vendor.okf_bundle_core.errors import CASMismatchError, ZettelError
from nanobot.agent.kg.vendor.okf_bundle_core.frontmatter import split_frontmatter
from nanobot.agent.kg.vendor.okf_bundle_core.lock import BundleLock, LockTimeout
from nanobot.agent.kg.vendor.okf_bundle_core.paths import (
    ACQUIRED_KNOWLEDGE,
    COLLECTIVE_MEMORY,
    PathEscapeError,
    resolve_safe_path,
)
from nanobot.agent.kg.vendor.okf_bundle_core.zettel import (
    WriteRequest,
    notes_read,
    notes_write,
)


def test_vendored_core_cas_git_and_bundle_layout(tmp_path: Path) -> None:
    memory = tmp_path / ".collective-memory"
    knowledge = tmp_path / ".acquired-knowledge"
    identifier = "20261005-120000"
    first = notes_write(memory, COLLECTIVE_MEMORY, WriteRequest(id=identifier, body="first body"))
    assert first.path.is_relative_to(memory / "notes")
    assert (memory / ".git").is_dir()
    assert notes_read(memory, COLLECTIVE_MEMORY, identifier).body == "first body"
    second = notes_write(memory, COLLECTIVE_MEMORY, WriteRequest(
        id=identifier, body="second body", expected_body_hash=first.body_hash,
    ))
    assert second.body_hash != first.body_hash
    with pytest.raises(CASMismatchError):
        notes_write(memory, COLLECTIVE_MEMORY, WriteRequest(
            id=identifier, body="stale body", expected_body_hash=first.body_hash,
        ))
    assert notes_read(memory, COLLECTIVE_MEMORY, identifier).body == "second body"

    extracted = notes_write(knowledge, ACQUIRED_KNOWLEDGE, WriteRequest(
        id=identifier, body="AK body",
    ))
    assert extracted.path.is_relative_to(knowledge / "notes")
    assert notes_read(knowledge, ACQUIRED_KNOWLEDGE, identifier).body == "AK body"
    assert notes_read(memory, COLLECTIVE_MEMORY, identifier).body == "second body"


def test_vendored_core_errors_and_path_boundary(tmp_path: Path) -> None:
    with pytest.raises(ZettelError) as error:
        split_frontmatter("---\n:bad: [\n---\nbody")
    assert error.value.code == "frontmatter_yaml_invalid"
    with pytest.raises(PathEscapeError):
        resolve_safe_path(tmp_path, "../outside", COLLECTIVE_MEMORY)
    external = tmp_path.parent / "other-file"
    (tmp_path / "escape").symlink_to(external)
    with pytest.raises(PathEscapeError):
        resolve_safe_path(tmp_path, "escape", COLLECTIVE_MEMORY)


def test_vendored_lock_remains_compatible_with_posix_flock(tmp_path: Path) -> None:
    if os.name == "nt":
        pytest.skip("Percival KG ships Linux-only; msvcrt backend is vendored but not exercised by CI")
    import fcntl

    lock = BundleLock(tmp_path, COLLECTIVE_MEMORY, exclusive=True, timeout=0.1)
    lock.acquire()
    try:
        fd = os.open(tmp_path / COLLECTIVE_MEMORY.lock_file, os.O_RDWR)
        try:
            with pytest.raises(BlockingIOError):
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            contender = BundleLock(tmp_path, COLLECTIVE_MEMORY, timeout=0.01)
            with pytest.raises(LockTimeout):
                contender.acquire()
            assert contender._fd is None
        finally:
            os.close(fd)
    finally:
        lock.release()
    with BundleLock(tmp_path, COLLECTIVE_MEMORY, timeout=0.1):
        assert (tmp_path / COLLECTIVE_MEMORY.lock_file).exists()


def test_vendor_manifest_identifies_patched_files() -> None:
    root = Path(__file__).resolve().parents[2] / "nanobot/agent/kg/vendor"
    manifest = json.loads((root / "SOURCE.json").read_text())
    assert manifest["revision"] == "ad047aa80a849bc4038daf6efcea63e954008be9"
    assert set(manifest["patched_files"]) == {"frontmatter.py", "lock.py"}
    actual = {
        file.name: hashlib.sha256(file.read_bytes()).hexdigest()
        for file in (root / "okf_bundle_core").glob("*.py")
    }
    assert actual == manifest["vendor_python_sha256"]
    assert {name for name in actual if actual[name] != manifest["upstream_python_sha256"][name]} == set(manifest["patched_files"])
    assert (root / "LICENSE.okf-bundle-core").is_file()


def test_vendored_core_matches_pinned_upstream_fixture(tmp_path: Path) -> None:
    """Opt-in source parity check; distributed wheels do not need a sibling checkout."""
    source = os.environ.get("PERCIVAL_KG_CORE_SOURCE")
    if not source:
        pytest.skip("set PERCIVAL_KG_CORE_SOURCE for upstream parity smoke")
    package_path = Path(source) / "src/okf_bundle_core"
    if not package_path.is_dir():
        pytest.skip("pinned core checkout not available")
    revision = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=source,
        capture_output=True, text=True, check=True, timeout=5,
    ).stdout.strip()
    assert revision == "ad047aa80a849bc4038daf6efcea63e954008be9"
    vendor_license = Path(__file__).resolve().parents[2] / "nanobot/agent/kg/vendor/LICENSE.okf-bundle-core"
    assert vendor_license.read_bytes() == (Path(source) / "LICENSE").read_bytes()
    fixture = """
import importlib, json, sys
from pathlib import Path
module = importlib.import_module(sys.argv[2] + '.zettel')
paths = importlib.import_module(sys.argv[2] + '.paths')
root = Path(sys.argv[1])
identifier = '20261005-120000'
first = module.notes_write(root, paths.COLLECTIVE_MEMORY, module.WriteRequest(id=identifier, body='first'))
second = module.notes_write(root, paths.COLLECTIVE_MEMORY, module.WriteRequest(id=identifier, body='second', expected_body_hash=first.body_hash))
read = module.notes_read(root, paths.COLLECTIVE_MEMORY, identifier)
print(json.dumps({'first': first.body_hash, 'second': second.body_hash, 'read': read.body, 'id': read.id}))
"""
    upstream = subprocess.run(
        [sys.executable, "-c", fixture, str(tmp_path / "upstream"), "okf_bundle_core"],
        env={**os.environ, "PYTHONPATH": str(package_path.parent)},
        capture_output=True, text=True, check=True, timeout=20,
    )
    vendor = subprocess.run(
        [sys.executable, "-c", fixture, str(tmp_path / "vendor"),
         "nanobot.agent.kg.vendor.okf_bundle_core"],
        capture_output=True, text=True, check=True, timeout=20,
    )
    assert json.loads(upstream.stdout) == json.loads(vendor.stdout)
