// PERCIVAL: helper para resolver a URL da SPA do Knowledge Graph (P8, decisão B1).
//
// Resolve a URL em 3 níveis, do mais específico para o mais genérico:
//
//   1. **Build-time env var** `VITE_KG_INTERFACE_URL` (decisão B1). Vite
//      substitui `import.meta.env.VITE_*` em build time pelo valor literal;
//      em runtime a string já está embutida no bundle. Em dev local o
//      `.env.development` define `http://localhost:5174/`; em produção
//      (Caddy/P10) define o origin público ou fica vazia para cair no (3).
//
//   2. **Runtime detection**: se a webui está rodando no dev server da Vite
//      (porta 5173 — `webui/vite.config.ts:server.port`), assume-se que o
//      usuário também subiu a SPA kg-interface em outra porta (`5174` —
//      `spa/vite.config.ts:server.port`). Aponta direto para ela sem exigir
//      env var.
//
//   3. **Default relativo** `/kg-interface/`. Funciona em produção/P10
//      porque o Caddy serve a SPA estática e os adapters CM/AK sob esse
//      path no mesmo origin da webui (`/kg-interface/*` → SPA,
//      `/kg-interface/api/*` → CM/AK).
//
// `as const` mantém o literal "/kg-interface/" como tipo imutável e estreito.
export const DEFAULT_KG_INTERFACE_URL = "/kg-interface/" as const;

// PERCIVAL: portas dos dev servers da webui (vite.config.ts) e da SPA
// kg-interface (spa/vite.config.ts). Mantenha alinhado com os `server.port`
// dos respectivos vite.config.ts.
const WEBUI_DEV_PORT = "5173";
const SPA_DEV_PORT = "5174";

export function resolveKgInterfaceUrl(): string {
  // 1) Build-time env var (substituída em build pela Vite).
  const envUrl = import.meta.env.VITE_KG_INTERFACE_URL;
  if (envUrl) return envUrl;
  // 2) Runtime detection: webui dev → aponta pra SPA dev no mesmo host.
  if (typeof window !== "undefined") {
    const { hostname, port } = window.location;
    if (port === WEBUI_DEV_PORT && (hostname === "localhost" || hostname === "127.0.0.1")) {
      return `http://localhost:${SPA_DEV_PORT}/`;
    }
  }
  // 3) Default relativo (produção / VPS / P10).
  return DEFAULT_KG_INTERFACE_URL;
}