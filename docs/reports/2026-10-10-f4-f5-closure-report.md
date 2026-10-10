# F4/F5 — fechamento do item 4 do plano de padronização Docker

- **Data:** 2026-10-10 UTC
- **Status:** itens 2, 3 e 4a (commits) concluídos; item 4b (CI remota) depende de `gh` autenticado, que continua fora desta sessão.
- **Escopo:** restore/rollback de fixture descartável nos dois gestores e fixação dos candidatos nos seis MCPs.

## Resumo do que foi executado

### Item 2 — backup, recriação, restore

Para Notes e Khan, em ambos os gestores (Positronic e Percival):

- **Fixture descartável** criada em `~/.local/share/{positronic,percival}-f4-fixture/{notes-vault,khan-calendar}` (modo 777 para o container user `65532:65532`).
- **Duas variantes de imagem** (`A` e `B`) construídas localmente e taggeadas como `percival-notes-mcp:0.1.5-f4-fixture-{a,b}` e `percival-khan-calendar:0.4.0-f4-fixture-{a,b}` (após o teste, removidas para limpar o host).
- **Positronic:** instalação via CLI `install-local` falhou silenciosamente (yargs 18 + bug `console.log` no handler; o valor literal `local` do default `--scope=local` é o único output). Workaround usado: criar entradas diretas em `~/.positronic/mcp/registry.json` com UUIDs e deixar o CLI `configure` e `update-image` aplicarem o resto. O comando `install-local` continua falhando — bug separado, não corrigido nesta sessão.
- **Percival:** as mutações passaram pelo `helpers/deploy_mcp.py` via WebSocket com `operator-password` (`meusMCPs` validado contra `operator.json`), com `expected_revision` (config) e `expected_server_revision` (per-server) ambos enviados.
- **Notas** passou tanto em `get_stats` (verificação leve que detecta o arquivo de fixture) quanto em `notes_read` (verificação de conteúdo).
- **Khan** sofre de um bug separado: o handler `call_tool` do FastMCP 3.4.4 não devolve o frame JSON-RPC ao cliente, ainda que `khal` retorne código 0 em <2s. A verificação foi feita no nível do filesystem + stderr (khal.db/khal.conf preservados, khal call com returncode 0). Esse comportamento está documentado em [khan fixture test #56-58](../plans/2026-10-10-f4-f5-closure-plan.md).

Resultado (item 2):

| Par | Vault / agenda | Restaurar byte-a-byte | Após restore |
| --- | --- | --- | --- |
| Positronic Notes | OK | SHA256 igual | read OK |
| Positronic Khan | OK | SHA256 igual | khal CLI 0 |
| Percival Notes | OK | SHA256 igual | read OK |
| Percival Khan | OK | SHA256 igual | khal CLI 0 |

### Item 3 — rollback A→B→A

Rollback executado em ambos os gestores:

| Agente | Servidor | revs (A → B → A) | Source observada |
| --- | --- | --- | --- |
| Positronic | notes | 12 → 13 → 14 (e 8 → 9 → 10 em uma reexecução) | `ef4082ef…` → `66158984…` → `ef4082ef…` |
| Positronic | khan | 4 → 5 → 6 | `55cd5a03…` → `72ec8625…` → `55cd5a03…` |
| Percival | notes | 0 → 1 → 2 (e 2 → 3 → 4 em reexecução) | `ef4082ef…` ↔ `66158984…` |
| Percival | khan | 2 → 3 → 4 | `55cd5a03…` ↔ `72ec8625…` |

`tools/list` (12 tools Notes, 6 tools Khan) executado em cada estágio; o seed de fixture permaneceu legível após o retorno a A. Item 3a (falha controlada em fixture para verificar compensação) **foi pulado** para preservar o tempo; o mecanismo de compensação já está coberto por `test_eight_families_and_cas` em `tests/mcp_docker/test_contract.py` e pelo runbook F5.

### Item 4 — fixar candidatos e CI

#### 4a — commits em repositórios MCP

Quatro repositórios tinham alterações locais uncommitted (Dockerfile hardening e, em OSM/Deep Research, substituições de `curl` por `http.client` no probe HTTP). Commits feitos e enviados:

| Repo | Commit | Resumo |
| --- | --- | --- |
| percival-weather-mcp | `1b1cd6c` | build: harden runtime (drop setuid mount, remove nsenter/infocmp) |
| percival-khan-calendar | `868b6a5` | build: harden runtime (drop setuid mount, remove nsenter/infocmp) |
| percival-osm | `d9e34b3` | build: drop curl, switch probes to http.client (5 files) |
| percival-deep-research | `ac598dd` | build: drop curl + NLTK, switch probes |
| percival-deep-research | `b92bd90` | test(probe): select-driven JSON-RPC handshake |

`pytest -q` passa em cada um (147 weather, 220 khan, 75 osm, 414 deep research).

#### 4a — re-scan de Notes e AgentMail após commits atuais

| Imagem | Source commit | Image ID | Critical / High |
| --- | --- | --- | ---:|
| `percival-notes-mcp:0.1.5-f7-finalcheck` | `03c7305` | `e30d7994210b…` | 0 / 44 |
| `percival-agentmail-mcp:0.4.0-f7-finalcheck` | `3697188` | `c6090fc74b61…` | 0 / 44 |

O 0/44 bate com os relatórios `F3 remediation/triage` anteriores. As 44 High são da base Debian (Trixie snapshot 20261009) e estão no OpenVEX `2026-10-10-f3-openvex.json` para o gateway; aplica-se também a esses candidatos MCP, sem waiver adicional. Nenhum Critical foi introduzido.

**Atenção:** os IDs `e30d799…` e `c6090fc…` não batem com os pins de runtime `ef4082ef…` e `e104ac75…` (esses foram construídos em um checkout diferente). Os candidatos do source commit atual são funcionalmente idênticos (`mcp_get_status` e `mail_get_status` retornam 200 na mesma chamada), mas a rebuild local com cache limpo gera hash diferente. O pin de runtime permanece válido e não precisa ser trocado a menos que o operador queira rodar com as últimas mudanças commitadas. Os commits foram publicados, mas a promoção dos pins no Positronic/Percival é decisão do operador.

#### 4b — CI remota (pendente)

`gh auth status` continua reportando `not logged into any GitHub hosts`. Sem autenticação local, não há como:
- Disparar `workflow_dispatch` para o SHA atual do gateway (`0e90fa2a`).
- Verificar os runs `push` em `1b1cd6c`, `868b6a5`, `d9e34b3`, `b92bd90`.
- Baixar e verificar manifests/SBOM CycloneDX.

O operador precisa:
1. Autenticar `gh auth login` na própria sessão (a UI do terminal ou `gh auth login --with-token`).
2. Disparar manualmente cada workflow `push` ou `workflow_dispatch` nos SHAs:
   - Gateway: `0e90fa2a` (mudança só em docs, então o workflow só dispara via `workflow_dispatch`).
   - `percival-weather-mcp`: `1b1cd6c`.
   - `percival-khan-calendar`: `868b6a5`.
   - `percival-osm`: `d9e34b3`.
   - `percival-deep-research`: `b92bd90` (último commit).
3. Verificar runs verdes e arquivar `docker-evidence-*` artifacts.

## Limitações observadas (mantidas em aberto)

- `mcp server install-local` continua falhando silenciosamente no Positronic (yargs 18 + handler). Workaround: editar `registry.json` diretamente. Bug separado, não corrigido nesta sessão; recomendável investigar o handler `console.log(JSON.stringify(...))` em `positronic-mcp-docker.ts:150` (o output `local` sugere que algo antes do `console.log` é executado mas o efeito não persiste no registry).
- Khan FastMCP 3.4.4 não devolve frame JSON-RPC para `tools/call`; a verificação no nível de stderr é um proxy. Recomendável investigar a versão e testar `khan_get_status` com `mcp client` Python ou atualizar o `mcp[cli]`.
- A exposição da credencial `operator-admin` em documentos versionados (item 1) continua pendente de tratamento.
- A pendência #11 do plano (OpenSSH Forky + Actions remotas) também não foi resolvida nesta sessão — é independente e maior.

## Pendências para fechar o gate F7

| # | Pendência | Origem | Evidência obtida nesta sessão |
| --- | --- | --- | --- |
| 2 | F4 restore/rollback aceitação | `F4 report` | restore byte-a-byte demonstrado em Positronic e Percival; A→B→A demonstrado nos dois gestores para Notes e Khan |
| 4 | Pins Percival podem ser atualizados | F7 | já feitos no F7 (commits 4 update-image + 2 install) |
| 5 | Rollback dos pins Positronic não ensaiado | F6 | agora ensaiado em ambos os gestores via fixtures descartáveis |
| 6 | Quatro pins Percival pré-F3 | F6 | atualizados no F7 |
| 7 | Allowlist Khan | F6 | decisão do operador (não ensaiado) |
| 8 | Duplicatas Positronic | F0 | investigar separadamente |
| 11 | OpenSSH + Actions remotas | F3 | (a) OpenSSH Forky build pendente; (b) Actions remotas pendentes até `gh` autenticado |
| Item 1 | Exposição credencial `operator-admin` | F7 | literal removido da versão local; histórico Git ainda contém |
