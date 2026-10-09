#!/usr/bin/env python3
"""Compile hash-locked Linux/amd64, Python 3.12 channel requirements.

Run ``uv run python -m scripts.compile_channel_locks`` after changing a
channel manifest. ``--check`` validates the committed lock files and their
manifest-derived inputs without network access.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, cast

ROOT = Path(__file__).resolve().parents[1]
LOCK_DIR = ROOT / "channel-locks"
LOCK_MANIFEST = LOCK_DIR / "manifest.json"
PYTHON_VERSION = "3.12"
PYTHON_PLATFORM = "x86_64-unknown-linux-gnu"


def _requirements_sha256(requirements: list[str]) -> str:
    return hashlib.sha256("\n".join(requirements).encode("utf-8")).hexdigest()


def _load_channels() -> dict[str, list[str]]:
    sys.path.insert(0, str(ROOT))
    from nanobot.channels.registry import discover_plugins

    return {
        name: list(plugin.dependencies)
        for name, plugin in sorted(discover_plugins().items())
        if plugin.dependencies
    }


def _compile(name: str, requirements: list[str], output: Path) -> None:
    with tempfile.TemporaryDirectory(prefix="percival-channel-lock-") as temporary:
        source = Path(temporary) / "requirements.in"
        source.write_text("\n".join(requirements) + "\n", encoding="utf-8")
        command = [
            "uv", "pip", "compile", str(source),
            "--generate-hashes",
            "--python-version", PYTHON_VERSION,
            "--python-platform", PYTHON_PLATFORM,
            "--no-annotate",
            "--custom-compile-command", "uv run python -m scripts.compile_channel_locks",
            "--output-file", str(output),
        ]
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
        if result.returncode:
            raise RuntimeError(result.stderr.strip() or result.stdout.strip())


def _expected_manifest(channels: dict[str, list[str]]) -> dict[str, Any]:
    records: dict[str, Any] = {}
    for name, requirements in channels.items():
        lock_path = LOCK_DIR / f"{name}.txt"
        records[name] = {
            "requirements": requirements,
            "requirementsSha256": _requirements_sha256(requirements),
            "lockSha256": hashlib.sha256(lock_path.read_bytes()).hexdigest(),
        }
    return {
        "schemaVersion": 1,
        "pythonVersion": PYTHON_VERSION,
        "platform": "linux/amd64",
        "resolver": subprocess.run(
            ["uv", "--version"], capture_output=True, text=True, check=True,
        ).stdout.strip(),
        "channels": records,
    }


def verify(channels: dict[str, list[str]]) -> list[str]:
    errors: list[str] = []
    try:
        actual = cast(
            dict[str, Any],
            json.loads(LOCK_MANIFEST.read_text(encoding="utf-8")),
        )
    except (OSError, json.JSONDecodeError) as exc:
        return [f"cannot read {LOCK_MANIFEST}: {exc}"]
    if actual.get("schemaVersion") != 1:
        errors.append("unsupported channel lock manifest schema")
    if actual.get("pythonVersion") != PYTHON_VERSION or actual.get("platform") != "linux/amd64":
        errors.append("channel lock target does not match Python 3.12 linux/amd64")
    raw_records = actual.get("channels")
    if not isinstance(raw_records, dict):
        return errors + ["channel lock manifest has no channels object"]
    records = cast(dict[str, Any], raw_records)
    if set(records) != set(channels):
        errors.append("channel lock names do not match current plugin manifests")
    for name, requirements in channels.items():
        lock_path = LOCK_DIR / f"{name}.txt"
        raw_record = records.get(name)
        if not isinstance(raw_record, dict):
            errors.append(f"missing lock record for {name}")
            continue
        record = cast(dict[str, Any], raw_record)
        if record.get("requirements") != requirements:
            errors.append(f"manifest requirements changed for {name}; regenerate locks")
        if record.get("requirementsSha256") != _requirements_sha256(requirements):
            errors.append(f"manifest requirements hash mismatch for {name}")
        try:
            digest = hashlib.sha256(lock_path.read_bytes()).hexdigest()
        except OSError:
            errors.append(f"missing channel lock file: {lock_path}")
        else:
            if record.get("lockSha256") != digest:
                errors.append(f"channel lock file hash mismatch for {name}")
    unexpected = {
        path.stem for path in LOCK_DIR.glob("*.txt")
    } - set(channels)
    if unexpected:
        errors.append(f"unexpected channel lock files: {sorted(unexpected)}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="validate committed lock metadata")
    args = parser.parse_args()
    channels = _load_channels()
    if args.check:
        errors = verify(channels)
        for error in errors:
            print(error, file=sys.stderr)
        if errors:
            return 1
        print(f"verified {len(channels)} hash-locked channel manifests")
        return 0

    LOCK_DIR.mkdir(exist_ok=True)
    for name, requirements in channels.items():
        print(f"locking channel {name}", flush=True)
        _compile(name, requirements, LOCK_DIR / f"{name}.txt")
    LOCK_MANIFEST.write_text(
        json.dumps(_expected_manifest(channels), indent=2) + "\n",
        encoding="utf-8",
    )
    errors = verify(channels)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print(f"wrote hash locks for {len(channels)} channels to {LOCK_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
