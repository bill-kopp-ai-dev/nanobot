"""HTTP and handshake composition for the WebUI gateway listener."""

from __future__ import annotations

import asyncio
import inspect
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, cast
from urllib.parse import urlsplit

from websockets.asyncio.server import ServerConnection
from websockets.http11 import Request as WsRequest

from nanobot.webui.gateway_auth import AccessController
from nanobot.webui.gateway_tokens import GatewayTokenStore
from nanobot.webui.http_utils import (
    is_localhost,
    is_loopback_host,
    normalize_config_path,
    origin_matches_request,
    parse_request_path,
    query_first,
)
from nanobot.webui.ws_http import GatewayHTTPHandler

if TYPE_CHECKING:
    from nanobot.channels.websocket.runtime import WebSocketConfig


def is_websocket_upgrade(request: WsRequest) -> bool:
    """Return whether a request contains a complete WebSocket upgrade handshake."""
    upgrade = request.headers.get("Upgrade") or request.headers.get("upgrade")
    connection = request.headers.get("Connection") or request.headers.get("connection")
    return bool(
        upgrade
        and "websocket" in upgrade.lower()
        and connection
        and "upgrade" in connection.lower()
    )


class WebUIGatewayEndpoint:
    """Compose HTTP routing and WebSocket authentication on one listener."""

    def __init__(
        self,
        *,
        config: WebSocketConfig,
        http: GatewayHTTPHandler,
        tokens: GatewayTokenStore,
        access: AccessController,
    ) -> None:
        self._config = config
        self._http = http
        self._tokens = tokens
        self._access = access
        self.webui_connections: set[ServerConnection] = set()
        # session_id -> set of connections, used to revoke open sockets
        self._connections_by_session: dict[str, set[ServerConnection]] = {}
        self._session_by_connection: dict[ServerConnection, str] = {}

    async def process_request(
        self,
        connection: ServerConnection,
        request: WsRequest,
        *,
        is_allowed: Callable[[str], bool],
    ) -> Any:
        """Route one listener request to a WS handshake or the HTTP application."""
        got, query = parse_request_path(request.path)
        expected_ws = normalize_config_path(self._config.path)
        if got == expected_ws and is_websocket_upgrade(request):
            terminal_version = query_first(query, "terminal_protocol")
            if terminal_version is not None and (
                terminal_version != "1"
                or query_first(query, "terminal_instance") != self._tokens.instance_id
            ):
                return connection.respond(409, "Terminal instance or protocol changed")
            client_id = query_first(query, "client_id") or ""
            if len(client_id) > 128:
                client_id = client_id[:128]
            if not is_allowed(client_id):
                return connection.respond(403, "Forbidden")
            return self.authorize_websocket_handshake(connection, query, request.headers)
        return await self._http.dispatch(connection, request)

    def authorize_websocket_handshake(
        self,
        connection: ServerConnection,
        query: dict[str, list[str]],
        headers: Any = None,
    ) -> Any:
        """Authorize a WebSocket upgrade and remember trusted WebUI connections."""
        if headers is not None:
            host_value = headers.get("Host", "") or headers.get("host", "")
            host = str(host_value or "")
            scheme_value = getattr(getattr(connection, "request", None), "scheme", None)
            scheme = cast(str | None, scheme_value)
            if not origin_matches_request(headers, host, scheme):
                origin_value = headers.get("Origin", "") or headers.get("origin", "")
                origin = str(origin_value or "")
                try:
                    parsed_origin = urlsplit(origin)
                    origin_host = parsed_origin.hostname or ""
                    scheme_matches = not scheme or parsed_origin.scheme == scheme
                except ValueError:
                    origin_host = ""
                    scheme_matches = False
                local_dev_origin = (
                    is_loopback_host(self._config.host)
                    and is_localhost(connection)
                    and is_loopback_host(origin_host)
                    and scheme_matches
                )
                if not local_dev_origin:
                    return connection.respond(403, "Origin does not match request host")
        supplied = query_first(query, "token")
        if supplied:
            session_id = self._tokens.session_for_issued_token(supplied)
            if session_id and self._consume_issued_with_session(connection, supplied, session_id):
                return None
            static_token = self._config.token.strip()
            if static_token and _safe_compare(supplied, static_token):
                # Legacy static tokens were retired in 0.1.0; refuse them.
                pass
            return connection.respond(401, "Unauthorized")

        return connection.respond(401, "Unauthorized")

    def _consume_issued_with_session(
        self,
        connection: ServerConnection,
        token_value: str,
        session_id: str,
    ) -> bool:
        from nanobot.access.errors import AuthError

        try:
            session = self._access.session(session_id)
        except AuthError:
            return False
        audience = self._tokens.take_issued_token_audience(token_value)
        if audience is None:
            return False
        if audience == "webui":
            self.webui_connections.add(connection)
        self.attach_session(connection, session.session_id)
        return True

    def attach_session(self, connection: ServerConnection, session_id: str) -> None:
        self._connections_by_session.setdefault(session_id, set()).add(connection)
        self._session_by_connection[connection] = session_id

    def validate_connection_session(self, connection: ServerConnection) -> bool:
        session_id = self._session_by_connection.get(connection)
        if session_id is None:
            return True
        from nanobot.access.errors import AuthError

        try:
            self._access.session(session_id)
        except AuthError:
            self.revoke_session(session_id)
            return False
        return True

    def close_expired_session_connections(self) -> None:
        for session_id in list(self._connections_by_session):
            if not self._access.session_is_valid(session_id):
                self.revoke_session(session_id)

    def discard_connection(self, connection: ServerConnection) -> None:
        self.webui_connections.discard(connection)
        session_id = self._session_by_connection.pop(connection, None)
        if session_id is not None:
            session_set = self._connections_by_session.get(session_id)
            if session_set is not None:
                session_set.discard(connection)
                if not session_set:
                    self._connections_by_session.pop(session_id, None)

    def revoke_session(self, session_id: str) -> None:
        for connection in list(self._connections_by_session.get(session_id, set())):
            self.discard_connection(connection)
            try:
                result = connection.close()
                if inspect.isawaitable(result):
                    asyncio.ensure_future(result)
            except Exception:
                pass
        self._connections_by_session.pop(session_id, None)

    def revoke_all_sessions(self) -> None:
        for session_id in list(self._connections_by_session):
            self.revoke_session(session_id)

    def clear(self) -> None:
        self.webui_connections.clear()
        self._connections_by_session.clear()
        self._session_by_connection.clear()


def _safe_compare(provided: str, expected: str) -> bool:
    import hmac

    return hmac.compare_digest(provided, expected)
