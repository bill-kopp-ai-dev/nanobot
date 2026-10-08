"""Typed broker client. Never forward unvalidated Docker arguments or URLs."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, cast

from nanobot.config.mcp_docker import SERVER_ID

_OPERATIONS = frozenset({
    "install", "configure", "disable-tool", "enable-tool", "activate",
    "deactivate", "update-image", "restart", "start", "stop", "exclude", "reconcile", "recover",
    "hydrate", "status", "observe", "health",
})


class BrokerUnavailableError(Exception):
    def __init__(self, message: str, *, reason: str = "unavailable") -> None:
        self.reason = reason
        super().__init__(message)


class BrokerRejectedError(Exception):
    """The broker responded but rejected a validly transported request."""

    def __init__(self, status_code: int, message: str) -> None:
        self.status_code = status_code
        super().__init__(message)


class BrokerClient:
    def __init__(self, token_file: Path, *, port: int = 18081) -> None:
        if port < 1 or port > 65535:
            raise ValueError("invalid broker port")
        self.token_file = token_file
        self.port = port

    def action(self, operation: str, server_id: str, data: dict[str, Any]) -> dict[str, Any]:
        if operation not in _OPERATIONS or not SERVER_ID.fullmatch(server_id):
            raise ValueError("unsupported broker action")
        token = self.token()
        request = urllib.request.Request(
            f"http://127.0.0.1:{self.port}/v1/{operation}",
            data=json.dumps({"server_id": server_id, **data}).encode("utf-8"),
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            method="POST",
        )
        try:
            # Ignore proxy variables for the dedicated localhost transport.
            opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
            with opener.open(request, timeout=30) as response:
                response_payload: object = json.load(response)
            if not isinstance(response_payload, dict):
                raise BrokerUnavailableError("invalid broker response", reason="invalid-response")
            return cast(dict[str, Any], response_payload)
        except urllib.error.HTTPError as exc:
            message = "request rejected"
            try:
                error_payload: object = json.load(exc)
                if isinstance(error_payload, dict):
                    error_mapping = cast(dict[str, object], error_payload)
                    if isinstance(error_mapping.get("error"), str):
                        message = cast(str, error_mapping["error"])
            except (ValueError, OSError):
                pass
            detail = f"broker rejected {operation} (HTTP {exc.code}): {message}"
            if 400 <= exc.code < 500:
                raise BrokerRejectedError(exc.code, detail) from exc
            raise BrokerUnavailableError(detail, reason="broker-error") from exc
        except (urllib.error.URLError, TimeoutError, ValueError, OSError) as exc:
            raise BrokerUnavailableError("broker is unavailable", reason="transport") from exc

    def token(self) -> str:
        """Read the current rotatable token from a private instance file."""
        try:
            token = self.token_file.read_text(encoding="utf-8").strip()
            stat = self.token_file.stat()
            # Gateway owns the file; the isolated broker reads through the
            # configured dedicated group. Refuse group-write, others-rwx and
            # any path the gateway group is not meant to access.
            group = int(os.environ.get("PERCIVAL_BROKER_TOKEN_GID", "65532"))
            if len(token) < 32:
                raise BrokerUnavailableError("broker token is too short", reason="token-invalid")
            if (not stat.st_mode & 0o400 or stat.st_mode & 0o027 or
                (stat.st_mode & 0o040 and stat.st_gid != group) or
                stat.st_uid not in {os.getuid(), 0}):
                raise BrokerUnavailableError("broker token owner, group or mode is invalid", reason="token-permissions")
        except FileNotFoundError as exc:
            raise BrokerUnavailableError("broker token is missing", reason="token-missing") from exc
        except (OSError, ValueError) as exc:
            raise BrokerUnavailableError("broker token is unreadable", reason="token-unreadable") from exc
        return token
