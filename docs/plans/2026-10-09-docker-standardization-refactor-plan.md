# Plano de refatoração — padronização dos processos Docker do Percival

- **Revisão:** 2026-10-23 / v1.1 — reconciliação com I1/I2 executados da IaC aberta PBLabs.
  F0–F8 e seus relatos permanecem como histórico de execução; o rastreio atual dos
  gates locais está em D1–D12/C1–C4. Integração IaC, distribuição e catálogo passam
  a I1–I9 do [plano de integração IaC](2026-10-23-iac-alignment-execution-plan.md).
  I1 concluiu arquitetura/handoff (`eb4e3555`); I2 entregou runtime 1 e conformance
  local Linux/amd64 (`0e7ff072`), ambos commitados/enviados. I3 foi adiado pelo operador;
  I4–I9 continuam pendentes. Esta revisão incorpora evidência existente, sem novo aceite.
- **Fonte de evidência:** [diagnóstico consolidado Docker](../reports/2026-10-09-docker-consolidated-diagnostic-and-standardization.md).
- **Escopo:** fluxo de build, tags/labels, Compose, entrypoints, transporte, healthchecks,
  CI, gestão local das imagens do Percival e dos seis MCPs (Notes, AgentMail, Weather,
  Khan Calendar, OSM e Deep Research), com contratos de handoff para a IaC aberta.
  Entregas de distribuição/IaC têm dono em I1–I9; F0–F8 não são renumeradas.
- **Estado de partida histórico (2026-10-09):** diagnóstico e builds locais, antes do
  cutover. Houve execução posterior e canário dos seis MCPs nos dois gestores, registrados
  abaixo. Antes de novas edições, reverificar os checkouts e preservar trabalho existente;
  não usar o snapshot inicial como inventário atual.
- **Execução F0:** baseline read-only e decisões do operador registrados em [inventário F0](../reports/2026-10-09-f0-docker-baseline-inventory.md) e [ADR de padronização](../Decisions/2026-10-09-docker-standardization.md). Gate F0 concluído; investigar causa das instâncias duplicadas Positronic antes de cutover/cleanup que as afete.
- **Resultado pretendido:** imagens reproduzíveis e rastreáveis, contratos previsíveis
  stdio/HTTP e um caminho verificável fonte→candidato local→release OCI→deployment
  validado. O aceite local continua distinto da homologação de distribuição e de VPS.
- **Autoridade:** o operador decide convenções de produto, riscos e cutover. Este plano não autoriza commit/push, publicação em registry/Catalog, tag/release, limpeza de imagens fora da lista aprovada ou deploy em VPS.

**Leitura do estado atual:** os relatos de execução F0–F7 abaixo são snapshots datados,
não instruções para repetir trabalho. Para o contrato vigente, usar a
[ADR I1](../Decisions/2026-10-23-open-iac-contracts.md), o
[handoff](../iac-p0-contract-handoff.md), o [runtime 1](../agent-runtime-contract.md)
e o [relatório I2](../reports/2026-10-23-i2-runtime-contract-conformance.md).
As pendências residuais continuam nos trackers D/C/autenticação e I1–I9.

## 1. Objetivo, escopo e limites

### Objetivo operacional

Um operador deve conseguir responder para qualquer container MCP local:

1. qual servidor e versão/revisão estão executando;
2. qual processo/cliente o gerencia e quem o consome (Percival ou Positronic);
3. qual identidade imutável de imagem está fixada e qual alias legível pode ser usado para diagnóstico;
4. se o processo está em stdio ou HTTP e qual evidência sustenta o estado de saúde;
5. quais dados persistem, onde, com qual UID/GID e como fazer rollback;
6. se a imagem foi construída e testada contra o contrato correspondente.

### Incluído

- Imagem principal gateway/WebUI/API/CLI e imagem broker do repositório Percival.
- Os seis repositórios MCP listados acima, sem forçar Dockerfiles ou dependências idênticos quando houver justificativa de domínio.
- Execução local em Docker Compose e spawn stdio por clientes MCP/broker.
- Compatibilidade do pin ID/RepoDigest já usado pelo broker; o identificador de conteúdo continua autoridade para execução.
- Adequação dos contratos do produto para imagem publicada, override Compose por produto,
  persistência e operação pela IaC, conforme I2–I4. Bootstrap/OpenTofu e índice vivem em
  workspaces próprios, não como cópia do código Percival neste repositório.

### Fora desta primeira refatoração

- Executar publicação/deploy/release dentro de F0–F8. Docker Hub já é o alvo da proposta
  para imagens oficiais abertas; I1 decidiu namespace e nomes. Acesso, publicação e
  homologação continuam sujeitos a I3/I5/B13. Docker MCP Catalog é opcional, nunca gate obrigatório.
- Trocar o broker próprio do Percival pelo Docker MCP Gateway externo.
- Alterar contratos de tools/resources/prompts MCP sem migração compatível.
- Mudar implicitamente os controles B14–B25, o acesso amplo ao host, as coberturas ou
  os pins atuais. I1 decidiu aquisição restrita pelo broker e consentimento local;
  I6 ainda implementará/provará aquisição e permissões da loja. Esta revisão não altera o runtime.
- Remover em massa containers/imagens pelo nome, idade, status `unhealthy` ou `docker system prune`.
- Renomear `~/Projects/nanobot`, pacote PyPI ou histórico git. O identificador
  **Docker-facing** deve refletir Percival; nomes públicos foram decididos em I1, sem exigir
  renomeação do código/paths internos para cumprir o contrato externo.

## 2. Decisões e invariantes de projeto

### Invariantes a preservar

- Gateway Percival continua sem Docker socket/CLI; somente o broker separado controla o daemon, de acordo com B16/B23.
- No runtime atual e nos ensaios locais, o broker fixa ID completo ou RepoDigest já
  presente e usa `--pull=never`; tags mutáveis não substituem o pin. Esse é o baseline
  B20, não veto permanente à distribuição OCI. Aquisição explícita por digest tem gate
  próprio em I6, conforme decisão I1; o spawn continua sem pull implícito.
- Servidores MCP stdio reservam stdout para JSON-RPC; Compose e comandos smoke não devem alocar TTY.
- Um container stdio lançado sob demanda não deve ser tratado como serviço HTTP persistente nem receber um healthcheck HTTP.
- Valor efetivo de segurança/persistência deve ser observado; configuração solicitada, imagem/tag ou container `Up` não bastam como prova.
- Dados de notas, calendários, cache, logs/reports e estado do gateway têm mounts explícitos e separados por finalidade, com ownership e backup documentados.
- Não alterar arquivos `.gitignore`, `.positronic`, `uv.lock`, `.venv`, tags ou imagens nos seis repositórios sem examinar o estado local e preservar alterações existentes.

### Decisões F0 aprovadas (baseline local de 2026-10-09)

As decisões de produto estão formalizadas em
[`docs/Decisions/2026-10-09-docker-standardization.md`](../Decisions/2026-10-09-docker-standardization.md):

1. Tags locais imutáveis `<semver>-<shortsha>` e alias `:dev` somente para
   desenvolvimento; repositórios Docker-facing `percival-<service>`,
   `percival-gateway` e `percival-mcp-broker`. Manter IDs/API MCP atuais.
2. F0 aprovou operação local e não autorizou pull/push/release/Catalog. A proposta IaC
   posterior escolhe Docker Hub como alvo público; a transição documental/contratual é
   I1, e execução/publicação continua dependente de I3/B13. Não ler a ADR local como
   proibição arquitetural permanente nem como autorização de publicação.
3. `linux/amd64` apenas nesta refatoração; ARM64 fora do escopo atual.
4. Rastrear `uv.lock` no Percival e usar instalação locked, incluindo estratégia
   reproduzível para dependências de canal (implementar em F3).
5. Incluir `khal` pinado na imagem do Khan para fornecer a superfície completa
   de 12 tools, sujeito às verificações F4 de tamanho/dependências/workspace.
6. **Decisão histórica F0:** API sempre ativa e protegida por `api_key` obrigatória; host bind loopback
    para API e 8765 por padrão; exposição externa exige opt-in e auth/proxy/TLS/
    firewall explícitos. **Atualização I2:** `nanobot-api` passou ao profile opt-in
    `api`, como runtime alternativo ao gateway no mesmo estado, para preservar
    single-writer. A chave API distinta e o bind host seguro continuam obrigatórios;
    o comportamento atual está no runtime 1, não na disponibilidade histórica deste item.
7. Preservar `percival.mcp-docker.server-id` e acrescentar labels owner,
   managed-by e instance-id; cada gestor rotula as próprias instâncias. Detalhar
   nomes/semântica das novas labels em F2.

### Contrato-alvo IaC e handoff das fases

Referências correntes: [plano de integração IaC, §§1–3](2026-10-23-iac-alignment-execution-plan.md)
e ADR/handoff I1. As cinco fontes de 2026-10-19 tiveram seus conflitos P0 arbitrados
em I1; schemas de deployment/índice/exports e a aquisição continuam por implementar.
O relatório comparativo é diagnóstico, não aceite.

| Camada | Dono e limite | Handoff deste plano |
| --- | --- | --- |
| Fonte/build/release | Repositório do produto ou MCP + GitHub Actions; Docker Hub para oficiais, OCI upstream homologado para terceiros | I1 decidiu identidades/versão; I2 alinhou metadata core. F2/F3/F5 fornecem labels/locks/SBOM/testes; I3/I5 ainda acrescentam scan/enforcement, publicação protegida, digest pós-push e pull anônimo |
| Host | OpenTofu + cloud-init/bootstrap idempotente no workspace IaC | Declarar Engine/CLI aprovados, data-root, socket/GID, UID/GID, paths e secrets reais; não instalar o agente nativamente |
| Core | Compose + tooling externo; gateway ou API, CLI de administração e broker sidecar na topologia gateway/MCP | I2 comprovou runtime 1 local: bind comum, single-writer, UID/init/probes e compatibilidade. I4 ainda entrega receita de deployment por digest, sem build na VPS |
| MCPs nativos | Gateway/MCP Manager com executor broker restrito | Fases existentes continuam base; I6/I7 acrescentam catálogo/aquisição/export, sem reimplementar o broker ou segundo dono Compose/WUD |
| Estado | Host persiste; tooling de deploy escreverá `deployment.lock`; manager exportará `capabilities.lock` | Owners decididos, locks ainda não implementados. I4 valida layout e lock core; I7 reaproveita `tools.mcpDocker`/CAS/journal sem segundo registry editável |

**Distinções obrigatórias para as próximas fases:**

- Candidato local usa ID de imagem e tag `<semver>-<shortsha>`; produção usa release
  SemVer + digest OCI verificado. I2 alinhou fonte/lock/fallback/defaults core a
  `0.1.0`; `0.3.5` só descreve o baseline herdado nos relatos históricos. Builds I2
  são worktree candidates, não releases. Não fabricar RepoDigest a partir de image ID.
- `deployment.yaml` é intenção; `deployment.lock` só avança após pull, startup,
  readiness e persistência validados, com escrita atômica/exclusão mútua. Cobrir o
  conjunto gateway/broker compatível, não somente uma imagem genérica `agent`.
- I1 definiu `/srv/pblabs/config/agent/` como raiz monolítica de estado do host de
  referência, montada em `/home/nanobot/.nanobot` no gateway/API/CLI, com token dentro
  dessa raiz inventariada. I4/C2 validam o mapeamento dos paths reais, ownership e
  coberturas antes de migrar o estado atual ou a proposta histórica `.percival`.
  Não copiar paths `/workspace`/`/config` ilustrativos nem mudar estado automaticamente.
- `capabilities.lock` será export do manager em I7, sem secrets; IaC/WUD não escreve nem recria
  seus MCPs. Recipes Compose dos MCPs são fixtures/manuais ou `externally-managed`
  explicitamente, nunca uma segunda receita de produção para o mesmo container.
- Aquisição por digest autorizada e spawn `--pull=never` são etapas distintas. I1
  escolheu extensão tipada do broker; I6 implementa sem execução Docker genérica ao LLM. Catálogo remoto
  não concede privilégios e não ativa automaticamente o tipo reservado `repository`.
- Core update é externo ao agente, não atualização silenciosa pela publicação de tag.
  Classificar migração de dados e ensaiar recuperação do conjunto imagem/config/auth/dados;
  rollback de imagem não desfaz migração. I8 cobre estado completo e falhas.
- Socket só no broker é fronteira existente, não garantia de isolamento total. Medir e
  registrar risco indireto B23–B25; mudança de policy Full exige decisão, não herança
  implícita de manifest. `:ro` em socket não restringe comandos da API Docker.

**Compatibilidade de instruções:** a ADR I1 já aditou local-only/B20: índice JSON
estático em GitHub e aquisição restrita, ainda sem ativar `repository`/`trustedCatalogs`.
Novos installs de catálogo exigirão consentimento explícito e começarão sem binds/rede;
os registros locais existentes preservam sua configuração. P0 limita suporte a **uma
instância Percival por daemon**, não uma por projeto Compose. A política de vulnerabilidades
continua vigente: triagem documental F3 não aprova Critical/High nem waiver automático.

### Evidência incorporada de I1/I2 e limites de reaproveitamento

| Entrega | Estado comprovado | Resíduo / dono |
| --- | --- | --- |
| I1 — identidades, contratos e sequência | ADR/handoff decididos; core `docker.io/pbeanlabs/percival-gateway` e `docker.io/pbeanlabs/percival-mcp-broker`; Weather/OSM selecionados; `pyproject.toml` como fonte de versão | Posse/acessos, fonte pública revisada, schemas e publicação ainda por verificar/implementar em I3–I7 |
| I2 — metadata e modos | Runtime 1, metadata `0.1.0`, mesmo bind em CLI/API/gateway, API opt-in, UID/GID 1000 e alternativo 1001, root-drop fail-closed e init único no core | I4 transforma contratos em deployment/preflight; D7 ainda exige os MCPs e os artefatos finais |
| I2 — probes e recovery local | 19 checks PASS em Engine 27.5.1 rootful/amd64: health autenticado do broker, doctor, initialize/list/call de fixture, recriação conjunta, crash/hydrate e persistência | Fixture não homologa os seis MCPs; I8 mede trabalho em voo/estado completo; C2–C4 comprovam VPS |
| I2 — compatibilidade e CI | Par atual, broker baseline independente e caller v1; WebUI protocolo 1/schema MCP 1 preservados. CI agora chama o runner isolado e arquiva `results.json` | Compatibilidade wire não autoriza probe nova em broker antigo. C1 mantém Actions no SHA final e B3 mantém clientes reais |
| Identidade dos artefatos I2 | Resultado fonte commitado/enviado em `0e7ff072`; relatório conserva baseline `eb4e3555` + diff e image IDs dos builds executados | Commit posterior não converte build worktree em build limpo. D8/I3 exigem candidato rastreado e scan/SBOM próprios; nenhum digest público foi capturado |

O relatório I2 registra 167 e 69 testes PASS em grupos focados (há três casos repetidos),
Ruff e basedpyright sem erros. São verificações herdadas, não novas execuções desta
revisão documental; não fecham F2/F4/F5/F7/F8 nem os itens D/C por si sós.

## 3. Fases, dependências e gates

As fases são sequenciais onde existe dependência de contrato. Em paralelo, cada repositório pode preparar testes/documentação, desde que não modifique o mesmo arquivo sem coordenação. Não há datas, orçamento ou disponibilidade de VPS aprovados; estimar depois de F0.

### F0 — Baseline, decisão de nomes e inventário de consumidores

**Responsável:** agente prepara evidências; operador confirma os donos/decisões.

**Trabalho**

- Capturar, sem revelar segredos: SHA/status/arquivos locais modificados de cada repositório, `pyproject.toml` version, digest/tag/OCI labels de cada imagem, `Config.Image` e labels de cada container, healthcheck efetivo, mounts, ports, init e transporte.
- Mapear os MCP consumers/runtime managers (broker Percival, Positronic/OpenCode, execução Compose manual) por `server_id`/config, sem adivinhar pela imagem ou nome aleatório.
- Salvar um inventário inicial com image ID e RepoDigest separados, tags humanas, versões e revisão; associar os dois containers Deep Research e os dois AgentMail ativos às referências atuais. Não imprimir env secrets.
- Confirmar as decisões §2 (tags/namespaces, arch, lock strategy, port 8765/API, `khal`) e definir labels de container para `owner`, `managed-by`, `server_id` e `instance_id`.
- Levantar referências de configs no Percival/Positronic às imagens antigas; mapear rollback antes de planejar remoção.

**Gate F0 — aprovação do contrato**

- Inventário registra cada container/image ID conhecido, dono/consumidor quando comprovado, e itens sem origem confirmada como pendentes.
- Padrão de tag, labels, transporte/health, arch e lock strategy aprovados.
- Caminho de compatibilidade dos aliases antigos e rollback descrito.
- Nenhuma imagem antiga é removida neste gate.

**Saída:** inventário versionável sem segredos e ADR/decisões para o padrão de imagem local.

**Execução 2026-10-09 — gate concluído:** baseline inicial em
`docs/reports/2026-10-09-f0-docker-baseline-inventory.md`; decisões confirmadas
em `docs/Decisions/2026-10-09-docker-standardization.md`. Instâncias duplicadas
do Positronic AgentMail/Deep Research estão mapeadas ao consumer, mas sua causa
permanece como follow-up obrigatório antes do cutover/cleanup que as afete.
Containers e imagens existentes foram preservados; nenhum cutover ou ajuste de
configuração foi executado.

**Reexecução 2026-10-24 — gate concluído:** inventário corrente em
`docs/reports/2026-10-24-f0-docker-baseline-inventory-r2.md` (reexecução read-only;
o snapshot de 2026-10-09 permanece histórico). Decisões D-1, D-2, D-3, D-5, D-6 e o
item 7 de labels confirmadas pelo operador e formalizadas no adendo de 2026-10-24 da
ADR de padronização. D-4 (rotação das credenciais expostas em claro) foi encerrada
por **aceitação formal do risco residual**, sem prazo e sem dono; revisão prevista
antes de I3/I5 ou de migração de estado/IaC. Fechamento registrado em
`docs/reports/2026-10-24-f0-closure-record.md`. Nenhuma mutação de imagem, container
ou configuração foi executada nesta reexecução; os achados A1/A2/A5/A6/A7/A9/A10/
A12/A13/A14 permanecem abertos nos planos donos.

### F1 — Correções imediatas de runtime: Deep Research e OSM

**Depende de:** F0 (contrato stdio/HTTP/init/TTY aprovado).
**Prioridade:** primeiro risco operacional visível.

**Deep Research**

- Remover healthcheck HTTP incondicional do caminho stdio; stdio deve ser validado pelo handshake MCP (`initialize`, `tools/list`) em smoke/client, não por porta.
- Separar serviço Compose stdio de profile/serviço HTTP. O profile stdio não publica 8000 nem usa healthcheck HTTP ou `restart: unless-stopped` como um serviço standalone.
- Manter health HTTP somente no modo HTTP, apontando ao endpoint correto. Considerar se `/health` é readiness de dependências upstream ou liveness; documentar sem tratar falha de API externa como morte do processo.
- Escolher um único init: manter tini dentro da imagem **ou** usar Compose/Docker `init: true`, nunca os dois no mesmo caminho. Executar stdio com `stdin_open` sem TTY.

**OSM**

- Remover probe `pgrep` do modo stdio ou instalar/pinar explicitamente o pacote necessário e verificar que a probe detecta um processo MCP válido. Preferir não depender de ferramenta de processo não incluída.
- Definir `tty: false` no serviço stdio e um único init. Conforme D-5 do adendo
  2026-10-24, os candidatos atuais usam init fornecido pelo launcher, sem tini embutido.
- Preservar health HTTP específico do profile HTTP e autenticação/regras de exposição existentes.

**Verificação F1**

- Construir as duas imagens em tags de candidato com revision explícita; containers stdio não reportam falso `unhealthy`, expõem handshake/tools/list válidos e não publicam portas.
- Profiles HTTP de Deep Research e OSM iniciam, respondem aos endpoints de saúde efetivamente especificados por cada servidor e respeitam auth/bind; não inferir `/healthz` de outro MCP.
- Confirmar sinal/encerramento e exatamente um PID 1 init.
- Exercitar em fixture isolada; manter os containers/imagens históricos para rollback.

**Gate F1:** relatório de execução com image IDs/digests, config `inspect`, resultado de MCP stdio e HTTP por modo; as duas regressões não podem ser corrigidas apenas desabilitando visibilidade do healthcheck sem provar funcionamento.

**Execução 2026-10-09 — gate concluído em candidatos locais:** Deep Research e
OSM passaram build `linux/amd64`, Compose stdio/HTTP isolado, handshake/tools,
probe HTTP, auth/bind no OSM, init único e encerramento por SIGTERM. O relatório
[`F1 runtime corrections`](../reports/2026-10-09-f1-runtime-corrections.md)
registra IDs, RepoDigests locais, configuração inspecionada, comandos, testes e
limitações. As imagens candidatas foram mantidas para rollback; containers e
consumidores históricos não foram alterados. O cutover permanece em F6.

**Reexecução 2026-10-24 — gate local revalidado:** os candidatos limpos OSM
`ce6de5ccd164` (`04d4399`) e Deep Research `bab6d3ced1b3` (`af3b23b`) passaram
Compose stdio/HTTP em fixtures, `initialize`/`tools/list` (37/5 tools), health
específico por profile, loopback, auth OSM e SIGTERM 143 nos quatro modos. PID 1
é `docker-init` do launcher; as imagens não embutem tini. Relatório e limites:
[`F1/F2 revalidation`](../reports/2026-10-24-f1-f2-runtime-identity-revalidation.md).
Os consumidores ativos permanecem nos pins antigos; A5/A6 não foram encerrados.

### F2 — Contrato de identidade e inventário contínuo

**Depende de:** F0. Pode correr em paralelo a correções F1 em branches/arquivos distintos.

**Trabalho**

- Definir OCI labels comuns: `title`, `description`, `source`, `documentation`, `licenses`, `version`, `revision`, `vendor`; sobrescrever explicitamente labels herdadas de imagens-base.
- Gerar VERSION de `pyproject.toml` e revision do checkout; falhar imagem candidata se `0.0.0`, `unknown` ou `local` for usado como identificador de release.
- I1 escolheu a fonte de versão e I2 alinhou fonte/lock/fallback/defaults core a
  `0.1.0`, sem renomear pacote/import/CLI. Antes da release pública, I3 verifica
  fonte/tag/metadata/labels do candidato exato e a origem após eventual migração de
  owner, preservando o vínculo SHA limpo→versão→image ID/digest→plataforma.
- Usar nomes/aliases Docker com Percival, separando alias de desenvolvimento (`:dev`) de tag imutável (`<version>-<shortsha>`); local build sem registry continua possível.
- Preservar pin broker por image ID/RepoDigest, mantendo tag legível sincronizada para operador; não traduzir tag para digest implicitamente nem puxar imagens.
- Acrescentar container labels que identifiquem origem/owner/gestor e instância nos containers criados pelo broker. Não usar nomes aleatórios como única forma de gestão; não adicionar `container_name` global fixo que impeça duas instâncias.
- Criar comando/script read-only de inventário que mostre tag, ID, RepoDigest, labels, data/arch, owners, container names, healthcheck, ports e referências de Compose/config; redigir variáveis/env/secrets.

**Contrato F2 fixado para implementação:** `percival.mcp-docker.owner` é
`percival`; `percival.mcp-docker.managed-by` é `percival-broker`; o
`percival.mcp-docker.server-id` existente segue compatível; e
`percival.mcp-docker.instance-id` é UUID v4 novo para cada encarnação de
container (um recreate gera novo ID). A captura de inventário seleciona campos
de Docker sem consultar `Config.Env`, filtra labels relevantes e redige mounts
de `.env`/secrets. O build canônico é `python scripts/percival-docker-build.py`
no checkout Percival: extrai a versão de `pyproject.toml`, revisão do Git, exige
versão SemVer não-placeholder e constrói localmente `linux/amd64` com tag
`percival-<service>:<version>-<shortsha>`; `--dev-alias` atualiza `:dev` só a
pedido. `--worktree-candidate` cria tag com sufixo explícito e hash do diff para
validação local, sem representar release nem atualizar `:dev`.

**Gate F2:** os seis builds canônicos apresentam labels coincidentes com versão/revisão da fonte; configuração broker continua pinada por identidade; inventário distingue instâncias mesmo quando compartilham image ID. Nenhuma tag externa é publicada.

**Execução local 2026-10-09 — implementação validada, gate aberto:** contrato OCI
dos seis MCPs, build local source-derived, labels broker-managed e inventário
read-only foram implementados e enviados a `origin/main`. Os candidatos F2
`linux/amd64` identificam o diff tracked local em tag e label explícitos. O relatório
[`F2 identity/inventory`](../reports/2026-10-09-f2-docker-identity-inventory.md)
registra IDs, hashes, verificações e limites. Os sete repositórios F2 foram
revisados, commitados e enviados a `origin/main`; ainda faltam builds canônicos
dos seis MCPs em checkouts limpos após esses commits, por isso F2 não está
marcada concluída. F3 iniciou após os commits F2 estarem integrados; os
candidatos F3 usam SHA HEAD + diff explícito. Não houve pull remoto de imagens,
mutação dos consumers, cutover ou cleanup.

**Reexecução 2026-10-24 — gate local concluído:** os seis builds canônicos limpos
já produzidos em D8 (§7.1 e §7.3/C3) foram reinspecionados contra os mesmos HEADs
limpos: Notes `c104735`, AgentMail `cd55a2f`, Weather `437a41c`, Khan `e8c5d8c`,
OSM `04d4399` e Deep Research `af3b23b`. Versão, SHA completo, oito labels OCI e
`linux/amd64` coincidem; nenhuma tag foi sobrescrita ou rebuild repetido. O
inventário foi complementado para o esquema duplo D-6, proveniência de worktree,
overrides Compose e Markdown; verificou 12 MCPs com 12 UUIDs v4 e seis pins nos
dois gestores, sem alteração de configuração. Relatório e evidências:
[`F1/F2 revalidation`](../reports/2026-10-24-f1-f2-runtime-identity-revalidation.md).
A melhoria de inventário está validada no worktree, ainda sem commit/push.
Lint/typecheck focados passaram; checks globais têm falhas externas ao diff
registradas no relatório. CI remoto, distribuição e cutover permanecem gates próprios.

### F3 — Reprodutibilidade, contextos e postura base

**Depende de:** decisões de lock/base em F0 e labels/tag spec F2.

**Trabalho**

- Pin de digest para todas as bases em cada arch aprovada, incluindo stages Node, uv, Python e base Alpine; pin de toolchain uv e inputs de sistema relevantes. Planejar update cadence trimestral e atualização urgente por CVE.
- Python: usar lock validado e `uv sync --locked`/`--frozen`, ou mecanismo de imagem com hashes aprovado em F0. Corrigir Weather e OSM, que exportam requirements `--no-hashes`; pin/hash dos channel manifests do gateway. Nunca deixar atualização de patch sem fluxo de manutenção.
- **Limite confirmado em I2:** a imagem core inclui WhatsApp (`neonize`/`segno`) e
  aceita channels adicionais por `NANOBOT_CHANNELS` no build. UID 1000 ainda pode
  instalar dependências ausentes em `/app/.venv` no startup; um digest da imagem
  não congela essas instalações posteriores. Fixar/incluir todos os channels
  habilitados no candidato imutável. UID alternativo/offline depende de pacotes
  pré-instalados, sem fallback de permissões ou rede implícita.
- Auditar tamanhos/contexto antes e depois. Excluir `.venv`, `.positronic`, `.env*`/secrets, caches, build/test artifacts e o que não é copiado por Dockerfile. Definir orçamento de contexto após baseline clean checkout (a referência local do gateway foi 346,73 MB, afetada por state local).
- Confirmar `.dockerignore` não exclui por engano arquivos necessários (`README`, `LICENSE`, `docs` embarcados ou manifest) e testar contexto em clean checkout.
- Gerar SBOM e scan de vulnerabilidade para imagem de candidato; definir antes da CI a política de severidade/waiver e owner de atualização. Scanner informa risco, não substitui pins nem revisão.
- Guardar manifest de build com source SHA, platform, base digests, dependency lock hash, image ID/RepoDigest, args não secretos e testes.
- O gate de distribuição I3/I5 requer scan/SBOM do candidato exato e digest real
  publicado, com scanner/DB registrados. Findings/waivers antigos não se transferem
  automaticamente entre builds; manter a política de postura e o dono da remediação.

**Gate F3:** mesmo source+lock+base digests gera o mesmo conjunto resolvido (ou diferenças explicadas por platform); build clean funciona em builder CI; contexto não contém estado local/secret; SBOM/scan registrados e exceções têm owner/expiração. Se exact image digest reproducibility não for alcançável, declarar qual nível de repeatability foi comprovado.

**Execução F3 local 2026-10-09 — implementação validada, gate aberto:** o
`uv.lock` existente do Percival foi liberado da regra de ignore e validado
(`145` packages); o gateway usa `uv sync --locked`. Weather migrou de export
`--no-hashes` para `uv sync --frozen`; OSM também instala diretamente pelo
`uv.lock`. Os 13 manifests de dependências de canais agora têm requirements
compilados com hashes para Python 3.12/linux/amd64;
`scripts.compile_channel_locks --check` compara conteúdo e hashes com os manifests Python, e o instalador do
gateway usa `pip --require-hashes` com validação do manifest. O lock do bootstrap
uv do Notes também é hashado.

Todas as instruções `FROM` nos oito Dockerfiles (gateway, broker e seis MCPs)
estão pinadas a digest linux/amd64. As imagens Debian usam o snapshot imutável
`20261009T000000Z`, upgrades explícitos e versões diretas de pacotes fixadas; o
broker Alpine fixa Python/pip e instala Pydantic de lock com hashes. Os
`.dockerignore` foram ampliados e inspecionados; os contextos BuildKit finais
mediram 193 B (Notes), 2.65 kB (AgentMail), 4.63 kB (Weather), 3.94 kB (Khan),
968 B (OSM), 6.85 kB (Deep Research), 28.78 MB (gateway) e 432 B (broker).
São contextos dos worktrees-candidatos locais, não checkouts limpos de CI.

Os oito candidatos foram construídos, inspecionados e receberam SBOM CycloneDX
via Docker Scout; smoke stdio/HTTP F1 de OSM e Deep Research passou. Trivy
0.67.2 (imagem fixada por digest; DB atualizado em 2026-10-09T13:10Z) registrou
Critical/High em todos os oito. A política em
[`docker-image-posture-policy`](../Decisions/2026-10-09-docker-image-posture-policy.md)
define esses níveis como bloqueadores; não foram concedidos waivers. F3 não
fecha até triagem/resolução ou aprovação explícita de exceções com owner e
expiração, além de rebuild/validação em builder/checkout limpo e evidência
reprodutível do conjunto resolvido. O relatório
  [`F3 reproducibility/context/posture`](../reports/2026-10-09-f3-reproducibility-contexts-posture.md)
  registra candidatos, contextos, hashes dos artefatos e findings.

**Execução F3 2026-10-25 — gate concluído no escopo local:** o build do gateway
passou a instalar a **união dos channel-locks** com `--require-hashes --no-deps`
(o caminho anterior resolvia por manifest e podia aceitar faixa já satisfeita) e
`uv pip check`; candidatos Docker definem
`NANOBOT_RUNTIME_PACKAGE_INSTALL=0`, então o startup reporta dependência ausente
sem instalar e a WebUI recusa (409) antes de alterar configuração — a instalação
nativa segue intacta fora da imagem. Os `.dockerignore` do core e dos cinco MCPs
alterados viraram allowlist explícita, e o novo
`scripts/check_docker_context.py` exporta o contexto efetivo com BuildKit e
mede canários sintéticos de estado/segredo: **19 canários por repositório, zero
vazados**, com o core caindo de 23.956.554 para 22.003.812 B.

Foram construídos **candidatos limpos a partir de checkouts commitados** (core
`f2173bbe`, AgentMail `89acdf4`, Weather `9583059`, Khan `4f4521a`, OSM
`4204213`, Deep `dd6451e`; Notes reaproveita o candidato limpo da D8
`c104735`). Rebuilds `--no-cache` dos mesmos fontes produziram **conjuntos
resolvidos idênticos** (pacotes Python e de sistema) nos sete serviços
repetidos — repetibilidade do conjunto resolvido, não igualdade bit a bit.
Trivy 0.67.2 (DB de 2026-10-25) reportou **0 Critical/High nos oito candidatos**
(SBOM CycloneDX por image ID); o único Medium (`CVE-2026-49138` do gateway) teve
avaliação `not_affected` reancorada no image ID novo, sem waiver. Runtime:
rehearsal I2 **18/18 PASS** no par novo, conformidade stdio dos MCPs e gateway
offline em UID 1000/1001 com 20 pins de canal conferidos. Relatório:
[`F3 2026-10-25`](../reports/2026-10-25-f3-reproducibility-contexts-posture.md).
**Fora do escopo:** build clean em builder de CI (B5/C1) e digest publicado
(B6/I3) continuam não executados; nenhum pin, container ou registry foi alterado.

**Remediação local 2026-10-09/10 — gate continua aberto:** versões Python com
correção disponível foram atualizadas, as bases Linux dos candidatos MCP/
gateway foram alinhadas a Debian Trixie e as oito imagens foram rebuildadas e
rescanneadas. Os candidatos passaram os smokes stdio; Notes e Khan também
passaram persistência local isolada. A política continua sem waivers e o scan
Trivy 0.67.2 ainda registra Critical/High nas oito imagens (ver
[`F3 remediation and F6 preflight`](../reports/2026-10-09-f3-remediation-and-f6-preflight.md));
portanto F3 não foi aprovada. HTTP/restore restantes de F4 e execuções remotas
F5 também não foram concluídos. F6 não foi iniciada e nenhum consumer foi
alterado.

**Execução adicional 2026-10-10 UTC — remediação local, gate F3 fechado; resíduo transferido para pendência #11:**
os oito serviços foram reconstruídos como worktree candidates identificados por
SHA/diff hash; os oito receberam novos scans Trivy e SBOM CycloneDX. O broker,
reduzido a Docker CLI 29.9.0 copiado para Python 3.12 Alpine, mantém 0 Critical/
High e passou unit tests e conexão a Engine 27.5.1 descartável. Nos seis MCPs e
gateway, hardening removeu `nsenter`/`infocmp` e setuid de `mount`; OSM e Deep
Research deixaram de instalar `curl`/`libcurl`. Deep também recebeu upgrades de
lock, remoção do setuptools global não usado e exclusão de NLTK transitivo; a
imagem passou smoke stdio/HTTP, teste sem NLTK e 414 testes/3 skipped. OpenSSH
10.5p1 de Debian Forky passou conexão client/server local, mas ainda não foi
integrado num build Forky do gateway. Scans atuais: **1 Critical e 328 High**;
Deep Research deixou de reportar CVE-2026-81726, mas findings de pacote-base
permanecem nos sete runtimes Debian. Um OpenVEX com seis avaliações restritas
ao image ID do gateway cobre CVEs de `sshd` ausente e discrepâncias de msgpack,
setuptools e urllib3; não cobre os demais findings nem outros digests. Nenhum
waiver foi aprovado. O Trivy ainda apresenta discrepância de inventário Python/
aviso de SBOM de terceiro no gateway. Relatório,
hashes de scan/SBOM, decisões e testes: [`F3 remediation and triage`](../reports/2026-10-10-f3-remediation-triage.md)
e [`F3 OpenVEX`](../reports/2026-10-10-f3-openvex.json). Notas F3 por servidor
foram publicadas em `docs/issues/2026-10-10-f3-status.md` (cinco MCPs) e
`docs/security/f3-status.md` (AgentMail, onde o `.gitignore` reserva
`docs/issues/` para rascunhos locais). A pendência #1 do plano é fechada
pelo critério "documentação e triagem completas" e o resíduo (Critical
OpenSSH no gateway, ausência de Actions remotas nos SHAs candidatos) é
tratado pela nova pendência #11. Não houve commit/push dos Dockerfiles/
compose alterados, alteração de consumers nem cutover.

### F4 — Padronizar Compose e contratos de runtime

**Depende de:** contrato de transporte/health de F0 e correções F1; metadados de F2.

**Padrão a aplicar**

- **Stdio:** `stdin_open: true`, `tty: false`, sem ports, healthcheck HTTP ou serviço persistente automático; uso padrão `docker compose run --rm -T` (ou invocation equivalente do cliente MCP). Garantir stdout exclusivamente MCP.
- **HTTP:** profile/serviço dedicado, com env `MCP_TRANSPORT` (ou adapter explicitamente documentado) e healthcheck próprio. Bind default loopback; exposição pública requer opt-in, TLS/proxy/auth e firewall documentados. Evitar reservar host port no stdio.
- **Init:** um de `init: true` ou tini embutido por processo. Smoke garante graceful SIGTERM.
- **Containers:** sem `container_name` fixo onde se admitem instâncias múltiplas; labels/instance ID estáveis ajudam inventário; restart apenas para endpoint HTTP persistente ou container persistent opt-in.
- **Config/secrets:** env prefix específico por servidor, env_file opcional/obrigatório explicitado, valores default seguros; nunca imprimir secrets em `compose config` logs ou inventário.
- **Persistência:** volumes somente para dados necessários (por exemplo `/vault`, calendar data, OSM cache, Deep Research reports/logs) com caminho, read/write e UID/GID declarados; testar read-only root quando compatível.
- **Khan:** `khal` já foi incluído na imagem conforme F0/F4. D3 decide a superfície
  efetiva por gestor e D5 exige tools/call de leitura por protocolo em fixture;
  não reabrir a escolha Docker-first nem presumir modo somente leitura inexistente.
- **Percival main Compose (runtime 1, I2):** API em profile `api`, alternativa ao
  gateway sobre o mesmo estado, com `api.api_key` distinta e obrigatória no bind
  não-loopback. CLI/API/gateway usam o mesmo bind do overlay; setup mutável ocorre
  com writers parados. Gateway sem verifier pode servir login/health, mas bootstrap
  protegido retorna 401: health não prova autenticação nem provider pronto.
  Probe do broker autentica `POST /v1/health` e exige `ready: true`; doctor e MCP
  initialize/list/call verificam camadas diferentes. Nenhum HTTP healthcheck global
  na imagem multimodo/CLI. Recriar gateway e broker juntos quando muda a identidade
  do gateway. I4 ainda prepara deployment por digest e preflight single-writer;
  Render/install-service são caminhos separados, não outro writer desta instância.

**Gate F4:** `docker compose config` de cada receita passa com estado limpo; stdio não publica porta/não aloca TTY; HTTP health somente em serviço HTTP; API sem chave no bind não-loopback e volumes sem ownership correto falham fechados com mensagem útil. Registros MCP da mesma app usam `server_id` distintos na única instância Percival suportada por daemon; não prometer isolamento entre duas instalações por nome de projeto Compose.

**Execução local 2026-10-09 — implementação parcial, gate aberto:** os sete
repositórios receberam contratos/receitas Compose alinhados e documentação
operacional correspondente. `docker compose config --quiet` passou nas receitas
e profiles enumerados; verificações estruturais confirmaram stdio sem TTY/portas/
health HTTP/restart persistente e HTTP isolado com bind loopback/healthcheck.
O gateway/API passaram a bind loopback por padrão e o API usa o `api_key` já
obrigatório pelo runtime com `restart: no` para não formar restart loop sem
credencial. Notes exige mount `/vault` gravável por UID/GID 65532; o Khan tem
`khal` na dependência travada e documenta UID/GID 1000; Weather/OSM/Deep têm
serviços HTTP de profile e stdio sob demanda. Veja
[`relatório F4 Compose/runtime`](../reports/2026-10-09-f4-compose-runtime.md).

O gate **não está fechado**: não foram construídas imagens candidatas nem
executados handshakes MCP, SIGTERM, probes HTTP com containers ou teste de
persistência/restore. A F3 segue aberta por findings Critical/High e rebuild
limpo pendente, portanto esses smokes aguardam resolução/aprovação do gate F3;
nenhum consumer/container real foi alterado.

**Atualização após I2 (2026-10-23):** o snapshot acima não descreve a cobertura atual
do core. Os testes locais de runtime 1 já comprovaram auth, permissões, sinais,
probes e persistência/crash/recreate do par gateway/broker. Restore Notes/Khan e
rollback A→B→A têm evidência própria no fechamento F4/F5. O restante continua em
D5/D7/D8, com C1 para Actions; F4 não recebe aceite integral por esses testes locais.

### F5 — Conformance tests e CI por repositório

**Depende de:** F1–F4 estabelecendo contratos e builds reproduzíveis.

- Percival root CI continua autoridade para gateway/broker. I2 já integrou o runner
  isolado ao job Docker: gateway/WebUI, API auth/profile, healthcheck efetivo, Compose
  render, UID/caps/`no-new-privileges`, init e broker em Engine 27.5.1. C1 precisa
  observar esse job no SHA final e conferir `results.json`/manifests/SBOM; `status`
  continua teste CLI, não readiness. Isso não substitui o browser real em B1/B4/B6.
- MCP CI atual: AgentMail e Khan já buildam imagem e inspecionam; OSM builda amd64/arm64; Weather testa código sem Docker build; Notes e Deep Research não têm workflow Docker no checkout. Adicionar build/smoke Docker para os três últimos, e unificar os checks existentes.
- Smoke stdio comum e sem API externa: `--version` se suportado, `initialize`, `tools/list`, stdout/stderr separados, env ausente falha sem vazamento, usuário/labels/entrypoint, TTY off, nenhum port binding.
- Smoke HTTP por profile: endpoint, auth e bind seguro; `healthy` não depende da API externa a menos que readiness downstream esteja intencionalmente sendo testada.
- Matriz de architecture só inclui target aprovado e comprovado. F1–F5 do plano MCP Docker first-class (WebUI+gateway+broker, Docker operations, recovery, VPS/Engine, owner acceptance) continuam gates separados; este plano não os fecha.
- Avaliar reusable workflow ou checklist central reutilizável sem fazer os seis repos dependerem de uma publicação/ação externa não aprovada. Cada repo deve buildar no seu SHA exato.

**Gate F5:** todos os seis repositórios executam build + conformance smoke em CI no
branch/candidato; CI principal verifica Compose e broker; artefatos guardam manifest/SBOM.
Jobs de conformance/PR não publicam imagens. O futuro pipeline protegido de release é
I3/I5, separado e condicionado a B13; não enfraquecer F5 para habilitá-lo. Gates remotos
no SHA candidato são C1 e devem passar antes de alegar CI fechado.

**Execução 2026-10-09 — implementação revisada, commitada e enviada a `main`;
gate remoto aberto:** os sete repositórios receberam workflows/conformance steps próprios.
Notes e Deep Research ganharam CI Docker; AgentMail passou a usar fixture
AgentMail local e sem egress para o handshake; Weather/Deep Research exercitam
HTTP profile; OSM CI foi alinhado a linux/amd64, a única arquitetura aprovada.
Os jobs geram manifests com source SHA/base digests/lock hash/image ID e SBOM
CycloneDX como artefatos, sem push. O CI principal verifica gateway/WebUI/API,
Compose, auth/readiness e mantém o broker em Engine 27.5.1. O smoke local também
expôs um bind interno incompatível com Docker port forwarding; o gateway foi
ajustado para usar listener de container e arquivo read-only de token issuance obrigatório
para WebUI, mantendo portas publicadas em loopback. Testes/smokes locais e SHAs
base constam em [`relatório F5 CI/conformance`](../reports/2026-10-09-f5-ci-conformance.md).

O gate F5 permanece aberto porque os workflows ainda não rodaram no GitHub no
SHA candidato exato: o estado dos Actions não foi consultado (esta sessão não
tem autenticação GitHub CLI) e os artefatos manifest/SBOM ainda não foram
observados remotamente. F3 segue bloqueada por findings Critical/High sem
waivers; F4 ainda precisa concluir persistência/restore e demais evidências de
aceite. Nenhum consumer foi alterado, nenhuma imagem publicada e nenhum cutover
foi executado.

**Atualização após I2 (2026-10-23):** `ci.yml` passou a invocar
`scripts/percival-i2-runtime-smoke.py` com imagens core pré-construídas; o job
preserva `results.json` como artefato. A asserção root incompatível com `user:` foi
substituída por provas efetivas de UID/caps/init. O wrapper
`scripts/percival-f5-compose-smoke.sh` delega ao mesmo runner. Isso é implementação
e prova local, sem run remoto observado; C1 permanece aberto. I2 não produziu
scan/SBOM novo nem resolveu D6, e não reexecutou os seis workflows MCP.

### F6 — Migração local controlada e cutover por serviço

**Depende de:** F2–F5 aprovados e referências dos consumidores mapeadas em F0.
F6 continua cutover **local**; a exceção histórica não autoriza outra promoção.
No caminho publicado, aplicar o mesmo canário a artefatos adquiridos/verificados por
I3/I5/I6, sob o manager correto; não construir fonte na VPS como instalação padrão.

Executar um serviço por vez, inicialmente Deep Research e OSM (corrigindo falsos unhealthy), depois AgentMail, Weather, Khan e Notes. Para cada serviço:

1. Registrar config do consumidor, owner, server_id, imagem antiga e pin de rollback.
2. Construir a imagem candidata do SHA aprovado; inspecionar labels/digest/User/healthcheck/ports e executar smoke na fixture.
3. Adicionar a referência/tag humana sem substituir o pin imutável usado pelo broker; confirmar pelo image ID que o container usa o candidato.
4. Atualizar somente o consumidor escolhido, sem mudar simultaneamente configurações do outro sistema; verificar MCP handshake, ferramentas e operação funcional apropriada.
5. Observar `docker ps`, health conforme transport, labels, restart count e logs redigidos; persistência e tool access mantêm o comportamento esperado.
6. Se gate falhar, reverter o consumidor ao image ID/RepoDigest antigo e confirmar handshake e estado dos dados; manter ambos os artefatos até a decisão de retenção.

**Gate F6:** cada serviço tem evidência de canary e rollback independente; owner/manager labels separam Percival de Positronic. Limpeza é uma lista explícita por Image ID/digest após confirmar zero referências em containers/configs, nunca `docker image prune -a`/`system prune` como atalho.

**Execução local parcial 2026-10-10 UTC — desvio autorizado pelo operador:**
apesar de F3–F5 abertos, o operador autorizou explicitamente iniciar F6. Pelo
CLI suportado do Positronic foram atualizados Deep Research, AgentMail, Khan e
Notes para os image IDs F3 candidatos, preservando escopos, configurações,
mounts e allowlists; Notes foi reconfigurado nos dois projetos autorizados.
Handshakes MCP/tools/list passaram. Khan mantém allowlist vazia. Por pedido
posterior, foram removidos os quatro image IDs Positronic substituídos sem
containers referenciando-os. O gateway e o broker Percival estavam parados; o
gateway antigo publicaria 8765 em todas as interfaces e a configuração Compose
atual não tem o caminho do segredo de token WebUI. Por isso não foram iniciados
nem houve alteração ao config do broker: Weather, OSM e os outros dois pins
Percival ainda aguardam cutover; suas imagens antigas permanecem no Engine.
Rollback dos quatro pins Positronic exige recarregar ou reconstruir as imagens
antigas e não foi ensaiado. F6 permanece parcial e não fecha os gates F3–F5.
Evidência detalhada:
[`F6 local cutover`](../reports/2026-10-10-f6-local-cutover.md).

### F7 — Aceite de operação e manutenção

**Depende de:** F6. Gates de deployment/release aplicáveis são independentes do aceite local.

- Aprovar manual de build/update/rollback e procedimento de incidente/health false-positive.
- Definir revisão trimestral de bases/dependências, atualização urgente por vulnerabilidade, retention de tags locais e limite de imagens intermediárias.
- Depois do cutover local, atualizar o inventário. No VPS, C2–C4 do
  [plano integrado](2026-10-23-integracao-pendencias-kg-e-mcp-docker-plan.md)
  consomem I4 (layout/receita/locks) e I8 (recovery), incluindo Engine/mount/GID/UID e
  novo aceite específico; o plano MCP Docker arquivado é origem histórica, não dono ativo.
- Release/publicação segue governança B13: aprovação explícita no SHA candidato, histórico/licenças/proveniência e sem publicação implícita neste plano.

**Sessão F7 — 2026-10-10 UTC (histórico):** o operador pediu um registro explícito das
pendências que ainda impedem o aceite. O cutover local foi autorizado de
forma parcial, mas os gates anteriores não foram fechados e o deploy do
gestor Percival está interrompido. Esta sessão cataloga cada pendência, o
critério de fechamento, o responsável, a evidência esperada e o efeito sobre
o gate F7. Nenhuma das ações abaixo é executada implicitamente; cada uma
exige autorização específica e a sua própria evidência.

#### Pendências abertas

> **Fonte de verdade a partir de 2026-10-23:** o quadro abaixo e as seções de fase **não** são
> mais o rastreamento corrente das pendências. O acompanhamento passou para o
> [fechamento da padronização Docker F4/F5/F7](closed/2026-10-23-fechamento-padronizacao-docker-f4-f5-f7-plan.md)
> (itens D1–D12), com os passos de Actions e VPS em C1–C4 do
> [plano integrado](2026-10-23-integracao-pendencias-kg-e-mcp-docker-plan.md). Este quadro é
> preservado como registro de 2026-10-10 e **não** deve ser atualizado item a item: as linhas
> #2, #4, #5 e #6 já tinham evidência parcial posterior, e #11 foi dividida entre D6 (OpenSSH) e
> C1 (Actions). A incorporação posterior de I1/I2 está no quadro de evidência da §2
> e no tracker D1–D12; os estados antigos de metadata/API/runtime não prevalecem
> sobre runtime 1.

**Plano de fechamento 2026-10-10 (histórico):** [F7 — aceite de operação e manutenção](closed/2026-10-10-f7-operations-acceptance-closure-plan.md). O quadro abaixo contém snapshots anteriores; o plano de fechamento confronta seus itens com os relatórios F4/F5 e o runtime observado antes de atualizar cada status.

**Reverificação de 2026-10-23 (resultado; o quadro acima não muda).** Os onze itens foram
confrontados com o código e com as imagens. Nenhum está integralmente concluído, e três foram
corrigidos em premissa. Mapa item → dono atual → situação:

| # | Item (resumo) | Dono hoje | Situação em 2026-10-23 |
| --- | --- | --- | --- |
| 1 | F3 findings sem waiver | — | **encerrado** pelo próprio critério "documentação e triagem completas"; o resíduo Crítico migrou para #11 |
| 2 | Provisionar stack gateway/broker | — | **encerrado**; o canário F7 provou 6 MCPs nos dois gestores |
| 3 | Rotacionar a credencial exposta | D1 | **aberto** — arquivo de credencial existe, rotação adiada pelo operador |
| 4 | Concluir F4 e F5 | D7, D8, C1 | **parcial** — restore e rollback provados; falta runtime nos artefatos finais, pins por checkout limpo e Actions |
| 5 | Identidade e procedência | D2 | **aberto** — levantamento feito, decisão de atribuição pendente |
| 6 | Manual de operação/rollback | D9 | **parcial** — manual criado e consistência com comandos verificada; walkthrough e retenção pendentes |
| 7 | Allowlist do Khan e duplicatas | D3, D4 | **aberto** — e o critério de D3 estava errado: não há modo somente leitura |
| 8 | Fechar o portão de release B13 | D12 | **aberto** — dependente de D1–D10, C1–C4 e A1–A9 |
| 9 | Skill de gestão F8 e `AGENTS.md` | D11 | **parcial** — decisão extensão-vs-skill não tomada; `Notes` e `AgentMail` sem `AGENTS.md` |
| 10 | Proveniência de commits | D2 | **aberto** — número de identidade verificado; política pendente |
| 11 | Resíduo OpenSSH e VEX | D6 (OpenSSH), C1 (Actions) | **aberto, maior severidade** — gateway ainda em `openssh-client` 10.0p1; waiver não aprovado |

Evidência completa em
[auditoria planos × código](../reports/2026-10-23-auditoria-planos-vs-codigo.md).

**Progresso do plano de fechamento 2026-10-10 UTC** (relatórios e artefatos produzidos nesta sessão; sem mutações em `main`/registry/remoto):

- **P1 — Procedência e identidade (parcial):** [relatório de procedência](../reports/2026-10-10-f7-provenance-and-identity.md). Mapeamento de 6 identidades distintas em 8 repos; nenhum `.mailmap` aplicado; nenhuma reescrita de commit; sem push. Decisão de `.mailmap` × reescrita × publicação exige confirmação do operador; nenhum commit está assinado por GPG/SSH.
- **P2 — Khan allowlist e duplicatas (diagnóstico):** [relatório Khan/duplicatas](../reports/2026-10-10-f7-khan-allowlist-and-duplicates.md). Khan com 12 tools em ambos os gestores; sem decisão registrada. Duplicatas Positronic (12 `docker run` filhos do PID 3758) têm pai vivo; não há órfãos verdadeiros no snapshot. Cleanup não foi executado.
- **P3 — Manual de operação/rollback:** [manual operacional](../operations/mcp-docker-local-runbook.md) criado e vinculado a partir de [`docs/percival-governance.md`](../percival-governance.md). Cobre inventário, build, atualização, rollback, backup/restore Notes/Khan, incidentes de health e SIGTERM, revisão trimestral, urgência por CVE e retenção. Walkthrough em fixture não foi executado nesta sessão.
- **P4 — Runtime, segurança, CI:** [relatório de bloqueios P4/P5](../reports/2026-10-10-f7-p4-p5-blockers.md). `gh auth status` continua sem login; promoção de pins exige rebuild + canary; OpenSSH Forky pendente; VEX restrito ao gateway.
- **P5 — VPS/aceite:** mesma pendência. Engine 27.x e migração real não foram ensaiadas nesta sessão.

| # | Pendência | Origem | Critério de fechamento | Responsável | Evidência esperada | Efeito em F7 |
|---|---|---|---|---|---|---|
| 1 | **F3 — findings Critical/High sem waiver — fechado pelo critério "documentação e triagem completas; resíduo de blocker transferido".** Scans locais worktree candidates 2026-10-10: broker 0/0; gateway 1 Critical/64 High; Notes, AgentMail, Weather, Khan, OSM e Deep Research 0/44 High cada. O gateway conserva Critical OpenSSH; CVEs de pacote-base permanecem. | [`F3 remediation/triage`](../reports/2026-10-10-f3-remediation-triage.md) e [`F3 preflight anterior`](../reports/2026-10-09-f3-remediation-and-f6-preflight.md) | Triagem local concluída para todos os candidatos (matriz de aplicabilidade, hardening aplicado nos sete runtimes Debian, NLTK excluído de Deep Research, OpenSSH Forky 10.5p1 testado fora da imagem, OpenVEX com 6 declarações restritas ao image ID do gateway). Notas F3 publicadas em `docs/issues/2026-10-10-f3-status.md` (Notes, Weather, Khan, OSM, Deep Research) e `docs/security/f3-status.md` (AgentMail, onde o `.gitignore` reserva `docs/issues/` para rascunhos locais); commits `ab0f07d`, `d2d6458`, `9746453`, `7f6bd4f`, `3588a45`, `1db41fc`. Resíduo transferido para a pendência #11 (correção de OpenSSH client 10.0p1 e VEX/build limpo dos findings base nas Actions remotas). | agente (remediação/evidência); operador (waiver/VEX e acesso GitHub). | JSON Trivy e CycloneDX com hashes, matriz de aplicabilidade, ADR/VEX aprovados, logs/actions e comparação de source SHA/diff. | Fechado como item próprio; o resíduo crítico passa a ser tratado por #11, e a triagem documentada por servidor é a base de evidência para qualquer decisão de waiver ou fix. |
| 2 | **F4 — restore e aceite de gateway/API ainda sem evidência completa.** | [`F4 report`](../reports/2026-10-09-f4-compose-runtime.md) | `docker compose config` em cada receita, smoke isolado de `initialize`/`tools/list`/SIGTERM, probes HTTP nos profiles HTTP, restore/rollback validado para Notes e Khan. | agente. | Logs, IDs de container, screenshots. | Sem evidência de restore/rollback, o aceite F7 não pode ser assinado. |
| 3 | **F5 — execuções remotas em GitHub Actions não verificadas.** `gh auth status: not logged into any GitHub hosts`. | [`F5 report`](../reports/2026-10-09-f5-ci-conformance.md) | Cada workflow de CI passa nos SHAs candidatos; manifest/SBOM arquivados. | operador (login); agente (análise). | URLs de runs, artifacts, comparação SHA. | Gate F5 ainda aberto; sem isso, qualquer release estaria sem CI verde. |
| 4 | **Gateway/broker local em Engine 29.7.2; pins antigos ainda ativos.** O stack Compose local está `healthy` com o overlay explicitamente descartável `docker-compose.engine29-override.yml`; isso não satisfaz nem representa o gate VPS Engine 27.x. O bind histórico `0.0.0.0:8765` foi substituído pelo par atual em loopback. Config revisão 4 ainda marca AgentMail, Weather, OSM e Deep Research ativos/em `running`, com pins antigos. | [`F6 cutover report`](../reports/2026-10-10-f6-local-cutover.md) e [`F7 local stack report`](../reports/2026-10-10-f7-local-stack-provisioning.md) | Atualizar os quatro pins via API/domínio autenticado; validar readiness/canary por serviço. Manter binds de host em loopback e socket apenas no broker. O gate VPS requer inventário e Engine 27.x aprovados separadamente. | agente (mutações via domínio após credencial operator-admin); operador (senha/autorização local, gate VPS). | Compose render, `docker compose ps`, `nanobot mcp-docker doctor`, IDs das imagens/containers, GIDs, observation/health e `tools/list` por `server_id`. | F6 local permanece parcial até pins/canary e rollback; F7 continua bloqueado pelo restante das pendências e gates VPS/CI. |
| 5 | **Rollback dos quatro pins Positronic não foi ensaiado.** As imagens antigas foram removidas; rollback agora exige reconstruir/recuperar tarballs. | [`F6 cutover report` addendum](../reports/2026-10-10-f6-local-cutover.md#addendum--limpeza-solicitada-pelo-operador) | Ensaio de `update-image` + `configure` voltando para IDs antigos reconstruídos; checagem de `tools/list`. | agente. | Logs, IDs, `tools/list` antes/depois. | F7 exige rollback testado. |
| 6 | **Quatro pins Percival ainda apontando para imagens pré-F3.** OSM, Weather, AgentMail e Deep Research com `imageId` antigo. | [`F6 cutover report`](../reports/2026-10-10-f6-local-cutover.md) | Cada `server_id` aponta para o image ID candidato correspondente; `observe`/`health` retornam `running`/`ready`; `tools/list` casa o contrato. | agente (quando broker disponível). | Logs do broker, `docker inspect`, `tools/list` de cada serviço. | F6 parcial; o aceite local cobre apenas Positronic. |
| 7 | **Permissões do Khan e decisão sobre allowlist.** Tools descobertas, mas allowlist vazia no registry Positronic (`revision 7`). | [`F6 cutover report`](../reports/2026-10-10-f6-local-cutover.md) | Decisão registrada sobre manter vazia ou expor subset. | operador. | ADR ou nota em `docs/percival-governance.md`. | Acceptance F7 requer alinhamento explícito. |
| 8 | **Duplicatas Positronic AgentMail/Deep Research.** Causa da duplicação ainda não identificada. | [`F0 inventory`](../reports/2026-10-09-f0-docker-baseline-inventory.md) | Origem da segunda instância documentada; consumer identificado. | agente. | Logs de spawn/Positronic, rótulos faltantes. | Documentação de observabilidade; pode bloquear F7 se houver instâncias órfãs. |
| 9 | **Falta padronização de F8 (skill + AGENTS.md).** | [`F8 seção abaixo`](#f8--skill-de-gestão-e-instruções-operacionais-nos-agentsmd) | Matriz dos `AGENTS.md` efetiva; skill revisada com dry-run/fixture. | agente; operador (ativação). | Skill em workshop, dry-run logs. | Bloqueia F8, mas F7 é independente. |
| 10 | **Identity mismatch nos commits.** `percival-notes-mcp` ficou com `bill@percival.local`; demais repositórios com `bill-kopp-ai-dev@users.noreply.github.com`. | journal de 2026-10-10 | Commits do `percival-notes-mcp` reescritos ou reatribuídos via política `mailmap`. | agente; operador. | `git log --pretty=format:'%h %an <%ae>' -n 5` em cada repo; `mailmap` aplicado. | Não bloqueia F7 funcionalmente, mas afeta a proveniência exigida por B13. |
| 11 | **Resíduo F3 — OpenSSH `CVE-2026-60002` no gateway e ausência de Actions remotas.** Item #1 ficou fechado pela documentação; restam (a) corrigir ou waverar o `openssh-client 1:10.0p1-7+deb13u4` no gateway (teste Forky com `OpenSSH_10.5p1` já fez conexão client/server local; falta build do gateway em base Forky, regressão Percival Remote SSH na imagem, e aprovação do operador caso se opte por waiver individual), e (b) reproduzir o conjunto de scans/VEX e os fluxos F0–F3 em `linux/amd64` via Actions remotas (`gh auth status: not logged into any GitHub hosts` em 2026-10-10). | [`F3 remediation/triage`](../reports/2026-10-10-f3-remediation-triage.md), [`F3 OpenVEX`](../reports/2026-10-10-f3-openvex.json) e [`F5 report`](../reports/2026-10-09-f5-ci-conformance.md) | (a) gateway build Forky com OpenSSH >=10.4 ou waiver individual do operador; (b) login GitHub e Actions verdes nos SHAs candidatos. | operador (waiver, login); agente (build Forky, scans remotos, ADR/VEX). | Logs do build Forky, `tests/webui/test_remote_*` verdes, ADR/VEX aprovados, URLs de runs, manifest/SBOM arquivados. | Bloqueia F7 e a publicação da primeira versão 0.1.0 do Percival enquanto o Critical ou os CVEs base não tiverem reprodutibilidade no builder CI. |

#### Ações necessárias para liberar o aceite F7

1. **F3 — concluído como item de pendência #1** (documentação e triagem).
   O resíduo crítico e a ausência de Actions remotas foram transferidos para
   a pendência #11, que precisa de (a) build do gateway em base Forky com
   OpenSSH >=10.4 ou waiver individual do operador, e (b) login GitHub e
   Actions verdes nos SHAs candidatos antes do aceite F7 ou de uma eventual
   publicação 0.1.0. Triagem por imagem permanece em
   [`F3 remediation/triage`](../reports/2026-10-10-f3-remediation-triage.md)
   e o OpenVEX em
   [`f3-openvex`](../reports/2026-10-10-f3-openvex.json); notas F3 por
   servidor em `docs/issues/2026-10-10-f3-status.md` (cinco MCPs) e
   `docs/security/f3-status.md` (AgentMail).
2. **Provisionar o stack gateway/broker Percival** — criar o arquivo
    `PERCIVAL_DOCKER_GATEWAY_TOKEN_ISSUE_SECRET_FILE` (modo 0600, persistente,
    em caminho fora do repo); fixar `PERCIVAL_DOCKER_GATEWAY_HOST=0.0.0.0`
    apenas dentro do container; confirmar GIDs do socket e do token; escolher
    stack local (Host gateway vs Compose pair) compatível com Engine 29.7.2 ou
    ajustar a base do broker.
   **Progresso 2026-10-10:** segredo criado em `~/.nanobot/mcp-docker/`
   (valor não registrado), `.env` local atualizado e gateway/broker construídos
   no HEAD `86cd784052abd11915246ff9f0a5ecd62715f557` mais worktree local. O
   override do broker recebeu o nome real do gateway Compose após o primeiro
   start evidenciar a incompatibilidade. Corrigi o alias camelCase do segredo
   WebUI e testei bootstrap com o segredo do arquivo. Compose combinado validado:
   18790/8765 em host loopback, gateway sem `docker.sock`, broker com socket e
   sem porta publicada; GIDs 966 (socket) e 1999 (token) conferidos. Gateway e
   broker estão `healthy`, e `doctor` passou. Para o Engine local 29.7.2, o
   stack usa o overlay descartável Engine 29; isso não fecha gate VPS Engine
   27. O relato e IDs estão em
   [`F7 local stack provisioning`](../reports/2026-10-10-f7-local-stack-provisioning.md).
   Os quatro MCPs continuam configurados com pins antigos; mutações via API
   requerem `operator-admin` existente, cuja senha está sob controle do
   operador. Nenhuma rotação/bypass foi feita; atualizar pins e validar canary
   aguardam autenticação local autorizada.
  3. **Atualizar pins Percival e validar canary** — usar `update-image` para
     OSM, Weather, AgentMail e Deep Research; ler revisão/secret antes de
     cada mutação; verificar handshake, `tools/list`, SIGTERM, readiness HTTP
     onde aplicável e rollback ensaiado.
    **Concluído 2026-10-10:** os 6 MCPs ficaram ativos em **ambos** os agentes
    (Positronic e Percival) com os mesmos pins finais. Positronic atualizou
    Notes/AgentMail/Deep Research/Khan/Weather e instalou OSM com
    `USER_AGENT`/`FROM_HEADER` aprovados. Percival executou `update-image`
    para os 4 pins existentes e `install` para Notes e Khan, com
    `PERCIVAL_NOTES_VAULT_PATH` e `KHAN_WORKSPACE_DIR` apontando para os mounts
    reais do broker. Permissões ajustadas: `/home/bill` 755, vaults
    `/home/bill/.local/share/percival-test-mcp/{notes-vault,khan-calendar}` 777.
     Credencial `operator-admin` validada e gravada em `operator-password`
     (mode 0600); o valor foi exposto em documentação versionada e requer
     rotação e revisão do histórico remoto.
    116 imagens antigas removidas. Broker Percival reportou
    `MCP Docker broker ready` e inspecionou 6/6 servers com
    `state=running`, `docker=running`, `mcp=connected`. Ferramentas
    observadas (99 totais): agentmail 24, weather 9, osm 37, deep-research 5,
    notes 12, khan-calendar 12. Relatório:
    [`F7 canary execution`](../reports/2026-10-10-f7-canary-execution.md) e
    [`F7 local stack provisioning`](../reports/2026-10-10-f7-local-stack-provisioning.md).
 4. **Concluir F4 e F5** — smokes locais de Compose, stdio/HTTP e auth já
    possuem evidência parcial em F4/F5/F7; permanecem restore real dos dados
    Notes/Khan, rollback de imagem/config em fixture nos dois gestores,
    verificação de SIGTERM/init no runtime efetivo e Actions com manifests/SBOM
    nos SHAs finais. `gh` continua sem autenticação nesta sessão. Antes de
    novos testes autenticados, conter a credencial `operator-admin` exposta em
    documentos versionados. Restore byte a byte e rollback A→B→A já foram
    evidenciados em [F4/F5 closure report](../reports/2026-10-10-f4-f5-closure-report.md);
    o que resta é C1 (Actions), D7 (runtime nos artefatos finais) e D8 (promoção dos pins).
    Critérios de aceite: itens D7, D8, D12 do
    [fechamento da padronização F4/F5/F7](closed/2026-10-23-fechamento-padronizacao-docker-f4-f5-f7-plan.md)
    e C1 do [plano integrado](2026-10-23-integracao-pendencias-kg-e-mcp-docker-plan.md).
5. **Documentar identidade e procedência dos commits** — uniformizar o
   committer em todos os repositórios via `mailmap` ou reescrevendo o commit
   do `percival-notes-mcp`, garantindo a proveniência exigida por B13.
6. **Anexar o manual de operação/rollback** — registrar o runbook de
   atualização, incidente/health false-positive, revisão trimestral e
   retenção. Anexar a `docs/percival-governance.md` ou `docs/operations/...`.
7. **Decidir a allowlist do Khan e fechar as duplicatas Positronic** —
   registrar formalmente; remover containers órfãos, se aplicável, pelo
   caminho suportado e somente após confirmar zero referências.

**Critério vigente de F7:** D12 consolida as evidências e registra aceite local,
aceite VPS/deploy e aprovação B13 separadamente. A lista acima é histórica; os
resíduos têm dono em D1–D12/C1–C4/autenticação. I1 definiu que B13 antecede a
publicação, pull anônimo/homologação antecedem promoção e C2–C4/I9 provam o alvo.
Não usar a exigência de encerramento consolidado como dependência circular que
impeça a primeira publicação de produzir suas provas públicas; manter os gates
locais/Actions/segurança aplicáveis antes de B13. I2 não assina F7 nem certifica VPS.

### F8 — Skill de gestão e instruções operacionais nos AGENTS.md

**Depende de:** contratos e evidências F0–F7; pode preparar o texto desde F0, mas só finalizar exemplos e fluxos após o aceite operacional. **Responsável:** agente prepara inventário, skill e patches de instruções; operador revisa escopo, ativa a skill e aprova qualquer mudança global/entre repositórios.

**Cobertura de instruções (todos os `AGENTS.md` efetivos para esta operação):** revisar o `AGENTS.md` global carregado do Positronic (`$POSITRONIC_HOME/AGENTS.md`, atualmente `/home/bill/.positronic/AGENTS.md`), o `AGENTS.md` raiz do Percival, o do consumidor Positronic (`/home/bill/Projects/alternative-positronic/positronic/AGENTS.md`) e os arquivos raiz dos seis repositórios MCP. Weather, Khan Calendar, OSM e Deep Research já possuem `AGENTS.md`; Notes e AgentMail não têm arquivo raiz no inventário de 2026-10-09: criar instruções de projeto para esses dois, após conferir convenções e conteúdo local. Descobrir também qualquer outro `AGENTS.md` **efetivamente carregado** no caminho de gestão dos containers (por exemplo, subdiretórios com instruções de runtime) e incluir no checklist; não alterar templates de workspace, caches, dependências vendorizadas ou repositórios alheios a esse fluxo só porque contêm um `AGENTS.md`.

**Boas práticas a consolidar, com redação adaptada a cada escopo:**

- Inventariar antes de agir: source SHA/worktree, image ID/RepoDigest, alias, labels `owner`/`managed-by`/`server_id`/`instance_id`, referências dos consumidores, transporte, portas, mounts, volumes/dados persistentes e rollback. Não inferir dono pelo nome ou estado `unhealthy`.
- Build e promoção com versão/revisão verificáveis e pin imutável por ID/RepoDigest; tags são aliases. Não fazer pull, substituir pin ou mudar simultaneamente clientes Percival e Positronic por efeito colateral.
- Distinguir build local de distribuição: Docker Hub para oficiais, registry upstream
  homologado para terceiros, digest OCI real e aquisição explícita autorizada em I6.
  Skill não substitui policy do manager, não edita locks/config manualmente e não
  transforma README/manifest remoto em shell ou autorização. Core e MCPs têm donos distintos.
- Stdio: stdout só JSON-RPC, sem TTY, portas ou health HTTP; validar `initialize`/`tools/list`. HTTP: serviço/profile separado, auth/bind explícitos e probe apropriada. Um init por processo e evidência de parada/restart; diferenciar liveness Docker, readiness HTTP e disponibilidade MCP.
- Broker é o único componente do Percival com socket Docker; gateways e MCPs comuns não recebem socket. Respeitar limites efetivos de mounts/rede e modelo aprovado de acesso ao host, sem estreitar ou ampliar B14–B25 implicitamente; não expor secrets em env dump, logs, inventários ou snippets.
- Mudanças por instância/consumidor com prévia, backup de config/dados quando aplicável, smoke, janela de observação e rollback confirmado. Identificar containers por labels+ID antes de parar/recriar; preservar containers externos e dados; nunca limpar por nome, idade, tag órfã ou `unhealthy` isolado. Destruição, push, deploy e publicação exigem autorização específica.
- Nos `AGENTS.md` globais, usar regras curtas e transversais com link para a skill/runbook; nos de projeto, citar comando/API suportado pelo **seu próprio** gestor, smoke/CI do repo e dados persistentes. Não copiar comandos de Positronic para o broker Percival nem sobrescrever instruções existentes. Respeitar o limite de 6000 caracteres do arquivo global e verificar o texto efetivamente carregado.

**Skill recomendada:** propor uma skill de *manutenção de containers e servidores MCP do Percival* que use o fluxo de revisão do Skill Workshop. Comparar antes com `mcp-docker-workflow` (skill existente de instalação/gestão do Positronic) e escolher extensão ou skill separada apenas se cobrir trabalho novo: inventário multi-consumidor, diagnóstico stdio/HTTP, canary/rollback, retenção e incidentes. Preferir skill local ao projeto Percival se o conteúdo for específico; global somente mediante aprovação do operador e sem duplicar contratos conflitantes. A skill documenta fluxos **read-only por padrão**, comandos de operação por gestor (API/UI de domínio do Percival versus TUI/CLI do Positronic), verificação de revisão/CAS e identidade antes de mutar, pré-condições/efeitos, tratamento de segredos, evidência e rollback. Nenhuma automação de prune, instalação, reinício ou remoção implícita; exemplos de mutação devem apontar a aprovação e o mecanismo suportado.

**Gate F8:** matriz arquivo → escopo → responsável → práticas/links atualizados cobrindo global, Percival, Positronic e os seis MCPs (incluindo criação dos dois arquivos ausentes), sem contradições entre gestores; skill proposta e revisada no fluxo apropriado, com exemplo dry-run de inventário e exercício em fixture isolada de falha stdio/HTTP e rollback, sem tocar servidores reais. Validar carregamento/limite do `AGENTS.md` global, links e comandos contra a versão instalada e registrar aprovações de ativação/alterações fora do repo. Se o operador escolher estender a skill existente, documentar a decisão e provar a mesma cobertura sem duplicação.

## 4. Matriz de dependências, responsabilidade e risco

| etapa | depende de | responsável primário | risco principal | evidência para avançar |
| --- | --- | --- | --- | --- |
| F0 baseline | diagnóstico existente | operador define owners/decisões; agente coleta inventário redigido | atribuição incorreta de instância ou alteração sobre estado local | inventário por ID/digest/config; não remover nada |
| F1 health/init | F0 decisões de transporte | agente implementa por repo; operador aprova runtime local | desligar probe sem detectar falha real ou quebrar stdio | handshake/tools/list e HTTP profile testados separadamente |
| F2 identidade | F0 | agente; operador aprova nome/tag/metadata | mudar ref destrói rollback ou quebra broker pin | OCI/container labels + manifest por SHA/digest |
| F3 reproducibilidade | lock/base policy F0, contract F2 | maintainers de cada MCP e Percival | resolver conflito com política uv.lock e divergência de arch | builds clean, locks/hashes, SBOM/scan e contexto reduzido |
| F4 Compose | F0/F1/F2 | agente prepara patches por repo; operador aprova portas/volumes | expor HTTP, TTY corromper stdio, perda de persistência | Compose config + smoke isolado + restore |
| F5 CI | F1–F4 | dono do CI de cada repo | green CI não representa candidate real ou deployment | build/smoke no SHA e artifacts/provenance |
| F6 canary | F0–F5 | operador controla clients/cutover; agente prepara rollback | derrubar ferramentas de um dos consumidores ou remover imagem usada | canary independente, rollback confirmado por ID |
| F7 operação | F6; release/VPS têm gates próprios | operador aceita cutover local; agente documenta | alegar prontidão maior que evidência | manual, sign-off local e relatórios de gates separados |
| F8 skill + instruções | F0–F7; rascunhos desde F0 | agente prepara; operador aprova skill global/changes entre repos | instruções conflitantes ou automação mutável sem gate | matriz dos AGENTS.md, skill revisada, dry-run/fixture e aprovação de ativação |

### Riscos e controles transversais

| risco | controle/gate |
| --- | --- |
| Healthcheck stdio passa a esconder falha real | Descrever status como observability; MCP handshake smoke para stdio; endpoint HTTP só quando modo HTTP ativo. |
| Aliases/tags mudam o conteúdo por baixo | Broker continua fixando image ID/RepoDigest; aliases legíveis mapeados; manifest de source/revision. |
| Secret ou estado privado vai ao builder/context | `.dockerignore` comprovado em clean checkout; proibir env secrets no build args/layers; scan/inspeção de conteúdo e secrets. |
| Uma migração quebra o outro consumidor | Identificar owner por container labels/config, canary um cliente por vez, manter rollback. |
| Health/cutover afirma saúde por processo vivo | Distinguish Docker process liveness, HTTP readiness e MCP initialize/tools/list. |
| Build reprodutível congela CVEs | Pins com cadence de update e caminho urgente; scans com severity owner/waiver. |
| Rename Docker quebra configs MCP ou dados | Primeiro renomear imagem/compose labels; nomes MCP/package/state são migração compatível e trabalho separado. |
| Main Compose expõe listener/token ou inicia dois writers | API opt-in e alternativa ao gateway no mesmo estado; bind host local, API key distinta e preflight single-writer em I4. Health do gateway não comprova login nem LLM pronto. |
| Cutover no VPS conflita com gates existentes | I4/C2 resolvem paths `~/.nanobot`/`.percival`/`/srv/pblabs`; C3 ensaia migração/rollback e Engine aprovado. Browser e aceite de risco continuam gates próprios. |
| Instruções antigas ou skill de outro gestor aplicadas ao Percival | Matriz de `AGENTS.md` efetivos, delimitação de APIs/CLIs por gestor, revisão da skill existente e validação de exemplos em fixture; nenhuma mutação implícita. |

## 5. Critérios globais de conclusão

Não considerar a padronização local completa até que:

- os 6 repositórios tenham cada um uma fonte rastreável com version/revision, base digest, dependências resolvidas e platform;
- tags humanas e IDs/RepoDigests apontem para os mesmos conteúdos, e cada container criado por broker tenha owner/manager/server/instance labels;
- stdio não reserve host ports, TTY nem HTTP healthcheck; modos HTTP estejam separados e testados;
- Deep Research e OSM deixem de apresentar falsos unhealthy, e cada servidor tenha teste válido de protocolo/prontidão;
- gateway/API/Compose e os perfis de volume/porta/auth tenham smoke CI; image builds de cada repo aconteçam em CI;
- contextos de build não contenham `.venv`, `.positronic`, secrets, logs ou caches não necessários; tamanho seja medido e orçamento aceito;
- nenhum alias/deletion/cutover remova artefato necessário à rollback; imagens antigas só sejam limpas após mapear referências;
- limitações funcionais (ex. Khan `tools/call` sem prova de protocolo em D5) e incidentes residuais estejam documentados;
- F8 cubra os `AGENTS.md` efetivos do fluxo (global, Percival, Positronic e seis MCPs), com instruções específicas verificadas, e a skill recomendada tenha revisão, exercício isolado e decisão explícita de ativação;
- operações de VPS, registry, publicação e release tenham gates/aprovação próprios, sem inferência de autorização a partir deste plano.

**Conclusão de integração IaC é separada:** os critérios locais acima alimentam I2–I8,
mas não fecham I9, a publicação pública ou o P0 conjunto dos dois produtos. O aceite IaC
exige imagens reais por digest, instalação limpa, locks sob seus donos, catálogo e
aquisição MCP autorizada, update/restore e evidência do alvo; consultar I1–I9.

## 6. Verificação e governança do plano

- No Percival, executar `pytest`, `basedpyright nanobot`, `ruff check .` (não `ruff format`) e gates WebUI/CI afetados em cada alteração pertinente. Usar as canonical checks próprias de cada servidor MCP conforme seus AGENTS/CI; não propagar convenções de lint de um repo a outro.
- Toda fase deve registrar source SHA, worktree dirty state, base/digest, imagem criada, comandos exatos, teste, resultado, limitações e rollback. Não usar resultado de build de `main` como evidência de outro SHA.
- Manter em separate worktrees/branches por repos quando apropriado e revisar diffs antes de cada stage; não sobrepor nem apagar as alterações locais observadas nos seis MCP repos.
- F0 pode converter decisões aqui propostas em ADR; fases devem ser marcadas concluídas apenas com evidência do gate, não só implementação.
- Nenhum commit, push, tag, release, registry push, Catalog submission, alteração do VPS ou remoção de imagens é autorizado por este plano. Publicação exige decisão específica do operador sob `docs/percival-governance.md`.
- A inclusão de F8 acrescenta documentação multi-repositório e um gate de skill após o aceite local; não altera os contratos Docker nem a ordem de canary, mas estende a conclusão global. Tempo e esforço serão estimados após F0, quando o inventário de instruções e consumidores estiver fechado.

## 7. Próxima ação proposta

I1 e I2 estão concluídos nos seus escopos; não refazer arbitragem, alinhamento de
metadata ou matriz core por tratá-los como tarefas ainda futuras. Por decisão do
operador, o ciclo parou em I2 e **I3 está adiado**, sem implementação em curso.
Quando reautorizado, I3 começa por I3.1–I3.3 (build/test/scan sem push). Antes de
I3.4, bill prepara acesso Docker Hub no ambiente de release e decide/executa a
migração recomendada para `p-bean-labs`, revisando labels OCI antes do digest público.
Nomes decididos não comprovam acesso, publicação nem migração realizada.

Os trabalhos locais independentes continuam com seus donos em D1–D12 do
[fechamento Docker](closed/2026-10-23-fechamento-padronizacao-docker-f4-f5-f7-plan.md),
C1–C4 do [plano integrado](2026-10-23-integracao-pendencias-kg-e-mcp-docker-plan.md)
e A1–A9 de [senha única](2026-10-11-single-password-acceptance-closure-plan.md),
conforme autorização de cada execução. I1/I2 não eliminam D1 (credencial), D6
(OpenSSH), D7/D8 (artefatos finais), D9–D11 (manual/instruções) ou os gates remotos.
Não repetir o cutover dos seis MCPs apenas porque um snapshot antigo o dizia pendente;
revalidar o candidato e executar somente a lacuna remanescente.

**Estado deste documento:** ativo como plano de fases e contrato local. Não foi
substituído pela refatoração de senha única. O quadro histórico de F7 não é tracker
corrente; os quatro planos vinculados acima (incluindo I1–I9 de integração IaC) têm os
donos dos gates. Nenhuma fase ganhou aceite por esta harmonização.

**Registro desta revisão (2026-10-23):** leitura cruzada dos dois planos Docker,
ADR/handoff I1, runtime/relatório I2 e fonte atual sobre `ca19cab9`. Corrigidos
trabalho futuro já entregue, disponibilidade da API, limites de topologia, owners
de locks ainda planejados e sequência dos aceites. Evidência incorporada com sua
identidade original; sem nova execução de runtime, scan, CI remoto ou promoção.
Validação documental: 84 links locais e 2 fragmentos nos dois planos, tabelas/fences
e IDs F0–F8/D1–D12 válidos; checks do plano IaC e dos sete documentos I2 passaram;
`git diff --check` limpo. Os 38 hashes de `source-inputs.sha256` de I2 continuam
iguais, incluindo runtime/runner/contrato/relatório/`results.json`, sustentando o
reaproveitamento sem nova execução de containers.
