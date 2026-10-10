# F6 — execução local parcial por consumidor

- **Observado:** 2026-10-10 UTC (2026-10-09 em America/Sao_Paulo).
- **Autorização:** o operador autorizou explicitamente executar F6 mesmo com
  F3–F5 pendentes. Esta execução documenta o desvio; não altera a política de
  zero Critical/High, não cria waiver e não fecha os gates anteriores.
- **Resultado:** quatro instalações MCP do Positronic passaram a apontar para
  candidatos locais por image ID. Handshake `initialize`/`tools/list` passou
  nos quatro serviços e em ambos os projetos autorizados para Notes. A pedido
  posterior do operador, as quatro imagens Positronic antigas sem referências
  de container foram removidas. O cutover F6 completo não terminou: os pins
  antigos do Percival ainda aguardam o gateway/broker.

## Procedimento e escopo preservado

As mutações foram feitas pelo launcher documentado
`positronic/scripts/positronic-dev.sh mcp server`, lendo revisão e configuração
com `show`, chamando `update-image` com image ID completo e recriando a
configuração por `configure` após o novo `configurationId`. Essa etapa é
necessária porque a capability Positronic invalida deliberadamente a
configuração anterior ao mudar a imagem. Rede, escopo, mounts e allowlists foram
mantidos. Nenhum tool que envia e-mail, altera calendário ou escreve/remove
notas foi chamado.

| Serviço / consumidor | Revisão anterior → nova | Image ID anterior → candidato | Verificação |
|---|---:|---|---|
| Deep Research / Positronic Global | 12 → 13 | `fa1e3cec8cd3c1423f87987f41c0d3c5f15505826953224924f015194c30ac99` → `c0c27be601955d2418e5f9cad6c5eefc12ab3753af9cce26e1737bc6989a2feb` | `discover` listou 5 tools. Evento Docker confirmou create/attach/start/die da imagem candidata; container de sessão atual `3b2415cd23d90ba336407161f0126ef030f117d08214d6d2a4019b9feb40b6d2` estava Up na inspeção. O container histórico `40bba2b310b94806ab97f5e360b05faa5192728f560c0afd06ce87061855a513` continua ativo e unhealthy; não foi parado. |
| AgentMail / Positronic Global | 12 → 13 | `f7acd7fa97c3201adb4c9fc26fc3be6e6cdac5c4a485e71a5ca9f1f9e11ac7c0` → `6af3c12ba1425f393dcd744bffd19b530968a27bd8c3a6724076d219a1fa0001` | `discover` listou 24 tools. Health check de inicialização fez somente `GET https://api.agentmail.to/v0/inboxes/...`, HTTP 200; nenhuma operação de e-mail foi enviada/modificada. Container candidato `f76aa5ae2fb332e2e37a43192316d3cab83a1f974220c5f20d955c39619162ff` estava Up. |
| Khan Calendar / Positronic Global | 6 → 7 | `01b960c604772a6e671686af8fdf5ccd7676c7564c7bf99af55f7c6a542fafbb` → `aff5bce93923fe263be8d919546eabe14565a4475b229935b6df6fe2bff65904` | `discover` listou 12 tools. A allowlist existente estava vazia e foi mantida vazia: nenhum tool de calendário foi habilitado. Inicialização consultou metadata pública do PyPI e escreveu apenas no filesystem descartável do container. |
| Notes / Positronic Local | 14 → 15 | `a677143c5b249352658242863d174a01b5e856beb56179a9f4f4b6ea477ffe65` → `830c014d1c0c4c5f24ac21ff5d38b9d45038cfb7f3da40729ac9b7f614f7ce2b` | `discover` listou 12 tools separadamente nos projetos `alternative-positronic` e `cevap-unesp`. As duas configurações mantiveram `network=none`, mount RW existente `/home/bill/.positronic/mcp/data/notes-vault` → `/vault` e a allowlist original. A origem do vault estava `65532:1000`, modo `0770`. Nenhuma operação de nota foi chamada. |

Na execução inicial, os image IDs antigos foram mantidos como referência de
rollback. Após a solicitação de limpeza, os quatro IDs antigos Positronic foram
removidos; rollback dessas instalações agora exige recarregar uma cópia
arquivada ou reconstruir as imagens antigas, algo que não foi verificado. O
caminho de configuração suportado continua sendo `mcp server update-image <id>
<image-id> <revisão-atual>`, seguido de reconfiguração equivalente (network,
mounts e allowlist). **Rollback não foi ensaiado.** Os IDs antigos do Percival
permanecem no Engine porque ainda estão fixados em `~/.nanobot/config.json`.

## Estado dos processos e limites

- Stdio é sob demanda por sessão; containers candidatos Deep Research e
  AgentMail foram observados ativos sem portas publicadas e sem restart
  persistente. A porta `8000/tcp` exibida para Deep Research é apenas a porta
  declarada na imagem; `HostConfig.PortBindings` estava vazio. Não foi aplicado
  healthcheck HTTP aos processos stdio.
- Deep Research candidato emite o aviso de Tini não ser PID 1/subreaper e sua
  árvore contém `docker-init` mais `/usr/bin/tini`. A descoberta MCP passou,
  mas o contrato de init único de F4 continua pendente.
- Na inspeção inicial de F6, uma instância Deep Research antiga estava unhealthy
  devido à probe HTTP aplicada ao transporte stdio. Na inspeção para limpeza
  subsequente, ela já não aparecia em `docker ps -a`; não foi encerrada por esta
  operação de limpeza. As sessões atuais inspecionadas usam os IDs candidatos.
- Khan continua sem tools efetivamente liberadas, portanto seu `tools/list`
  validou a imagem, não uma chamada funcional do agente.
- A registry Positronic agora contém image IDs candidatos. O mount de dados
  Notes foi preservado; nenhum volume ou dado foi removido.

## Serviços Percival ainda não migrados

OSM, Weather, AgentMail e Deep Research estão na configuração MCP Docker do
Percival; OSM/Weather não são instalações Positronic. O gateway e o broker
Percival estavam `Exited (137)`. O container gateway histórico tem `8765` ligado
a todas as interfaces (`HostIp=""`); portanto não foi iniciado. O `docker
compose config` atual também falha fechado porque
`PERCIVAL_DOCKER_GATEWAY_TOKEN_ISSUE_SECRET_FILE` não está definido. O daemon é
Engine 29.7.2; o broker candidato F3 ainda requer Engine 27.x fora da fixture
29 descartável. Não criei segredo, não iniciei o gateway exposto e não editei
`~/.nanobot/config.json` diretamente. O pin Percival de AgentMail/Deep Research,
além de OSM/Weather, não foi alterado.

## Pendências para concluir F6

1. Provisionar e verificar o arquivo privado de token de emissão WebUI e os
   valores de estado/GIDs necessários; escolher uma stack compatível com o
   Engine local e com bind de host loopback. Depois iniciar gateway/broker por
   Compose e validar readiness sem tocar nas configurações de terceiros.
2. Atualizar OSM e Weather no broker Percival pela API/domínio autenticado; usar
   os image IDs antigos para rollback e fazer handshake/ferramentas por
   `server_id`.
3. Decidir se a allowlist vazia atual de Khan deve continuar vazia ou se há
   autorização para expor tools. Até lá, não ampliar o acesso.
4. Fazer chamada funcional não destrutiva por serviço elegível, ensaiar rollback
   por ID e fechar as evidências restantes de F4/F5. F3 continua com
   Critical/High sem waiver e o resultado da CI remota continua desconhecido.

Na execução F6 inicial não houve commit, push, pull, tag, publicação, deploy
VPS, limpeza de imagens, remoção de dados ou encerramento de container
histórico. A limpeza autorizada posteriormente está registrada abaixo.

## Addendum — limpeza solicitada pelo operador

Após nova autorização explícita para encerrar processos antigos e excluir
imagens MCP antigas, revalidei `docker ps -a`, a registry Positronic e as
referências de image ID. Os quatro containers MCP ativos observados usam os
IDs candidatos: duas instâncias AgentMail (`6af3c12b…`; containers
`b96740f5baf577324f831cd3dbc15552f8dfac741f0a2eb919ad52d4d05b559f` e
`f76aa5ae2fb332e2e37a43192316d3cab83a1f974220c5f20d955c39619162ff`) e duas
Deep Research (`c0c27be6…`; containers
`c944db99b2dd200b79aeebb6335aedd7898acd08ce18b787ee2c8c7e07c74fb4` e
`3b2415cd23d90ba336407161f0126ef030f117d08214d6d2a4019b9feb40b6d2`);
mantive-os ativos por serem processos com a imagem nova. Nenhum
container referenciava as quatro imagens Positronic antigas.

Removi exatamente estes IDs antigos do Positronic:

- AgentMail `f7acd7fa97c3201adb4c9fc26fc3be6e6cdac5c4a485e71a5ca9f1f9e11ac7c0`
- Deep Research `fa1e3cec8cd3c1423f87987f41c0d3c5f15505826953224924f015194c30ac99`
- Khan Calendar `01b960c604772a6e671686af8fdf5ccd7676c7564c7bf99af55f7c6a542fafbb`
- Notes `a677143c5b249352658242863d174a01b5e856beb56179a9f4f4b6ea477ffe65`

O Docker removeu também as tags `positronic/khan-calendar:0.4.0-local` e
`positronic/notes:0.1.5-local`. Não removi volumes, containers das sessões
candidatas nem imagens não-MCP. Os quatro containers MCP históricos do Percival
estão `Exited`, mas seus image IDs continuam pinados em sua configuração; não
removi esses containers nem imagens. O gateway/broker Percival continuam
parados. A limpeza e o deploy multi-consumidor permanecem parciais até os pins
Percival serem atualizados pelo serviço suportado.
