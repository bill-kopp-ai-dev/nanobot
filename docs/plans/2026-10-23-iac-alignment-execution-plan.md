# Harmonização Percival × IaC aberta PBLabs — plano de integração

- **Preparado em:** 2026-10-23, a pedido do operador, para harmonizar os planos de
  implementação com a proposta IaC. **Estado:** planejamento; I1–I9 não executados.
- **Resultado pretendido:** Percival consumível pela IaC Docker-first, com distribuição
  pública verificável, implantação por digest e MCP Manager integrado ao índice público,
  preservando os contratos e as evidências do runtime existente.
- **Escopo:** contratos e adaptações do Percival; dependências de IaC, MCPs e índice com
  dono lógico e aceite explícitos. Não duplica código dos outros produtos neste repositório.
- **Autoridade:** a revisão dos planos autoriza estas edições documentais, não publicação,
  push, instalação no host, alteração de credenciais reais, cutover ou escrita remota.
  Aprovação de arquitetura não é autorização operacional de deploy/release.

## 1. Referências, precedência e limites da evidência

As cinco fontes fornecidas estão em `/home/bill/Downloads/positronic-bean-IaC/`:

| Referência | Aplicação neste plano |
| --- | --- |
| `AGENTS.md`, §§2–7 e §9 | Delimitação dos repositórios, contratos externos e fases P0-A–P0-H |
| `PBLabs_Open_IaC_DockerHub_Implementation_Guide_v1.0.md`, §§0–6, 12–14 e 17 | Guia principal; imagens, Compose, bootstrap, estado e integração nativa |
| `PBLabs_MCP_Distribution_Services_Strategy_v2.0.md`, §§4–8, 9.1 e 21 | Distribuição aberta, curadoria, OCI upstream e decisões pendentes |
| `iac-docker-first-strategy_v2.0_dockerhub.md`, §§6, 9–10, 26–32 e 37–39 | Ownership, locks e transação de update/recuperação |
| `stack_v0.3_dockerhub.md`, §§39–41 | Capacidades científicas, proveniência e lacunas operacionais |

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

Estas fontes locais precisam ser disponibilizadas/versionadas no workspace IaC antes
da execução por outro ambiente; este plano registra nomes/versões/seções, não presume
que o diretório Downloads seja um repositório público ou uma dependência de runtime.

## 2. Contrato-alvo comum aos planos ativos

1. **GitHub** mantém fonte/IaC/curadoria; **GitHub Actions** verifica e publica;
   **Docker Hub** é o registry principal das imagens oficiais abertas. Organização,
   namespace, nomes públicos das imagens e URL do índice ainda exigem confirmação.
2. Terceiros são consumidos do registry OCI upstream homologado, sem mirror obrigatório.
   Docker MCP Catalog e GitHub Pages são opcionais; Cloudflare Pages não é requisito.
3. OpenTofu provisiona infraestrutura; cloud-init/bootstrap idempotente prepara o host;
   Compose gerencia o **core**, incluindo gateway/API quando aplicável e broker sidecar.
   O **MCP Manager nativo do gateway**, com executor broker, é dono de seus MCPs.
   MCP `externally-managed` tem dono externo explícito; WUD, se adotado, só atua no core.
4. Runtime atual preserva imagens locais por ID/RepoDigest e `run --pull=never`.
   A integração nova precisa de **aquisição explícita e verificada por digest** antes
   do spawn. I1 decide a fronteira dessa operação; manter `--pull=never` no spawn é
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
   Perfil/permissões para instalação por catálogo exigem decisão específica em I1/I6;
   não herdar Full silenciosamente nem alterar os mounts existentes por esta revisão.
10. P0 cobre distribuição aberta. Premium GCP, entitlements, billing, marketplace,
    Kubernetes, registry próprio e entrega privada de clientes exigem escopo separado.

## 3. Work packages, donos e critérios de aceite

IDs **I1–I9** pertencem a este plano. P0-A–P0-H abaixo são as fases do **guia de
implementação/AGENTS de referência**; os outros documentos usam numerações diferentes.
F0–F8, D1–D12, C1–C4 e A1–A9 dos planos existentes conservam seus próprios significados.

| ID / fase | Entrega e dono lógico | Dependências | Critério de aceite / evidência |
| --- | --- | --- | --- |
| **I1 / P0-A** | Contratos e arbitragem — operador decide; agente prepara ADR e matriz de compatibilidade | Fontes e decisões atuais | Confirmar org/namespace e nomes públicos de gateway/broker/MCPs; preservar primeira versão `0.1.0`; alinhar versão/labels/tags ao candidato sem confundir pacote herdado. ADR delimita aditamento das decisões local-only/B20, aquisição por digest, permissões para catálogo, schemas e paths; dono e revisão dos contratos definidos. Estado: **pendente** |
| **I2 / P0-B** | Agent Runtime Contract Percival — repositório do produto | F2–F4/D7; I1 para identidades públicas | Documentar gateway, API e CLI na imagem principal + imagem broker; comandos reais, shutdown/init único, usuário efetivo/UID/GID e path de escrita. Validar Compose não-root, caminho root-com-drop fail-closed/Render ou sua alteração justificada; probes reais por modo e autenticação, sem health fictício na CLI. Matriz gateway↔broker versionada com startup/recreate/falha. `linux/amd64` comprovado; ARM64 só com evidência própria. Estado: **pendente**, com base existente reutilizável |
| **I3 / P0-B** | Distribuição das imagens core — CI dos repositórios de produto | I1/I2; D2/D6/D7/D8 e C1 para candidato final; B13 antes de publicar | PR build/test/scan sem push. Release aprovada via workflow protegido Buildx, permissões mínimas e token de push só no CI; capturar digest OCI e plataforma por imagem, SBOM/scan/proveniência. Pull anônimo com configuração Docker limpa + smoke independente; registro fonte→versão→digest→plataforma. Publicação não dispara deploy. Estado: **pendente** |
| **I4 / P0-C** | Handoff de deployment — contratos Percival aqui; bootstrap/Compose/locks/OpenTofu no workspace IaC separado | I1/I2; I3 para instalação pública; C2 antes de escrita em VPS | Receita de deploy sem `build:`/`:dev`, referências core por tag+digest, broker sidecar/namespace de rede preservados; config agregada validada no diretório-base real. Preflight resolve UID/GID/socket/data-root/token/nome real do gateway, paths protegidos e versões Engine/CLI. Bootstrap idempotente e caminho manual; `deployment.lock` cobre as duas imagens e compatibilidade do core, com exclusão mútua/gravação atômica após validação. Instalação limpa e falha não avançam lock. Layout/backup/retorno ensaiados em fixture; validação estática OpenTofu antes de qualquer plan/apply autorizado. Estado: **pendente** |
| **I5 / P0-D, P0-E, P0-G** | MCPs oficiais, template e índice — mantenedores dos MCPs e workspace do índice | I1 para identidades/schema; F2–F5/D5/D7/D8/C1 para candidatos selecionados | Escolher primeiro e segundo MCP próprios (reutilizar existentes quando adequados; PubMed é candidato, não obrigação). Pipelines replicáveis com protocolo real, `server.json` no schema oficial aplicável, complemento operacional e README coerentes; publicar/homologar dois MCPs no Docker Hub, pull anônimo, digest/plataforma comprovados. Índice curado por PR com Markdown/YAML→JSON determinístico, schema versionado e pelo menos um comunitário upstream sem reatribuição/mirror. URL real ou raw em commit pinado; Pages opcional. Estado: **pendente** |
| **I6 / P0-F** | Adapter de catálogo e aquisição autorizada — Percival gateway/manager + executor broker | I1, I5; operações/contratos existentes da trilha B | Busca/inspeção/instalação configuram somente artefato homologado por digest/plataforma sob policy/consentimento local. Evoluir API tipada do broker se necessário; nenhuma tool Docker genérica, socket/CLI no gateway ou comando de Markdown executado. Aquisição explícita pode preceder spawn `--pull=never`; testar mismatch, imagem ausente, origem não confiável, permissão negada, timeout/429 e concorrência. E2E por transporte real com `initialize`, `tools/list` e tool segura. Manter compatibilidade local-image/pinned-image e versões antigas de cliente/host (B3); não ativar `source.type: repository`/`trustedCatalogs` só porque o schema antigo os reservava. Estado: **pendente** |
| **I7 / P0-F** | Export/reconciliação `capabilities.lock` — MCP Manager no gateway | I1/I6; CAS, backups e journal existentes | `tools.mcpDocker` continua fonte canônica até migração aprovada. Export versionado, atômico e associado à revisão registra publisher/origem/registry/imagem/versão/digest/plataforma/owner/status sem valores de secrets, env ou paths privados desnecessários. Image ID local sem RepoDigest é identificado como local/não publicado, nunca fabricado como OCI. Restore reconcilia só digests aprovados; conflito/export obsoleto/falha é observável. IaC/WUD não escreve esse lock e ele não vira segundo registry editável. Estado: **pendente** |
| **I8 / P0-H** | Resiliência, update e recuperação — produto + IaC, cada qual no seu domínio | I3–I7; D9 para runbook MCP; C3/C4 para aceite no VPS | Exercitar instalação sem catálogo/registry, cache, 429/backoff limitado, ausência de fallback para digest novo; não desinstalar MCP existente em indisponibilidade. Core update externo com falha e retorno de gateway+broker compatíveis, locks não avançados em falha, migração de dados com backup/restore explícitos. Backup do estado completo (config/auth/workspace/KG/MCP/audit/locks/secrets protegidos), não só transições MCP; RPO/RTO definidos e restore medido em fixture. Verificar logs sem conteúdo científico/segredos e risco indireto no alvo; `:ro` no socket não equivale a bloquear mutações na API Docker. Estado: **pendente** |
| **I9 / P0-H** | Aceite de integração IaC — operador assina; agente consolida | I1–I8, gates de produto aplicáveis e C1–C4/D12/autenticação | Matriz requisito→repo/SHA→digest→teste→evidência→decisão, com aceite local, público/registry, staging/VPS e release B13 separados. Nenhuma funcionalidade anunciada como entregue por existir plano/template. Estado: **pendente** |

**Dependências por marco, sem ciclo artificial:** I4 pode desenvolver/ensaiar bootstrap
e recovery em fixture antes de C2; C2 é pré-condição de aplicação no VPS, não de
preparação local. I6 começa com o schema e **primeiro** MCP homologados de I5; o segundo
próprio/comunitário fecha P0-G depois, sem bloquear a prova P0-F. I8 é incremental por
domínio: seus ensaios locais de core/backup precedem C3; a prova no alvo é compartilhada
com C3/C4 e consolida I8/I9 depois. C3 não espera o fechamento integral de I8 para poder
produzir essa própria evidência.

**Subtarefas de compatibilidade a incluir na execução:**

- **I2:** definir Compose como implantação canônica e documentar o status de
  `gateway install-service`/Render (legado, desenvolvimento ou caminho suportado
  separado), sem dois processos gravando o mesmo estado. Não remover interfaces ou
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
| Fases históricas F0–F8 e padrão local de imagem/runtime | [padronização Docker](2026-10-09-docker-standardization-refactor-plan.md) | Base de I2/I3/I5, não prova de distribuição |
| D1–D12: credencial, proveniência, Khan, vulnerabilidade, runtime, pins, runbook e F7/F8 | [fechamento Docker](2026-10-23-fechamento-padronizacao-docker-f4-f5-f7-plan.md) | I3/I5 usam os gates aplicáveis ao candidato; I8 amplia recuperação para core/estado completo |
| A1–A7 KG; B1–B7 MCP/browser; C1 CI e C2–C4 VPS | [plano integrado](2026-10-23-integracao-pendencias-kg-e-mcp-docker-plan.md) | C1 continua verificação remota, não pipeline de push; C3 consome contrato de paths/IaC de I4 |
| A1–A9 de autenticação e ensaio P2–P4 | [senha única](2026-10-11-single-password-acceptance-closure-plan.md) | Reutilizar provas do candidato; persistir verifier/segredos em I4/I8 sem copiá-los para locks |
| Publicação, índice, aquisição, export de lock e aceite IaC | **I1–I9 deste plano** | Lacunas novas têm dono sem reabrir planos arquivados |

O aceite local F7 pode referenciar I1/I2/I4 quando o contrato for alterado; **não precisa
esperar publicar dois MCPs para continuar trabalho local independente**. Inversamente,
F7 assinado não fecha I9. Nenhum gate é encerrado apenas por encaminhamento a outro plano.
O P0 conjunto de Percival e Positronic exige evidências de ambos; I9 comprova a parte
Percival, não certifica o outro produto nem autoriza edições nos seus repositórios.

## 5. Ordem de execução, impacto e verificação

1. Preparar I1, revisar contratos do runtime I2 e continuar os itens locais D/B já
   executáveis. Namespace só bloqueia publicação/identidades finais, não diagnóstico,
   testes de contrato ou preparação local.
2. Após I1/I2, preparar I3/I4 e I5 nos respectivos repositórios. Testes de IaC com
   artefatos locais são fixtures; instalação pública só fecha depois de I3.
3. Com schema/artefatos homologados, implementar I6/I7 sobre o manager existente;
   exercitar I8 e integrar os gates C2–C4/autenticação no alvo identificado.
4. Consolidar I9 sem confundir divulgação, instalação e atualização de produção.

**Impacto:** amplia o planejamento de distribuição antes local para integração aberta;
adiciona CI de release, adapter de catálogo, locks e ensaios de deploy/recovery. Não muda
runtime por esta edição. Dependências novas: identidades/contratos I1, artefatos públicos
I3/I5, workspace IaC/índice e host C2. Mantenedores e operador confirmam alocação; não há
prazo, orçamento ou credenciais aprovados. Reestimar após I1 e inventário C2. Riscos
principais: perda de estado por layout, promoção sem evidência, escalada via broker e
dois donos escrevendo locks/containers; controles estão nos aceites acima.

**Validações por entrega:** Markdown/links e `git diff --check` nesta revisão; em futura
execução, checks canônicos do produto para código afetado, Compose agregado + smoke real,
bootstrap com sintaxe/idempotência em fixture, OpenTofu `fmt -check`/`validate` quando
disponível, schemas/geradores determinísticos e CI protegido. Evidência deve registrar
source SHA, estado do checkout, versão, image ID **e** digest OCI quando existente,
plataforma, scanner/DB, comandos, resultados, limitações e retorno. Não refazer prova
existente sem mudança de candidato, contrato ou preocupação não resolvida.

## 6. Registro desta revisão

**2026-10-23 — harmonização documental:** I1–I9 criados como trabalho planejado; os
planos ativos receberam fronteiras/donos/dependências IaC e correção das migrações
automáticas de paths e da referência a catálogo OCI antigo. Nenhum item de implementação,
publicação, CI remota ou aceite foi fechado. Próxima ação: I1 (contratos/ADR), com I2 e
pendências locais independentes em paralelo quando houver responsáveis disponíveis.

**Verificação editorial desta edição:** `git diff --check` passou; verificação local
dos 10 documentos Markdown alterados/novos confirmou 181 referências locais com
destino existente, fences balanceados, whitespace, IDs I1–I9 e regras de ignore dos
novos arquivos. Corrigido o link histórico do relatório F5 no plano de padronização.
Não foram executados testes de aplicação, builds, containers ou checks remotos:
esta entrega altera planejamento e uma exceção documental no `.gitignore`.

**Revisão final da campanha:** `AGENTS.md` do Percival alinhado aos contratos acima;
relatório diagnóstico revisado para distinguir versão decidida, aquisição/spawn,
evidência histórica e limites da fronteira do broker. Verificação ampliada: 12
documentos Markdown, 200 referências locais, estrutura/whitespace e padrões comuns
de credenciais passaram, assim como `git diff --check`. O commit/push da documentação
foi solicitado pelo operador; não equivale a aceite dos itens I1–I9 ou deploy.
