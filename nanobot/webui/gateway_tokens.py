"""Token state for the embedded WebUI gateway.

Tokens are short-lived and tied to an authenticated session when one is
required. Trusted-proxy requests may still issue a token without an explicit
session for proxy-mediated identity providers (preserved behaviour, but
never the default).
"""

from __future__ import annotations

import secrets
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Literal

from websockets.http11 import Request as WsRequest

from nanobot.webui.http_utils import bearer_token, parse_query, query_first

IssuedTokenAudience = Literal["client", "webui"]


@dataclass
class GatewayTokenStore:
    """Own short-lived WebSocket and WebUI API tokens for one gateway process."""

    max_tokens: int = 10_000
    instance_id: str = field(default_factory=lambda: str(uuid.uuid4()), init=False)
    issued_tokens: dict[str, float] = field(default_factory=dict)
    issued_token_sessions: dict[str, str] = field(default_factory=dict)
    issued_token_audiences: dict[str, IssuedTokenAudience] = field(default_factory=dict)
    api_tokens: dict[str, float] = field(default_factory=dict)
    api_token_sessions: dict[str, str] = field(default_factory=dict)
    session_validator: Callable[[str], bool] | None = field(default=None, repr=False)

    def check_api_token(self, request: WsRequest) -> bool:
        self._purge_expired_api_tokens()
        token = bearer_token(request.headers) or query_first(
            parse_query(request.path), "token"
        )
        if not token:
            return False
        expiry = self.api_tokens.get(token)
        if expiry is None or time.monotonic() > expiry:
            self.api_tokens.pop(token, None)
            self.api_token_sessions.pop(token, None)
            return False
        session_id = self.api_token_sessions.get(token)
        if session_id is not None and (
            self.session_validator is None or not self.session_validator(session_id)
        ):
            self.api_tokens.pop(token, None)
            self.api_token_sessions.pop(token, None)
            return False
        return True

    def session_for_api_token(self, token: str) -> str | None:
        if not token:
            return None
        if time.monotonic() > self.api_tokens.get(token, 0.0):
            return None
        session_id = self.api_token_sessions.get(token)
        if session_id is not None and (
            self.session_validator is None or not self.session_validator(session_id)
        ):
            return None
        return session_id

    def can_issue(self, *, include_api_token: bool = False) -> bool:
        self._purge_expired_issued_tokens()
        self._purge_expired_api_tokens()
        if len(self.issued_tokens) >= self.max_tokens:
            return False
        if include_api_token and len(self.api_tokens) >= self.max_tokens:
            return False
        return True

    def issue_token(
        self,
        ttl_s: int | float,
        *,
        audience: IssuedTokenAudience = "client",
        session_id: str | None = None,
    ) -> str:
        token_value = f"nbwt_{secrets.token_urlsafe(32)}"
        expiry = time.monotonic() + float(ttl_s)
        self.issued_tokens[token_value] = expiry
        self.issued_token_audiences[token_value] = audience
        if session_id:
            self.issued_token_sessions[token_value] = session_id
        return token_value

    def issue_api_token(
        self,
        ttl_s: int | float,
        *,
        session_id: str | None = None,
    ) -> str:
        token_value = f"nbwt_{secrets.token_urlsafe(32)}"
        expiry = time.monotonic() + float(ttl_s)
        self.api_tokens[token_value] = expiry
        if session_id:
            self.api_token_sessions[token_value] = session_id
        return token_value

    def take_issued_token_audience(
        self,
        token_value: str | None,
    ) -> IssuedTokenAudience | None:
        if not token_value:
            return None
        self._purge_expired_issued_tokens()
        expiry = self.issued_tokens.pop(token_value, None)
        if expiry is None:
            self.issued_token_audiences.pop(token_value, None)
            self.issued_token_sessions.pop(token_value, None)
            return None
        audience = self.issued_token_audiences.pop(token_value, "client")
        self.issued_token_sessions.pop(token_value, None)
        if time.monotonic() > expiry:
            return None
        return audience

    def session_for_issued_token(self, token_value: str | None) -> str | None:
        if not token_value:
            return None
        if time.monotonic() > self.issued_tokens.get(token_value, 0.0):
            return None
        return self.issued_token_sessions.get(token_value)

    def revoke_session_tokens(self, session_id: str) -> None:
        for store, session_map in (
            (self.issued_tokens, self.issued_token_sessions),
            (self.api_tokens, self.api_token_sessions),
        ):
            for token, owner in list(session_map.items()):
                if owner == session_id:
                    store.pop(token, None)
                    session_map.pop(token, None)

    def clear(self) -> None:
        self.issued_tokens.clear()
        self.issued_token_sessions.clear()
        self.issued_token_audiences.clear()
        self.api_tokens.clear()
        self.api_token_sessions.clear()

    def _purge_expired_api_tokens(self) -> None:
        now = time.monotonic()
        for token_key, expiry in list(self.api_tokens.items()):
            if now > expiry:
                self.api_tokens.pop(token_key, None)
                self.api_token_sessions.pop(token_key, None)

    def _purge_expired_issued_tokens(self) -> None:
        now = time.monotonic()
        for token_key, expiry in list(self.issued_tokens.items()):
            if now > expiry:
                self.issued_tokens.pop(token_key, None)
                self.issued_token_audiences.pop(token_key, None)
                self.issued_token_sessions.pop(token_key, None)


def token_response_payload(token: str, expires_in: Any) -> dict[str, Any]:
    return {"token": token, "expires_in": expires_in}
