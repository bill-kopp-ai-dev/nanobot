# Percival: MCP em Docker e pagina de administracao

**Data da analise:** 2026-10-06
**Status:** recomendacao tecnica para decisao e prototipo; nenhuma integracao Docker-MCP ou pagina nova foi implementada nesta analise.
**Escopo:** Percival Linux-only; cliente MCP, runtime de containers, plano de controle e interface de administracao.
**Base:** [relatorio de pesquisa de 2026-10-03](PERCIVAL_MCP_DOCKER_RESEARCH_REPORT.md), codigo local e fontes primarias consultadas em 2026-10-06. Referencias locais correspondem a arvore inspecionada, nao a uma versao publicada do Percival.

**Complemento posterior:** a [analise da implementacao Positronic](2026-10-06-percival-positronic-docker-mcp-transfer-assessment.md) acrescenta evidencia de um broker proprio funcional, revê a preferencia inicial por prototipar somente o Docker MCP Gateway e propoe comparacao entre executores com criterio de isolamento do Docker daemon. Ler esse complemento antes de tratar a recomendacao abaixo como escolha final.

## Parecer executivo

**Recomendo prototipar um Docker MCP Gateway externo, com o Percival como cliente MCP e uma pagina dedicada de administracao dentro da WebUI do Percival.** O acesso ao Docker daemon deve pertencer ao gateway/runtime e, se houver administracao pelo browser, a um plano de controle separado e de privilegio estritamente delimitado. O browser nao deve falar com Docker nem com o endpoint MCP do gateway diretamente. A pagina deve comecar com inventario, configuracao efetiva, disponibilidade e diagnosticos; botoes que alterem containers so entram depois de comprovar um contrato de administracao seguro no ambiente escolhido.

Isto entrega uma experiencia *first-class* para servidores empacotados em imagens sem exigir que o agente implemente a API Docker. A experiencia precisa nomear imagem e digest, origem, politica de tools, privilegios, estado e erros em superficies proprias; **uma URL HTTP generica sozinha nao satisfaz o objetivo**. Tambem nao e necessario que o agente rastreie container IDs para oferecer uma boa integracao: essa responsabilidade pode permanecer no runtime. A distincao entre protocolo, transporte, runtime e plano de controle do relatorio original continua valida [R1].

**Ajuste de prioridade:** o relatorio original propoe `MCPRegistry`, `MCPLifecycleManager`, lazy activation e schema cache antes do gateway [R1, sec. 23 e 33]. Eu inverteria a dependencia: primeiro provar uma conexao real e o contrato operacional/UI; depois introduzir as abstracoes que as falhas medidas exigirem. A configuracao de infraestrutura (Docker Engine/Desktop, host versus Compose, rootless, registry e build) permanece decisao aberta no projeto [L0].

## 1. Evidencia: estado do Percival nesta arvore

| Capacidade ou superficie | Observacao verificavel | Implicacao |
| --- | --- | --- |
| Cliente MCP | `connect_mcp_servers` aceita `stdio`, SSE e Streamable HTTP; faz discovery paginado e registra tools, resources e prompts [L1]. | Reusar o cliente, nao reimplementar MCP. |
| Ciclo de vida existente | `MCPProvider` tem conexoes por servidor, lock de conexao/reload/reconnect, status `connecting/connected/failed`, reload, retry e shutdown no owner async [L1]; ha testes de concorrencia e cleanup [L2]. | Ja ha um nucleo de supervisao. Isto **nao** equivale a lazy startup, cache persistente, idle recycle ou health de container. |
| Startup | O gateway chama `connect()` antes da execucao/descoberta de tools pelo runner [L3]. | Um backend gateway que inicie containers sob demanda pode reduzir o ganho inicial de lazy no agente; medir cold start antes de adicionar cache. |
| Configuracao | `MCPServerConfig` armazena `command/args/env/cwd` ou `url/headers`, `enabled_tools` e `tool_timeout`, sem `image` ou referencia Docker [L4]. | Falta um contrato de integracao containerizada com metadados confiaveis. |
| Preset GitHub | O preset atual usa `command="agent-docker"` com `run -i --rm`, e a UI testa comandos via `shutil.which` [L5]. O Dockerfile inspecionado nao instala explicitamente esse binario [L6]. | O exemplo `command: docker` do relatorio descreve o mecanismo geral, **nao** o preset desta arvore. Sua operabilidade nesta imagem nao foi demonstrada. |
| WebUI MCP | Apps/Settings ja lista presets/custom servers, configura tools, testa conexoes, reconecta e faz hot reload; mostra status da tentativa de conexao [L5, L7]. | Reusar servicos e componentes quando fizer sentido, mas nao confundir estado MCP com estado de container. |
| Pagina KG | O link da sidebar abre outra SPA em `/kg-interface/`; o gateway serve assets e `/kg-interface/api/*` no mesmo origin, com autenticacao [L8]. O bundle KG tem proveniencia propria [L9]. | Referencia boa para **pagina dedicada e acesso autenticado**, nao obrigacao de criar outro frontend/SPA. |
| Deploy em container | `docker-compose.yml` nao traz servico de MCP Gateway nem Docker socket no agente; Dockerfile nao instala a CLI Docker [L6]. | Ainda nao existe deploy integrado dessa capacidade. |
| Rede e segredos | URLs MCP HTTP sao validadas por SSRF; IPs locais/privados requerem `tools.ssrfWhitelist`, hoje uma excecao por CIDR compartilhada com outras ferramentas [L1, L10]. `headers` aceita `${VAR}` resolvido pelo loader [L11]. | Um gateway em loopback/rede Compose requer autorizacao de destino **estreita**, sem liberar uma rede inteira para todo HTTP do agente; token de gateway precisa de provisionamento e rotacao. |

O arquivo de pesquisa [R1] ainda estava nao rastreado no Git durante esta analise; e referencia de trabalho, nao evidencia de implementacao. Nenhum container ou teste de integracao foi executado para este relatorio.

## 2. O que as fontes externas sustentam — e o que nao sustentam

O projeto open source `docker/mcp-gateway` documenta `docker mcp gateway run --port ... --transport streaming` e `--servers`/`--tools` para selecionar superficies; o exemplo Compose monta o socket **no gateway** [E1]. A especificacao de entrada modela `type: server`, `image`, `longLived`, volumes, secrets e `allowHosts` [E2]. A referencia de CLI oferece perfis, catalogos e comandos de administracao (`server enable/disable/inspect`, `profile server add/remove`); perfis podem usar imagens ou entradas locais [E3, E4]. Ha suporte documentado a `--watch`, mas a documentacao de perfis ainda aponta limitacoes de atualizacao dinamica: **nao inferir consistencia imediata para todas as combinacoes** [E3].

**Limite importante para a pagina:** nas fontes consultadas nao foi identificada uma API HTTP administrativa publica/estavel do gateway que permita listar, criar, iniciar, parar, atualizar e inspecionar containers individualmente. `MCP` e sua rota HTTP sao o *plano de dados* (tools/resources/prompts), nao uma API Docker de administracao. `/health` atesta o gateway, nao necessariamente cada servidor [E5]. Os comandos de CLI demonstram administracao possivel no ambiente em que rodam; **nao** sao uma API que se possa invocar do browser nem autorizam executar strings arbitrarias recebidas da UI. Verificar versao e contrato no prototipo antes de prometer controles [E1, E3, E4].

O transporte Streamable HTTP permite um endpoint para multiplas sessoes, mas sua especificacao nao define gerencia de containers [E6]. Para o gateway Docker, autenticar HTTP por Bearer e o padrao; `--allow-unauthenticated` o desliga [E5]. A verificacao de assinatura descrita como default cobre imagens elegiveis do namespace Docker Hub `mcp/`, **nao** imagens de terceiros em geral. Egress nao e negado globalmente por padrao: `disableNetwork`, `allowHosts` e politicas do gateway precisam ser configurados e testados [E5]. Pin por digest e uma propriedade de proveniencia/reprodutibilidade, nao uma assinatura por si so [E2, E5].

As paginas de Docker Desktop/MCP Toolkit e de Docker AI Governance devem ser distinguidas do binario open source instalavel separadamente no Docker Engine: a pagina Docker AI Governance menciona disponibilidade comercial especifica, ao passo que documenta a instalacao manual do plugin no Engine [E7]. Nao pressupor Desktop, feature flags, secret store ou endpoints identicos em todos os modos de instalacao.

## 3. Arquitetura recomendada e limites de autoridade

```text
WebUI Percival: /mcp-containers
        | leituras e comandos humanos autenticados (API propria)
        v
Gateway Python do Percival ----> estado de configuracao + MCPProvider
        |
        | MCP HTTP autenticado (plano de dados, endpoint privado e restrito)
        v
Docker MCP Gateway --------> Docker daemon --------> imagens/containers MCP
        ^
        | plano de controle (somente se existir integracao verificada)
Servico operacional restrito / CLI do host / reconciliador externo
```

- **Gateway Python do Percival:** dono de configuracao efetiva, identidade logica dos MCPs, filtro de tools, autorizacao da UI, read models e reconciliacao com o `MCPProvider`; WebUI/TUI continuam clientes, conforme `AGENTS.md` [L12]. Nao expor `docker.sock` nem CLI Docker ao agente/exec tool como efeito colateral da nova pagina.
- **Docker MCP Gateway:** dono de catalogo/perfil efetivo, imagem/container, mounts, rede, limites e credenciais por servidor. A permissao de acessar o daemon continua poderosa e deve ficar confinada ao componente operacional; gateway comprometido ainda representa risco ao host [E1, E5].
- **Plano de controle da UI:** se houver mudancas de perfil/imagem ou operacoes sobre containers, um servico restrito pode usar CLI/API documentada e pinada **fora do processo do agente**, com operacoes tipadas e nomes autorizados. Este componente so sera implementado depois de provar que e necessario e como ele autentica, registra resultados, limita parametros e reconcilia estado; nao passar comandos Docker arbitrarios do frontend. Uma alternativa viavel para a primeira entrega e configuracao operacional externa mais pagina observacional.
- **Origem da verdade:** o runtime e autoritativo para container e imagem executados; o Percival e autoritativo para tools habilitadas ao modelo; a configuracao declarada identifica o que *deveria* existir. A UI deve exibir divergencias, nao inventar `running` a partir de `connected`.

**Questao de multiplexacao:** um gateway pode anunciar tools de varios servidores sob **uma** conexao MCP. Hoje o Percival prefixa wrappers pelo nome da conexao (`mcp_<nome>_<tool>`) [L1]. Nao assumir que `runtime.gateway.server` do exemplo em [R1] vira automaticamente um endpoint, processo ou namespace por imagem. O prototipo precisa verificar nomes retornados, colisoes, filtragem por servidor, mudancas de inventario e semantica de recarga; so entao definir o mapeamento estavel da UI e do `enabledTools`. Um gateway com **uma imagem** torna esse primeiro teste inequivoco; ampliar para varias imagens e um gate separado.

### Contrato de dados minimo (proposta, nao schema existente)

Manter `tools.mcpServers` compativel para comandos/URLs legados. Adicionar metadados tipados, por exemplo uma secao `tools.mcpDocker` **associada por ID estavel a uma entrada MCP gateway**, apenas quando validada a necessidade; nao gravar `image` em `MCPServerConfig` como se o cliente MCP fosse o dono do runtime. A forma final depende do modo de deploy e do contrato efetivo do gateway.

O read model do backend pode distinguir: `server_id`, `gateway_id`, `source` (catalogo/perfil), `declared_image` e digest quando conhecidos, `connection_status` (Percival), `gateway_status`, `runtime_status` **somente quando observavel**, `last_checked_at`, `tools_discovered`, `tools_enabled`, `auth_configured` (booleano) e `error_code` redigido. Campos nao observaveis devem ser `unknown`/ausentes, sem inferir IDs ou uptime de containers. Nunca retornar valores de token, secrets ou mounts sensiveis para o browser. Cada imagem, servidor de catalogo e conexao MCP precisa de identidade distinta.

## 4. Interface: pagina dedicada, sem duplicar a arquitetura KG

**Concordo com a pagina dedicada:** o espaco operacional de imagens, politicas, estado e tools nao cabe confortavelmente no modal MCP atual. Recomendo inicialmente **uma rota/pagina dentro da WebUI React existente** (sugestao: `/mcp-containers`), acessivel na navegacao do Percival e por um link contextual em Apps > MCP. A SPA KG separada tem origem e ciclo de build proprios; duplicar esse arranjo acrescentaria bundle, roteamento, autenticacao e testes sem evidencia de ganho para esta funcionalidade [L8, L9, L13]. Reutilizar a integracao ao gateway e o visual, nao copiar o mecanismo de empacotamento da KG.

| Area da pagina | Primeira entrega | Dependencia para avancar |
| --- | --- | --- |
| Visao geral | Gateway configurado/atingivel, contagem de servidores declarados, conexoes MCP e ultimas verificacoes, com estados separados. | Read model no gateway Python, sem chamada direta do browser ao gateway Docker. |
| Lista e detalhe | Nome, origem da entrada, imagem@digest declarada, capabilities, tools ativas, e status conhecido/desconhecido; erro redigido e horario da observacao. | Relacionar config declarada e tools descobertas sem supor namespaces. |
| Diagnostico | Acao de testar handshake/discovery ja existente, resposta curta diferenciando `gateway indisponivel`, `auth`, `MCP handshake`, `imagem/servidor` quando comprovado. | Observabilidade do gateway e categorizacao de erros; `/health` isolado nao prova container funcional. |
| Politica de tools | Mostrar filtro em vigor e reutilizar alteracao de `enabledTools` existente quando mapeamento for confiavel. | Respeitar tanto allowlist do gateway quanto do Percival (intersecao efetiva). |
| Operacoes | `habilitar`, `desabilitar`, `atualizar imagem`, `reiniciar` ou `remover` **somente** quando o backend escolhido puder declarar semantica e verificar estado posterior. | Plano de controle restrito, origem de verdade, autorizacao humana e teste de rollback. |

A UI precisa distinguir **configured / gateway reachable / MCP connected / container running** e nunca apresentar um `docker run` generico como servidor gerenciado. Nomes, status e ultimo erro nao devem atualizar implicitamente a configuracao ao simples carregar a pagina. Em falhas, manter o inventario declarado visivel. Confirmacoes proporcionais a mudancas destrutivas e indicacao de qual servidor sera afetado ajudam a evitar que a acao em um gateway multiplex desligue tools de outros servidores. Filtros, empty/loading/error states, labels acessiveis e versao mobile/rail sao criterios para a pagina dedicada; manter Settings/Apps para cadastro generico de MCPs [L7, L13].

**Autorizacao:** reutilizar autenticacao e superficie de mutacoes do gateway WebUI [L8, L14]; explicitar privilegio humano para alterar a configuracao/runtime, em vez de tornar controle de container uma tool oferecida ao modelo. Testar acesso nao autenticado e caminhos de navegador/reverse proxy. Como a WebUI e servida no mesmo origin, nao ha necessidade de passar o Bearer do Docker MCP Gateway ao JavaScript. A pagina KG usa autenticacao em `/kg-interface/api/*`, mas seus endpoints especificos de grafos nao devem virar um proxy Docker [L8].

## 5. Sequencia de trabalho e gates

| Etapa | Entrega e responsavel recomendado | Evidencia para passar ao proximo gate |
| --- | --- | --- |
| D0 — decisao de ambiente | Operador define host Linux ou container/Compose para prototipo, Engine/Desktop, instalacao do gateway, tipo de segredo, imagem de teste sem credencial e politica de rede. Agente registra matriz de decisoes e riscos. | Runtime escolhido e versoes registradas; escopo do experimento definido. |
| P1 — prova de dados | Agente configura **um** servidor MCP de imagem pinada e gateway externo, sem Docker socket no processo/container Percival; valida auth, SSRF, tool discovery/chamada e falha/reconexao/shutdown. | Comando/versao/digest/config anonimizados, resultados repetiveis; testes negativos para token ausente e endpoint privado nao autorizado; latencia de cold start registrada. |
| P2 — pagina observacional | Agente implementa rota React e API de leitura no backend, distinguindo estados e `unknown`; aproveita status/reload/test existentes e adiciona apenas metadados validados. | UI lista servidor com imagem/proveniencia, estado MCP e erro redigido; testes de backend para auth/projecao e teste frontend de comportamento; browser sem socket/token do gateway. |
| P3 — gerencia validada | Administracao pela UI e requisito da entrega completa: o agente verifica operacoes/versao do gateway e implementa o plano de controle restrito, ou demonstra a limitacao e propoe backend alternativo para decisao. | Habilitar/desabilitar um servidor afeta apenas o selecionado; confirmacao, autorizacao, resultado, reconciliacao e rollback demonstrados; segredo nao vaza em logs/erros. |
| P4 — varios servidores e release gate | Agente valida multiplexacao, colisoes, segregacao de secrets, fontes e tool allowlists, atualizacao por digest, persistencia, rollback e empacotamento Linux. | Testes de integracao Docker no CI/gate proprio, alem de `pytest`, `basedpyright nanobot`, `ruff check .` e testes/build WebUI afetados [L12]; aval do operador no SHA candidato antes de release. |

**Cenario falsificador do desenho proposto:** se o gateway nao preservar um mapeamento estavel de tools/servidores sob mudancas de perfil ou nao permitir gerenciamento por servidor com isolamento suficiente para a UI, comparar (i) multiplos gateways, um por dominio de politica, (ii) controle de perfil externo com pagina somente observacional, e (iii) runtime Docker interno. Adotar (iii) somente quando um requisito concreto nao couber em (i)/(ii) e o custo de manutencao/seguranca for justificado. Nao prometer `start/stop` individual antes dessa prova.

## 6. Riscos e questoes ainda abertas

1. **Excecao SSRF ampla:** `tools.ssrfWhitelist` e global [L10]. Precisa de autorizacao de destino MCP especifica para gateway, vinculada a endpoint e validada em cada request/redirect, ou de outro transporte testado. Isto nao deve virar uma liberacao generica de toda a rede Compose.
2. **Gateway e controle privilegiados:** se o gateway/operador usar o Docker socket, a separacao protege o agente de acesso direto, mas nao torna o gateway inofensivo. Escopo de acesso, isolamento de rede, identidade do processo, mounts e tratamento de configuracao precisam de revisao no ambiente escolhido [E5].
3. **Credenciais e proveniencia:** Bearer da conexao Percival->gateway e secrets dos servidores sao coisas diferentes. Resolver e rotacionar sem persistir valores no browser; registrar digest/origem/licenca e nao atribuir verificacao criptografica a imagens de terceiros sem prova [E2, E5, L11].
4. **Divergencia entre config, gateway e UI:** definir quem pode editar perfis e como detectamos edicoes fora da UI. O `--watch` existe, mas o comportamento por modo/perfil necessita teste [E1, E3].
5. **Estado ambiguo:** `connected` significa sessao MCP ativa; `healthy`, `running` e `ready for tool call` sao sinais diferentes. Em container sob demanda (`longLived: false`), `not running` pode ser normal [E2].
6. **Empacotamento e produto:** Percival e Linux-only, mas o CI geral e o empacotamento herdado ainda precisam reconciliacao [L0, L12]. Nao vincular o novo gate ao release 0.1.0 ate concluir o escopo de suporte e a validacao no SHA exato.

**Proxima decisao solicitada ao operador antes de codificar:** qual e o ambiente de referencia para P1 (Percival no host ou em container/Compose) e quais acoes administrativas sao obrigatorias na primeira versao utilizavel da pagina. A recomendacao tecnica e **P1 no ambiente alvo real, pagina observacional em P2 e controles comprovados em P3**; P2 e um marco intermediario, nao o fechamento do objetivo de administracao grafica.

## Fontes e rastreabilidade

**Local (inspecionado em 2026-10-06):**

- [L0] [Brief de projeto](../../.positronic/PROJECT.md), linhas 3-21, 27-48; [governanca](../percival-governance.md), linhas 33-60.
- [L1] [`nanobot/agent/tools/mcp.py`](../../nanobot/agent/tools/mcp.py), linhas 1010-1349, 1373-1708; normalizacao de nomes nas linhas 177-199 e 1161-1195.
- [L2] [`tests/agent/test_mcp_connection.py`](../../tests/agent/test_mcp_connection.py), linhas 119-159, 317-455, 658-719.
- [L3] [`nanobot/cli/gateway_runtime.py`](../../nanobot/cli/gateway_runtime.py), linhas 56-64, 478-502.
- [L4] [`nanobot/config/schema.py`](../../nanobot/config/schema.py), linhas 364-377, 421-422.
- [L5] [`nanobot/webui/mcp_presets_api.py`](../../nanobot/webui/mcp_presets_api.py), linhas 407-439, 707-735, 948-1016, 1103-1229, 1632-1697.
- [L6] [`Dockerfile`](../../Dockerfile), linhas 11-15, 39-50; [`docker-compose.yml`](../../docker-compose.yml), linhas 1-62.
- [L7] [`McpManagementDialog.tsx`](../../webui/src/components/settings/system/McpManagementDialog.tsx), linhas 27-106, 195-262; [`settings_routes.py`](../../nanobot/webui/settings_routes.py), linhas 93-103, 145-185; [`settings_system.py`](../../nanobot/webui/settings_system.py), linhas 1003-1030.
- [L8] [`PercivalSidebar.tsx`](../../webui/src/components/percival/PercivalSidebar.tsx), linhas 39-79, 116-150; [`kg-interface.ts`](../../webui/src/lib/kg-interface.ts), linhas 1-40, 70-85; [`ws_http.py`](../../nanobot/webui/ws_http.py), linhas 600-622; [`kg_static.py`](../../nanobot/webui/kg_static.py), linhas 15-66.
- [L9] [`nanobot/web/kg-interface/SOURCE.json`](../../nanobot/web/kg-interface/SOURCE.json); [`THIRD_PARTY_NOTICES.md`](../../THIRD_PARTY_NOTICES.md), linhas 24-27.
- [L10] [`nanobot/security/network.py`](../../nanobot/security/network.py), linhas 16-76, 78-151; [`nanobot/agent/tools/mcp.py`](../../nanobot/agent/tools/mcp.py), linhas 1043-1052, 1122-1141.
- [L11] [`nanobot/config/loader.py`](../../nanobot/config/loader.py), linhas 192-215, 244-283.
- [L12] [`AGENTS.md`](../../AGENTS.md), linhas 12, 27-31, 33-54; [governanca](../percival-governance.md), linhas 33-55.
- [L13] [`webui/src/App.tsx`](../../webui/src/App.tsx), linhas 13-17, 141-156; [`AppsSettings.tsx`](../../webui/src/components/settings/system/AppsSettings.tsx), linhas 188-215; [origem KG](../../nanobot/web/kg-interface/SOURCE.json).
- [L14] [`settings_routes.py`](../../nanobot/webui/settings_routes.py), linhas 153-185, 215-216; [`ws_http.py`](../../nanobot/webui/ws_http.py), linhas 600-616.
- [R1] [Relatorio de pesquisa inicial](PERCIVAL_MCP_DOCKER_RESEARCH_REPORT.md), secoes 1, 23-35.

**Externas (documentacao primaria consultada em 2026-10-06; links para `main` podem mudar, conferir versao pinada no prototipo):**

- [E1] [docker/mcp-gateway: funcionamento e Compose](https://github.com/docker/mcp-gateway/blob/main/docs/mcp-gateway.md).
- [E2] [Docker MCP Server Entry Specification](https://github.com/docker/mcp-gateway/blob/main/docs/server-entry-spec.md).
- [E3] [Docker MCP Profiles](https://github.com/docker/mcp-gateway/blob/main/docs/profiles.md); verificar limitacoes por modo/versao.
- [E4] [Referencia gerada: `gateway run`](https://github.com/docker/mcp-gateway/blob/main/docs/generator/reference/mcp_gateway_run.md), [comandos `server`](https://github.com/docker/mcp-gateway/blob/main/docs/generator/reference/mcp_server.md), [Docker Docs: CLI](https://docs.docker.com/ai/mcp-catalog-and-toolkit/cli/).
- [E5] [Docker MCP Gateway security model](https://github.com/docker/mcp-gateway/blob/main/docs/security.md).
- [E6] [Especificacao MCP 2025-06-18: transports](https://modelcontextprotocol.io/specification/2025-06-18/basic/transports).
- [E7] [Docker Docs: MCP Gateway, distribuicao e instalacao manual](https://docs.docker.com/ai/mcp-catalog-and-toolkit/mcp-gateway/).
