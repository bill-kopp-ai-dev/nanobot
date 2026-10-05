// PERCIVAL: testes da chave sidebar.positronicBean em todos os locales.
// Mesmo padrão do `i18n-knowledge-graph.test.ts` (P8 etapa 2): cada locale
// deve ter a chave como string não-vazia. Como "Positronic Bean" é nome
// próprio da empresa, mantemos a string idêntica em todos os locales
// (decisão alinhada com a abordagem do nome próprio "percival" no
// rebranding P8 etapa 6).
import { describe, expect, it } from "vitest";

import { resources } from "@/i18n";
import { supportedLocales } from "@/i18n/config";

describe("sidebar.positronicBean i18n", () => {
  it.each(supportedLocales.map((entry) => entry.code))(
    "locale %s tem sidebar.positronicBean definida como string não-vazia",
    (locale) => {
      const common = resources[locale as keyof typeof resources]?.common as
        | { sidebar?: { positronicBean?: unknown } }
        | undefined;
      expect(common).toBeDefined();
      const label = common?.sidebar?.positronicBean;
      expect(label).toBeDefined();
      expect(typeof label).toBe("string");
      expect((label as string).length).toBeGreaterThan(0);
    },
  );

  it("sidebar.positronicBean é 'Positronic Bean' em todos os locales (nome próprio)", () => {
    for (const entry of supportedLocales) {
      const common = resources[entry.code as keyof typeof resources]?.common as
        | { sidebar?: { positronicBean?: string } }
        | undefined;
      expect(common?.sidebar?.positronicBean, `locale ${entry.code}`).toBe(
        "Positronic Bean",
      );
    }
  });
});