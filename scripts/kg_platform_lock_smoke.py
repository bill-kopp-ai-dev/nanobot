"""Cross-process lock smoke for the bundled KG core.

Runs two short-lived subprocesses that each acquire the bundle lock and
asserts that a second waiter is blocked for the expected budget. Used as
the Windows/macOS/Linux matrix check; the OS-specific lock backend
(``fcntl`` on POSIX, ``msvcrt`` on Windows) is selected automatically by
``nanobot.agent.kg.vendor.okf_bundle_core.lock``.

Run with ``python scripts/kg_platform_lock_smoke.py`` from the repository
root. Exits 0 on success, non-zero with a diagnostic message on failure.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from nanobot.agent.kg.maintenance import init_bundle  # noqa: E402
from nanobot.agent.kg.vendor.okf_bundle_core.lock import (  # noqa: E402
    BundleLock,
    LockTimeout,
)
from nanobot.agent.kg.vendor.okf_bundle_core.paths import COLLECTIVE_MEMORY  # noqa: E402


def _acquire(bundle: Path, *, exclusive: bool, timeout: float) -> BundleLock:
    lock = BundleLock(bundle, COLLECTIVE_MEMORY, exclusive=exclusive, timeout=timeout)
    lock.acquire()
    return lock


def main() -> int:
    tmp = Path(tempfile.mkdtemp())
    bundle = tmp / ".collective-memory"
    init_bundle(bundle, "cm")

    # Single-process mutual exclusion: a second writer must time out.
    held = _acquire(bundle, exclusive=True, timeout=2.0)
    try:
        try:
            contender = _acquire(bundle, exclusive=True, timeout=0.5)
        except LockTimeout:
            contender = None
        if contender is not None:
            contender.release()
            print("FAIL: second writer should have been blocked", file=sys.stderr)
            return 1
    finally:
        held.release()
    print("single-process mutual exclusion ok")

    # Cross-process mutual exclusion: a child holds the write lock for ~1.5s
    # while the parent waits with a 0.3s budget. The parent must observe a
    # LockTimeout near the budget.
    marker = tmp / "child_held"
    child_script = (
        "import sys, time;"
        f"sys.path.insert(0, {str(REPO_ROOT)!r});"
        f"from pathlib import Path;"
        f"from nanobot.agent.kg.vendor.okf_bundle_core.lock import BundleLock;"
        f"from nanobot.agent.kg.vendor.okf_bundle_core.paths import COLLECTIVE_MEMORY;"
        f"lock = BundleLock(Path({str(bundle)!r}), COLLECTIVE_MEMORY, exclusive=True, timeout=5.0);"
        f"lock.acquire();"
        f"Path({str(marker)!r}).write_text('1');"
        "time.sleep(1.5);"
        "lock.release();"
    )
    proc = subprocess.Popen(
        [sys.executable, "-c", child_script],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    deadline = time.time() + 4.0
    while not marker.exists() and time.time() < deadline:
        time.sleep(0.05)
    if not marker.exists():
        print("FAIL: child did not acquire the lock within 4s", file=sys.stderr)
        proc.kill()
        return 1
    t0 = time.time()
    contender: BundleLock | None = None
    try:
        contender = _acquire(bundle, exclusive=False, timeout=0.3)
    except LockTimeout:
        elapsed = time.time() - t0
        if not (0.25 <= elapsed <= 1.0):
            print(
                f"FAIL: reader waited {elapsed:.3f}s, expected near 0.3s budget",
                file=sys.stderr,
            )
            proc.kill()
            return 1
    if contender is not None:
        contender.release()
        print("FAIL: reader should have been blocked by the writer", file=sys.stderr)
        proc.kill()
        return 1
    proc.wait(timeout=5.0)
    print(f"cross-process lock ok ({os.name})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
