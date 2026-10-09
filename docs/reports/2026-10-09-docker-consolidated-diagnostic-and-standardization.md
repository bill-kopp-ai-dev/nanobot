# Diagnóstico consolidado Docker — Percival e servidores MCP locais

**Data:** 2026-10-09
**Escopo:** stack Docker do Percival em `/home/bill/Projects/nanobot` e os
servidores MCP locais Notes, AgentMail, Weather, Khan Calendar, OSM e Deep
Research.

## Conclusão executiva

O Docker já é um caminho funcional de execução e existe uma base útil para
gateway/broker, mas o fluxo completo ainda não está pronto para distribuição
estável. As principais causas de confusão operacional são: imagens MCP
repetidas sem tags legíveis, metadados de versão/revisão ausentes ou
divergentes, contratos de healthcheck incompatíveis com stdio e diferenças de
Compose/CI entre os seis servidores.

O problema mais visível do snapshot — dois contêineres `unhealthy` — é um falso
negativo do healthcheck de Deep Research: ambos executam stdio, mas o Docker
sonda HTTP. Eles usam o mesmo image ID `fa1e3cec8cd3…`, sem RepoTag nem
RepoDigest local. O OSM tem um defeito separado: o healthcheck stdio chama
`pgrep`, que não está instalado na imagem OSM examinada. Os dois AgentMail
ativos estão `running` **sem healthcheck**; isso não significa que Docker
confirmou sua saúde. A imagem em execução é antiga e está rotulada `0.0.0` /
revision `unknown`, enquanto o código-fonte atual declara a versão 0.4.0.

Recomendação: corrigir primeiro os contratos de healthcheck/init/TTY e
construir um inventário com identidade imutável e legível. Só depois decidir a
limpeza de imagens/container antigos, verificando antes quais configurações do
Percival e do Positronic ainda os referenciam.

## 1. Inventário do runtime observado

### Contêineres ativos

| contêiner | imagem / identidade | estado | interpretação |
| --- | --- | --- | --- |
| `nanobot-gateway` | `nanobot-nanobot-gateway` | running; `8765` publicado em `0.0.0.0`/`::`, `18790` em loopback | gateway/WebUI do Percival |
| `nanobot-percival-mcp-broker-1` | `percival-mcp-broker:local` | running, healthy | broker do Percival |
| `flamboyant_leavitt` | Deep Research, ID `fa1e3cec8cd3…`, label `3.0.1`, sem RepoTag/Digest | running, unhealthy | stdio funcional; probe HTTP falha |
| `priceless_rosalind` | mesmo ID/labels de Deep Research | running, unhealthy | segunda instância idêntica; sem label de consumidor |
| `amazing_lumiere` | AgentMail, ID `f7acd7fa97c3…`, labels `0.0.0`/`unknown`, sem RepoTag/Digest | running, healthcheck ausente | Docker não reporta healthy/unhealthy |
| `sleepy_swanson` | mesmo ID/labels de AgentMail | running, healthcheck ausente | segunda instância idêntica |

No diagnóstico original, o servidor Deep Research respondeu a `tools/list`;
essa observação não foi repetida para cada instância. Portanto, `unhealthy` por
si só não prova falha do MCP. A ausência de labels de owner/gestor no container
também impede afirmar, pela inspeção Docker, qual instância pertence ao
Percival e qual ao Positronic; as labels da imagem identificam somente o
servidor.

Na janela inicial de 08:35 havia uma instância de cada servidor (Deep Research
e AgentMail). Os timestamps de criação mostram que as segundas instâncias
`priceless_rosalind` e `amazing_lumiere` apareceram por volta de 08:43. Não foi
confirmado qual processo/cliente criou esse segundo par.

### Contêineres históricos relevantes

| contêiner | imagem | status observado | evidência relevante |
| --- | --- | --- | --- |
| `percival-mcp-osm` | `percival-osm`, revision `5f80a41` | exited (143), unhealthy | log do healthcheck: `/bin/sh: 1: pgrep: not found` |
| `percival-mcp-deep-research` | ID `4882d99a4146…`, label `3.0.1` | exited (143), unhealthy | healthcheck HTTP com transporte stdio |
| `percival-mcp-weather` | ID `1f87321f15c4…` | exited (255), sem healthcheck | causa do exit não determinada |
| `percival-mcp-agentmail` | ID `d4eb9e2e6f80…` | exited (255), sem healthcheck | causa do exit não determinada |
| `percival-f2-engine27` | `docker:27.5.1-dind` | exited (0) | fixture de smoke anterior |

### Imagens locais e rastreabilidade

O inventário encontrou nomes/tags de estilos diferentes:

- Notes: `positronic/notes:0.1.5-local`, `percival-notes-mcp:docker-test`.
- AgentMail: `percival-agentmail-mcp:dev`, além das instâncias em execução sem
  tag e da imagem rotulada `0.0.0`/`unknown`.
- Weather: `percival-weather-mcp:audit` e tags de fixtures F1/F2.
- Khan Calendar: `positronic/khan-calendar:0.4.0-local` e
  `percival-khan-calendar:dev`.
- OSM: `percival-osm:local` e imagens de fixtures F1/F2.
- Deep Research: `percival-deep-research:dev`, `:smoke`, tags sob
  `localhost:5000/percival/deep-research` e imagens em execução sem tag.
  Existem cópias locais de cerca de 1,37 GB com label `3.0.1`, mas IDs
  diferentes.

A linha `unsee` vista no lazydocker era um fallback de exibição, não o nome
real do servidor. A inspeção de labels mostra `percival-deep-research` v3.0.1;
a imagem não tem RepoTag nem RepoDigest. O ID preserva a identidade do
conteúdo, conforme o pin local do broker, mas sem alias legível, revision e
label de instância fica difícil distinguir build atual de cópia antiga.

## 2. Sequência de warm-up do broker

No snapshot das 08:35 locais, o broker tentou iniciar `confident_heisenberg`
(Deep Research) e `jovial_hoover` (AgentMail); ambos saíram após cerca de cinco
segundos. Em seguida, o broker criou `flamboyant_leavitt` e `sleepy_swanson`,
que permaneceram ativos. Os logs do Docker não indicaram OOM ou escalação de
sinal para a primeira dupla; o padrão é compatível com retentativa após falha
de prontidão.

O processo do broker tinha sido reiniciado por volta das 08:11 locais dentro
de um container mais antigo (criado em 2026-10-08). **A causa desse restart e
a causa exata da falha da primeira dupla continuam sem confirmação.** O padrão
foi observado numa única janela, sem série temporal para estimar frequência.

## 3. Stack principal do Percival: Compose e construção da imagem

O fluxo principal tem duas imagens: gateway + WebUI no `Dockerfile`, e broker
MCP em `Dockerfile.mcp-broker`. O broker usa Docker CLI 27.5.1 pinada por
digest, UID 65532, filesystem read-only e é o único serviço com socket Docker.
O Compose combina a topologia pelo overlay `docker-compose.mcp-broker.yml`;
`docker-compose.engine29-override.yml` é explicitamente descartável/local.

### Bloqueios para distribuição confiável

1. **Reprodutibilidade do gateway incompleta.** O `Dockerfile` usa tags
   mutáveis para `node:24-bookworm-slim` e a imagem uv/Python. Instala Python
   com `uv pip install .`, sem lock copiado; `uv.lock` é ignorado neste
   checkout. Dependências de canais também são resolvidas de faixas/manifests
   sem hash. O build observado resolveu 98 pacotes; builds do mesmo commit
   podem resultar em dependências/base diferentes. A documentação descreve a
   pré-instalação por `NANOBOT_CHANNELS` como reprodutível, garantia mais forte
   que o fluxo atual.
2. **Porta 8765 aberta em todas as interfaces.** O Compose limita `18790` a
   `127.0.0.1`, mas publica `8765` sem `host_ip`; a configuração efetiva
   mostrou bindings em `0.0.0.0` e `::`. O token e firewall podem mitigar, mas
   o bind público não deveria ser implícito para toda instalação.
3. **Labels OCI incorretas na imagem gateway.** A imagem final herda labels da
   base uv — title/source/revision e version de uv — em vez de identificar
   Percival. Gateway/API/CLI não declaram `image:` explicitamente; Compose
   sintetiza nomes dependentes do project name. Os identificadores Docker
   ainda usam `nanobot`; padronizar para `percival`, com migração documentada.
4. **Contexto local grande.** O build transmitiu 346,73 MB. `.dockerignore`
   não exclui `.venv`, `.positronic` e vários caches/testes/documentos. O
   diretório `.venv` local ocupava 832 MB em disco. Isso aumenta custo de build
   e pode enviar estado local desnecessário a builders remotos.
5. **Health/prontidão do gateway não monitorados.** Gateway e API não têm
   healthcheck no Compose. O CI executa `status` e verifica fronteira de
   privilégios, mas não inicia o gateway/WebUI em Compose para medir prontidão.
6. **API pode entrar em restart loop.** `nanobot-api` é serviço padrão, força
   `serve --host 0.0.0.0` e não recebe nem exige `api_key` no Compose. O comando
   recusa wildcard sem chave; isso foi reproduzido em teste isolado. Com
   `restart: unless-stopped`, `docker compose up` sem chave reinicia o
   serviço. Decidir se a API fica em profile opcional ou se requer chave
   explicitamente; não remover a autenticação.
7. **Ownership do volume é corrigido recursivamente em cada startup root.**
   `entrypoint.sh` executa `chown -R nanobot:nanobot` em todo o diretório
   persistente antes de reduzir para UID 1000. Isso pode alongar restart e
   reatribuir ownership em hosts com UIDs diferentes. O código preserva o
   grupo dedicado do token do broker; um novo teste de migração de ownership
   em host/VPS não foi executado nesta revisão.
8. **Teste Docker legado não é gate de CI.** `tests/test_docker.sh` chama
   `agent-docker commit` e não tem `trap` de cleanup; o workflow usa checks
   inline diferentes e não cobre serviço gateway pronto.

### Aspectos positivos confirmados

- O Dockerfile principal é multi-stage; `npm ci` usa `package-lock.json` e
  somente o `dist` da WebUI segue para o runtime.
- O processo da aplicação reduz para UID 1000; o Compose limita capabilities,
  usa `no-new-privileges` e preserva os perfis de segurança padrão.
- O broker está isolado em sidecar: somente ele recebe o socket, não publica
  portas, roda como UID 65532, com filesystem read-only e capabilities
  removidas. A imagem do broker usa digest fixo e tem smoke em Engine 27.5.1
  na CI.

### Evidência local de build

- `docker build --check .` e `docker build --check -f Dockerfile.mcp-broker .`
  passaram sem warnings.
- Builds reais temporários do gateway e broker passaram. O gateway iniciou o
  entrypoint, reduziu para `nanobot` e executou `status` sem mount de dados; a
  ausência de config/workspace era esperada. As imagens temporárias foram
  removidas após os testes.
- `docker compose config` da base + broker overlay + override local passou e
  confirmou volumes, binds, portas e isolamento do socket.
- Não houve `compose up`, deploy, push, publicação ou mutação de container
  persistente. O build WebUI passou com avisos de Browserslist desatualizado e
  chunks acima de 500 kB (chunk principal ~585 kB).

## 4. Comparação dos seis repositórios MCP

| servidor | build e execução | health/transporte | Compose, metadados e CI |
| --- | --- | --- | --- |
| **Notes** | Python 3.12 Bookworm pinada por digest, uv 0.12.18, `uv sync --frozen`, usuário 65532. Entrypoint exige `/vault` montado. | Stdio; sem porta/healthcheck. | Sem Compose/CI encontrados; sem labels OCI no Dockerfile. README inclui smoke de build/stdio/inspect. `.dockerignore` allowlist pequena. |
| **AgentMail** | Multi-stage, `uv.lock`, `uv sync --locked`, usuário 1000; bases e uv 0.5.11 via tags mutáveis. | Stdio; sem `EXPOSE`/healthcheck. | Compose `:dev`, `init: true`, `stdin_open`, `tty: false`, `.env`; CI builda, verifica `--version`, erro de config e labels. Build args default `0.0.0`/`unknown`; atual Compose passa versão/revisão local, mas runtime observado é imagem antiga sem revisão. |
| **Weather** | Lock existe, mas Dockerfile exporta requirements com `--no-hashes`; base Python e uv 0.5.7 sem digest; usuário não-root. | Stdio default; HTTP opcional; deliberadamente sem healthcheck de imagem. Documenta `/healthz` em HTTP. Entry point chama modos `http`/`http-loopback`, diferentes de `streamable-http`. | Sem Compose; possui `mcp.yaml`, manifesto Catalog e `io.docker.server.metadata`. CI testa código, não constrói Docker; labels OCI sem version/revision convencionais. |
| **Khan Calendar** | Multi-stage, lock + `uv sync --locked`, usuário 1000; bases e uv 0.5.11 sem digest. | Stdio; sem porta/healthcheck. Compose adiciona um único `init: true`. | Compose `:dev`, build args fixos `VERSION=0.4.0`/`GIT_SHA=local`; uma tag local `0.4.0-local` inspecionada tinha labels `0.0.0`/`unknown`. CI verifica build, versão, help e labels. `khal` não está na imagem: ferramentas CLI dependem de binário externo ao container. |
| **OSM** | `uv sync --frozen`, mas bases sem digest e requirements exportados `--no-hashes`. Usuário 10001; imagem inclui tini. | Stdio/HTTP por `MODE`; healthcheck stdio chama `pgrep`, mas `procps` não é instalado. A imagem testada confirma `pgrep` ausente. | Compose tem `container_name` fixo, `tty: true` em stdio e profile HTTP; CI faz build multiarch e teste de catálogo. Metadata MCP disponível; versão OCI não uniforme. |
| **Deep Research** | Multi-stage, lock + `uv sync --frozen`, patch obrigatório para gpt-researcher, usuário 1000; imagem ~1,37 GB; bases sem digest. | Default stdio, healthcheck Docker sempre HTTP `/health`; gera falso unhealthy. Dockerfile e Compose ambos incluem init (tini + `init: true`). | Compose publica 8000 mesmo em stdio, define restart e nome fixo de rede. Label fixa versão `3.0.1`, sem revision; não foi encontrado job Docker CI neste checkout. |

## 5. Padrão comum recomendado

Padronizar o **contrato operacional e metadados**, preservando diferenças
justificadas de dependências e de dados:

1. **Stdio como default MCP:** anexar stdin, `tty: false`, não publicar portas;
   processo iniciado pelo cliente é efêmero e não precisa `restart`. HTTP fica
   em profile/serviço separado, com porta e autenticação adequadas.
2. **Health por transporte:** sem probe HTTP para servidor stdio. Validar
   protocolo por `initialize` + `tools/list`; probes HTTP pertencem ao profile
   HTTP. Separar liveness de readiness upstream e instalar/utilizar apenas
   ferramentas realmente presentes na imagem.
3. **Um único init:** escolher entre `init: true` do Docker ou tini dentro da
   imagem; não usar ambos. TTY nunca deve ser ligado ao stream JSON-RPC.
4. **Imagem rastreável:** nome/tag Docker legível usando `percival` (substituir
   namespaces expostos `positronic`/`nanobot`), tags dev separadas de SemVer,
   e OCI labels title, description, source, documentation, license, version,
   revision e vendor. Versão/commit devem vir automaticamente do
   `pyproject.toml` e checkout. Manter o pin do broker por image ID/RepoDigest,
   junto a alias legível e inventário da revisão.
5. **Instâncias identificáveis:** labels Docker de container para `server_id`,
   owner/consumidor (`percival`/`positronic`), gestor e instance ID. Evitar
   `container_name` fixo onde múltiplas instâncias possam coexistir. Não
   renomear ferramentas/servidores MCP como efeito colateral; esses nomes são
   contratos de cliente e exigem migração compatível.
6. **Build reprodutível:** pin de digest das bases, lock/frozen e hashes para
   Python/canais, `npm ci` com lock para frontend; atualização periódica dos
   pins para incorporar patches de segurança. Enxugar `.dockerignore` para não
   enviar venv, estado Positronic, caches, dados ou artefatos de teste.
7. **Compose/CI:** um contrato de volumes/env documentado por servidor, sem
   Docker socket em MCPs comuns. Todo Dockerfile deve ter build CI; smoke comum
   deve verificar metadata/user/entrypoint, MCP initialize/tools/list sem API
   externa e health HTTP apenas no modo HTTP. Manter metadata Catalog separada
   de OCI labels genéricas.
8. **Exceções funcionais explícitas:** decidir se Khan inclui `khal` na imagem
   para execução totalmente Docker-first ou preserva ferramentas host-dependent
   por decisão de tamanho/arquitetura.

## 6. Sequência de execução

1. **Corrigir Deep Research:** separar stdio de HTTP health/port mapping,
   remover um nível de tini e criar profile/serviço HTTP próprio. Rebuild com
   revision explícita; validar MCP initialize/tools/list e HTTP health no
   profile correto. Não apagar as cópias antigas ainda.
2. **Corrigir OSM:** retirar `pgrep` ausente ou o healthcheck stdio; desligar
   TTY em stdio e testar ambos os transports.
3. **Fechar inventário e convenções:** definir nome Docker `percival`, formato
   de tags, OCI/container labels e como o broker mantém pin por ID/RepoDigest
   sem perder rastreabilidade humana. Mapear owner/manager para cada instância.
4. **Revisar gateway/API e build:** fechar bind de 8765, API key/profile,
   healthcheck, ownership do volume, digests/locks e contexto Docker.
5. **Alinhar CI dos seis repositórios** e documentar a exceção do `khal`.
6. **Só então limpar imagens/containers antigos**, confirmando referências
   Positronic/Percival e mantendo rollback. Não remover por nome aleatório,
   data ou `unhealthy` isoladamente.

## 7. Verificações e limitações

- Foram examinados os três relatórios-base, arquivos de instrução aplicáveis,
  Dockerfiles, Compose, `.dockerignore`, `pyproject.toml`, documentação e
  workflows dos seis repositórios.
- Docker Compose renderizou com sucesso; os dois Dockerfiles do stack Percival
  passaram `docker build --check` e builds reais de auditoria; um smoke de
  gateway executou `status`; a recusa da API sem key foi reproduzida. Um
  container efêmero `--network none` confirmou `pgrep` ausente em OSM.
- Não foram feitos builds dos seis MCPs, chamadas a APIs externas, inspeção de
  credenciais, deploy/VPS, publicação, Browser WebUI+gateway+broker ou remoção
  de recursos persistentes. As alterações locais preexistentes nos seis
  repositórios foram preservadas.
- A causa do restart do broker e dos exit codes 255 permanece sem confirmação.
  O inventário é uma observação do host em 2026-10-09, não uma série temporal;
  namespaces host-network e workloads k8s-adjacentes não foram enumerados.
