// PERCIVAL: helper para resolver a URL do site da empresa Positronic Bean
// (https://labs.positronicbean.com — em construção, dec 2026). Mesmo padrão
// do `kg-interface.ts`: build-time env var (`VITE_POSITRONIC_BEAN_URL`)
// com default absoluto. Como é um site público fixo (sem path relativo
// porque não roda no mesmo origin da webui), o default aqui é absoluto,
// diferente do KG que defaulta a `/kg-interface/` (P10) pro caso de mesma
// origem.
export const DEFAULT_POSITRONIC_BEAN_URL = "https://labs.positronicbean.com" as const;

export function resolvePositronicBeanUrl(): string {
  return import.meta.env.VITE_POSITRONIC_BEAN_URL ?? DEFAULT_POSITRONIC_BEAN_URL;
}