# F7 — provisionamento local do gateway/broker Percival

- **Data:** 2026-10-10 UTC.
- **Escopo:** ação 2 da sessão “Ações necessárias para liberar o aceite F7”;
  execução local no host de desenvolvimento, não no VPS.
- **Resultado:** gateway e broker Compose estão `healthy`; `nanobot mcp-docker
  doctor` passou. O stack usa o overlay explicitamente descartável para Engine
  29, pois o host executa Docker Client/Server `29.7.2`. Este resultado não
  comprova compatibilidade com Engine 27 nem fecha gates de VPS/F5.

## Diagnóstico e escolhas

- `docker.service` está `enabled` e `active`; `/var/run/docker.sock` é modo
  `0660`, GID `966`.
- O state existente `~/.nanobot` foi preservado. O token do broker já existia
  como UID:GID `1000:1999`, modo `0640`; o `.env` local mantinha token GID
  `1999` e socket GID `966`.
- O stack usa o Compose pair (gateway + sidecar broker), sem Docker socket no
  gateway. O overlay `docker-compose.engine29-override.yml` permanece apenas
  para desenvolvimento local descartável; o Dockerfile broker mantém a
  verificação Engine 27 fora desse overlay.
- A configuração persistida tem AgentMail, Weather, OSM e Deep Research com
  `active=true`, `state=running` e revisão global 4. O gateway poderia
  reconciliar essas entradas no startup. Após autorização expressa do operador
  para iniciar como pré-requisito do item 3, o gateway e broker subiram; na
  observação final os quatro containers MCP antigos continuavam `Exited`, sem
  novas conexões MCP iniciadas por esta execução.

## Alterações e execução

- Criado `~/.nanobot/mcp-docker/webui-token-issue-secret`, segredo aleatório
  persistente (valor omitido), UID:GID `1000:1000`, modo `0600`; `.env` local
  ignorado aponta para o arquivo. O broker token permaneceu `1000:1999/0640`
  após a normalização de ownership no entrypoint.
- O primeiro Compose start mostrou que o broker procurava o gateway pelo nome
  padrão `nanobot-gateway`, diferente do container gerado pelo projeto Compose.
  `docker-compose.mcp-broker.yml` agora exige e passa
  `PERCIVAL_GATEWAY_CONTAINER_NAME`; `.env` local usa
  `nanobot-nanobot-gateway-1`. O container histórico não precisou ser removido
  nem renomeado.
- Teste do endpoint `/webui/bootstrap` mostrou que o segredo de arquivo era
  rejeitado enquanto o `tokenIssueSecret` legado do config era aceito. A causa
  foi a conversão do modelo Pydantic para dict por aliases camelCase: o override
  escrevia `token_issue_secret`, sem substituir `tokenIssueSecret`. Corrigi
  `nanobot/channels/manager.py` para atualizar a chave existente e adicionei
  regressão em `tests/cli/test_gateway_commands.py`. Com o novo build, o segredo
  de arquivo passou a autenticar o bootstrap e a leitura da API de domínio.
- Imagens do stack, construídas do HEAD `86cd784052abd11915246ff9f0a5ecd62715f557`
  mais worktree local (revision label
  `86cd7840-f7-a367032c515e`):
  - Gateway `sha256:442578fd085ca2d37dc4221011604c1b1ff722238a01091dd8d43c4d63cd4855`.
  - Broker `sha256:7547079a2b96395de6df1e231b7d6ac9646acb1ad05d3eb5c08d360e6d9e0b72`.
- Render combinado validado: host ports 18790/8765 em `127.0.0.1`; gateway sem
  `/var/run/docker.sock`; broker com socket, sem portas publicadas e com
  supplemental GIDs `966`/`1999`.
- Depois do start: gateway health `healthy`, broker health `healthy`, e
  `nanobot mcp-docker doctor` retornou “MCP Docker broker ready (token,
  transport and Docker host policy verified)”. A leitura autorizada do domínio
  confirmou revisão 4 e os quatro pins antigos. O token de emissão WebUI não
  foi impresso nem salvo em log/relatório.
- `UV_PROJECT_ENVIRONMENT=/home/bill/.positronic/runtime/tmp/opencode/nanobot-f7-test-env
  uv run --locked --extra dev pytest -q tests/cli/test_gateway_commands.py`:
  **27 passed**. `git diff --check` passou.

## Limites e próximo passo

- Os pins dos quatro MCPs não foram atualizados. `operator.json` existe e está
  protegido (`0600`); a senha administrativa não está disponível ao agente.
  Mutations `update-image` exigem essa credencial no domínio autenticado. Não
  houve bypass, rotação ou redefinição da credencial.
- Próximo passo: o operador executa as quatro mutações autenticadas na WebUI
  local usando a senha atual, ou disponibiliza um handoff local protegido para
  que o agente as execute; em seguida validar image ID, observação, health e
  `tools/list` por `server_id`.
- Engine 27.x em VPS, boot limpo, F4/F5, rollback e aceite F7 continuam abertos.
