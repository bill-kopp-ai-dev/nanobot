# Brand assets spec — kg-interface SPA

Atualizado em 2026-08-02 — alinhamento visual com a webui percival
(`agent-docker/nanobot/webui/`) da branch `feat/percival-branding`. Os assets são
**bit-by-bit cópias** dos arquivos equivalentes lá (md5sum bate):

```
nanobot/webui/public/brand/nanobot_icon.png       →  spa/public/brand/percival_icon.png
nanobot/webui/public/brand/nanobot_favicon_32.png →  spa/public/brand/percival_favicon_32.png
```

## Decisão

Mantemos os arquivos nomeados como **`percival_*`** (não `nanobot_*`) nesta
SPA — aqui não temos o mesmo trade-off "diff mínimo com upstream" que a
webui tem (porque esta SPA **é** um projeto próprio, não um fork de algo
externo). A webui foi sobrescrita para preservar `nanobot_*` apenas por
causa de merges upstream; aqui, o conteúdo é o logo **percival** mas o
nome é livre.

## Tabela de assets

| # | Arquivo | Tipo | Dimensões | Origem (asset fonte) | Referenciado em |
|---|---|---|---|---|---|
| 1 | `percival_icon.png` | image/png | **192×192** | cópia verbatim de `nanobot_icon.png` (md5sum `0d5476754c1909466ef1f40703aed654`) | `Sidebar.tsx` (logo do header), `index.html` (apple-touch futuro) |
| 2 | `percival_favicon_32.png` | image/png | **32×32** | cópia verbatim de `nanobot_favicon_32.png` (md5sum equivalente) | `index.html:5` (`<link rel="icon">`) |

## Pendências

- **SVG vetorial**: igual à webui (`nanobot_mark.svg`) — pendente até o
  design system da percival produzir um SVG vetorial. A webui também ainda
  aguarda (Etapa 9 do plano P8). Quando entrar, considerar trocar o `src`
  do header de PNG pra SVG e remover o `percival_icon.png` (mantém o
  `percival_favicon_32.png` pelo uso como favicon raster).
- **Outros assets da webui** (`percival_logo.png`, `percival_logo.webp`,
  `percival_apple_touch.png`): não portados porque esta SPA não usa
  (a sidebar não tem `SidebarHeader` com logo+texto separado; o cabeçalho
  é só o logo). Se um dia a SPA precisar de hero/OG image, copiar
  diretamente — sem mudar nome, já que aqui convenção é `percival_*`.

## Convenção de nomes

- Novos assets em `public/brand/` DEVEM usar prefixo `percival_*` (não
  `nanobot_*` nem `kg-interface_*`).
- Componentes DEVEM apontar pra `/brand/percival_<recurso>.<ext>`,
  casando com o que a webui usa (`/brand/nanobot_<recurso>.<ext>` no
  contexto da webui por causa da decisão A2 do upstream, mas aqui a SPA
  não tem essa restrição).
