# Plano de refatoração — UI e serviço de servidores MCP Docker

- **Revisão:** 2026-10-08 / revisão de executabilidade após análise das 15 capturas e do código atual.
- **Estado:** implementação local em andamento; evidências e gates abertos em [relatório de execução](../reports/2026-10-08-mcp-docker-ui-refactor-execution.md).
- **Objetivo:** tornar a instalação e a gestão de servidores MCP Docker claras e previsíveis na WebUI, mantendo alinhados os fluxos do gateway, domínio e broker.
- **Contexto:** a capability MCP Docker possui UI de leitura e gestão das oito famílias operacionais, com F3/F4/F5 implementadas localmente. O gate Browser WebUI + gateway + broker continua aberto; este plano de refatoração não substitui nem fecha os gates de deployment do plano principal.
- **Plano de execução relacionado:** [MCP Docker first-class no Percival](2026-10-06-mcp-docker-first-class-execution-plan.md).

## 1. Evidência e análise da UI atual

### Capturas de referência

As 15 imagens disponíveis em `/home/bill/Pictures` foram examinadas nesta
revisão:

- `screenshot-2026-10-08_13-55-15.png`
- `screenshot-2026-10-08_13-55-31.png`
- `screenshot-2026-10-08_13-55-46.png`
- `screenshot-2026-10-08_13-58-31.png`
- `screenshot-2026-10-08_14-05-56.png`
- `screenshot-2026-10-08_14-23-44.png`
- `screenshot-2026-10-08_14-43-06.png`
- `screenshot-2026-10-08_15-00-43.png`
- `screenshot-2026-10-08_15-01-01.png`
- `screenshot-2026-10-08_15-20-40.png`
- `screenshot-2026-10-08_15-31-02.png`
- `screenshot-2026-10-08_15-47-19.png`
- `screenshot-2026-10-08_15-52-21.png`
- `screenshot-2026-10-08_19-16-54.png`
- `screenshot-2026-10-08_19-17-10.png`

As capturas mostram a página dividida entre navegação/lista de servidores e o detalhe do servidor selecionado. O título e a ação de atualizar ficam no cabeçalho da página; autorização do operador, instalação, restore, gestão, configuração, atualização e exclusão aparecem em uma longa coluna abaixo do detalhe/histórico. Isso empurra ações importantes para fora da primeira tela. O formulário “Install a local image” aparece como um disclosure dentro dessa área de gestão, sem uma ação global no cabeçalho que explique claramente que ele adiciona outro servidor.

Nas capturas de `deep-research`, o servidor já aparece na lista, com identidade de imagem, configuração e tools. Portanto, para esse servidor instalado, o formulário de instalação não é uma etapa necessária: suas ações estão em “Manage deep-research”. O formulário serve para registrar uma nova instalação a partir de uma imagem que já existe no Docker local. O painel de restore mostra uma caixa destacada mesmo sem backups, enquanto a gestão de ferramentas repete uma linha com botão para cada tool; ambos devem escalar com estado/quantidade sem dominar o fluxo.

As capturas são referência de composição visual, não especificação confiável de estado runtime: as versões das 13:55 e 15:47/15:52 mostram broker indisponível e estados `unknown`, enquanto as versões das 19:16/19:17 mostram Docker parado/desconectado. Nas capturas de 15:20 o diff de uma edição de variáveis também parece mudar `network` de `bridge` para `none`. No código atual, `submitConfigure` preserva `selected.configuration.network`; a captura pode representar uma versão anterior ou outro estado e ainda precisa de reprodução no browser. Em contraste, o formulário de instalação atual de fato hardcodeia `network: "none"` e afirma que a rede é fixa, apesar de o contrato Python aceitar `none` e `bridge`. Distinguir observação visual, implementação verificada e runtime real: estados efetivos vêm do gateway/broker, e screenshots não provam o estado atual.

### Código e contrato atuais relevantes

- `webui/src/components/McpContainersPage.tsx`: cabeçalho, lista/detalhe, histórico, refresh e composição da página.
- `webui/src/components/McpDockerManagement.tsx`: autorização administrativa, formulário de instalação e ações de gestão do servidor selecionado.
- `webui/src/lib/api.ts`: tipo do snapshot e adaptadores HTTP/WebSocket MCP Docker.
- `webui/src/tests/mcp-containers.test.tsx`: testes da página e das mutações.
- `nanobot/webui/ws_http.py`: mapeamento de mutações WebSocket para rotas.
- `nanobot/webui/settings_routes.py`: autenticação/allowlist e dispatch das rotas.
- `nanobot/mcp_docker/service.py`: `DockerMcpService.act("install", ...)` e demais operações do domínio.

O contrato existente de `install` inspeciona uma imagem local identificada por ID imutável ou RepoDigest, configura e inicia o servidor gerenciado, descobre tools e persiste registro/configuração. Não faz pull. A instalação exige um `server_id` novo; repetir um ID já registrado resulta em conflito.

### Invariantes de implementação a preservar

- `list()` chama `recover_pending()` antes de ler o snapshot: uma leitura pode reconciliar **uma transição já registrada**, mas não deve iniciar uma operação nova apenas para satisfazer a UI. `brokerStatus: ready` prova somente preflight do broker, não saúde individual de container/MCP; `observe` pode falhar separadamente.
- Em `DockerMcpService.list()`, `tools` usa a lista recebida de `observe` **quando presente**, mas recai em `server.tools` (registro salvo) quando a observação falha. Na implementação atual, `_discover()` rejeita `tools/list` vazio: `connected` com zero tools não é uma observação bem-sucedida representável. UI não pode chamar lista salva de “discovered now” nem exigir esse caso em testes sem alterar antes o contrato broker/serviço.
- A UI recebe snapshots por GET e mutações por WebSocket; revisões global e por servidor são conferidas pelo domínio. O `refresh()` atual absorve falhas de GET e mantém snapshot anterior; `invoke()` anuncia sucesso antes de aguardar esse refresh e `submitInstall()` não seleciona o novo ID. Os itens que prometem resultado verificado/seleção precisam corrigir estes fluxos, não apenas reposicionar formulários.
- A senha administrativa digitada é guardada em memória e enviada na mutação; preencher o campo não autentica antecipadamente. O status da UI deve distinguir **senha fornecida (não verificada)** de autorização efetivamente aceita em uma operação; nenhuma gestão pode contornar `operator_admin`, `allowRemoteAdmin`, CAS ou bloqueio por transição pendente.
- Ao modificar o editor, manter o sentinel de secret apenas no payload de atualização para o **mesmo nome e tipo** já configurados; o serviço resolve o sentinel a partir do valor anterior e proíbe persistir o sentinel literal. `[]` para `mounts` é rejeitado pelo schema e pelo broker atuais; `null` significa bind amplo, não “zero mounts”.

## 2. Primeiro item proposto

### Item 1 — Ação global “Adicionar servidor MCP”

**Problema:** a entrada para instalação está visualmente embutida no fluxo de gestão de uma página que normalmente já apresenta um servidor selecionado. Isso mistura a ação global de criar uma nova instalação com ações específicas do servidor atual e ocupa espaço no fluxo de gestão.

**Mudança proposta:** adicionar uma ação explícita **“Adicionar servidor MCP”** no cabeçalho da página, junto à ação “Atualizar”. A ação abre o fluxo de instalação/configuração atualmente representado pelo formulário “Install a local image”. O formulário deixa de ser apresentado como seção de gestão do servidor selecionado; permanece acessível pelo novo ponto de entrada e fechado/oculto até ser solicitado.

**Localização recomendada:** cabeçalho superior da página, ao lado de “Atualizar”. Nas capturas, o cabeçalho já agrupa título/descrição à esquerda e atualização à direita; colocar a ação de adicionar nessa mesma área estabelece que ela se aplica à lista inteira, e não ao servidor em foco. Em telas estreitas, as ações podem quebrar linha sem perder rótulos ou acessibilidade.

**Fluxo esperado:**

1. A pessoa aciona “Adicionar servidor MCP”.
2. A UI apresenta os campos já existentes: `server_id`, identidade da imagem, configuração de persistência, redução de mounts, ambiente tipado e preview redigido.
3. O texto deixa explícito que só são aceitas imagens já presentes localmente e que não há pull; instalação com acesso amplo ao host mantém aviso, revisão e confirmação digitada existentes.
4. Após a mutação confirmada, a UI refaz a leitura; se ela funcionar e contiver o `server_id` recém-criado, seleciona/mostra a nova instalação. Se o refresh falhar, informa **operação aceita, estado ainda não verificado**, mantém o ID para localizar depois e não apresenta estado antigo como atual.
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
- Abertura com gestão bloqueada mostra caminho para fornecer senha sem criar instalação prematuramente; mudança de seleção, refresh periódico ou 409 não reaproveita revisão/confirmação antigas sem revalidar o formulário.
- Falha de GET após mutação não é rotulada como “estado verificado”; o mesmo contrato de feedback aplica-se aos Itens 3, 4 e 7.
- Testes de UI verificam o ponto de entrada, abertura/cancelamento, envio da instalação e tratamento de conflito; gates WebUI aplicáveis passam.

**Arquivos de implementação prováveis:** `webui/src/components/McpContainersPage.tsx`, `webui/src/components/McpDockerManagement.tsx` e `webui/src/tests/mcp-containers.test.tsx`. Alterações de `webui/src/lib/api.ts` ou do backend não são esperadas para este item, salvo necessidade confirmada na revisão do contrato.

## 3. Segundo item proposto

### Item 2 — Tornar explícito e configurável o nível de acesso ao host

**Evidência visual:** `screenshot-2026-10-08_15-00-43.png` e `screenshot-2026-10-08_15-01-01.png` mostram “Configure host” subordinado ao restante de “Manage <server>”, com pouco contraste hierárquico. No estado sem a caixa marcada, o servidor tem acesso amplo por padrão, mas esse nível fica implícito no checkbox e no texto auxiliar. No estado marcado, aparece uma caixa de caminhos vazia, sem resumo do escopo atual nem explicação visível; isso parece um formulário pronto para salvar embora a lista vazia seja rejeitada pelo contrato atual. A seção não permite reconhecer rapidamente o nível de acesso do servidor selecionado.

**Contrato observado:** em `DockerHostConfig`, `mounts: null` representa o padrão de acesso amplo ao sistema de arquivos do host; uma lista não vazia representa caminhos de host explicitamente reduzidos. O schema rejeita lista vazia e `MountPolicy.docker_args` também rejeita redução sem caminhos. O broker monta covers de proteção **após** os binds somente onde um bind pai alcançaria o caminho protegido. O snapshot traz configuração declarada e mounts efetivos (destination/type/readWrite), mas não a origem host de cada bind; portanto, a UI não pode declarar verificados os caminhos de origem apenas por esse snapshot.

**Mudança proposta:** substituir o checkbox por uma área visualmente destacada **“Acesso ao host”**, com badge de nível atual e três opções selecionáveis, com mudanças pendentes até a pessoa salvar:

1. **Full access** — permite acesso amplo ao sistema de arquivos do host, exceto pelos caminhos protegidos obrigatoriamente pelo broker.
2. **Minimum access** — não monta caminhos de filesystem do host no container gerenciado; isso não elimina acesso à imagem/rootfs do container, a rede configurada ou outros recursos Docker. Covers só são necessários onde há um bind pai que permita alcançar um caminho protegido.
3. **Customized** — expõe somente os caminhos absolutos escolhidos; a lista editável aparece apenas neste modo.

Exibir o resumo do nível atual mesmo antes de editar, junto com estado de observação (por exemplo, confirmado, divergente ou indisponível) somente quando os dados existentes permitirem sustentar essa distinção. Usar destaque visual proporcional ao risco: “Full access” deve ser inequívoco, mas não alarmista; “Minimum access” e “Customized” devem mostrar o escopo legível. Manter a revisão antes/depois e exigir confirmação digitada pelo ID do servidor para qualquer ampliação de acesso. Reduções continuam exigindo revisão explícita.

**Decisão de representação pendente de validação técnica:** recomendação a testar: `null` = full; `[]` = minimum; lista não vazia = customized. Hoje `DockerHostConfig.check_mounts` **e** `MountPolicy.docker_args` rejeitam `[]`; é uma mudança de contrato, não só do formulário. Para `[]`, `docker_args` deve produzir zero binds de `/host` (e nenhum cover supérfluo), sem tocar nos covers exigidos para Full/Customized. Testar com a inspeção efetiva do broker que `/host` não remonta a árvore do host e que os caminhos de controle nunca se tornam acessíveis; verificar symlinks/submounts, restart, restore e backups existentes. Validar round-trip de install/configure/update/restore e deploy misto antes de alterar o schema 1; configurações antigas sem campo `mounts` continuam Full. Se a representação implícita ficar ambígua, escolher campo explícito com migração versionada **antes** da UI, sem duas fontes de verdade. Não prometer “controle de rede mínimo” a partir de `mounts=[]`.

**Fronteira de rede:** acesso ao filesystem do host e conectividade de rede são controles separados. Não incluir `network` nas três opções de host. A mensagem atual da UI que diz que a rede é sempre `none` é inconsistente com o contrato Python (`none`/`bridge`) e com a necessidade de servidores com acesso de rede; a apresentação/configuração de rede está proposta separadamente no Item 7.

**Critérios de aceite:**

- A seção tem hierarquia visual de controle de segurança e exibe de imediato o nível configurado do servidor selecionado.
- As opções Full access, Minimum access e Customized têm explicações concretas e acessíveis; customized expõe o editor de caminhos apenas quando selecionado.
- A pessoa pode mudar a opção sem executar mutação até salvar; cancelar/reverter mantém a configuração salva.
- O modo Customized não pode ser salvo com lista vazia; a validação explica o requisito e nunca converte silenciosamente uma seleção vazia em acesso amplo. Minimum access só existe se for definido e representado explicitamente no contrato.
- Minimum access corresponde a zero binds da árvore do host no container gerenciado; os covers são aplicados aos binds Full/Customized quando necessários, e testes de inspeção garantem que caminhos protegidos não se tornam acessíveis em nenhum dos três modos.
- Full access, Minimum e Customized sobrevivem ao ciclo de leitura, salvamento, restart/reconciliação, atualização da imagem e restore (inclusive backup legado) sem mudança silenciosa de modo.
- Para servidor `stopped-persistent`, não aplicar `configure` de mounts inadvertidamente enquanto o broker atual iniciaria o container; preservar o stop por correção de domínio comprovada ou bloquear com explicação até que ela exista.
- Ampliações continuam exigindo confirmação explícita do `server_id`; a prévia antes/depois mostra o escopo de acesso e não revela secrets.
- A UI distingue configuração declarada de runtime observado e apresenta estado desconhecido quando o broker não fornece evidência suficiente.
- A rede é apresentada separadamente e nenhuma mensagem afirma que está fixa em `none` quando a configuração pode usar `bridge`.
- Testes de UI cobrem seleção, edição/cancelamento, salvamento, confirmação de aumento, falha/conflict e exibição de estado sem observação; testes backend cobrem os três modos e os covers invariantes.

**Arquivos de implementação prováveis:** `webui/src/components/McpDockerManagement.tsx`, `webui/src/lib/api.ts`, `webui/src/tests/mcp-containers.test.tsx`, `nanobot/mcp_docker/contracts.py`, `nanobot/mcp_docker/mount_policy.py`, `nanobot/mcp_docker/service.py`, `nanobot/mcp_docker/broker.py` e testes em `tests/mcp_docker/`. A lista final depende da representação escolhida e do que a observação efetiva consegue garantir sem expor informação desnecessária do host.

## 4. Terceiro item proposto

### Item 3 — Melhorar a edição e revisão de variáveis de ambiente

**Evidência visual:** `screenshot-2026-10-08_15-20-40.png` mostra lista compacta de variáveis sem explicar `plain`, `secret` e `reference`; um secret existente aparece vazio com a indicação “Leave unchanged to keep secret”, e o diff Before/After ocupa grande área com JSON completo e rolagem interna. No diff, `network` parece mudar de `bridge` para `none` durante uma edição de variáveis. Na revisão do código atual, `submitConfigure` usa `selected.configuration.network` no payload e o preview usa o mesmo valor. Portanto, não assumir regressão já reproduzida: proteger esse invariante com teste e reproduzir a tela no browser antes de ampliar o backend.

**Contrato observado:** nomes de variável seguem o padrão de identificadores de ambiente. `plain` persiste um valor literal visível; `secret` é redigido nas leituras, mas o valor literal ainda é persistido na configuração do Percival — não é um vault externo. Um secret existente pode ser mantido sem reexibição do valor. `reference` usa o formato `${VAR}` e o broker resolve `VAR` no próprio ambiente do broker durante a criação do container; variável ausente impede o start. `configure` recria o container de um servidor ativo, inclusive quando só muda o ambiente.

**Mudança proposta:** manter o editor como lista de variáveis, mas dar rótulos e ajuda contextual a cada tipo:

- **Plain:** valor literal salvo e exibido na configuração.
- **Secret:** valor não exibido; indicar claramente quando um secret já está configurado e que deixar o campo vazio o preserva. Ações explícitas permitem substituir ou remover; nunca oferecer revelação do valor salvo.
- **Reference:** explicar que `${VAR}` é resolvida pelo ambiente do broker, não pelo ambiente do container ou pelo formulário; indicar que uma referência indisponível impede iniciar o servidor.

Substituir o diff integral de configuração por um resumo focado em variáveis adicionadas, alteradas, removidas, sem alteração e secrets preservados. Se outras configurações mudarem, apresentá-las em seção separada; não atribuir ao editor de variáveis alterações em `network` ou acesso ao host. O fluxo `configure` do broker atualmente remove/recria o container de um servidor ativo, inclusive quando o payload não muda; a revisão deve dizer isso antes de salvar e bloquear envio sem mudança efetiva. Validar nomes vazios/malformados, duplicatas e referências inválidas antes do envio, com erro associado à linha correspondente; não usar `Object.fromEntries`/filtro de nome vazio para descartar silenciosamente linhas ou sobrescrever duplicatas. Manter identificadores estáveis nas linhas para evitar perder foco/valores ao renomear; rótulos e remoção devem identificar a variável.

**Critérios de aceite:**

- Cada tipo (`plain`, `secret`, `reference`) tem explicação contextual e a edição se adapta ao tipo selecionado.
- Secret existente é identificado como configurado e preservado quando não substituído; seu valor nunca aparece em tela, preview, logs ou erro. A UI não sugere que o valor está armazenado em um vault.
- Campo visual vazio de secret existente **não** se converte em valor literal vazio no payload: usar sentinel somente para manter secret inalterado; substituir/remover requer ações explícitas. Renomear um secret requer novo valor (não reaproveitar sentinel sob outro nome). Para secret novo, vazio é validado conforme decisão explícita de produto, sem confundir com “manter”.
- Remover uma variável é explícito; o resumo identifica o nome e o efeito, e os secrets removidos não são revelados.
- Referências `${VAR}` são validadas no cliente e erros do broker por variável ausente são apresentados sem alegar sucesso.
- Duplicatas, nomes inválidos e linhas incompletas recebem validação clara antes de salvar e não são silenciosamente descartados ou sobrescritos.
- A revisão mostra apenas alterações pertinentes em variáveis e secrets; outras configurações são separadas e permanecem intactas quando não editadas.
- Salvar somente variáveis preserva `network`, mounts e persistência selecionados; um teste de regressão cobre explicitamente o caso `bridge` sem mudança da rede.
- A UI informa que `configure` recria o container se o servidor está ativo; enviar configuração sem mudança efetiva não dispara recriação. Estado `stopped-persistent` merece teste específico, pois o broker atual pode iniciar o container durante `configure`: decidir se deve manter parado ou bloquear edição até correção do domínio, sem prometer preservação que hoje não existe.
- Durante edição, refresh periódico ou alteração de revisão não substitui silenciosamente o rascunho nem deixa confirmação válida para um snapshot diferente; 409 apresenta estado novo e permite reabrir a revisão/redigir novamente.
- O layout permanece utilizável em telas estreitas, teclado e leitor de tela, com nomes acessíveis para campos, erros e remoção.

**Arquivos de implementação prováveis:** `webui/src/components/McpDockerManagement.tsx`, `webui/src/lib/api.ts`, `webui/src/tests/mcp-containers.test.tsx`, `nanobot/mcp_docker/contracts.py`, `nanobot/mcp_docker/broker.py` e testes de contrato/serviço existentes. Mudanças de backend só devem ser incluídas se a revisão confirmar lacuna no contrato de referência/erros; não são necessárias apenas para reorganizar a UI.

## 5. Quarto item proposto

### Item 4 — Abrir “Update image” sob demanda

**Evidência visual:** nas capturas da página completa (`screenshot-2026-10-08_13-58-31.png`, `screenshot-2026-10-08_14-43-06.png` e `screenshot-2026-10-08_15-31-02.png`), a gestão do servidor se estende por uma página longa. “Update image” aparece perto do fim, depois da configuração de host e variáveis, imediatamente antes de “Exclude server”. Isso reduz a descoberta da atualização e aproxima visualmente uma operação de manutenção da ação destrutiva de exclusão. `screenshot-2026-10-08_15-31-02.png` mostra a identidade atual e a candidata iguais; nesse caso o backend atual ainda aceita a operação e recria o container com a mesma imagem.

**Mudança proposta:** substituir o formulário permanente por um botão **“Update image”** no conjunto de ações do servidor selecionado, próximo de Restart/Activate/Deactivate. O botão abre um diálogo ou painel lateral identificado com o servidor, mantendo a atualização contextual a esse servidor. Não mover a ação para o cabeçalho global da página: diferentemente de instalar outro servidor, atualizar altera somente o servidor selecionado. Manter “Exclude server” no fim da gestão, separado e com a hierarquia destrutiva existente.

**Fluxo esperado:**

1. A pessoa aciona “Update image” para o servidor selecionado.
2. O diálogo identifica o servidor e mostra a imagem atual como origem, seguida dos campos existentes para tipo e identidade candidata (`local image ID` ou `RepoDigest`). A identidade atual pode continuar pré-preenchida, mas o envio fica bloqueado se tipo e referência imutável forem idênticos; aliases distintos para a mesma imagem efetiva não são dedutíveis apenas no cliente.
3. A ajuda explica que o destino deve ser uma identidade imutável de imagem já presente localmente; não há pull nem build. O broker valida a disponibilidade e correspondência da identidade na execução.
4. A revisão explicita que a configuração do servidor (host, rede, mounts e ambiente) será mantida, e descreve o rollback: há backup da identidade/configuração e tentativa de recuperação para a imagem anterior se a operação falhar; os layers antigos não são arquivados e a imagem anterior precisa continuar disponível localmente.
5. A pessoa marca a revisão e digita o `server_id`. Cancelar fecha o diálogo sem enviar `update-image` ou alterar o servidor.
6. Após a mutação, a UI tenta atualizar o snapshot; só declara **estado verificado** após GET bem-sucedido que corresponda ao servidor/revisão esperados. Se o GET falhar, informa que a operação foi aceita mas o estado não foi verificado; conflito, imagem ausente e falha do broker não são apresentados como sucesso.

**Fronteira inicial:** reaproveitar a operação `update-image` existente, as validações de imagem, backup, journal, CAS e recuperação. A mudança principal é de apresentação/interação. Acrescentar proteção contra atualização sem efeito: bloquear na UI a mesma tupla `(type, reference)` e rejeitar também no serviço **depois da checagem de revisão sob lock, mas antes de `_backup()`/journal**. O broker não deve destruir/recriar container por essa mesma tupla se chamado diretamente. Aliases diferentes (ID versus RepoDigest) para a mesma imagem efetiva ficam **fora deste item inicial**; só prometer detecção após preflight tipado do broker antes do backup, sem comparar tags mutáveis nem dar ao gateway acesso ao Docker. Não adicionar catálogo de imagens nesta fase; isso exigiria API de inventário.

**Critérios de aceite:**

- A ação é visível nas ações do servidor selecionado e não aparece como ação global; o formulário não ocupa espaço persistente no fim da página.
- O diálogo mostra claramente servidor, imagem atual, identidade candidata e que imagens locais imutáveis são aceitas sem pull.
- Abrir/cancelar não envia mutação, não altera o servidor selecionado e não modifica estado persistido.
- A mesma tupla imutável (tipo e referência) não pode acionar remoção/recriação do container nem gerar backup/transição; aliases distintos não são rotulados como no-op sem evidência tipada do broker.
- Fechamento, Escape, foco inicial/restaurado e troca de servidor no diálogo não transferem confirmação para outro ID; rascunho e revisão são revalidados antes do envio.
- A confirmação explícita e revisões global/servidor existentes continuam obrigatórias.
- Em `stopped-persistent`, `update-image` do broker atual pode iniciar o container porque `active=true`; preservar o stop com mudança de contrato testada ou bloquear a operação nesse estado até resolvê-lo. Não usar o texto “mantém a configuração” para prometer que mantém o estado operacional sem prova.
- O resumo deixa claro que a configuração atual do servidor permanece e que rollback depende da imagem anterior ainda existir localmente.
- A UI diferencia mutação aceita de refresh falho e estado verificado; imagem ausente, conflito, broker rejeitado/indisponível e transição não resolvida são comunicados como falha/estado pendente.
- Testes WebUI cobrem ação, abertura/fechamento, formulário, no-op, confirmação, sucesso e erros. Testes de domínio/broker cobrem rejeição antes de backup/journal para tupla igual, ausência de recriação e preservação da configuração no update.

**Arquivos de implementação prováveis:** `webui/src/components/McpDockerManagement.tsx`, possivelmente `webui/src/components/McpContainersPage.tsx` para composição/layout, `webui/src/tests/mcp-containers.test.tsx`, `nanobot/mcp_docker/service.py`, `nanobot/mcp_docker/broker.py` e testes em `tests/mcp_docker/`. Alterações de serviço/broker devem se limitar à garantia contra no-op se a revisão confirmar que ela é necessária no servidor, além da apresentação da UI.

## 6. Quinto item proposto

### Item 5 — Reorganizar o card de detalhe e tornar disponibilidade inequívoca

**Evidência visual:** `screenshot-2026-10-08_19-16-54.png` e `screenshot-2026-10-08_19-17-10.png` mostram `active` em verde e `Gateway intent: running`, mas `Docker state: stopped` e `MCP connectivity: disconnected`. A hierarquia e a cor podem levar a pessoa a concluir que o servidor está operacional, embora a observação diga o contrário. O mesmo card dá peso e espaço semelhantes ao intent, conectividade, tipo da imagem e configuração; o digest imutável ocupa uma linha visual longa. “Host configuration metadata” e “Observed effective Docker configuration” repetem campos e expõem uma lista extensa de mounts inline. “Discovered tools” diz “No tools currently observed” mesmo quando o container está parado, sem distinguir lista vazia de impossibilidade de observar ferramentas no runtime. As capturas de indisponibilidade do broker (`13-55` e `15-47`/`15-52`) exibem outra condição e não devem ser tratadas como evidência do estado Docker/MCP.

**Mudança proposta:** estabelecer uma ordem de leitura em três níveis:

1. **Identidade e estado operacional:** nome do servidor, estado de disponibilidade observado em destaque e indicação curta da fonte da imagem. O digest permanece íntegro no dado e pode ser copiado, mas é truncado visualmente com affordance acessível para copiar/ver o valor completo.
2. **Resumo de estado:** apresentar juntos intent/configuração desejada pelo gateway, estado observado do container Docker e conectividade MCP, com rótulos claros e cores consistentes. `active` significa habilitado na configuração, não disponibilidade. Derivar um resumo somente das combinações definidas abaixo; “MCP conectado” não significa que há tools habilitadas para o agente.
3. **Detalhes sob demanda:** mover metadados de configuração, configuração Docker observada, tools e atividade para subseções ou disclosures compactos. No resumo, manter poucos fatos acionáveis (por exemplo, rede, modo de acesso ao host, persistência e contagem de variáveis). Em detalhes, manter a distinção entre configuração declarada e observada efetivamente.

**Regras de apresentação e semântica:**

| Evidência do snapshot atual | Resumo permitido | Observação obrigatória |
| --- | --- | --- |
| GET falhou, mantendo snapshot anterior | **Dados desatualizados; atualização falhou** | Não atribuir disponibilidade atual ao snapshot anterior; oferecer retry. |
| `brokerStatus` indisponível, observação `unknown` ou erro individual | **Não verificado** | Mostrar causa conhecida e intent salvo separadamente. |
| Docker `running`, MCP `connected`, `active` true, intent `running` | **MCP conectado** | Mostrar tools habilitadas/desabilitadas separadamente; não inferir alcance das APIs. |
| Docker `running`, MCP `disconnected` | **Container em execução; MCP desconectado** | Sinalizar divergência se intent é `running`. |
| Docker `stopped`, `state=stopped-persistent`, persistente e ativo | **Parado conforme configuração** | Não chamar de falha ou disponível. |
| Docker `stopped` ou `container-missing`, intent `running` | **Não está em execução (divergência)** | Diferenciar parado de container ausente nos detalhes. |
| Imagem `image-missing` | **Imagem ausente** | Não inferir conectividade MCP. |
| Demais combinações (incluindo `active=false` com runtime conectado) | **Divergência/estado não classificado** | Preservar os valores individuais e evitar verde de disponibilidade. |

- Verificar precedência: falha de GET ou broker/observação sem evidência confiável prevalece sobre intent, `running` salvo e tools salvas; status do broker pronto isoladamente nunca determina o status do servidor. Se `brokerStatus` faltar num host anterior, não assumir `ready`: usar os resultados de observação disponíveis com proveniência explícita ou sinalizar leitura não verificada.
- Não apagar os estados individuais ao derivar o resumo. Eles continuam visíveis, sobretudo quando divergem, e o texto deve explicar que intent é desejado enquanto Docker/MCP são observações.
- Separar **tools salvas no registro** de **tools observadas agora**. Quando broker/observação falhar, `list()` pode retornar as salvas; quando container parar, `observe` retorna `tools=[]`. Mostrar “não verificáveis agora” e, se útil, a contagem salva com rótulo inequívoco (exige expor sua proveniência no contrato se a UI precisar mostrá-la simultaneamente). Como `_discover()` rejeita lista vazia, “zero tools observadas com MCP conectado” não é caso testável no contrato atual; mudar o broker deliberadamente antes de exigir esse estado.
- Truncar visualmente IDs/digests sem remover informação do DOM acessível; oferecer copiar identidade completa. Evitar `break-all` como apresentação padrão em resoluções largas.
- Remover listas extensas de mounts do resumo e mostrar contagem + detalhes expandíveis. Manter os rótulos dos paths e o acesso somente se o contrato de observação os fornecer; não alegar origem de host quando o snapshot só prova destinations/mount efetivo.
- Resumir environment metadata por contagem e tipos, ou lista de nomes/tipos em detalhes; não renderizar valores nem mask hints de secrets neste card de leitura geral. A edição de secrets permanece no fluxo próprio.
- Se houver divergência entre configuração salva e runtime, exibi-la como tal, sem tratar os metadados configurados como prova do estado aplicado.

**Critérios de aceite:**

- A identidade e a disponibilidade observada são o foco inicial; digest longo não domina nem quebra o cabeçalho e pode ser copiado por teclado/leitor de tela.
- A combinação `active + intent running + Docker stopped + MCP disconnected` aparece inequivocamente indisponível/parada, nunca como servidor saudável ou ativo em sentido operacional.
- Estados desejados e observados permanecem separados, legíveis e acessíveis, com tratamento explícito de unknown/broker unavailable e sem derivação enganosa.
- Tools salvas e tools observadas são distinguidas; ausência de observação não é apresentada como ausência real de tools. Nenhum teste assume sucesso de `tools/list` vazio antes de eventual alteração do contrato.
- Configuração declarada, Docker efetivo, mounts, variáveis e tools deixam de competir visualmente com o estado operacional; detalhes podem ser consultados sem carregar todo o conteúdo no primeiro plano.
- Nenhum valor de secret ou mask hint é exibido no card; a visualização continua coerente com a política de redaction.
- Testes cobrem a matriz acima (inclusive parado intencionalmente, imagem/container ausente, GET falho com snapshot anterior e tools salvas quando broker falha) e acesso/cópia de digest.
- Layout permanece utilizável em largura estreita, zoom, navegação por teclado e leitor de tela, sem depender apenas de cor.

**Arquivos de implementação prováveis:** `webui/src/components/McpContainersPage.tsx`, possivelmente componentes menores para status/detalhes, `webui/src/lib/api.ts` apenas se o tipo atual não representar a evidência necessária, `webui/src/tests/mcp-containers.test.tsx` e eventuais testes backend apenas se for identificada lacuna de contrato. O primeiro passo é confirmar precisamente como `tools`, `dockerObservation`, `mcpConnectivity`, `active`, `state`, `effectiveConfiguration` e `brokerStatus` são preenchidos nos estados observado e desconhecido.

## 7. Sexto item proposto

### Item 6 — Encurtar e agrupar o fluxo de gestão sem esconder operações

**Evidência visual:** `screenshot-2026-10-08_13-58-31.png` e `screenshot-2026-10-08_14-43-06.png` mostram o fluxo inteiro em coluna: autorização do operador, instalação, restore, ações do servidor, acesso por tool, configuração de host/ambiente, atualização e exclusão. A captura de 13:58 deixa a autorização depois do painel de observação e mostra a maior parte das ações fora da primeira tela. `screenshot-2026-10-08_14-23-44.png` mostra um card de restore inteiro mesmo sem nenhum backup. `screenshot-2026-10-08_14-43-06.png` mostra uma linha alta com botão separado para cada tool.

**Mudança proposta:** manter a observabilidade como primeira área e tratar a gestão como um workspace com seções focadas. Mostrar estado compacto **senha necessária / senha fornecida (não verificada)** perto do início da gestão; manter senha e rotação no fluxo administrativo, sem exibir a senha fora do formulário. Não chamar de “desbloqueado” antes de validação do servidor: hoje a senha só é conferida na mutação. Agrupar ações operacionais frequentes, controles de tools e configuração; deixar restore condicional a backups disponíveis e manter exclusão numa área destrutiva separada. Os Itens 1, 3 e 4 continuam donos dos fluxos detalhados de instalação, edição e atualização.

**Regras de apresentação:**

- Com zero backups, não renderizar um card de restore de altura integral; mostrar estado vazio discreto ou ocultar a seção com indicação acessível de que não há backups. Com backups, revelar lista, origem/revisão disponível, conflito e confirmação por servidor; backup de `update-image` para servidor ainda existente **não** é restaurável pela rota atual, que recusa sobrescrita. Não apresentar esse caso como restaurável.
- Mostrar ações de gestão quando senha for fornecida e não houver transição pendente, mas sem afirmar autenticação antecipada; explicar como fornecer senha. Respeitar restrição local/remota do backend, limpar senha em 401/desconexão e mantê-la só em memória.
- Manter Restart/Activate/Deactivate/Start/Stop como ações do servidor selecionado, com habilitação coerente com intent, persistência e observação; ações indisponíveis devem explicar dependência, não apenas parecer quebradas.
- Resumir acesso por tool (quantas habilitadas/desabilitadas) e usar linhas compactas/controles consistentes que escalem para catálogos maiores. Preservar nome, estado, operação individual e acessibilidade; não adicionar bulk action sem confirmar contrato/autorização.
- Manter “Exclude server” visual e espacialmente separado das ações rotineiras, com explicação de backup/remoção e confirmação digitada já existentes.
- Em telas estreitas, preservar ordem de foco e contexto do servidor ao abrir/fechar formulários ou disclosures; evitar obrigar a pessoa a percorrer todos os detalhes apenas para chegar à ação escolhida.

**Critérios de aceite:**

- O resumo read-only vem antes dos formulários, mas status de autorização e caminho para desbloquear são descobertos sem rolar até o fim da página.
- Sem backups, restore não consome um card destacado vazio; com backups elegíveis, restore continua acessível e mantém confirmação/conflito; backups de servidores ainda presentes não oferecem botão ativo de restore.
- O número e estado de tools ficam claros; a lista pode ser operada por teclado/leitor de tela, mesmo com muitas ferramentas, sem uma fila de cartões altos.
- As ações de rotina são distintas da edição de configuração e da zona destrutiva; nenhuma operação é removida nem executada ao abrir um painel.
- Seleção do servidor e estado de autorização não mudam indevidamente ao abrir/cancelar uma ação; erros e transições pendentes ficam visíveis no contexto correto.
- Testes de UI cobrem zero/múltiplos backups (inclusive backup não restaurável), senha ausente/fornecida/rejeitada, tools habilitadas/desabilitadas e viewport estreito.

**Arquivos de implementação prováveis:** `webui/src/components/McpContainersPage.tsx`, `webui/src/components/McpDockerManagement.tsx`, componentes de UI reutilizáveis conforme a solução escolhida e `webui/src/tests/mcp-containers.test.tsx`. Não alterar API/domínio apenas para recolher ou reagrupar informação existente.

## 8. Sétimo item proposto

### Item 7 — Apresentar e configurar a rede separadamente do acesso ao host

**Evidência visual e código:** `screenshot-2026-10-08_14-05-56.png` apresenta “Network access is fixed to none” no formulário de instalação. No código atual, `submitInstall` e seu preview também definem `network: "none"` fixo. Porém `DockerHostConfig` aceita `Literal["none", "bridge"]`; as capturas de estado instalado mostram `network: bridge`, e quatro servidores MCP foram implantados com bridge para alcançar APIs externas. Isso é uma diferença real entre opções do contrato e do fluxo de instalação, não apenas um problema de cópia. O formulário de configuração atual preserva a rede já selecionada, mas não oferece edição explícita.

**Mudança proposta:** substituir a frase de rede fixa por controle explícito e separado de “Acesso à rede” nos fluxos de instalação e configuração. Apresentar ao menos `none` e `bridge` com explicação concisa do efeito e da conectividade concedida, mantendo a política do host Docker e as decisões de deployment fora de qualquer promessa da UI. Exibir a rede configurada; exibir a rede efetiva observada separadamente quando o broker a fornecer. `bridge` não deve ser confundido com modo de acesso aos caminhos do host nem escondido dentro das opções Full/Minimum/Customized do Item 2.

**Fronteira e confirmação:** usar apenas valores aceitos pelo contrato existente, com `none` como default preservado. `none` → `bridge` aumenta o alcance de rede: exigir revisão e confirmação digitada do ID no configure, **independentemente** de mudança de mounts; na instalação manter a confirmação digitada já exigida. `bridge` → `none` também exige revisão, mas não confirmação extra de ampliação. Não alegar conectividade externa garantida: DNS, firewall, daemon, redes e disponibilidade remota podem impedir o acesso. Hoje `configure` recria o container ativo; explicitar essa consequência antes de salvar e revisar o estado `stopped-persistent` antes de habilitar edição de rede nesse caso.

**Critérios de aceite:**

- Instalação e configuração permitem escolher `none` ou `bridge` explicitamente; a UI não afirma que a rede é fixa em `none`.
- A configuração revisada mostra somente mudanças de rede quando só esse campo foi editado; alterações de ambiente ou host mantêm a rede anterior.
- A rede configurada e a observação efetiva nunca são apresentadas como o mesmo fato; desconhecido/indisponível não é inferido.
- Troca de rede explicita a recriação operacional; `none` → `bridge` requer ID digitado mesmo sem ampliação de mounts; `bridge` → `none` exige revisão, e envio sem mudança é bloqueado.
- Testes cobrem instalação nas duas opções, edição/preservação não relacionada, persistência/serialização e erro de rede não suportada. Um browser smoke confirma que a UI realmente envia a escolha, com o gateway e broker da fixture.
- Nenhum caminho de host, mount protegido ou `docker.sock` passa a ser exposto por selecionar `bridge`.

**Arquivos de implementação prováveis:** `webui/src/components/McpDockerManagement.tsx`, `webui/src/lib/api.ts` se o snapshot não representar a rede atual, `webui/src/tests/mcp-containers.test.tsx` e testes de contrato/serviço/broker apenas se a revisão encontrar lacuna. O contrato Python já aceita os dois valores; a primeira hipótese é mudança de UI e testes, a confirmar no fluxo completo.

## 9. Sequenciamento e governança do plano

Os Itens 1 a 7 são propostas sujeitas à validação visual, funcional e contratual. Dividir a execução em lotes que deixem a UI utilizável em cada integração; não publicar texto de funcionalidade antes de ela existir no contrato de ponta a ponta:

| Lote sugerido | Entrega e dependência verificável | Gate antes do próximo lote |
| --- | --- | --- |
| 0 — baseline | Registrar snapshot atual dos casos broker indisponível/`unknown`, observação individual falha, `image-missing`, `container-missing`, `stopped-persistent`, `stopped` inesperado, `running/connected`, com/sem backups e com `bridge`; reproduzir ou classificar a discrepância de rede no diff da captura. Confirmar comportamento de drafts sob polling/409 e de GET após mutação. | Contratos de observação, segredo e CAS anotados; fixture isolada para mutações disponível. |
| 1 — correções de verdade | Item 5 (estado/dados antigos/tools salvas), Item 7 (seleção de rede e aumento de alcance) e proteção de rascunho/feedback do Item 3. Corrigir primeiro comunicação falsa e mudanças silenciosas; preservar `none` como default. | Matriz de estados, comparação de config, `none`/`bridge`, expansão de acesso e GET falho cobertos; broker/gateway da fixture confirmam payload e estado. |
| 2 — fluxos | Item 1 (adicionar), Item 4 (atualizar sob demanda) e restante do Item 3 (editor e revisão), com confirmação contextual, CAS e tratamento de concorrência. | Abrir/cancelar/no-op não escreve; fluxo feliz, conflito e falha de GET separados; secrets nunca aparecem no preview. |
| 3 — composição | Item 6 (gestão/restore/tools) com componentes acessíveis e responsivos; não introduzir mutação nova. | Zero/múltiplos backups, tools numerosas, teclado, foco e largura estreita validados. |
| 4 — acesso ao host | Item 2 somente depois de provar a semântica de `[]`, covers, restore/backups e deploy misto. Pode ser separado dos demais lotes; enquanto não entregue, a UI mostra apenas Full/Customized existentes e valida caminho não vazio. | Testes de contrato e inspeção de mounts nos três modos, restore legados e smoke browser+broker sem expor caminho de controle. |

**Condições transversais de aceite:**

- Toda mutação continua passando pelo gateway com `operator_admin`, revisões CAS, confirmação proporcional e bloqueio de journals pendentes. Após 409, refresh para mostrar estado novo e exigir nova revisão; em erro de GET após mutação, distinguir “aceita, não verificada” de erro da mutação e de sucesso observado. Não reusar confirmação após alteração de ID, revisão ou escopo.
- Polling de 30 s e mudanças em segundo plano não apagam rascunho/valor de secret nem o aplicam a outro servidor. Ao detectar revisão alterada, sinalizar conflito, invalidar confirmação antiga e oferecer descarte/rebase explícito; evitar merger automático de secrets. Mudança de seleção avisa sobre rascunho não salvo ou o descarta de modo explícito.
- Rede e host são dimensões independentes: mostrar diffs somente dos campos alterados, validar `none`/`bridge`, nunca converter lista vazia em Full nem exibir intenção salva como Docker observado. Manter máscaras/covers obrigatórios e `docker.sock` exclusivo do broker.
- Em `webui/`, rodar `bun run test`, `bun run lint` e `bun run build`; no backend alterado, testes focados e `pytest`, `basedpyright nanobot`, `ruff check .` conforme os gates do Percival. Verificar `git diff --check` e teste manual/browser de teclado, foco e layout em largura larga/estreita. Executar fluxo Browser WebUI + gateway + broker em fixture isolada para as mutações afetadas; registrar SHA, resultados e lacunas. Testes locais não fecham Actions no SHA candidato nem gates VPS/reboot/deploy.
- Para mudança de contrato/snapshot (`brokerStatus`, eventual proveniência de tools e novo `mounts=[]`), seguir `.agent/review-guide.md`: provar cliente e host atuais, cliente novo com host mais antigo suportado e cliente antigo com host novo, com ausência de campos/capacidade tratada como **não confirmada**, nunca como autorização implícita a emitir `[]` ou `bridge`. Declarar alcance de compatibilidade e alternativa para host sem suporte antes de habilitar controles novos. Não converter campos opcionais de leitura em mudança de protocolo global sem decisão explícita.

O plano não autoriza publicação, release, alteração de deployment ou execução de mutações em servidores MCP reais. A implementação deve ser verificada em ambiente controlado, usando fixture de UI/gestão e broker isolado; `deep-research` pode servir de fixture visual/read-only quando apropriado, sem reinstalá-lo nem alterar seu acesso, secrets, rede ou imagem real. Alterações de host/rede devem usar servidor descartável e gates Browser + gateway + broker, mantendo os gates VPS/deploy separados.
