# Plano inicial de execução — MCP Docker first-class no Percival

- **Data / revisão:** 2026-10-06 / v0.1 (proposta para discussão).
- **Estado:** planejamento; nenhuma fase deste plano foi iniciada ou validada no Percival. O número v0.1 identifica **este plano**, não uma versão lançada do produto.
- **Objetivo:** instalar e administrar servidores MCP empacotados em imagens Docker por uma página dedicada na WebUI, com descoberta e chamada de tools pelo agente, identidade de imagem verificável, política explícita, diagnóstico e operações de ciclo de vida compreensíveis.
- **Bases:** [análise da arquitetura e UI](../reports/2026-10-06-percival-docker-mcp-architecture-and-ui.md), [comparação com o Positronic](../reports/2026-10-06-percival-positronic-docker-mcp-transfer-assessment.md), [pesquisa inicial](../reports/PERCIVAL_MCP_DOCKER_RESEARCH_REPORT.md), [regras do Percival](../../AGENTS.md) e [governança](../percival-governance.md). A comparação mais recente qualifica a preferência pelo Docker MCP Gateway no primeiro parecer.
- **Responsáveis propostos:** operador decide ambiente, operações indispensáveis, política de acesso e aceite; agente implementa provas, backend, UI, testes e documentação, após as decisões correspondentes. Não há prazo nem orçamento aprovados; reestimar após F1.

## 1. Resultado esperado e limites

**Critério de aceite da capability:** no Linux suportado, um operador autorizado consegue cadastrar uma imagem presente/identificada, configurá-la, descobrir e liberar tools explicitamente, ativar, inspecionar status/erros, desativar e retirar o **registro** de um servidor pela página; o agente chama apenas as tools permitidas e perde esse acesso na próxima chamada após revogação. Os servidores MCP genéricos existentes continuam utilizáveis. Imagem, dados montados e secrets do host **não** são apagados ao retirar um registro. O significado de atualizar imagem, reiniciar e gerenciar containers persistentes será decidido em Q2/Q7; não apresentar esses controles como implementados sem teste operacional.

**Limites iniciais propostos, reversíveis:** uma imagem de teste sem segredo e um servidor na prova F1; experiência primeiro observacional em F3, depois mutações reais em F4. A primeira entrega funcional **inclui F4**: só a página de leitura não completa a administração pedida. Não antecipar migração de entradas MCP legadas, Global/Local por projeto, catálogos OCI, distribuição de imagens, assinatura, OAuth compartilhado nem criação de nova SPA sem uma necessidade validada. Essas possibilidades ficam nas questões em aberto, não como funcionalidades já descartadas do produto.

**Fronteiras mantidas:** o gateway Python é dono de execução, registro de tools, estado lógico e política; WebUI/TUI são clientes. A UI não fala com Docker nem injeta comandos arbitrários. O agente e sua ferramenta shell não devem receber `docker.sock` ou acesso equivalente ao daemon como consequência da nova capability. O componente com acesso ao daemon também requer controle de privilégio; separá-lo do agente reduz uma superfície, não torna Docker inofensivo. Suporte de release: Linux somente.

## 2. Hipótese arquitetural e decisão de executor

**Hipótese de trabalho (não decisão final):** reaproveitar do Positronic o **modelo de domínio** (instalação desativada, imagem local por ID ou referência OCI por digest, configuração separada, allowlist e estado efetivo), escrito para o gateway Python do Percival; comparar dois executores sob o mesmo contrato de administração:

| Candidato | Prova indispensável antes de escolher | Condição para rejeitar ou replanejar |
| --- | --- | --- |
| Docker MCP Gateway externo | Transporte MCP, imagem local/pin, segregação de secrets, mapeamento de tools por servidor e operações administrativas individuais demonstradas numa versão fixada, com daemon fora do processo do agente. | Só entrega multiplex/CLI sem controle isolável por servidor necessário à UI, ou depende de exceção SSRF ampla. |
| Broker restrito separado, inspirado no Positronic | Imagem local inspecionada, `--pull=never`, ciclo MCP completo e operações tipadas em um serviço isolado; ponte segura entre `stdio` e cliente do Percival e tratamento de falha/reconexão. | Exige conceder Docker ao processo/usuário que executa shell do agente; custo/risco da ponte não se justifica frente ao gateway externo. |

Um `MCPServerConfig(command="docker", ...)` **no processo do agente** é útil como prova restrita em ambiente isolado, mas não satisfaz a fronteira de produção. Se nenhum candidato oferecer simultaneamente administração exigida e isolamento aceitável, F1 termina com decisão de reescopo/novo desenho; não se declara a capability entregue com um mock ou uma página que apenas lista URLs.

### Contrato provisório do domínio (para alinhar provas, não schema aprovado)

- **Instalação gerenciada:** `server_id` estável, fonte e identidade da imagem (`local-image` com ID completo `sha256:...` **ou** `pinned-image` com `nome@sha256:...`), executor, revisão e intenção de ativação. ID local e RepoDigest não são intercambiáveis; pin não equivale a assinatura. Cadastro não faz pull nem ativa tools.
- **Configuração efetiva:** rede, mounts e referências a secrets conforme o executor escolhido; allowlist de nomes MCP **brutos** inicialmente vazia. No Percival, `tools.mcpServers[*].enabledTools` usa `["*"]` por padrão, portanto a configuração gerenciada precisa derivar uma lista restritiva sem alterar o default dos MCPs genéricos.
- **Estados separados:** instalado/configurado, ativação solicitada, imagem observável, conexão MCP e container observado quando houver sinal confiável; usar `unknown` para sinais indisponíveis. `connected` não demonstra que toda chamada funcionará e `not running` pode ser normal em `stdio` sob demanda. Inventário permanece visível durante erro.
- **Fonte de verdade e ownership:** a camada de domínio guarda intenção/política; o executor confirma imagem e operação; `MCPProvider` relata conexão e tools. A UI renderiza o estado projetado pelo backend, não reconcilia Docker por conta própria. Persistência e revisão do schema seguem Q4.

## 3. Fases, entregas e gates

| Fase | Depende de | Trabalho proposto (agente, salvo indicação) | Evidência de saída |
| --- | --- | --- | --- |
| **F0 — enquadramento** | — | Operador resolve Q1 e o núcleo de Q2; agente inventaria o deployment alvo, riscos, permissões, `MCPProvider`, auth WebUI e fluxos MCP existentes. Define fixture sem segredo, critério comparativo e versão dos executores. | Matriz de ambiente, operações e fronteiras aprovada; plano da prova e resultados esperados/que a falsificam registrados. Sem iniciar containers no estado pessoal do Positronic. |
| **F1 — prova do executor** | F0 | Experimentar gateway externo e broker direto somente em ambiente isolado; testar uma imagem local por ID ou digest, `initialize`, `tools/list`, chamada real, teardown, reconexão, latência, perda de imagem e controle individual. Verificar daemon, credenciais e destino de rede. | Relatório com versões, ID/digest, config sem segredo, medidas e falhas; decisão explícita do operador sobre executor e isolamento. Se houver bridge nova, contrato e esforço estimados antes de F2. |
| **F2 — backend e política** | F1 | Definir schema e storage, serviço de domínio Python, adaptação à configuração MCP existente e `MCPProvider`, estados e API de leitura. Aplicar gate na descoberta **e imediatamente antes** de cada chamada, inclusive wrapper obsoleto/reconnect; compatibilizar reload. Desenvolver autenticação administrativa e operações tipadas no backend sem expor Docker ao modelo/browser. | Testes para cadastro desativado, allowlist vazia, imagem ausente, múltiplos MCPs, revogação concorrente, namespaces, auth negativa e recuperação após erro; servidor genérico permanece intacto. |
| **F3 — página observacional** | Contrato de leitura F2 | Criar página React dedicada na WebUI existente (rota de trabalho `/mcp-containers`), link na sidebar e link contextual em Apps/MCP. Exibir lista, detalhe, origem/ID de imagem, intenção de ativação, allowlist, último teste, erros redigidos e estados distintos; loading/empty/error e layout compacto. | Teste de UI + fluxo autenticado com gateway real; lista não desaparece se Docker/MCP cair, não exibe valor de segredo nem trata `ready` lógico como `running`. Ainda não é a entrega funcional final. |
| **F4 — gestão gráfica** | F2, F3, operações validadas em F1 | Implementar pela mesma API instalar registro, configurar campos suportados, descobrir/revisar tools, ativar/desativar e excluir **registro**; confirmação e revisão de estado para mutações, refresh/reconnect e resultado por servidor. Acrescentar update/restart apenas com semântica validada em Q2/Q7. | Fluxo completo pela UI sem editar JSON nem CLI manual, com 401/403 para ator indevido, falha fechada, negação na próxima chamada após revogação, outro MCP não afetado e rollback/recuperação demonstrados. |
| **F5 — integração e prontidão** | F4 | Provar ao menos dois servidores diferentes, credenciais/mounts permitidos, persistência, restart/falha Docker, observabilidade, deploy Linux escolhido, documentação de operação e recuperação. Ajustar CI do Percival e empacotamento afetado. | Testes Docker em Linux (fixture isolada), gate Python/WebUI/empacotamento no SHA candidato, limites conhecidos e aceite do operador; não inferir release público, tag ou publicação. |

**Caminho crítico:** Q1/Q2 → F0 → F1/decisão do executor → F2/contratos → F3+F4 → F5. Desenho visual e casos de teste podem avançar durante F1; mutações da UI dependem do executor e da autorização efetivamente demonstrados. Se Global/Local (Q5) ou gestão de container persistente (Q7) forem exigidos na primeira versão, revisar F2–F5, testes, prazo e riscos **antes** de considerar o escopo fechado.

## 4. Superfície da UI e contrato operacional inicial

| Superfície | Operação/estado esperado | Restrição antes da implementação |
| --- | --- | --- |
| Overview | Número de registros, ativos por intenção, conectados, indisponíveis, último refresh; falha do executor em separado. | Contagens vêm do backend, não de `docker ps` inferido no browser. |
| Lista e detalhe | ID, imagem e origem, revisão, rede/mounts **apenas metadados permitidos**, tools descobertas versus liberadas, status MCP, último erro redigido. | Segredos e paths sensíveis podem exigir mascaramento por papel; definir Q6. |
| Cadastro e configuração | Escolher imagem presente/digest, validar identidade, declarar rede/mounts e salvar **desativado**; descobrir tools sem executá-las. | Prévia de acesso a paths e egress; nenhuma flag Docker livre enviada do frontend. |
| Ativação e política | Revisar allowlist, ativar, desativar, testar conexão; revogação opera mesmo com sessão MCP em cache. | Novo gate na chamada; opção de recursos/prompts exige política própria, não liberação implícita. |
| Exclusão e recuperação | Confirmar ID, retirar registro/acesso; preservar imagem, dados montados e secret; expor resultado e recuperação suportada. | Definir backup/revisão/idempotência em Q4 e Q7; UI não promete apagar container persistente sem contrato. |

GET autenticado e mutações via canal WebUI já existente são ponto de partida, **não autorização administrativa suficiente por si só**. O gateway atual usa `websockets.process_request` e `dispatch_webui_mutation` para ações WebUI allowlisted; definir e testar o papel/credencial de operador separado para as mutações Docker. A página React será parte da WebUI existente, não um segundo build SPA nos moldes da KG. Mudanças no contrato MCP ou na conexão privada ao gateway Docker não podem ser substituídas por `tools.ssrfWhitelist` amplo; validar destino a cada request/redirect ou usar transporte isolado testado.

## 5. Riscos, controles e dependências

| Risco | Controle / teste que falta |
| --- | --- |
| Docker daemon acessível a shell/modelo ou browser | Isolar o executor privilegiado; testar que cliente Percival e frontend não recebem CLI/socket/token administrativo por acidente. Rever rootless/rootful e política de mounts. |
| Ferramenta revogada mas ainda em sessão, outros caminhos de execução | Checar autorização por ID + tool bruta em cada chamada e antes da publicação; cobrir CLI, WebUI e caminhos que efetivamente executem tools (subagente/job se aplicável). |
| Spoof de estado e perda silenciosa de erro | Inventário declarativo separado de status MCP e Docker; erro persistido/redigido e `unknown` quando não observável. |
| Imagem mutável, secret vazado, egress excessivo | ID/RepoDigest verificado, pull explícito, mount limitado e revisão humana; não transmitir secret no frontend nem logs; política de rede específica por servidor. |
| Mutação parcial de config/daemon | Revisão otimista, lock apropriado, prévia para ações de alcance amplo, backup e recuperação testados; não pressupor transação entre filesystem e Docker. |
| Diferença host/Compose, gateway/plugin e CI | Reproduzir no ambiente alvo, registrar versões, caminhos e latência; smoke do Positronic não substitui gate do Percival. |

## 6. Questões para análise e decisão, em ordem sugerida

Estes IDs são **abertos**, não decisões presumidas. Discutir um por vez; ao resolver, anotar decisão, evidência, impacto no plano e responsável. Os itens marcados **bloqueiam** a fase indicada; os demais podem ser adiados com limitação explícita.

| ID / bloqueio | Pergunta objetiva e recomendação preliminar | Evidência/decisão necessária |
| --- | --- | --- |
| **Q1 — F0** | Qual é o deployment de referência: Percival no host Linux ou em container/Compose? Qual Engine/CLI, rootless/rootful, usuário, acesso ao daemon, rede e política de montagem? **Recomendação:** escolher o ambiente que representará o uso real e um ambiente de teste isolado. | Topologia e permissões observadas; define a fronteira do executor e o CI viável. |
| **Q2 — F0/F1** | Quais ações precisam funcionar **na primeira versão utilizável**: cadastrar imagem local, configurar, ativar/desativar, liberar tools, atualizar, reiniciar, excluir registro, start/stop de container persistente? **Recomendação:** núcleo cadastro/configuração/tools/ativação/exclusão de registro; validar semântica de restart/update separadamente. | Lista de ações e expectativa por operação, aprovada pelo operador; determina escolha entre gateway e broker. |
| **Q3 — F1** | Gateway externo consegue isolar identidade, credenciais e administração por servidor sem expor daemon ao agente? Se não, como transportar MCP e ações tipadas entre um broker separado e o Percival? | Comparativo real, versão pinada, desenho da ponte, esforço e falhas. **Decisão de executor** antes de F2. |
| **Q4 — F2** | Onde guardar inventário/configs/backup e como coexistir com `tools.mcpServers`, presets/plugins e recarga? Qual revisão, lock e recuperação em crash? **Recomendação:** serviço próprio, identidade estável e nenhuma edição direta da config por UI. | Schema v1, migração/rollback, conflitos de escrita e fixture de teste. |
| **Q5 — opcional no MVP** | Global/Local por projeto já é requisito? Como obter identidade de projeto confiável por chamada em CLI/WebUI/jobs? **Recomendação:** começar com política de instalação única até demonstrar isolamento por projeto. | Contrato de contexto/revogação; se exigido, ampliar F2 e acrescentar preview/apply com testes multi-projeto. |
| **Q6 — F2/F4** | Quem pode administrar Docker: somente operador local, WebUI remota, ambos? Qual credencial/papel distinto do token WebUI e quais metadados de mount/log o browser pode ver? | Matriz 401/403, fluxo de credencial, auditoria redigida e teste de acesso remoto. |
| **Q7 — F4** | Qual a semântica de atualizar, reiniciar, excluir e restaurar quando containers são efêmeros (`stdio --rm`) ou persistentes? Qual retenção dos backups? | Tabela de transições, resultado observável, compensação/rollback e confirmação proporcional. |
| **Q8 — F5** | Imagens somente locais ou também OCI/pull? Qual política de assinatura/licença/SBOM, secrets, egress e mounts para produção? | Origens permitidas, revisão de licença/proveniência e ensaio de segredo/rede sem dados privados. |
| **Q9 — F5** | Quais variantes Linux/deploy entram no gate e como testar Docker no CI sem afetar outros jobs? | Matriz Linux, isolamento das fixtures, build WebUI e execução no SHA candidato; conciliar CI geral/TUI herdados. |

**Primeira conversa sugerida:** Q1, seguida de Q2. Após essas respostas, revisar F0/F1 e só então congelar a escolha de executor. Alterações posteriores em Q3–Q9 devem atualizar dependências, evidências, custo e risco neste plano; não transformar recomendações provisórias em status de entrega.

## 7. Verificação, estimativa e transferência

- Durante implementação, testes focados de backend/transportes/UI por fase; ao fechar gates de código e antes de considerar entrega: `pytest`, `basedpyright nanobot`, `ruff check .` na raiz do Percival; no diretório `webui/`, `bun run test`, `bun run lint`, `bun run build`. Não executar `ruff format`. Testes Docker em ambiente isolado Linux com fixture reproduzível e resultado do smoke real anexado ao gate.
- Evidência mínima da execução: commit/SHA, versões de Docker/plugin quando aplicável, identidade da imagem, descrição anonimizada de rede/mounts, testes/erros e decisão do gate. Medir cold start e duração de chamada no F1 antes de projetar cache ou lazy activation.
- **Cronograma/custo:** desconhecidos; estimar após Q1–Q3 e F1, com responsáveis e dependências da ponte/CI. Fases representam ordem e gates, **não** promessa de duração. Publicação, repo público, tag ou release dependem da política própria do Percival e sign-off do operador no candidato exato.
