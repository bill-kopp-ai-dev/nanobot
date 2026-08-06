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
//   2. **Runtime detection**: se a webui está sendo servida por um dev server
//      local — ou diretamente pela Vite (porta 5173 —
//      `webui/vite.config.ts:server.port`) OU pelo gateway nanobot local
//      (porta 8765, que serve o bundle estático da webui em dev/prod) —,
//      assume-se que o usuário também subiu a SPA kg-interface em outra
//      porta (`5174` — `spa/vite.config.ts:server.port`). Aponta direto
//      para ela sem exigir env var.
//
//      Por que tratar 8765 também? Em dev local o caminho natural é abrir
//      o gateway (`http://127.0.0.1:8765`) — não o Vite da webui em
//      5173 (o `dev-spa.sh` sobe apenas a SPA + adapters, e a webui é
//      servida pelo bundle estático que o gateway entrega). Sem isso,
//      o `window.location.port === 8765` caía no caminho (3) e o botão
//      abria `http://127.0.0.1:8765/kg-interface/`, que é 404 no dev
//      local porque o gateway não sabe servir `/kg-interface/` (esse
//      path só existe atrás do Caddy/Cloudflare em P10).
//
//   3. **Default relativo** `/kg-interface/`. Funciona em produção/P10
//      porque o Caddy serve a SPA estática e os adapters CM/AK sob esse
//      path no mesmo origin da webui (`/kg-interface/*` → SPA,
//      `/kg-interface/api/*` → CM/AK).
//
// `as const` mantém o literal "/kg-interface/" como tipo imutável e estreito.
export const DEFAULT_KG_INTERFACE_URL = "/kg-interface/" as const;

// PERCIVAL: portas dos dev servers da webui (vite.config.ts direto + gateway
// nanobot local) e da SPA kg-interface (spa/vite.config.ts). Mantenha
// alinhado com os `server.port` dos respectivos vite.config.ts e com o
// `nanobot/channels/websocket/runtime.py:port` (default 8765).
const WEBUI_DEV_PORTS = new Set(["5173", "8765"]);
const SPA_DEV_PORT = "5174";

// PERCIVAL: hosts locais que justificam o "atalho" pra SPA dev em 5174.
// Em produção o Caddy serve o caminho /kg-interface/ no MESMO origin da
// webui, então apontar pra outra porta quebraria o cookie de auth, etc.
// Restringir a hosts locais evita essa regressão em deploys reais.
const LOCAL_HOSTNAMES = new Set(["localhost", "127.0.0.1"]);

export function resolveKgInterfaceUrl(): string {
  // 1) Build-time env var (substituída em build pela Vite).
  const envUrl = import.meta.env.VITE_KG_INTERFACE_URL;
  if (envUrl) return envUrl;
  // 2) Runtime detection: webui servida por dev server local (Vite ou
  //    gateway nanobot) → aponta pra SPA dev no mesmo host.
  if (typeof window !== "undefined") {
    const { hostname, port } = window.location;
    if (LOCAL_HOSTNAMES.has(hostname) && WEBUI_DEV_PORTS.has(port)) {
      return `http://localhost:${SPA_DEV_PORT}/`;
    }
  }
  // 3) Default relativo (produção / VPS / P10).
  return DEFAULT_KG_INTERFACE_URL;
}