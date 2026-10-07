"""Local operator credential for Docker MCP administration."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import threading
from pathlib import Path

from nanobot.utils.helpers import _write_text_atomic  # pyright: ignore[reportPrivateUsage]

_LOCK = threading.RLock()
_N, _R, _P = 2**15, 8, 1


class OperatorCredential:
    def __init__(self, data_dir: Path) -> None:
        self.path = data_dir / "mcp-docker" / "operator.json"

    def exists(self) -> bool:
        return self.path.is_file()

    def verify(self, password: str) -> bool:
        if not password or not self.exists():
            return False
        try:
            stored = json.loads(self.path.read_text(encoding="utf-8"))["hash"]
            algorithm, n, r, p, salt, digest = stored.split("$")
            if (algorithm, int(n), int(r), int(p)) != ("scrypt", _N, _R, _P):
                return False
            salt_bytes = base64.b64decode(salt, validate=True)
            expected = base64.b64decode(digest, validate=True)
            if len(salt_bytes) != 16 or len(expected) != 32:
                return False
            actual = hashlib.scrypt(password.encode(), salt=salt_bytes, n=_N, r=_R, p=_P, dklen=32, maxmem=64 * 1024 * 1024)
            return hmac.compare_digest(actual, expected)
        except (OSError, ValueError, KeyError, TypeError):
            return False

    def set_password(self, password: str, *, current_password: str | None = None, recover: bool = False) -> None:
        if not password or len(password.encode()) > 1024:
            raise ValueError("operator password must be 1 to 1024 UTF-8 bytes")
        with _LOCK:
            if self.exists() and not recover and (current_password is None or not self.verify(current_password)):
                raise PermissionError("current operator password required")
            self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            salt = os.urandom(16)
            digest = hashlib.scrypt(password.encode(), salt=salt, n=_N, r=_R, p=_P, dklen=32, maxmem=64 * 1024 * 1024)
            encoded = "$".join(("scrypt", str(_N), str(_R), str(_P),
                                 base64.b64encode(salt).decode(), base64.b64encode(digest).decode()))
            if self.path.exists():
                os.chmod(self.path, 0o600)
            _write_text_atomic(self.path, json.dumps({"hash": encoded}), initial_mode=0o600)
