# F4 — gestão MCP Docker pela página

**Estado:** implementação local concluída; gate end-to-end F4 permanece aberto.

## Entrega

- A página `#/mcp-containers` agora oferece as oito famílias de gestão via
  mutações tipadas pelo WebSocket autenticado do WebUI: instalar; configurar;
  habilitar/desabilitar tool; ativar/desativar servidor; atualizar imagem;
  reiniciar; excluir; iniciar/parar contêiner persistente.
- Setup de `operator-admin` ocorre pelo navegador local sem senha anterior;
  rotação exige credencial atual. A senha administrativa é enviada como campo
  distinto do bearer WebUI e fica apenas em memória da página, sendo descartada
  ao desconectar o WebSocket ou desmontar a página. A política de administração
  remota continua explícita no host e desabilitada por padrão.
- O editor de host cobre mount reductions, `network: none` e env `plain`,
  `secret` e `reference`. Mostra estado antes/depois e redige secrets; ressubmete
  `_REDACTED_MCP_ENV_SECRET` para preservar o valor sem exibi-lo. O broker
  acrescenta à observação o network mode e mounts efetivos (tipo/destino/RW),
  sem retornar `Source` dos mounts do host.
- A instalação alerta sobre o acesso R/W amplo padrão e exige ID de servidor
  digitado e revisão do preview. Aumento de escopo em configuração exige ID do
  servidor; update e exclude têm confirmação digitada, com backup automático do
  backend antes de update/exclude. Start/stop só aparece para servidor ativo
  com `persistent: true`.
- 401 solicita nova senha; 403 explica política local/remota; 409 reconsulta o
  snapshot atual; broker offline e demais erros não são apresentados como
  sucesso. Após ação bem-sucedida, a página reconsulta o estado observado.
- A rede é mostrada como fixa em `none`, único valor aceito pelo contrato atual;
  a interface não cria escolhas de rede que o broker não suporta.

## Evidência local

- `uv run --no-sync pytest tests/mcp_docker tests/config/test_gateway_config.py -q`:
  **36 passed**.
- `bun run test -- src/tests/mcp-containers.test.tsx src/tests/i18n.test.tsx`:
  **35 passed** (8 fluxos MCP Docker + 27 i18n). Cobertura inclui setup sem
  senha anterior, rotação, mutação com ambas credenciais, preservação do
  sentinel secreto e confirmação digitada ao ampliar mount scope.
- `bun run build`: passou (`tsc` + Vite).
- `bun run lint`: passou.
- `uv run --no-sync basedpyright nanobot/mcp_docker/broker.py
  nanobot/mcp_docker/service.py nanobot/webui/settings_routes.py`: **0 errors**.
- `uv run --no-sync ruff check` nos arquivos Python F4: passou.
- `git diff --check`: passou.
- Smoke real do gateway+broker descartáveis com duas fixtures MCP:
  `scripts/percival-f2-docker-smoke.sh` (executado via `bash`), com as imagens
  gateway/broker construídas da árvore F4 e Weather/OSM construídas dos commits
  fonte B20. Broker Docker CLI **27.5.1**, Engine local **29.7.2**. O driver
  exercitou instalação, disable/enable, deactivate/activate, configuração,
  restart, update-image/rollback fixture, start/stop persistente (Weather) e
  exclude nas duas fixtures. Os containers do smoke foram removidos pelo
  cleanup; os outros containers pré-existentes do host permaneceram intactos.
  Este smoke é integração do domínio/broker, não interação browser real.

## Limites e gate aberto

- Não foi executada a matriz integrada **Browser WebUI + gateway + broker** para
  todas as operações. Os testes de UI usam cliente WebSocket simulado e o smoke
  Docker exerce o driver de integração do gateway, sem navegador. A prova de
  resposta visual com mounts/rede efetivos após salvar, auth negativa via proxy,
  conflito 409 com mutação concorrente e não interferência em outro registro
  ainda precisam ser ensaiados juntos.
- O Engine disponível é 29.7.2. Nenhum resultado aqui comprova o deployment
  canônico no Engine 27.x do VPS, cujo inventário e aceite continuam pendentes
  para F5.
- Traduções novas estão completas em pt-BR e inglês; em outros oito locales as
  novas strings de gestão usam inglês temporariamente, embora a estrutura de
  chaves esteja alinhada e coberta por `i18n.test.tsx`.
- Restore da UI, journal/recovery de crash e reconciliação continuam em F5; o
  restore permanece via CLI conforme o plano.

**Próxima ação:** executar a matriz integrada browser/gateway/broker contra as
duas fixtures, registrar snapshots/payloads redigidos e comprovar conflitos,
auth 401/403, preview/redaction e estado de outro servidor antes de fechar F4.
