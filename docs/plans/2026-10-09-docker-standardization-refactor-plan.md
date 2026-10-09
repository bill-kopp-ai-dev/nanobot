# Plano de refatoração — padronização dos processos Docker do Percival

- **Revisão:** 2026-10-09 / v0.7 (F0/F1 concluídos; F2 implementada com gate de
  rebuild limpo pendente; F3 implementada localmente com gate aberto; F4
  implementada localmente com gate de runtime ainda aberto).
- **Fonte de evidência:** [diagnóstico consolidado Docker](../reports/2026-10-09-docker-consolidated-diagnostic-and-standardization.md).
- **Escopo:** fluxo de build, tags/labels, Compose, entrypoints, transporte, healthchecks, CI, gestão local das imagens do Percival e dos seis servidores MCP (Notes, AgentMail, Weather, Khan Calendar, OSM e Deep Research), e orientação operacional nos `AGENTS.md` aplicáveis.
- **Estado de partida:** diagnóstico e builds de auditoria locais concluídos; não houve cutover nem alteração dos seis repositórios. Há alterações locais preexistentes em alguns MCPs; devem ser preservadas e revisadas separadamente antes de qualquer edição.
- **Execução F0:** baseline read-only e decisões do operador registrados em [inventário F0](../reports/2026-10-09-f0-docker-baseline-inventory.md) e [ADR de padronização](../Decisions/2026-10-09-docker-standardization.md). Gate F0 concluído; investigar causa das instâncias duplicadas Positronic antes de cutover/cleanup que as afete.
- **Resultado pretendido:** imagens reproduzíveis e rastreáveis, contratos de execução previsíveis para stdio/HTTP, menor risco de colisões/falsos unhealthy e um caminho verificável da fonte até uma imagem executada localmente.
- **Autoridade:** o operador decide convenções de produto, riscos e cutover. Este plano não autoriza commit/push, publicação em registry/Catalog, tag/release, limpeza de imagens fora da lista aprovada ou deploy em VPS.

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

### Fora desta primeira refatoração

- Publicar imagens, escolher registry público, ingressar no Docker MCP Catalog ou promover um release.
- Trocar o broker próprio do Percival pelo Docker MCP Gateway externo.
- Alterar contratos de tools/resources/prompts MCP sem migração compatível.
- Mudar os controles aprovados de acesso ao host do broker MCP (B14–B25), sua semântica ampla de acesso a arquivos, as coberturas de segurança ou o pin local por ID/RepoDigest.
- Remover em massa containers/imagens pelo nome, idade, status `unhealthy` ou `docker system prune`.
- Renomear o diretório local `~/Projects/nanobot`, package PyPI, histórico git ou configurar distribuição pública. O identificador **Docker-facing** deve migrar para Percival; os demais nomes são decisão separada.

## 2. Decisões e invariantes de projeto

### Invariantes a preservar

- Gateway Percival continua sem Docker socket/CLI; somente o broker separado controla o daemon, de acordo com B16/B23.
- O broker continua fixando imagens locais por ID completo ou RepoDigest validado e usa `--pull=never`; tags mutáveis não substituem o pin.
- Servidores MCP stdio reservam stdout para JSON-RPC; Compose e comandos smoke não devem alocar TTY.
- Um container stdio lançado sob demanda não deve ser tratado como serviço HTTP persistente nem receber um healthcheck HTTP.
- Valor efetivo de segurança/persistência deve ser observado; configuração solicitada, imagem/tag ou container `Up` não bastam como prova.
- Dados de notas, calendários, cache, logs/reports e estado do gateway têm mounts explícitos e separados por finalidade, com ownership e backup documentados.
- Não alterar arquivos `.gitignore`, `.positronic`, `uv.lock`, `.venv`, tags ou imagens nos seis repositórios sem examinar o estado local e preservar alterações existentes.

### Decisões F0 aprovadas

As decisões de produto estão formalizadas em
[`docs/Decisions/2026-10-09-docker-standardization.md`](../Decisions/2026-10-09-docker-standardization.md):

1. Tags locais imutáveis `<semver>-<shortsha>` e alias `:dev` somente para
   desenvolvimento; repositórios Docker-facing `percival-<service>`,
   `percival-gateway` e `percival-mcp-broker`. Manter IDs/API MCP atuais.
2. Operação local; registry remoto/pull/push/release/Catalog ficam sem decisão e
   sem autorização neste plano.
3. `linux/amd64` apenas nesta refatoração; ARM64 fora do escopo atual.
4. Rastrear `uv.lock` no Percival e usar instalação locked, incluindo estratégia
   reproduzível para dependências de canal (implementar em F3).
5. Incluir `khal` pinado na imagem do Khan para fornecer a superfície completa
   de 12 tools, sujeito às verificações F4 de tamanho/dependências/workspace.
6. API sempre ativa e protegida por `api_key` obrigatória; host bind loopback
   para API e 8765 por padrão; exposição externa exige opt-in e auth/proxy/TLS/
   firewall explícitos.
7. Preservar `percival.mcp-docker.server-id` e acrescentar labels owner,
   managed-by e instance-id; cada gestor rotula as próprias instâncias. Detalhar
   nomes/semântica das novas labels em F2.

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
- Definir `tty: false` no serviço stdio; manter só um tini (o Dockerfile já o inclui).
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

### F2 — Contrato de identidade e inventário contínuo

**Depende de:** F0. Pode correr em paralelo a correções F1 em branches/arquivos distintos.

**Trabalho**

- Definir OCI labels comuns: `title`, `description`, `source`, `documentation`, `licenses`, `version`, `revision`, `vendor`; sobrescrever explicitamente labels herdadas de imagens-base.
- Gerar VERSION de `pyproject.toml` e revision do checkout; falhar imagem candidata se `0.0.0`, `unknown` ou `local` for usado como identificador de release.
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

### F3 — Reprodutibilidade, contextos e postura base

**Depende de:** decisões de lock/base em F0 e labels/tag spec F2.

**Trabalho**

- Pin de digest para todas as bases em cada arch aprovada, incluindo stages Node, uv, Python e base Alpine; pin de toolchain uv e inputs de sistema relevantes. Planejar update cadence trimestral e atualização urgente por CVE.
- Python: usar lock validado e `uv sync --locked`/`--frozen`, ou mecanismo de imagem com hashes aprovado em F0. Corrigir Weather e OSM, que exportam requirements `--no-hashes`; pin/hash dos channel manifests do gateway. Nunca deixar atualização de patch sem fluxo de manutenção.
- Auditar tamanhos/contexto antes e depois. Excluir `.venv`, `.positronic`, `.env*`/secrets, caches, build/test artifacts e o que não é copiado por Dockerfile. Definir orçamento de contexto após baseline clean checkout (a referência local do gateway foi 346,73 MB, afetada por state local).
- Confirmar `.dockerignore` não exclui por engano arquivos necessários (`README`, `LICENSE`, `docs` embarcados ou manifest) e testar contexto em clean checkout.
- Gerar SBOM e scan de vulnerabilidade para imagem de candidato; definir antes da CI a política de severidade/waiver e owner de atualização. Scanner informa risco, não substitui pins nem revisão.
- Guardar manifest de build com source SHA, platform, base digests, dependency lock hash, image ID/RepoDigest, args não secretos e testes.

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

### F4 — Padronizar Compose e contratos de runtime

**Depende de:** contrato de transporte/health de F0 e correções F1; metadados de F2.

**Padrão a aplicar**

- **Stdio:** `stdin_open: true`, `tty: false`, sem ports, healthcheck HTTP ou serviço persistente automático; uso padrão `docker compose run --rm -T` (ou invocation equivalente do cliente MCP). Garantir stdout exclusivamente MCP.
- **HTTP:** profile/serviço dedicado, com env `MCP_TRANSPORT` (ou adapter explicitamente documentado) e healthcheck próprio. Bind default loopback; exposição pública requer opt-in, TLS/proxy/auth e firewall documentados. Evitar reservar host port no stdio.
- **Init:** um de `init: true` ou tini embutido por processo. Smoke garante graceful SIGTERM.
- **Containers:** sem `container_name` fixo onde se admitem instâncias múltiplas; labels/instance ID estáveis ajudam inventário; restart apenas para endpoint HTTP persistente ou container persistent opt-in.
- **Config/secrets:** env prefix específico por servidor, env_file opcional/obrigatório explicitado, valores default seguros; nunca imprimir secrets em `compose config` logs ou inventário.
- **Persistência:** volumes somente para dados necessários (por exemplo `/vault`, calendar data, OSM cache, Deep Research reports/logs) com caminho, read/write e UID/GID declarados; testar read-only root quando compatível.
- **Khan:** escolher e implementar uma opção: instalar `khal` com dependências no container, ou manter explicitamente host-dependent e restringir os claims de Docker-first às ferramentas suportadas. Testar tools individualmente.
- **Percival main Compose:** decidir se `nanobot-api` vai para profile opcional ou torna `api_key` obrigatório; bind 8765 seguro como padrão; evitar restart loop sem segredo; avaliar healthcheck gateway/API e inicialização recursiva de ownership.

**Gate F4:** `docker compose config` de cada receita passa com estado limpo; stdio não publica porta/não aloca TTY; HTTP health somente em serviço HTTP; API e volumes falham fechados com mensagem útil; duas instâncias do mesmo servidor não colidem por container name.

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

### F5 — Conformance tests e CI por repositório

**Depende de:** F1–F4 estabelecendo contratos e builds reproduzíveis.

- Percival root CI continua autoridade para gateway/broker. Estender job Docker para smoke de `gateway` e WebUI em fixture isolada, API auth/profile, healthcheck efetivo, Compose render, UID/capabilities/`no-new-privileges`, e broker no Engine 27.5.1 (ou versão de gate aprovada). Separar teste CLI `status` do readiness real.
- MCP CI atual: AgentMail e Khan já buildam imagem e inspecionam; OSM builda amd64/arm64; Weather testa código sem Docker build; Notes e Deep Research não têm workflow Docker no checkout. Adicionar build/smoke Docker para os três últimos, e unificar os checks existentes.
- Smoke stdio comum e sem API externa: `--version` se suportado, `initialize`, `tools/list`, stdout/stderr separados, env ausente falha sem vazamento, usuário/labels/entrypoint, TTY off, nenhum port binding.
- Smoke HTTP por profile: endpoint, auth e bind seguro; `healthy` não depende da API externa a menos que readiness downstream esteja intencionalmente sendo testada.
- Matriz de architecture só inclui target aprovado e comprovado. F1–F5 do plano MCP Docker first-class (WebUI+gateway+broker, Docker operations, recovery, VPS/Engine, owner acceptance) continuam gates separados; este plano não os fecha.
- Avaliar reusable workflow ou checklist central reutilizável sem fazer os seis repos dependerem de uma publicação/ação externa não aprovada. Cada repo deve buildar no seu SHA exato.

**Gate F5:** todos os seis repositórios executam build + conformance smoke em CI no branch/candidato; main project CI verifica Compose e broker; artefatos guardam manifest/SBOM; nenhum job publica imagem. Gates remotos GitHub Actions no SHA candidato devem passar antes de alegar CI fechado.

### F6 — Migração local controlada e cutover por serviço

**Depende de:** F2–F5 aprovados e referências dos consumidores mapeadas em F0.

Executar um serviço por vez, inicialmente Deep Research e OSM (corrigindo falsos unhealthy), depois AgentMail, Weather, Khan e Notes. Para cada serviço:

1. Registrar config do consumidor, owner, server_id, imagem antiga e pin de rollback.
2. Construir a imagem candidata do SHA aprovado; inspecionar labels/digest/User/healthcheck/ports e executar smoke na fixture.
3. Adicionar a referência/tag humana sem substituir o pin imutável usado pelo broker; confirmar pelo image ID que o container usa o candidato.
4. Atualizar somente o consumidor escolhido, sem mudar simultaneamente configurações do outro sistema; verificar MCP handshake, ferramentas e operação funcional apropriada.
5. Observar `docker ps`, health conforme transport, labels, restart count e logs redigidos; persistência e tool access mantêm o comportamento esperado.
6. Se gate falhar, reverter o consumidor ao image ID/RepoDigest antigo e confirmar handshake e estado dos dados; manter ambos os artefatos até a decisão de retenção.

**Gate F6:** cada serviço tem evidência de canary e rollback independente; owner/manager labels separam Percival de Positronic. Limpeza é uma lista explícita por Image ID/digest após confirmar zero referências em containers/configs, nunca `docker image prune -a`/`system prune` como atalho.

### F7 — Aceite de operação e manutenção

**Depende de:** F6. Gates de deployment/release aplicáveis são independentes do aceite local.

- Aprovar manual de build/update/rollback e procedimento de incidente/health false-positive.
- Definir revisão trimestral de bases/dependências, atualização urgente por vulnerabilidade, retention de tags locais e limite de imagens intermediárias.
- Depois de cutover local, atualizar o relatório de inventário; para o VPS, executar gates e migração do plano `2026-10-06-mcp-docker-first-class-execution-plan.md` incluindo engine/mount/GID/UID e aceite de risco específico.
- Release/publicação segue governança B13: aprovação explícita no SHA candidato, histórico/licenças/proveniência e sem publicação implícita neste plano.

**Gate F7:** evidência por stage, owners para manutenção, rollback testado, limitações registradas; operador aceita cutover local. “Pronto para release” exige além disso os gates específicos de Percival/CI/VPS e sign-off do operador.

### F8 — Skill de gestão e instruções operacionais nos AGENTS.md

**Depende de:** contratos e evidências F0–F7; pode preparar o texto desde F0, mas só finalizar exemplos e fluxos após o aceite operacional. **Responsável:** agente prepara inventário, skill e patches de instruções; operador revisa escopo, ativa a skill e aprova qualquer mudança global/entre repositórios.

**Cobertura de instruções (todos os `AGENTS.md` efetivos para esta operação):** revisar o `AGENTS.md` global carregado do Positronic (`$POSITRONIC_HOME/AGENTS.md`, atualmente `/home/bill/.positronic/AGENTS.md`), o `AGENTS.md` raiz do Percival, o do consumidor Positronic (`/home/bill/Projects/alternative-positronic/positronic/AGENTS.md`) e os arquivos raiz dos seis repositórios MCP. Weather, Khan Calendar, OSM e Deep Research já possuem `AGENTS.md`; Notes e AgentMail não têm arquivo raiz no inventário de 2026-10-09: criar instruções de projeto para esses dois, após conferir convenções e conteúdo local. Descobrir também qualquer outro `AGENTS.md` **efetivamente carregado** no caminho de gestão dos containers (por exemplo, subdiretórios com instruções de runtime) e incluir no checklist; não alterar templates de workspace, caches, dependências vendorizadas ou repositórios alheios a esse fluxo só porque contêm um `AGENTS.md`.

**Boas práticas a consolidar, com redação adaptada a cada escopo:**

- Inventariar antes de agir: source SHA/worktree, image ID/RepoDigest, alias, labels `owner`/`managed-by`/`server_id`/`instance_id`, referências dos consumidores, transporte, portas, mounts, volumes/dados persistentes e rollback. Não inferir dono pelo nome ou estado `unhealthy`.
- Build e promoção com versão/revisão verificáveis e pin imutável por ID/RepoDigest; tags são aliases. Não fazer pull, substituir pin ou mudar simultaneamente clientes Percival e Positronic por efeito colateral.
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
| Main Compose expõe listener/token ou API fica em loop | Bind local por padrão, API opt-in ou auth necessária, smoke com config vazia e de auth. |
| Cutover no VPS conflita com gates existentes | Este plano não substitui migração `.nanobot` → `.percival`, Engine 27.x, Browser F3/F4/F5 nem aceite de risco do plano MCP Docker. |
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
- limitações funcionais (ex. Khan sem khal na imagem) e incidentes residuais estejam documentados;
- F8 cubra os `AGENTS.md` efetivos do fluxo (global, Percival, Positronic e seis MCPs), com instruções específicas verificadas, e a skill recomendada tenha revisão, exercício isolado e decisão explícita de ativação;
- operações de VPS, registry, publicação e release tenham gates/aprovação próprios, sem inferência de autorização a partir deste plano.

## 6. Verificação e governança do plano

- No Percival, executar `pytest`, `basedpyright nanobot`, `ruff check .` (não `ruff format`) e gates WebUI/CI afetados em cada alteração pertinente. Usar as canonical checks próprias de cada servidor MCP conforme seus AGENTS/CI; não propagar convenções de lint de um repo a outro.
- Toda fase deve registrar source SHA, worktree dirty state, base/digest, imagem criada, comandos exatos, teste, resultado, limitações e rollback. Não usar resultado de build de `main` como evidência de outro SHA.
- Manter em separate worktrees/branches por repos quando apropriado e revisar diffs antes de cada stage; não sobrepor nem apagar as alterações locais observadas nos seis MCP repos.
- F0 pode converter decisões aqui propostas em ADR; fases devem ser marcadas concluídas apenas com evidência do gate, não só implementação.
- Nenhum commit, push, tag, release, registry push, Catalog submission, alteração do VPS ou remoção de imagens é autorizado por este plano. Publicação exige decisão específica do operador sob `docs/percival-governance.md`.
- A inclusão de F8 acrescenta documentação multi-repositório e um gate de skill após o aceite local; não altera os contratos Docker nem a ordem de canary, mas estende a conclusão global. Tempo e esforço serão estimados após F0, quando o inventário de instruções e consumidores estiver fechado.

## 7. Próxima ação proposta

Triar e resolver os findings Critical/High F3, priorizando dependências com
versão corrigida disponível e os pacotes base reportados; registrar owner e
expiração antes de qualquer waiver. Depois, repetir builds/scan em checkouts
limpos no builder CI e fechar F3 somente com evidência do conjunto resolvido.
F2 ainda depende de rebuilds canônicos limpos. Não iniciar F4/cutover a partir
de candidatos locais não aceitos; manter imagens e consumers históricos sem
alteração.
