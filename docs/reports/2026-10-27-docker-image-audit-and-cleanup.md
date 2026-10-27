# Auditoria de imagens Docker do host — inventário, limpeza e postura de vulnerabilidades

- **Data:** 2026-10-27 (UTC-03:00), coleta entre 18:45 e 19:20.
- **Escopo:** store de imagens, containers, volumes e cache de build do daemon Docker
  rootful do host (Client/Server 29.9.2); frota Percival (6 MCPs + gateway/broker) e a
  imagem do agente Positronic.
- **Autorização:** pedido explícito do operador em 2026-10-27 — eliminar imagens antigas,
  manter apenas as atuais, auditar as desconhecidas e corrigir as com problemas. A
  execução seguiu o [runbook MCP Docker local](../operations/mcp-docker-local-runbook.md):
  inventário somente-leitura antes de agir (§3.1), remoção por **lista nominal de
  image ID** sem `prune` (§5.1), retenção por pin e fixture (§5), e nada de mutação
  através de atalho em `registry.json`, `config.json` ou `audit.jsonl`.
- **Método:** `docker image ls/inspect` com labels OCI e `io.percival.*`/`io.positronic.*`
  por imagem; cruzamento com os pins de `~/.positronic/mcp/registry.json` (Positronic) e
  `~/.nanobot/config.json` (Percival); scan Trivy 0.76.1 com o DB local de 2026-10-24
  (`--skip-db-update`), o mesmo DB para todas as imagens, para comparação direta.

## 1. Estado antes e depois

| Recurso | Antes (18:50) | Depois (19:15) | Delta |
|---|---|---|---|
| Imagens (IDs únicos) | 170 (54,67 GB; 45,7 GB recuperáveis) | **39 (13,72 GB)** | −131 imagens, −40,9 GB |
| Containers | 17 (8 em execução) | 16 (14 em execução) | −7 obsoletos, +6 recriados pelo broker |
| Volumes | 21 (2,498 GB; 100 % recuperáveis) | **2 (699,4 MB)** | −19 volumes, −1,80 GB |
| Cache de build | 3.391 registros (226,3 GB) | **0** | −226,3 GB |
| Raiz do host | — | 475 GB; 284 GB em uso; 186 GB livres (61 %) | — |

Nenhuma imagem em uso, nenhum pin de gestor e nenhum volume com link ativo foi
removido. O reclaimed real de disco é o do cache de build (226,3 GB) somado às camadas
deixadas de órfãs (≈ 40 GB); o tamanho virtual das imagens não é todo espaço físico
recuperado porque camadas são compartilhadas.

## 2. Retenção aplicada (o que ficou, e por quê)

| Image ID | Imagem | Motivo da retenção |
|---|---|---|
| `e104ac754951` | agentmail MCP `0.4.0-f7-test-keyfile` | **pin ativo** nos dois gestores + container em execução |
| `ef4082ef1390` | notes MCP `0.1.5-f7-test-vaultpath` | **pin ativo** nos dois gestores + container em execução |
| `265891c14514` | deep-research MCP `3.0.1-9e8272b-f3` | **pin ativo** nos dois gestores + container em execução |
| `67f8ada63989` | osm MCP `0.5.0-311a49d-f3` | **pin ativo** nos dois gestores + container em execução |
| `55cd5a038d22` | khan-calendar MCP `0.4.0-d8d4122-f3` | **pin ativo** nos dois gestores + container em execução |
| `e75fdd4abc8a` | weather MCP `0.9.0-94c7fde-f3` | **pin ativo** nos dois gestores + container em execução |
| `d128e0ca1dee` | gateway ativo (`nanobot-nanobot-gateway:latest`, rev `40d8eb9`) | container em execução (compose) |
| `6ea63b38852c` | broker ativo (`percival-mcp-broker:local`, rev `29a482c`) | container em execução (compose) |
| `e7ce9898c041` / `41c9ec34cb54` | gateway / broker `766d33b` | **candidato atual** (build de 2026-10-27, 0 Critical/High) |
| `553b88fe1829`, `918ab216a6d3`, `07aa40fb1182`, `ec854780d2d4`, `738edcce0bac`, `4cd60d26d8af` | MCPs `iac1-*` | **candidato atual** por servidor (build do source auditado, 0 Critical/High) |
| `2a0e5c342504` / `c6784ebbc29a` | gateway / broker D8-A (rev `3daabe2`) | alvo de rollback do core exigido pelo runbook §5.1 |
| `d06d8eedcc4e` / `c6e370a5d56c` | gateway / broker pré-D11 | snapshot de rollback preservado (runbook §5.1) |
| `ac62466dfd99` | gateway `0.3.5-29a482c-d11-builtin` | retenção explícita do runbook §5.1 (par core D11) |
| `84e4c8f13ca4` | gateway `0.1.0-b49dd8b` | fixture `d6-nopip`: runbook diz "permanece fora de qualquer limpeza" |
| `0a5c16cd68ee` | `positronic:iac-diagnostic-e869d8d18551` | artefato do diagnóstico da Etapa 1 (source `e869d8d1`) |
| `4cee6ff3ebc4`, `2b4f19dae3a7`, `e529028263db`, `b658b05ce9c4`, `5e6baf67325a`, `41eb228142f7`, `cc9311ae7d42`, `eacce4ec0ff8`, `f6bb96a2e3c5` | bases pinadas por digest nos Dockerfiles vigentes | rebuild offline e reprodutibilidade (runbook §5: 2 digests por base) |
| `431b37ce1acf`, `621f24939922` | `oven/bun:1.3.14-{debian,slim}` | bases pinadas do Dockerfile do agente Positronic |
| `790fd66d1697` | `aquasec/trivy:latest` (0.76.1) | ferramenta de scan em uso |
| `4cc92b64ca74` | `anchore/syft:v1.55.0` | ferramenta de SBOM |
| `aa3df78ecf32` | `docker:27.5.1-dind` | harness da receita de privilégios (D-05) e gate Engine 27.x |
| `a3d8aaa63ed8`, `be2656061b53` | `registry:2`, `alpine:3` | registry local (gate de distribuição) e base de fixture |

## 3. O que foi removido (131 imagens por ID, 7 containers, 19 volumes)

| Categoria | Quantidade | Exemplos |
|---|---|---|
| Intermediários F3/F4/F5 | 46 | `percival-*:f3-repeat-*`, `f3-sealed-repeat-*`, `f3-final-repeat-*`, `f3-clean-repeat-*`, `f5-recheck`, `f4-test` |
| Candidatos F3/D8 superados | 8 | `percival-agentmail-mcp:0.4.0-89acdf4`, `percival-notes-mcp:0.1.5-c104735`, `percival-*:0.1.0-f2173bb`, `percival-*:0.5.0-4204213` — substituídos pelos builds `iac1-*`, mais novos e verificados |
| Histórico do core | 12 | `percival-gateway:0.1.0-{b76ade9,ce31e52,92eeff9,6767a75}`, `percival-*:d6-forky`, `forky-probe`, `d6-nopip-build/test`, `0.1.0-50e6ebd`, `0.3.5-29a482c-d11-builtin` (tag duplicada), `percival-i2-*` |
| Fixtures sem dono | 5 | `pinprobe:{full,libs,diag,local}` (1,0 GB; sem labels, sem referência em repo, config ou compose), `percival-remote-ssh-fixture:10.6p1` |
| Alias de diagnóstico | 7 | `percival-agentmail-mcp:dev`, `percival-osm:dev`, `percival-osm:local`, `percival-khan-calendar:dev`, `percival-deep-research:smoke`, `percival-gateway:forky-probe` |
| Builds antigos do agente | 5 | `positronic:dev-{f699f311,27ca3d0f,16d5405b-dirty,b1b3eed5,07c54d5e}` (3,1 GB) |
| Smoke test do Positronic | 1 | `positronic-mcp-local-smoke-f3-0-1:2026-10-20T15-21-35-376Z` |
| Dangling (sem tag) | 9 | camadas órfãs de 2026-10-20 (12 MB cada) |
| Bases/ferramentas não usadas | 12 | `nanobot-nanobot-cli:latest` (1,28 GB), `archlinux` (541 MB), `uv:0.11.32-debian` (1,49 GB), `node:24-bookworm-slim`, `python:3.11-slim`, `python:3.12-alpine3.23`, `alpine:3.20`, `busybox`, `aquasec/trivy:0.67.2` (2025-10), `docker:29.9.0-cli`, `registry` duplicatas |
| Containers | 7 | 6 instâncias `percival-mcp-*` de 2026-10-10 (exited) + `f4probe5bhurh8-s-1` (busybox) |
| Volumes | 19 | `trivy-f3-cache` (1,47 GB, DB de 2026-10-10 expirado), 3 volumes de registry de teste `percival-f1` (315 MB), 14 volumes anônimos vazios, `percival-state`, `percival-osm_percival-cache` |

Correção factual: as 6 instâncias `percival-mcp-*` removidas **não** eram órfãs — eram
instâncias antigas de 2026-10-10; o broker do Percival as recriou automaticamente em
~20 minutos sobre os mesmos image IDs, o que confirma a supervisão do gestor. Nenhuma
referência de pin foi alterada.

## 4. Achado P1 — as imagens em produção carregam 45 a 78 achados Critical/High

Scan Trivy 0.76.1, DB de 2026-10-24, mesmo DB para todas as linhas:

| Imagem | Estado | Critical | High | Com correção disponível |
|---|---|---|---|---|
| agentmail MCP `A` (pin, em uso) | 2026-10-10 | 1 | 44 | 1 |
| notes MCP `A` (pin, em uso) | 2026-10-10 | 1 | 44 | 1 |
| osm MCP `A` (pin, em uso) | 2026-10-10 | 1 | 44 | 1 |
| khan MCP `A` (pin, em uso) | 2026-10-10 | 1 | 44 | 1 |
| weather MCP `A` (pin, em uso) | 2026-10-10 | 1 | 44 | 1 |
| deep-research MCP `A` (pin, em uso) | 2026-10-10 | **7** | **71** | 34 |
| gateway ativo | 2026-10-24 | 0 | 0 | 0 |
| broker ativo | 2026-10-24 | 0 | 0 | 0 |
| MCPs `iac1-*` (candidatos atuais) | 2026-10-27 | **0** | **0** | 0 |
| gateway/broker `766d33b` | 2026-10-27 | 0 | 0 | 0 |
| agente Positronic `iac-diagnostic` | 2026-10-27 | 0 | 93 | 45 |

**Causa raiz (verificada por inspeção de pacotes).** As imagens `A` usam
`debian:forky-slim` pinado em 2026-10-05, com `bsdutils 1:2.41.5-0+deb13u1` e
`libsystemd0 257.13-1~deb13u1`; os CVEs sem correção disponível são exatamente os
`CVE-2026-76642/78408/78409/78410` (bsdutils/libsystemd) que o Debian 13 ainda não
corrigia. Os builds `iac1-*` (2026-10-27) usam a mesma base com a revision atual
(`bsdutils 1:2.42.4-1`, `libsystemd0 262-1`) e resultam em **0 Critical/High** com o
mesmo DB. Ou seja: **a correção já está construída e verificada localmente**; o que
falta é a promoção.

**Por que a promoção não foi executada nesta auditoria.** O runbook §5.1 registra que os
candidatos não são elegíveis para instalação: o CI remoto falha em cinco dos seis
repos e a distribuição (aquisição por catálogo/digest) não está implementada; a
promoção exige `update-image` + `configure` com revisão esperada nos dois gestores,
sendo que o lado Percival exige sessão WebUI autenticada com elevação. Promover sem
essa janela violaria os gates que o próprio operador aprovou. O procedimento está
pronto para execução, com rollback para as imagens `A` (preservadas).

## 5. Achado P2 — a imagem do agente Positronic está com a base defasada

`positronic:iac-diagnostic-e869d8d18551` tem 93 High (45 com correção). Causa: o runtime
é `oven/bun:1.3.14-slim` (Debian 13 com pacotes de 2026-05) e o script de snapshot
instala apenas alguns pacotes — `bsdutils 1:2.41-5` e `libsystemd0 257.9-1~deb13u1`
permanecem nas versões da base. Rem Remedy em duas etapas, ambas de produto:

1. **Barata:** rodar `apt-get upgrade` a partir do snapshot datado de 2026-10-18 dentro
   do stage de runtime (o snapshot já contém as versões corrigidas). Deve remover os 45
   achados com correção.
2. **Estrutural:** migrar o runtime do agente de Debian 13 para `debian:forky-slim`, como
   os MCPs já fazem, com o bun instalado a partir do release oficial. É a única forma de
   chegar a 0/0, mas é mudança de produto com risco de compatibilidade do runtime bun.

Nenhuma das duas etapas foi aplicada: são mudanças no `Dockerfile`/`debian-snapshot.sh`
do `alternative-positronic`, fora do escopo de uma auditoria de store e das decisões
`D-01`..`D-06` (correções de produto foram deslocadas para planos de execução por
checkout).

## 6. Achado P3 — drift documental do estado do core

O runbook §5.1 afirma que o par core ativo é `ac62466dfd99` (gateway) /
`6ea63b38852c` (broker). Em 2026-10-27, o container `nanobot-nanobot-gateway-1` roda
`d128e0ca1dee` (ver `0.1.0`, rev `40d8eb99e5ef`, tags
`nanobot-nanobot-gateway:latest` e `percival-gateway:0.1.0-40d8eb9-d11-2e4d276142d8`),
construído em 2026-10-24 21:38 — depois do snapshot do runbook (17:28). O broker
`6ea63b38852c` continua correto. Correção registrada no runbook (§5.4).

## 7. Achado P4 — tags mutáveis e "latest" enganoso

`nanobot-nanobot-gateway:latest` aponta para uma build de 2026-10-24 e
`percival-agentmail-mcp:dev` / `percival-osm:dev` / `percival-khan-calendar:dev` eram
aliases mutáveis (o runbook §1.2 proíbe tag mutável como identificador de execução).
Os aliases `dev` foram removidos; o `latest` do gateway foi mantido porque é o que o
compose do host resolve, mas ele precisa ser substituído por pin imutável no
plano de distribuição.

## 8. Itens deliberadamente preservados (decisão do operador pendente)

| Item | Motivo | Custo |
|---|---|---|
| volume `positronic-percival-registry` | único artefato do registry local (`repositories/percival`), ligado ao gate de distribuição ainda aberto; apagá-lo é destrutivo e não reconstruível a partir dos repos | 667 MB |
| `docker:27.5.1-dind` + container `d7host-noinit` | harness da receita de privilégios (D-05) e gate de Engine 27.x | 530 MB |
| `percival-gateway:0.1.0-b49dd8b` + container `d6-nopip` | runbook §5.1: "permanece fora de qualquer limpeza" | 1,33 GB |
| pares de rollback do core (`2a0e5c3`/`c6784eb`, `d06d8ee`/`c6e370a`) | reversibilidade exigida pelo runbook | 2,68 GB |

## 9. Verificação pós-limpeza

- `docker ps`: 14 containers em execução — gateway e broker do Percival (healthy) e os
  6 MCPs em cada gestor (Percival e Positronic).
- Pins dos dois gestores relidos: os 12 pins intactos, com as mesmas revisões; as 6
  imagens pinadas presentes no store.
- Smoke pelos MCPs: `khan_get_status` (conf casa com o layout, lock desabilitado),
  `osm_get_health` (ok), `notes_get_status` (vault montado), `weather_get_status`
  (0.9.0 operacional), `agentmail_mail_get_version`.
- `docker system df`: 39 imagens (13,72 GB), 2 volumes (699,4 MB), cache de build 0.

## 10. Decisões pendentes para o operador

1. **Promoção dos 6 MCPs para os builds `iac1-*`** — fecha 45 a 78 Critical/High nos
   dois gestores. Requer: janela aprovada, releasing dos gates de CI/distribuição
   (ou waiver explícito), `update-image` + `configure` com revisão esperada nos dois
   gestores, e a sessão WebUI elevada do Percival. Rollback: images `A` preservados.
2. **Volume do registry** — apagar (667 MB, destrutivo) ou reter até o gate de
   distribuição.
3. **Imagem do agente** — aplicar só a etapa 1 do §5 (upgrade no snapshot) ou planejar
   a migração de base do §5.
