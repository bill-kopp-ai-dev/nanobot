# Percival: portabilidade da estrategia MCP Docker do Positronic

**Data:** 2026-10-06. **Natureza:** analise de arquitetura; nenhum runtime, container ou interface foi implementado ou testado no Percival nesta etapa.

**Conclusao:** **sim, podemos adaptar o modelo de produto e boa parte do desenho do Positronic ao Percival; nao recomendo copiar o executor TypeScript nem inserir `docker run` diretamente no processo Python do agente como arquitetura de producao.** A implementacao vigente do Positronic e o **broker proprio de imagens locais e `stdio` (ADR 0004-ter)**, nao o plano historico F5 baseado no Docker MCP Gateway [P1-P3]. Seu contrato de instalacao, ativacao, escopo, allowlist, transicoes auditaveis e administracao grafica e particularmente relevante para a pagina que o operador quer no Percival. O executor precisa ser escolhido mediante um teste de isolamento e custo operacional: gateway externo se seus controles bastarem; broker restrito separado se controle individual, imagem local e perfis de acesso exigirem mais. A pagina e os modelos de dominio podem ser projetados para ambas as alternativas.

Este documento **complementa e qualifica** o [parecer anterior](2026-10-06-percival-docker-mcp-architecture-and-ui.md), que recomendava prototipar primeiro o Docker MCP Gateway antes de examinar o broker funcional do Positronic. A prioridade de prova passa a ser comparar as duas alternativas no ambiente alvo, sem declarar uma delas pronta para release por inferencia.

## 1. O que esta efetivamente demonstrado

| Item | Evidencia | Limite da evidencia |
| --- | --- | --- |
| Decisao atual | ADR 0004-ter substituiu 0004-bis: Docker Engine/CLI, `docker run --pull=never`, `stdio`; plugin `docker mcp`, Docker Desktop e catalogo OCI nao participam do caminho de invocacao [P1]. | F5 continua em documentos/codigo de leitura e nao deve ser confundido com o executor atual. |
| Bench F2.1 | Quatro servidores (AgentMail, Khan, Deep Research, Notes) fizeram `initialize`, `tools/list` e chamada real em sessao Positronic; redes e mounts distintos foram exercitados [P4]. | Bench datado de 2026-09-30, **anterior** a reinstalacao limpa em schema v2; nao prova os quatro servidores no fluxo v2/TUI atual. O nome "Percival Bench" designa um teste **no Positronic**, nao integracao no Percival. |
| Estado v2 | Plano registra implementacao e smoke com imagem local sem push, testes de dominio/API/TUI; transicoes de escopo tiveram teste isolado com quatro imagens e rollback [P2, P5]. | Aceite manual completo da TUI e reconexao em sessao ativa com os quatro servidores ainda constam pendentes [P2, P5]. Os testes nao foram reexecutados nesta analise. |
| Codigo presente | `ManagedServers` implementa registry v2, inspecao da imagem, comando Docker, status, autorizacao por tool, audit trail e preview/apply com snapshot e journal; `activeConfigs` injeta comando no cliente MCP do OpenCode; `McpCatalog.convertTool` checa autorizacao antes da chamada [P6-P8]. | Leitura estatica no checkout `source/opencode` em `2c113ba68`. Presenca de implementacao nao comprova isolamento do daemon, confiabilidade em crash nem adequacao ao Python. |

O [relatorio estrategico F2.1/F5](../../../alternative-positronic/positronic/docs/reports/POSITRONIC_MCP_STRATEGY_REVIEW_2026-10-01.md) explica por que o Positronic mudou de direcao; e uma **fotografia anterior** a ADR 0004-ter e a v2. Ja o arquivo de [capabilities geradas](../../../alternative-positronic/positronic/docs/capabilities/mcp-docker.md) ainda enumera capacidades legadas de catalogo/profile F5 ao lado de `server.manage`: nao tomar essa lista isolada como prova de que o plugin esta no caminho de invocacao [P1-P3].

## 2. Mapeamento para o Percival

| Estrategia Positronic | Adocao proposta no Percival | Adaptacao/condicao |
| --- | --- | --- |
| Inventario tipado (`server_id`, fonte `local-image` ou `pinned-image`, revisao) separado de configuracao operacional [P2, P6] | **Adotar o conceito.** Metadados confiaveis por servidor permitem inventario e pagina dedicada, sem confundir uma entrada MCP generica com container gerenciado. | Manter `tools.mcpServers` e presets existentes para MCP generico; criar camada de dominio propria para MCP Docker. Nao inferir gerenciamento de `command: docker` arbitrario. Comecar pequeno e migrar apenas entradas explicitamente cadastradas. |
| Instalacao desativada, `allowedTools: []`, ativacao/configuracao/disponibilidade independentes [P2, P6] | **Adotar cedo.** Registro isolado nao publica tools; descobrir, revisar e habilitar sao etapas distintas. | Hoje `MCPServerConfig.enabled_tools` tem default `["*"]`, que habilita todas as capabilities, inclusive resources/prompts [L1, L2]. A camada gerenciada deve derivar allowlist explicita; falhar fechado em config invalida. |
| Identidade da imagem: ID local `sha256:<64 hex>` ou OCI `nome@sha256:<digest>`, `docker image inspect`, `--pull=never` [P1, P6] | **Adotar com tipagem distinta.** Permite imagem construida localmente sem publicar catalogo. | ID local e RepoDigest nao sao intercambiaveis e o ID so tem significado operacional no Engine que possui a imagem; pin evita substituicao por tag mas **nao** valida assinatura/licenca. Build/pull/update devem ser atos separados. |
| `stdio` direto, uma conexao por servidor, `--rm --interactive`, rede/mounts tipados [P4, P6] | **Aproveitar compatibilidade do cliente**, que ja inicia `stdio` e mantem uma conexao por servidor, reconectando e recarregando [L1]. | O comando Docker no mesmo processo/usuario do agente exporia o daemon tambem a ferramentas de shell; o guard de workspace nao e sandbox de processo [L3]. Servico isolado ou outro plano de execucao e condicao de producao. |
| Escopo Global/Local por projeto, perfis e secrets separados; gate no discovery e em cada chamada [P1-P3, P7, P8] | **Adotar como politica quando houver identidade de projeto confiavel.** Em principio da para aplicar politica antes do registro e em `MCPToolWrapper.execute`, inclusive com schema em cache. | Percival tem `ToolRegistry` global e `MCPProvider` configurado por `tools.mcpServers`, nao o `InstanceState` por diretorio do OpenCode [L1, L2, L4]. Identificar o projeto de **cada chamada** (WebUI, CLI, cron/subagente) e testar revogacao sem reinicio; se nao houver contexto confiavel, iniciar sem escopo Local, nao mapear projetos por nome de pasta. |
| Preview/apply de mudanca de escopo com fingerprint, confirmacao de mounts, revisao, idempotencia, snapshot e journal [P1, P5, P6] | **Adotar na fase de mudancas multi-projeto.** Excelente padrao para evitar promocao acidental de dados locais ao global. | Nao trazer o aparato de transicao inteira no primeiro servidor de escopo unico. Ao implementar, bloquear chamadas durante `preparing/failed`, validar recovery apos crash e auditar antes/depois de cada mutacao. |
| TUI de gestao + API tipada com credencial `operator-admin` separada [P2, P5] | **Adaptar para a pagina React/WebUI do Percival** e uma unica API de dominio no gateway Python. Pagina dedicada continua recomendada; reutilizar auth/navegacao WebUI existente. | Percival autentica mutacoes WebUI por WebSocket allowlisted [L5], mas autenticacao de WebUI nao prova papel de administrador do Docker. Novo gate de operador no backend, inclusive contra sessao remota valida, antes de chamar plano operacional. Nunca entregar socket, token operacional ou secrets ao browser/modelo. |

### Diferencas de runtime que impedem um port literal

1. O Positronic injeta `activeConfigs(projectPath)` no MCP do OpenCode; em Percival, o ponto de composicao e `MCPProvider.from_config`/`connect_mcp_servers` e o ciclo de vida usa task owner do SDK Python [P7, L1]. Implementar um **adaptador Python** entre registro gerenciado e `MCPServerConfig`/provider, preservando reload/reconnect e ownership async; nao duplicar cliente MCP.
2. A allowlist do Percival filtra na descoberta, e `MCPToolWrapper.execute` chama a sessao sem um gate gerenciado por chamada [L1, L2]. Retirar um servidor via hot reload nao e equivalente a revogar a proxima invocacao ja capturada por outra tarefa. Introduzir verificacao imediatamente antes do `call_tool` (e antes da publicacao por contexto), com testes de desativacao, revogacao, reconnect e paths alternativos de execucao [L4].
3. Nomes expostos em Percival sao `mcp_<conexao>_<tool>`; a allowlist aceita tanto nome bruto como envelopado [L1]. Persistir a politica por **ID da instalacao + nome bruto da tool**, resolver nomes envelopados somente na borda e testar colisoes de nomes sanitizados; um gateway multiplex exigiria ainda origem de cada tool.
4. O Positronic assume registro de projetos e configs por projeto; Percival nao deve copiar `$POSITRONIC_HOME`, `projectKey`, formato JSON/Effect/Bun nem superficies TUI como dependencias. Reusar criterios, nao estado privado, credenciais ou codigo sem revisar licencas e proveniencia.

## 3. Comparacao de executores para o produto

| Criterio | Gateway Docker MCP externo (parecer anterior) | Broker ao estilo Positronic |
| --- | --- | --- |
| Integracao MCP inicial | Um endpoint MCP, possivelmente multiplexado; testar namespace e filtro por servidor. | `stdio` individual ja aceito pelo Percival; mapeamento servidor/tool direto. |
| Administracao grafica individual | CLI/perfis existem, mas nao foi comprovada API HTTP administrativa estavel nem controle `start/stop` por container [R1]. Requer plano de controle testado. | Dominios e comandos tipados sob controle proprio; oferece semantica natural para instalar/ativar/desativar/atualizar/excluir **registro**. `--rm` nao equivale a container persistente. |
| Imagem local/credenciais | Capacidade depende de catalogo, modo do gateway e isolamento efetivo das credenciais: ensaiar antes de prometer. | ID local + inspecao + mount por perfil ja demonstrados no Positronic [P2, P4, P6]. |
| Fronteira Docker | Socket no gateway externo, fora do processo Percival; privilegiado permanece o gateway. | Injecao literal de `command: docker` no processo Percival **nao isola** o daemon do shell do agente. Isolar o broker em componente/usuario/container distinto custa engenharia de transporte/autorizacao e deploy. |
| Custo e dependencia | Menos codigo proprio para gerenciar containers; depender do comportamento/versao do plugin e de seus controles demonstrados. | Mais controle e sem plugin Docker MCP; manutencao propria de ciclo de vida, lock, estado, logs e ponte MCP. |

**Recomendacao condicional:** para satisfazer pagina administrativa por servidor, **preferir o modelo de dominio do Positronic**. Executar P1 como comparacao pequena: (a) um gateway externo e (b) broker direto **somente em ambiente isolado de experimento**, com uma imagem de teste sem segredo e sem dar socket Docker ao deployment real do Percival. Se o gateway provar administracao individual e isolamento de credenciais com contrato versionado, ele pode continuar como executor. Se nao, especificar um **broker operacional separado** com API restrita por ID/operacao e transporte MCP apropriado (por exemplo, uma ponte `stdio`↔HTTP autenticada), em vez de simplesmente chamar a CLI Docker no gateway Python. A ponte e trabalho novo, nao componente ja provado no Positronic/Percival. Uma arquitetura capaz de controlar servidores individualmente **sem** separar o daemon do agente so pode ser aceita como excecao explicita de risco, nao como equivalencia de seguranca.

## 4. Cuidados encontrados na leitura estatica do codigo Positronic

- `ManagedServers.status()` pode retornar `ready` apos validar imagem, mounts e allowlist; **nao prova handshake MCP nem container em execucao** [P6]. Na pagina Percival, manter separadas disponibilidade declarada, conexao MCP, ultima chamada e estado Docker observado.
- `effective()` usa `Promise.allSettled` e omite candidatos que falharam [P6]. Para operacao grafica, manter erros/instalacoes pendentes no read model em vez de fazer servidores desaparecerem da lista.
- O lock com arquivo exclusivo e remocao de lock orfao por PID/idade e uma implementacao propria [P6]. Nao copiar sem analisar corrida entre verificacao e remocao, PID reutilizado e testes de crash/concorrencia no filesystem alvo. Snapshot + rename de varios arquivos tambem nao e transacao unica com Docker.
- `command()` limita rede a `none|bridge|host` e fornece mounts por argumentos tipados [P6]. Validacao da existencia/leitura de um path nao substitui uma politica de quais paths podem ser montados, nem permissao no container; `host` e mounts gravaveis precisam de decisao explicita. Para o Percival, a autorizacao tem de residir no backend e valer igualmente para UI e CLI.
- `authorize()` revalida imagem, estado e allowlist e registra resultado antes da chamada [P6-P8]. Esse padrao e valioso; a trilha de auditoria deve evitar argumentos/respostas/segredos. Em mutacoes de multiplos arquivos, a auditoria final e a recuperacao apos falha merecem teste separado antes de atribuir semantica transacional.

## 5. Plano de validacao minimo que decide a transferencia

| Gate | Prova que suporta a escolha | Resultado que enfraquece a escolha |
| --- | --- | --- |
| T0 — ambiente | Operador confirma host Linux ou Compose, rootless/rootful, onde roda Docker CLI/socket e quais acoes a pagina precisa na primeira versao. Inventario nao toca o estado pessoal de outro projeto. | Sem forma de isolar o daemon e com `docker run` direto requerido em producao: broker literal rejeitado. |
| T1 — chamada real | Uma imagem local identificada por ID completo, `--pull=never`, sem credencial; `initialize`, `tools/list`, chamada, desativacao e reconnect medidos no mesmo Percival, preservando MCPs legados. | Falha de `stdio` no deploy real ou reconexao que republica tool revogada. |
| T2 — gate de politica | Registro inicia desativado, tools vazias; liberacao explicita de uma tool; chamada concorrente apos revogacao negada; auth da pagina diferencia operador de usuario WebUI remoto. | Recurso/prompt ou chamada por outro caminho atravessa a politica; browser ou agente recebe acesso ao Docker/socket. |
| T3 — executor e UI | Pagina lista declarado, pendente, connected e erro separadamente; administracao de um servidor nao afeta os demais; update exige imagem pinada, confirma alcance e mostra rollback. Comparar gateway e broker separado pelo mesmo contrato. | Backend nao oferece controles individuais verificaveis; UI passa a apresentar estado inferido como observado. |
| T4 — release | Integracao Docker automatizada em CI Linux apropriado + `pytest`, `basedpyright nanobot`, `ruff check .` e verificacao WebUI no SHA candidato [L6]. | Apenas smoke do Positronic ou teste manual isolado: nao fecha gate Percival. |

**Proxima decisao do operador:** escolher o ambiente alvo de T0 e enumerar as operacoes obrigatorias da pagina (por exemplo instalar imagem local, ativar/desativar, editar rede/mounts/tools, atualizar, excluir registro). Esses dois fatores determinam se vale validar apenas o gateway ou construir um broker separado. Nenhuma migracao de estado Positronic para Percival e implicita.

## Referencias

**Positronic (outro repositorio, leitura em 2026-10-06):**

- [P1] [ADR 0004-ter](../../../alternative-positronic/positronic/docs/decisions/0004-ter-mcp-local-broker.md), secoes Decisao e Consequencias.
- [P2] [Plano MCP v2](../../../alternative-positronic/positronic/docs/plans/POSITRONIC_CAPABILITY_MCP_PLAN.md), secs. 1, 3-6 e 8; status/pendencias nas linhas 3-8 e 212-233.
- [P3] [`AGENTS.md` Positronic](../../../alternative-positronic/positronic/AGENTS.md), linhas 14-33 (decisao vigente versus F5).
- [P4] [Percival Bench no Positronic](../../../alternative-positronic/positronic/docs/plans/POSITRONIC_MCP_PERCIVAL_BENCH_EXECUTION.md), secs. Resultado, Credenciais e dados, Integracao e observacao.
- [P5] [Transicoes de escopo: plano e execucao](../../../alternative-positronic/positronic/docs/plans/POSITRONIC_CAPABILITY_MCP_SCOPE_TRANSITION_PLAN.md), secs. 4, 6-7 (pendencia nas linhas 143-154).
- [P6] [`managed.ts`](../../../alternative-positronic/source/opencode/packages/positronic-mcp-docker/src/managed.ts), linhas 63-83, 150-185, 218-396, 539-634, 670-711, 748-785; [`schema.ts`](../../../alternative-positronic/source/opencode/packages/positronic-mcp-docker/src/schema.ts), linhas 3-53.
- [P7] [`service.ts`](../../../alternative-positronic/source/opencode/packages/positronic-mcp-docker/src/service.ts), linhas 388-397; [integracao MCP OpenCode](../../../alternative-positronic/source/opencode/packages/opencode/src/mcp/index.ts), linhas 663-768.
- [P8] [`catalog.ts`](../../../alternative-positronic/source/opencode/packages/opencode/src/mcp/catalog.ts), linhas 42-86.

**Percival (checkout `a3876207`):**

- [L1] [`mcp.py`](../../nanobot/agent/tools/mcp.py), linhas 612-645, 1010-1150, 1162-1217, 1373-1415, 1550-1708.
- [L2] [`schema.py`](../../nanobot/config/schema.py), linhas 364-377, 387-422.
- [L3] [Fronteiras de seguranca](../../.agent/security.md), secs. Workspace Restriction e Shell Sandbox.
- [L4] [`registry.py`](../../nanobot/agent/tools/registry.py), linhas 19-51, 86-108, 187-201.
- [L5] [`ws_http.py`](../../nanobot/webui/ws_http.py), linhas 485-545; [parecer WebUI](2026-10-06-percival-docker-mcp-architecture-and-ui.md), sec. 4.
- [L6] [`AGENTS.md`](../../AGENTS.md), linhas 12, 33-55.
- [R1] [Parecer anterior sobre Gateway, controles e fontes externas](2026-10-06-percival-docker-mcp-architecture-and-ui.md), secs. 2-5.
