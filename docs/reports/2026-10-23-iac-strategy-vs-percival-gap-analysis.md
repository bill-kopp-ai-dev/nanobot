# Estratégia "Infrastructure as Code" PBLabs × estado real do Percival — análise de conformidade e gaps

- **Data:** 2026-10-23.
- **Tipo:** análise comparativa de documentação de estratégia contra o estado real do código. **Não é decisão, não é plano
  de execução e não autoriza publicação, deploy ou mudança de infraestrutura.**
- **Revisão de coerência pré-commit:** 2026-10-23. Os encaminhamentos executáveis
  estão no [plano de integração IaC](../plans/2026-10-23-iac-alignment-execution-plan.md).
  A revisão distingue base implementada de aceite de segurança, aquisição de imagem
  de spawn e evidência histórica de estado atual; não reexecutou gates operacionais.
- **Estratégia analisada:** os 5 documentos em `/home/bill/Downloads/positronic-bean-IaC/` —
  `PBLabs_Open_IaC_DockerHub_Implementation_Guide_v1.0.md` (1252 linhas, guia principal),
  `PBLabs_MCP_Distribution_Services_Strategy_v2.0.md` (1083 linhas),
  `iac-docker-first-strategy_v2.0_dockerhub.md` (1167 linhas), `stack_v0.3_dockerhub.md` (984 linhas) e
  `AGENTS.md` (351 linhas). Todos datados de **2026-10-19** e marcados como decisão vigente.
- **Alvo:** repositório `nanobot` (produto Percival) em `/home/bill/Projects/nanobot`, commit `b6ba9425`, branch
  `main`, árvore limpa, estado verificado nesta data.
- **Método:** leitura integral dos 5 documentos de estratégia; inspeção read-only do código, dos Dockerfiles, dos
  manifests Compose, do CI e dos registros de decisão do repositório; `grep` dirigido para `docker.sock`, `image:`,
  `sha256:`, `docker login`, `docker push`, `DOCKERHUB`; inspeção do diretório `~/Projects`.
- **Natureza das evidências:** todas as afirmações sobre o Percival são observações diretas do repositório ou do host,
  com `arquivo:linha`. As afirmações sobre a estratégia são citações localizadas por documento e seção.
- **Não verificado:** nenhum build, nenhum teste, nenhum container foi executado; nenhuma rede foi acessada; nenhuma
  imagem foi construída ou inspecionada em registry; nenhum estado de Docker no host foi lido. Não é possível afirmar
  que a suíte passa hoje nem que as imagens públicas existem. A namespace Docker Hub e a organização GitHub citadas
  como `pblabs` nos documentos são **ilustrativas** — os próprios documentos exigem confirmação antes de uso, e nada
  aqui confirma que existam.
- **Diretório da estratégia:** `/home/bill/Downloads/positronic-bean-IaC` contém **apenas os 5 documentos**. Não há
  `bootstrap/`, `compose/`, `opentofu/`, `schemas/`, `tests/` nem `.github/` — a estrutura recomendada no `AGENTS.md`
  §4 e no guia §5.2 **não existe em nenhuma forma, nem parcial**.

---

## 1. Conclusão

**O Percival já tem uma base de runtime MCP que deve ser aproveitada; distribuição,
integração IaC e descoberta ainda precisam de implementação e homologação próprias.**

Três conclusões, em ordem de impacto:

1. **O executor Docker tem implementação; seu aceite completo continua aberto.** As fontes afirmam que a fronteira
   de privilégio Docker é um *gap de engenharia P0* e instruem a não afirmar que já existe
   (`iac-docker-first-strategy` §16, `implementation guide` §14.3, `distribution strategy` §21 item 13). O Percival já
   tem esse componente: `percival-mcp-broker`, container separado com interface HTTP allowlisted (17 ações ADMIN + 4
   ações MCP), autenticação por bearer token, `--pull=never`, `cap_drop: ALL`, `read_only`, política de mounts e
   auditoria em `audit.jsonl`. **Não se deve reimplementar essa base por supor que inexiste.**
   Isso não prova isolamento total: B23–B25 registram risco indireto, e browser/CI/VPS
   têm gates próprios. A integração com catálogo e aquisição continua pendente.

2. **O que falta de verdade é o inverso: distribuição, IaC e descoberta.** Não existe registry escolhido, pipeline de
   publicação, `install.sh`, OpenTofu, `deployment.yaml`/`deployment.lock`, `capabilities.lock`, `pblabs-mcp-index`,
   nem os contratos IaC/MCP propostos homologados. Isso caracteriza lacunas de entrega,
   não uma porcentagem medida de progresso do sistema como um todo.

3. **Há uma lacuna contratual de aquisição que exige decisão explícita.** A estratégia exige que o
   MCP Manager **faça pull de imagem OCI por digest** de Docker Hub ou do registry upstream
   (`iac` §15.4, §20; `guide` §14.3). O broker do Percival **proíbe pull**: `--pull=never` fixo
   (`nanobot/mcp_docker/broker.py:182`) e o contrato só aceita `local-image` (ID completo) ou `pinned-image` (RepoDigest
   **já presente localmente**) — `nanobot/mcp_docker/contracts.py:22-29`. Atualizar um MCP exige hoje um
   build/load ou pull externo verificado antes da operação atual. Aquisição explícita
   por digest e spawn `--pull=never` **podem coexistir**; é preciso definir executor,
   autorização, verificação e compatibilidade para essa nova etapa.

**Recomendação:** não tratar os documentos como especificação a ser seguida cegamente. Tratá-los como **contrato
alvo a arbitrar**, usando o inventário abaixo como entrada. Antes de qualquer código, é preciso (a) corrigir os
documentos que já descrevem como aberto o que está fechado, (b) decidir o conflito pull-vs-não-pull, e (c) decidir
namespace Docker Hub e organização GitHub para a distribuição. Trabalho local independente
não precisa aguardar essas identidades.

---

## 2. O que a estratégia prescreve (síntese das 5 fontes)

Consolidado, na ordem de precedência declarada no `AGENTS.md` §2 (guia de implementação > estratégia de distribuição >
estratégia IaC > reference stack):

| # | Decisão | Onde |
|---|---|---|
| D1 | **Docker Hub (`docker.io`)** = registry principal das imagens abertas oficiais PBLabs, agentes e MCPs | `AGENTS.md` §3; `iac` §1, §51.2 |
| D2 | **GitHub** = fonte de código, IaC, documentação e curadoria; **GitHub Actions** = canal de publicação | `AGENTS.md` §3; `guide` §0.3 |
| D3 | **PBLabs MCP Index** (`pblabs-mcp-index`) = catálogo público curado em Markdown + manifests + JSON gerado; GitHub Pages **opcional** | `AGENTS.md` §6.1; `guide` §11 |
| D4 | **Docker MCP Catalog oficial é opcional**, nunca requisito. Não confundir com o Docker Hub | `AGENTS.md` §3; `distribution` §1.2.5, §4.1 |
| D5 | Runtime **registry-agnostic**: MCP comunitários vêm de `ghcr.io`/upstream sem mirror obrigatório | `AGENTS.md` §3; `distribution` §2.3 |
| D6 | **Docker/OCI é a única reference stack de produção**; `install.sh` faz só bootstrap | `iac` §2, §51.1 |
| D7 | Quatro camadas de IaC com donos distintos: OpenTofu / cloud-init+scripts / Docker Compose (core) / **Native MCP Manager** (MCPs) | `iac` §6 |
| D8 | **Um container, um lifecycle owner.** WUD é opcional e só para o core; **nunca** gerencia MCPs do manager nativo | `AGENTS.md` §3; `iac` §13, §32 |
| D9 | **O LLM não recebe `docker.sock` irrestrito.** Executor Docker confiável entre agente e daemon | `AGENTS.md` §3; `iac` §16; `guide` §14.3 |
| D10 | Produção usa **tag explícita + digest OCI**; `latest` nunca é estado; releases **não** atualizam VPS silenciosamente | `AGENTS.md` §3; `iac` §26; `distribution` §7.2 |
| D11 | Três canais: **público (P0)**, **premium GCP (P1, adiado)**, **customer-private (P2, sob contrato)** | `distribution` §1.1 |
| D12 | Estado persistente fora dos containers; `/srv/pblabs/` com `deployment.yaml` (desejado), `deployment.lock` (resolvido), `capabilities.lock` (MCP Manager) | `guide` §4; `iac` §9, §27–28 |
| D13 | **Descoberta não é autorização**; manifest remoto nunca concede privilégio | `distribution` §2.2; `guide` §0.2 |
| D14 | MCPs PBLabs e de terceiros: sem rebroadcast de identidade; fingerprint por digest homologado; curadoria por PR | `distribution` §6.3, §8.4 |
| D15 | Percival = **single-user** (derivado de nanobot); `<positronic>_` = multiusuário (derivado de OpenCode). Contrato externo comum, implementação distinta | `stack` §5; `guide` §1.1–1.2 |
| D16 | Segredos nunca em imagem, manifest, log ou código; pull público **anônimo**; publicação só no CI confiável | `stack` §20; `guide` §6.3–6.4 |

**Fases prescritas:** `P0-A` (identidades) → `P0-B` (Dockerfiles + CI dos agentes) → `P0-C` (IaC, bootstrap, locks) →
`P0-D` (template + 1º MCP) → `P0-E` (índice GitHub) → `P0-F` (executor Docker confiável + MCP Manager) → `P0-G` (2º MCP
próprio + 1 comunitário) → `P0-H` (hardening, falhas, restauração). Fonte: `AGENTS.md` §9; `guide` §17.

---

## 3. Estado real do Percival hoje

### 3.1 O que existe

| Ativo | Evidência |
|---|---|
| Dockerfile de runtime multi-stage, **bases pinadas por digest**, snapshot Debian para reprodutibilidade de `apt`, hardening (`rm nsenter`, `mount` sem suid), labels OCI completas, SBOM e Trivy no CI | `Dockerfile:1,11,25-36,15-22`; `.github/workflows/ci.yml` job `docker` |
| Dockerfile do broker separado, `USER 65532:65532`, dependências `--require-hashes` | `Dockerfile.mcp-broker:29,18-20` |
| `entrypoint.sh` com `exec` (PID 1 = Python), SIGTERM tratado, e **drop de privilégio via `setpriv` que falha fechado** (`exit 1` em vez de rodar como root) | `entrypoint.sh:54-55,72` |
| Compose com `cap_drop: [ALL]`, `security_opt: [no-new-privileges:true]`, healthchecks reais, `init: true`, limites de CPU/RAM, binds em loopback | `docker-compose.yml:1-32` |
| **`/var/run/docker.sock` montado em exatamente 1 serviço**, o broker, em overlay opt-in explícito; `nanobot-gateway`, `nanobot-api` e `nanobot-cli` nunca o veem | `docker-compose.mcp-broker.yml:41-42`; verificado por `grep` em todos os `docker-compose*.yml` |
| Fronteira de privilégio real: broker com interface HTTP allowlisted, `127.0.0.1:18081` apenas, bearer token, `--pull=never`, `cap_drop: ALL`, `read_only`, negação explícita de socket em mounts, rejeição de rootless, gate de versão do Engine | `nanobot/mcp_docker/broker.py:76-92,182`; `mount_policy.py:107-108,128` |
| Estado MCP com CAS por revisão, backups verificados, journal de transições, auditoria append-only | `nanobot/mcp_docker/service.py`; `~/.nanobot/mcp-docker/{backups,transitions,audit.jsonl}` |
| Probes de saúde reais nos três componentes | gateway `GET /health` (200/503 conforme readiness) `nanobot/cli/gateway_runtime.py:795-830`; API `nanobot/api/server.py:548`; broker `ready()` + TCP `broker.py:72-119` |
| Canário histórico com seis MCPs ativos; configuração sozinha não prova disponibilidade atual | `docs/reports/2026-10-10-f7-canary-execution.md` |
| Suítes Python/WebUI/TUI e gate de cobertura existem; contagem e sucesso atuais não foram medidos nesta análise | `tests/`, `webui/`, `tui/`, `pyproject.toml` |
| CI com 6 jobs incluindo `mcp-broker` em Docker-in-Docker, SBOM CycloneDX e evidência de fronteiras de privilégio | `.github/workflows/ci.yml` |

### 3.2 O que **não** existe

| Ausência | Verificação |
|---|---|
| **Nenhum registry escolhido.** Nenhuma menção a `docker login`, `docker push`, `DOCKERHUB` ou `dockerhub` em `.github/workflows/` | `grep` — zero ocorrências |
| **Nenhum serviço Compose com `image:`.** Todos os três serviços usam `build:`. `image:` aparece só em `docker-compose.mcp-broker.yml:18` (`percival-mcp-broker:dev`, tag mutável) e no override descartável `docker-compose.engine29-override.yml:7` | `grep "^ *image:" docker-compose*.yml` |
| **Nenhum digest em Compose.** Nenhuma forma `repo:tag@sha256:...` em nenhum manifest | `grep "sha256:" docker-compose*.yml` → vazio |
| Bootstrap PBLabs, OpenTofu e contratos de deployment/índice/locks propostos não aparecem como integração homologada neste checkout | Não confundir com instaladores ou schemas já existentes para outros domínios |
| `pblabs-iac` ou repositório equivalente | Não existe em `~/Projects` |
| `.env.example` | Referenciado por `.dockerignore` e `.gitignore`, **não commitado** |
| `HEALTHCHECK` em qualquer Dockerfile; `STOPSIGNAL` em qualquer Dockerfile | `grep "^HEALTHCHECK\|^STOPSIGNAL" Dockerfile Dockerfile.mcp-broker` → vazio |
| Workflow de publicação de imagem | Único workflow de publicação é `tui-release.yml`, que publica binários TUI (`linux-x64`, `linux-arm64`), não imagens |

### 3.3 Decisões internas do repositório que restringem a distribuição

- `docs/Decisions/2026-10-09-docker-image-posture-policy.md`: *"Status: local policy established for F3; **no
  publication or deployment authorized**"*.
- `docs/Decisions/2026-10-09-docker-standardization.md`, decisão 2: *"**Registry:** esta refatoração permanece
  **local-only**. Não escolher registry e não fazer pull/push, publicação, release ou Catalog submission; requerem
  autorização/decisão próprias."*

**O limite local-only precisa de aditamento para a evolução**, preservando as demais
decisões. A política de postura não deve ser revogada por mudar o canal de distribuição:
Critical/High continuam bloqueadores sem correção ou waiver individual. Scans de
2026-10-09 são históricos; a remediação de 2026-10-10 reduziu findings e transferiu
resíduos para D6/C1. Triagem documental não concede waiver. Avaliar o candidato exato
antes da promoção, sem atribuir a ele contagens de outra imagem.
decisão explícita do operador, não apenas um token.

---

## 4. Matriz de conformidade

Legenda: **✅** conforme no aspecto observado · **🟡** parcial ou com divergência de modelo · **❌** ausente · **⚠️** decisão
arquitetural ativo.

| Domínio da estratégia | Exigência | Estado Percival | Nota |
|---|---|---|---|
| Registry | D1 | ❌ | Nenhum registry escolhido; ADR proíbe escolher |
| Publicação CI | D1, D10 | ❌ | CI constrói e produz SBOM; nunca faz push |
| Imagem por digest | D10 | ❌ | Zero digest em qualquer manifest |
| `install.sh` bootstrap | D6 | ❌ | `scripts/install.sh` é instalador PyPI do pacote `nanobot-ai`, sem semântica de deploy |
| OpenTofu / IaC de host | D7 | ❌ | Nenhum arquivo `.tf`; nenhuma pasta `opentofu/` |
| Layout `/srv/pblabs/` | D12 | 🟡 | Estado real é `~/.nanobot` com bind único; funcionalmente equivalente (persistência fora do container) mas **sem `deployment/` nem `compose/` segregados** |
| `deployment.yaml` / `.lock` | D12 | ❌ | Nenhum dos dois |
| `capabilities.lock` | D12 | 🟡 | Estado equivalente existe em `config.json` (`mcpDocker`) com CAS + backups + journal + audit, mas **sem export de lockfile portável/handoff** |
| Executor Docker confiável | D9 | 🟡 | Broker implementado e reutilizável; integração nova e aceite de segurança no alvo continuam pendentes |
| Sem `docker.sock` no LLM | D9 | ✅ | Socket só no broker; verificado por teste em `ci.yml` |
| Native MCP Manager | D7, D8 | 🟡 | Gateway detém estado/autorização/CAS, broker executa Docker; lifecycle local existe, catálogo/export ainda não |
| Interface semântica da loja | `search_mcp_apps`, `install_mcp_app`… | 🟡 | Existe como API interna do broker (17 ações), **não** com os nomes/assinaturas do contrato prescrito, e sem busca por catálogo |
| Pull de imagem por digest | `iac` §15.4, §20 | ⚠️ **aquisição pendente** | Spawn usa `--pull=never`; aquisição explícita anterior precisa de contrato próprio |
| PBLabs MCP Index | D3 | ❌ | Não existe. MCPs instalados manualmente, por UI/CLI, sem catálogo |
| `server.json` / `pblabs.app.yaml` | `guide` §12 | ❌ | Nenhum dos dois para nenhum dos 6 MCPs |
| Comprovação de proveniência MCP | D14 | 🟡 | `docs/reports/2026-10-09-f3-image-build-manifest.json` registra tag candidata, source revision, RepoDigest e Trivy dos 8 imagens. **É evidência forte, mas é um relatório interno de 2026-10-09, não um manifest homologado e versionado** |
| Curadoria de terceiros | D14 | ❌ | Sem índice, sem revisão por PR, sem fingerprint por digest |
| Health / readiness real | `guide` §1.3 | ✅ | Três endpoints reais; `guide` §18 explicitamente proíbe inventar `/healthz` — o Percival não inventou |
| Contrato de runtime do agente | `guide` §1.3 | 🟡 | Validar usuário efetivo/probes por modo (§5.1), não apenas declarações do Dockerfile |
| Volume único de estado | D12 | ✅ | `~/.nanobot:/home/nanobot/.nanobot` em todos os serviços |
| Segredos fora da imagem | D16 | ✅ | Token do broker em arquivo 0640 com GID dedicado; chaves MCP com `kind: secret` e sentinel de redacted |
| Compose só para o core | D8 | ✅ | Nenhum container MCP em Compose; MCPs são criados pelo broker com labels de ownership |
| `linux/amd64` | `guide` §1.3 | ✅ | Decisão explícita; CI valida |
| `arm64` | adiado | ✅ | Fora de escopo por decisão registrada |
| Sandbox científico | `stack` §17 | 🟡 | `docker-compose.bwrap.yml` + bubblewrap instalado na imagem, overlay local; **`stack` §17 chama de "gap técnico prioritário"** |
| Research memory / provenance | `stack` §4.2, §15 | 🟡 | Workspace é repo git com `memory/`, `prompts/`, `skills/`, `AGENTS.md`/`SOUL.md`; KG com provenance. Falta schema formal de provenance |
| Scientific Intelligence | `stack` §4.1 | 🟡 | 6 MCPs cobrem e-mail, calendário, notas, OSM, clima, pesquisa profunda. **Falta literatura científica** (PubMed/Crossref) — candidato natural a 1º MCP oficial |
| Sem telemetry de conteúdo | `stack` §25 | 🟡 | `audit.jsonl` e `llm_usage.sqlite3` existem; **não verifiquei** se contêm conteúdo científico |
| Monitoramento / fleet inventory | `iac` §42 | ❌ | Nenhum inventário de frota; não aplicável ainda (sem clientes) |
| Backup / RPO / RTO | `stack` §27 | 🟡 | Backups de transição MCP existem e são verificados; **não há política de backup de `~/.nanobot` como um todo** (workspace, memória, config, auth) |
| Rollback do core | `iac` §21 | ❌ | Sem `deployment.lock`, sem procedimento de rollback de imagem, sem classificação migration-bearing |
| Release SemVer por digest | D10 | 🟡 | Versão `0.3.5` herdada do nanobot; **alvo público declarado é `0.1.0`** (`AGENTS.md`, `docs/percival-governance.md`) |

---

## 5. Achados que exigem decisão

### 5.1 Contrato de runtime do agente — validar os modos efetivos

O `guide` §1.3 exige "Não-root sempre que viável; UID/GID e permissões explícitos". Observado:

- `Dockerfile:103` = **`USER root`**. A justificativa está documentada no próprio Dockerfile (linhas 98–102): o
  entrypoint precisa fazer `chown` do volume Render e então cai para `nanobot` via `setpriv`. O entrypoint **falha
  fechado** (`entrypoint.sh:54-55`) em vez de continuar como root.
- `docker-compose.yml:9` define `user:` não-root com UID/GID configuráveis; também
  declara `cap_add: [CHOWN, SETGID, SETUID]`. O drop se aplica ao caminho iniciado como
  root, não automaticamente a todo serviço Compose.

O requisito é verificar UID/GID, permissões e capabilities **efetivos** em cada modo.
`USER root` isolado não prova execução root no Compose nem violação de "não-root
quando viável". A revisão I2 considera as opções abaixo, sem pressupor uma correção:

1. **Aceitar a exceção** e amendá-la no `Agent Runtime Contract` com a justificativa e as condições em que vale
   (bind mount owned por UID aritrário; Render). Requer que a camada de instalação cuide do ownership do volume.
2. **Mover o `chown` para a IaC** (`install.sh`/cloud-init criando o diretório com o UID correto) e tornar `USER` não-root
   no Dockerfile. Mais limpo, mais fiel ao contrato, mas quebra o caminho Render e exige migração do volume existente.
3. **Dois Dockerfiles** (host-IAC não-root / Render root-com-drop). Mais complexo; provavelmente desproporcional.

**Nenhuma build foi executada**; a leitura é do Dockerfile e do entrypoint.

### 5.2 Aquisição por digest versus spawn sem pull implícito

| | Estratégia | Percival |
|---|---|---|
| Texto | "`Native MCP Manager` → resolver imagem OCI por tag humana/digest homologado e efetuar pull" (`iac` §15.4); "`registry OCI (Docker Hub ou upstream) pull by verified digest`" (`iac` §20) | `args = [..., "--pull=never", ...]` (`broker.py:182`); contrato aceita só `local-image` (ID completo, `contracts.py:13,27`) ou `pinned-image` (RepoDigest **já presente localmente**, `contracts.py:14,29`) |
| Consequência | O agente é quem busca e fixa a versão | Alguém externo constrói/baixa; o agente só executa o que já está na máquina |

O contrato atual impede **pull implícito no spawn** e valida a identidade local da
imagem. Isso não prova incapacidade do agente de baixar arquivos ou introduzir bytes
por outros caminhos. O alvo IaC busca instalar artefatos OCI homologados sem build na VPS.

Não são mutuamente exclusivos — o broker poderia aceitar um `RepoDigest` e fazer o pull ele mesmo, sob as mesmas
restrições —, mas isso **é uma mudança no componente mais sensível da arquitetura** e precisa ser decidida
explicitamente. Se a decisão for manter `--pull=never`, a estratégia precisa de um passo adicional explícito: *como* a
imagem chega ao host (bundle pré-construído + `docker load`, ou `install.sh` que faz pull antes de subir o core), e
quem é responsável por verificar o digest no caminho.

### 5.3 Duas imagens e múltiplos serviços, não um core container

A estratégia ilustra o core com **um serviço `agent`** (`guide` §3.2). O Percival tem
**duas imagens**, três serviços na base (gateway, api, cli) e o quarto (broker) no
overlay opt-in. O template precisa ser adaptado a essa arquitetura:

- o `core.compose.yml` da estratégia precisa de um override para o broker, ou o Percival precisa de um
  `percival.override.yml` próprio — os dois não são o mesmo artefato;
- a Health/Readiness contract precisa cobrir **dois** componentes com respostas distintas;
- a política de atualização do core precisa decidir se gateway e broker sobem juntos (mesmo digest base) ou em
  cadência independente.

### 5.4 Dois caminhos de lifecycle concorrentes

`nanobot gateway install-service` / `uninstall-service` escreve unidades **systemd-user** (e LaunchAgent no macOS).
Isso coexiste com o Compose e cria exatamente a ambiguidade que a estratégia proíbe com `D8` ("um container, um
lifecycle owner"). Não é o mesmo vetor de conflito do MCP Manager, mas é o mesmo **tipo** de ambiguidade, e ambos
escrevem em `~/.nanobot/run/gateway.json`. Precisa de uma decisão: Compose é o caminho suportado e o
`install-service` é marcado como legado/depreciado, ou ambos são suportados com documentação de quando usar cada um.

### 5.5 Findings de segurança ativos

1. **`docker.sock` montado read-write no broker** (`docker-compose.mcp-broker.yml:41-42`, sem `read_only`). Somado ao
   bind de `/` → `/host-inventory` em modo leitura, um comprometimento do broker equivale a root no host. Isso é
   **necessário** para a função (o broker precisa operar o daemon) e é exatamente o risco que o `guide` §14.3 nomeia —
   e concentra privilégio no broker. Recomendo tratar isso como item
   explícito do threat model, com o mesmo peso dado a "LLM não recebe socket".
2. **Gate de versão do Docker Engine**: o broker exige **Server 27.x** (`broker.py:85`: `"Docker Client 27.x/29.x and
   Server 27.x required"`), rejeita rootless (linha 92), e aceita 29.x só com `PERCIVAL_DISPOSABLE_ENGINE29=1`.
   A estratégia assume "Docker Engine + Compose" genérico. **Uma VPS nova com Engine 28 ou 30 não funciona**, e a
   camada de IaC precisa declarar e **fixar** a versão de Engine do host, não apenas instalá-la.
3. **Override de Engine 29 descartável:** excluir esse opt-in das receitas de produção
   e verificar a versão real do host. Permitir a fixture 29 não significa rejeitar 27;
   não atribuir tal falha sem execução. Não copiar `.env` real para o bootstrap.
4. **Permissões amplas e administração remota:** B14/B23 aprovam acesso amplo com
   exclusões e risco indireto conhecido; `allowRemoteAdmin` é opt-in, não default
   universal. Decidir policy/consentimento do catálogo em I1/I6 sem herdar config viva
   nem restringir a instalação existente silenciosamente.
5. **Presets MCP quebrados**: o preset `github` invoca um binário chamado `agent-docker`
   (`nanobot/webui/mcp_presets_api.py:408-428`), que não existe no container do gateway (o único binário Docker real
   é `/usr/bin/docker`, `broker.py:27`). O mesmo token aparece em `webui/src/lib/code-language.ts` como rótulo de UI.
   Como o gateway não tem nem binário nem socket, **esse preset não funciona como escrito**. O preset `supabase` usa
   `npx ... @latest`, que viola a própria regra de imutabilidade da estratégia.
6. **Escopo da integração CI principal:** Weather/OSM são fixtures do job broker
   deste repositório. Isso não prova ausência de CI nos outros quatro: F5 registra
   workflows próprios nos seis MCPs; C1 exige runs nos sete SHAs candidatos. Expandir
   a matriz integrada é decisão de cobertura, não correção de CI inexistente.
7. **Paths privados/fixtures:** o canário histórico usou diretórios específicos do
   operador. O bootstrap deve gerar configuração limpa, sem esses paths ou credenciais.
8. **`tests/test_docker.sh` obsoleto**: faz `agent-docker commit` e faz grep de strings de status que não existem mais
   na CLI atual. Não está ligado ao CI e falharia se executado.

### 5.6 Versão declarada em múltiplos lugares

`pyproject.toml:3` (`0.3.5`), fallback literal em `nanobot/__init__.py:38-55`, `Dockerfile:13`, `Dockerfile.mcp-broker:5`,
`${PERCIVAL_IMAGE_VERSION:-0.3.5}` em `docker-compose.yml:15` e `docker-compose.mcp-broker.yml:16`. O CI sobrescreve
a partir do `pyproject.toml`, então a deriva é detectável, mas **não é bloqueada**. Pior: o alvo público declarado é
`0.1.0` e o valor atual `0.3.5` é metadado herdado do nanobot. Publicar `0.3.5` como primeira release PBLabs seria
confuso e contradiz `AGENTS.md` e `docs/percival-governance.md`. **`0.1.0` já está decidida
como primeira versão pretendida; falta alinhar os metadados antes de P0-B.**

---

## 6. Contradições internas entre os documentos da estratégia

Estas precisam de arbitragem **antes** da implementação, porque cada uma altera o schema ou o layout de arquivos que
serão escritos.

| # | Tema | Documento A | Documento B | Efeito |
|---|---|---|---|---|
| C1 | **`pblabs.app.yaml` tem ou não tem `distribution`?** | `distribution` §6.2: **sem** `distribution.{registry,image,tag,digest}`; tem `runtime.container`, `review.approved_release` | `guide` §12.2: **com** `distribution: {registry,image,tag,digest}`, `security.requested_mounts`, `review.last_reviewed` | Schema diverge. O `distribution` bota imagem/digest só no `app.json` gerado; o `guide` grava no manifest revisado à mão. Escolher um e versionar |
| C2 | **ID do MCP comunitário** | `distribution` §5.1/§6.3/§8.3: `community.github-official`, dir `servers/github-official/` | `guide` §11.1/§12.3/§14.5: `community.github-upstream`, dir `servers/github-upstream/` | `id` é chave de `catalog.yaml`, `app.json` e lockfile. Escolher canônico |
| C3 | **Campos de `capabilities.lock`** | `distribution` §8.3: sem `schema_version`, sem `owner`, sem `platform` | `guide` §14.5: com `schema_version`, `owner: native-mcp-manager`, `platform` | Declarar owner ajuda a reconciliação; impedir dois donos exige implementação/teste, não somente um campo. Homologar schema único |
| C4 | **Escopo do token Google premium** | `distribution` §12.2 explicita acesso ao repositório premium, não token por imagem | `iac` §12 usa a expressão mais genérica "scoped ao Artifact Registry" | Ambiguidade a esclarecer, não prova de contradição: scoped ao registry/repositório não significa por imagem. Premium permanece fora de P0 |
| C5 | **Layout de `pblabs-mcp-index`** | `distribution` §5.1: sem `scripts/`; workflows `.yaml` | `guide` §11.1: `scripts/{validate,generate_catalog,verify_oci}.py`; workflows `.yml` | O `distribution` exige verificação de disponibilidade de imagem/digest sem fornecer o script que faria isso |
| C6 | **Nomes dos documentos de entrega** | `distribution` §20.1: `docs/mcp-app-contract-v0.1.md`, `docs/public-release-runbook.md` | `stack` §41: `pblabs-mcp-app-contract-v0.1.md`, `public-distribution-runbook.md`; `guide` §5.2: `docs/agent-runtime-contract.md`, `docs/release-runbook.md`, `docs/deployment-runbook.md`, `docs/security-model.md` | Três esquemas. Fixar um |
| C7 | **Significado de "gateway"** | `distribution` §1.3: Gateway **proibido** como dono de lifecycle MCP; §6.2 cita "host/gateway" como mecanismo de egress | `iac` §15, §50: Gateway como **mediador de transporte `stdio`** / executor confiável | Três sentidos para uma palavra. A lacuna de **bridge `stdio`** permanece em `guide` §14.4. Harmonizar vocabulário antes de implementar |
| C8 | **Rótulos dos três canais** | `distribution` §1.1: "Public Distribution" / "Premium MCP Service" / "Custom MCP Delivery" | `iac` §36: `OPEN` / `COMMERCIAL` / `CUSTOMER_PRIVATE` | Mapeamento 1:1 evidente, mas os rótulos canônicos precisam ser fixados porque entram em `capabilities.lock` e em schemas |

**Nota de precedência:** o `AGENTS.md` §2 coloca o `implementation guide` como fonte **#1** e o `distribution` como
**#2**, mas o `guide` §19.1 trata o `distribution` como "definição vigente". Essa precedência parcial é a causa
provável de C1–C5. **Um passo de arbitragem explícito resolveria os oito de uma vez.**

---

## 7. Caminho recomendado

Não é plano de execução — é a ordem que a análise indica, com o critério que fecha cada etapa.

### Fase 0 — Arbitragem (sem código)

**Por que primeiro:** C1–C8 e a questão pull-vs-não-pull (5.2) determinam o schema, o layout e o desenho do broker.
Implementar antes de decidir produz trabalho descartável.

1. Decidir **organização GitHub** e **namespace Docker Hub**. Quase todo o resto depende desses dois nomes; os próprios
   documentos os tratam como ilustrativos e exigem confirmação.
2. Decidir **pull-vs-não-pull** (5.2) e, se pull, se o broker ganha essa capacidade ou se a verificação de digest
   fica na `install.sh`.
3. Arbitrar **C1–C8** e publicar a decisão num único ADR, com precedência explícita entre os quatro documentos.
4. Alinhar os metadados com a primeira versão pretendida **`0.1.0`**, já decidida,
   e documentar SemVer/imutabilidade de tags.
5. Aplicar a política de vulnerabilidades ao candidato: resolver findings ou obter
   waiver individual com os termos exigidos, sem reabrir o limiar por conveniência.

**Critério de saída:** ADR único, com as cinco decisões acima, referenciado pelos quatro documentos com
precedência corrigida.

### Fase 1 — Corrigir a premissa dos documentos

A estratégia instrui explicitamente a **não implementar o que já existe** (`guide` §14.3: *"gap de engenharia P0"*;
`distribution` §21 item 13). Deixar isso como está convida à reimplementação do broker — o componente mais sensível do
sistema. Atualizar `guide` §14.3, `iac` §16 e `distribution` §21 para apontar para o broker existente, com as
**limitações reais** dele (`--pull=never`, Engine 27.x, sem catálogo, sem export de lockfile). Registrar também que o
Percival tem **duas** imagens e **três** serviços, não um core container.

**Critério de saída:** os quatro documentos citam `percival-mcp-broker` como o executor confiável e listam suas
limitações; nenhuma frase diz "gap P0, não afirmar que já existe" sobre esse componente.

### Fase 2 — Contrato de distribuição do agente (P0-A/P0-B do lado Percival)

1. Validar probes reais por modo no Compose/contrato de imagem, sem exigir
   `HEALTHCHECK` HTTP global numa imagem que também executa CLI.
2. Validar usuário efetivo, ownership e capabilities em cada modo (§5.1); documentar
   a compatibilidade do caminho não-root e do root-com-drop fail-closed.
3. Adicionar `STOPSIGNAL SIGTERM` explícito (o comportamento já está correto; falta a declaração).
4. Workflow de publicação: buildx `linux/amd64` → scan → push por tag de release → captura do digest OCI → **pull
   anônimo com `DOCKER_CONFIG` limpo** → smoke em runtime limpo. Reaproveitar o job `docker` existente, que já gera
   SBOM e manifest.
5. Compose de **implantação** separado do Compose de **desenvolvimento**: `image:` por digest, sem `build:`, com o
   serviço `cli` disponível para `auth init` (já recomendado em
   `2026-10-11-percival-image-distribution-and-auth-recovery-review.md`).

**Critério de saída:** `docker pull` anônimo da imagem released funciona em runner limpo, com digest registrado e
arquivo de serviço com `image:` por digest.

### Fase 3 — IaC de host (P0-C)

1. Decidir a versão de **Docker Engine** do host — fixa, e **não** "mais recente" (ver 5.5.2).
2. `install.sh` idempotente: preflight → verificar/preparar Docker+Compose → criar layout → resolver digest
   homologado → `compose config` → `pull` → `up -d` → readiness → **escrever `deployment.lock` só após sucesso**.
3. `deployment.yaml` (desejado/policy, sem secrets) + `deployment.lock` (resolvido), com JSON Schema e escrita atômica.
4. Fornecer os cinco pré-requisitos que o broker exige e que a IaC precisa provisionar:
   `PERCIVAL_DOCKER_SOCKET_GID`, `PERCIVAL_BROKER_TOKEN_GID`, `PERCIVAL_STATE_HOST_PATH`,
   `PERCIVAL_BROKER_TOKEN_HOST_PATH`, `PERCIVAL_GATEWAY_CONTAINER_NAME`. **Nenhum deles é opcional.**
5. Isolar o override Engine 29 do deployment de produção. `.env` real é estado
   local ignorado, não template versionado; fornecer somente exemplos sem secrets.

**Critério de saída:** instalação limpa em Linux host novo, com `deployment.lock` correto e rollback ensaiado.

### Fase 4 — Contrato de capabilities e catálogo (P0-E)

1. Definir `capabilities.lock` — reaproveitando o que já existe em `config.json` (`mcpDocker`) e exportando-o no
   formato do contrato. Incluir `owner` e `platform` (ver C3). Sem secrets.
2. `mcp-server-template` + **primeiro MCP oficial**. **Recomendação:** escolher entre literature (PubMed/Crossref) e
   notes/calendar. As MCPs próprias existentes têm vantagem de domínio e provenance já registrada; a estratégia
   prioriza "scientific intelligence" (`stack` §4.1) e as MCPs atuais **não cobrem literatura científica**. Decisão do
   operador.
3. `pblabs-mcp-index`: `catalog.yaml`, fichas Markdown, `pblabs.app.yaml`, `catalog.json`/`app.json` gerados,
   `server.json` para o MCP oficial. Validar `server.json` contra o schema oficial — sem inventar versão.
4. Curadoria de **um MCP comunitário upstream** sem mirror, com tag+digest fixados e autoria preservada.

**Critério de saída:** dois MCPs próprios publicados e um comunitário curado, com digest homologado e fichas
coerentes com os manifests.

### Fase 5 — Decisões de produto e hardening

1. `nanobot gateway install-service`: suportado, legado ou removido (5.4).
2. Preset `github` do WebUI: corrigir (`agent-docker` não existe) ou remover. Preset `supabase`: remover `@latest`.
3. Verificar C1 nos sete SHAs candidatos e avaliar a matriz integrada sem confundir
   as duas fixtures do CI principal com toda a cobertura dos seis repositórios.
4. Substituir `tests/test_docker.sh` (obsoleto) por um teste no padrão atual, ou removê-lo.
5. Política de backup de `~/.nanobot` inteiro, não só das transições MCP.
6. Policy de catálogo: administração remota e acesso ao host exigem configuração e
   consentimento explícitos; não copiar os valores da instalação de desenvolvimento.

**Critério de saída:** nenhum caminho de lifecycle concorrente; nenhum preset que não funcione; os 6 MCPs no CI.

### Fora de escopo confirmado

Cloud Run/Firestore/Artifact Registry premium; entitlement; cobrança; marketplace;
Kubernetes; registry próprio. WUD é **opcional**, restrito ao core se validado, não
proibido pela estratégia nem requisito para fechar a distribuição aberta.

---

## 8. Riscos

| Risco | Evidência | Mitigação proposta |
|---|---|---|
| Reimplementar o executor Docker por partir da premissa "gap P0" | `guide` §14.3, `distribution` §21.13 | Fase 1 |
| Promover sem aplicar a política de vulnerabilidades ao candidato | ADR de postura; remediação/triagem histórica F3 | Fase 0 item 5, D6/C1 e scan da imagem exata |
| Schema do catálogo divergente do gerado, por causa de C1–C5 | §6 | Fase 0 item 3 |
| Broker concentra privilégio equivalente ao controle do host | `docker-compose.mcp-broker.yml:41-42` + inventário host | Threat model, API tipada/autorizada e auditoria; `:ro` no socket não impede mutações na API Docker |
| Host com Engine ≠ 27.x não funciona | `broker.py:85` | Fase 3 item 1 — fixar versão de Engine |
| Pipeline de IaC consumindo `.env` com override descartável | `.env` tem `PERCIVAL_DISPOSABLE_ENGINE29=1`; `docker-compose.engine29-override.yml` no header "NEVER use in a real deploy" | Fase 3 item 5 |
| Rate limit do Docker Hub em VPS de cliente | `distribution` §4.3: 100 pulls/6h anônimo, 200 Personal; plano pago do publicador **não** remove o limite do consumidor | Downloads sob demanda, cache local, backoff para 429; sem `pull` em loop |
| Config viva com paths de fixture como estado inicial | `~/.nanobot/config.json` → `/home/bill/.local/share/percival-test-mcp/…` | Fase 3 — `install.sh` gera config limpa |
| Duas rotas de lifecycle escrevendo `~/.nanobot/run/gateway.json` | `nanobot gateway install-service` + Compose | Fase 5 item 1 |

---

## 9. Perguntas em aberto — requerem decisão do operador

1. **Organização GitHub e namespace Docker Hub.** Bloqueia identidades públicas e
   publicação, não diagnóstico/testes locais independentes.
2. **Quem adquire e verifica imagens por digest?** (§5.2) Broker restrito ou helper
   confiável anterior ao spawn; preservar política e compatibilidade.
3. **Metadados de release:** como alinhar a fonte de versão com `0.1.0`, já decidida?
4. **Findings do candidato:** quais serão corrigidos ou submetidos a waiver individual?
5. **Usuário efetivo/ownership:** quais modos suportar e como verificá-los? (§5.1)
6. **`install-service`:** suportado, legado ou removido? (§5.4)
7. **1º MCP oficial:** literature (PubMed/Crossref, alinha com `stack` §4.1) ou reaproveitar uma MCP própria
   existente? §7 Fase 4 item 2.
8. **Policy do catálogo:** como reconciliar requisitos solicitados e acesso amplo
   B14/B23 com consentimento explícito e risco indireto conhecido? (§5.5.4)

---

## 10. Índice de evidências

**Documentos de estratégia** (`/home/bill/Downloads/positronic-bean-IaC/`): seções citadas por documento e número ao
longo do relatório. Todos datados de 2026-10-19.

**Código Percival** (`/home/bill/Projects/nanobot`, commit `b6ba9425`):

| Afirmação | Evidência |
|---|---|
| `USER root` no Dockerfile | `Dockerfile:103` |
| Sem `HEALTHCHECK`/`STOPSIGNAL` | `grep "^HEALTHCHECK\|^STOPSIGNAL" Dockerfile Dockerfile.mcp-broker` → vazio |
| Bases por digest | `Dockerfile:1,11` |
| `entrypoint` com `exec` e drop que falha fechado | `entrypoint.sh:54-55,72` |
| `docker.sock` só no broker | `docker-compose.mcp-broker.yml:41-42`; `grep` em todos os `docker-compose*.yml` |
| Sem `image:` nos serviços do core | `grep "^ *image:" docker-compose*.yml` |
| Sem digest em Compose | `grep "sha256:" docker-compose*.yml` → vazio |
| Sem publicação de imagem no CI | `grep "docker login\|docker push\|DOCKERHUB" .github/workflows/` → vazio |
| `--pull=never` | `nanobot/mcp_docker/broker.py:182` |
| Contrato de imagem só aceita ID local ou RepoDigest presente | `nanobot/mcp_docker/contracts.py:13-14,22,27,29` |
| Gate de Engine 27.x e rejeição de rootless | `nanobot/mcp_docker/broker.py:85,92` |
| Rejeição de socket em mounts | `nanobot/mcp_docker/mount_policy.py:107-108,128` |
| Health do gateway com 200/503 por readiness | `nanobot/cli/gateway_runtime.py:795-830` |
| Health da API | `nanobot/api/server.py:548` |
| `ready()` do broker | `nanobot/mcp_docker/broker.py:72-119` |
| Preset `github` com binário inexistente | `nanobot/webui/mcp_presets_api.py:408-428` |
| Versão em múltiplos lugares | `pyproject.toml:3`, `nanobot/__init__.py:38-55`, `Dockerfile:13`, `Dockerfile.mcp-broker:5`, `docker-compose.yml:15`, `docker-compose.mcp-broker.yml:16` |
| Gate de cobertura 75% | `pyproject.toml:205` |
| Duas fixtures no CI broker principal; CI próprio dos MCPs tem gate C1 separado | `.github/workflows/ci.yml:497-498`; relatório F5 e plano integrado C1 |
| Proveniência e Trivy das 8 imagens | `docs/reports/2026-10-09-f3-image-build-manifest.json` |
| Publicação não autorizada | `docs/Decisions/2026-10-09-docker-image-posture-policy.md`; `docs/Decisions/2026-10-09-docker-standardization.md` decisão 2 |
| Estado MCP, backups, journal, auditoria | `nanobot/mcp_docker/service.py`; `~/.nanobot/mcp-docker/` |
| Canário histórico com 6 MCPs ativos; não equivale a disponibilidade atual | `docs/reports/2026-10-10-f7-canary-execution.md` |

**Limitações de verificação.** Nenhum build, teste ou container foi executado. Nenhuma imagem foi construída ou
consultada em registry: ausência de pipeline no checkout **não comprova inexistência
de imagem pública**. A situação do registry não foi verificada. Nenhum estado de Docker do host foi
e de qualquer menção a registry no repositório**, não em inspeção do Docker Hub. Nenhum estado de Docker do host foi
lido. O conteúdo de `audit.jsonl` e de `llm_usage.sqlite3` não foi inspecionado quanto a vazamento de conteúdo
científico. As linhas de `nanobot/mcp_docker/broker.py`, `contracts.py` e `mount_policy.py` citadas foram confirmadas por
`grep` dirigido; a leitura completa desses módulos não foi feita nesta sessão.

---

## 11. Nota de método

Este relatório foi produzido por inspeção read-only: leitura dos 5 documentos de estratégia, leitura e `grep` do
código do repositório, e listagem de diretórios. A elaboração inicial escreveu este
relatório; a revisão documental posterior também harmonizou planos e `AGENTS.md`,
com registro no Git. Nenhum resultado de execução — build, teste, container — é afirmado aqui.
