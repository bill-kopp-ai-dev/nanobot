# WebUI não consegue carregar o status dos servidores MCP Docker

- **Status:** aberta; causa ainda não determinada
- **Reportado em:** 2026-11-01
- **Severidade proposta:** média — falha a observabilidade/gestão visual, sem evidência de que os MCPs tenham parado
- **Área:** WebUI, rota de snapshot MCP Docker e observação do broker

## Sintoma

Na página `http://127.0.0.1:8765/#/mcp-containers`, a WebUI mostra o alerta:

> Could not load Docker MCP status. Try again.

A captura do operador mostra a página sem os cards de servidores. Em capturas
anteriores do mesmo episódio, os cards apareciam com `Data outdated; refresh
failed`, embora Docker e MCP estivessem indicados como `running`/`connected`.
O usuário reportou que o erro persiste após atualização das imagens do gateway,
broker e Deep Research.

## Estado observado

Inventário read-only posterior confirmou os containers ativos:

- Gateway: `sha256:d96a060e2c24b53a5765323ae4df142d89a2823e47ca23b3d764af92054fb9fa`,
  revisão `093da161b443c7cf756cf13f29633967baf62c09`, status `running/healthy`.
- Broker: `sha256:eb5ce9ef51ed9117fc0b2efe262dc8acbbd85eeff03ff3ff7bef6f437783bb81`,
  mesma revisão, status `running/healthy`.
- Deep Research: `sha256:1863c62b1f4a7420c191e315dd1a9fad1d4c9b4de0c762490aa369ee30585196`,
  confirmado tanto na referência configurada quanto no container.

Esses sinais não provam que a leitura autenticada do snapshot esteja saudável;
health do gateway/broker e conectividade MCP são checks distintos da rota WebUI.

Captura anterior de logs do gateway mostrou três respostas `200` à rota
`/api/settings/mcp-docker/list`, com durações de `6583`, `5439` e `4997` ms.
Essas linhas indicam latência elevada, mas não explicam o alerta visual; não há
correlation IDs nem resposta/corpo HTTP dessas requisições no material
disponível. É necessário confirmar se as linhas pertencem ao mesmo refresh que
produziu o erro.

## Código relevante

- `webui/src/components/McpContainersPage.tsx`: `refresh()` chama
  `fetchMcpDockerSnapshot`; exceção não-401 resulta na mensagem genérica. A
  página faz polling a cada 30 s e expõe retry manual.
- `webui/src/lib/api.ts`: `fetchMcpDockerSnapshot()` lê
  `/api/settings/mcp-docker/list` usando `API_READ_TIMEOUT_MS = 20_000`.
- `nanobot/webui/settings_routes.py`: rota/backend que obtém a configuração e
  solicita as observações do broker.
- `nanobot/mcp_docker/broker.py`: observação do estado Docker/MCP e cache read-only
  de 10 s para compartilhar snapshots de chamadas sobrepostas.

O componente distingue 401 de outros erros. A mensagem observada, portanto,
classifica a falha apenas como não-401; ainda pode corresponder a timeout,
resposta 5xx, erro de parsing/transporte ou falha parcial no snapshot. Nenhuma
dessas causas está confirmada.

## Investigação necessária

1. Reproduzir com os image IDs acima e registrar, para o mesmo refresh,
   timestamp, duração, status HTTP, corpo sanitizado, erro do browser e
   correlation/request ID do gateway/broker. Não incluir bearer, tokens, env ou
   conteúdo de configuração sensível.
2. Confirmar se falha a requisição inicial, o polling, o retry manual ou mais de
   uma requisição concorrente. Correlacionar Network/Console do browser com os
   logs do gateway e broker.
3. Medir a rota autenticada sob chamadas simultâneas e comparar com o limite de
   leitura de 20 s. Verificar contenção entre observações, discovery MCP,
   inspeção Docker e serialização do snapshot.
4. Distinguir falha total de observação parcial: estados guardados não devem ser
   apresentados como atuais quando a leitura falhou; ao mesmo tempo, um MCP
   conectado não deve desaparecer da UI por erro transitório sem diagnóstico
   suficiente.
5. Corrigir a causa e adicionar regressões para a rota e para o comportamento
   da página em timeout/5xx/transporte, incluindo refresh manual e polling.

## Critérios de resolução

- A rota autenticada responde com snapshot coerente e status/erro diagnóstico
  sanitizado; estados obsoletos são identificados explicitamente.
- Refresh inicial, polling e retry não deixam a página presa no alerta quando a
  API retorna com sucesso, e exibem estado de falha preciso quando não retorna.
- Chamadas concorrentes permanecem abaixo do timeout de 20 s no runtime de
  teste, com latência e quantidade de discoveries documentadas.
- Testes focados da rota e da WebUI passam; nenhuma alteração de pin/configuração
  dos MCPs é necessária para encobrir a falha.

## Próxima ação

Reproduzir a rota com DevTools Network/Console aberto na sessão autenticada e
correlacionar a requisição que falha com logs do gateway/broker. A pesquisa real
de Deep Research continua como validação separada e não deve ser repetida
automaticamente por causa desta falha de UI.
