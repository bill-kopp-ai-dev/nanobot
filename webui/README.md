# nanobot WebUI Source

This directory contains the React/TypeScript source for the nanobot WebUI. If
you installed `nanobot-ai` from PyPI and only want to use the bundled browser UI,
read the user guide in [`docs/webui.md`](../docs/webui.md). You do not need
Node.js, Bun, Vite, or anything in this directory unless you are changing the
frontend.

For the project overview, install guide, and general docs map, see the root [`README.md`](../README.md) and [`docs/README.md`](../docs/README.md).

## Pick a Path

| Goal | Start with | Opens at |
|---|---|---|
| Use the bundled browser UI | [`docs/webui.md`](../docs/webui.md) | `http://127.0.0.1:8765` |
| Use the WebUI from another device | [`docs/webui.md#lan-access`](../docs/webui.md#lan-access) | `http://<your-ip>:8765` |
| Change WebUI source code | [Develop the WebUI (Vite HMR)](#develop-the-webui-vite-hmr) | `http://127.0.0.1:5173` |
| Debug setup failures | [`docs/troubleshooting.md#webui-problems`](../docs/troubleshooting.md#webui-problems) | Diagnosis order and common fixes |

The source app is built with Vite + React 18 + TypeScript + Tailwind 3 +
shadcn/ui. It talks to the gateway over the WebSocket multiplex protocol and
reads session metadata from the embedded REST surface on the same port.

## Layout

```text
webui/                 source tree (this directory)
nanobot/web/dist/      build output served by the gateway
```

## Develop the WebUI (Vite HMR)

### 1. Install nanobot from source

From the repository root:

```bash
python -m pip install -e .
```

> Editable installs intentionally **skip** the WebUI bundle step — Vite HMR is faster than rebuilding `dist/` on every change.

### 2. Enable the WebSocket channel

In `~/.nanobot/config.json`, merge:

```json
{ "channels": { "websocket": { "enabled": true } } }
```

### 3. Start the gateway

In one terminal:

```bash
nanobot gateway
```

### 4. Start the WebUI dev server

In another terminal:

```bash
cd webui
bun install            # npm install also works
bun run dev
```

Then open `http://127.0.0.1:5173`.

By default the dev server proxies `/api`, `/webui`, `/auth`, and WebSocket traffic to `http://127.0.0.1:8765`.

If your gateway listens on a non-default port, point the dev server at it:

```bash
NANOBOT_API_URL=http://127.0.0.1:9000 bun run dev
```

### 4a. (Optional) Open the Knowledge Graph SPA alongside the WebUI

The sidebar shows a "Knowledge Graph" button that opens the
`mcp_servers/spa/` SPA. In dev local they run on different origins
(WebUI on `:5173`, SPA on `:5174` — see
`agent-docker/mcp_servers/spa/vite.config.ts`), so the WebUI needs to know
the SPA's absolute URL. The shipped `.env.development` sets
`VITE_KG_INTERFACE_URL=http://localhost:5174/`, so a vanilla
`bun run dev` already works — no action needed unless you change the
SPA's port. If you do, override:

```bash
VITE_KG_INTERFACE_URL=http://localhost:5180/ bun run dev
```

The helper (`src/lib/kg-interface.ts`) also has a runtime fallback:
if the WebUI itself is served from `:5173` (the Vite dev server), it
auto-detects the SPA on `:5174` without requiring the env var. This
makes the button work even when the user only runs `bun run dev`
without an `.env` file. **Caveat:** this fallback only fires on
`:5173` — if you access the gateway/prod build (`:8765`), the helper
falls back to the relative `/kg-interface/` (P10 default) and won't
find the SPA on a different origin. For that scenario, rebuild the
WebUI bundle with the SPA URL baked in:

```bash
bun run build:dev-kg
```

This embeds `VITE_KG_INTERFACE_URL=http://localhost:5174/` into the
bundle served by the gateway, so the button works regardless of how
you reach the WebUI (dev server OR gateway).

In production (P10) the SPA is served by Caddy on the same origin as
the WebUI under `/kg-interface/`, so the helper defaults to that
relative path and no env var is needed.

## Build for packaged runtime

You usually do not need to run this by hand: `python -m build` invokes the WebUI build automatically when packaging the wheel.

If you want to preview the production bundle locally without rebuilding the wheel:

```bash
cd webui
bun run build          # writes to ../nanobot/web/dist
```

The gateway picks up the new bundle on the next restart.

## Test

```bash
cd webui
bun run test
```

## Acknowledgements

- [`agent-chat-ui`](https://github.com/langchain-ai/agent-chat-ui) for UI and interaction inspiration across the chat surface.
