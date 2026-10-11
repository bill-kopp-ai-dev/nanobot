# WebSocket Server Channel

Nanobot can act as a WebSocket server, allowing external clients (web apps, CLIs, scripts) to interact with the agent in real time via persistent connections.

## Features

- Bidirectional real-time communication over WebSocket
- Streaming support — receive agent responses token by token
- Session-bound token authentication issued by `/webui/bootstrap` after a successful `/auth/login`
- Multi-chat multiplexing — one connection can run many concurrent `chat_id`s
- TLS/SSL support (WSS) with enforced TLSv1.2 minimum
- Client allow-list via `allowFrom`
- Auto-cleanup of dead connections

## Quick Start

### 1. Configure

The WebSocket channel is enabled by default. Add only the fields you want to
override under `channels.websocket`. WebUI authentication is backed by the
single instance password stored at `~/.nanobot/auth/verifier.json` after
`nanobot auth init`; the channel no longer reads a static `token` or
`tokenIssueSecret` to authorize upgrades:

```json
{
  "channels": {
    "websocket": {
      "host": "127.0.0.1",
      "port": 8765,
      "path": "/",
      "allowFrom": ["*"],
      "streaming": true
    }
  }
}
```

### 2. Start nanobot

```bash
nanobot gateway
```

You should see:

```text
WebSocket server listening on ws://127.0.0.1:8765/
```

### 3. Connect a client

```bash
# Using websocat
websocat ws://127.0.0.1:8765/?client_id=alice

# Using Python
import asyncio, json, websockets

async def main():
    async with websockets.connect("ws://127.0.0.1:8765/?client_id=alice") as ws:
        ready = json.loads(await ws.recv())
        print(ready)  # {"event": "ready", "chat_id": "...", "client_id": "alice"}
        await ws.send(json.dumps({"content": "Hello nanobot!"}))
        reply = json.loads(await ws.recv())
        print(reply["text"])

asyncio.run(main())
```

## Connection URL

```text
ws://{host}:{port}{path}?client_id={id}&token={token}
```

| Parameter | Required | Description |
|-----------|----------|-------------|
| `client_id` | No | Identifier for `allowFrom` authorization. Auto-generated as `anon-xxxxxxxxxxxx` if omitted. Truncated to 128 chars. |
| `token` | Required | Short-lived WebSocket token returned by `/webui/bootstrap` after a successful `/auth/login`. The token is bound to the issuing session; rotating the password, logging out, or restarting the gateway invalidates it. Static tokens and proxy assertions do not bypass this requirement. |

## Wire Protocol

All frames are JSON text. Each message has an `event` field.

### Server → Client

**`ready`** — sent immediately after connection is established:

```json
{
  "event": "ready",
  "chat_id": "uuid-v4",
  "client_id": "alice"
}
```

**`message`** — full agent response:

```json
{
  "event": "message",
  "chat_id": "uuid-v4",
  "text": "Hello! How can I help?",
  "media": ["/tmp/image.png"],
  "reply_to": "msg-id"
}
```

`media` and `reply_to` are only present when applicable.

**`delta`** — streaming text chunk (only when `streaming: true`):

```json
{
  "event": "delta",
  "chat_id": "uuid-v4",
  "text": "Hello",
  "stream_id": "s1"
}
```

**`stream_end`** — signals the end of a streaming segment:

```json
{
  "event": "stream_end",
  "chat_id": "uuid-v4",
  "stream_id": "s1"
}
```

**`reasoning_delta`** — incremental model reasoning / thinking chunk for the active assistant turn. Mirrors `delta` but targets the reasoning bubble above the answer rather than the answer body:

```json
{
  "event": "reasoning_delta",
  "chat_id": "uuid-v4",
  "text": "Let me decompose ",
  "stream_id": "r1"
}
```

**`reasoning_end`** — close marker for the active reasoning stream. WebUI uses this to lock the in-place bubble and switch from the shimmer header to a static collapsed state:

```json
{
  "event": "reasoning_end",
  "chat_id": "uuid-v4",
  "stream_id": "r1"
}
```

Reasoning frames only flow when the channel's `showReasoning` is `true` (default) and the model returns reasoning content (DeepSeek-R1 / Kimi / MiMo / OpenAI reasoning models, Anthropic extended thinking, or inline `<think>` / `<thought>` tags). Models without reasoning produce zero `reasoning_delta` frames.

**`runtime_model_updated`** — broadcast when the gateway default runtime changes or
when a config reload requires clients to refresh their model catalog:

```json
{
  "event": "runtime_model_updated",
  "model_name": "openai/gpt-4.1-mini",
  "model_preset": "fast"
}
```

`model_preset` is omitted when no named preset is active. WebUI clients use this event
to refresh model settings after default-runtime and config changes. `/model <preset>`
is session-scoped; its selection is reflected through `session_updated` and the
session row's `model_preset` field instead of this global event.

**`attached`** — confirmation for `new_chat` / `attach` inbound envelopes (see [Multi-chat multiplexing](#multi-chat-multiplexing)):

```json
{"event": "attached", "chat_id": "uuid-v4"}
```

**`error`** — soft error for malformed inbound envelopes. The connection stays open:

```json
{"event": "error", "detail": "invalid chat_id"}
```

### Client → Server

**Legacy (default chat):** send a plain string, or a JSON object with a recognized text field:

```json
"Hello nanobot!"
```

```json
{"content": "Hello nanobot!"}
```

Recognized fields: `content`, `text`, `message` (checked in that order). Invalid JSON is treated as plain text. These frames route to the connection's default `chat_id` (the one announced in `ready`).

**Typed envelopes (multi-chat):** any JSON object with a string `type` field is a typed envelope:

| `type` | Fields | Effect |
|--------|--------|--------|
| `new_chat` | — | Server mints a new `chat_id`, subscribes this connection, replies with `attached`. |
| `attach` | `chat_id` | Subscribe to an existing `chat_id` (e.g. after a page reload). Replies with `attached`. |
| `message` | `chat_id`, `content` | Send `content` on `chat_id`. First use auto-attaches; no explicit `attach` needed. |

See [Multi-chat multiplexing](#multi-chat-multiplexing) for the full flow.

## Configuration Reference

All fields go under `channels.websocket` in `config.json`.

### Connection

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `enabled` | bool | `true` | Enable the WebSocket server. Set to `false` only when you intentionally do not want the bundled WebUI/WebSocket surface. |
| `host` | string | `"127.0.0.1"` | Bind address. Use `"0.0.0.0"` to accept external connections. |
| `port` | int | `8765` | Listen port. |
| `path` | string | `"/"` | WebSocket upgrade path. Trailing slashes are normalized (root `/` is preserved). |
| `publicWsUrl` | string | `""` | Exact public `ws://` or `wss://` endpoint returned by `/webui/bootstrap`. Set this when a reverse proxy forwards requests with an origin `Host` header (for example, `wss://claw.example.com/`); its path must match `path`. |
| `maxMessageBytes` | int | `37748736` | Maximum inbound message size in bytes (1 KB – 40 MB). Default (36 MB) is sized to accept up to 4 base64-encoded image attachments at 8 MB each; lower it if the channel only carries text. |

### Authentication

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `token` | string | `""` | Legacy static secret accepted for config loading only; it never authorizes a WebSocket handshake. |
| `websocketRequiresToken` | bool | `true` | Legacy setting accepted for config loading only. WebSocket handshakes always require a session-bound token. |
| `trustedProxyAuth` | object or `null` | `null` | Legacy assertion configuration does not authenticate or bypass the instance-password session. A configured peer CIDR is used only to trust forwarded HTTPS scheme metadata. |
| `trustedProxyAuth.trustedPeerCidrs` | list of CIDR strings | — | Direct TCP peer networks trusted for forwarded HTTPS scheme metadata. Universal CIDRs (`0.0.0.0/0`, `::/0`) are rejected. |
| `trustedProxyAuth.assertionHeader` | string | — | Preserved for config compatibility; its value does not authenticate a user or issue tokens. |
| `tokenTtlS` | int | `300` | Time-to-live for issued tokens in seconds (30 – 86,400). The TTL is per-session; rotating the password, logging out, or restarting the gateway invalidates outstanding tokens regardless of TTL. |

The legacy `tokenIssuePath` and `tokenIssueSecret` fields are preserved for
back-compat read but ignored. Tokens are no longer issued from a secret endpoint;
they are returned by `/webui/bootstrap` in exchange for a valid `percival_session`
cookie set by `POST /auth/login`. See [Authentication](#authentication-flow)
for the full flow.

### Access Control

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `allowFrom` | list of string | `["*"]` | Allowed `client_id` values. `"*"` allows all; `[]` denies all. |

### Streaming

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `streaming` | bool | `true` | Enable streaming mode. The agent sends `delta` + `stream_end` frames instead of a single `message`. |

### Keep-alive

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `pingIntervalS` | float | `20.0` | WebSocket ping interval in seconds (5 – 300). |
| `pingTimeoutS` | float | `20.0` | Time to wait for a pong before closing the connection (5 – 300). |

### TLS/SSL

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `sslCertfile` | string | `""` | Path to the TLS certificate file (PEM). Both `sslCertfile` and `sslKeyfile` must be set to enable WSS. |
| `sslKeyfile` | string | `""` | Path to the TLS private key file (PEM). Minimum TLS version is enforced as TLSv1.2. |

## Authentication flow

WebUI authentication is backed by the single instance password stored at
`~/.nanobot/auth/verifier.json` after `nanobot auth init`. The token issued by
`/webui/bootstrap` is short-lived and bound to the active session.

### How it works

1. The browser loads `/`. The frontend calls `GET /webui/bootstrap` with the
   `percival_session` cookie. If the cookie is missing or invalid, the
   gateway returns `401` and the frontend shows the login form.
2. The user submits the instance password to `POST /auth/login`. The gateway
   verifies the password against `auth/verifier.json` (scrypt, with rate
   limiting per account and per origin) and, on success, sets the
   `percival_session` and `percival_csrf` cookies (`HttpOnly`,
   `SameSite=Strict`, `Secure` when HTTPS).
3. Subsequent `GET /webui/bootstrap` returns a one-time-use WebSocket token
   and a REST `api_token`, both bound to the session:

   ```json
   {"token": "nbwt_aBcDeFg...", "expires_in": 300}
   ```

4. The client opens the WebSocket with `?token=nbwt_aBcDeFg...&client_id=...`.
   The token is consumed on the upgrade (single use) and cannot be reused.
   Rotating the password with `nanobot auth change`, logging out, or
   restarting the gateway invalidates outstanding tokens regardless of TTL.

Sensitive MCP mutations additionally require `POST /auth/elevate` with the same
instance password. Elevation lasts 15 minutes per session and is revoked on
logout, password rotation, or gateway restart.

### Reverse proxies

Reverse proxies must forward the native instance-password login and preserve
the matching `Host` and `Origin`. For HTTPS termination, configure the proxy
peer CIDR so `X-Forwarded-Proto: https` is trusted only from that peer; the
assertion header does not replace login, session, CSRF, or WebSocket token
checks. Keep the gateway inaccessible to untrusted direct clients. The unified
aiohttp listener serves HTTP and WebSocket upgrades on the same configured
port, including `POST /auth/login` with a JSON body.

### Example setup

```json
{
  "channels": {
    "websocket": {
      "port": 8765,
      "path": "/ws",
      "tokenTtlS": 300,
      "websocketRequiresToken": true,
      "allowFrom": ["*"],
      "streaming": true
    }
  }
}
```

Client flow (session-bound token):

```bash
# 1. Log in with the instance password and capture cookies.
curl -c cookies.txt -X POST http://127.0.0.1:8765/auth/login \
     -H 'Content-Type: application/json' \
     -d '{"password":"your-instance-password"}'

# 2. Exchange the session for a one-time WebSocket token
curl -b cookies.txt http://127.0.0.1:8765/webui/bootstrap

# 3. Connect using the token
websocat "ws://127.0.0.1:8765/ws?client_id=alice&token=nbwt_aBcDeFg..."
```

### Limits

- Issued tokens are single-use — each token can only complete one handshake.
- Outstanding tokens are capped at 10,000. Requests beyond this return HTTP 429.
- Expired tokens are purged lazily on each issue or validation request.
- Sessions are revoked on password rotation, logout, or gateway restart
  regardless of cookie TTL.

## Multi-chat multiplexing

A single WebSocket can carry many concurrent chats. The server tracks `chat_id -> {connections}` as a fan-out set, so the same chat can also be mirrored across multiple connections (e.g. two browser tabs).

### Typical flow (web UI with a sidebar)

```text
client                                server
  | --- connect -------------------->  |
  | <-- {"event":"ready",              |
  |      "chat_id":"d3..."}   (default)|
  |                                     |
  | --- {"type":"new_chat"} --------->  |
  | <-- {"event":"attached",            |
  |      "chat_id":"a1..."}             |
  |                                     |
  | --- {"type":"message",              |
  |      "chat_id":"a1...",             |
  |      "content":"hi"} ------------>  |
  | <-- {"event":"delta", ...}          |
  | <-- {"event":"stream_end", ...}     |
  |                                     |
  | --- {"type":"attach",               |  # after page reload
  |      "chat_id":"a1..."} --------->  |
  | <-- {"event":"attached", ...}       |
```

### Rules

- Every outbound event carries `chat_id`. Clients must dispatch by that field.
- `chat_id` format: `^[A-Za-z0-9_:-]{1,64}$`. Non-matching values return `error`.
- `message` auto-attaches on first use — no separate `attach` is required for chats the server minted (`new_chat`) on the same connection.
- Errors (invalid envelope, unknown `type`, bad `chat_id`) are soft: the server replies with `{"event":"error","detail":"..."}` and keeps the connection open.

### Backward compatibility

Legacy clients that only send plain text or `{"content": ...}` keep working unchanged: those frames route to the connection's default `chat_id` (the one from `ready`). No config flag is needed.

### Security boundary

`chat_id` is a *capability*: anyone holding a valid WebSocket auth credential and the chat_id can attach to that conversation and see its output. This is safe for nanobot's local, single-user model. Multi-tenant deployments should namespace chat_ids per user (or introduce a per-tenant auth gate) — nanobot does not do this today.

## Security Notes

- **Timing-safe comparison**: Static token validation uses `hmac.compare_digest` to prevent timing attacks.
- **Defense in depth**: `allowFrom` is checked at both the HTTP handshake level and the message level.
- **chat_id as capability**: see [Multi-chat multiplexing](#multi-chat-multiplexing). Auth on the WebSocket handshake is the single line of defense; callers who pass it can attach to any chat_id they know.
- **TLS enforcement**: When SSL is enabled, TLSv1.2 is the minimum allowed version.
- **Default-secure**: `websocketRequiresToken` defaults to `true`. Explicitly set it to `false` only on trusted networks.

## Media Files

Outbound `message` events may include a `media` field containing local filesystem paths. Remote clients cannot access these files directly — they need either:

- A shared filesystem mount, or
- An HTTP file server serving the nanobot media directory

## Common Patterns

### Trusted local network (no auth)

```json
{
  "channels": {
    "websocket": {
      "host": "0.0.0.0",
      "port": 8765,
      "websocketRequiresToken": false,
      "allowFrom": ["*"],
      "streaming": true
    }
  }
}
```

### Static token (legacy, rejected on upgrade in 0.1.0+)

```json
{
  "channels": {
    "websocket": {
      "token": "my-shared-secret",
      "allowFrom": ["alice", "bob"]
    }
  }
}
```

The field is preserved for back-compat reads but the WebSocket upgrade rejects
it in 0.1.0+. Clients must exchange a valid session for a token through
`/auth/login` and `/webui/bootstrap` instead.

### Public endpoint with session-bound tokens

```json
{
  "channels": {
    "websocket": {
      "host": "0.0.0.0",
      "port": 8765,
      "path": "/ws",
      "websocketRequiresToken": true,
      "sslCertfile": "/etc/ssl/certs/server.pem",
      "sslKeyfile": "/etc/ssl/private/server-key.pem",
      "allowFrom": ["*"]
    }
  }
}
```

Run `nanobot auth init` on the gateway host before the first start so the
bind-to-`0.0.0.0` validator finds `auth/verifier.json`. Clients POST the
instance password to `/auth/login`, then exchange the resulting session
cookie for a WebSocket token via `/webui/bootstrap`.

### Custom path

```json
{
  "channels": {
    "websocket": {
      "path": "/chat/ws",
      "allowFrom": ["*"]
    }
  }
}
```

Clients connect to `ws://127.0.0.1:8765/chat/ws?client_id=...`. Trailing slashes are normalized, so `/chat/ws/` works the same.
