# F4 — Revalidação de Compose e contratos de runtime

- **Data:** 2026-10-25
- **Escopo:** receitas Compose do core Percival e dos seis MCPs; validação local
  dos modos stdio/HTTP usando os candidatos F3 já retidos.
- **Resultado:** os contratos Compose e os smokes aplicáveis passaram. Durante
  esta execução de validação não houve build, retag/promoção, alteração de pin,
  limpeza, cutover, commit ou push; qualquer publicação posterior deve apontar
  para a autorização e os commits específicos do operador.
- **Referência:** [plano de padronização](../plans/closed/2026-10-09-docker-standardization-refactor-plan.md), §3/F4;
  [estado F3](../operations/mcp-docker-local-runbook.md#53-candidatos-limpos-f3-2026-10-25).

## Mudanças realizadas

- Core e overlay do broker preservam `create_host_path: false` em todos os binds
  de estado/token, com long syntax no overlay; o core declara um init do launcher.
- Notes declara UID/GID `65532:65532`; Khan declara `1000:1000` e executa com
  rootfs somente leitura, `/tmp` tmpfs, `cap_drop: ALL` e
  `no-new-privileges`.
- Weather declara UID/GID `999:999`; o HTTP profile lê o bearer token de secret
  file, sem interpolar o valor no ambiente Compose.
- OSM encaminha os settings de runtime documentados; bearer token e chave
  OpenRouteService são montados como arquivos. `/dev/null` fornece chave ORS
  vazia por padrão, preservando o fallback documentado.
- Deep Research não injeta placeholders vazios de credenciais: configurações e
  chave chegam pelo `/app/.env` montado read-only. O profile HTTP fixa
  `MCP_TRANSPORT=streamable-http`, que foi confirmado no endpoint `/mcp`.
- AgentMail mantém a API key e o inbox ID em arquivos separados fora do repo;
  o servidor lê a chave pelo suporte nativo `_FILE`, e o wrapper carrega o inbox
  ID no processo. Nenhum dos dois valores é emitido pelo render.
- O checker `scripts/check_compose_contract.py` agora trata segredo materializado
  como erro de gate e reconhece `AGENTMAIL_INBOX_ID` como dado sensível. Foram
  adicionados cinco testes focados em contratos stdio/HTTP, UID/GID e redação.

## Evidência executada

### Render e estrutura

- `python scripts/check_compose_contract.py --all`: **8/8 receitas PASS**,
  17 serviços cobertos (core, core+broker e seis MCPs).
- `docker compose config --quiet`: passou nos serviços e profiles relevantes;
  Deep Research passou separadamente em `stdio`, `http` e `production`.
- `git diff --check`: passou nos sete repositórios alterados.
- Quatro testes do checker passaram. A execução usou um venv temporário em
  `/tmp/nanobot-f4-venv`, pois a `.venv` do checkout aponta para um Python que
  não existe e não permite escrita.
- Renderizações com credenciais sintéticas para AgentMail, Weather, OSM e Deep
  Research confirmaram que os valores não aparecem no `docker compose config`.

### MCP stdio

Smokes executados com `docker compose run --rm -T --no-deps`, sem rebuild/pull,
apontando a overrides temporários para image tags já existentes e IDs registrados
no runbook:

| MCP | Resultado `initialize` / `tools/list` | Encerramento após EOF |
| --- | --- | --- |
| Notes | 12 tools; stdout apenas JSON-RPC | exit 0 |
| AgentMail | 24 tools contra mock HTTP local em rede Docker `internal` | exit 0 |
| Weather | 9 tools; stdout apenas JSON-RPC | exit 0 |
| Khan Calendar | 12 tools; stdout apenas JSON-RPC | exit 0 |
| OSM | 37 tools; stdout apenas JSON-RPC | exit 0 |
| Deep Research | 5 tools; stdout apenas JSON-RPC | exit 0 |

Notes e Khan usaram diretórios de fixture sob `/tmp/sectest`, nunca vault ou
calendário real. O smoke AgentMail usou credenciais sintéticas e mock local; não
executou operações de email.

### HTTP e fail-closed do core

- OSM HTTP profile: healthcheck do Compose executou `initialize` autenticado em
  `/mcp`; estado final `healthy`.
- Weather HTTP profile: `/healthz` ficou `healthy`; MCP sem bearer retornou 401;
  MCP com o secret file sintético retornou `initialize` HTTP 200.
- Deep Research HTTP profile: `/health` ficou `healthy`; handshake Streamable
  HTTP em `/mcp` retornou 200. A primeira tentativa revelou 404 com o transporte
  antigo `sse`; fixado `streamable-http`, o handshake passou.
- Core: `nanobot-cli --version` executou no candidato F3 com bind de estado
  descartável e identidade não-root. API profile com bind não-loopback e
  `api_key` vazia encerrou antes de escutar e mostrou a mensagem explícita
  `api_key is not set`. Bind de estado sem permissão de escrita também encerrou
  antes do comando e mostrou diagnóstico e remediação.

## Limites e incidentes

- O profile `production` do Deep Research passou no render estrutural, mas o
  proxy nginx não foi iniciado: não há `nginx:alpine` local nem `nginx.conf`
  fornecido/revisado. Não foi feito pull nem criada configuração de proxy; o
  teste do proxy TLS/auth continua dependente dessa fixture/operação.
- Uma tentativa inicial de smoke AgentMail apontou credencial **sintética** ao
  endpoint remoto e recebeu HTTP 403 durante a inicialização. Não houve
  autenticação válida nem operação de leitura/escrita/email; os smokes seguintes
  foram conduzidos somente contra mock local. Não repetir chamadas externas sem
  aprovação específica.
- O Compose de OSM usa volume nomeado de cache; o volume foi preservado após os
  containers temporários serem baixados. Não houve prune/remoção de volumes.
- O `docker compose run` do core reportou um container broker órfão preexistente
  (`nanobot-percival-mcp-broker-1`); foi observado, não parado nem removido.
- A `.venv` do nanobot não pôde ser reutilizada; o teste focal foi executado no
  ambiente temporário indicado. Nenhuma suíte integral dos seis repositórios foi
  repetida, pois as mudanças de aplicação/imagem não faziam parte desta tarefa.

## Conclusão

Os critérios locais F4 para render, separação stdio/HTTP, binds loopback,
redação de credenciais, identidade/persistência declaradas e smokes dos seis
MCPs foram atendidos para as receitas exercitadas. O runtime do proxy nginx no
profile opcional `production` permanece não verificado até haver uma imagem e
configuração de fixture apropriadas. Nenhuma evidência de F4 autoriza promoção,
cutover ou deploy.
