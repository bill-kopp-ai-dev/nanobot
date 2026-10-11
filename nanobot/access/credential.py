"""Hashed single-password credential for a Percival instance.

Reuses and generalises the prior operator-admin verifier (scrypt N=2^15, r=8,
p=1) so the operator-facing file moves from ``mcp-docker/operator.json`` to a
neutral location. Concurrent CLI processes and the gateway share a
file-system lock to avoid racing on initialisation.
"""

from __future__ import annotations

import base64
import contextlib
import fcntl
import hashlib
import hmac
import json
import os
import threading
import time
import unicodedata
from pathlib import Path
from typing import Any

from nanobot.access.errors import AccessError
from nanobot.access.password import MAX_PASSWORD_BYTES, accept_password
from nanobot.utils.helpers import _write_text_atomic  # pyright: ignore[reportPrivateUsage]

_N = 2**15
_R = 8
_P = 1
_SALT_BYTES = 16
_DIGEST_BYTES = 32
_MAX_SCRYPT_MEM = 64 * 1024 * 1024

_LOCK_DIR_NAME = ".lock"
_LOCK_STALE_AGE_S = 30.0


class AccessCredentialError(AccessError):
    """Base for credential storage failures."""


class AccessCredential:
    """Hashed single-password verifier persisted in the instance data dir."""

    schema_version = 1

    def __init__(self, data_dir: Path) -> None:
        self._data_dir = data_dir
        self.path = data_dir / "auth" / "verifier.json"
        self._lock_path = data_dir / "auth" / _LOCK_DIR_NAME
        self._path_lock = threading.RLock()

    # -- Lifecycle -------------------------------------------------------

    def exists(self) -> bool:
        return self.path.is_file()

    def is_usable(self) -> bool:
        if not self.exists():
            return False
        try:
            payload = self._read_payload()
        except (OSError, ValueError, KeyError, TypeError):
            return False
        return self._decode(payload) is not None

    def revision(self) -> tuple[int, int, int, int] | None:
        """Return a cheap file identity used to detect out-of-process rotation."""
        try:
            stat = self.path.stat()
        except FileNotFoundError:
            return None
        return (stat.st_dev, stat.st_ino, stat.st_mtime_ns, stat.st_size)

    # -- Verify ----------------------------------------------------------

    def verify(self, password: str) -> bool:
        if not password:
            return False
        normalised = unicodedata.normalize("NFC", password)
        try:
            if len(normalised.encode("utf-8")) > MAX_PASSWORD_BYTES:
                return False
        except UnicodeEncodeError:
            return False
        if not self.exists():
            return False
        try:
            payload = self._read_payload()
        except (OSError, ValueError, KeyError, TypeError):
            return False
        decoded = self._decode(payload)
        if decoded is None:
            return False
        algorithm, n, r, p, salt, expected = decoded
        if algorithm != "scrypt":
            return False
        try:
            actual = hashlib.scrypt(
                normalised.encode("utf-8"),
                salt=salt,
                n=n,
                r=r,
                p=p,
                dklen=_DIGEST_BYTES,
                maxmem=_MAX_SCRYPT_MEM,
            )
        except (ValueError, OSError):
            return False
        return hmac.compare_digest(actual, expected)

    # -- Mutate ----------------------------------------------------------

    def set_password(
        self,
        password: str,
        *,
        current_password: str | None = None,
        recover: bool = False,
    ) -> None:
        """Replace the stored verifier.

        With ``recover=True`` the existing verifier is overwritten without
        requiring the current password; this path is reserved for the
        local-recovery CLI and must be explicitly authorised by the operator.
        """
        accepted = accept_password(password)
        with self._process_lock():
            if self.exists() and not recover:
                if current_password is None or not self.verify(current_password):
                    raise AccessCredentialError("current password required")
            salt = os.urandom(_SALT_BYTES)
            digest = hashlib.scrypt(
                accepted.encode("utf-8"),
                salt=salt,
                n=_N,
                r=_R,
                p=_P,
                dklen=_DIGEST_BYTES,
                maxmem=_MAX_SCRYPT_MEM,
            )
            payload = {
                "schemaVersion": self.schema_version,
                "algorithm": "scrypt",
                "n": _N,
                "r": _R,
                "p": _P,
                "salt": base64.b64encode(salt).decode("ascii"),
                "digest": base64.b64encode(digest).decode("ascii"),
                "createdAt": int(time.time()),
            }
            self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            os.chmod(self.path.parent, 0o700)
            _write_text_atomic(self.path, json.dumps(payload), initial_mode=0o600)

    # -- Helpers ---------------------------------------------------------

    def _read_payload(self) -> dict[str, Any]:
        with self.path.open("r", encoding="utf-8") as handle:
            return json.loads(handle.read())

    def _decode(
        self,
        payload: dict[str, Any],
    ) -> tuple[str, int, int, int, bytes, bytes] | None:
        try:
            if int(payload.get("schemaVersion", -1)) != self.schema_version:
                return None
            algorithm = payload.get("algorithm")
            if not isinstance(algorithm, str):
                return None
            n = int(payload["n"])
            r = int(payload["r"])
            p = int(payload["p"])
            salt = base64.b64decode(str(payload["salt"]), validate=True)
            digest = base64.b64decode(str(payload["digest"]), validate=True)
        except (KeyError, TypeError, ValueError):
            return None
        if (n, r, p) != (_N, _R, _P) or len(salt) != _SALT_BYTES or len(digest) != _DIGEST_BYTES:
            return None
        return algorithm, n, r, p, salt, digest

    @contextlib.contextmanager
    def _process_lock(self):
        """Cross-process exclusive lock for write paths.

        ``fcntl`` is unavailable on Windows. The in-process RLock is always
        acquired first to serialise threads within the gateway.
        """
        with self._path_lock:
            self._lock_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            fd = os.open(
                self._lock_path,
                os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW,
                0o600,
            )
            try:
                if hasattr(fcntl, "flock"):
                    self._acquire_flock(fd)
                try:
                    yield
                finally:
                    if hasattr(fcntl, "flock"):
                        with contextlib.suppress(OSError):
                            fcntl.flock(fd, fcntl.LOCK_UN)
            finally:
                os.close(fd)

    def _acquire_flock(self, fd: int) -> None:
        """Best-effort cross-process flock with stale-lock recovery."""
        if not hasattr(fcntl, "flock"):
            return
        deadline = time.monotonic() + 10.0
        while True:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                return
            except BlockingIOError:
                if self._lock_is_stale() and time.monotonic() < deadline:
                    with contextlib.suppress(OSError):
                        fcntl.flock(fd, fcntl.LOCK_UN)
                    continue
                if time.monotonic() >= deadline:
                    fcntl.flock(fd, fcntl.LOCK_EX)
                    return
                time.sleep(0.05)

    def _lock_is_stale(self) -> bool:
        try:
            stat = self._lock_path.stat()
        except OSError:
            return False
        return (time.time() - stat.st_mtime) > _LOCK_STALE_AGE_S


__all__ = [
    "AccessCredential",
    "AccessCredentialError",
]
