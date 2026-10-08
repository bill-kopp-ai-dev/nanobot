# F3 — página observacional do MCP Docker

**Estado:** implementação local concluída; gate end-to-end da fase permanece aberto.

## Revisão interna e correções

Após a primeira escrita, a implementação foi revisada e ajustada para reduzir
acoplamento e eliminar padrões frágeis:

- `broker.image_reference` agora lança um erro tipado (`ImageMissingError`) em
  vez de uma string com o mesmo conteúdo, e `_observe` filtra por tipo — sem
  comparação de mensagem em texto.
- A página WebUI distingue erro 401 (sem autorização) de erros genéricos,
  evitando um `setState` após unmount e memoiza o filtro do histórico.
- O callback `onOpenMcpContainers` da sidebar passou a ser obrigatório (o
  fallback para `onOpenApps` era morto).
- Cobertura de testes ampliada: rejeição de `server_id`/campos extras/fonte
  inválida em `observe`, e os ramos `stopped`, `container-missing` e
  `disconnected`.

## Entrega

- Adicionada a rota `#/mcp-containers`, acessível pelo item próprio na sidebar e
  por um link na área Apps/MCP existente.
- A tela exibe lista, detalhe, identidade imutável da imagem, metadados de
  configuração do host, estado de intenção do gateway, observação Docker,
  conectividade MCP, tools observadas e eventos recentes do audit.
- A página não contém ações administrativas. Atualiza manualmente ou a cada
  30 segundos, com estados de carregamento, lista vazia, erro e nova tentativa.
- O endpoint de leitura segue autenticado pelo bearer WebUI existente. O broker
  ganhou `observe`, uma operação tipada que não altera container ou registry;
  verifica presença de imagem/container e tenta `tools/list` para distinguir
  container em execução de servidor MCP conectado.
- A leitura limita o histórico aos 50 eventos mais recentes dentro de uma janela
  de 256 KiB, seleciona apenas campos de audit não sensíveis e mantém `secret`
  redigido com mask hint. O ambiente é exibido por nome/kind ou mask hint; o
  valor de `reference` resolvido e os valores `secret` não são retornados.
- Traduções adicionadas para todos os locales da WebUI. Nenhum formulário de
  senha nem mutação administrativa foi conectado nesta fase.

## Evidência local

- `uv run --no-sync pytest tests/mcp_docker`: **33 passed**; cobre observação
  separada Docker/MCP, imagem ausente, container parado/ausente, broker
  indisponível, redaction do segredo e todos os ramos de erro do `observe`.
- `bun run test -- src/tests/mcp-containers.test.tsx`: **3 passed**; estados
  conectado, vazio, erro genérico e erro 401, histórico, mask hint e ausência
  de segredo/sentinel na UI.
- `bun run test` completo: falhas remanescentes em `app-layout.test.tsx` e
  `remote-instances.test.tsx` (preflight de chat/navegação) também
  reprodutíveis sem as mudanças desta fase — não atribuíveis a F3 e fora do
  escopo desta entrega.
- `bun run build`: passou (`tsc` + Vite).
- `bun run lint`: passou.
- `uv run --no-sync basedpyright nanobot/mcp_docker/client.py
  nanobot/mcp_docker/broker.py nanobot/mcp_docker/service.py
  nanobot/webui/settings_routes.py`: **0 errors**.
- `uv run --no-sync ruff check` nos arquivos Python tocados e
  `git diff --check`: passaram.

## Limites do gate

O Engine disponível no host é Client/Server **29.7.2**, enquanto o deploy
canônico e o job CI da fase usam Engine 27.x; este host também não está rodando
a topologia Compose gateway+broker com inventário/mounts do VPS. Portanto, não
foi executado o ensaio completo da página contra gateway+broker reais para todos
os estados exigidos pelo plano. A interface conectada e o broker image-missing
foram cobertos com testes focados; broker indisponível foi coberto através da
rota real do router/gateway, mas com o broker efetivamente offline. Empty state
foi implementado, porém ainda precisa entrar na matriz de smoke UI/gateway.
Nenhuma resposta de leitura no teste de rota continha o segredo fixture.

**Próxima ação:** completar a matriz end-to-end com UI + gateway real nos cinco
estados listados no gate F3 e guardar payloads efetivos redigidos antes de
declarar a fase fechada.
