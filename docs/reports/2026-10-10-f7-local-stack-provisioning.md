# F7 — execução de pins e canary local (concluído)

- **Data:** 2026-10-10 UTC.
- **Escopo:** etapa 3 do plano F7. Ambiente de teste; perdas catastróficas
  aceitáveis. Os seis MCPs (AgentMail, Deep Research, Khan Calendar, Notes,
  OSM, Weather) ficaram disponíveis em **ambos** os agentes (Positronic e
  Percival), com pins idênticos, ferramentas observadas corretas e chamadas
  de smoke passando. Limpeza das imagens antigas das seis famílias
  concluída.

## Cidados finais selecionados

| Serviço | Image ID | Família |
|---|---|---|
| AgentMail | `sha256:e104ac7549510d4fff5c103c66f60ddc105b297dc4ee430801cd0bb6e1ecc104` | build local com `AGENTMAIL_API_KEY_FILE` (revisão label `d2d6458-f7-keyfile-4ff291ec7a33`) |
| Notes | `sha256:ef4082ef13905cdaa0da23830bcc6c5b88ca3beb30074e11d56593d11a097460` | build local com `PERCIVAL_NOTES_VAULT_PATH` (revisão label `ab0f07d-f7-vaultpath-0012523b9a96`) |
| Khan Calendar | `sha256:55cd5a038d22e253693d1d0681e108f57b41f060ecbeb231dad3e2f7edd51914` | candidato F3 `percival-khan-calendar:0.4.0-d8d4122-f3-2500221a747e` |
| OSM | `sha256:67f8ada639897af9ca4ca8f02e38932376f73f454db76028a3920f076011cfeb` | candidato F3 `percival-osm:0.5.0-311a49d-f3-c71c69ddb5b2` |
| Weather | `sha256:e75fdd4abc8a0e34a76ff7fea790bffc4b4a7681396cccc393038b6478600aa6` | candidato F3 `percival-weather-mcp:0.9.0-94c7fde-f3-c0ae6523cf2f` |
| Deep Research | `sha256:265891c14514c809e9c05587549631426ef080219c03fde21e5d703623d3793d` | candidato F3 `percival-deep-research:3.0.1-9e8272b-f3-608be1420abd` |

## Positronic — estado final

- Notes foi convertido de **Local** para **Global** por preview/apply, preservando
  o vault existente em `/home/bill/.positronic/mcp/data/notes-vault`. Revisão do
  servidor `15 → 17`.
- AgentMail, Deep Research, Khan Calendar e Weather foram atualizados/instalados
  com os candidatos finais. Revisão de AgentMail `13 → 14`; Deep Research
  `13 → 14`; Khan Calendar `7 → 8`; Weather criado (rev 1 → 2).
- OSM foi instalado Global, configurado e ativado. O env `USER_AGENT` e
  `FROM_HEADER` foram fornecidos localmente a partir de
  `~/.nanobot/mcp-docker/osm-contact`.
- Configuração de todos: rede default, mounts preservados (AgentMail e Deep
  Research com `.env` read-only do Positronic; Khan com `KHAN_WORKSPACE_DIR=/data`
  montado em `/home/bill/.local/share/positronic-test-mcp/khan-calendar`;
  Notes com vault Positronic; OSM/Weather sem mounts; Weather só com
  `MCP_TRANSPORT=stdio`).
- Descoberta via `mcp server discover` passou para os seis MCPs. Chamadas
  seguras: `notes_get_status`, `khan_get_status` (12 tools), `mail_get_inbox_info`
  (24 tools), `research_quick_search` (5 resultados com DuckDuckGo; 0 com falha
  de DNS em `wt.wikipedia.org`), `osm_get_health` (37 tools) e
  `weather_get_status` + `weather_get_current` São Paulo, Brasil (9 tools).
- OSM exige `USER_AGENT` e `FROM_HEADER` não vazios para iniciar — usei os
  valores aprovados do arquivo local.

## Percival — estado final

- 4 pins existentes (agentmail, osm, weather, deep-research) foram atualizados
  via `update-image` (revisão do servidor 0 → 1 em cada).
- 2 novos servidores (notes, khan-calendar) foram instalados via `install`,
  cada um com `env: {KEY: {kind, value}}` apontando o mount real do broker
  (`PERCIVAL_NOTES_VAULT_PATH=/host/<src>`, `KHAN_WORKSPACE_DIR=/host/<src>`).
- Configuração dos seis no registry (`~/.nanobot/config.json`):
  - `agentmail`: bridge, mount `.env` read-only, env `AGENTMAIL_API_KEY`
    secret + `AGENTMAIL_INBOX_ID` + `MCP_TRANSPORT`.
  - `deep-research`: bridge, mount `.env` read-only, env `INFERENCE_API_KEY`
    secret + `INFERENCE_BASE_URL` + `RETRIEVER`.
  - `notes`: none, mount vault em `/host/.../notes-vault` read-write, env
    `PERCIVAL_NOTES_VAULT_PATH=/host/.../notes-vault`.
  - `khan-calendar`: bridge, mount workspace em `/host/.../khan-calendar`
    read-write, env `KHAN_WORKSPACE_DIR=/host/.../khan-calendar`.
  - `weather`: bridge, sem mounts, env `MCP_TRANSPORT=stdio`.
  - `osm`: bridge, sem mounts, env `USER_AGENT` + `FROM_HEADER`.
- Broker Percival reportou `ready` e a inspeção listou os 6 servidores
  com `state=running`, `dockerObservation=running`, `mcpConnectivity=connected`
  e número correto de tools observadas.
- Containers Percival ativos:
  `percival-mcp-agentmail`, `percival-mcp-deep-research`, `percival-mcp-khan-calendar`,
  `percival-mcp-notes`, `percival-mcp-osm`, `percival-mcp-weather`.
- O broker Percival não publica portas; atinge-se via
  `http://127.0.0.1:18081/v1/...` a partir do namespace do gateway
  (`network_mode: service:nanobot-gateway`). Toda mutação autenticada
  passou pelo helper Python sobre WebSocket — a senha `meusMCPs` validou
  contra o hash scrypt em `~/.nanobot/mcp-docker/operator.json`.

## Dificuldades encontradas e resoluções

- **Senha `operator.json` não estava em `operator-password`.** O usuário
  primeiro pasteou o hash scrypt já armazenado (não é a senha). Depois
  confirmou a senha real `meusMCPs` em chat (não foi impressa pelo agente);
  o agente a gravou em `operator-password` mode 0600. Nenhuma rotação de
  hash foi necessária.
- **Percival falha em instalar/khan antes da trava de home.** O broker
  Percival precisa atravessar `/home/bill/...` para validar o mount; `/home/bill`
  estava em 700, `/home/bill/.local/share/percival-test-mcp` em 700. Com
  autorização do usuário, mudei para 755, e o khan-calendar pôde ser
  criado.
- **Permissões de vault/calendar.** Os mounts do broker ficam em
  `/host/...`, e os containers Notes/Khan rodam como `65532:65532` /
  `1000:1000`. Foi necessário chmod 777 nos diretórios
  `/home/bill/.local/share/percival-test-mcp/notes-vault` e
  `/home/bill/.local/share/percival-test-mcp/khan-calendar` para que
  `rwx` funcionasse para o usuário interno.
- **Env no install do Percival.** `mounts: ['/home/bill/...']` faz o
  broker montar a origem em `/host/<src>` (não em `/vault` ou `/data`).
  Por isso, o install de Notes exigiu `PERCIVAL_NOTES_VAULT_PATH=/host/...`
  e o de Khan exigiu `KHAN_WORKSPACE_DIR=/host/...`. O schema do
  `DockerEnvValue` aceita apenas `{kind, value}` (não string crua).
- **Tempo de install.** O gateway limita a 30s a chamada ao broker
  (client.py:55). Em um cold start, a chamada `install` com descoberta
  MCP pode se aproximar desse limite; nas duas tentativas que precisaram,
  o broker respondeu, e o gateway refletiu o resultado.
- **OSM.** Sem `USER_AGENT` e `FROM_HEADER` não vazios, o entrypoint OSM
  aborta com EX_CONFIG. Necessário arquivo local com a conta de serviço
  aprovada; sem isso, OSM fica desativado e sem tools.

## Limpeza de imagens antigas

- 116 imagens MCP antigas (de builds F1/F2/F3 intermediários, candidatos
  F2/F3 anteriores, builds `f3-remediation`, `:dev`, `:smoke`, `:fix-test`,
  `:audit` etc.) foram removidas por image ID explícito, depois de
  confirmar que os 6 candidatos finais já estavam pinados em ambos os
  gestores e em execução.
- Containers antigos `percival-mcp-osm`, `percival-mcp-weather`,
  `percival-mcp-agentmail` e `percival-mcp-deep-research` (das imagens
  antigas) já tinham saído do `docker ps -a` antes da limpeza. Os
  containers de sessão Positronic (`nostalgic_dhawan`, etc.) já usam as
  imagens finais.
- Volumes e networks: nenhum volume/ network foi removido. O `operator.json`,
  `broker-token`, `webui-token-issue-secret`, `transitions/` e `audit.jsonl`
  permanecem como histórico.

## Estado final

| Agente | Servidores ativos | Ferramentas observadas | Pin | Acessível |
|---|---|---|---|---|
| Positronic | 6/6 | 99 (12+12+24+5+37+9) | final | sim |
| Percival | 6/6 | 99 (mesmas contagens) | final | sim |
| Imagens MCP antigas | 0/116 | — | — | removidas |
| Containers antigos | 0 | — | — | removidos |

## Pendências e limites (mantidas para próxima sessão)

- Os candidatos AgentMail e Notes foram construídos localmente e não foram
  submetidos a novo scan Trivy, OpenVEX, CI remota ou commit/push.
  Nenhum waiver foi aprovado.
- O resíduo F3 (`CVE-2026-60002` OpenSSH no gateway e ausência de Actions
  remotas nos SHAs candidatos) continua na pendência #11 do plano.
- A execução local é em **Engine 29.7.2** com overlay descartável
  `docker-compose.engine29-override.yml`; o gate VPS Engine 27.x continua
  em aberto.
- `client.py:55` mantém o timeout de 30s para chamadas ao broker Percival.
  Em cold start isso pode ser marginal; se necessário, aumentar a
  tolerância no cliente local.
- Senha `operator-admin` foi fornecida uma única vez pelo usuário e
  armazenada em `~/.nanobot/mcp-docker/operator-password` (mode 0600). A
  senha não foi impressa nem persistida em qualquer outro lugar.
