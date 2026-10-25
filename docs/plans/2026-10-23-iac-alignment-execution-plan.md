# Harmonização Percival × IaC aberta PBLabs — plano de integração

- **Preparado em:** 2026-10-23, a pedido do operador, para harmonizar os planos de
  implementação com a proposta IaC. **Estado atual:** I1 concluído no escopo de
  arquitetura/handoff e I2 concluído em conformance local Linux/amd64 em 2026-10-23,
  commitado e enviado em `0e7ff072`; **I3 adiado por decisão do operador em 2026-10-23**,
  com pré-requisitos de acesso registrados no §10; I4–I9 pendentes e não iniciados.
- **Resultado pretendido:** Percival consumível pela IaC Docker-first, com distribuição
  pública verificável, implantação por digest e MCP Manager integrado ao índice público,
  preservando os contratos e as evidências do runtime existente.
- **Escopo:** contratos e adaptações do Percival; dependências de IaC, MCPs e índice com
  dono lógico e aceite explícitos. Não duplica código dos outros produtos neste repositório.
- **Autoridade:** a revisão dos planos e execução de I1 autorizam estas edições documentais, não publicação,
  push, instalação no host, alteração de credenciais reais, cutover ou escrita remota.
  Aprovação de arquitetura não é autorização operacional de deploy/release.
  Pedido posterior de bill autorizou implementar/ensaiar I2 localmente e, depois, o
  commit/push do resultado em `main` (`0e7ff072`); publicação, credencial de registry,
  criação ou migração de repositório e deploy continuam sem autorização.
- **Revisão de detalhamento:** 2026-10-23, sobre `a299da09` (árvore inicialmente limpa).
  Naquela revisão I1–I9 ficaram pendentes. A execução posterior de I1 está registrada
  no §11 e na [ADR decidida](../Decisions/2026-10-23-open-iac-contracts.md), com
  [handoff](../iac-p0-contract-handoff.md) e [snapshot das fontes](../references/2026-10-23-iac-source-snapshot.md).
  Contratos aprovados não são schemas/API já implementados.
- **Condição de conclusão:** evidência rastreável de distribuição, implantação,
  lifecycle MCP e recuperação na parte Percival; aceite do operador em I9.
  Este documento não estabelece uma data de entrega nem estima esforço sem baseline.
- **Reconciliação documental em 2026-10-25:** F0–F8 foi fechado por transferência
  para a [continuidade Docker](2026-10-25-docker-standardization-continuation-plan.md).
  D1–D12 e F7 estão encerrados com ressalvas; F1–F5 têm evidências locais posteriores
  nos relatórios F3/F4/F5 de 2026-10-25. C1 segue aberto e I3 segue adiado; I4–I9
  continuam pendentes. Resíduos de runtime/promoção/segredos não desaparecem com o
  fechamento administrativo e mantêm seus donos no sucessor e planos especializados.

**Navegação:** [baseline histórico](#11-baseline-estático-histórico-de-2026-10-23) ·
[resumo I1–I9](#3-work-packages-donos-e-critérios-de-aceite) ·
[subtarefas](#5-roteiro-detalhado-por-work-package) ·
[sequência](#6-sequenciamento-e-caminho-crítico-por-marco) ·
[contratos](#7-contratos-mínimos-arbitrados-em-i1) ·
[verificação](#8-plano-de-verificação-e-matriz-de-falhas) ·
[registro](#10-registro-de-execução-e-critério-de-encerramento).

## 1. Referências, precedência e limites da evidência

As cinco fontes fornecidas estão em `/home/bill/Downloads/positronic-bean-IaC/`:

| Referência | Aplicação neste plano |
| --- | --- |
| `AGENTS.md`, §§2–7 e §9 | Delimitação dos repositórios, contratos externos e fases P0-A–P0-H |
| `PBLabs_Open_IaC_DockerHub_Implementation_Guide_v1.0.md`, §§0–8 e 10–17 | Guia principal; imagens, Compose, bootstrap, estado, template/índice e integração nativa |
| `PBLabs_MCP_Distribution_Services_Strategy_v2.0.md`, §§4–8, 9.1 e 21 | Distribuição aberta, curadoria, OCI upstream e decisões pendentes |
| `iac-docker-first-strategy_v2.0_dockerhub.md`, §§6, 9–10, 26–32 e 37–39 | Ownership, locks e transação de update/recuperação |
| `stack_v0.3_dockerhub.md`, §§20, 25–28 e 39–41 | Secrets, logs, backup/update, capacidades científicas e lacunas operacionais |

Precedência de referência: guia de implementação → estratégia de distribuição →
estratégia IaC → stack. As instruções no `AGENTS.md` da pasta de fontes descrevem aquele
workspace; não substituem as instruções deste repositório. Exemplos, paths internos,
nomes de APIs e schemas das fontes são propostas, não componentes homologados.

O [relatório comparativo](../reports/2026-10-23-iac-strategy-vs-percival-gap-analysis.md)
é insumo diagnóstico, não ADR nem aceite. Para execução, verificar o artefato atual e
os registros mais recentes, incluindo a
[auditoria planos × código](../reports/2026-10-23-auditoria-planos-vs-codigo.md).
Em particular:

- **`0.1.0` já é a primeira versão pretendida de Percival**, conforme
  [AGENTS.md](../../AGENTS.md) e [governança](../percival-governance.md). `nanobot-ai`
  `0.3.5` é metadado herdado; não reabrir a decisão nem publicá-lo como release Percival.
- Broker e manager existem: `nanobot/mcp_docker/broker.py`, `service.py`, política de
  mounts e Compose sidecar. Aproveitar essa base. Existência não fecha os gates de
  browser, VPS, segurança ou integração com catálogo. Socket ausente no gateway não
  prova ausência de acesso indireto via token/broker ou escrita no host.
- Image ID local e digest de manifesto OCI são identidades diferentes. Nunca preencher
  um digest de registry a partir de um ID local, tag ou valor de exemplo.
- Scans de 2026-10-09 não descrevem automaticamente candidatos posteriores. A triagem
  de 2026-10-10 fechou um item documental, não concedeu waiver. Revalidar o candidato
  pela [política de postura](../Decisions/2026-10-09-docker-image-posture-policy.md).
- Compose já contém probes e `user:` não-root. Não exigir `HEALTHCHECK` HTTP global em
  imagem multimodo (CLI/gateway/API), nem tratar `USER root` no Dockerfile isoladamente
  como usuário efetivo. I2 verifica processo, entrypoint, overrides e permissões reais.

### 1.1 Baseline estático histórico de 2026-10-23

Inspeção estática em `a299da09`, anterior a I2/D7/F3/F4/F5; não é descrição atual de
defeitos a corrigir novamente. I2 unificou binds/API e probes, D7 corrigiu init e F3
de 2026-10-25 vedou instalação tardia de channels na imagem. Links apontam
para o checkout e devem ser pinados ao SHA no relatório de implementação.

| Observação direta | Consequência executável |
| --- | --- |
| [`contracts.py`](../../nanobot/mcp_docker/contracts.py) aceita somente `local-image`/`pinned-image`; modelos usam `extra="forbid"`. `McpDockerConfig` não contém catálogo, publisher, versão ou plataforma | I6/I7 precisam de desenho de persistência/migração; adicionar campos ao JSON atual quebra leitores antigos. Não anunciar `repository` ou `trustedCatalogs` como campos aceitos hoje |
| [`broker.py`](../../nanobot/mcp_docker/broker.py), `ready()`/`image_reference()`/`_spawn()`: Engine rootful Server 27.x; Client 27.x/29.x; inventário obrigatório; imagem local; spawn sem pull | I4 homologa versão exata do host/Compose. I6 acrescenta aquisição autorizada sem substituir o controle de identidade no spawn |
| `ready()` exige **um** bind de estado no gateway em `/home/nanobot/.nanobot`, com origem igual ao path inventariado. [`mount_policy.py`](../../nanobot/mcp_docker/mount_policy.py) exige token sob esse estado verificado | Um bind de estado monolítico e token dentro dele são baseline. Token separado em `/srv/pblabs/secrets/` ou fragmentação de estado exigem mudança de contrato/código e provas, não apenas Compose |
| [`docker-compose.mcp-broker.yml`](../../docker-compose.mcp-broker.yml) só troca o bind do gateway; API/CLI da [base](../../docker-compose.yml) mantêm `~/.nanobot` | I4 deve mapear todos os serviços habilitados para o mesmo estado da instância; caso contrário, `auth init` pode criar o verifier no volume errado |
| [`broker.py`](../../nanobot/mcp_docker/broker.py), `_exchange()`, usa `docker attach`, handshake por troca e timeout; allowlist MCP contém quatro métodos. `_name()` deriva nome apenas de `server_id` | Não presumir bridge MCP genérica, streaming/cancelamento ou duas instalações isoladas pelo nome do projeto Compose. I2/I6 delimitam suporte e testam colisões |
| [`service.py`](../../nanobot/mcp_docker/service.py) serializa via `WebUISettingsConfig`, persiste `config.json` e recupera transições; [`client.py`](../../nanobot/mcp_docker/client.py) tem timeout HTTP de 30 s | I6 não mantém pull longo dentro da transação de configuração nem assume sucesso após timeout. I7 integra export sem criar outro writer canônico |
| [`ci.yml`](../../.github/workflows/ci.yml) constrói as duas imagens, gera SBOM e manifests; não há etapa de scanner de vulnerabilidades nos workflows atuais | SBOM não é scan. I3 deve acrescentar enforcement da política, além do build/push protegido; alegação de Trivy no CI do relatório comparativo não se sustenta neste checkout |
| O job Docker de `ci.yml` contém asserção `id -u = 0` sobre CLI que herda `user: 1000:1000` | Divergência estática a reproduzir/corrigir em I2/C1 antes de reutilizar esse job como prova de permissões; não é falha de run observada nesta revisão |
| [`Dockerfile`](../../Dockerfile) permite instalação de dependências de channels em `/app/.venv` no startup; [`entrypoint.sh`](../../entrypoint.sh) faz drop para UID 1000 no caminho root | Imagem por digest não fixa dependências instaladas depois. I2 registra channels incluídos e comportamento sem rede/UID alternativo; não habilita canais que dependem de mutação não homologada |
| [`auth.py`](../../nanobot/cli/auth.py) oferece `auth init/change/reset/status`; `init` é interativo e recusa sobrescrever senha existente | Bootstrap precisa do setup antes do bind externo, sem senha default/flag inventada. Reexecução idempotente não pode rotacionar nem recriar credenciais |

Os relatórios anteriores têm snapshots de host, CLI e CI que podem ter envelhecido.
Usar suas evidências com identidade/data; reconferir ferramentas e comandos instalados
na execução. Ausência de pipeline neste checkout não prova ausência de imagem no registry.

Estas fontes locais precisam ser disponibilizadas/versionadas no workspace IaC antes
da execução por outro ambiente; este plano registra nomes/versões/seções, não presume
que o diretório Downloads seja um repositório público ou uma dependência de runtime.

## 2. Contrato-alvo comum aos planos ativos

1. **GitHub** mantém fonte/IaC/curadoria; **GitHub Actions** verifica e publica;
   **Docker Hub** é o registry principal das imagens oficiais abertas. I1 confirmou
   GitHub atual `bill-kopp-ai-dev`, futuro `p-bean-labs` e Docker Hub `pbeanlabs`;
   core: `percival-gateway` e `percival-mcp-broker`. Nomes/donos estão decididos;
   acessos, disponibilidade, publicação e URL operacional do índice não foram verificados.
2. Terceiros são consumidos do registry OCI upstream homologado, sem mirror obrigatório.
   Docker MCP Catalog e GitHub Pages são opcionais; Cloudflare Pages não é requisito.
3. OpenTofu provisiona infraestrutura; cloud-init/bootstrap idempotente prepara o host;
   Compose gerencia o **core**, incluindo gateway/API quando aplicável e broker sidecar.
   O **MCP Manager nativo do gateway**, com executor broker, é dono de seus MCPs.
   MCP `externally-managed` tem dono externo explícito; WUD, se adotado, só atua no core.
4. Runtime atual preserva imagens locais por ID/RepoDigest e `run --pull=never`.
   A integração nova precisa de **aquisição explícita e verificada por digest** antes
   do spawn. I1 escolheu extensão restrita do broker; manter `--pull=never` no spawn é
   compatível com um pull prévio restrito. Não habilitar pull arbitrário ou `docker_run`.
5. Produção instala artefatos publicados por tag de versão + digest OCI real, não faz
   build do checkout na VPS. Build local, `:dev` e worktree candidates continuam caminhos
   de desenvolvimento; não são release nem estado implantado homologado.
6. `deployment.yaml` declara intenção; tooling externo de deploy escreve
   `deployment.lock` após pull/start/readiness/persistência validados. O MCP Manager
   exporta `capabilities.lock`, sem secrets, a partir de seu estado canônico.
7. `/srv/pblabs/` é layout **do host de referência**, não mudança automática dos paths
   internos. Mapear `~/.nanobot`, a proposta `.percival` e o destino aprovado em I4/C2;
   preservar `/home/nanobot/.nanobot` até migração explícita. Não dividir diretórios por
   simples bind de paths que a aplicação ainda não lê.
8. Atualização do core é externa ao agente; release não atualiza VPS silenciosamente.
   Classificar `runtime-only`/`migration-bearing`; imagem antiga não desfaz migração de
   dados. Preservar backup, compatibilidade e recuperação da combinação inteira.
9. Manifests são dados não confiáveis; descoberta não concede rede, mounts, secrets ou
   tools. B14–B25 e seus riscos indiretos são baseline, não aprovação genérica da loja.
   Perfil/permissões foram decididos em I1: consentimento local explícito, novos
   installs de catálogo sem host binds/
   rede por default e recusa de requisito obrigatório sem enforcement; preservar os
   registros atuais. A implementação e prova dessas regras pertencem a I4/I6.
10. P0 cobre distribuição aberta. Premium GCP, entitlements, billing, marketplace,
    Kubernetes, registry próprio e entrega privada de clientes exigem escopo separado.

## 3. Work packages, donos e critérios de aceite

IDs **I1–I9** pertencem a este plano. P0-A–P0-H abaixo são as fases do **guia de
implementação/AGENTS de referência**; os outros documentos usam numerações diferentes.
F0–F8, D1–D12, C1–C4 e A1–A9 dos planos existentes conservam seus próprios significados.

| ID / fase | Entrega e dono lógico | Dependências | Critério de aceite / evidência |
| --- | --- | --- | --- |
| **I1 / P0-A** | Contratos e arbitragem — bill decide/revisa; agente prepara | Fontes e decisões atuais; confirmações do operador nesta sessão | **Concluído em 2026-10-23 — arquitetura/handoff.** [ADR](../Decisions/2026-10-23-open-iac-contracts.md), [matriz de contratos/compatibilidade](../iac-p0-contract-handoff.md) e snapshot com hashes. Contas/names, fonte de versão, aquisições, consentimento, topologia, C1–C8 e ordem B13/público/VPS decididos. Metadata executável é I2 antes do candidato; acesso/publicação/schemas/API e demais gates continuam pendentes |
| **I2 / P0-B** | Agent Runtime Contract Percival — repositório do produto | F2–F4/D7; decisões I1 disponíveis | **Concluído localmente em 2026-10-23.** [Runtime contract 1](../agent-runtime-contract.md) e [relatório por I2.1–I2.6](../reports/2026-10-23-i2-runtime-contract-conformance.md): metadata/lock/fallback/defaults `0.1.0`; modos/writers/UID/GID/init/probes; bind CLI/API/gateway unificado, API opt-in; root-com-drop/Render flag fail-closed e sinais; startup/recreate/crash/persistência, matriz com broker baseline e cliente v1. 19 checks de containers em Engine 27.5.1 rootful `linux/amd64`; pytest focado, lint/typecheck passaram. Builds worktree, não release; ARM64/Render serviço/Actions/VPS não certificados. Resultado commitado e enviado em `0e7ff072` (`origin/main`), por autorização do operador |
| **I3 / P0-B** | Distribuição das imagens core — CI dos repositórios de produto | I1/I2 para preparar pipeline; I6/I7 quando incluídos no candidato final; D2/D6/D7/D8/C1 aplicáveis e B13 antes de publicar | PR build/test/scan sem push. Release aprovada via workflow protegido Buildx, permissões mínimas e token de push só no CI; capturar digest OCI e plataforma por imagem, SBOM/scan/proveniência. Pull anônimo com configuração Docker limpa + smoke independente; registro fonte→versão→digest→plataforma. Publicação não dispara deploy. Estado: **pendente, não iniciado — adiado por decisão do operador em 2026-10-23**; pré-requisitos de Docker Hub e de owner GitHub registrados no §10 |
| **I4 / P0-C** | Handoff de deployment — contratos Percival aqui; bootstrap/Compose/locks/OpenTofu no workspace IaC separado | I1/I2; I3 para instalação pública; C2 antes de escrita em VPS | Receita de deploy sem `build:`/`:dev`, referências core por tag+digest, broker sidecar/namespace de rede preservados; config agregada validada no diretório-base real. Preflight resolve UID/GID/socket/data-root/token/nome real do gateway, paths protegidos e versões Engine/CLI. Bootstrap idempotente e caminho manual; `deployment.lock` cobre as duas imagens e compatibilidade do core, com exclusão mútua/gravação atômica após validação. Instalação limpa bem-sucedida cria lock; falha não o avança. Layout/backup/retorno ensaiados em fixture; validação estática OpenTofu antes de qualquer plan/apply autorizado. Estado: **pendente** |
| **I5 / P0-D, P0-E, P0-G** | MCPs oficiais, template e índice — mantenedores dos MCPs e workspace do índice | I1 para identidades/schema; F2–F5/D5/D7/D8/C1 para candidatos selecionados | Weather primeiro e OSM segundo, selecionados em I1. Pipelines replicáveis com protocolo real, `server.json` no schema oficial aplicável, complemento operacional e README coerentes; publicar/homologar dois MCPs no Docker Hub, pull anônimo, digest/plataforma comprovados. Índice curado por PR com Markdown/YAML→JSON determinístico, schema versionado e pelo menos um comunitário upstream sem reatribuição/mirror. URL real ou raw em commit pinado; Pages opcional. Estado: **pendente** |
| **I6 / P0-F** | Adapter de catálogo e aquisição autorizada — Percival gateway/manager + executor broker | I1, I5a/I5b para primeira prova; I5c para aceite completo; operações/contratos existentes da trilha B | Busca/inspeção/instalação configuram somente artefato homologado por digest/plataforma sob policy/consentimento local. Evoluir API tipada do broker se necessário; nenhuma tool Docker genérica, socket/CLI no gateway ou comando de Markdown executado. Aquisição explícita pode preceder spawn `--pull=never`; testar mismatch, imagem ausente, origem não confiável, permissão negada, timeout/429 e concorrência. E2E por transporte real com `initialize`, `tools/list` e tool segura. Manter compatibilidade local-image/pinned-image e versões antigas de cliente/host (B3); não ativar `source.type: repository`/`trustedCatalogs` porque B20 os previa como futuros. Estado: **pendente** |
| **I7 / P0-F** | Export/reconciliação `capabilities.lock` — MCP Manager no gateway | I1; base local existente para export inicial; I6 para catálogo/aquisição no restore | `tools.mcpDocker` continua fonte canônica até migração aprovada. Export versionado, atômico e associado à revisão registra publisher/origem/registry/imagem/versão/digest/plataforma/owner/status sem valores de secrets, env ou paths privados desnecessários. Image ID local sem RepoDigest é identificado como local/não publicado, nunca fabricado como OCI. Restore exige configuração/backup privado e autorização local, não só esse export sem secrets; conflito/export obsoleto/falha é observável. IaC/WUD não escreve esse lock e ele não vira segundo registry editável. Estado: **pendente** |
| **I8 / P0-H** | Resiliência, update e recuperação — produto + IaC, cada qual no seu domínio | I2/I4 para core local; I6/I7 para MCP; I3/I5 para prova pública; D9 e C3/C4 nos respectivos domínios | Exercitar instalação sem catálogo/registry, cache, 429/backoff limitado, ausência de fallback para digest novo; não desinstalar MCP existente em indisponibilidade. Core update externo com falha e retorno de gateway+broker compatíveis, locks não avançados em falha, migração de dados com backup/restore explícitos. Backup do estado completo (config/auth/workspace/KG/MCP/audit/locks/secrets protegidos), não só transições MCP; RPO/RTO definidos e restore medido em fixture. Verificar logs sem conteúdo científico/segredos e risco indireto no alvo; `:ro` no socket não equivale a bloquear mutações na API Docker. Estado: **pendente** |
| **I9 / P0-H** | Aceite de integração IaC — operador assina; agente consolida | I1–I8, gates de produto aplicáveis e C1–C4/D12/autenticação | Matriz requisito→repo/SHA→digest→teste→evidência→decisão, com aceite local, público/registry, staging/VPS e release B13 separados. Nenhuma funcionalidade anunciada como entregue por existir plano/template. Estado: **pendente** |

**Dependências incrementais:** I4 pode desenvolver/ensaiar bootstrap
e recovery em fixture antes de C2; C2 é pré-condição de aplicação no VPS, não de
preparação local. I6 começa com o schema e **primeiro** MCP homologados de I5; o segundo
próprio/comunitário fecha P0-G depois, sem bloquear a prova P0-F. I8 é incremental por
domínio: seus ensaios locais de core/backup precedem C3; a prova no alvo é compartilhada
com C3/C4 e consolida I8/I9 depois. C3 não espera o fechamento integral de I8 para poder
produzir essa própria evidência.
Sequência de release/B13 e VPS foi arbitrada em I1.6: aprovação de publicação é
anterior ao pull público, que bloqueia homologação/promoção; VPS/I9 têm aceite próprio.

**Compatibilidade transversal (detalhada no §5):**

- **I2:** documentar/provar Compose como implantação canônica decidida em I1;
  `gateway install-service`/Render ficam como caminhos separados de compatibilidade/
  desenvolvimento, sem dois processos gravando o mesmo estado. Não remover interfaces ou
  variantes de deployment sem avaliar os consumidores; refletir a decisão no runbook.
- **I5/I6:** rever presets/scripts que contornem o manager ou dependam de binário Docker
  no gateway; verificar os achados `agent-docker` e `@latest` antes de corrigi-los.
  Atualizar/remover smoke obsoleto `tests/test_docker.sh` conforme o contrato real,
  sem introduzir um segundo executor. Índice indisponível não pode forçar o uso desses
  caminhos nem mudar a imagem instalada.
- **I4/I8:** publicar apenas exemplos de configuração limpos, sem paths de fixtures do
  operador, `.env` real ou flag `PERCIVAL_DISPOSABLE_ENGINE29` no deployment de produção.
  Registrar defaults/opt-in de administração remota e permissão por aplicativo; não
  copiar a configuração viva como template nem mudar os defaults atuais por esta edição.

### Arbitragem de I1: decisões que não podem ficar implícitas

**Resultado:** decisões fixadas na ADR/handoff de I1; a lista abaixo é o escopo de
arbitragem preservado para rastreio, não questões ainda sem encaminhamento.

- **Aquisição:** escolher extensão restrita do broker ou helper confiável de pré-aquisição,
  sem dar ao agente um shell Docker. A primeira opção é a recomendação para o alvo
  first-class; uma pré-carga manual pode servir à transição, não fecha I6.
- **Schemas divergentes:** resolver C1–C8 do relatório comparativo com contrato canônico,
  revisão e testes de compatibilidade: `distribution` no manifest operacional, ID
  comunitário, campos/owner do lock, nomes/layout e vocabulário de lifecycle. Não copiar
  YAML ilustrativo como schema homologado. Divergência de escopo do token premium fica
  registrada para o dono da estratégia, sem puxar premium para P0.
- **Permissões:** resolver a tensão entre baseline Full de B14/B23 e pedidos de mounts
  restritos da loja. Registrar limites, consentimento e risco indireto; não transformar
  um manifest em concessão automática nem estreitar a instalação atual silenciosamente.
- **ADRs:** aditar a decisão local-only/B20 quando o contrato novo for aprovado;
  preservar as decisões históricas e a política de vulnerabilidades. A escolha de
  Docker Hub como alvo não revoga limiares de severidade, B13 ou a revisão do histórico
  privado antes de divulgação.

## 4. Rastreio único: integração com os planos existentes

| Assunto | Dono do gate | Uso neste plano |
| --- | --- | --- |
| Fases históricas F0–F8 e padrão local de imagem/runtime | [padronização arquivada](closed/2026-10-09-docker-standardization-refactor-plan.md); [continuidade ativa](2026-10-25-docker-standardization-continuation-plan.md) | Contratos/evidências históricos; resíduos ativos R01–R14 e referências de gates, não prova de distribuição |
| D1–D12: credencial, proveniência, Khan, vulnerabilidade, runtime, pins, runbook e F7/F8 | [fechamento Docker arquivado](closed/2026-10-23-fechamento-padronizacao-docker-f4-f5-f7-plan.md) | Encerrados com limites; I3/I5 revalidam o candidato afetado, sem reabrir os IDs administrativos. R06/R07 cobrem exposição/persistência de chaves válidas, distinta do segredo legado D1 |
| A1–A7 KG; B1–B7 MCP/browser; C1 CI e C2–C4 VPS | [plano integrado](2026-10-23-integracao-pendencias-kg-e-mcp-docker-plan.md) | C1 continua verificação remota, não pipeline de push; C3 consome contrato de paths/IaC de I4 |
| A1–A9 de autenticação e ensaio P2–P4 | [senha única](2026-10-11-single-password-acceptance-closure-plan.md) | Reutilizar provas do candidato; persistir verifier/segredos em I4/I8 sem copiá-los para locks |
| Publicação, índice, aquisição, export de lock e aceite IaC | **I1–I9 deste plano** | Lacunas novas têm dono sem reabrir planos arquivados |

O aceite local F7 pode referenciar I1/I2/I4 quando o contrato for alterado; **não precisa
esperar publicar dois MCPs para continuar trabalho local independente**. Inversamente,
F7 assinado não fecha I9. Nenhum gate é encerrado apenas por encaminhamento a outro plano.
O P0 conjunto de Percival e Positronic exige evidências de ambos; I9 comprova a parte
Percival, não certifica o outro produto nem autoriza edições nos seus repositórios.

## 5. Roteiro detalhado por work package

Subtarefas `I<n>.<m>` refinam os nove itens, não criam fases de produto novas. Estado
inicial de todas: **pendente**. Cada implementação deve informar arquivos realmente
alterados, verificação e evidência, além do contrato aprovado usado como entrada.
Esse é o estado da abertura; I1.1–I1.7 foram concluídos como arquitetura/handoff,
com resultados por subtarefa na matriz de execução do handoff.

### 5.1 I1 — Arbitragem, identidade e contratos

**Entrada:** baseline §1.1, fontes §1, decisões B14–B25 e política de postura.
**Responsável:** agente prepara; operador e mantenedores dos contratos decidem.

1. **I1.1 — Inventariar entregáveis e responsáveis.** Identificar checkouts/repos reais
   de produto, IaC, índice, template e MCPs; registrar dono nominal, revisor e acesso
   necessário. Se não existe workspace IaC, registrar a dependência de sua criação;
   Downloads continua fonte documental. Versionar as cinco referências ou um snapshot
   autorizado com SHA-256/data no workspace responsável, preservando proveniência.
2. **I1.2 — Identidades e versão.** Confirmar controle da org GitHub, namespace Docker
   Hub, repos públicos e nomes das **duas** imagens core. Registrar política Git tag
   `v0.1.0` → imagem `0.1.0` se adotada, sem sobrescrever tags publicadas. Escolher fonte
   de versão; inventariar `pyproject.toml`, fallback Python, Dockerfiles, defaults Compose,
   locks e labels afetados. Nome de pacote Python e rebranding amplo não se decidem
   por inferência; a mudança de versão deve manter locks/build/metadata coerentes.
3. **I1.3 — ADR de arquitetura.** Preparar em `docs/Decisions/` um aditamento datado
   (nome a definir) a local-only/B20: índice estático, aquisição restrita, contrato de
   confiança, compatibilidade/migração e owners. Broker é a recomendação para aquisição
   first-class; helper prévio confiável é opção a comparar por autorização, timeout,
   auditoria e custo de operação. Manter spawn `--pull=never` em ambas as opções.
4. **I1.4 — Arbitragem dos schemas.** Resolver C1–C8 do relatório comparativo numa
   tabela `conflito → escolha → dono → versão → consumidores → teste`. Fixar onde mora
   a release aprovada, como catálogo e app são vinculados, identidade comunitária,
   lifecycle, nomes de arquivos, owners e canais. C4 premium fica com encaminhamento
   fora de P0. Publicar referências canônicas, não editar contratos concorrentes.
5. **I1.5 — Policy e topologia.** Definir consentimento de instalação/update, concessões
   por app e quem configura confiança no índice. Comparar requisito solicitado ao que
   o executor realmente consegue impor (§7.3). Decidir uma instância Percival por daemon
   como limite inicial ou implementar isolamento comprovado: hoje nomes MCP não incluem
   identidade da instalação. Fixar Compose como caminho canônico e status de Render/
   `install-service`, preservando consumidores e single-writer.
6. **I1.6 — Ordem release/aceite.** Registrar condições anteriores a B13 e condições
   verificáveis somente após publicação (pull anônimo, bootstrap público, índice real).
   I9 depende de I3/I5 e não pode ser pré-requisito integral da primeira publicação.
   Se a governança exigir evidência VPS anterior à publicação, propor staging com
   artefatos privados transportados de modo autorizado (sem build na VPS), ou outro
   aditamento explícito. Se exigir C3 público antes de I3, registrar o ciclo como
   bloqueio; não eliminá-lo presumindo waiver nem publicidade autorizada.
7. **I1.7 — Pacote de handoff.** Registrar versões e repositórios canônicos de runtime,
   deployment, app/index e capabilities; responsáveis por revisão e mudança incompatível.
   Obter aceite das partes antes de fixar o candidato que consome esses contratos.

**Saída:** ADR decidido e matriz de contratos/compatibilidade; questões sem decisão
explicitamente bloqueiam apenas seus consumidores. O aceite arquitetural não executa
publicação nem concede privilégios ao LLM. Não marcar I1 fechado com ADR ainda proposto.

**Executado em 2026-10-23:** [ADR decidida](../Decisions/2026-10-23-open-iac-contracts.md),
inventário de oito checkouts/remotes/SHAs e três workspaces ausentes, hashes das cinco
fontes e snapshot semântico autorizado; C1–C8 e matriz de compatibilidade no
[handoff](../iac-p0-contract-handoff.md). bill confirmou decisões e responsabilidade/
revisão nesta sessão. Não houve verificação técnica das contas nem criação de repo.

### 5.2 I2 — Contrato real de runtime e conformance do core

**Entrada:** código atual; I1 para escolhas que alteram suporte ou identidade pública.
**Superfície:** `Dockerfile`, `Dockerfile.mcp-broker`, `entrypoint.sh`, Compose e smokes
existentes, `nanobot/cli/gateway_runtime.py`, autenticação e cliente/broker tipados.
Antes de fixar candidato, aplicar o inventário de metadata do handoff I1: fonte
`pyproject.toml`, `uv.lock` regenerado, fallback/metadata instalada, defaults e labels
coerentes com `0.1.0`, sem renomear pacote/import/CLI nem alterar dependências sem causa.

1. **I2.1 — Matriz de modos.** Documentar gateway (`gateway`), API (`serve`), CLI
   (`status`, `auth init/change/status`) e broker (`python3 -m nanobot.mcp_docker.broker`).
   Para cada um: imagem, argumentos, config/home, diretórios lidos/escritos, UID/GID,
   capabilities, rede, probe, exit code e comportamento de SIGTERM/EOF. Gateway+broker
   é a topologia da capability Docker; API é habilitada somente quando configurada.
2. **I2.2 — Estado e primeiro startup.** Demonstrar que a CLI encontra a mesma instância
   do gateway. Executar setup de config/provider e senha fixture pela interface real,
   antes de expor listener não-loopback. Provar recusa sem verifier/chave API e
   recuperação após setup. API e senha humana têm contratos distintos; não converter
   uma credencial na outra. Não exigir chamada LLM paga para uma prova de processo.
3. **I2.3 — Permissões efetivas.** Cobrir Compose não-root com diretório correto e UID
   alternativo aprovado, erro de ownership, caminho root-com-drop e falha de `setpriv`.
   Inspecionar PID/UID/GID/capabilities efetivos sem dump de env. Corrigir a asserção root
   divergente do CI (§1.1) após reprodução, sem remover a prova de drop. Validar acessos
   à `.venv` e aos channels; declarar quais estão pré-instalados na imagem de release.
4. **I2.4 — Processo e saúde.** Verificar init único, encaminhamento de sinais, prazo de
   shutdown e ausência de órfãos. `STOPSIGNAL SIGTERM` explícito pode documentar o
   default; não substitui teste. Gateway `/health` e API `/health` não comprovam a
   capability Docker: agregar probe autenticada tipada do broker e handshake MCP.
   A probe atual do sidecar combina `ready()` e TCP; TCP sozinho não prova auth/protocolo.
5. **I2.5 — Startup/recreate.** Subir gateway e broker na rede compartilhada; não criar
   dependência circular de health entre ambos. Recriar gateway com novo container ID
   **e** broker para reatar `network_mode: service:...`; provar reconexão, hydrate e
   persistência. Testar broker atrasado, token inválido, Server incompatível e crash.
6. **I2.6 — Compatibilidade.** Versionar matriz gateway↔broker atual/antigo e cliente↔host
   de B3; campo ausente não autoriza capacidade nova. Registrar versões do protocolo,
   formatos de config e transportes realmente suportados. Verificar o empacotamento
   mínimo do broker: todo módulo novo precisa entrar na imagem, com dependências pinadas.

**Saída:** contrato runtime no produto (arquivo a fixar em I1) e ensaio `linux/amd64`
com matriz preenchida. Falha de processo/estado bloqueia promoção do candidato; limitar
suporte é decisão explícita, não motivo para ocultar teste falho. ARM64 tem gate próprio.

**Executado em 2026-10-23:** I2.1–I2.6 entregues em
[`docs/agent-runtime-contract.md`](../agent-runtime-contract.md), com resultados,
imagens, comandos e limites no [relatório I2](../reports/2026-10-23-i2-runtime-contract-conformance.md).
V01 coberto localmente; V02/V03/V04 têm provas locais e conservam as extensões
I4/I8/C1/B3. Sem verifier, recusa é 401 em bootstrap/WS protegido, não proibição
de todo listener de login; documentação corrigida conforme comportamento medido.
Nenhum gate de publicação/CI remoto/VPS encerrado por este ensaio.

### 5.3 I3 — CI e distribuição das duas imagens core

**Entrada:** I1/I2 e gates de D2/D6/D7/D8/C1 aplicáveis ao candidato; B13 antes de publicar.

1. **I3.1 — Separar conformance de publicação.** Reutilizar build, manifests e SBOMs do
   job Docker, corrigindo os checks afetados; acrescentar scan de imagem e secrets.
   PR de origem não confiável nunca recebe credencial de push nem ambiente de release.
   Fixar ações/dependências críticas, permissões mínimas, gatilho confiável e aprovação
   do ambiente. Não executar checkout de PR não confiável com secrets via
   `pull_request_target`. PAT mínimo é opção inicial; OIDC/OAT dependem de suporte real.
2. **I3.2 — Fixar candidato.** Checkout limpo no SHA integral; versões/labels coerentes;
   Dockerfiles, locks, bases e snapshot SPA identificados. Revalidar checks afetados
   por metadados novos. Evidência de outro SHA só vale com análise do diff (§10).
   A release que anuncia integração IaC inclui I6/I7 e correções de I4/I8 no SHA final.
   Preparar o pipeline cedo não obriga publicar `0.1.0` antes dessas funcionalidades.
   Se uma imagem intermediária já foi publicada sob autorização própria, mudança de
   código posterior exige novo candidato/versão aprovada e nova homologação I3.
3. **I3.3 — Construir e verificar artefato.** Buildx para `linux/amd64`; executar smokes
   e scans sobre o artefato exato a promover. Bloquear Critical/High sem correção ou
   waiver individual válido da política de postura. SBOM/scan/proveniência por imagem.
   Não testar build A e publicar rebuild B como se fossem os mesmos bytes; se o formato
   de promoção exigir rebuild, repetir os checks de imagem sobre o novo artefato.
4. **I3.4 — Publicar sob autorização.** Após B13, publicar tags versionadas das duas
   imagens; capturar digests reais. Gateway e broker têm digests distintos, mesmo
   quando compartilham versão/SHA. Se só uma publicação concluir, reter diagnóstico e
   não promover bundle de core incompleto; não sobrescrever tag já distribuída.
5. **I3.5 — Verificação independente.** Pull **por digest** com configuração Docker
   limpa e daemon/cache isolado, sem secrets herdados de login. Inspecionar plataforma
   e labels, verificar associação tag→digest e testar CLI, startup, auth e sidecar
   sobre as imagens baixadas. Config limpa com imagem já em cache não basta como prova
   de distribuição. Registrar digest de índice OCI e de manifest de plataforma quando
   houver índice, inclusive os gerados por attestations em build de plataforma única.
6. **I3.6 — Promover metadados.** Somente após verificação, disponibilizar o par core
   compatível ao bundle IaC, com release notes aprovadas, changelog, limitações,
   classificação de migração e referências públicas revisadas. Labels OCI/source e
   attestations também podem divulgar URLs/detalhes privados; revisar antes do push.

**Saída:** duas imagens públicas homologadas, proveniência e pull/smoke anônimo vinculados
aos digests. Imagem publicada que falha no smoke é **não homologada**, não “despublicada”
automaticamente. Correção de artefato exige nova versão aprovada, sem reutilizar tag
SemVer já publicada para apontar a bytes diferentes.

### 5.4 I4 — Bundle de deployment, bootstrap e handoff IaC

**Entrada:** I1/I2 para contrato; I3 para prova pública; C2 antes de escrita no VPS.
**Dono:** IaC implementa automação; Percival fornece contrato e correções do produto.

1. **I4.1 — Layout e inventário.** Aprovar mapa host→container por serviço (§7.2).
   Descobrir socket/GID, data-root real/aliases, submounts, diretório privado, UID/GID,
   token e nome real do container gateway. Gate Server 27.x é compatibilidade do código,
   não afirmação de que toda versão 27.x continua mantida/segura pelo fornecedor.
   Fixar patch homologado e versão mínima do Compose; incompatibilidade de segurança/
   disponibilidade vira decisão de upgrade com testes, não downgrade silencioso do host.
2. **I4.2 — Compose de produção.** Criar bundle separado do desenvolvimento com imagens
   aprovadas por tag+digest, sem `build:`/`:dev`. Mapear gateway, CLI e API habilitada
   ao estado aprovado; manter CLI de setup como tarefa one-shot. Não exigir API sem chave.
   Validar merge/resolução com lista exata de `-f`, diretório-base, env e project name.
   Overlay não deve deixar `build:` ou bind antigo herdado. Não importar overlay bwrap
   ou Engine29 automaticamente; bwrap muda o perfil de privilégio e exige aceite próprio.
3. **I4.3 — Preflight.** Validar contrato/schema do bundle, origem/checksum, plataforma,
   espaço para imagens/backup, portas, permissões de todos os diretórios-pai e versão
   Engine/CLI/Compose. Resolver o gateway pelo projeto/serviço real, não pelo nome
   literal `nanobot-gateway`. Exigir token sob o estado verificado (§7.2) e acesso do
   broker por GID dedicado; nenhum `chmod 777`. Um host incompatível falha antes da mutação.
4. **I4.4 — Instalação idempotente.** Implementar sequência validada: preflight →
   preparar diretórios/owners e credenciais ausentes → adquirir imagens aprovadas →
   setup interativo de config/senha pela CLI correta → subir core → readiness conjunta
   → escrita/leitura de marcador fixture → recreate/persistência → commit do lock.
   Inicialização da config não sobrescreve arquivo existente; reexecutar preserva senha,
   token, CAS, dados, digests e permissões. Instalar Docker/alterar host exige autorização
   específica. Incluir procedimento manual equivalente, sem depender de `curl | sh`.
5. **I4.5 — Transação externa.** Implementar exclusão mútua por instância, identidade da
   operação e estado anterior retido. Validar geração esperada de intenção/lock antes
   do commit. Lock atômico só após aprovação dos probes/persistência (§7.1). Registrar
   fases e falhas fora do lock de sucesso, sem secrets. Reentrada após interrupção
   inspeciona runtime e reconcilia; não presume que lock antigo descreve runtime atual.
6. **I4.6 — IaC e fixture.** Exercitar instalação limpa e segunda execução em host/VM
   descartável; testar falha parcial sem avançar lock. OpenTofu oferece referência para
   host provisionado, não pré-requisito de todo self-host. Executar `fmt -check` e
   `validate` no workspace real, inicializando providers de forma controlada; state,
   planos sensíveis e credenciais ficam privados. `plan/apply` reais exigem autorização.

**Saída:** bundle versionado e contratos interoperáveis, instalação manual/automatizada
e idempotência provadas em fixture. Apenas C2–C4 fecham implantação/aceite no alvo real.

### 5.5 I5 — MCPs oficiais, template e índice curado

**Entrada:** identidades e schemas I1; gates dos MCPs selecionados, não de um MCP arbitrário.
**Marcos incrementais:** I5a (template/primeiro MCP), I5b (índice mínimo), I5c (segundo
oficial + comunitário). São marcos deste item, não IDs de fases dos documentos externos.

1. **I5.1 — Selecionar candidatos.** Comparar MCPs existentes por utilidade, licença,
   maturidade, necessidade de secrets/rede, suporte de transporte e custo de teste.
   I1 selecionou Weather primeiro e OSM segundo; PubMed/Crossref exigem nova seleção,
   implementação e manutenção antes de entrar no escopo de entrega.
   Registrar primeiro/segundo oficial e comunitário, donos e superfícies de tools;
   preparar releases A/B homologadas para os ensaios de update/retorno. Para terceiro,
   escolher versões upstream verificáveis sem republicar sob identidade PBLabs.
   Se Khan entrar, D3/D5 são gates concretos, não cobertos por `tools/list` genérico.
2. **I5.2 — Template extraído de caso real.** Padronizar Dockerfile, locks, testes de
   protocolo/imagem, licença, README e pipeline a partir do primeiro caso funcional.
   Segundo MCP reutiliza esse fluxo; evitar abstração de pipeline sem consumidor.
   `server.json` usa schema oficial verificado/pinado e namespace coerente; não criar
   `server.json` para gateway/broker nem registrar terceiros em nome da PBLabs.
3. **I5.3 — Release MCP.** Por repo, checkout limpo/SHA integral, labels, scan/SBOM,
   protocolo no container, SIGTERM/EOF/init e dados persistentes. Corrigir guards/pins
   D8 aplicáveis (incluindo SHA curto do OSM) e publicar só sob autorização. Repetir
   pull anônimo/smoke por digest após publicação. Reutilizar critérios I3 por imagem,
   sem supor que aprovação B13 do core autoriza release de outro repo.
4. **I5.4 — Fontes e geração do índice.** Implementar schemas e gerador do contrato I1;
   uma fonte revisada para cada informação de release, derivação explícita dos JSONs.
   Validar unicidade de IDs, referências internas/URLs, schema, publisher/licença,
   versão, transporte, plataformas e digest. Rejeitar placeholders e release não
   homologada. Bytes gerados são determinísticos para as mesmas entradas; se houver
   `generated_at`, derivá-lo de entrada estável da revisão, não do relógio de cada run.
5. **I5.5 — Integridade da distribuição.** Vincular catálogo e apps à mesma revisão
   imutável (commit/release e hashes conforme contrato). Testar que alteração de tag
   upstream não altera a release aprovada. Disponibilizar URL JSON real HTTPS ou raw
   em commit pinado; `blob/` não é endpoint JSON. Pages e submissão a MCP Registry/
   Docker MCP Catalog são opcionais e têm autorizações separadas.
6. **I5.6 — Comunitário e repetibilidade.** Curar uma imagem upstream por digest, com
   autoria/licença e revisão de permissões/protocolo. Recursos/secrets de teste precisam
   ser fixtures; se o candidato exigir credenciais reais indisponíveis, registrar
   bloqueio ou submeter outra escolha, sem simular E2E. Completar I5c e registrar os
   três artefatos e respectivas revisões de curadoria.

**Saída:** I5a/I5b desbloqueiam a primeira integração I6; I5 só fecha com dois MCPs
oficiais publicados e um comunitário homologado no upstream, entradas consistentes e
geração/distribuição verificadas. Descoberta não é prova de instalação.

### 5.6 I6 — Adapter de catálogo, aquisição e lifecycle autorizado

**Entrada:** I1, I5a/I5b; base manager/broker existente. Fixtures podem antecipar contratos,
mas a prova de aquisição exige MCPs publicados/índice real. O core dessa prova pode
ser candidato local rastreado, sem esperar sua publicação I3; o aceite público final
repete os smokes afetados sobre o core publicado. Não reimplementar B15.

1. **I6.1 — Interface de domínio.** Mapear busca, inspeção de requisitos, instalação,
   configuração, status, habilitar/desabilitar, checar/solicitar update e remover para
   operações existentes. Definir entrada por app/release aprovados, não URL/comando
   livre. Expor pela interface real escolhida (API/CLI/chat); UI web da loja não é
   requisito P0. Browser dos fluxos WebUI alterados continua B1/B4/B6, com seu harness.
2. **I6.2 — Adapter somente dados.** Validar schemas, tamanho, timeout, URL/origem,
   redirects e vínculo catálogo→app. Rejeitar origem não aprovada, URL local/metadata
   de infraestrutura e campos que escapem do contrato; nenhuma instrução Markdown
   modifica policy. Cache identifica revisão/hash/data de verificação; índice/app de
   snapshots diferentes não pode formar uma release instalável.
3. **I6.3 — Decisão local.** Apresentar publisher, tools/efeitos, digest/plataforma,
   permissões, dados persistentes e secrets por referência; comparar com policy e
   obter consentimento requerido **antes** de adquirir/executar. Persistir decisão
   vinculada à revisão aprovada e à configuração autorizada. Catálogo não transforma
   omissão de mounts em Full; instalação antiga preserva semântica `null`/`[]`/lista.
4. **I6.4 — Aquisição restrita.** Acrescentar operação tipada no executor decidido em
   I1, com verificação de confiança/policy no limite privilegiado; autenticação do
   gateway sozinha não converte qualquer `repo@digest` em artefato homologado. Argumentos
   estruturados, registry/repo/digest/plataforma validados; sem shell, build remoto,
   login de push ou opções Docker livres. Não adicionar socket/CLI ao gateway.
5. **I6.5 — Timeout, cache e concorrência.** Pull pode ultrapassar 30 s do cliente atual:
   decidir operação rastreável/polling ou timeout limitado compatível, idempotência por
   identidade de aquisição e limite de downloads simultâneos. Não manter lock de config
   durante rede longa. Timeout/cancelamento identifica operação em andamento antes de
   retry. Revalidar CAS e consentimento após aquisição e antes de alterar estado;
   conflito pode deixar imagem em cache, mas não instala registro nem remove dados.
6. **I6.6 — Verificação e commit.** Confirmar digest publicado, manifest/plataforma e
   RepoDigest local; usar referência `repo@digest` compatível com o contrato atual,
   mantendo tag humana separada. Spawn segue `--pull=never`. Usar transação/journal
   existentes para instalar/update; só declarar disponível após handshake, `tools/list`
   e projeção real no cliente. Se falhar, reconciliar/compensar com evidência e preservar
   o último bom; falha de compensação permanece pendência observável.
7. **I6.7 — Transporte suportado.** Homologar os MCPs escolhidos sobre o bridge real
   (§1.1/§7.3), com chamadas sequenciais/concorrentes, stderr separado, EOF, timeout,
   restart e ausência de órfãos. Recursos de sessão, paginação, streaming, notifications,
   cancelamento ou HTTP só são anunciados quando implementados/testados. Manifest com
   transporte/requisito não suportado é recusado antes do spawn, ou vira engenharia
   explícita; o broker HTTP não prova suporte a containers MCP HTTP.
8. **I6.8 — Lifecycle completo.** Provar descoberta→install→configure→list/status→tool
   call→disable/enable→update→rollback→remove para os três artefatos de I5c. Reutilizar
   B15 para restart/start/stop/exclude, preservando opt-in persistente, toolsDisabled,
   confirmação tipada e dados. Atualização nunca segue automaticamente tag móvel ou
   concede permissões novas. Corrigir/retirar caminhos `agent-docker`, `@latest` e
   smoke obsoleto após verificar consumidores, sem criar executor alternativo no gateway.

**Saída:** aquisição e experiência first-class autorizadas, casos positivos/negativos
§8 aprovados e compatibilidade B3. Manual de pré-pull não fecha I6. Nova origem/metadata
de config usa migração aprovada; versões antigas não recebem campos desconhecidos.

### 5.7 I7 — Export e reconciliação de capabilities

**Entrada:** contrato I1 e estado atual; export local pode começar antes de I6/I5c.

1. **I7.1 — Origem dos metadados.** Identificar o que existe no config canônico e o que
   falta (app/publisher/version/platform/catalog revision). Persistir metadados novos
   via manager/schema aprovado em I6, não extraí-los de tag ou imagem por adivinhação.
   Separar `app_id` do índice, `server_id` local e instância (§7.3).
2. **I7.2 — Export seguro.** Usar projeção allowlisted; não serializar config inteiro.
   Incluir schema, instalação, revisões global/per-server, origem aprovada, imagem,
   digest/plataforma comprovados, owner e estados intencional/observado com data da
   observação. Sem broker, estado observado é desconhecido, não `running` inventado.
   Não exportar env, secrets, mask hints ou paths privados dispensáveis.
   `DockerMcpService.list()` chama `recover_pending()`; não presumir que copiar essa
   resposta implementa export puro/consistente. Usar snapshot sob o mecanismo de
   serialização apropriado e separar observação/recovery da projeção exportada.
3. **I7.3 — Atomicidade e atraso.** Exportar snapshot consistente da revisão canônica
   com ordenação estável, arquivo temporário no mesmo filesystem e replace durável.
   Não permitir export antigo sobrescrever novo. Se config comitou e export falhou,
   reportar “operação aplicada, export pendente”, preservar a revisão anterior do lock
   e refazer a projeção no recovery. Não reexecutar install/update porque o export falhou.
4. **I7.4 — Reconciliação controlada.** Por padrão, comparar export/config/runtime e
   reportar drift; não importar lock como segundo registry. Restore parte de backup
   privado consistente, policy e configuração autorizada/secrets disponíveis; validar
   revisão, origem, digests, paths e permissões no novo host. Lock sozinho não restaura
   env/mounts/dados nem representa consentimento vigente. Aplicar via manager e CAS.
5. **I7.5 — Legado e externos.** Preservar local-image sem RepoDigest como local/não
   publicado com ID separado; restore em outro host exige artefato local verificável
   ou migração aprovada para digest OCI. `owner: external` é inventário/conexão, nunca
   autorização de start/stop/delete pelo manager. Definir formato para origem desconhecida.

**Saída:** export reprodutível por snapshot, estado de sincronização observável e
reconciliação/restore testados sem secrets nem writer concorrente. Sem atomicidade
distribuída fictícia entre config, containers e lock derivado.

### 5.8 I8 — Falhas, update e recuperação de estado completo

**Entrada incremental:** I2/I4 para core local; I6/I7 para catálogo/MCP; I3/I5 para
distribuição pública; C2/C3 para topologia real. Não aguarda I5c para iniciar backup.

1. **I8.1 — Política de recuperação.** Inventariar estado por caminho/dono (§7.2):
   config/auth, sessões, workspace/memória, KG, auditoria/journal/backups MCP, locks,
   dados externos dos apps e secrets protegidos. Distinguir estado autoritativo de
   caches reconstruíveis; definir frequência, retenção, destino, criptografia, chaves
   de recuperação e espaço com operador. Aprovar RPO (perda máxima tolerável de dados)
   e RTO (tempo-alvo de restauração); não inventar metas numéricas.
2. **I8.2 — Backup consistente.** Definir parada/quiescência dos writers ou mecanismo
   de snapshot consistente, incluindo DB/SQLite e apps externos. Registrar revisões,
   hashes, UID/GID/modes e par core/config/dados compatível. Cópia de arquivos vivos
   sem consistência não prova backup. Raw backups e secrets nunca entram no relatório
   público; manter fora da exposição Full ou comprovar sua proteção em I4.
3. **I8.3 — Core update.** Tooling externo preserva o par gateway/broker e bundle anterior,
   bloqueia updates concorrentes e classifica `runtime-only`/`migration-bearing`.
   Suspender mutações MCP na janela e definir destino de operações em voo. Recriar
   sidecar junto ao gateway quando necessário; probes conjuntos e teste de persistência
   antes do lock. Não recriar MCPs diretamente pelo Compose/WUD.
4. **I8.4 — Retorno.** Para runtime-only, restaurar par compatível e verificar config/
   sessão/MCP. Para migration-bearing, testar restauração da combinação imagem+config+
   auth+dados sem binário antigo sobre estado migrado parcialmente. Se restauração
   falhar, manter operação pendente e ingress controlado; não anunciar rollback OK.
5. **I8.5 — Injeção de falhas.** Exercitar §8 incluindo indisponibilidade/429, disco cheio,
   CAS, crash após startup/antes do lock, export atrasado e falha do segundo serviço.
   Registry/índice indisponíveis não trocam digest nem desinstalam MCPs. Imagem em
   cache só é reutilizada se identidade e policy continuarem verificadas.
6. **I8.6 — Restore medido.** Restaurar em fixture independente (não só voltar o bind
   original); demonstrar login, leitura/escrita autorizada, integridade KG/dados MCP e
   reconciliação. Medir RTO e perda máxima observada contra RPO aprovado; reter último
   bom e par de rollback. Não prometer operação offline de tools que dependem de APIs
   externas só porque a imagem está em cache.
7. **I8.7 — Alvo e runbooks.** Compartilhar prova com C3/C4/D9/autenticação, registrando
   execução por gate. Inspecionar logs/erros/evidências com dados sintéticos marcados
   para detectar vazamento, sem abrir dados científicos reais. Revalidar risco indireto,
   máscaras, proxy e topologia com inventário do alvo; obter novo aceite do operador.

**Saída:** procedimentos ensaiados, métricas contra metas aprovadas e falhas recuperáveis
ou limitações aceitas explicitamente. Prova em fixture não encerra C3/C4.

### 5.9 I9 — Aceite, documentação e handoff

1. **I9.1 — Matriz de evidência.** Consolidar I1–I8, contratos, candidatos/digests,
   testes e decisões no formato §10; apontar pendências D/B/C/autenticação aplicáveis
   sem fechá-las por referência. P0 público exige I5c e lifecycle dos três artefatos.
2. **I9.2 — Walkthrough independente.** Reexecutar instruções publicadas em instalação
   limpa/manual e automatizada, conferir URLs/artefatos reais e passos de recuperação.
   Evidência existente pode ser herdada com justificativa; a documentação tem de
   corresponder à versão instalada, não a comandos propostos.
3. **I9.3 — Aceites separados.** Registrar conformance local/Actions, homologação pública,
   staging/VPS C2–C4, fechamento F7/D12 e aprovação B13 com seus próprios responsáveis,
   datas e escopos. I9 não substitui nem antecede artificialmente gates pós-publicação.
   Bloqueio externo continua aberto; “parcial” não satisfaz aceite final.
4. **I9.4 — Transferência operacional.** Entregar release/runtime/deployment/security
   runbooks, owners, retenção, revisão de contratos/bases/curadoria e procedimento de
   incidente/restore. Operador assina limitações e próxima responsabilidade de manutenção.
   Registrar resultado e arquivar este plano apenas após encerramento ou transferência
   explícita de cada pendência, conforme convenção do projeto.

**Saída:** aceite da parte Percival da IaC. Evidência/assinatura Positronic é externa;
nenhuma conclusão sobre P0 conjunto sem o aceite correspondente daquele produto.

## 6. Sequenciamento e caminho crítico por marco

| Marco | Pode começar quando | Condição de saída / desbloqueio |
| --- | --- | --- |
| **M0 — contrato decidido** | Fontes/baseline disponíveis; diagnóstico I2 em paralelo | I1; donos/repos, policy, schemas e sequência release/aceite decididos |
| **M1 — runtime/candidato local** | Base existente e decisões I1 aplicáveis | I2 e gates locais do candidato; habilita ensaios I4/I8 e CI I3 |
| **M2 — core público** | M1 e implementação I6/I7/I4/I8 incluída na release; C1 aplicável, findings tratados, B13/autorização | I3; duas imagens finais homologadas, desbloqueia instalação pública I4 |
| **M3 — primeiro MCP e índice mínimo** | I1; trabalho de produto/template paralelo ao core | I5a/I5b; primeiro oficial homologado e snapshot do índice desbloqueiam I6 |
| **M4 — manager integrado** | M3, contrato de aquisição/migração aprovado; core candidato local é suficiente | primeira prova I6/I7 com primeiro MCP; I5c e regressão nos três, com revalidação no core final para aceite público |
| **M5 — recuperação e alvo** | I4/I8 locais; C2 antes do alvo, M2 antes de implantação pública | C3/C4 com I8 no alvo; autenticação/D9/D12 conforme escopo |
| **M6 — aceite Percival** | M2–M5, I5c e gates de produto aplicáveis | I9 assinado, evidências e manutenção transferidas |

**Caminhos condicionais:** I1→I2→I3→I4 público→C3/C4→I9 e
I1→I5a/I5b→I6/I7→regressão I5c/I8→I3 final→I9. O maior deles depende de recursos e bloqueios;
não há duração medida para chamá-lo de cronograma fechado. C1 final continua cobrindo os
sete repos previstos; conformance intermediária não aguarda todos os candidatos finais.
M0–M6 são rótulos de entregas, não uma cadeia numérica rígida: preparação do CI I3
começa cedo; sua publicação final pode vir depois de M4 e dos ensaios locais I8.

- I4 **local** e ensaios de core/backup I8 não esperam publicação/host real. Instalação
  pública I4 espera I3; aplicação no alvo espera C2 e autorização. C3 produz parte de
  I8, não espera seu encerramento integral.
- I7 export local pode avançar antes de aquisição; restore de imagem remota depende I6.
  I6 não espera o segundo oficial/comunitário para a primeira prova, mas seu aceite
  completo deve incluí-los após I5c.
- Se I6/I7 ou ensaio I8 mudar código/contrato do core, refixar o SHA, reconstruir as
  imagens e reexecutar I3/checks afetados. Um digest público anterior não prova o
  manager novo; o core local permite desenvolver essa integração sem ciclo I3↔I6.
- Harness Browser WebUI é dependência compartilhada de B1/B4/B6 e fluxos UI alterados;
  não precisa virar dependência da API de busca se a loja P0 não usar browser.
- D1 já foi encerrado para o segredo legado de administração; não é bloqueio atual
  de rotação. R06/R07 do sucessor tratam chaves válidas e formato de persistência,
  com revisão antes de publicação/migração. D2/D6/D7/D8 estão fechados no escopo
  registrado; os checks do candidato alterado continuam obrigatórios em C1/I3/I5.
- A sequência B13↔VPS segue a ADR I1: B13 antes de publicar, homologação pública antes
  de promover, C2–C4/I9 separados. Não transformar ensaio privado em deploy público
  homologado nem fechar I9 antes do pull público.

## 7. Contratos mínimos arbitrados em I1

As tabelas abaixo preservam **informação e invariantes** do plano. Nomes/versões/owners
canônicos foram decididos na ADR/handoff I1; não são schemas já aceitos pelo código.
Versão do schema, da API e da imagem são distintas; implementação cabe a I2–I7.

### 7.1 Estado desejado, commit de deployment e export MCP

| Artefato / writer único | Informação mínima | Invariante e comportamento de falha |
| --- | --- | --- |
| `deployment.yaml` / operador-tooling IaC | schema, instalação/produto, release/par core desejado, plataforma, revisão do bundle/contrato, policy e referências não secretas | intenção não é estado aplicado; resolver apenas release aprovada, sem secrets nem tag flutuante como decisão final |
| `deployment.lock` / tooling externo de deploy | schema/generation, operação, hash/revisão da intenção e bundle, duas imagens com versão/digests/plataforma e compatibilidade, probes/persistência/resultados/data | commit por instância após sucesso conjunto; CAS/exclusão mútua, replace durável no mesmo filesystem e leitura de confirmação; nunca escrever sucesso parcial |
| Registro privado da operação / tooling externo | fases, alvo, lock anterior, candidato, resultado, ação de recuperação e evidência redigida | crash pode deixar runtime novo e lock velho; detectar/reconciliar antes de novo update. Não editar lock à mão para ocultar drift |
| `tools.mcpDocker` / gateway-manager | intenção/configuração/autorização persistida e revisões; metadados novos pelo schema/migração aprovados | fonte canônica continua com single-writer/CAS/journal. Broker não escreve config; ferramenta externa não registra MCP por arquivo paralelo |
| `capabilities.lock` / manager | schema, instância, revisões da fonte, app/server IDs, origem/revisão da curadoria, publisher, versão/imagem/digests/plataforma comprovados, owner e estado observado datado | projeção derivada e atômica; falha não reverte silenciosamente operação comitada. Export atrasado é visível e reparável; não concede consentimento nem substitui backup |

Commit de `deployment.lock` não torna Docker/config/filesystem uma transação única.
Em falha após startup, preservar lock anterior, marcar runtime **não reconciliado** no
registro da operação e validar retorno ou concluir commit após nova verificação. Se
rollback falhar, relatar o que roda realmente; não marcar “último bom restaurado”.

Identidades de imagem: registrar repo+tag humana, digest de índice (se houver), digest
de manifest executável/plataforma e image ID local em campos distintos. Compatibilidade
gateway↔broker é uma relação validada entre duas imagens, não igualdade de seus digests.

### 7.2 Layout, persistência e proteção

| Dado | Baseline / decisão necessária | Prova de aceite |
| --- | --- | --- |
| Estado de instância | Host absoluto aprovado → `/home/nanobot/.nanobot`, bind único do gateway; CLI/API usam a mesma origem. I1 fixa `/srv/pblabs/config/agent/` como referência de host; I4/C2 verificam o alvo antes de migrar | `auth status`, identidade da config e marcador persistem após recreate; nenhuma escrita acidental no `~/.nanobot` do operador |
| Token do broker | Sob a raiz de estado verificada; path interno usado pelo cliente e bind broker coerentes; owner do gateway, grupo dedicado e modo compatível (receita atual 0640) | token legível pelos dois processos e protegido de outros; modo/pais testados; nunca imprimir valor. Caminho separado exige evolução de `MountPolicy` |
| Workspace/KG/sessões/DB | Resolver paths configurados reais, inclusive absolutos fora do diretório padrão; persistir tudo que não é reconstruível | backup/restore consistente, checks de hashes/doctor/leitura pertinentes. Bundle vazio não prova migração de dados reais |
| Locks, intenção, bundle Compose, backups e secrets externos | Layout IaC pode colocá-los **fora** do estado hoje mascarado; protegê-los de MCP Full é requisito novo de I4, pois a política atual não mascara esses paths automaticamente | cobertura/negação comprovada para aliases/submounts/UIDs; estender política ou escolher layout protegido aprovado. Permissão de diretório isolada não prova proteção para todo UID MCP |
| Dados persistentes dos apps MCP | Mapear volumes/binds realmente usados, owners e writer; não presumir que `persistent: true` salva dados externos ou sobrevive a recriação | reinício, update e restore com dados fixture; remoção preserva dados, sem `rm -v` ou prune |
| Runtime gravável/cache | `.venv`, temporários e caches explicitados por modo; channels incluídos na release e política de instalações tardias | startup/recreate sem downloads imprevistos, ou exceção documentada e testada. Não tornar toda raiz `read_only` sem verificar os writers |

O layout de referência não exige migrar hoje para `.percival` nem criar `workspace/`,
`memory/` e `config/` separados que o código não lê. Cada novo bind, symlink ou path
protegido precisa passar no inventário/mount policy no namespace do daemon real.

### 7.3 App, confiança, compatibilidade e limites do executor

- **IDs:** ID curado como `pblabs.<app>` é distinto de `server_id`, que atualmente aceita
  `[a-z][a-z0-9-]{0,39}`. I1 exige `server_id` explícito válido, sem mapping por slug ou
  truncamento; múltiplos registros da mesma app têm IDs distintos na instância. Nomes
  Docker atuais `percival-mcp-<server_id>` colidem entre instalações no mesmo daemon.
- **Confiança:** origem do índice é opt-in local; validação sintática + digest de imagem
  não prova curadoria autorizada. Vincular catálogo, app, versão, digest, plataforma e
  consentimento à revisão aprovada. Definir aquisição por commit/hash ou mecanismo de
  assinatura verificado; não anunciar assinatura não implementada. O executor mantém
  allowlist/policy verificável mesmo diante de pedido forjado do gateway.
- **Requisitos aplicáveis:** contrato atual só oferece mounts `null`/`[]`/lista de paths
  R/W, redes `none`/`bridge`, env tipado e modo persistente. Não oferece bind read-only
  por path, egress por domínio, limites CPU/RAM por app ou configuração genérica de
  comando/transporte. `bridge` não é firewall. Se um manifest exige isolamento/limite
  não implementado, recusar ou ampliar contrato com autorização/teste; não alegar que
  o requisito foi aplicado por estar no YAML.
- **Compatibilidade de config:** `extra="forbid"` impede acrescentar campos para leitores
  antigos. I1 fixa schema 2 para metadados novos, migração explícita e retorno por snapshot;
  metadados não podem virar registry concorrente para contornar o schema. Negociação de
  feature do broker não prova que o leitor antigo entende a configuração nova.
- **Transporte:** bridge existente é ponto de partida, não implementação universal MCP.
  Declarar métodos/versão e semântica de sessão homologados para cada app; seleção de
  MCP HTTP exige integração própria comprovada. Registro `external` não é um MCP nativo
  simplesmente renomeado para contornar requisitos de instalação.
- **Lifecycle/tools:** aumentar permissões ou mudar tools no update exige revisão.
  Preservar semântica atual de tools novas/`toolsDisabled` ou obter aditamento explícito;
  não alterar B19 silenciosamente ao introduzir curadoria. Remover entrada do índice
  não remove app instalado; revogação de confiança exige política local explícita.

## 8. Plano de verificação e matriz de falhas

Cada caso define antes da execução a condição que suporta ou refuta o contrato.
`PASS` exige o resultado observado e evidência; mock/fixture valida seu contrato local,
não fecha sozinho publicação, transporte real, browser ou VPS. `SKIP` não é `PASS`.

| Caso / itens | Exercício mínimo | Resultado exigido / condição de reprovação |
| --- | --- | --- |
| **V01 / I2** | Gateway/API/CLI/broker, UID/GID corretos e incorretos, root-com-drop e falha de drop | processo e writers esperados; erro fail-closed, sem root acidental nem troca de estado |
| **V02 / I2/I4** | CLI de setup com volume limpo, verifier ausente/existente, API sem/com chave | primeira instalação funciona; sem senha default; segundo bootstrap não altera credencial/config; API sem chave recusa bind |
| **V03 / I2/I8** | SIGTERM/EOF, crash/restart, broker atrasado e gateway recriado com novo ID | init único e encerramento limitado; sidecar reatado, estado reconciliado, sem órfãos |
| **V04 / I2/C1** | Cliente atual/host atual, novo/antigo, antigo/novo e schema incompatível | feature ausente não autoriza; recusa/migração explícita sem corromper config; check CI divergente reproduzido/corrigido |
| **V05 / I3/I5** | PR não confiável, release não aprovada, scan bloqueante/waiver expirado | nenhum push/token exposto; promoção bloqueada. Waiver é individual e válido para a imagem |
| **V06 / I3/I5** | Pull anônimo limpo por digest, versão/labels e plataforma; push parcial gateway/broker | bytes/plataforma vinculados à fonte; nenhum bundle promovido se faltar uma imagem ou smoke falhar |
| **V07 / I4** | Compose agregado com diretório-base/env reais; Engine/rootless/GID/path incompatível | sem `build:`, imagem mutável ou bind herdado; preflight reprova antes de alterar o alvo |
| **V08 / I4/I8** | Bootstrap duas vezes, intenção igual, dados e credenciais fixture já presentes | efeito estável; sem reset de senha/token, perda de dados ou atualização de digest silenciosa |
| **V09 / I4/I8** | Falha de pull, startup do segundo serviço ou readiness/persistência | lock não avança; último bom preservado e estado efetivo reportado |
| **V10 / I4/I8** | Crash após `up`/antes do lock; disco cheio/erro de rename/fsync; duas atualizações simultâneas | lock parseável anterior ou novo completo; sem sucesso falso; runtime/lock divergentes reconciliados antes de nova promoção |
| **V11 / I5** | Gerar JSON duas vezes; ID duplicado, versão/digest/transporte incoerentes, placeholder e tag upstream alterada | mesmos bytes para entradas iguais; inválidos recusados; tag alterada não atualiza índice |
| **V12 / I6** | JSON/manifest malformado, tamanho excessivo, origem/redirect não aprovados, snapshots de índice/app misturados | nenhuma aquisição/execução nem concessão de policy; erro limitado sem dados privados |
| **V13 / I6** | Permissão negada, admin remoto desabilitado, mounts ausentes vs `null`/`[]`, requisito read-only/egress não suportado | sem escalada implícita; consentimento/policy efetivos e recusa de requisito não aplicado |
| **V14 / I6** | Digest mismatch/inexistente no registry, arquitetura errada, RepoDigest divergente ou imagem local ausente após aquisição declarada bem-sucedida | aquisição/spawn bloqueados; não resolver por tag nem fabricar digest com image ID. Ausência no cache antes do pull é caso positivo V17 |
| **V15 / I6/I8** | 429/timeout/registry fora, índice fora com/sem cache verificado | retries/backoff limitados e operação rastreável; sem troca de artefato/desinstalação; tools de API externa podem ficar indisponíveis |
| **V16 / I6** | Dois installs/updates simultâneos, CAS alterado durante pull, retry após timeout | sem registro duplicado/permissão obsoleta nem pull infinito; cache residual não é instalação comitada |
| **V17 / I6/I8** | Três apps I5c, primeiro install com cache vazio, handshake/list/call, tools no cliente real e lifecycle completo | aquisição aprovada funciona; resultado pelo protocolo, não proxy de stderr/filesystem; dados preservados após remove/update |
| **V18 / I6** | Bridge com chamadas concorrentes/sequenciais, EOF, stderr, resposta tardia e método/transporte não suportado | correlação/sessão correta, timeout e limpeza; capacidade não homologada é recusada/limitada explicitamente |
| **V19 / I7** | Export de snapshot durante mutação, broker fora, falha de export após commit, tentativa de export antigo | revisão consistente e sem secrets; observação desconhecida/obsoleta explícita, reparação sem repetir mutação |
| **V20 / I7/I8** | Restore de lock sem config/secrets, backup corrompido, drift/CAS e owner externo | validação/consentimento requeridos; sem overwrite cego, concessão nova ou lifecycle de externo |
| **V21 / I4/I8** | Full e mounts reduzidos com aliases/submounts, paths novos de locks/backups/secrets e colisão entre instalações | nenhuma reabertura de superfícies protegidas; topologia incompatível recusada; risco indireto medido e aceito no alvo |
| **V22 / I8** | A→B→A runtime-only e migration-bearing, inclusive falha de restauração | par core/config/auth/dados compatível; recuperação medida; falha não é declarada rollback OK |
| **V23 / I8** | Restore em fixture independente com KG/dados MCP e credenciais sintéticas | integridade e login/leitura/escrita preservados; RPO/RTO medidos contra meta aprovada |
| **V24 / I8/I9** | Logs, erros, manifests, provenance/SBOM e relatórios com marcadores sintéticos sensíveis | sem conteúdo científico/segredos/paths privados indevidos; release notes só anunciam o que a evidência comprova |

**Checks por superfície, no workspace responsável:**

- Documentação: links, estrutura/fences, consistência de IDs/estados e `git diff --check`.
- Código Percival: `pytest`, `basedpyright nanobot`, `ruff check .` conforme escopo e
  CI; testes afetados em `tests/mcp_docker/` e autenticação. Mudanças de WebUI exigem
  lint/test/build do `webui/package.json` e gates browser pertinentes. Não rodar format.
- Container: adaptar `scripts/percival-f5-compose-smoke.sh`, smokes F1/F2 e
  `scripts/write_docker_ci_manifest.py`; hoje podem rebuildar fixtures e assumir paths
  de desenvolvimento. Criar modo de imagem pré-publicada antes de usá-los para provar
  os digests de release. O job que só faz `compose config` do broker não prova sidecar vivo.
- IaC: `bash -n`, ShellCheck se disponível, teste real de idempotência, Compose agregado
  `config --quiet` e smoke; `tofu fmt -check`/`validate` no repo IaC. Ausência de ferramenta
  vira check não executado com causa, não instalação implícita no host nem gate verde.
- Índice/contratos: validação YAML/JSON/schema, fixtures de compatibilidade/negação,
  gerador determinístico e protocolo OCI/MCP real nos artefatos homologados.

Não refazer prova existente sem mudança de candidato, contrato ou preocupação não
resolvida. A evidência final precisa cobrir o **artefato que será implantado**, mesmo
quando os testes de fonte do mesmo SHA sejam reaproveitados.

## 9. Riscos, recursos e critérios de parada

| Risco / dependência | Controle, dono e consequência |
| --- | --- |
| Candidatos publicados sem gates ou mistura de builds | I3/I5 e operador: identidade exata, scan/protocolo e B13/autorização; bloquear promoção sem par core completo |
| Engine suportado pelo código sem versão de host segura/disponível | I2/I4 + mantenedor IaC: verificar patch/suporte; homologar mudança de versão se necessário, sem usar override descartável em produção |
| Token fora do estado ou novos locks/backups acessíveis por MCP Full | I4 + produto: respeitar bind/token atuais e estender proteção comprovada para paths novos; layout que falha é bloqueador |
| Aquisição introduz canal privilegiado arbitrário | I1/I6 + produto: confiança verificável no executor, API tipada e policy/consentimento; nenhuma URL/texto livre vira execução |
| Timeout gera duas operações ou lock finge transação global | I4/I6/I7: idempotência, CAS, registro de operação e reconciliação após crash; não repetir mutação comitada |
| Requisitos de app impossíveis no executor atual | I5/I6: seleção compatível ou engenharia explícita; recusa antes do spawn, sem prometer read-only/egress/resource limits não impostos |
| Gate de release circular com prova pública/VPS | I1.6 decidiu B13 antes de publicação e homologação pública antes de promoção; staging privado adicional exige autorização própria; impedimento não é waiver implícito |
| Perda de estado/credenciais ou dois writers durante migração | I4/I8 + operador: backup consistente, quiescência, par compatível e restore medido; interromper se não houver retorno verificável |
| Um mesmo daemon hospeda instalações que colidem | I1/I2/I6: limite de suporte explícito ou namespace/labels validados; project name Compose sozinho não resolve `_name(server_id)` |
| Falta de org/namespace/workspaces, credencial CI ou host | I1/C1/C2 + operador: confirmar recurso e dono, avançar só em trabalho independente; não inventar URLs, datas ou runs |

**Responsáveis decididos em I1:** bill assume manutenção/revisão de produto, MCPs,
IaC/índice/template nesta fase. **Recursos a confirmar:** disponibilidade efetiva dos
responsáveis, runner/daemon isolado Engine 27.x, browser para gates WebUI,
namespace de publicação, staging/VPS, armazenamento de backups e dados de teste
autorizados. Credenciais de push ficam somente no CI; inventário e restore reais têm
responsáveis próprios. Execução paralela só quando houver responsáveis/recursos sem
conflito; este plano não autoriza delegação automática.

**Impacto e estimativa:** adiciona distribuição, aquisição, contratos, locks e recuperação
ao baseline local; inclui engenharia real em CI, policy, persistência e timeouts. Não é
apenas preencher templates. Não há prazo/orçamento/alocação aprovados. Após I1/M1,
estimar cada pacote com esforço, dependências, responsável e intervalo de incerteza;
reestimar após C2 e primeira prova I6. Mudança de transporte/schema/layout exige análise
do impacto sobre testes, migração, manutenção, custo de operação e risco.

**Parar e registrar bloqueio concreto** se faltar autorização para a próxima operação,
se surgir Critical/High sem correção/waiver válido, se divergir digest/plataforma, se
paths/UIDs/máscaras não forem comprovados, se houver writer concorrente ou se o retorno
não for verificável. Preservar evidência e último bom; não contornar com prune, edição
manual de config/locks/journal, exposição de secrets ou relaxamento do gate de Engine.

## 10. Registro de execução e critério de encerramento

Para cada subtarefa/caso, registrar:

| Campo | Conteúdo exigido |
| --- | --- |
| Identidade | item/caso, data ISO-8601 com fuso, executor/revisor e ambiente local/CI/registry/staging/VPS |
| Fonte | repositório e SHA integral, estado do checkout, versão do contrato/schema, inputs/locks/bases e revisão do bundle/índice |
| Artefato | imagem/tag, image ID e digests OCI distintos, plataforma e par compatível; hash dos relatórios |
| Execução | comando/API real, versões de ferramentas/scanner e timestamp da DB, parâmetros não sensíveis, resultado esperado/observado e exit code |
| Evidência | URL do run com `headSha`, paths privados dos artefatos brutos e resumo redigido versionado; sem backups/secrets nos uploads públicos |
| Conclusão | passou/falhou/não executado; limites, compensação/retorno e decisão do dono/data; bloqueio e próximo responsável quando aberto |

Artefatos brutos ficam fora da fonte rastreada, conforme
[workflow de evidência](../../.agent/workflow.md). Resumos versionados devem permitir
localizar/verificar o resultado sem divulgar material privado. Testes herdados mantêm
SHA/data originais e justificativa do diff não invalidante; não recebem data de execução
nova. Evidências finais precisam existir e ser recuperáveis, não apenas nomeadas no plano.

**Quadro inicial da revisão:** I1–I9 pendentes; nenhuma subtarefa de implementação ou
caso V01–V24 executado por aquela revisão. **Estado atual:** I1 concluído como
arquitetura/handoff; I2 concluído localmente, commitado e enviado em `0e7ff072`;
**I3 adiado por decisão do operador em 2026-10-23**; I4–I9 pendentes e não iniciados.
V01 coberto no escopo
local; V02/V03/V04 têm evidência local e extensões I4/I8/C1/B3 abertas; V05–V24 pendentes.
Registrar avanço e fechar cada I com
seu aceite; I9 exige evidência e assinatura, não percentuais estimados de completude.

**Próxima ação deste plano IaC:** I3 continua adiado, sem implementação iniciada
nesta revisão. Quando reautorizado, começa por I3.1–I3.3 (build/test/scan sem push),
que não exigem credencial de registry. O adiamento não impede C1 ou os ensaios
locais I4/I7/I8 autorizados em seus escopos. Preparação de bill antes de I3.4:

1. **Docker Hub** — namespace `pbeanlabs` com permissão de push e token de escopo
   mínimo guardado como secret no ambiente de release do repositório onde o pipeline
   roda. Credencial é necessária apenas no **push** de I3.4 (imagens core) e I5.3
   (MCPs oficiais); I3.5, I4, I6 e I8 usam pull anônimo, sem login local.
2. **Owner GitHub/fonte pública** — decidir a migração recomendada antes de publicar
   `0.1.0` e revisar a origem pública separada `percival`, conforme ADR I1. Não
   presumir transferência/divulgação do histórico privado `nanobot`: as labels
   `org.opencontainers.image.source`/`documentation` fixadas nos Dockerfiles entram no
   digest da imagem, e o plano proíbe reaproveitar tag SemVer já publicada para
   apontar a bytes diferentes; corrigir a origem depois exigiria nova versão e nova
   homologação I3. A decisão de migrar é do operador e ainda não foi executada.
3. **Workspaces** — `pblabs-iac`, `pblabs-mcp-index`, `mcp-server-template` e o repo
   público `percival`, criados diretamente no owner final, para não amarrar URLs de
   catálogo a `bill-kopp-ai-dev`.

Nomes decididos não comprovam controle, disponibilidade ou publicação.

## 11. Histórico de revisão documental

### 2026-10-23 — harmonização inicial (histórico anterior a esta revisão)

I1–I9 foram criados como trabalho planejado; planos ativos receberam fronteiras/donos/
dependências IaC e correção das migrações automáticas de paths e do catálogo OCI antigo.
`AGENTS.md` do Percival e relatório diagnóstico foram alinhados na campanha registrada
em `a299da09`. Nenhum item de implementação/publicação/CI remota/aceite foi fechado.

O registro anterior relata checks de 10 documentos/181 referências e depois 12
documentos/200 referências, `git diff --check`, estrutura/whitespace e padrões comuns
de credenciais; inclui mudança documental no `.gitignore` e solicitação de commit/push.
São **evidências históricas daquela campanha**, não checks reexecutados nesta edição
nem autorização de nova escrita remota. O status remoto não foi reconferido aqui.

### 2026-10-23 — revisão cuidadosa e detalhamento do plano

Inspeção das diretrizes, planos ativos, decisões, fontes IaC e código/CI em `a299da09`,
com árvore inicialmente limpa. Alteração restrita a este documento:

- baseline verificável com divergência SBOM/scan e asserção de UID no CI;
- subtarefas I1–I9 com entrada, superfície, dono, saída e dependências incrementais;
  sequência B13/VPS explicitamente sujeita a arbitragem, sem ciclo tratado como resolvido;
- requisitos de setup da senha, bind único/token, identidade de instância, limitações
  de bridge/policy e migração de schemas estritos;
- aquisição com timeout/idempotência e autorização no executor, promoção do mesmo
  artefato testado e distinção image ID/manifest/índice OCI;
- transação/reconciliação de locks, backup privado consistente, restore medido e
  matriz V01–V24 com condições de reprovação;
- evidências históricas separadas das verificações desta edição, sem fechar gates.

**Limites desta revisão:** inspeção estática e checks editoriais; sem execução de
aplicação, testes runtime, builds, containers, rede/registry ou host remoto. As condições
V01–V24 continuam planejadas.

**Verificação editorial desta edição:** `git diff --check` passou; verificação local
confirmou 22 links de arquivos com destino existente, 7 âncoras internas válidas,
I1–I9 com 55 subtarefas contíguas, M0–M6 e V01–V24 sem lacunas/duplicações, referências
de seção, tabelas, headings, fences e whitespace consistentes. Só este plano foi
alterado no repositório; nenhuma conclusão de runtime deriva desses checks editoriais.

### 2026-10-23 — execução I1: decisões e handoff

Solicitação do operador para executar I1; contas informadas: GitHub `bill-kopp-ai-dev`
agora, `p-bean-labs` futuramente, Docker Hub `pbeanlabs`, sem acessos configurados nesta
máquina. bill aprovou explicitamente o conjunto arquitetural, responsáveis, nomes de
entregáveis, Weather/OSM e o slug público separado `percival`.

Entregues ADR, handoff com C1–C8/compatibilidade/metadata e snapshot semântico das cinco
fontes com hashes SHA-256. Inventariados oito checkouts e remotes localmente, incluindo
mudanças preexistentes preservadas; workspaces IaC/índice/template ausentes e atribuídos
a bill. I1.1–I1.7 encerrados no escopo arquitetural; o handoff detalha seus resultados.
Governança e `AGENTS.md` referenciam as decisões; o aditamento preserva o histórico
local-only e separa aprovação B13, homologação pública e aceite no alvo.

**Limites:** sem login, rede, push, criação/migração de repos, publicação, builds,
testes runtime, alteração de credenciais/configuração real ou deploy. `0.3.5` continua
metadata do código atual até I2 alinhar o candidato; a ADR não o rebatiza como release.
**Verificação I1:** checks editoriais passaram nos sete documentos envolvidos:
69 links locais e 7 âncoras, tabelas/fences/headings/whitespace; hashes dos cinco
originais e HEADs dos oito checkouts conferidos. C1–C8, I1.1–I1.7, 55 subtarefas,
M0–M6 e V01–V24 íntegros; `git diff --check` passou. O handoff registra os comandos
locais reproduzíveis. Não são provas de implementação/runtime ou de acesso remoto.

### 2026-10-23 — execução I2: runtime 1 e conformance local

Pedido posterior do operador para seguir I2, sobre `eb4e3555` + worktree I2. Metadata
`0.1.0` alinhada sem rename ou upgrades incidentais; runtime 1 documentado; CLI/API
recebem o mesmo bind de estado do gateway no overlay, API vira opt-in. Corrigidas
permissões de leitura/traversal dos artefatos, ownership tmpfs, encaminhamento de
SIGTERM no root init restrito e probe autenticada do broker. O runner isolado
substitui o smoke F5 antigo no CI; o ponto de entrada shell permanece como wrapper.

Ensaio final: Engine 27.5.1 descartável, CLI broker 29.9.0, `linux/amd64`, 19 checks
PASS incluindo baseline broker real e cliente v1 independente; nenhum estado vivo
alterado. Suites focadas: 167 PASS (core/auth/MCP/compatibilidade), 69 PASS
(API/metadata/probe, três casos repetidos); Ruff e typecheck passaram. O relatório
registra os IDs locais realmente executados, artefatos brutos, falhas intermediárias,
correções e limites. I2.1–I2.6 concluídos no escopo local; sem commit/push, release, Actions remoto, ARM64,
Render serviço ou VPS **naquela execução** (commit/push posterior registrado na entrada
seguinte).

### 2026-10-23 — fechamento do ciclo em I2 e adiamento de I3

Decisão do operador: encerrar o ciclo de execução em I2 e **adiar I3**; nenhum work
package de implementação inicia sem nova autorização. bill aprovou o commit e o push do
resultado de I2 em `main` (`0e7ff072`; `origin/main` reconferido por `ls-remote`).
Publicação, credencial de registry, criação ou migração de repositório e deploy seguem
sem autorização.

Duas perguntas do operador foram respondidas a partir do plano e do código, e ficam
registradas como pré-requisitos de I3: (a) o Docker Hub só é usado com credencial no
**push** de I3.4 e I5.3 — I3.5/I4/I6/I8 seguem com pull anônimo, e os workflows atuais
(`ci.yml`, `tui-release.yml`, `kg-platform.yml`) não têm etapa de push; (b) a
transferência para `p-bean-labs` foi **recomendada antes de I3.4**, porque as labels OCI
de origem fixadas nos Dockerfiles entram no digest publicado e a transferência também
muda o regime de secrets/environments do pipeline de release. Nenhuma das duas ações
foi executada.

**Limites:** apenas edição documental nesta rodada; sem build, container, rede, registry,
publicação, deploy, criação de repositório ou alteração de credencial. Os resultados de
I2 seguem valendo com a identidade do commit `0e7ff072`; esta alteração não toca
código, contratos nem artefatos do ensaio, portanto não exige reexecução do runner I2
(`.agent/workflow.md`).
