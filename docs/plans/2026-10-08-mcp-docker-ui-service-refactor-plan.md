# Plano de refatoração — UI e serviço de servidores MCP Docker

- **Revisão:** 2026-10-08 / rascunho em evolução.
- **Estado:** quatro itens propostos; aguardam validação antes de implementação.
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

As capturas são referência de composição visual, não especificação confiável de estado runtime: algumas exibem broker indisponível/estados `unknown` e `network: bridge`. A revisão atual também encontrou texto na UI dizendo que a rede é fixa em `none`, embora o contrato Python permita `none` e `bridge`; tratar essa frase como inconsistência conhecida, não como estado efetivo. Estados e configuração efetiva devem vir do gateway/broker atual.

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

## 3. Segundo item proposto

### Item 2 — Tornar explícito e configurável o nível de acesso ao host

**Evidência visual:** as duas capturas do painel “Configure host” mostram uma seção subordinada ao restante de “Manage <server>”, com pouco contraste hierárquico. No estado sem a caixa marcada, o servidor tem acesso amplo por padrão, mas esse nível fica implícito no checkbox e no texto auxiliar. No estado marcado, aparece uma caixa de caminhos vazia, sem resumo do escopo atual nem explicação visível do que uma lista vazia significaria. A seção não permite reconhecer rapidamente o nível de acesso do servidor selecionado.

**Contrato observado:** em `DockerHostConfig`, `mounts: null` representa o padrão de acesso amplo ao sistema de arquivos do host; uma lista não vazia representa caminhos de host explicitamente reduzidos. O schema rejeita lista vazia e `MountPolicy.docker_args` também rejeita redução sem caminhos. O broker aplica mounts de proteção do control plane em ambos os modos. O snapshot traz a configuração declarada e mounts efetivos, mas a observação efetiva não inclui a origem host de cada bind; portanto, a UI deve distinguir configuração salva de runtime observado e não declarar verificação de caminhos que o snapshot não prova.

**Mudança proposta:** substituir o checkbox por uma área visualmente destacada **“Acesso ao host”**, com badge de nível atual e três opções selecionáveis, com mudanças pendentes até a pessoa salvar:

1. **Full access** — permite acesso amplo ao sistema de arquivos do host, exceto pelos caminhos protegidos obrigatoriamente pelo broker.
2. **Minimum access** — não expõe caminhos adicionais do host; as proteções obrigatórias do broker continuam aplicadas. A descrição deve ser explícita para que “mínimo” não prometa ausência de outros acessos do container.
3. **Customized** — expõe somente os caminhos absolutos escolhidos; a lista editável aparece apenas neste modo.

Exibir o resumo do nível atual mesmo antes de editar, junto com estado de observação (por exemplo, confirmado, divergente ou indisponível) somente quando os dados existentes permitirem sustentar essa distinção. Usar destaque visual proporcional ao risco: “Full access” deve ser inequívoco, mas não alarmista; “Minimum access” e “Customized” devem mostrar o escopo legível. Manter a revisão antes/depois e exigir confirmação digitada pelo ID do servidor para qualquer ampliação de acesso. Reduções continuam exigindo revisão explícita.

**Decisão de representação pendente de validação técnica:** uma possibilidade compatível com o formato atual é representar `null` como full, `[]` como minimum e lista não vazia como customized. Isso exige alterar o validador do contrato e `MountPolicy.docker_args` para aceitar a lista vazia como “nenhum bind opcional do host”, sem remover os covers obrigatórios. Antes de adotar essa codificação, verificar migração/compatibilidade com configurações existentes e garantir que configure, install, update, restore, serialização e observação preservam os três estados. Se a representação implícita ficar ambígua, considerar um campo explícito de modo com migração versionada; evitar manter duas fontes de verdade para o mesmo nível.

**Fronteira de rede:** acesso ao filesystem do host e conectividade de rede são controles separados. Não incluir `network` nas três opções de host. Revisar a mensagem atual da UI que diz que a rede é sempre `none`: o contrato Python permite `none` e `bridge`; a interface não deve descrever estado fixo sem verificar a configuração efetiva. Se necessário, tratar a apresentação de rede como item separado.

**Critérios de aceite:**

- A seção tem hierarquia visual de controle de segurança e exibe de imediato o nível configurado do servidor selecionado.
- As opções Full access, Minimum access e Customized têm explicações concretas e acessíveis; customized expõe o editor de caminhos apenas quando selecionado.
- A pessoa pode mudar a opção sem executar mutação até salvar; cancelar/reverter mantém a configuração salva.
- Minimum access corresponde a zero caminhos opcionais de host, enquanto o broker ainda aplica todos os covers obrigatórios; a distinção fica coberta por testes do contrato e do broker.
- Full access, minimum e customized sobrevivem ao ciclo de leitura, salvamento, restart/reconciliação e restore sem mudança silenciosa de modo.
- Ampliações continuam exigindo confirmação explícita do `server_id`; a prévia antes/depois mostra o escopo de acesso e não revela secrets.
- A UI distingue configuração declarada de runtime observado e apresenta estado desconhecido quando o broker não fornece evidência suficiente.
- A rede é apresentada separadamente e nenhuma mensagem afirma que está fixa em `none` quando a configuração pode usar `bridge`.
- Testes de UI cobrem seleção, edição/cancelamento, salvamento, confirmação de aumento, falha/conflict e exibição de estado sem observação; testes backend cobrem os três modos e os covers invariantes.

**Arquivos de implementação prováveis:** `webui/src/components/McpDockerManagement.tsx`, `webui/src/lib/api.ts`, `webui/src/tests/mcp-containers.test.tsx`, `nanobot/mcp_docker/contracts.py`, `nanobot/mcp_docker/mount_policy.py`, `nanobot/mcp_docker/service.py`, `nanobot/mcp_docker/broker.py` e testes em `tests/mcp_docker/`. A lista final depende da representação escolhida e do que a observação efetiva consegue garantir sem expor informação desnecessária do host.

## 4. Terceiro item proposto

### Item 3 — Melhorar a edição e revisão de variáveis de ambiente

**Evidência visual:** a captura de “Environment variables” mostra uma lista compacta de linhas com nome, tipo e valor, mas sem explicar o efeito de `plain`, `secret` ou `reference`. O valor de um secret existente aparece vazio com a indicação “Leave unchanged to keep secret”, o que pode parecer campo incompleto. A comparação Before/After ocupa grande parte do painel com JSON completo e rolagem interna, misturando alterações de ambiente com outras configurações. Na captura, `network` muda de `bridge` para `none` apesar de a edição mostrada ser de variáveis; isso pode ser captura de outra versão ou regressão e deve ser investigado. O código atual preserva `selected.configuration.network` no preview e no payload de configure, comportamento que precisa ficar protegido por teste.

**Contrato observado:** nomes de variável seguem o padrão de identificadores de ambiente. `plain` persiste um valor literal visível; `secret` é redigido nas leituras, mas o valor literal ainda é persistido na configuração do Percival — não é um vault externo. Um secret existente pode ser mantido sem reexibição do valor. `reference` usa o formato `${VAR}` e o broker resolve `VAR` no próprio ambiente do broker durante a criação do container; variável ausente impede o start. Mudanças de configuração podem exigir restart do servidor.

**Mudança proposta:** manter o editor como lista de variáveis, mas dar rótulos e ajuda contextual a cada tipo:

- **Plain:** valor literal salvo e exibido na configuração.
- **Secret:** valor não exibido; indicar claramente quando um secret já está configurado e que deixar o campo vazio o preserva. Ações explícitas permitem substituir ou remover; nunca oferecer revelação do valor salvo.
- **Reference:** explicar que `${VAR}` é resolvida pelo ambiente do broker, não pelo ambiente do container ou pelo formulário; indicar que uma referência indisponível impede iniciar o servidor.

Substituir o diff integral de configuração por um resumo focado em variáveis adicionadas, alteradas, removidas, sem alteração e secrets preservados. Se outras configurações mudarem, apresentá-las em seção separada; não atribuir ao editor de variáveis alterações em `network` ou acesso ao host. Informar quando salvar requer restart. Validar nomes vazios/malformados, duplicatas e referências inválidas antes do envio, com erro associado à linha correspondente; tornar rótulos e ação de remoção acessíveis e específicos da variável.

**Critérios de aceite:**

- Cada tipo (`plain`, `secret`, `reference`) tem explicação contextual e a edição se adapta ao tipo selecionado.
- Secret existente é identificado como configurado e preservado quando não substituído; seu valor nunca aparece em tela, preview, logs ou erro. A UI não sugere que o valor está armazenado em um vault.
- Remover uma variável é explícito; o resumo identifica o nome e o efeito, e os secrets removidos não são revelados.
- Referências `${VAR}` são validadas no cliente e erros do broker por variável ausente são apresentados sem alegar sucesso.
- Duplicatas, nomes inválidos e linhas incompletas recebem validação clara antes de salvar e não são silenciosamente descartados ou sobrescritos.
- A revisão mostra apenas alterações pertinentes em variáveis e secrets; outras configurações são separadas e permanecem intactas quando não editadas.
- Salvar somente variáveis preserva `network`, mounts e persistência selecionados; um teste de regressão cobre explicitamente o caso `bridge` sem mudança da rede.
- A UI informa quando a aplicação da configuração reinicia o servidor; estados de salvamento/falha e conflitos continuam inequívocos.
- O layout permanece utilizável em telas estreitas, teclado e leitor de tela, com nomes acessíveis para campos, erros e remoção.

**Arquivos de implementação prováveis:** `webui/src/components/McpDockerManagement.tsx`, `webui/src/lib/api.ts`, `webui/src/tests/mcp-containers.test.tsx`, `nanobot/mcp_docker/contracts.py`, `nanobot/mcp_docker/broker.py` e testes de contrato/serviço existentes. Mudanças de backend só devem ser incluídas se a revisão confirmar lacuna no contrato de referência/erros; não são necessárias apenas para reorganizar a UI.

## 5. Quarto item proposto

### Item 4 — Abrir “Update image” sob demanda

**Evidência visual:** nas capturas da página completa (`screenshot-2026-10-08_13-58-31.png`, `screenshot-2026-10-08_14-43-06.png` e `screenshot-2026-10-08_15-31-02.png`), a gestão do servidor se estende por uma página longa. “Update image” aparece perto do fim, depois da configuração de host e variáveis, imediatamente antes de “Exclude server”. Isso reduz a descoberta da atualização e aproxima visualmente uma operação de manutenção da ação destrutiva de exclusão. A captura próxima do painel mostra a identidade atual e a candidata iguais; nesse caso o backend atual ainda aceita a operação e recria o container com a mesma imagem.

**Mudança proposta:** substituir o formulário permanente por um botão **“Update image”** no conjunto de ações do servidor selecionado, próximo de Restart/Activate/Deactivate. O botão abre um diálogo ou painel lateral identificado com o servidor, mantendo a atualização contextual a esse servidor. Não mover a ação para o cabeçalho global da página: diferentemente de instalar outro servidor, atualizar altera somente o servidor selecionado. Manter “Exclude server” no fim da gestão, separado e com a hierarquia destrutiva existente.

**Fluxo esperado:**

1. A pessoa aciona “Update image” para o servidor selecionado.
2. O diálogo identifica o servidor e mostra a imagem atual como origem, seguida dos campos existentes para tipo e identidade candidata (`local image ID` ou `RepoDigest`). A identidade atual pode continuar pré-preenchida, mas o envio fica bloqueado se o candidato representar a mesma imagem efetiva.
3. A ajuda explica que o destino deve ser uma identidade imutável de imagem já presente localmente; não há pull nem build. O broker valida a disponibilidade e correspondência da identidade na execução.
4. A revisão explicita que a configuração do servidor (host, rede, mounts e ambiente) será mantida, e descreve o rollback: há backup da identidade/configuração e tentativa de recuperação para a imagem anterior se a operação falhar; os layers antigos não são arquivados e a imagem anterior precisa continuar disponível localmente.
5. A pessoa marca a revisão e digita o `server_id`. Cancelar fecha o diálogo sem enviar `update-image` ou alterar o servidor.
6. Após a mutação, a UI atualiza o snapshot e mostra o resultado verificado; conflito, imagem ausente ou falha do broker não são apresentados como sucesso.

**Fronteira inicial:** reaproveitar a operação `update-image` existente, as validações de imagem, backup, journal, CAS e recuperação. A mudança principal é de apresentação/interação. Acrescentar uma proteção estreita contra atualização sem efeito: no mínimo, bloquear antes da mutação quando o tipo e a referência imutável candidata são idênticos à fonte atual. Essa checagem deve ocorrer antes de criar backup/journal, não apenas no broker depois de o serviço já abrir a transição. Se o requisito incluir aliases diferentes para a mesma imagem efetiva (ID local versus RepoDigest), será necessário um preflight tipado do broker antes do backup; decidir isso na revisão técnica, sem comparar tags mutáveis nem dar ao gateway acesso ao Docker. Não adicionar catálogo/seletor de imagens locais nesta fase; isso exigiria uma API de inventário Docker além do fluxo atual de entrada de identidade.

**Critérios de aceite:**

- A ação é visível nas ações do servidor selecionado e não aparece como ação global; o formulário não ocupa espaço persistente no fim da página.
- O diálogo mostra claramente servidor, imagem atual, identidade candidata e que imagens locais imutáveis são aceitas sem pull.
- Abrir/cancelar não envia mutação, não altera o servidor selecionado e não modifica estado persistido.
- A mesma identidade imutável (mesmo tipo e referência) não pode acionar remoção/recriação do container nem gerar backup/transição; se o produto exigir detectar aliases da mesma imagem, o preflight tipado compara a identidade resolvida antes de abrir a transição.
- A confirmação explícita e revisões global/servidor existentes continuam obrigatórias.
- O resumo deixa claro que a configuração atual do servidor permanece e que rollback depende da imagem anterior ainda existir localmente.
- A resposta só informa sucesso depois da mutação e refresh; imagem ausente, conflito, broker rejeitado/indisponível e transição não resolvida são comunicados como falha/estado pendente.
- Testes WebUI cobrem ação, abertura/fechamento, formulário, no-op, confirmação, sucesso e erros. Testes de domínio/broker cobrem rejeição/idempotência para imagem igual e preservação da configuração no update.

**Arquivos de implementação prováveis:** `webui/src/components/McpDockerManagement.tsx`, possivelmente `webui/src/components/McpContainersPage.tsx` para composição/layout, `webui/src/tests/mcp-containers.test.tsx`, `nanobot/mcp_docker/service.py`, `nanobot/mcp_docker/broker.py` e testes em `tests/mcp_docker/`. Alterações de serviço/broker devem se limitar à garantia contra no-op se a revisão confirmar que ela é necessária no servidor, além da apresentação da UI.

## 6. Sequenciamento e governança do plano

Os Itens 1 a 4 são propostas sujeitas à validação visual, funcional e contratual antes de implementação. O Item 2 requer resolver a semântica persistida de Minimum access e seus invariantes no broker antes de construir a interface final. O Item 3 deve confirmar a discrepância visual de rede e proteger com teste a preservação da configuração não editada. O Item 4 deve impedir a atualização idêntica antes do backup; detectar aliases equivalentes depende de decidir e implementar um preflight tipado do broker. Próximos itens serão definidos após revisar os demais fluxos da página e as fronteiras do serviço; o plano não antecipa mudanças adicionais de backend sem evidência.

O plano não autoriza publicação, release, alteração de deployment ou execução de mutações em servidores MCP reais. A implementação deve ser verificada em ambiente controlado, usando `deep-research` como fixture de UI/gestão quando apropriado, sem reinstalá-lo como teste do Item 1 nem alterar seu acesso, secrets ou imagem real durante testes dos Itens 2 a 4.
