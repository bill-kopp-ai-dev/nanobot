// PERCIVAL: testes do helper de URL do site da empresa Positronic Bean
// (https://labs.positronicbean.com — em construção, dec 2026). Mesmo padrão
// do `kg-interface.test.ts` (decisão B1): build-time env var com default.
import { afterEach, describe, expect, it, vi } from "vitest";
import {
  DEFAULT_POSITRONIC_BEAN_URL,
  resolvePositronicBeanUrl,
} from "@/lib/positronic-bean";

describe("resolvePositronicBeanUrl", () => {
  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it("retorna o default https://labs.positronicbean.com quando VITE_POSITRONIC_BEAN_URL não está setada", () => {
    expect(resolvePositronicBeanUrl()).toBe(DEFAULT_POSITRONIC_BEAN_URL);
    expect(DEFAULT_POSITRONIC_BEAN_URL).toBe("https://labs.positronicbean.com");
  });

  it("retorna o valor de VITE_POSITRONIC_BEAN_URL quando definido", () => {
    vi.stubEnv(
      "VITE_POSITRONIC_BEAN_URL",
      "https://staging.positronicbean.com/",
    );
    expect(resolvePositronicBeanUrl()).toBe(
      "https://staging.positronicbean.com/",
    );
  });

  it("não normaliza whitespace (decisão B1: sem coerção)", () => {
    vi.stubEnv(
      "VITE_POSITRONIC_BEAN_URL",
      "  https://labs.positronicbean.com  ",
    );
    // Decisão B1: helper é pass-through; validação/normalização é
    // responsabilidade do chamador.
    expect(resolvePositronicBeanUrl()).toBe(
      "  https://labs.positronicbean.com  ",
    );
  });
});