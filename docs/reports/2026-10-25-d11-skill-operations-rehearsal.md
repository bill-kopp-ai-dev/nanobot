# D11 — rehearsal da skill de operações MCP Docker

- **Data:** 2026-10-25 UTC.
- **Resultado:** D11 permanece **parcial**. O harness descartável completou 24 checks e registrou 1 blocker, usando a própria imagem candidata após o deploy local.
- **Fonte:** Percival `main` em `40d8eb99e5efba5b1d1dd600e63bd7c283d61295`, worktree com alterações D11.
- **Runner:** [`scripts/d11/skill_rehearsal.py`](../../scripts/d11/skill_rehearsal.py), com o adaptador [`d9_rehearsal.py`](../../scripts/d11/d9_rehearsal.py).
- **Resultado redigido:** [`2026-10-25-d11-skill-operations-rehearsal.json`](2026-10-25-d11-skill-operations-rehearsal.json), `completed: true`; 24 `passed`, 1 `blocked`.
- **Skill no checkout:** SHA-256 `81373efc83c7ec8a043dc38990254653137d85cb36351356c8061d347d1a8bdd`.
- **Engine:** Docker-in-Docker rootful 27.5.1. Imagens de core copiadas por `docker save/load`; seus IDs no daemon interno: gateway `sha256:a4c64a7b253a10d9fd1360282a8d02eb1681a62cb93a8a829340f1c5f95e2c48`, broker `sha256:b0f7801379341f8f2265d63f11c993e1575392267b84aa9b64639adef60473d2`. O ID da imagem gateway no daemon do host é `sha256:d128e0ca1dee1d60eaeed46a9d2fe4cfbc42c5fc42700cd723c602200e9a37aa`; no DinD, `docker save/load` expõe o config ID da plataforma `linux/amd64`. As imagens MCP da fixture foram identificadas pelos IDs registrados no JSON.

## Evidência

- O loader encontrou exatamente uma skill `mcp-docker-operations`, como `builtin`, disponível e enabled. A montagem era somente leitura e correspondia ao hash da skill do checkout. O runbook central ficou legível no contexto descartável em `/app/docs/operations/mcp-docker-local-runbook.md`.
- O dry-run determinístico leu owner `Percival manager fixture`, servidor `i2fixture`, transporte stdio, IDs A/B por `sha256`, revisão global/servidor, ausência de transição pendente e estado `running/connected`. O arquivo de configuração, audit e contagem de backups permaneceram inalterados. CAS obsoleto retornou conflito e campo fora da allowlist foi recusado; o broker foi substituído por um guard que falha se receber chamada, provando rejeição antes do transporte.
- A transição A→B e o rollback B→A usaram o manager e CAS; a repetição final usou como gateway a imagem candidata recém-deployada; o runner também montou a cópia da skill do checkout em read-only, enquanto a presença/hash no bundle foram verificados separadamente no image ID e no gateway ativo; `initialize`, `tools/list` e `ping` sintético passaram para B e A. O MCP stdio com probe HTTP falsa ficou `unhealthy`, mas a chamada MCP passou. O caminho atual de exclude/backup/restore validou checksum/identidade/confirmação, voltou ao image ID A e restabeleceu `ping`; read-model e observação do broker convergiram em `running/connected`.
- Os outros checks D9 da base passaram. O DinD único foi removido pelo `finally`. O deploy local recriou gateway e broker conforme autorizado; a config MCP ficou na revisão 18, os doze containers MCP dos dois gestores e `d6-nopip` permaneceram intactos. O host manteve 15 containers e nenhum `percival-i2-*` residual.

## Gates D11 que continuam abertos

1. **Dry-run do agente:** a checagem determinística validou loader, conteúdo e dados que o agente precisaria usar, mas não invocou um modelo/agent. Não havia endpoint de modelo isolado configurado; não foram usadas credenciais de produção. C3 continua pendente.
2. **Profile HTTP:** o fixture atual exercitou stdio com healthcheck falso; ainda não tem servidor MCP HTTP isolado cuja readiness falha deliberadamente. C6 continua aberto; C7 (restore/read-model) passou no fixture.
3. **Proveniência/deploy local:** candidata construída e implantada localmente como `percival-gateway:0.1.0-40d8eb9-d11-2e4d276142d8`; image ID no host `sha256:d128e0ca1dee1d60eaeed46a9d2fe4cfbc42c5fc42700cd723c602200e9a37aa`, revisão completa `40d8eb99e5efba5b1d1dd600e63bd7c283d61295`, `worktree=dirty`, diff `2e4d276142d8e8147c7886277287184bf192c47a3a0a7016085f9c95c6780978`, versão `0.1.0`. A skill embutida tem hash `81373e…`; o loader ativo confirmou `builtin`, disponível/enabled. O rehearsal completo também passou com essa candidata. C10 está atendido para o artefato local de teste, não para release; a imagem anterior `sha256:ac62466dfd99ca60006890479d052550287609ec7726bdae81d1976393f289c6` permanece retida em `percival-gateway:rollback-d11-pre-skill-20261025`. Não houve publicação/VPS.
4. **Política admin:** preflight read-only observou `allowRemoteAdmin=true` e publicação host no loopback. Não foi alterada. O registro da decisão do operador está pendente.

Duas tentativas intermediárias terminaram antes da primeira mutação MCP por erros de interpolação/serialização do harness, com `completed: false`; em ambas o DinD foi removido pelo `finally` e não houve mutação MCP. A execução documentada neste relatório é a repetição corrigida.
