// PERCIVAL: testes de regressão do rebranding textual (P8 etapa 6, decisão A1).
// Verifica que os 10 locales foram atualizados, com as exceções documentadas
// (chave nanobotFeatures, comandos de CLI `nanobot gateway`, localStorage keys,
// paths de assets que mantém nome nanobot_*).
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

import { resources } from "@/i18n";
import { supportedLocales } from "@/i18n/config";

const LOCALES = supportedLocales.map((entry) => entry.code);
const ROOT = resolve(__dirname, "..", "..");

function readText(rel: string): string {
  return readFileSync(resolve(ROOT, rel), "utf8");
}

describe("rebranding textual — i18n locales", () => {
  it.each(LOCALES)(
    "locale %s: comando CLI 'nanobot gateway' preservado em app.error.gatewayHint",
    (locale) => {
      const data = resources[locale as keyof typeof resources]?.common as
        | { app?: { error?: { gatewayHint?: string } } }
        | undefined;
      const hint = data?.app?.error?.gatewayHint;
      expect(hint).toBeDefined();
      expect(hint).toContain("nanobot gateway");
    },
  );

  it.each(LOCALES)(
    "locale %s: chave settings.nanobotFeatures preservada (identificador interno)",
    (locale) => {
      const data = resources[locale as keyof typeof resources]?.common as
        | { settings?: { nanobotFeatures?: unknown } }
        | undefined;
      expect(data?.settings?.nanobotFeatures).toBeDefined();
    },
  );

  it.each(LOCALES)(
    "locale %s: não contém 'nanobot' (case-insensitive) em valores visíveis (fora das exceções)",
    (locale) => {
      // PERCIVAL: achado de revisão — a versão anterior deste teste usava
      // `.includes("nanobot")` (case-sensitive, minúsculo), que não pega ocorrências
      // capitalizadas em início de frase (ex: "Nanobot reads these values...").
      // Isso deixou passar 20 strings com "Nanobot" (maiúsculo) não rebrandizadas em
      // 9 dos 10 locales (settings.byok.description, settings.oauth.localCodeHelp,
      // settings.oauth.localCallbackHelp, errors.workspaceScopeRejected.body).
      // Regex /nanobot/i pega os dois casos.
      const NANOBOT_RE = /nanobot/i;
      const data = resources[locale as keyof typeof resources]?.common;
      const whitelist: string[] = [];
      const hint = (data as { app?: { error?: { gatewayHint?: string } } } | undefined)
        ?.app?.error?.gatewayHint;
      if (typeof hint === "string" && NANOBOT_RE.test(hint)) whitelist.push(hint);
      const route = (
        data as { filePreview?: { routeMissing?: string } } | undefined
      )?.filePreview?.routeMissing;
      if (typeof route === "string" && NANOBOT_RE.test(route)) whitelist.push(route);

      const collected: string[] = [];
      const walk = (value: unknown): void => {
        if (typeof value === "string") {
          if (NANOBOT_RE.test(value) && !whitelist.includes(value)) collected.push(value);
        } else if (value && typeof value === "object") {
          for (const v of Object.values(value)) walk(v);
        }
      };
      walk(data);
      expect(collected).toEqual([]);
    },
  );
});

describe("rebranding textual — index.html", () => {
  const html = readText("index.html");

  it("título é 'percival'", () => {
    expect(html).toMatch(/<title>percival<\/title>/);
  });

  it("meta description (fallback en) é 'percival web UI'", () => {
    expect(html).toContain('content="percival web UI');
  });

  it("loading splash (boot copy hardcoded) é 'Loading percival'", () => {
    expect(html).toContain("Loading percival");
  });

  it("localStorage keys preservadas (decisão §6 do plano)", () => {
    expect(html).toContain('"nanobot-webui.theme"');
    expect(html).toContain('"nanobot.locale"');
  });

  it("paths de assets em public/brand mantêm nomes nanobot_* (Etapa 7)", () => {
    expect(html).toContain("/brand/nanobot_mark.svg");
    expect(html).toContain("/brand/nanobot_favicon_32.png");
    expect(html).toContain("/brand/nanobot_apple_touch.png");
  });

  it.each(LOCALES)(
    "fallback JS '%s' (boot e description) contém 'percival'",
    (locale) => {
      // Valida o bloco do locale no objeto `copy` do IIFE em index.html.
      // A chave aceita tanto aspas (ex: "zh-CN":) quanto identificador (ex: en:).
      // Usa [\s\S]*? com lookahead para capturar o menor bloco até o próximo
      // locale ou final do objeto.
      const escapedLocale = JSON.stringify(locale);
      // Primeira tentativa: chave-quoted (ex: "zh-CN": ou "id":).
      const quoted = new RegExp(
        `${escapedLocale}:\\s*\\{[\\s\\S]*?\\}`,
        "u",
      );
      // Segunda: identificador (ex: en: ou fr:).
      const ident = new RegExp(
        `(^|[\\s,{])${locale}:\\s*\\{[\\s\\S]*?\\}`,
        "u",
      );
      const found = quoted.exec(html) ?? ident.exec(html);
      expect(found, `bloco do locale ${locale} em index.html`).not.toBeNull();
      const block = found?.[0] ?? "";
      // Garante que nenhum dos campos tem 'nanobot' (substituído por 'percival').
      // PERCIVAL: case-insensitive — ver achado de revisão acima sobre "Nanobot"
      // capitalizado escapando de checagens case-sensitive.
      expect(block).not.toMatch(/nanobot/i);
      // Sanity check: ao menos um dos campos deve ter 'percival'.
      expect(block).toMatch(/percival/i);
    },
  );
});

describe("rebranding textual — walker recursivo (sanity check)", () => {
  // Garante que o rebranding não apagou conteúdo: cada locale deve ter
  // ocorrências de 'percival' (case-insensitive) em valores visíveis.
  // Se uma das substituições tivesse errado o alvo (sed mal-escapado), o
  // walker detectaria.
  it.each(LOCALES)("locale %s tem 'percival' em algum valor visível", (locale) => {
    const data = resources[locale as keyof typeof resources]?.common;
    expect(data).toBeDefined();
    const found: string[] = [];
    const walk = (value: unknown): void => {
      if (typeof value === "string") {
        if (/percival/i.test(value)) found.push(value);
      } else if (value && typeof value === "object") {
        for (const v of Object.values(value)) walk(v);
      }
    };
    walk(data);
    expect(found.length, `locale ${locale} deve ter 'percival' em algum texto`).toBeGreaterThan(0);
  });
});

describe("rebranding textual — assets em public/brand", () => {
  // Decisão A2: nomes dos arquivos permanecem nanobot_*.
  // Etapa 7 substitui o CONTEÚDO dos binários.
  it.each([
    "nanobot_mark.svg",
    "nanobot_favicon_32.png",
    "nanobot_apple_touch.png",
    "nanobot_icon.png",
    "nanobot_logo.png",
    "nanobot_logo.webp",
  ])("asset %s existe em public/brand/", (filename) => {
    const path = resolve(ROOT, "public", "brand", filename);
    // readFileSync throws se não existir.
    expect(() => readFileSync(path)).not.toThrow();
  });
});
