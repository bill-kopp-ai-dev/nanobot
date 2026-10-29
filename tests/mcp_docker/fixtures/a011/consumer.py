"""Disposable consumer fixture for the IaC installation preflight contract."""

from __future__ import annotations

import argparse
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preflight-script", required=True, type=Path)
    parser.add_argument("--installation-id", required=True)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    command = list(args.command)
    if command and command[0] == "--":
        command.pop(0)
    if not command:
        parser.error("provide the fixture consumer command after --")
    return subprocess.run(
        [
            sys.executable,
            str(args.preflight_script),
            "--installation-id",
            args.installation_id,
            "--",
            *command,
        ],
        check=False,
    ).returncode


if __name__ == "__main__":
    raise SystemExit(main())
