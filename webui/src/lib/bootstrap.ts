import type { BootstrapResponse, AuthSessionStatus } from "./types";
import { fetchWithTimeout } from "./http";

const LEGACY_SECRET_STORAGE_KEY = "nanobot-webui.bootstrap-secret";

export class BootstrapAuthRequiredError extends Error {
  constructor(message = "bootstrap authentication required") {
    super(message);
    this.name = "BootstrapAuthRequiredError";
  }
}

export class LoginError extends Error {
  readonly status: number;
  readonly body: string;
  constructor(status: number, body: string) {
    super(`login failed: HTTP ${status}: ${body}`);
    this.name = "LoginError";
    this.status = status;
    this.body = body;
  }
}

export class ElevationError extends Error {
  readonly status: number;
  readonly body: string;
  constructor(status: number, body: string) {
    super(`elevation failed: HTTP ${status}: ${body}`);
    this.name = "ElevationError";
    this.status = status;
    this.body = body;
  }
}

export interface LoginResult {
  sessionId: string;
  csrfToken: string;
  sessionIdleRemainingS: number;
  sessionAbsoluteRemainingS: number;
}

function removeLegacyStorage(): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.removeItem(LEGACY_SECRET_STORAGE_KEY);
  } catch {
    // ignore storage errors
  }
}

removeLegacyStorage();

/** Log in with the single instance password over the new `/auth/login` endpoint. */
export async function login(
  password: string,
  baseUrl: string = "",
  timeoutMs?: number,
): Promise<LoginResult> {
  const res = await fetchWithTimeout(`${baseUrl}/auth/login`, {
    method: "POST",
    credentials: "same-origin",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ password }),
  }, timeoutMs);
  if (!res.ok) {
    throw new LoginError(res.status, await res.text());
  }
  const body = (await res.json()) as {
    session_id: string;
    csrf_token: string;
    session_idle_remaining_s: number;
    session_absolute_remaining_s: number;
  };
  return {
    sessionId: body.session_id,
    csrfToken: body.csrf_token,
    sessionIdleRemainingS: body.session_idle_remaining_s,
    sessionAbsoluteRemainingS: body.session_absolute_remaining_s,
  };
}

/** Clear the session cookie by calling /auth/logout. */
export async function logout(
  csrfToken: string,
  baseUrl: string = "",
  timeoutMs?: number,
): Promise<void> {
  const res = await fetchWithTimeout(`${baseUrl}/auth/logout`, {
    method: "POST",
    credentials: "same-origin",
    headers: {
      "X-Percival-CSRF": csrfToken,
    },
  }, timeoutMs);
  if (!res.ok) {
    // Logout is best-effort; a server error here is not fatal for the client.
    return;
  }
  await res.text();
}

/** Request an elevated session (15 min) for sensitive MCP mutations. */
export async function elevate(
  password: string,
  csrfToken: string,
  baseUrl: string = "",
  timeoutMs?: number,
): Promise<{ elevationRemainingS: number; elevationTtlS: number }> {
  const res = await fetchWithTimeout(`${baseUrl}/auth/elevate`, {
    method: "POST",
    credentials: "same-origin",
    headers: {
      "Content-Type": "application/json",
      "X-Percival-CSRF": csrfToken,
    },
    body: JSON.stringify({ password }),
  }, timeoutMs);
  if (!res.ok) {
    throw new ElevationError(res.status, await res.text());
  }
  const body = (await res.json()) as {
    elevation_remaining_s: number;
    elevation_ttl_s: number;
  };
  return {
    elevationRemainingS: body.elevation_remaining_s,
    elevationTtlS: body.elevation_ttl_s,
  };
}

/** Inspect the current session without re-prompting. */
export async function authStatus(
  baseUrl: string = "",
  timeoutMs?: number,
): Promise<AuthSessionStatus> {
  const res = await fetchWithTimeout(`${baseUrl}/auth/status`, {
    method: "GET",
    credentials: "same-origin",
  }, timeoutMs);
  if (!res.ok) {
    throw new Error(`status failed: HTTP ${res.status}`);
  }
  return (await res.json()) as AuthSessionStatus;
}

/**
 * Fetch a short-lived token + the WebSocket path from the gateway's
 * ``/webui/bootstrap`` endpoint using the active session cookie.
 */
export async function fetchBootstrap(
  baseUrl: string = "",
  timeoutMs?: number,
): Promise<BootstrapResponse> {
  const res = await fetchWithTimeout(`${baseUrl}/webui/bootstrap`, {
    method: "GET",
    credentials: "same-origin",
  }, timeoutMs);
  if (!res.ok) {
    if (res.status === 401 || res.status === 403) {
      throw new BootstrapAuthRequiredError(`bootstrap failed: HTTP ${res.status}`);
    }
    throw new Error(`bootstrap failed: HTTP ${res.status}`);
  }
  const body = (await res.json()) as BootstrapResponse;
  if (!body.ws_path || !body.token || !body.api_token) {
    throw new Error("bootstrap response missing session credentials");
  }
  return body;
}

/** Derive a WebSocket URL from the current window location and the server-provided path. */
export function deriveWsUrl(
  wsPath: string,
  token: string,
  wsUrl?: string | null,
): string {
  const query = `?token=${encodeURIComponent(token)}`;
  const path = wsPath && wsPath.startsWith("/") ? wsPath : `/${wsPath || ""}`;
  if (typeof window !== "undefined" && window.location.port === "5173") {
    const host = window.location.hostname.includes(":")
      ? `[${window.location.hostname}]`
      : window.location.hostname;
    let scheme = "ws";
    let port = "8765";
    if (wsUrl && /^wss?:\/\//i.test(wsUrl)) {
      const upstream = new URL(wsUrl);
      scheme = upstream.protocol === "wss:" ? "wss" : "ws";
      port = upstream.port;
    }
    const authority = port ? `${host}:${port}` : host;
    return `${scheme}://${authority}${path}${query}`;
  }
  if (wsUrl && /^(wss?|nanobot-host):\/\//i.test(wsUrl)) {
    const join = wsUrl.includes("?") ? "&" : "?";
    return `${wsUrl}${join}token=${encodeURIComponent(token)}`;
  }
  if (typeof window === "undefined") {
    return `ws://127.0.0.1:8765${path}${query}`;
  }
  const scheme = window.location.protocol === "https:" ? "wss" : "ws";
  const host = window.location.host;
  return `${scheme}://${host}${path}${query}`;
}
