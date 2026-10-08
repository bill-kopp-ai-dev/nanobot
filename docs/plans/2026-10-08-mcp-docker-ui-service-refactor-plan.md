# Plano de refatoração — UI e serviço de servidores MCP Docker

- **Revisão:** 2026-10-08 / rascunho inicial.
- **Estado:** iniciado; primeiro item definido para revisão. Itens posteriores serão adicionados conforme a análise conjunta da UI e dos contratos de serviço avançar.
- **Objetivo:** tornar a instalação e a gestão de servidores MCP Docker claras e previsíveis na WebUI, mantendo alinhados os fluxos do gateway, domínio e broker.
- **Contexto:** a capability MCP Docker possui UI de leitura e gestão das oito famílias operacionais, com F3/F4/F5 implementadas localmente. O gate Browser WebUI + gateway + broker continua aberto; este plano de refatoração não substitui nem fecha os gates de deployment do plano principal.
- **Plano de execução relacionado:** [MCP Docker first-class no Percival](2026-10-06-mcp-docker-first-class-execution-plan.md).

## 1. Evidência e análise da UI atual

### Capturas de referência

Imagens examinadas em `/home/bill/Pictures`:

- `screenshot-2026-10-08_13-55-15.png`
- `screenshot-2026-10-08_13-55-31.png`
- `screenshot-2026-10-08_13-55-46.png`
- `screenshot-2026-10-08_13-58-31.png`

As capturas mostram a página dividida entre navegação/lista de servidores e o detalhe do servidor selecionado. O título e a ação de atualizar ficam no cabeçalho da página; a área de gestão aparece mais abaixo, depois do detalhe/histórico e da autorização do operador. O formulário “Install a local image” aparece como um disclosure dentro dessa área de gestão, sem uma ação global no cabeçalho que explique claramente que ele adiciona outro servidor.

Nas capturas de `deep-research`, o servidor já aparece na lista, com identidade de imagem, configuração e tools. Portanto, para esse servidor instalado, o formulário de instalação não é uma etapa necessária: suas ações estão em “Manage deep-research”. O formulário serve para registrar uma nova instalação a partir de uma imagem que já existe no Docker local.

As capturas são referência de composição visual, não especificação confiável de estado runtime: algumas exibem broker indisponível/estados `unknown` e `network: bridge`, enquanto o contrato de UI revisto informa rede fixa em `none`. Estados e configuração efetiva devem vir do gateway/broker atual.

### Código e contrato atuais relevantes

- `webui/src/components/McpContainersPage.tsx`: cabeçalho, lista/detalhe, histórico, refresh e composição da página.
- `webui/src/components/McpDockerManagement.tsx`: autorização administrativa, formulário de instalação e ações de gestão do servidor selecionado.
- `webui/src/lib/api.ts`: tipo do snapshot e adaptadores HTTP/WebSocket MCP Docker.
- `webui/src/tests/mcp-containers.test.tsx`: testes da página e das mutações.
- `nanobot/webui/ws_http.py`: mapeamento de mutações WebSocket para rotas.
- `nanobot/webui/settings_routes.py`: autenticação/allowlist e dispatch das rotas.
- `nanobot/mcp_docker/service.py`: `DockerMcpService.act("install", ...)` e demais operações do domínio.

O contrato existente de `install` inspeciona uma imagem local identificada por ID imutável ou RepoDigest, configura e inicia o servidor gerenciado, descobre tools e persiste registro/configuração. Não faz pull. A instalação exige um `server_id` novo; repetir um ID já registrado resulta em conflito.

## 2. Primeiro item proposto

### Item 1 — Ação global “Adicionar servidor MCP”

**Problema:** a entrada para instalação está visualmente embutida no fluxo de gestão de uma página que normalmente já apresenta um servidor selecionado. Isso mistura a ação global de criar uma nova instalação com ações específicas do servidor atual e ocupa espaço no fluxo de gestão.

**Mudança proposta:** adicionar uma ação explícita **“Adicionar servidor MCP”** no cabeçalho da página, junto à ação “Atualizar”. A ação abre o fluxo de instalação/configuração atualmente representado pelo formulário “Install a local image”. O formulário deixa de ser apresentado como seção de gestão do servidor selecionado; permanece acessível pelo novo ponto de entrada e fechado/oculto até ser solicitado.

**Localização recomendada:** cabeçalho superior da página, ao lado de “Atualizar”. Nas capturas, o cabeçalho já agrupa título/descrição à esquerda e atualização à direita; colocar a ação de adicionar nessa mesma área estabelece que ela se aplica à lista inteira, e não ao servidor em foco. Em telas estreitas, as ações podem quebrar linha sem perder rótulos ou acessibilidade.

**Fluxo esperado:**

1. A pessoa aciona “Adicionar servidor MCP”.
2. A UI apresenta os campos já existentes: `server_id`, identidade da imagem, configuração de persistência, redução de mounts, ambiente tipado e preview redigido.
3. O texto deixa explícito que só são aceitas imagens já presentes localmente e que não há pull; instalação com acesso amplo ao host mantém aviso, revisão e confirmação digitada existentes.
4. Após sucesso, a UI atualiza o snapshot e seleciona/mostra a nova instalação para que as operações específicas passem ao detalhe de gestão.
5. Cancelar/fechar o fluxo não envia a mutação `install` nem altera o servidor atualmente selecionado.

**Fronteira inicial:** mudança de apresentação e fluxo da WebUI. Reutilizar a ação e a validação existentes; não alterar sem necessidade o contrato de domínio, o formato persistido, o broker ou a semântica de segurança. Se a implementação revelar uma lacuna real no contrato, documentá-la antes de ampliar o escopo.

**Critérios de aceite:**

- A página oferece uma ação global identificável como “Adicionar servidor MCP” no cabeçalho, junto de atualizar.
- O formulário de instalação não fica visualmente associado ao painel “Manage <server>” e só aparece depois da ação explícita.
- O formulário continua aceitando os tipos de identidade e configurações suportados e apresenta preview sem revelar valores `secret`.
- A UI informa que a imagem deve estar disponível localmente e não promete pull.
- Abrir/cancelar o formulário não envia mutação nem altera o registro selecionado.
- A confirmação e a mutação mantêm `server_id`, revisões e credencial administrativa conforme o contrato atual; conflitos são apresentados sem alegar sucesso.
- Após instalação bem-sucedida, a página refaz a leitura e permite localizar/gerir a nova instalação.
- Testes de UI verificam o ponto de entrada, abertura/cancelamento, envio da instalação e tratamento de conflito; gates WebUI aplicáveis passam.

**Arquivos de implementação prováveis:** `webui/src/components/McpContainersPage.tsx`, `webui/src/components/McpDockerManagement.tsx` e `webui/src/tests/mcp-containers.test.tsx`. Alterações de `webui/src/lib/api.ts` ou do backend não são esperadas para este item, salvo necessidade confirmada na revisão do contrato.

## 3. Sequenciamento e governança do plano

O Item 1 é a primeira proposta, ainda sujeita à validação visual/funcional antes de implementação. Os próximos itens serão definidos após revisar conjuntamente os demais fluxos da página e as respectivas fronteiras do serviço; este rascunho não antecipa mudanças de backend sem evidência.

O plano não autoriza publicação, release, alteração de deployment ou execução de mutações em servidores MCP reais. A implementação deve ser verificada em ambiente controlado, usando `deep-research` como fixture de UI/gestão quando apropriado, sem reinstalá-lo como teste do Item 1.
