// PERCIVAL: testes da chave sidebar.knowledgeGraph em todos os locales (P8 etapa 2).
// Decisão B3: chave deve existir como string não-vazia em cada um dos 10 locales
// (en + 9 traduções). Traduções são propostas e devem ser validadas com falantes
// nativos antes de P10 — o teste aqui cobre apenas presença e tipo.
import { describe, expect, it } from "vitest";

const LOCALES = [
  "en",
  "es",
  "fr",
  "id",
  "ja",
  "ko",
  "vi",
  "zh-CN",
  "zh-TW",
  "pt-BR",
] as const;

describe("sidebar.knowledgeGraph i18n", () => {
  it.each(LOCALES)(
    "locale %s tem sidebar.knowledgeGraph definida como string não-vazia",
    async (locale) => {
      const data = await import(`@/i18n/locales/${locale}/common.json`);
      const sidebar = data.default.sidebar as Record<string, unknown> | undefined;
      expect(sidebar).toBeDefined();
      expect(sidebar?.knowledgeGraph).toBeDefined();
      expect(typeof sidebar?.knowledgeGraph).toBe("string");
      expect((sidebar?.knowledgeGraph as string).length).toBeGreaterThan(0);
    },
  );
});
