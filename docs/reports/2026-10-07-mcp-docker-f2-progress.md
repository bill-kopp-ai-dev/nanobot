# F2 — registro de implementação parcial (gate aberto)

**Base:** `b1221c8c` + alterações locais não commitadas, 2026-10-07. Este
registro não é um aceite de F2 nem substitui o ensaio do VPS em F5.

## Implementado e verificado

- `tools.mcpDocker` versionado (`schemaVersion: 1`) em `config.json`, com
  `revision` por seção e servidor, `servers` e `configurations` separados,
  IDs/RepoDigests locais validados, env `plain`/`secret`/`reference`, default
  de acesso amplo e rede `none`. Referências `${VAR}` não são resolvidas no
  gateway; o broker futuro deverá resolvê-las no spawn.
- `save_config` usa o writer de arquivo existente, modo `0600` na primeira
  criação e CAS adicional para impedir que um objeto de configuração antigo
  sobrescreva a seção MCP Docker. O serviço de domínio usa o lock serializado
  de `WebUISettingsConfig`, faz CAS e registra audit `started`/`committed`/
  `failed` sem valores de env. Cria backup para update/exclude e tenta
  compensação em falha de update. Não há journal/crash recovery (F5).
- Credencial scrypt local `operator.json` modo `0600`, CLI `operator-init`/
  `operator-rotate`, bootstrap de status somente loopback e rotas WebSocket
  tipadas: list, onze ações, setup e rotate. Mutações exigem bearer WebUI e
  senha administrativa separada; admin remoto desativado por default. A leitura
  de env `secret` retorna sentinel e mask hint, sem valor.
- CI geral e workflow de release TUI removem jobs/targets Windows/macOS;
  preservam os dois targets Linux de release TUI. Python Ubuntu agora é
  22.04/3.12 e 22.04/3.14. A matriz Arch e o job broker ficam pendentes.
- Contratos sintéticos `tests/mcp_docker`: 6 testes passam, incluindo CAS
  concorrente, 8 famílias simuladas, senha/rotas, redaction, broker offline,
  mode e backup. Não são prova de Docker Engine ou de MCP real.

## Falta para o gate F2

1. **Broker F2 real:** substituir o script descartável de F1 por executor
   separado com Docker CLI 27.x, inspeção/prontidão do daemon, imagem local
   imutável, CLI sem shell, covers derivados do inventário efetivo e aliases,
   rejeição de mounts/rede/flags que reabram paths protegidos, env `reference`
   resolvido só no broker e token rotacionável em arquivo. Não há sidecar
   canônico conectado ao cliente F2; ações são fail-closed se o broker não
   estiver disponível.
2. **Execução do agente:** integrar transporte Streamable HTTP autenticado à
   registry com namespace isolado do MCP genérico e gate para ativação e
   `toolsDisabled` antes de cada chamada (inclusive wrappers cacheados,
   reconexão e canais). Sem isso, nenhuma tool gerenciada é publicada.
3. **Semântica sob falha:** assegurar revogação antes de desativar/excluir,
   compensação real do update/exclude e distinguir intenção de observação
   Docker/conectividade MCP; testes de transições inválidas, timeouts, daemon
   indisponível e manutenção de volumes anônimos. A simulação de broker não
   demonstra reversão física; recovery pós-crash continua F5.
4. **CI e integração:** job `mcp-broker` com duas fixtures e a mesma topologia
   gateway+sidecar, validação real de mounts/negativas de daemon e smoke de
   oito famílias; completar Arch pinado. Nenhum teste Docker F2 foi executado.

## Verificações locais

- `pytest -q -o addopts='' tests/mcp_docker tests/config tests/webui/test_settings_routes.py`:
  **140 passed**; conjunto ampliado com `tests/utils`: **496 passed**.
- `pytest`: **8507 passed, 66 skipped, 1 failed** por dependência `nh3`
  ausente no teste Matrix (`tests/channels/test_channel_setup.py`); não foi
  executada a instalação de todas as dependências de canais da CI.
- `basedpyright` dos arquivos Python tocados: **0 errors**; gate completo
  `basedpyright nanobot`: **1580 errors** (dependências opcionais ausentes no
  ambiente, também observadas no relatório F1).
- `ruff check` dos arquivos tocados: **passou**; `ruff check .` tem os **2
  imports não usados preexistentes** em `tests/kg/test_cm_policy.py`.
- YAML dos workflows analisado por `yaml.safe_load`; smoke Docker F2 não
  executado. Sem commit/push/tag.

**Próxima ação:** broker F2 + política derivada do inventário de mounts, depois
registry/gate por chamada; executar smoke Docker com duas fixtures antes de
pedir encerramento de F2. A aceitação de risco de F1 não valida esta fase.