# Brand assets spec — percival webui

Atualizado em 2026-08-01, Etapa 7 do plano P8 (fork mínimo da webui do nanobot).

## Origem dos assets

- **Substituídos** em 2026-08-01 a partir de `webui/public/brand/New_logos/` (5 PNGs/WebP).
- **NÃO substituído**: `nanobot_mark.svg` (sem versão SVG do novo logo; marcado como pendência para Etapa 9 — assets finais).

## Decisão A2 (revisada em 2026-08-01)

Mantemos os **nomes** dos arquivos como `nanobot_*` (não renomeamos para `percival_*`)
para preservar diff mínimo em merges futuros do upstream. O **conteúdo** dos binários
foi substituído pelo logo percival.

## Tabela de assets

| # | Arquivo (caminho no repo) | Tipo | Dimensões (atuais) | Dimensões (originais nanobot) | Mudou? | Referenciado em |
|---|---|---|---|---|---|---|
| 1 | `nanobot_mark.svg` | image/svg+xml | viewBox (SVG, 1358 chars) | viewBox original | NÃO | `Sidebar.tsx:117`, `index.html:14` |
| 2 | `nanobot_favicon_32.png` | image/png | **32×32** | 32×32 | NÃO | `index.html:15` |
| 3 | `nanobot_apple_touch.png` | image/png | **180×180** | 180×180 | NÃO | `index.html:16` |
| 4 | `nanobot_icon.png` | image/png | **192×192** | 73×75 | SIM (era 73×75) | `Sidebar.tsx:117` (mark da sidebar, desde 2026-08-02) |
| 5 | `nanobot_logo.png` | image/png | **2426×386** | 400×75 | SIM (era 400×75) | (não referenciado — órfão) |
| 6 | `nanobot_logo.webp` | image/webp | **2425×385** | 399×74 | SIM (era 399×74) | (não referenciado — órfão) |

## Pendência: `nanobot_mark.svg`

**Status:** SEM versão SVG do logo percival.

**Impacto:** apenas o favicon em aba do navegador e o mark na Sidebar (ambos servidos
pelo SVG) ainda mostram o "n" antigo do nanobot — o apple-touch-icon já usa o PNG novo
(ver mitigação abaixo).

**Mitigação até Etapa 9:**
- O apple-touch-icon (180×180 PNG) já foi substituído — quando o app é instalado,
  usa o PNG, não o SVG.
- O favicon em aba do navegador ainda mostra o "n" nanobot até a Etapa 9.

**Próximo passo:** na Etapa 9 (assets finais), gerar `percival_mark.svg` ou
converter o PNG `percival_icon.png` (192×192) para SVG.

## Decisão sobre divergência de dimensões (4, 5, 6)

A decisão A2 original do plano dizia "manter dimensões, formato, viewBox, paleta".
Em 2026-08-01 o usuário optou (opção B) por **manter as dimensões novas** porque:

- `nanobot_icon.png`, `nanobot_logo.png`, `nanobot_logo.webp` **não são referenciados** em código.
- Os assets novos vêm em alta resolução (192×192, 2426×386, 2425×385) e isso é benéfico
  para uso futuro em displays Retina/4K.
- Dimensões pequenas forçadas (73×75, 400×75) perderiam qualidade.

**Trade-off:** se algum CSS externo faz `width: 73px; height: 75px` em `nanobot_icon.png`,
vai ver o asset em sua resolução nativa (192×192) em vez do tamanho forçado.
Não há, no momento da Etapa 7, nenhum CSS que faça isso.
