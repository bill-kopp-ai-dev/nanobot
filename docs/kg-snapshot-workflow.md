# Atualização verificável dos snapshots KG

O hook em [`hatch_build.py`](../hatch_build.py) **valida** o vendor core e a
SPA antes de embalar sdist/wheel. As fontes vizinhas não são consultadas
implicitamente. Nunca alterar `SOURCE.json` apenas para fazer passar um
hash: comparar diffs, licenças, APIs e tests primeiro.

## Core `okf-bundle-core`

O snapshot rastreado em `nanobot/agent/kg/vendor/` inclui
`LICENSE.okf-bundle-core`, `SOURCE.json` (revisão, SHA-256 upstream e vendor,
`patched_files`) e `PATCHES.md`. Compare uma revisão fixa da fonte com o
vendorizado; preserve os patches de `frontmatter.py`/`lock.py` ou resolva-os
explicitamente. Revalide imports, layout, locks e testes KG em plataforma
suportada. `PERCIVAL_KG_CORE_SOURCE=<checkout>` só inicializa snapshot
**ausente**; se já existe, o hook recusa sobrescrevê-lo: faça atualização
revisada na árvore de trabalho e registre novos hashes e diffs.

## SPA

Atualize fonte em commit rastreado do repo SPA, execute `bun run test`,
`bun run lint`, `bun run build`. Capture `git rev-parse HEAD`, estado limpo
e SHA do `bun.lock`. Em checkout/cópia **limpa** do fork, forneça
`PERCIVAL_KG_SPA_SOURCE=<checkout-spa>` e
`PERCIVAL_FORCE_KG_SPA_BUILD=1` durante a construção do sdist; o hook
primeiro verifica o snapshot anterior, substitui somente assets reconhecidos
e grava novo `SOURCE.json` (SHA e flag `dirty`). Se houver files novos não
reconhecidos no snapshot, faça inspeção em vez de removê-los à força. Compare
licença, JS/CSS/index e hashes. Confira que `dirty=false` e a revisão SHA
é a que recebeu os testes; com `dirty=true`, a integridade do snapshot pode
estar provada, mas não a reprodução a partir da revisão declarada.

Construa o wheel **a partir do sdist** em ambiente sem checkout SPA vizinho;
instale num ambiente limpo e verifique hash de todos os assets, licença,
skills, gateway e rota `/kg-interface/`. Consulte
[`docs/releasing.md`](releasing.md) para os gates adicionais do pacote
Python/TUI; nenhum snapshot local é, por si, uma release.
