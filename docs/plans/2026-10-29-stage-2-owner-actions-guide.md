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

1. Acompanhar a execução `Test Suite` já disparada em `main` e compartilhar o link,
   o SHA completo e o resultado por job.
2. Manager Percival: consulta manual adiada por decisão de Bill até a atualização
   do agente e confirmação da nova imagem em execução.
3. C01/C03: conteúdo aprovado por Bill em 2026-10-29 na revisão IaC
   `bf9c25201453f1f9c89b9a49030def4b2a053599`; vincular essa revisão aos consumidores.
4. A-011: Bill já é o responsável pela IaC; não há nomeação ou handoff adicional.
    Resta implementar e provar o preflight técnico.
 5. C02 foi aprovado por Bill em 2026-10-29. A-010 passou localmente em DinD
   descartável Engine 27.5.1, incluindo Notes `resources/list/read` e
   `prompts/list/get`, chamadas concorrentes e cleanup do manager. Ainda faltam
   candidato limpo/CI remoto; isso não aprova runtime, piloto ou release.
6. Bill decidiu deferir o índice `pblabs-mcp-index` até identificar seu owner/path.
   Não criar repo nem escolher uma cópia por inferência.

Não compartilhe senhas, tokens, chaves, valores de secrets ou arquivos de credencial
no chat, neste guia ou nos artefatos de CI. Configure acesso somente pelo mecanismo
protegido do serviço correspondente.

## 1. CI remoto do Percival e matriz Python 3.14

### O que já foi verificado

O checkout local contém `.github/workflows/ci.yml`, com o workflow `Test Suite` e
gatilhos `workflow_dispatch`, push em `main`, pull request e agenda. A matriz Python
já declara Python 3.12 e **Python 3.14**. O workflow também contém jobs de WebUI,
TUI, build/smoke Docker e MCP broker. A matriz no arquivo não prova que o workflow
remoto tenha passado no SHA candidato. O relatório stage-2 registra o estado anterior,
quando CI remoto ainda não havia sido observado; a execução iniciada consta abaixo.

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

### Execução iniciada em 2026-10-29

Bill disparou manualmente `Test Suite` em `main`. A captura da página da execução
`#52` mostra o run [4086251288](https://github.com/bill-kopp-ai-dev/nanobot/actions/runs/4086251288)
na fila (`Queued`), com o SHA abreviado exibido como `fead9`. A captura não mostra
conclusão nem resultados dos jobs; portanto, a execução continua pendente de
acompanhamento e ainda não fecha o aceite. Registrar o SHA completo, conclusão,
resultado por job e artifacts depois que o run terminar.

### Atualização reportada por Bill

Bill informou que o item foi executado, mas falhou. A imagem encaminhada mostra o
diff de um commit (`fead9d9`), não a página do GitHub Actions; ela não identifica o
run concluído, os jobs com falha nem a causa. Portanto, registramos a falha como
reportada pelo owner, mas ainda não confirmada contra o run `#52` (`4086251288`).
O aceite permanece aberto até conferir a execução e registrar o SHA completo, a
conclusão, o job/log de falha e os artifacts pertinentes. Não inferir causa nem
tratar o estado inicial `Queued` como resultado final.

**Aceite para a pendência:** execução remota completa no SHA pertinente, com logs e
artifacts disponíveis e resultado por job registrado. Uma execução de outro SHA é
histórico útil, mas precisa de análise de aplicabilidade; não fecha automaticamente
o gate do candidato atual.

## 2. Acesso autenticado ao manager Percival

Bill havia autorizado a consulta e aceitado os efeitos incidentais possíveis de
`recover_pending()`. Em 2026-10-29, decidiu adiar o teste manual até que as atualizações
do agente Percival estejam concluídas e a imagem atualizada esteja efetivamente em
execução. A autorização anterior não é instrução para consultar o manager agora.

### Onde está

O manager é uma página integrada ao Percival WebUI, chamada **Contêineres MCP**,
acessível pela barra lateral ou por **Configurações → Apps**. A rota da página é
`#/mcp-containers`; na instalação Compose local padrão, o endereço é
`http://127.0.0.1:18790/#/mcp-containers`. Não há um servidor MCP independente nem
uma ferramenta de chat chamada “Percival Native MCP Manager” para instalar.

A página chama a API autenticada do próprio gateway
(`/api/settings/mcp-docker/list`). Ao abrir, e depois a cada 30 segundos, ela
carrega a intenção/configuração salva, consulta o broker para observar Docker e
faz handshake MCP (`initialize` e `tools/list`) nos servidores configurados. O
broker, e não o gateway, é o único componente com acesso ao Docker Engine.

### Decisão do owner — adiado em 2026-10-29

O teste será retomado somente depois das atualizações do agente e quando a instalação
alvo estiver rodando a nova imagem. Antes de abrir o manager, identificar essa
instalação e confirmar a versão/SHA ou image ID em execução. A versão atualmente
ativa é antiga/desatualizada e não é evidência adequada para confirmar o agente
atualizado.

**Até essa condição ser atendida, não abra nem atualize a página Contêineres MCP.**
Ao carregar, a página chama `list()` automaticamente e continua atualizando a cada
30 segundos; `list()` pode executar recuperação pelo broker. Não configurar integração
MCP no chat, iniciar/alterar o broker ou modificar o deploy para antecipar o teste.

### O que fazer quando o teste for retomado

1. Abra a página WebUI da mesma instalação Percival que será consultada e entre
   normalmente. Use **Contêineres MCP** na barra lateral, ou **Configurações → Apps**.
   Se estiver usando a instalação Compose local padrão, abra
   `http://127.0.0.1:18790/#/mcp-containers`.
2. A página carrega a lista automaticamente usando a sessão autenticada do WebUI;
   não é preciso configurar uma integração MCP nem informar senha/token ao agente.
   A leitura exige o token normal do WebUI; elevação com senha do operador é para
   mutações e não deve ser solicitada para esta consulta.
3. Antes de abrir a página, identifique qual instalação/runtime é o alvo. Ao carregar,
   o `list()` chama `recover_pending()` antes de observar o estado; pode reconciliar
   uma transição interrompida, atualizar journal/audit ou enviar `recover`/`exclude`
   ao broker. Essa possibilidade está coberta pela autorização registrada acima.
4. Revise o inventário mostrado, incluindo estado salvo versus observado, conectividade,
   tools observadas e qualquer recovery. Se o objetivo for o agente registrar ou analisar
   o resultado, compartilhe apenas a saída/informação sanitizada; não compartilhe token.
   Containers históricos sem ownership comprovado permanecem recusados/não adotados.

**Aceite para a pendência:** resposta de `list()` pela interface autenticada, revisão
observada, distinção entre estado salvo/observado/conectividade e registro de todo
recovery, sem expor segredos. Não substituir o manager por edição manual de
`config.json`, journal, audit ou registry.

## 3. Revisão e versionamento dos contratos

Os documentos submetidos à revisão no checkout IaC eram:

- `positronic-bean-IaC/docs/agent-runtime-contract.md` — S2-C01, status draft 0.1.
- `positronic-bean-IaC/docs/mcp-app-contract.md` — S2-C01/S2-C03, status draft 0.1.

**Aprovação do owner — 2026-10-29:** Bill aprovou o conteúdo dos contratos C01 e
C03. A revisão de conteúdo está concluída. Essa aprovação não altera, por si só,
o status formal de adoção por deployments, não prova implementação de schemas e
não autoriza publicação ou mudanças em runtime.

O conteúdo aprovado corresponde às versões registradas no commit local IaC
`bf9c25201453f1f9c89b9a49030def4b2a053599` (`docs(iac): clarify PBLabs approval
authority`). Use esse SHA como referência imutável desta aprovação; não o trate
como evidência de publicação remota ou adoção em deployment.

O C03 registra `server.json` conforme R-06 e `pblabs.app.yaml` como extensão
operacional versionada; não reabra a seleção desses formatos. O conteúdo aprovado
deve ser preservado ao vincular essa revisão aos consumidores. Lacunas de
implementação/validação continuam sendo gates próprios, não motivo para reabrir
a aprovação do texto.

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

1. **Concluído em 2026-10-29:** Bill aprovou o conteúdo de C01 e C03, incluindo os
   requisitos de runtime, lifecycle, metadata e as decisões R-06/R-09/R-10 acima.
   Não é necessário repetir a revisão de conteúdo.
2. **Concluído localmente:** os textos aprovados estão registrados no commit IaC
   `bf9c25201453f1f9c89b9a49030def4b2a053599`. **Pendente:** vincular esse SHA
   imutável aos consumidores e registrar as evidências correspondentes. Preserve
   o conteúdo aprovado; mudanças posteriores exigem nova revisão.
3. A aprovação dos documentos não equivale à implementação/validação dos schemas,
   à adoção por um deployment ou à autorização para publicar, implantar ou mutar
   runtime.
4. Bill decidiu deferir o índice até haver evidência do owner/path. “Checkout
   canônico” significa a única cópia Git/repo designada como fonte de verdade para
   manifests e schemas, com owner e revisão rastreáveis; `~/.nanobot` é estado/runtime
   (verificado como não Git), não o índice. `~/Projects/pblabs-mcp-index` não existe
   localmente. Não criar repo remoto sem autorização própria.
5. **Destino C02 escolhido por Bill em 2026-10-29:** IaC `docs/decisions/`.
   Bill aprovou em conteúdo o ADR
   `docs/decisions/2026-10-29-iac-c02-percival-executor-transport.md` (revision
   0.2-approved), incluindo implementar resources/prompts na bridge Notes. O arquivo
   ainda não tem SHA commitado para vínculo imutável e aprovação não equivale a adoção
   em deployment nem autorização operacional.

**Aceite para a pendência:** C02 está aprovado; após obter commit SHA, vinculá-lo ao
Percival e ao consumidor. Executar testes de capabilities no candidato limpo e CI
autenticado. A aprovação não substitui essa evidência nem os gates de implementação.

## 4. A-011 — preflight implementado pelo owner da IaC

O contrato que o Percival precisa oferecer/testar é: no mesmo daemon Docker, uma
segunda instalação ou writer concorrente deve ser recusado **antes de qualquer
mutação**. Mudar o nome do projeto Compose não conta como isolamento. O Percival
fornece fixture/teste de consumidor; a IaC é dona do preflight do bundle/instalação.

### Estado e execução

Bill é o responsável pelos projetos e pela IaC; não há nomeação nem handoff
adicional a fazer. Na inspeção read-only em 2026-10-29, a árvore da IaC contém
documentação e evidências, mas não contém `scripts/`, `bootstrap/`, `compose/` ou
`tests/` executáveis de preflight. O `AGENTS.md` da IaC descreve esses diretórios
como estrutura recomendada, não como implementação presente; também adverte que o
workspace local não deve ser presumido como o repositório público `pblabs-iac`.
Não foi encontrada fixture consumidora específica de A-011 no Percival. **Ainda
não há comando para executar este teste.**

Antes de implementar, fechar em uma especificação curta dois detalhes técnicos que
determinam o desenho correto: (a) identidade do daemon Docker, para que nomes de
projeto Compose distintos não contornem a detecção; (b) coordenação atômica e
durável entre processos concorrentes, de modo que uma recusa ocorra antes de
qualquer escrita/ação no daemon. O preflight deve falhar fechado se não puder
estabelecer essas propriedades. Esta restrição de instalação única vale para o
aceite A-011 desta campanha; não altera por si só a arquitetura geral, que prevê
segregação de instalações onde suportada.

Quando esses artefatos existirem, execute-os somente em fixture descartável ou
ambiente isolado, nunca contra o daemon/runtime real. A validação deve demonstrar:

1. Uma instalação única no daemon de teste é aceita.
2. Uma segunda instalação no mesmo daemon é recusada antes de qualquer escrita,
   início, atualização ou remoção.
3. Um writer concorrente sobre o estado compartilhado também é recusado antes de
   mutar.
4. Alterar o nome do projeto Compose não contorna a recusa.
5. O estado da fixture antes e depois de cada tentativa recusada é idêntico.

Adicione também uma prova de corrida: iniciar duas tentativas em paralelo no daemon
descartável e demonstrar que exatamente uma adquire o direito de mutar, enquanto a
outra recusa antes da primeira mutação.

Depois da implementação, use o comando canônico que os repositórios documentarem
para rodar a fixture e os testes do preflight. Registre os SHAs de ambos os
repositórios, os comandos/resultados e a evidência de que as tentativas recusadas
não mutaram o estado.

**Aceite para A-011:** teste do contrato no Percival mais evidência da implementação
IaC nos SHAs correspondentes. A descrição do requisito neste guia, sem a implementação
e os resultados dos testes, não fecha o item.

## 5. O que não é necessário fazer agora

- Não publicar imagem, wheel, pacote ou código-fonte.
- Não fazer deploy, cutover, piloto ou mudança de pins no runtime.
- Não executar ainda o teste manual do manager; ele depende da atualização do agente e
  da confirmação da nova imagem em execução.
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
CI: link da execução Test Suite em main + SHA completo + conclusão e resultado por job
Manager: adiado até a nova imagem do agente estar em execução; depois registrar imagem/SHA e resultado sanitizado de list()
Contratos: C01/C03 aprovados por Bill em 2026-10-29; SHAs/revisões canônicas e vínculo aos consumidores
Índice: checkout/path e owner de pblabs-mcp-index (ou confirmar que falta criar)
IaC A-011: Bill é responsável; implementação pendente + SHAs/resultados da IaC e do teste consumidor
```

Não inclua tokens, credenciais ou valores de configuração secretos nesse retorno.
