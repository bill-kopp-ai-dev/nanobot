"""Shared HTTP helpers for the embedded WebUI gateway."""

from __future__ import annotations

import email.utils
import gzip
import http
import ipaddress
import json
import re
import time
from dataclasses import dataclass
from typing import Any, cast
from urllib.parse import parse_qs, urlparse, urlsplit

from websockets.datastructures import Headers
from websockets.http11 import Response

from nanobot.access.sessions import (
    SESSION_COOKIE_NAME,
    SESSION_CSRF_COOKIE,
    SESSION_CSRF_HEADER,
)

QueryParams = dict[str, list[str]]

_JSON_GZIP_MIN_BYTES = 4 * 1024
_JSON_GZIP_LEVEL = 5


@dataclass(slots=True)
class JSONResponseMetrics:
    """Serialization timings and sizes for an HTTP JSON response."""

    json_encode_ms: float = 0.0
    gzip_ms: float = 0.0
    uncompressed_bytes: int = 0
    response_bytes: int = 0
    gzip_enabled: bool = False


def strip_trailing_slash(path: str) -> str:
    if len(path) > 1 and path.endswith("/"):
        return path.rstrip("/")
    return path or "/"


def normalize_config_path(path: str) -> str:
    return strip_trailing_slash(path)


def case_insensitive_header(headers: Any, key: str) -> str:
    """Read a header from websockets/http test stubs without assuming casing."""
    try:
        value = headers.get(key)
    except Exception:
        value = None
    if value is None:
        try:
            value = headers.get(key.lower())
        except Exception:
            value = None
    return str(value or "").strip()


def combined_list_header(headers: Any, key: str) -> str:
    """Combine repeated values for a comma-separated HTTP list header."""
    try:
        values = headers.get_all(key)
    except (AttributeError, KeyError):
        return case_insensitive_header(headers, key)
    return ", ".join(str(value).strip() for value in values if str(value).strip())


def safe_host_header(value: str) -> str:
    """Return a safe Host header value, or empty when it should not be echoed."""
    value = value.strip()
    if not value:
        return ""
    if re.fullmatch(r"\[[0-9A-Fa-f:.]+\](?::\d{1,5})?", value):
        return value
    if re.fullmatch(r"[A-Za-z0-9.-]+(?::\d{1,5})?", value):
        return value
    return ""


def host_for_url(host: str, port: int) -> str:
    host = host.strip()
    if host in ("0.0.0.0", "::"):
        host = "127.0.0.1"
    if ":" in host and not host.startswith("["):
        host = f"[{host}]"
    return f"{host}:{port}"


def accepts_gzip(value: str) -> bool:
    wildcard_quality: float | None = None
    for item in value.split(","):
        name, *params = (part.strip() for part in item.split(";"))
        quality = 1.0
        for param in params:
            key, separator, raw_value = param.partition("=")
            if separator and key.strip().lower() == "q":
                try:
                    quality = float(raw_value.strip())
                except ValueError:
                    quality = 0.0
                break
        if name.lower() == "gzip":
            return quality > 0
        if name == "*":
            wildcard_quality = quality
    return wildcard_quality is not None and wildcard_quality > 0


def http_json_response(
    data: dict[str, Any],
    *,
    status: int = 200,
    accept_encoding: str | None = None,
    extra_headers: list[tuple[str, str]] | None = None,
    metrics: JSONResponseMetrics | None = None,
) -> Response:
    encode_started = time.perf_counter()
    body = json.dumps(data, ensure_ascii=False).encode("utf-8")
    if metrics is not None:
        metrics.json_encode_ms = (time.perf_counter() - encode_started) * 1000
        metrics.uncompressed_bytes = len(body)
    headers = [
        ("Date", email.utils.formatdate(usegmt=True)),
        ("Connection", "close"),
        ("Content-Type", "application/json; charset=utf-8"),
    ]
    if accept_encoding is not None:
        headers.append(("Vary", "Accept-Encoding"))
        if len(body) >= _JSON_GZIP_MIN_BYTES and accepts_gzip(accept_encoding):
            gzip_started = time.perf_counter()
            body = gzip.compress(body, compresslevel=_JSON_GZIP_LEVEL, mtime=0)
            if metrics is not None:
                metrics.gzip_ms = (time.perf_counter() - gzip_started) * 1000
                metrics.gzip_enabled = True
            headers.append(("Content-Encoding", "gzip"))
    if extra_headers:
        headers.extend(extra_headers)
    headers.append(("Content-Length", str(len(body))))
    if metrics is not None:
        metrics.response_bytes = len(body)
    reason = http.HTTPStatus(status).phrase
    return Response(status, reason, Headers(headers), body)


def http_response(
    body: bytes,
    *,
    status: int = 200,
    content_type: str = "text/plain; charset=utf-8",
    extra_headers: list[tuple[str, str]] | None = None,
) -> Response:
    headers = [
        ("Date", email.utils.formatdate(usegmt=True)),
        ("Connection", "close"),
        ("Content-Length", str(len(body))),
        ("Content-Type", content_type),
    ]
    if extra_headers:
        headers.extend(extra_headers)
    reason = http.HTTPStatus(status).phrase
    return Response(status, reason, Headers(headers), body)


def http_error(status: int, message: str | None = None) -> Response:
    body = (message or http.HTTPStatus(status).phrase).encode("utf-8")
    return http_response(body, status=status)


def parse_request_path(path_with_query: str) -> tuple[str, QueryParams]:
    """Parse normalized path and query parameters in one pass."""
    parsed = urlparse("ws://x" + path_with_query)
    path = strip_trailing_slash(parsed.path or "/")
    return path, parse_qs(parsed.query, keep_blank_values=True)


def parse_query(path_with_query: str) -> QueryParams:
    return parse_request_path(path_with_query)[1]


def query_first(query: QueryParams, key: str) -> str | None:
    values = query.get(key)
    return values[0] if values else None


def is_localhost(connection: Any) -> bool:
    addr = getattr(connection, "remote_address", None)
    if not addr:
        return False
    host = cast(Any, addr[0] if isinstance(addr, tuple) else addr)
    if not isinstance(host, str):
        return False
    if host.startswith("::ffff:"):
        host = host[7:]
    return host in {"127.0.0.1", "::1", "localhost"}


def _connection_ip(connection: Any) -> ipaddress.IPv4Address | ipaddress.IPv6Address | None:
    addr = getattr(connection, "remote_address", None)
    host = cast(Any, addr[0] if isinstance(addr, tuple) else addr)
    if not isinstance(host, str):
        return None
    try:
        return ipaddress.ip_address(host)
    except ValueError:
        return None


def _address_matches_network(
    address: ipaddress.IPv4Address | ipaddress.IPv6Address,
    network: ipaddress.IPv4Network | ipaddress.IPv6Network,
) -> bool:
    if isinstance(address, ipaddress.IPv4Address):
        if isinstance(network, ipaddress.IPv4Network):
            return address in network
        return ipaddress.IPv6Address(f"::ffff:{address}") in network
    if isinstance(network, ipaddress.IPv6Network):
        return address in network
    mapped = address.ipv4_mapped
    return mapped is not None and mapped in network


def is_trusted_proxy_authenticated_request(
    connection: Any,
    headers: Any,
    config: Any,
) -> bool:
    """Return True when a configured proxy peer presents a non-empty assertion."""
    if not is_trusted_proxy_peer(connection, config):
        return False
    trusted_proxy_auth = getattr(config, "trusted_proxy_auth", None)
    assertion_header = getattr(trusted_proxy_auth, "assertion_header", "")
    return bool(case_insensitive_header(headers, assertion_header))


def is_trusted_proxy_peer(connection: Any, config: Any) -> bool:
    """Return whether the immediate peer belongs to configured proxy CIDRs."""
    trusted_proxy_auth = getattr(config, "trusted_proxy_auth", None)
    if trusted_proxy_auth is None:
        return False
    address = _connection_ip(connection)
    if address is None:
        return False
    networks = getattr(trusted_proxy_auth, "_trusted_peer_networks", ())
    return any(_address_matches_network(address, network) for network in networks)


def _host_without_port(value: str) -> str:
    value = value.strip().strip('"').strip("'")
    if not value:
        return ""
    if value.startswith("["):
        end = value.find("]")
        return value[1:end] if end > 0 else value
    if value.count(":") == 1:
        host, port = value.rsplit(":", 1)
        if port.isdigit():
            return host
    return value


def is_loopback_host(value: str) -> bool:
    host = _host_without_port(value)
    if host.startswith("::ffff:"):
        host = host[7:]
    host = host.rstrip(".").lower()
    if host == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def _split_comma_header(value: str) -> list[str]:
    return [part.strip() for part in value.split(",") if part.strip()]


def _forwarded_header_values(value: str, key: str) -> list[str]:
    values: list[str] = []
    for entry in _split_comma_header(value):
        for part in entry.split(";"):
            name, sep, raw = part.partition("=")
            if sep and name.strip().lower() == key:
                cleaned = raw.strip().strip('"')
                if cleaned:
                    values.append(cleaned)
    return values


def _all_forwarded_values_are_loopback(headers: Any) -> bool:
    checks: list[str] = []
    checks.extend(_split_comma_header(case_insensitive_header(headers, "X-Forwarded-For")))
    checks.extend(_split_comma_header(case_insensitive_header(headers, "X-Real-IP")))
    checks.extend(_split_comma_header(case_insensitive_header(headers, "X-Forwarded-Host")))
    forwarded = case_insensitive_header(headers, "Forwarded")
    checks.extend(_forwarded_header_values(forwarded, "for"))
    checks.extend(_forwarded_header_values(forwarded, "host"))
    return all(is_loopback_host(value) for value in checks)


def is_local_browser_request(connection: Any, headers: Any) -> bool:
    """Return True only for a local TCP peer presenting a local browser origin."""
    if not is_localhost(connection):
        return False
    host = case_insensitive_header(headers, "Host")
    if not is_loopback_host(host):
        return False
    return _all_forwarded_values_are_loopback(headers)


def bearer_token(headers: Any) -> str | None:
    auth = headers.get("Authorization") or headers.get("authorization")
    if auth and auth.lower().startswith("bearer "):
        return auth[7:].strip() or None
    return None


_COOKIE_NAME_RE = re.compile(r"^[A-Za-z0-9_.\-]{1,64}$")


def parse_cookie_header(value: str) -> dict[str, str]:
    """Parse a Cookie header into a name->value mapping (last value wins)."""
    if not value:
        return {}
    out: dict[str, str] = {}
    for raw_segment in value.split(";"):
        segment = raw_segment.strip()
        if not segment or "=" not in segment:
            continue
        name, _, value_part = segment.partition("=")
        name = name.strip()
        if not name or not _COOKIE_NAME_RE.match(name):
            continue
        out[name] = value_part.strip()
    return out


def read_session_cookie(headers: Any) -> str:
    """Return the session cookie value, or an empty string when absent."""
    raw = case_insensitive_header(headers, "Cookie")
    if not raw:
        return ""
    cookies = parse_cookie_header(raw)
    return cookies.get(SESSION_COOKIE_NAME, "")


def read_csrf_cookie(headers: Any) -> str:
    raw = case_insensitive_header(headers, "Cookie")
    if not raw:
        return ""
    cookies = parse_cookie_header(raw)
    return cookies.get(SESSION_CSRF_COOKIE, "")


def read_csrf_header(headers: Any) -> str:
    return case_insensitive_header(headers, SESSION_CSRF_HEADER)


def build_session_cookie(value: str, *, secure: bool, max_age_s: int) -> str:
    """Render a session cookie with conservative defaults."""
    parts = [
        f"{SESSION_COOKIE_NAME}={value}",
        "Path=/",
        "HttpOnly",
        "SameSite=Strict",
        f"Max-Age={int(max_age_s)}",
    ]
    if secure:
        parts.append("Secure")
    return "; ".join(parts)


def build_csrf_cookie(value: str, *, secure: bool) -> str:
    parts = [
        f"{SESSION_CSRF_COOKIE}={value}",
        "Path=/",
        "SameSite=Strict",
        f"Max-Age={SESSION_ABSOLUTE_COOKIE_S}",
    ]
    if secure:
        parts.append("Secure")
    return "; ".join(parts)


def build_clear_cookies(secure: bool) -> list[tuple[str, str]]:
    expires = "Thu, 01 Jan 1970 00:00:00 GMT"
    parts_session = [
        f"{SESSION_COOKIE_NAME}=",
        "Path=/",
        "HttpOnly",
        "SameSite=Strict",
        f"Expires={expires}",
    ]
    parts_csrf = [
        f"{SESSION_CSRF_COOKIE}=",
        "Path=/",
        "SameSite=Strict",
        f"Expires={expires}",
    ]
    if secure:
        parts_session.append("Secure")
        parts_csrf.append("Secure")
    return [("Set-Cookie", "; ".join(parts_session)), ("Set-Cookie", "; ".join(parts_csrf))]


SESSION_ABSOLUTE_COOKIE_S = 12 * 60 * 60


def origin_matches_request(
    headers: Any,
    request_host: str,
    request_scheme: str | None = None,
) -> bool:
    """Return True when Origin is a valid same-authority HTTP(S) origin."""
    origin = case_insensitive_header(headers, "Origin")
    if not origin:
        return True
    try:
        parsed_origin = urlsplit(origin)
        parsed_host = urlsplit(f"//{request_host}")
        if parsed_origin.scheme not in {"http", "https"} or not parsed_origin.hostname:
            return False
        if request_scheme and parsed_origin.scheme != request_scheme:
            return False
        if parsed_origin.username or parsed_origin.password or parsed_origin.path not in {"", "/"}:
            return False
        if not parsed_host.hostname:
            return False
        origin_port = parsed_origin.port or (443 if parsed_origin.scheme == "https" else 80)
        host_port = parsed_host.port or origin_port
    except ValueError:
        return False
    return (
        parsed_origin.hostname.rstrip(".").casefold()
        == parsed_host.hostname.rstrip(".").casefold()
        and origin_port == host_port
    )


def cookie_request_is_secure(
    headers: Any,
    *,
    request_scheme: str | None = None,
    connection: Any = None,
    config: Any = None,
) -> bool:
    """Whether cookies should be marked Secure for this request.

    The gateway serves loopback HTTP only by default; cookies are Secure
    only when the underlying transport is HTTPS (or behind a trusted proxy
    that asserts HTTPS). The current request's ``X-Forwarded-Proto`` is
    consulted but only when the immediate peer is loopback or a trusted
    proxy peer.
    """
    if request_scheme == "https":
        return True
    if connection is not None and config is not None and not is_trusted_proxy_peer(connection, config):
        return False
    proto = case_insensitive_header(headers, "X-Forwarded-Proto").split(",", 1)[0]
    proto = proto.strip().lower()
    if proto in {"https", "wss"}:
        return True
    return False
