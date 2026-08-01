// PERCIVAL: helper para resolver a URL da SPA do Knowledge Graph (P8, decisão B1).
// Variável de ambiente VITE_KG_INTERFACE_URL com default /kg-interface/.
// Em produção (P10) o path /kg-interface/ é servido pela SPA estática;
// em dev local a webui roda com VITE_KG_INTERFACE_URL=http://localhost:5173.
export const DEFAULT_KG_INTERFACE_URL: string = "/kg-interface/";

export function resolveKgInterfaceUrl(): string {
  return import.meta.env.VITE_KG_INTERFACE_URL ?? DEFAULT_KG_INTERFACE_URL;
}
