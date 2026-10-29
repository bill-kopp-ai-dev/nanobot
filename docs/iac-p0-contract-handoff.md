# IaC P0 — handoff de contratos e compatibilidade do Percival

- **Data:** 2026-10-23; baseline local `a299da0951d2d7c20f3879519cecf4032e794ca5`.
- **Estado:** pacote de contratos semânticos 1, decidido para I1 pela
  [ADR](Decisions/2026-10-23-open-iac-contracts.md). Não são schemas/API executáveis.
- **Propriedade e autoridade:** os projetos PBLabs, incluindo Percival e IaC,
  pertencem à Positronic Bean Labs (PBLabs), de Bill Kopp
  (`bill.kopp.dev@gmail.com`). Bill é o único decisor final para aprovações que
  exijam autoridade do owner/empresa. Revisões técnicas e execução podem ser
  delegadas, sem transferir essa aprovação final. O site
  `labs.positronicbean.com` está em desenvolvimento e não é serviço operacional.
- **Dono e revisor atual dos domínios abaixo:** Bill Kopp; o agente prepara as
  mudanças. Não há alegação de revisão independente. Operadores técnicos podem
  executar atividades autorizadas, mas publicação, deploy ou mudança de produção
  não são autorizados por este handoff.
- **Evidência de entrada:** [snapshot/hashes das fontes](references/2026-10-23-iac-source-snapshot.md).
  O plano IaC já tinha revisão local não commitada; foi preservada e complementada.
- **Atualização posterior I2:** [runtime 1 entregue](agent-runtime-contract.md) e
  [conformance local](reports/2026-10-23-i2-runtime-contract-conformance.md). O inventário
  e a tabela de metadata abaixo preservam o baseline **de I1**, não o estado após I2.
  Fonte/lock/fallback/defaults agora usam `0.1.0`; versões futuras/schemas continuam
  com seus gates. O push SSH da documentação I1 foi verificado em `eb4e3555`;
  o commit/push do resultado de I2 foi verificado em `0e7ff072`; permissões de
  publicação/Actions/Docker Hub não foram comprovadas por isso.

## 1. Inventário de checkouts e entregáveis

Todos os paths são relativos a `~/Projects/`. As URLs de origem foram observadas via
`git remote -v`; a leitura dos remotes é local e não confirma acesso às contas.
`p-bean-labs` é destino futuro informado pelo operador, não proprietário atual.

| Entregável | Checkout / GitHub atual | HEAD observado | Estado na entrada / responsabilidade |
| --- | --- | --- | --- |
| Percival core | `nanobot/` / `bill-kopp-ai-dev/nanobot` | `a299da0951d2d7c20f3879519cecf4032e794ca5` | plano IaC modificado pela revisão anterior; produto/contratos/runtime/CI |
| Positronic | `alternative-positronic/` / `bill-kopp-ai-dev/alternative-positronic` | `bd995793dd91ba36b1c3780e4ed6df166de21038` | limpo; dependência de contrato próprio, não editada/certificada por I1 Percival |
| Weather, primeiro oficial | `percival-weather-mcp/` / `bill-kopp-ai-dev/percival-weather-mcp` | `1b1cd6c5781a2f2948d4bddb906a934a0a50f2ea` | limpo; versão fonte `0.9.0`, não prova de release pública |
| OSM, segundo oficial | `percival-osm/` / `bill-kopp-ai-dev/percival-osm` | `d9e34b31b20a550097791b9a4a13a90aa33b3500` | `.positronic/` e `AGENTS.md` não rastreados; versão fonte `0.5.0`; preservar trabalho |
| AgentMail | `percival-agentmail-mcp/` / `bill-kopp-ai-dev/percival-agentmail-mcp` | `36971882b57a2afc64b1cc0a12025a920d1b89f6` | limpo; gate C1 e contrato próprio |
| Khan Calendar | `percival-khan-calendar/` / `bill-kopp-ai-dev/percival-khan-calendar` | `868b6a54f915bacda155e5b438311255a4d1ed1f` | `.positronic/policy.json` e `project.json` não rastreados; preservar |
| Notes | `percival-notes-mcp/` / `bill-kopp-ai-dev/percival-notes-mcp` | `03c730531e4fec972c53738e0dff04e82688bd4a` | limpo; gate C1 e contrato próprio |
| Deep Research | `percival-deep-research/` / `bill-kopp-ai-dev/percival-deep-research` | `c1ab70839050e45c4751cb98b0ee91033bfe3a99` | `.positronic/` e `AGENTS.md` não rastreados; preservar |
| IaC aberta | planejado `positronic-bean-IaC/` / `<owner>/pblabs-iac` | não existe nesse workspace | bill cria/configura workspace antes de I4; Downloads é fonte documental |
| Índice | planejado `pblabs-mcp-index/` / `<owner>/pblabs-mcp-index` | não existe nesse workspace | bill cria/configura antes de I5b; sem URL operacional por enquanto |
| Template | planejado `mcp-server-template/` / `<owner>/mcp-server-template` | não existe nesse workspace | bill cria/configura antes de I5a; reutilizar MCPs existentes |
| Fonte pública Percival | futuro repo `<owner>/percival`; não é o checkout privado atual | não verificado remotamente | revisão/criação/publicação com bill antes de release aberta |

`<owner>` é um namespace GitHub, não uma identidade pessoal nem a entidade dona:
`bill-kopp-ai-dev` antes da migração e `p-bean-labs` após migração explicitamente
executada. A titularidade empresarial por PBLabs e a autoridade final de Bill não
executam a migração nem alteram remotes/labels/trust. Verifique o estado real antes
de qualquer alteração. A listagem de `~/Projects` não prova inexistência remota.
Nenhum checkout externo foi modificado nesta execução.

### Acessos e dependências externas

| Recurso | Estado conhecido | Dono / consumidor bloqueado |
| --- | --- | --- |
| GitHub local | acesso por SSH funcional (push de I1/I2 verificado); sem `gh` nem sessão web nesta máquina | bill configura o que falta; C1/I3/I5 remoto e criação/migração de repos |
| Docker Hub `pbeanlabs` | conta informada; autorização/names/publicidade não verificadas | bill confirma controle e habilita publicação protegida em I3/I5 |
| Credencial de publicação | não provisionada/verificada; nunca necessária para pull público | bill, ambiente protegido do Actions; não colocar push token no runtime/VPS. Push é exigido só em I3.4 e I5.3; I3.5/I4/I6/I8 usam pull anônimo |
| Transferência de owner para `p-bean-labs` | destino informado pelo operador; existência e controle não verificados nesta execução | decisão do operador; recomendada antes de I3.4 porque as labels OCI de origem dos Dockerfiles entram no digest publicado. Ainda não executada |
| Workspaces IaC/índice/template | ausentes nos paths inventariados; nomes e dono decididos | bill; criação local/remota e implementação pertencem I4/I5 |
| VPS/staging | alvo e transporte de artefatos ainda não definidos | bill; C2/C3/C4 e prova no alvo I8/I9 |
| MCP Registry oficial | posse de namespace/schema externo não verificada | bill/I5; verificar `server.json` e nomes reais antes de publicar, sem derivar `io.github.*` do Docker Hub |

Não é preciso configurar login Docker nesta máquina para decidir contratos ou para
futuro pull anônimo; é preciso provisionar a autorização de push no canal de release.
Instalação de ferramentas, criação remota e alteração de credenciais são tarefas
específicas posteriores, não efeitos colaterais de I1.

## 2. Mapa de autoridade e versões

Este documento define a semântica de integração acordada para o Percival. Até a entrega
dos schemas abaixo, não afirmar validação por JSON Schema. Ao criar cada workspace,
o dono transfere/incorpora o contrato e referencia sua revisão; não mantém cópias
concorrentes. Revisão incompatível exige nova versão e aceite dos consumidores.

| Contrato / versão-alvo | Autoridade e arquivo de implementação/documentação | Writer / consumidores | Gate responsável |
| --- | --- | --- | --- |
| Runtime Percival 1 | produto: `docs/agent-runtime-contract.md` | mantenedor; IaC, CI, operadores | I2 cria e comprova modos/probes/UID/processo/compatibilidade |
| Release core 1 | produto: `docs/releasing.md`, fonte `pyproject.toml`; IaC: `docs/release-runbook.md` e referências homologadas | Actions publica; deploy consome artefatos aprovados | I2 alinha metadata; I3 implementa/verifica pipeline |
| Deployment desejado 1 | IaC: `schemas/deployment.schema.json`, `docs/deployment-runbook.md` | operador/tooling IaC; deploy lê | I4 cria schema/bootstrap/fixtures |
| Deployment resolvido 1 | IaC: `schemas/deployment-lock.schema.json` | somente tooling externo de deploy; leitura pelo suporte/manager | I4/I8 provam commit/recovery |
| App/index 1 | índice: `schemas/pblabs-mcp-app.schema.json`, `schemas/catalog.schema.json`, `docs/mcp-app-contract.md` | YAML/Markdown revisados por PR; JSON gerado; manager lê | I5 valida/gera; I6 consome |
| Capabilities export 1 | produto: `docs/mcp-manager-contract.md`, `schemas/capabilities-lock.schema.json` | somente manager; IaC/suporte leem | I7 cria schema/export/restore |
| Config MCP persistida 2 | produto: modelos em `nanobot/mcp_docker/contracts.py` | somente gateway; broker recebe DTOs tipados, não escreve config | I6/I7 migram explicitamente |
| Aquisição broker, feature 1 | produto: `docs/mcp-manager-contract.md`, contratos/client/broker | gateway solicita; broker valida/executa; API nova só após negociação | I6 implementa operação longa, idempotência e compatibilidade |
| Segurança e recuperação | IaC: `docs/security-model.md`, `docs/deployment-runbook.md`; produto: política de postura e runbooks atuais | cada domínio escreve seu procedimento; bill revisa integração | I4/I8/I9, D/C/autenticação aplicáveis |

Os arquivos ainda não existentes nesta tabela são **destinos de entrega**, não links
para artefatos disponíveis. Os runbooks atuais continuam válidos nos seus escopos.
Não criar documentos vazios para aparentar o fechamento dos próximos itens.

## 3. Convenções externas e identidade

Artefatos externos usam `schema_version: 1` (inteiro), chaves `snake_case`, datas
ISO-8601 com fuso, digests `sha256:` seguidos de 64 hex minúsculos e plataforma
`linux/amd64` em P0. `schemaVersion` camelCase da configuração interna é distinto.
Schema desconhecido ou requisito não suportado é erro, não versão implicitamente
compatível. Campos adicionais precisam de regra explícita no schema do produtor.

`distribution_channel: OPEN` é a modalidade de entrega. `stable`/`dev` são qualificações
de release, não substitutos desse campo. `COMMERCIAL`/`CUSTOMER_PRIVATE` têm o mapping
da ADR, mas são rejeitados pelos consumidores P0 até implementação aprovada.

App IDs `pblabs.weather`, `pblabs.osm` e `community.github-official` são chaves da
curadoria; publisher é identidade separada. Para comunitários, preservar upstream,
licença, MCP name e registry, sem mirror/rebranding obrigatório. A entrada comunitária
é alvo de I5c, não servidor já homologado por I1.

Uma app admite registros com `server_id` diferentes na mesma instância; o usuário
escolhe um ID válido `[a-z][a-z0-9-]{0,39}`. Não derivar ID de app removendo pontos ou
truncando strings. O broker atual usa nomes por server ID e P0 limita Percival a uma
instância por daemon; a identidade UUID de uma encarnação Docker não é a da instalação.

## 4. App e índice: contrato semântico 1

Fonte: `catalog.yaml` aponta para `servers/<slug>/{README.md,pblabs.app.yaml}`;
`server.json` oficial é validado no schema MCP externo aplicável em I5 e referenciado
sem falsificar autoria. Índice gera `public/catalog.json` e
`public/apps/<slug>/app.json`. Workflows `.yml`, scripts de validar/gerar/verificar OCI.

| Campo/grupo | Semântica e validação obrigatória |
| --- | --- |
| `schema_version`, `id`, `version` | versão do contrato, ID único de app e versão humana da release; `review.approved_release` deve ser igual a `version` |
| `publisher`, `source_class`, `distribution_channel` | identidade original; `official`/`community`; somente `OPEN` em P0 |
| `source` | repo/revisão de origem quando comprovados, licença, referências de proveniência; nunca deduzir autoria pelo registry. Oficiais exigem vínculo da imagem ao SHA de fonte |
| `distribution.registry`, `.image`, `.tag` | hostname normalizado e referência OCI completa sem tag/digest em `.image`, coerentes entre si; tag é humana, não decisão final de execução |
| `distribution.digest`, `.platform`, `.platform_digest` | raiz OCI homologada, plataforma e manifest executável validado; se raiz já é manifest da plataforma, os dois digests são iguais |
| `runtime` / `compatibility` | transporte real, modo de startup e produtos/faixa mínima comprovados. P0 Percival começa pelo stdio homologado; não habilitar HTTP por texto do manifest |
| `security` / `configuration` | mounts/rede solicitados e nomes de secrets, nunca valores; requisitos obrigatórios separados de recomendações de recursos. Manifest não configura policy |
| `review` | status, `approved_release`, revisor/data e evidências ligadas ao digest/plataforma; `approved` no arquivo só vale dentro do snapshot confiável aprovado |

`app.json` preserva esses valores e inclui o hash dos inputs que o geraram, sem
transformar-se em fonte manual concorrente. `catalog.json` contém entradas/versões e
referências **relativas** para apps na mesma revisão, com hashes verificáveis. Recusar
IDs duplicados, paths que escapam do snapshot, plataformas/digests incoerentes,
placeholders, mistura de commits e URL/redirect fora da origem aprovada.

A geração é determinística para os mesmos inputs/revisão do gerador: ordenação,
encoding e serialização definidos em I5. Datas de revisão vêm dos inputs; não usar
relógio da execução no conteúdo determinístico. CI registra o horário fora desses
bytes. O commit do próprio output não é um campo autorreferente: o pin Git integral
é configurado/validado externamente pelo consumidor.

Não existe URL pública aprovada nesta execução. I5b deve obter um commit real do
repo escolhido e verificar leitura do JSON/raw nesse commit antes de registrar o
endpoint. Mudança de conta ou revisão não altera automaticamente a confiança.

## 5. Estado de deployment e locks: contrato semântico 1

| Artefato | Conteúdo mínimo obrigatório | Regra de escrita/consumo |
| --- | --- | --- |
| `deployment.yaml` | `schema_version`, `installation_id`, produto, `distribution_channel`, plataforma, release/par core desejado, revisão do bundle/contratos, policy e refs não secretas | intenção do operador/tooling IaC; não é resultado observado; referência de secret não é seu valor |
| `deployment.lock` | `schema_version`, `installation_id`, `generation`, `operation_id`, hash da intenção/bundle, versão/SHA, duas imagens com referência/tag/digests/plataforma, revisão da matriz gateway↔broker, probes/persistência e `committed_at` | só deploy externo; exclusão mútua/CAS e replace durável após sucesso conjunto; falha não avança lock |
| Registro privado de operação | operação, fases, alvo, lock anterior/candidato, estado observado, falhas e recuperação redigida | tooling externo reconcilia crash após startup/antes do lock; sem segredos em lock público nem falsa transação Docker+FS |
| `capabilities.lock` | `schema_version`, `installation_id`, `owner: native-mcp-manager`, revisão global/fonte e por servidor, app/server IDs, publisher/origem, revisão/hashes da curadoria, canal, imagem/versão/digests/plataforma comprovados, owner por registro, estado e horário de observação | somente manager exporta snapshot consistente/atômico; export atrasado é detectável; IaC/WUD não escreve nem usa como registry editável |

Em capabilities, o envelope tem `owner: native-mcp-manager`; cada registro declara
`owner` como `native-mcp-manager` ou `externally-managed`. O segundo é observação
de registro externo explícito; nunca autoriza lifecycle pelo manager. São papéis
lógicos do export, não renomeação dos labels Docker históricos `owner: percival`
e `managed-by: percival-broker`.
Image ID local sem RepoDigest aparece como origem local/não publicada, com digest
OCI ausente, não inventado. Registros legados sem app/publisher/versão comprovados
usam ausência/`unknown` conforme schema, não inferem identidade por nome da imagem.

Digests de índice OCI, manifest de plataforma e image ID local são campos distintos.
O digest raiz aprovado é a identidade da referência de aquisição; validar a plataforma
no grafo OCI e conferir RepoDigest local da referência efetivamente adquirida. Não
supor que inspecionar image ID comprova digest do índice.

Export não contém valores de env/secrets, mask hints nem paths privados dispensáveis.
O snapshot associa revisão canônica e observação datada; broker fora significa
observação desconhecida, não sucesso inventado. `list()` atual pode executar recovery:
I7 deve separar observação/projeção e serializar adequadamente o export.

Falha de export após mutação comitada não repete a mutação nem reverte o commit
silenciosamente. Registrar atraso e regenerar a projeção na revisão corrente; impedir
que um export antigo sobrescreva outro novo. Restore exige backup/config/secrets
privados, versão compatível e autorização local; lock sem secrets não restaura sozinho.

## 6. Persistência e matriz de compatibilidade

As novas informações de confiança/proveniência pertencem ao mesmo nó canônico
`tools.mcpDocker` **schemaVersion 2**: referências de índices confiáveis/revisões,
metadados de app por servidor e registro de consentimento/revisão. I6 define modelos
tipados e migra o nó sob CAS; DTO de imagem continua distinguindo ID local/RepoDigest.
Broker mantém sua policy independente aprovada, não escreve configuração do gateway.

Não criar um registry paralelo em sidecar para preservar artificialmente schema 1.
Audit/journal de operações e export derivado não são fontes alternativas de intenção.
Arquivos de confiança do executor são policy provisionada, não inventário concorrente
de instalações. Snapshots privados preservam env, auth e estado necessários ao retorno.

| Escritor/leitor/feature | Regra decidida | Evidência a produzir |
| --- | --- | --- |
| Gateway atual + schema 1 + broker atual | manter operação local-only existente, sem campos novos | regressão I2/I6; I1 não reexecutou runtime |
| Gateway novo lendo schema 1 | leitura preserva schema e dados; só migração explícita, com backup validado/quiescência/CAS, habilita v2 | V04/V20, fixture independente v1 |
| Gateway antigo lendo schema 2 | não suportado; preflight de downgrade detecta antes de iniciar writer; erro atual não deve ser contornado apagando campos | V04; retorno pelo snapshot v1 e par compatível |
| Gateway novo + broker antigo | feature ausente bloqueia aquisição de catálogo; operações locais compatíveis continuam no contrato anterior | V04; negociação e recusa observável |
| Gateway antigo + broker novo | endpoints antigos mantêm semântica; campo ausente não autoriza aquisição e API nova não é presumida | V04; fixture de cliente antigo |
| Cliente UI antigo + host novo | leitura/admin existente compatível na faixa declarada; operação nova exige feature confirmada | B3/V04 com fixture independente; ausência não é consentimento |
| Config v2 → retorno v1 | parar writer, restaurar snapshot privado compatível/config/auth/dados e par core; não restaurar só export | V20/V22/V23; imagem antiga não desfaz migração |
| Artefato externo com schema desconhecido | falhar antes de adquirir/spawn/commit; não reinterpretar campos silenciosamente | V11/V12/V20 |
| Exigência de segurança sem enforcement | rejeitar/explicar incompatibilidade ou implementar/homologar antes | V13/V21; `bridge` não é filtro por domínio |
| Transporte/método MCP não homologado | recusar ou limitar suporte declarado; não chamar TCP/attach de sessão universal | V17/V18; handshake/list/call reais |

Faixas de versões efetivamente compatíveis e tempos de timeout/shutdown dependem
de medição I2/I6; não há números homologados inventados nesta matriz. Server Docker
rootful 27.x permanece gate do código atual; override Engine 29 é descartável-only.

## 7. Inventário de metadata e execução atribuída

I1 escolhe a fonte e inventaria superfícies; I2 aplica o alinhamento atômico antes
de fixar candidato, sem resolver/rebatizar pacote ou atualizar dependências sem motivo.

| Superfície atual | Baseline observado | Mudança/check requerido antes do candidato |
| --- | --- | --- |
| `pyproject.toml [project]` | `nanobot-ai`, `0.3.5` | fonte única passa a `0.1.0`; pacote/import/CLI preservados |
| `uv.lock` pacote raiz | `nanobot-ai`, `0.3.5` | regenerar coerentemente com fonte; revisar diff sem upgrades incidentais; não editar lock gerado à mão |
| `nanobot/__init__.py` | metadata instalada tem precedência; fallback lê pyproject ou usa `0.3.5` | fallback/metadata/wheel coerentes; não confundir dist-info antiga do ambiente com fonte nova |
| Dois Dockerfiles | `ARG VERSION=0.3.5`; OCI source aponta para repo privado atual | defaults/build args/labels coerentes; fonte aponta para SHA/repo efetivo do candidato público quando houver |
| Compose base/overlay broker | `${PERCIVAL_IMAGE_VERSION:-0.3.5}` | defaults de desenvolvimento coerentes; deploy I4 usa referências release por digest, sem build |
| `.github/workflows/ci.yml` | lê versão do pyproject para as duas builds | gate fonte=tag=labels=metadata; scan/push de release são I3, SBOM atual não é scan |
| WebUI/TUI `package.json` | ambos `0.1.0` | preservar identidade de componente; não impor versão de dependência JS como versão de produto; revisar locks/scripts se houver mudança |
| `tui-release.yml`, scripts e docs de release | release de binários separada; exemplo de tag herdado | incluir na revisão de publicação B13/I3; não disparar workflow para testar I1 |

SHA das imagens/proveniência deve ser o da fonte efetivamente construída, não a futura
conta nem um SHA anterior à mudança de metadata. Historicamente `0.3.5` continua válido
nos relatórios que descrevem aquele artefato; não substituir números em massa.

## 8. Handoff, aceite e próximo responsável

| Subtarefa | Resultado I1 | Próximo consumidor / condição |
| --- | --- | --- |
| I1.1 | inventário local/remotes/SHAs, donos/acessos e snapshot documental com hashes registrados | bill cria IaC/índice/template em I4/I5 e leva as fontes originais ou snapshot autorizado; não se presume workspace criado |
| I1.2 | contas/naming core/MCP/público, versão-fonte, tags e inventário de metadata decididos | I2 aplica metadata; I3/I5 verificam controle/names antes de publicar |
| I1.3 | ADR adita local-only/B20 e escolhe broker restrito; spawn sem pull permanece | I6 implementa e prova autorização/idempotência/aquisição |
| I1.4 | C1–C8 arbitrados; C4 premium encaminhado fora de P0; contratos semânticos versionados | I4/I5/I7 entregam schemas executáveis nos owners designados |
| I1.5 | consentimento, concessões iniciais, topologia, single-writer, paths e limite por daemon decididos | I2/I4/I6 comprovam enforcement; instalação atual não foi alterada |
| I1.6 | B13 → publicação → homologação pública → promoção/VPS/I9; staging privado separado quando necessário | nenhum token/publicação/waiver implícito; C2/C3/C4/B13 mantêm donos |
| I1.7 | pacote de handoff e versões/consumidores/revisão/retorno registrados | bill confirmou os papéis nesta fase; reabrir aceite se entrar novo mantenedor ou mudar contrato |

**Aceite registrado:** bill confirmou o conjunto arquitetural e donos/nomes/seleção
por perguntas explícitas nesta sessão e confirmou `percival` como repo público separado.
Isso encerra I1 no escopo **arquitetura e handoff**; os testes V01–V24 continuam
planejados. Apenas checks documentais/estáticos foram executados nesta campanha.

**Próximo passo técnico (atualizado após I2):** I2 foi concluído, commitado e enviado
em `0e7ff072`; o operador adiou **I3** em 2026-10-23 e nenhum work package inicia sem
nova autorização. Antes de I3.4, a preparação de acessos fica a cargo de bill: token de
push do namespace Docker Hub `pbeanlabs` no ambiente de release do repositório que
hospeda o pipeline — pull anônimo não exige login local — e transferência do
reposititório para `p-bean-labs`, recomendada por causa das labels OCI de origem que
entram no digest publicado. Diagnóstico e fixtures locais não dependem de login. Não
há estimativa de prazo/custo baseada só nesta decisão.

### Verificação documental de I1

Passaram: sete documentos com 69 links locais e 7 âncoras válidos, estrutura de
tabelas/fences/headings/whitespace; os cinco hashes originais e oito HEADs do inventário
correspondem à origem; C1–C8 e I1.1–I1.7 completos. O checker do plano confirmou as
55 subtarefas, M0–M6 e V01–V24 sem lacunas/duplicações; `git diff --check` passou.
Foram corrigidos um link preexistente para o manual operacional na governança e a
âncora do plano afetada pela atualização do título de contratos.

Comandos read-only usados (scripts de verificação locais, fora da fonte rastreada):

```bash
python3 /home/bill/.positronic/runtime/tmp/opencode/check_i1_handoff_ses_e96f9440.py
python3 /home/bill/.positronic/runtime/tmp/opencode/check_iac_plan_ses_e96f9440.py docs/plans/2026-10-23-iac-alignment-execution-plan.md
git diff --check
```

Executar no checkout `~/Projects/nanobot`. Os scripts verificam o snapshot desta
execução: mudança futura nos arquivos de origem/HEADs exige analisar e renovar o
inventário, não conservar o resultado como evidência atual. Não foram executados
pytest, typecheck, build, containers, rede, login, push, publicação ou deploy em I1.
