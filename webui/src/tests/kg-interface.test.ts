// PERCIVAL: testes do helper de URL da SPA do Knowledge Graph (P8 etapa 1).
import { afterEach, describe, expect, it, vi } from "vitest";
import { DEFAULT_KG_INTERFACE_URL, resolveKgInterfaceUrl } from "@/lib/kg-interface";

describe("resolveKgInterfaceUrl", () => {
  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it("retorna o default /kg-interface/ quando VITE_KG_INTERFACE_URL não está setada", () => {
    expect(resolveKgInterfaceUrl()).toBe(DEFAULT_KG_INTERFACE_URL);
  });

  it("retorna o valor de VITE_KG_INTERFACE_URL quando definido", () => {
    vi.stubEnv("VITE_KG_INTERFACE_URL", "http://localhost:5173");
    expect(resolveKgInterfaceUrl()).toBe("http://localhost:5173");
  });

  it("retorna string vazia como qualquer outro valor falsy (sem normalização)", () => {
    vi.stubEnv("VITE_KG_INTERFACE_URL", "");
    // Decisão B1: NÃO fazer fallback quando setado para string vazia — fica como "".
    // Se quisermos fallback, isso é mudança de decisão, não bug.
    expect(resolveKgInterfaceUrl()).toBe("");
  });

  it("DEFAULT_KG_INTERFACE_URL é exatamente /kg-interface/", () => {
    expect(DEFAULT_KG_INTERFACE_URL).toBe("/kg-interface/");
  });
});
