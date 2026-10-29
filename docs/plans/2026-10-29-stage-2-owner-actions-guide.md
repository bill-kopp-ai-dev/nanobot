# Stage-2 Percival — guia do owner para destravar dependências

**Data:** 2026-10-29
**Para:** Bill Kopp, owner do Percival e responsável pelas decisões do produto
**Objetivo:** indicar as ações do owner necessárias para retomar os itens de S2-NB
que dependem de CI remoto, manager autenticado, contratos comuns e execução da IaC.

Este guia é operacional e não concede autorização para publicação, deploy, operação
em dados reais ou mutação de runtime. As decisões já dadas nesta campanha estão
resumidas abaixo; não é necessário repeti-las.

## Resumo rápido

As ações imediatas são:

1. Disparar o workflow `Test Suite` do Percival em `main` e compartilhar o link e o
   resultado da execução.
2. Tornar disponível uma sessão/interface autenticada do manager Percival para
   executar o `list()` já autorizado.
3. Revisar os drafts C01/C03 e encaminhar as decisões de detalhe para versionamento
   pelos owners dos repositórios canônicos.
4. Nomear/confirmar o owner técnico da IaC para implementar o preflight de A-011.
5. Confirmar onde está o checkout/repositório canônico `pblabs-mcp-index` e quem o
   mantém, pois as fontes consultadas não deixam o estado atual inequívoco.

Não compartilhe senhas, tokens, chaves, valores de secrets ou arquivos de credencial
no chat, neste guia ou nos artefatos de CI. Configure acesso somente pelo mecanismo
protegido do serviço correspondente.

## 1. CI remoto do Percival e matriz Python 3.14

### O que já foi verificado

O checkout local contém `.github/workflows/ci.yml`, com o workflow `Test Suite` e
gatilhos `workflow_dispatch`, push em `main`, pull request e agenda. A matriz Python
já declara Python 3.12 e **Python 3.14**. O workflow também contém jobs de WebUI,
TUI, build/smoke Docker e MCP broker. A matriz no arquivo não prova que o workflow
remoto esteja habilitado ou que já tenha passado no SHA candidato; o relatório
stage-2 ainda registra CI remoto não observado.

### O que fazer

1. Abra o repositório Percival no GitHub (`bill-kopp-ai-dev/nanobot`) e entre em
   **Actions**.
2. Se Actions estiver desabilitado, habilite-o para o repositório, respeitando as
   políticas da organização. Se não tiver permissão, peça-a ao administrador do
   repositório.
3. Selecione **Test Suite** → **Run workflow**; escolha `main` e inicie a execução.
   O gatilho manual está no workflow atual. Não é necessário fazer push só para
   iniciar o ensaio.
4. Abra a execução e confira o commit/ref executado e o estado de todos os jobs
   aplicáveis. Em particular, confirme `Python (latest, 3.14 + coverage)`, TUI,
   Docker e `MCP Docker broker smoke (Engine 27.5.1)`. Registre falhas e skips sem
   tratá-los como sucesso.
5. Envie o link da execução e o SHA exibido. O agente pode então comparar o resultado
   com o candidato e atualizar a evidência. Se a UI não permitir `Run workflow`, diga
   qual erro/permissão aparece; não compartilhe token.

**Aceite para a pendência:** execução remota completa no SHA pertinente, com logs e
artifacts disponíveis e resultado por job registrado. Uma execução de outro SHA é
histórico útil, mas precisa de análise de aplicabilidade; não fecha automaticamente
o gate do candidato atual.

## 2. Acesso autenticado ao manager Percival

Bill já autorizou executar `list()` e aceitou que a chamada possa disparar
`recover_pending()`, reconciliar transições, atualizar journal/config ou acionar o
broker. Essa autorização não precisa ser repetida para a consulta aprovada.

### O que fazer

1. Disponibilize o Percival Native MCP Manager autenticado numa sessão onde o agente
   tenha a interface/ferramenta de gestão correspondente. Hoje essa interface não
   está conectada à sessão do agente.
2. Se a autenticação depender de segredo, configure-o pelo mecanismo protegido do
   manager ou do ambiente. Não cole o segredo na conversa nem o grave neste plano.
3. Informe que a interface está disponível e qual runtime/instalação é o alvo. O
   executor deve confirmar identidade do owner, contexto e revisão/CAS atual antes
   de chamar `list()`.
4. Após a chamada, revise o inventário datado e sanitizado, inclusive qualquer
   recovery ocorrido. Containers históricos sem ownership comprovado permanecem
   recusados/não adotados até decisão baseada em evidência.

**Aceite para a pendência:** resposta de `list()` pela interface autenticada, revisão
observada, distinção entre estado salvo/observado/conectividade e registro de todo
recovery, sem expor segredos. Não substituir o manager por edição manual de
`config.json`, journal, audit ou registry.

## 3. Revisão e versionamento dos contratos

Os drafts atuais foram encontrados no checkout IaC:

- `positronic-bean-IaC/docs/agent-runtime-contract.md` — S2-C01, status draft 0.1.
- `positronic-bean-IaC/docs/mcp-app-contract.md` — S2-C01/S2-C03, status draft 0.1.

Eles declaram explicitamente que não foram adotados. O C03 deve ser atualizado para
refletir as decisões já tomadas em R-06; a redação atual ainda diz que schema e
versão precisam ser selecionados. O contrato C01 ainda precisa consolidar os perfis
de runtime e os limites de lifecycle acordados pelos produtos.

### Decisões já tomadas — não reabrir

- R-02 (`mounts=[]` por default) foi supersedida por R-10 em 2026-10-29: o default
  do broker Percival é acesso host amplo conforme B14/B22/B23–B25. Apps devem
  configurar explicitamente `[]` ou binds estreitos conforme seu perfil; ampliar um
  perfil reduzido exige confirmação/auditoria.
- Schema externo `server.json`, extensão operacional versionada `pblabs.app.yaml`,
  Docker MCP Catalog fora e `pblabs-mcp-index` como destino dos manifests (R-06).
- Suporte/limitação de cancelamento e deadline declarados por transporte, método e
  deadline; não há obrigação geral de implementar cancelamento (R-09).

### Ação do owner

1. Revise os drafts C01/C03 no checkout IaC, usando as três decisões acima como
   requisitos já aprovados.
2. Em C01, confirme se o texto representa os comportamentos do Percival e do broker:
   init único, mounts por perfil, secrets por referência, sinais/grace/drain,
   estado persistente, readiness e limitações. O draft pede que valores de grace e
   limites sejam baseados em comportamento observado, não inventados.
3. Em C03, confirme que o documento distingue `server.json` do schema de extensão
   `pblabs.app.yaml`, identifica versões/fontes oficiais e não concede privilégios
   de runtime por metadata.
4. Devolva comentários ou uma aprovação explícita com exceções do Percival. O owner
   coordenador deve então versionar os contratos nos seus checkouts canônicos e
   registrar a revisão usada pelos consumidores.
5. Confirme o owner e a localização atual de `pblabs-mcp-index`. Os documentos
   consultados divergem sobre sua existência. Se não houver checkout, indique quem
   o criará e onde; criação de repositório remoto é ação separada e precisa de
   autorização própria.
6. Para S2-C02, confirme com a coordenação IaC em qual repositório ficará o ADR do
   executor/transporte. A receita do broker está definida por R-02/R-10; o ADR deve descrever a
   arquitetura existente e suas fronteiras, não inventar outro broker.

**Aceite para a pendência:** revisão do owner registrada, drafts atualizados e
versionados por seus owners, exceções por produto explicitadas, e referência
imutável (commit/revisão) ligada ao teste do consumidor. Draft aprovado verbalmente,
sem versão rastreável, não fecha a dependência.

## 4. A-011 — preflight implementado pelo owner da IaC

O contrato que o Percival precisa oferecer/testar é: no mesmo daemon Docker, uma
segunda instalação ou writer concorrente deve ser recusado **antes de qualquer
mutação**. Mudar o nome do projeto Compose não conta como isolamento. O Percival
fornece fixture/teste de consumidor; a IaC é dona do preflight do bundle/instalação.

### Ação do owner

1. Nomeie ou confirme a pessoa responsável pela implementação no checkout
   `positronic-bean-IaC` e informe como ela revisará o retorno do Percival.
2. Encaminhe o critério acima e peça que o preflight verifique a identidade/instalação
   já presente antes de escrever, iniciar, atualizar ou remover qualquer recurso.
3. Peça evidência em fixture descartável para os casos: instalação única permitida;
   segunda instalação/writer recusado; nenhuma mutação feita no caso recusado; nome
   Compose diferente não contorna a recusa.
4. Quando a IaC devolver o resultado, forneça o link/commit e a evidência para
   vincular ao teste de consumidor no Percival.

**Aceite para A-011:** teste do contrato no Percival mais evidência da implementação
IaC no SHA correspondente. Só o texto enviado ao owner IaC é uma transferência, não
um fechamento.

## 5. O que não é necessário fazer agora

- Não publicar imagem, wheel, pacote ou código-fonte.
- Não fazer deploy, cutover, piloto ou mudança de pins no runtime.
- Não fornecer Docker Hub push token nem segredo do manager ao agente por chat.
- Não restaurar trackers legados obsoletos.
- Não redecidir schema, destino de metadata ou formato de cancelamento/deadline já
  aprovados. O default de mounts foi atualizado por R-10; perfis por app continuam
  sujeitos à configuração e prova explícitas.

Publicação, piloto e qualquer operação em runtime ativo continuam exigindo as
autorizações próprias já previstas no plano stage-2.

## 6. Retorno simples para destravar a próxima rodada

Quando concluir as ações que dependem de você, basta retornar com:

```text
CI: link da execução Test Suite em main + SHA + jobs verdes/falhos
Manager: interface autenticada disponível (sim/não); alvo identificado
Contratos: comentários/aprovação C01/C03; exceções do Percival
Índice: checkout/path e owner de pblabs-mcp-index (ou confirmar que falta criar)
IaC A-011: owner técnico responsável + como receber a evidência
```

Não inclua tokens, credenciais ou valores de configuração secretos nesse retorno.
