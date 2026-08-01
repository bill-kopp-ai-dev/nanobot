// PERCIVAL: testes da chave sidebar.knowledgeGraph em todos os locales (P8 etapa 2).
// Decisão B3: chave deve existir como string não-vazia em cada locale suportado.
// Traduções são propostas e devem ser validadas com falantes nativos antes de P10 —
// o teste aqui cobre apenas presença e tipo.
//
// Usa `resources` exportado por `@/i18n` (padrão do projeto, ver `i18n.test.tsx`)
// em vez de `import()` direto do JSON, para evitar acoplar o teste a paths de
// bundler/alias e ganhar type-safety na navegação do namespace.
import { describe, expect, it } from "vitest";

import { resources } from "@/i18n";
import { supportedLocales } from "@/i18n/config";

describe("sidebar.knowledgeGraph i18n", () => {
  it.each(supportedLocales.map((entry) => entry.code))(
    "locale %s tem sidebar.knowledgeGraph definida como string não-vazia",
    (locale) => {
      const common = resources[locale as keyof typeof resources]?.common as
        | { sidebar?: { knowledgeGraph?: unknown } }
        | undefined;
      expect(common).toBeDefined();
      const label = common?.sidebar?.knowledgeGraph;
      expect(label).toBeDefined();
      expect(typeof label).toBe("string");
      expect((label as string).length).toBeGreaterThan(0);
    },
  );
});
