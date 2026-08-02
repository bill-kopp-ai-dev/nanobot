// PERCIVAL: testes do helper de URL da SPA do Knowledge Graph (P8 etapa 1).
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { DEFAULT_KG_INTERFACE_URL, resolveKgInterfaceUrl } from "@/lib/kg-interface";

describe("resolveKgInterfaceUrl", () => {
  // happy-dom expõe `window.location` apontando para `http://localhost:3000/`
  // por default — exatamente a porta que o teste do nível 1 (dev) intercepta.
  // Stubamos manualmente em cada teste para isolar o caminho esperado.
  const ORIGINAL_LOCATION = window.location;

  beforeEach(() => {
    // Stub o location.href para uma origem não-dev (8765 do gateway), que
    // NÃO dispara o fallback de runtime detection; assim o teste do default
    // relativo cai no caminho (3) do helper.
    Object.defineProperty(window, "location", {
      value: { hostname: "127.0.0.1", port: "8765" },
      writable: true,
      configurable: true,
    });
  });

  afterEach(() => {
    vi.unstubAllEnvs();
    Object.defineProperty(window, "location", {
      value: ORIGINAL_LOCATION,
      writable: true,
      configurable: true,
    });
  });

  it("retorna o default /kg-interface/ quando VITE_KG_INTERFACE_URL não está setada e não estamos no dev server", () => {
    // Caminho (3): sem env var + origin ≠ dev server (8765 do gateway) →
    // default relativo (produção / VPS / P10).
    expect(resolveKgInterfaceUrl()).toBe(DEFAULT_KG_INTERFACE_URL);
  });

  it("detecta em runtime o dev server da webui (porta 5173) e aponta pra SPA dev (5174)", () => {
    // Caminho (2): sem env var + webui rodando na porta 5173 → aponta pra
    // SPA dev em 5174 sem precisar de env var (resiliente a cache/skip
    // do .env.development).
    Object.defineProperty(window, "location", {
      value: { hostname: "127.0.0.1", port: "5173" },
      writable: true,
      configurable: true,
    });
    expect(resolveKgInterfaceUrl()).toBe("http://localhost:5174/");
  });

  it("detecta em runtime o dev server via hostname localhost também", () => {
    Object.defineProperty(window, "location", {
      value: { hostname: "localhost", port: "5173" },
      writable: true,
      configurable: true,
    });
    expect(resolveKgInterfaceUrl()).toBe("http://localhost:5174/");
  });

  it("NÃO detecta como dev quando a porta não é 5173 (ex: 8765 do gateway)", () => {
    Object.defineProperty(window, "location", {
      value: { hostname: "127.0.0.1", port: "8765" },
      writable: true,
      configurable: true,
    });
    expect(resolveKgInterfaceUrl()).toBe(DEFAULT_KG_INTERFACE_URL);
  });

  it("retorna o valor de VITE_KG_INTERFACE_URL quando definido (prioridade sobre detecção)", () => {
    // Caminho (1): env var tem prioridade absoluta — mesmo se o usuário
    // está no dev server, o valor explícito vence (permite apontar pra
    // uma SPA em outro host/porta).
    Object.defineProperty(window, "location", {
      value: { hostname: "127.0.0.1", port: "5173" },
      writable: true,
      configurable: true,
    });
    vi.stubEnv("VITE_KG_INTERFACE_URL", "https://kg.example.com/");
    expect(resolveKgInterfaceUrl()).toBe("https://kg.example.com/");
  });

  it("retorna o valor de VITE_KG_INTERFACE_URL quando definido", () => {
    vi.stubEnv("VITE_KG_INTERFACE_URL", "http://localhost:5174");
    expect(resolveKgInterfaceUrl()).toBe("http://localhost:5174");
  });

  it("cai no fallback de runtime quando VITE_KG_INTERFACE_URL é string vazia", () => {
    // PERCIVAL: revisão 2026-08-02 — a detecção de runtime (caminho 2 do
    // helper) substitui o antigo comportamento pass-through. Antes,
    // `VITE_KG_INTERFACE_URL=""` retornava `""` (decisão B1); agora cai
    // no próximo fallback porque `""` é falsy. Como o location.stubado
    // aponta pra 8765 (não-dev), cai no default relativo /kg-interface/.
    // Isso é uma melhoria: o botão nunca fica quebrado por env var vazia.
    vi.stubEnv("VITE_KG_INTERFACE_URL", "");
    expect(resolveKgInterfaceUrl()).toBe(DEFAULT_KG_INTERFACE_URL);
  });

  it("não normaliza whitespace (decisão B1: sem coerção)", () => {
    vi.stubEnv("VITE_KG_INTERFACE_URL", "  http://localhost:5174  ");
    // Decisão B1: helper é pass-through; validação/normalização é responsabilidade
    // do chamador (C4: documentar no RUNBOOK como setar a env var).
    expect(resolveKgInterfaceUrl()).toBe("  http://localhost:5174  ");
  });

  it("DEFAULT_KG_INTERFACE_URL é exatamente /kg-interface/", () => {
    expect(DEFAULT_KG_INTERFACE_URL).toBe("/kg-interface/");
  });
});