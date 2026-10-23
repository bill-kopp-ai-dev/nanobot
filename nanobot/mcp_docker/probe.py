"""Authenticated, read-only broker readiness probe for the minimal sidecar image."""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
from pathlib import Path
from typing import cast


def check(token_file: Path, *, port: int = 18081) -> None:
    """Verify HTTP authentication and the broker's host policy, not just TCP."""
    if not 1 <= port <= 65535:
        raise ValueError("invalid broker port")
    if token_file.stat().st_mode & 0o037:
        raise ValueError("invalid broker token permissions")
    token = token_file.read_text(encoding="utf-8").strip()
    if len(token) < 32:
        raise ValueError("invalid broker token")
    request = urllib.request.Request(
        f"http://127.0.0.1:{port}/v1/health",
        data=b'{"server_id":"broker"}',
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        method="POST",
    )
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(request, timeout=30) as response:
        payload: object = json.load(response)
    if not isinstance(payload, dict) or cast(dict[str, object], payload).get("ready") is not True:
        raise ValueError("invalid broker readiness response")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=18081)
    args = parser.parse_args()
    try:
        check(Path(os.environ["PERCIVAL_BROKER_TOKEN_FILE"]), port=args.port)
    except (KeyError, OSError, ValueError):
        # Do not print token contents, private paths, headers or server errors.
        print("broker readiness failed (token, transport or host policy)", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
