# MCP Docker: servidores ativos nao se recuperam apos desligamento do host

**Estado:** recuperacao local verificada em 2026-10-11 UTC; aceite de boot/VPS 27.x ainda aberto | **Prioridade original:** alta (indisponibilidade de 6/6 MCPs gerenciados) | **Observado:** 2026-10-10, host local, Docker Engine 29.7.2 (override descartavel; gate VPS 27.x nao avaliado).

**Plano e execucao local:** [recuperacao pos-desligamento](2026-10-10-mcp-docker-post-shutdown-recovery-plan.md). Gateway e broker locais atualizados; seis MCPs reais reconciliados, com 99 tools observadas. Gate de boot/VPS ainda pendente.

## Comportamento observado

Apos um desligamento e nova inicializacao do host, o gateway e o sidecar broker voltaram como `healthy` por `restart: unless-stopped`, mas os seis containers gerenciados permaneceram `exited`. O `config.json` continua declarando os seis servidores `active=true`, `state=running`, `persistent=false`; seus journals de transicao estao `committed`. O preflight `nanobot mcp-docker doctor` passa, mas verifica apenas broker/daemon/politica de host, nao a disponibilidade dos servidores. As tools MCP do Percival nao devem ser consideradas disponiveis nessa situacao.

| Container | Exit | Termino UTC | Evidencia relevante |
| --- | ---: | --- | --- |
| `percival-mcp-osm` | 143 (SIGTERM) | 22:27:48 | Parada do Docker no desligamento |
| `percival-mcp-deep-research` | 143 (SIGTERM) | 22:27:48 | Parada do Docker no desligamento |
| `percival-mcp-agentmail` | 255 | 22:46:37 | Estado atribuido na volta do daemon |
| `percival-mcp-weather` | 255 | 22:46:37 | Estado atribuido na volta do daemon |
| `percival-mcp-notes` | 255 | 22:46:37 | Estado atribuido na volta do daemon |
| `percival-mcp-khan-calendar` | 255 | 22:46:37 | Estado atribuido na volta do daemon |

Os seis têm `RestartPolicy.Name=no`, `OOMKilled=false` e labels `percival.mcp-docker.managed-by=percival-broker`. Nao ha falha da aplicacao MCP demonstrada nos logs consultados; os codigos 143/255 isoladamente nao diagnosticam erro das imagens.

## Sequencia e causa

1. `journalctl -b -1` registra `systemctl poweroff --no-wall` e `systemd-logind: poweroff requested` em 2026-10-10 19:27:48 -03 (22:27:48 UTC). O Docker recebeu `terminated` durante o desligamento; `docker.service` excedeu o timeout de parada de 5 s e systemd matou `dockerd` com SIGKILL as 19:27:53 -03. O host voltou no boot seguinte; o daemon iniciou as 19:46:37 -03 (22:46:37 UTC), registrando `layer not mounted` para os quatro containers que passaram a exibir exit 255. O timeout/SIGKILL agrava a parada, mas a causa do desligamento nao foi um crash espontaneo dos MCPs.
2. Compose reiniciou gateway e broker (~22:46:39 UTC). O broker respondeu `ready`, sem reativar os seis servidores. A intencao persistida, validada por leitura apenas dos campos `active`, `state` e `persistent` de `config.json`, continuou ativa; os containers existentes continuaram parados.
3. **Lacuna no codigo:** `MCPProvider._reconcile_managed()` chama a operacao `reconcile` para servidores ativos (`nanobot/agent/tools/mcp.py`, linhas 1523-1563). Em `nanobot/mcp_docker/broker.py`, linhas 438-445, `reconcile` chama `_spawn()` somente quando `_inspect(server_id) is None`. Se o container existe mas `State.Running=false`, nao chama `_spawn()` nem `docker start`: retorna `running=false` e a conexao nao e restabelecida. `DockerMcpService.list()` (linhas 83-173) apenas observa o container; o `recover` do journal trata transicoes pendentes, nao este caso com journal `committed`. O runbook (`docs/mcp-docker-f5-runbook.md`, linhas 115-121) espera que a reconciliacao tipada recupere servidores ativos apos outage.

O `percival-f2-engine27` teve exit 0 em 2026-10-08 e nao e parte do incidente. Os containers com nomes aleatorios vistos no mesmo periodo usam as imagens MCP, mas nao possuem label de gestao Percival; os exemplares inspecionados usam `AutoRemove=true`, `OpenStdin=true` e comando stdio, compativeis com sessoes MCP sob demanda. A origem exata de cada um nao foi determinada. Nao substituem `percival-mcp-*`; a atribuicao anterior de que seriam replicas gerenciadas/containers orfaos estava incorreta. Nao os remover como mitigacao desta issue.

## Reproducao controlada

Em fixture descartavel, instalar servidor ativo nao persistente, confirmar container nomeado rodando e journal `committed`, parar o container simulando perda do processo/host, sem remover o objeto Docker, e reiniciar gateway/broker ou invocar o caminho de `reconcile` usado pelo provider. **Atual:** a observacao mostra `stopped`/`disconnected`; `reconcile` retorna `running=false`, sem reiniciar. **Esperado:** a intencao ativa restaura o container e redescobre as tools; um servidor inativo ou `stopped-persistent` continua parado. Repetir com perda total do objeto (`container-missing`) como controle (caminho ja tratado por `_spawn`). Nao executar novo poweroff no host real como parte do teste.

## Correcao e aceite

- Tratar no broker o objeto existente mas parado ao reconciliar intencao `active=true`, distinguindo a parada deliberada de `stopped-persistent` da perda inesperada; preservar labels, politica de mounts/rede, identidade da imagem e protecao de transicoes/journals. Considerar qual operacao (`docker start` ou recriacao verificada) garante configuracao efetiva sem alterar intencao salva silenciosamente.
- Adicionar teste de regressao para **container existente parado + ativo** no broker e exercitar o caminho `MCPProvider.connect()` apos retorno do broker; verificar `running=true`, MCP conectado e tools descobertas. Cobrir separadamente o caso persistente deliberadamente parado e o container ausente.
- Validar em ensaio descartavel gateway + broker + servidor real antes/depois da parada; conferir observacao Docker e `tools/list`, nao apenas `healthy` do broker. Registrar explicitamente que o gateway/sidecar iniciam apos boot e que os MCPs gerenciados se recuperam; manter gate de VPS Engine 27.x aberto ate ensaio proprio.
- Investigar separadamente o timeout de 5 s na parada do `docker.service` e seus efeitos no shutdown; nao aumentar timeout nem alterar restart policy dos MCPs sem avaliar ciclo de vida deliberadamente parado.

## Fontes de verificacao

`docker ps -a`; `docker inspect` (estado, timestamps, restart policy, labels e OOM); `docker logs` dos servidores e broker; `journalctl -b -1 -u docker` e logind no boot anterior; `journalctl -b -u docker` no boot atual; leitura filtrada do `config.json` e estados dos journals; `nanobot mcp-docker doctor` no gateway; `nanobot/agent/tools/mcp.py`, `nanobot/mcp_docker/broker.py`, `nanobot/mcp_docker/service.py` e runbook F5. Nenhum container, configuracao ou credencial foi modificado nesta investigacao.

## Resolucao local executada (2026-10-11 UTC)

Com a autorizacao posterior do operador para implantar e ensaiar, o broker/gateway foram reconstruidos e recriados via Compose local com o override Engine 29. `reconcile` iniciou **os seis containers existentes**, sem trocar nenhum dos IDs da tabela acima; observacao posterior confirmou `running`/`connected` e `toolsSource=observed`: AgentMail 24, Deep Research 5, Khan 12, Notes 12, OSM 37, Weather 9 (total 99). Gateway e broker permaneceram `healthy`, configuracao `revision=18`, journals pendentes 0; o gateway registrou seis conexoes gerenciadas no segundo deploy. O primeiro deploy registrou cinco, revelando corrida de prontidao broker/gateway; um retry periodico do MCPProvider no ciclo de vida do gateway foi adicionado e testado sem exigir turno do usuario. Detalhes, hashes e gates no [plano](2026-10-10-mcp-docker-post-shutdown-recovery-plan.md).

Esta resolucao vale para **host local/Engine 29 com override**; reboot real apos o ultimo build, implantacao VPS Engine 27.x, CI remoto e aceite do operador no candidato nao foram realizados. O incidente local esta contido, mas a issue continua aberta para o gate de recuperacao de boot/VPS definido no plano.
