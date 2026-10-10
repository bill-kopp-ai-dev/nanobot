# F7 — procedência e identidade dos commits (P1)

- **Data:** 2026-10-10 UTC.
- **Escopo:** pacote P1 do [plano de fechamento F7](../plans/2026-10-10-f7-operations-acceptance-closure-plan.md), pendência #10 do plano principal.
- **Método:** varredura read-only dos oito repos; comparação entre autor, committer e configuração Git local; mapeamento para identidades conhecidas. Nenhuma mutação em `main`, nenhum push, nenhuma alteração de configuração Git, nenhum `.mailmap` aplicado.
- **Atenção:** este relatório não credita autoria por inferência. Identidades com nome/exemplo/domínio do agente são sinalizadas como automação local; só após decisão do operador e evidência de que a mesma pessoa é responsável é que se pode aplicar `.mailmap` ou reescrever commits.

## 1. Estado atual por repositório

Configuração Git local observada em 2026-10-10 (todos os oito repos estão com `main` como branch corrente; nenhum `git config` global ativo):

| Repositório | `user.name` | `user.email` | `.mailmap` |
| --- | --- | --- | --- |
| `nanobot` (gateway) | bill | bill-kopp-ai-dev@users.noreply.github.com | ausente |
| `percival-notes-mcp` | bill | bill@percival.local | ausente |
| `percival-agentmail-mcp` | Bill | bill@example.com | ausente |
| `percival-deep-research` | Bill | bill@example.com | ausente |
| `percival-khan-calendar` | bill | bill@percival.local | ausente |
| `percival-osm` | bill-kopp-ai-dev | bill-kopp-ai-dev@users.noreply.github.com | ausente |
| `percival-weather-mcp` | Positronic Agent | agent@positronic.local | ausente |
| `alternative-positronic` | (vazio) | (vazio) | ausente |

Janela F0–F7 (commits a partir de 2026-09-30 até o snapshot atual). Todos os oito repos aceitaram commits sob identidades que precisam ser explicadas:

| Repo | Identidades observadas (autor/committer) | Comentário |
| --- | --- | --- |
| `nanobot` | `Bill Kopp <bill.kopp.dev@gmail.com>`, `bill <bill-kopp-ai-dev@users.noreply.github.com>`, `Positronic <positronic@percival.local>`, `Positronic <positronic@percival.os>`, `Percival <percival@local>`, `Positronic <positronic@local>` (mais upstream `Xubin Ren`, `chengyongru`, `GitHub`, etc.) | Recente F4-F7 alterna entre Bill Kopp e o agente Positronic; commits anteriores do upstream predominam. |
| `percival-notes-mcp` | `bill <bill@percival.local>`, `bill-kopp-ai-dev <bill-kopp-ai-dev@users.noreply.github.com>`, `bill-kopp <bill.kopp.dev@gmail.com>`, `bill-Kopp <whats.up.ai.chat@gmail.com>`, `Positronic <positronic@percival.local>` | Cinco identidades relacionadas a Bill; sem `mailmap`. |
| `percival-agentmail-mcp` | `Bill <bill@example.com>`, `bill-kopp-ai-dev <bill-kopp-ai-dev@users.noreply.github.com>`, `bill-kopp <bill.kopp.dev@gmail.com>`, `Positronic <positronic@percival.local>` | `bill@example.com` é placeholder evidente; agente assinou um commit OCI. |
| `percival-deep-research` | `Bill <bill@example.com>`, `bill-kopp <bill.kopp.dev@gmail.com>`, `Positronic <positronic@percival.local>`, `Positronic <positronic@percival.os>` | Mesmo placeholder; agente (`@percival.os` e `@percival.local`) domina a janela F1–F3. |
| `percival-khan-calendar` | `Bill <bill@example.com>`, `bill <bill@percival.local>`, `bill-kopp-ai-dev <…noreply.github.com>`, `bill-kopp <bill.kopp.dev@gmail.com>`, `Positronic <positronic@percival.local>` | Recente volta para `bill@percival.local`. |
| `percival-osm` | `Bill <bill@example.com>`, `bill-kopp-ai-dev <…noreply.github.com>`, `bill-kopp <bill.kopp.dev@gmail.com>`, `bill-Kopp <whats.up.ai.chat@gmail.com>`, `Daniel Nowak <…noreply.github.com>`, `Positronic <positronic@percival.local>`, `Positronic <positronic@percival.os>` | Placeholder e três variantes "Bill"; o commit `Daniel Nowak` é contribuição externa preservada. |
| `percival-weather-mcp` | `Bill <bill@example.com>`, `bill-kopp-ai-dev <…noreply.github.com>`, `bill-kopp-ai-dev <bill.kopp.dev@gmail.com>`, `bill-kopp <bill.kopp.dev@gmail.com>`, `bill-Kopp <whats.up.ai.chat@gmail.com>`, `Positronic Agent <agent@positronic.local>`, `Positronic <positronic@percival.local>` | Cinco rótulos "Bill" diferentes; o agente domina os commits F0–F7. |
| `alternative-positronic` | `Bill Kopp <bill.kopp.dev@gmail.com>` (todo o intervalo), com alguns commits pontuais `bill <bill@local>`, `positronic-bot <positronic@local>`, `positronic-f1-bot <bot@positronic.local>`, `positronic <local@positronic>`, `Trae <trae@anthropic.com>` | Identidade canônica é `Bill Kopp`/`bill.kopp.dev@gmail.com`; bots e aliases aparecem no histórico. |

## 2. Análise das identidades "agente"

Os endereços `Positronic <positronic@percival.local>`, `Positronic <positronic@percival.os>`, `Positronic <positronic@local>`, `Percival <percival@local>`, `Positronic Agent <agent@positronic.local>`, `positronic-bot <positronic@local>`, `positronic-f1-bot <bot@positronic.local>` e `Trae <trae@anthropic.com>` **não são identidades do operador**. São identidades locais usadas por agentes automatizados em sessões que não estavam configuradas com o `user.name`/`user.email` do operador. Elas não devem ser silenciosamente reatribuídas a `Bill Kopp`; sem o `mailmap` ou reescrita aprovada, **continuam aparecendo como autor/committer oficial do objeto commit** e qualquer clone ou CI remoto as preserva.

A família `Bill <bill@example.com>` é placeholder genérico: aparece em todos os MCPs exceto `percival-osm`/`percival-weather-mcp` (que usam variantes levemente diferentes) e corresponde a um estado em que a sessão não estava com `user.name`/`user.email` ajustados. Nenhum dos commits do agente está assinado por GPG/SSH, e `git log --pretty='%G?'` retorna `N` (no signature) em todos os repos relevantes, com `U` e `E` aparecendo apenas em commits históricos do `nanobot` (upstream `Xubin Ren`/`GitHub`). Sem assinaturas, não há como afirmar criptograficamente que duas identidades pertencem à mesma pessoa; a decisão é documental.

## 3. Imagens promovidas x commits correspondentes

O canário F7 pinou seis imagens em ambos os gestores. As revisões registradas nas OCI labels comparam com o HEAD de cada repo:

| Serviço | Image ID ativo | OCI revision | HEAD no `main` | Observação |
| --- | --- | --- | --- | --- |
| AgentMail | `sha256:e104ac754951…` | `d2d6458-f7-keyfile-4ff291ec7a33` | `3697188` (HEAD atual do repo) | Imagem foi construída a partir de `d2d6458` (F3); HEAD `3697188` é o commit de hardening posterior. O pin atual **não reproduz** o HEAD atual sem rebuild. |
| Notes | `sha256:ef4082ef1390…` | `ab0f07d-f7-vaultpath-0012523b9a96` | `03c7305` | Imagem baseada em `ab0f07d`; HEAD `03c7305` ainda é o commit de `PERCIVAL_NOTES_VAULT_PATH`. Pin bate com HEAD atual. |
| Khan | `sha256:55cd5a038d22…` | `d8d4122` (mais `source-diff-sha256`) | `868b6a5` | HEAD posterior ao SHA embutido; pin atual não reproduz HEAD. |
| OSM | `sha256:67f8ada63989…` | `311a49d` (mais `source-diff-sha256`) | `d9e34b3` | HEAD posterior; pin atual não reproduz HEAD. |
| Weather | `sha256:e75fdd4abc8a…` | `94c7fde` (mais `source-diff-sha256`) | `1b1cd6c` | HEAD posterior; pin atual não reproduz HEAD. |
| Deep Research | `sha256:265891c14514…` | `9e8272b` (mais `source-diff-sha256`) | `b92bd90` | HEAD posterior; pin atual não reproduz HEAD. |

Implicação: dos seis pinados, apenas Notes bate com o HEAD atual. Para os outros cinco, uma rebuild a partir do HEAD atual produziria image ID diferente do pin em runtime. O [relatório F4/F5](../reports/2026-10-10-f4-f5-closure-report.md) já havia sinalizado esse descolamento para Notes e AgentMail; o canário F7 não fechou essa pendência, apenas a documentou.

## 4. Recomendações para fechamento da pendência #10

1. **Decidir a representação canônica antes de qualquer publicação.** Sem `mailmap`, a publicação do repositório público do Percival congelaria o estado atual. Manter duas/ três identidades em commits já enviados é inevitável; a escolha é: (a) documentar a proveniência sem reescrever, (b) aplicar `.mailmap` apenas nas apresentações, deixando os objetos intactos, (c) reescrever os commits recentes (impacta clones, CI, pins e OpenVEX). O caminho (a)+(b) é o menos invasivo; (c) requer decisão específica.
2. **Identificar quem operou cada sessão.** Identidades de agente (domínio `percival.local`, `percival.os`, `positronic.local`, `positronic@local`, `positronic-bot`, `positronic-f1-bot`, `Trae`) representam o agente local; não devem ser creditadas ao operador. A `Bill <bill@example.com>` precisa ser explicada: é o operador, configuração não ajustada, ou automação com placeholder? Sem essa resposta, `mailmap` é prematuro.
3. **Conciliar imagem × HEAD.** A promoção de um pin de runtime só deve acontecer depois que o SHA da imagem coincidir com o HEAD do `main` (ou uma tag assinada, quando aplicável). Hoje, o canário usa candidatos F3 com diff hash; o fechamento F4 e F5 depende dessa reconciliação.
4. **Preparar `.mailmap` por repo quando a equivalência estiver confirmada.** Mesmo sem reescrita, apresentar logs coerentes para revisão ajuda B13. O arquivo é puramente visual; pode ser criado fora da janela de release e revisado antes de virar canônico.
5. **Sinalizar a falta de assinaturas.** Nenhum commit do intervalo F0–F7 é assinado por GPG/SSH, o que enfraquece a proveniência mesmo após qualquer `mailmap`. A decisão de assinar e com qual chave é independente deste relatório.

## 5. Ações executadas e limites desta sessão

- Coleta read-only de `git log` em oito repos com `user.name`/`user.email` locais, com janela 2026-09-30 → hoje e agregação por par (autor, committer).
- Inspeção read-only de `docker inspect` para seis imagens promovidas (apenas OCI labels; sem env, sem `docker inspect` integral).
- Sem aplicação de `.mailmap`. Sem `git config` alterado. Sem `git commit --amend` ou `git rebase`. Sem push. Sem tag.
- O mapeamento de identidades por pessoa física **não foi concluído** por falta de informação do operador sobre quem operou cada sessão, especialmente para as contas `Bill <bill@example.com>` e variantes.

## 6. Próximo passo sugerido

Confirmar formalmente, com o operador: (a) quais identidades "Bill" representam o operador; (b) se as identidades de agente devem permanecer no histórico ou se é aceitável reescrevê-las antes de qualquer publicação; (c) se a rebuild + promoção dos cinco pins deve ser tratada como pré-condição para F4/F5 verdes. Sem essas respostas, `.mailmap` e F4/F5 ficam em modo "documentar sem resolver".
