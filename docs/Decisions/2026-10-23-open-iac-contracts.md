# Percival — contratos P0 da IaC aberta e distribuição

- **Data:** 2026-10-23.
- **Status:** decidido para o handoff arquitetural de I1. bill aprovou nesta sessão
  o conjunto de aquisição/policy/topologia/sequenciamento, os responsáveis, os nomes
  de entregáveis e Weather/OSM; confirmou também o slug público `percival`.
- **Responsável/revisor:** bill, operador e responsável pelos contratos nesta fase.
  Preparação técnica: agente. Não houve revisão humana independente.
- **Registro de consentimento:** sessão `ses_e96f9440affe5HbhNZOSFMAKN4`, respostas
  explícitas de aprovação do conjunto, confirmação dos donos/entregáveis e `percival`.
- **Escopo:** I1.1–I1.7 do [plano IaC](../plans/2026-10-23-iac-alignment-execution-plan.md).
  Schemas/API abaixo são decisões de contrato, não funcionalidades já implementadas.
- **Artefatos normativos:** [handoff e compatibilidade](../iac-p0-contract-handoff.md)
  e [snapshot documental das fontes](../references/2026-10-23-iac-source-snapshot.md).

## 1. Contexto e precedência

O Percival já possui manager, broker, configuração com CAS, journal e política de
mounts. A integração acrescentará distribuição pública, índice estático, aquisição
autorizada e exports; não deve substituir essa base por outro executor.

Esta decisão adita o item 2 de [padronização Docker](2026-10-09-docker-standardization.md)
somente para permitir o planejamento/implementação da distribuição escolhida e adita
o futuro catálogo OCI de B20: o alvo P0 é índice JSON estático em GitHub. O runtime
atual continua aceitando apenas `local-image`/`pinned-image`, com spawn sem pull;
`repository` e `trustedCatalogs` não são ativados por esta decisão.

As decisões históricas continuam preservadas. Mantêm precedência a governança B13,
as restrições B23–B25 e a [política de postura de imagens](2026-10-09-docker-image-posture-policy.md).
Para C1–C8 e contratos externos P0, esta ADR/handoff arbitram os exemplos conflitantes
das cinco fontes congeladas. Para o comportamento hoje disponível, prevalecem código
e evidência atual; divergência com o alvo é trabalho pendente, não feature implícita.

## 2. Identidades e migração de contas

Informação do operador: GitHub atual `bill-kopp-ai-dev`, destino futuro da Positronic
Bean Labs `p-bean-labs`, Docker Hub `pbeanlabs`. A máquina ainda não tem acessos
configurados. São identidades confirmadas pelo operador, não prova técnica de posse,
permissão de push, visibilidade ou disponibilidade de nomes.

| Uso | Identidade decidida | Condição |
| --- | --- | --- |
| Desenvolvimento Percival atual | `bill-kopp-ai-dev/nanobot` | remote SSH observado; checkout permanece `~/Projects/nanobot` |
| Fonte pública Percival | `bill-kopp-ai-dev/percival`, futuramente `p-bean-labs/percival` | repositório separado e histórico revisado; criação/publicação ainda não executadas |
| IaC aberta | `pblabs-iac` | novo repositório sob proprietário GitHub vigente; workspace planejado `~/Projects/positronic-bean-IaC` |
| Índice | `pblabs-mcp-index` | repositório separado sob proprietário vigente; workspace planejado `~/Projects/pblabs-mcp-index` |
| Template MCP | `mcp-server-template` | repositório separado sob proprietário vigente; workspace planejado `~/Projects/mcp-server-template` |
| Imagem principal | `docker.io/pbeanlabs/percival-gateway` | gateway, API e CLI compartilham a imagem; preserva naming local existente |
| Imagem broker | `docker.io/pbeanlabs/percival-mcp-broker` | imagem separada; mesmo ciclo de release do core |
| Primeiro MCP oficial | `docker.io/pbeanlabs/percival-weather-mcp` | fonte `percival-weather-mcp`; app `pblabs.weather` |
| Segundo MCP oficial | `docker.io/pbeanlabs/percival-osm` | fonte `percival-osm`; app `pblabs.osm` |

Os nomes são destinos decididos, não endpoints homologados. Os demais MCPs preservam
os slugs atuais; não se declara sua publicação nesta fase. Positronic mantém seu
contrato e implementação próprios; o inventário não certifica seu runtime.

A migração futura troca o proprietário GitHub, não o namespace Docker Hub. Revalidar
permissões, Actions/environments, secrets, URLs, labels de fonte e pins do índice.
Não seguir redirect para mudar confiança automaticamente. Artefatos já distribuídos
mantêm tags/digests/proveniência; não reescrever labels ou tags de release antiga.
Novo proprietário/commit de curadoria exige atualização local explícita da confiança.

Publicar fonte Percival requer a revisão prevista em [governança](../percival-governance.md).
Exportar histórico revisado pode mudar o SHA: fixar o candidato final nesse repositório,
conferir o diff e revalidar checks afetados antes de produzir imagens/proveniência.

## 3. Versão, plataformas e par core

- Primeira versão Percival: **`0.1.0`**, preservando a decisão anterior.
- Fonte única da versão do produto: `[project].version` de `pyproject.toml`.
  CI lê esse valor; build não inventa uma versão a partir da tag ou do pacote upstream.
- Git `vX.Y.Z` corresponde à tag de imagem `X.Y.Z`; igualdade com a fonte é gate.
  Cada release associa duas imagens/digests distintos ao mesmo SHA/versão do core.
- Tag SemVer publicada é imutável por política. Correção recebe versão nova aprovada.
  Tags locais `<semver>-<shortsha>`, `:dev` e `:ci` não são releases de produção.
- Alvo inicial: `linux/amd64`. ARM64 precisa de seu próprio build/smoke e decisão.
- `nanobot-ai`, imports `nanobot`, CLI `nanobot` e nome do checkout são preservados.
  Nome futuro de pacote/PyPI e rebranding amplo continuam fora desta decisão.

I1 fixa fonte e regra, sem produzir candidato de imagem. A alteração atômica dos
metadados herdados `0.3.5`, fallback, locks e defaults está atribuída a I2 antes de
fixar seu candidato; o inventário preciso está no handoff. Não é permitido anunciar
o checkout atual como `0.1.0` por existir esta ADR. I3 bloqueia publicação se metadata,
labels, fonte, tag e versão do pacote construído divergirem.

## 4. Aquisição: extensão tipada do broker

**Escolha:** estender o broker existente para aquisição explícita por digest, separada
do spawn `--pull=never`. O gateway continua responsável por intenção, consentimento,
CAS e configuração; só o broker tem CLI/socket e executa a aquisição autorizada.

| Opção | Autorização/auditoria | Timeout/estado | Operação e decisão |
| --- | --- | --- | --- |
| Extensão restrita do broker | reutiliza boundary tipada e valida policy também no executor | operação rastreável; pull fora do lock de config; consulta após timeout | **escolhida**; preserva um executor e entrega I6 first-class |
| Helper confiável de pré-aquisição | precisaria de canal/policy/auditoria adicionais | precisa igualmente de idempotência e reconciliação | útil para pré-carga manual de desenvolvimento; não fecha I6 |

Contrato de I6:

1. Receber referência OCI exata, plataforma, identidade da operação e prova da
   curadoria/consentimento vinculada à revisão esperada; nunca comando Docker livre.
2. O executor verifica catálogo/app/release/digest/plataforma e seu próprio conjunto
   de confiança permitido. Não aceitar `approved: true` ou digest arbitrário do gateway
   como prova de revisão. Nenhuma URL de manifesto vira shell, mount ou flag Docker.
3. Política verificável do executor vem de snapshot aprovado provisionado pelo operador,
   somente leitura para o processo broker e sem endpoint de ampliação pelo gateway.
   I4/I6 devem comprovar proteção dos arquivos e reload autorizado; não presumir que
   o bearer atual isola um gateway comprometido. B23–B25 e risco indireto permanecem.
4. Pull por digest, verificação OCI/plataforma/RepoDigest local e resposta com identidades
   observadas. Não preencher digest OCI a partir de image ID nem usar tag como fallback.
5. Longa operação identificável/idempotente, prazo e retries limitados, consulta após
   timeout de cliente e auditoria sem secrets. Não segurar CAS/lock de config no pull.
6. Só depois da aquisição e de revalidar CAS/policy, instalar/atualizar via máquina de
   estados existente e confirmar handshake/probe real. Cache residual não é instalação.
7. Rejeitar feature ausente no broker antigo; a compatibilidade local-only permanece.
   Não converter `source.type` em `repository`; imagem adquirida vira `pinned-image`
   com RepoDigest verificado, acompanhada de metadados no novo schema canônico.

## 5. Confiança, consentimento e suporte inicial

- Índice é opt-in do operador: repositório/proprietário, commit integral aprovado e
  hashes dos artefatos. Sem origem configurada, sem aquisição por catálogo.
- P0 usa JSON estático da mesma revisão Git; `main`, Pages e redirects não são pins.
  Pages é opcional. A URL operacional só é registrada depois de existir e ser testada.
- Instalação/update via catálogo exige consentimento local vinculado à app/release,
  digest, plataforma, revisão da curadoria e configuração efetiva. LLM não concede
  privilégios a si mesmo. `allowRemoteAdmin` continua `false` por default e opt-in.
- Instalação nova de catálogo começa sem host binds (`mounts: []`), rede `none` e sem
  env secreto até concessão explícita. Campo ausente no manifest não vira `null`/Full.
  Necessidade de rede/API ou dados exige escolha de configuração antes de ativar.
- Full continua opção **explícita**, com exclusões e risco B23–B25. Registros locais
  existentes mantêm sua configuração; não migrar `mounts: null` para `[]` silenciosamente.
- Executor atual não impõe read-only por path, egress por domínio nem CPU/RAM por app.
  Requisito obrigatório que não possa ser imposto bloqueia a instalação; estimativa
  de recursos só é informativa quando assim declarada. Não prometer isolamento no YAML.
- Mudança de imagem requer nova revisão/consentimento. B19 permanece: `toolsDisabled`
  é preservado por nome; tools novas entram habilitadas **após** o update aprovado,
  com o diff de tools apresentado. Não muda a policy de um servidor sem update.
- Inicialmente **uma instância Percival por daemon Docker**; nomes atuais por
  `server_id` não isolam duas instalações. I4 detecta/reprova conflito antes de mutar;
  Compose project name diferente não remove essa restrição.
- App ID e `server_id` são distintos. I6 recebe um `server_id` explícito que passa no
  regex existente; colisão é erro, sem truncamento nem mapping implícito por slug.
  Vários registros da mesma app numa única instância usam IDs distintos explícitos.

## 6. Topologia, estado e compatibilidade

Compose é o deployment canônico P0 do core. Gateway e broker compartilham namespace
de rede; só o broker recebe socket/CLI. A API continua ativa/configurada conforme a
decisão anterior, com chave obrigatória; CLI de setup usa o mesmo estado. O novo bundle
de I4 deve tratar explicitamente todos esses serviços, não copiar o overlay atual.

Render e `gateway install-service` permanecem caminhos separados de compatibilidade/
desenvolvimento, sem remoção de interfaces nesta fase e sem receber o selo IaC P0.
Nunca executá-los sobre o estado que já possui gateway escritor via Compose. I2
documenta limites e prova o root-com-drop fail-closed/UID efetivo onde aplicável.

O host de referência usa `/srv/pblabs/config/agent/` como raiz monolítica de estado
Percival, montada em `/home/nanobot/.nanobot` no gateway, API e CLI. Não renomear o
path interno nem dividir config/workspace/KG em novos binds por esta decisão.
O token fica **dentro** dessa raiz inventariada; seu nome/UID/GID efetivos são aprovados
no preflight I4/C2. Não migrar a instalação real nem copiar sua config como template.

Intenção/locks ficam em `/srv/pblabs/deployment/`, bundle em `/srv/pblabs/compose/`
e backups privados em `/srv/pblabs/backups/`. Essa separação exige proteção adicional:
I4 deve mascarar/proteger essas superfícies e qualquer confiança/secret externo antes
de permitir MCP Full. O código atual não oferece essa cobertura só por usar tais nomes.
Paths reais, aliases/submounts e workspace externo são aprovados no inventário C2.

O handoff fixa os schemas externos e a matriz de migração. `tools.mcpDocker` continua
canônico, com single-writer/CAS/journal; novos metadados exigem schema **2**, migração
explícita e backup. Schema 1 não recebe campos novos sob `extra="forbid"`. Nenhuma
migração ocorre só por leitura/startup ou por baixar índice. Downgrade de v2 requer
quiescência e restauração do snapshot v1 com o par core compatível, nunca descarte
silencioso de campos ou restauração isolada de um lock público.

## 7. Arbitragem C1–C8

Versões nesta tabela são versões-alvo de contrato, independentes da release `0.1.0`.
Os JSON Schemas executáveis ainda serão entregues por I4/I5/I7 nos seus repositórios.

| Conflito | Escolha canônica | Dono/revisão | Versão/consumidores | Prova atribuída |
| --- | --- | --- | --- | --- |
| C1 — distribuição no app | `pblabs.app.yaml` contém `distribution`; `review.approved_release` deve corresponder à versão; JSON é projeção, não release editada à mão | bill/índice | app/index 1; I5/I6/I7 | V11/V12: divergência YAML/JSON, release/digest e mistura de snapshots são recusadas |
| C2 — comunitário | `community.github-official`, diretório `servers/github-official/`; é ID de curadoria, não publisher upstream | bill/índice | app/index 1 | V11: ID único e autoria original; entrada só em I5c após homologação |
| C3 — capabilities | incluir schema, instância, revisão, owner, origem, plataforma, digests e observação datada; sem secrets | bill/produto | capabilities 1; manager/IaC leitura | V19/V20: consistência, obsolescência, export em falha e restore autorizado |
| C4 — token premium | encaminhado a bill como dono da estratégia; não presumir token por imagem nem implementar premium | bill/estratégia | fora de P0, sem schema premium aprovado | confirmar escopo/permissões do provedor se P1 for aberto; não há teste P0 |
| C5 — layout do índice | `scripts/validate.py`, `generate_catalog.py`, `verify_oci.py`; workflows `.yml`; fontes em `servers/`, saídas em `public/` | bill/índice | index 1 | V11/V12: validação/geração determinística e disponibilidade real em I5 |
| C6 — nomes de documentos | runtime no produto; MCP app/schema no índice; deploy/security/release na IaC, conforme mapa do handoff | bill/cada domínio | pacote de contratos 1 | links e unicidade editorial agora; walkthrough I9 depois |
| C7 — gateway | gateway Percival = runtime/manager; broker = executor/bridge limitada; proxy/rede = mecanismo distinto, sem lifecycle MCP | bill/produto/IaC | runtime 1 + API de aquisição negociada em I6 | V17/V18: protocolo real; não declarar bridge universal |
| C8 — canais | `OPEN` = Public Distribution; `COMMERCIAL` = Premium MCP Service; `CUSTOMER_PRIVATE` = Custom MCP Delivery | bill/contratos | app/locks 1 só aceitam `OPEN` em P0; demais reservados | V11/V12: canais não implementados rejeitados; nenhuma ativação premium por enum |

## 8. Ordem de publicação, homologação e VPS

O ciclo aplica-se **por artefato**, com seus próprios gates. I5 pode publicar/homologar
MCPs e índice antes do core final, sem esperar I6/I7; isso viabiliza a integração
no core local. O candidato core final incorpora I6/I7 antes de sua publicação I3.

1. Para o core, fechar I1; construir/ensaiar candidato local rastreado em I2/I4/I6–I8
   e executar gates locais/Actions aplicáveis ao SHA final. I6 pode usar core local
   e MCPs públicos homologados; uma imagem intermediária não substitui o core final.
2. Preparar fonte pública revisada e pacote B13: SHA/versão, scopes concluídos,
   scans/SBOM/proveniência, limitações e plano de recuperação. bill aprova separadamente
   a divulgação/publicação exata. Esta ADR não concede essa autorização.
3. Publicar sob I3/I5; então testar pull **anônimo limpo**, digest/plataforma e smokes
   públicos. Até isso passar, imagem está **publicada, não homologada** e não entra
   no bundle de deployment. Falha mantém diagnóstico e bloqueia promoção, sem retag.
4. Aplicar C2 e obter autorização específica de implantação; C3 usa bundle homologado
   e ensaio local de recuperação. C4 é novo aceite do operador **no alvo**. Fechar
   I8/I9/F7/autenticação somente com as respectivas provas, não com a publicação.

Assim, I9/C3/C4 públicos não são pré-requisitos integrais de B13/primeira publicação;
os requisitos que só podem ser medidos após publicação são gates de **promoção**.
Isso não dispensa testes locais, Actions, scans, revisão de fonte ou gates de produto
aplicáveis antes de publicar. Se um gate específico exigir VPS previamente, preparar
staging com artefatos privados transportados sob autorização própria e sem build na
VPS, ou registrar bloqueio. Esta ADR não autoriza essa transferência nem dá waiver.

## 9. Aceite de I1 e consequências

I1 conclui decisões e handoff, não implementação. bill assumiu os papéis de responsável
e revisor dos domínios nesta fase e confirmou as escolhas registradas. O detalhamento
técnico foi preparado pelo agente sob a solicitação de executar I1; não se atribui ao
operador execução de testes ou leitura linha a linha dos documentos produzidos.

I2–I9 ficam pendentes. Falta criar os workspaces/repos externos, configurar/verificar
acessos e implementar/validar schemas/runtime/pipelines. Essas dependências têm dono
no handoff e bloqueiam seus consumidores, não a arbitragem arquitetural encerrada.
Mudança incompatível requer revisão de bill, nova versão do contrato afetado, matriz
de consumidores/retorno e revalidação do candidato. Não editar contratos concorrentes
nos Downloads para simular aceite de outro produto ou uma publicação já realizada.
