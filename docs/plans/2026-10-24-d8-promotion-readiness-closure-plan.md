# Plano de fechamento D8 — reconciliação de pins e prontidão de promoção

- **Preparado em:** 2026-10-24.
- **Objetivo:** fechar a D8 do [plano de fechamento F4/F5/F7](2026-10-23-fechamento-padronizacao-docker-f4-f5-f7-plan.md) §2.9, removendo os findings corrigíveis dos candidatos Forky, produzindo um conjunto de candidatos com proveniência limpa e verificável, e declarando de forma explícita quais gates dependem de autorização, credencial ou infraestrutura externa do operador.
- **Estado inicial:** D8 **parcial**. Oito candidatos locais construídos de checkouts limpos (seis MCPs + par core), sem Critical/High nos scans; pins críticos anteriores atualizados; Forky/OpenSSL/sem-`pip` verificados no runtime; contrato D7 conforme em cinco MCPs; smokes `initialize`/`tools/list` verdes; scans, SBOMs e OpenVEX por image ID registrados; retenção A/B documentada na §5.1 do [runbook](../operations/mcp-docker-local-runbook.md). Restam findings Python Medium/Low nos MCPs, findings no broker, smoke autenticado do AgentMail, CI remoto não verificado e os gates I3/B13.
- **Referências:** [plano mestre D1–D12](2026-10-23-fechamento-padronizacao-docker-f4-f5-f7-plan.md) §2.9; [relatório F3, reconciliação D8](../reports/2026-10-10-f3-remediation-triage.md) §"Reconciliação D8"; [runbook operacional](../operations/mcp-docker-local-runbook.md) §5.1; [walkthrough D9](../reports/2026-10-24-d9-runbook-walkthrough.md); [plano IaC I1–I9](2026-10-23-iac-alignment-execution-plan.md) §I3/§10; [ADR I1](../Decisions/2026-10-23-open-iac-contracts.md).
- **Autoridade:** este plano orienta trabalho local em repositórios de produto e fixtures descartáveis. Ele **não** autoriza promoção, canário, cutover, publicação em registry, alteração de configuração de qualquer gestor, mutação de pin ativo, rotação de credencial, limpeza de imagens/containers/volumes, deploy em VPS ou preparação de comandos de promoção. Cada uma dessas ações exige autorização específica do operador pela interface suportada. Onde o plano descreve um procedimento de promoção, o texto é um **critério de prontidão**, não uma instrução executável.

## 1. Estado conhecido e gaps remanescentes

Oito candidatos locais foram construídos com `scripts/percival-docker-build.py` a partir
de checkouts limpos, com SHA integral no label `revision` e `linux/amd64`. Nenhum foi
promovido, publicado ou conectado a gestor vivo. O inventário vigente:

| Candidato | Revisão | Image ID | C/H/M/L/U |
| --- | --- | --- | ---: |
| Notes `0.1.5-713e95e` | `713e95ef147abdc07b7efa388fd7cb08c1ce84dd` | `sha256:1bc3417de299f23d3408e68cabab87808a980e467e327965a7e3c9916a640f64` | 0/0/1/1/0 |
| AgentMail `0.4.0-6c71497` | `6c71497fa2a028d34e408dab1cf97bc0fe5d78c4` | `sha256:b8ed6f58fe6ae1c64f98ee6ebe3dd5cbaa70f043d79278eeb89f48b83273208b` | 0/0/1/0/0 |
| Weather `0.9.0-89993a4` | `89993a4f31ef7c7f423f9e046117dc9b50eb3d2c` | `sha256:e3537f2d2983f227547ae8d5af194d560550d3ab677cc6ae641f0e83bb0916a4` | 0/0/1/1/0 |
| Khan Calendar `0.4.0-2d75c05` | `2d75c0547c66b4925427ab6920d889c0d8ffce02` | `sha256:020200378c995ddfb086315331ad07818d888cf69859869e6e60d8f44588700b` | 0/0/3/0/0 |
| OSM `0.5.0-bf78fa4` | `bf78fa4f4cf906cfad4c18efbd6f487a630510a0` | `sha256:286fdfeb8327cdbec597c7089eb6e58e59b0b68148c3f48a3a9404daff989369` | 0/0/2/1/0 |
| Deep Research `3.0.1-61ae512` | `61ae51274a10468a6c0edb25978afcb8d32e01be` | `sha256:af9c6fa288630a37e116ecd07f9dd3671a6f97a14553f438b5c0d0c44a453003` | 0/0/5/1/0 |
| Gateway `0.1.0-3daabe2` | `3daabe20f4c6a7b5f26f2158b97dc2591905507` | `sha256:2a0e5c34250459bcc1861c3cd291333944f7b7451f65f3dbead0c562cb0ada9f` | 0/0/1/0/0 |
| MCP broker `0.1.0-3daabe2` | `3daabe20f4c6a7b5f26f2158b97dc2591905507` | `sha256:c6784ebbc29a41c6591dfeec52528dbd19fb44be18591eadf4db8803141ccf2d` | 0/0/1/0/2 |

### 1.1 Gap G1 — findings Python nos seis MCPs (13 Medium, 4 Low)

Todos os findings residuais estão em `python-pkg`; os pacotes Debian Forky não têm
vulnerabilidades no resultado do scanner. Os upgrades são **todos** disponíveis em
versões compatíveis, e o mecanismo de resolução é o lock `uv.lock` de cada repo:

| Serviço | Pacote instalado | Versão corrigida | Observação de compatibilidade |
| --- | --- | --- | --- |
| Notes | `python-dotenv 1.1.1` / `Pygments 2.19.2` | `1.2.2` / `2.20.0` | Transitivos de `mcp[cli]`/`pydantic-settings`; sem pin direto no `pyproject.toml`. |
| AgentMail | `mcp 1.28.1` | `1.30.0` | O `pyproject.toml` permite `>=1.28.1,<2.0.0`; o lock está atrás do piso. |
| Weather | `python-dotenv 1.1.1` / `Pygments 2.19.1` | `1.2.2` / `2.20.0` | `python-dotenv` é dependência direta (`>=1.1.1`); `Pygments` é transitivo. |
| Khan Calendar | `fastmcp 3.4.4` / `fastmcp-slim 3.4.4` / `opentelemetry-api 1.44.0` | `3.4.10` / `1.45.1` | `fastmcp>=3.2.0` já admite a linha corrigida; `opentelemetry-api` é transitivo. |
| OSM | `python-dotenv 1.0.1` / `Pygments 2.19.1` / `pydantic-settings 2.13.1` | `1.2.2` / `2.20.0` / `2.14.2` | `pydantic-settings>=2.10.1` admite a correção. |
| Deep Research | `fastmcp 3.4.4` / `fastmcp-slim 3.4.4` / `litellm 1.93.0` / `multidict 6.7.1` / `opentelemetry-api 1.44.0` / `setuptools 83.0.0` | `3.4.10` / `1.93.2` / `6.9.1` / `1.45.1` / `84.1.0` | `setuptools` chega por `spacy`; `litellm` é transitivo de `gpt-researcher`. O override `filelock==4.2.1` já aprovado precisa ser preservado. |

Os oito OpenVEX D8 (`docs/reports/2026-10-24-d8-openvex-*.json`) são **rascunhos
técnicos**, limitados a um único image ID por documento, e hoje marcam esses findings
como `affected` ou `under_investigation`. Eles não são waivers e não constituem aceite
do operador. Um rebuild com pins corrigidos invalida o image ID de referência: os
documentos precisam ser reemitidos para os novos IDs, e os antigos não podem ser
reatribuídos.

### 1.2 Gap G2 — findings do par core

- **Gateway:** um Medium `CVE-2026-49138` do metadado `nanobot-ai 0.1.0`, com avaliação
  `not_affected` restrita ao image ID `sha256:2a0e5c34…`. Não é bloqueante por severidade,
  mas é um assessment que precisa ser reemitido junto com o novo candidato.
- **Broker:** `zlib 1.3.2-r0` Medium (`CVE-2026-85091`, fix `1.3.2-r1`) marcado
  `affected`, e `musl`/`musl-utils 1.2.5-r23` com severidade `UNKNOWN`
  (`CVE-2026-107891`, fix `1.2.5-r24`) marcados `under_investigation`. A origem é a base
  `python:3.12-alpine3.23` do runtime do broker, não o Docker CLI.

**Fato verificado nesta revisão:** a base Alpine já usada no estágio `docker-cli`
(`docker:29.9.2-cli-alpine3.24`) contém `musl-1.2.6-r3`, `musl-utils-1.2.6-r3` e
`zlib-1.3.2-r1` — versões **acima** das versões corrigidas exigidas
(`musl 1.2.5-r24` e `zlib 1.3.2-r1`). O `zlib` corrigido e o `musl` acima do piso já
existem em tag disponível; o path de remediação é mover o runtime do broker para uma
base Alpine 3.24 equivalente, o que remove simultaneamente o `zlib` afetado e o `UNKNOWN`
de `musl`. Isso é uma decisão de base de imagem, não um patch de pacote solto, e precisa
ser validada contra o comportamento do CLI Docker copiado em `/usr/bin/docker`.

### 1.3 Gap G3 — smoke autenticado do AgentMail

O AgentMail não tem homologação por runtime/protocolo. `initialize`/`tools/list`
falham sem `AGENTMAIL_API_KEY` e `AGENTMAIL_INBOX_ID` válidos, porque o servidor não
inicia a sessão MCP sem credencial e upstream alcançável. As falhas observadas pelo
harness são **falhas de pré-condição**, não evidência de defeito funcional. Nenhum
segredo foi lido, inventado ou registrado. O critério exige credencial **aprovada pelo
operador** e upstream acessível; o agente não pode fabricar esse pré-requisito.

### 1.4 Gap G4 — CI remoto dos SHAs publicados

`gh auth status` não encontrou sessão autenticada, e `GH_TOKEN` não está disponível no
ambiente. As Actions dos seis SHAs MCP (`713e95e`, `6c71497`, `89993a4`, `2d75c05`,
`bf78fa4`, `61ae512`) e do core (`3daabe20…`) não puderam ser confirmadas. Os workflows
existem nos seis repos MCP (`ci.yml`, `docker.yml` no OSM) e no core (`ci.yml`), mas
sucesso local não substitui o gate remoto, conforme o critério do próprio plano mestre.

### 1.5 Gap G5 — gates de distribuição (I3/B13) e de promoção

I3 foi adiado por decisão do operador. Não existe catálogo de digest, nem caminho de
aquisição por digest, nem registro OCI: os image IDs locais **não são** digests OCI
publicados. B13 (aprovação de publicação) e o aceite público homolgado são atos
distintos, na ordem I1.6. Sem esses gates, o candidato B não é elegível para instalação
mesmo que todos os findings locais sejam corrigidos.

### 1.6 Gap G6 — estado do core no repositório

O texto do plano mestre §2.9 e do relatório F3 afirma que "o core permanece sem push".
Isso era verdade na redação original, mas o core foi enviado em `297d4295` (com
`ce31e526` e `3daabe20` precedendo). A afirmação precisa ser reconciliada com o estado
real do repositório, sem alterar o fato de que **nenhuma imagem foi publicada**.

## 2. Escopo e fronteiras

Incluído: atualização de pins nos seis MCPs; decisão e aplicação de base para o runtime
do broker; rebuild limpo dos candidatos afetados; rescan Trivy e SBOM CycloneDX por
image ID; reemissão dos OpenVEX; reexecução do contrato D7 e dos smokes stdio; execução
do smoke autenticado do AgentMail **se** o operador fornecer a credencial; verificação do
CI remoto **se** houver sessão GitHub; reconciliação documental; reemissão do snapshot de
retenção.

Fora do escopo: promoção, canário, cutover e publicação; alteração de pin, revisão,
CAS ou `configurationId` de qualquer servidor nos dois gestores; alteração de
`allowTools`, allowlist ou credencial; mudança de runtime do gestor; `docker prune` ou
qualquer limpeza; deploy em VPS; preparação de comandos de promoção; fechamento de
D11, D12, I3, I9, C1–C4 ou A1–A9; assinatura de waivers.

## 3. Plano de execução

### Fase A — Reconciliar pins Python nos seis MCPs

1. Em cada repo, trabalhar em branch própria a partir de `main` sincronizado com
   `origin/main`, confirmando `git status --short` vazio antes de qualquer alteração.
2. Re-resolver o lock apenas para os pacotes nominalmente corrigidos, preservando
   todas as demais versões. O padrão já provado na D6 é o re-resolve **explícito** do
   pacote, porque o resolvedor preserva pins já fixados e um re-resolve cego reintroduz
   versões vulneráveis:
   `uv lock --upgrade-package <pacote>` por pacote listado na §1.1.
3. **Preservar o override aprovado** do Deep Research (`[tool.uv] override-dependencies`
   com `filelock==4.2.1`). Se o re-resolve o tensionar, parar e registrar: o override
   foi decisão explícita do operador e não é renegociável dentro desta execução.
4. Atualizar a dependência direta quando a correção está declarada em
   `pyproject.toml` (`python-dotenv` em Weather, `pydantic-settings` em OSM), para que o
   piso declarado não permaneça abaixo do corrigido.
5. Rodar a suíte de cada repo (`uv run pytest -q`) e o conformance de imagem
   (`scripts/docker-ci-conformance.py`) no checkout. Registrar contagem de testes e
   qualquer skip com justificativa.
6. Verificar no lock resolvido, para cada serviço, que a versão de cada pacote da
   §1.1 é **igual ou superior** à versão corrigida. Uma versão superior é aceitável
   desde que o teste do repo passe; uma inferior bloqueia a fase.
7. Commit por repo com mensagem indicando serviço e pacotes; push para `main` somente
   com a autorização aplicável.

**Saída:** seis commits de lock com pins corrigidos, contagens de teste por repo e
tabela verificável `pacote → versão` conferida contra a §1.1.

### Fase B — Base do runtime do broker (zlib/musl)

1. Tratar a decisão como **troca de base do runtime**, não como patch de pacote.
   Alvo: base Alpine equivalente à 3.24 já em uso no estágio `docker-cli`, com digest
   pinado, preservando `python:3.12-alpine*`, o usuário não-root `65532:65532`, o
   `STOPSIGNAL SIGTERM` e o entrypoint `python3 -m nanobot.mcp_docker.broker`.
2. Verificar, antes do rebuild, que a base candidata contém `zlib >= 1.3.2-r1` e
   `musl >= 1.2.5-r24` (verificado: `docker:29.9.2-cli-alpine3.24` traz `zlib-1.3.2-r1`
   e `musl-1.2.6-r3`). Registrar os números de versão observados.
3. Preservar a cópia do binário `docker` a partir do estágio `docker-cli` e a remoção de
   `pip`/`ensurepip` do venv do broker — o gateway e o broker já são candidatos limpos.
4. Rebuild do broker e smoke D-in-D do par core (`scripts/percival-i2-runtime-smoke.py`
   em Engine 27.5.1 descartável), exigindo 18/18 checks PASS e o comportamento de
   `docker ps`/spawn idêntico ao candidato anterior.
5. Se a troca de base introduzir regressão funcional do CLI Docker ou do broker,
   **parar**. Registrar a regressão como defeito separado em vez de reintroduzir
   `zlib 1.3.2-r0` com um assessment `not_affected` sem base técnica.

**Saída:** broker reconstruído com `zlib`/`musl` corrigidos, smoke do par core verde e
avaliação de `CVE-2026-107891` resolvida como `fixed` para o novo image ID.

### Fase C — Rebuild limpo, rescan e reemissão de avaliações

1. Rebuild dos candidatos afetados a partir de checkouts **limpos** (sem
   `--worktree-candidate`), com `scripts/percival-docker-build.py`. O script recusa
   versões placeholder e registra SHA integral; tags de candidato existentes não são
   sobrescritas.
2. Para cada image ID novo: Trivy 0.67.2 (`aquasec/trivy@sha256:ac2f9d…`) com DB
   atualizado e registro do `UpdatedAt`/`DownloadedAt`; SBOM CycloneDX com Syft 1.55.0;
   SHA-256 do JSON de scan e do SBOM.
3. Atualizar a tabela de candidatos do relatório F3 e do plano mestre §2.9 com os novos
   image IDs e contagens. **Substituir**, não acumular: os IDs antigos ficam
   explicitamente marcados como superados, com a referência ao scan que os originou.
4. Reemitir os OpenVEX por imagem com o novo image ID e `status` coerente com o
   resultado do scan. Findings corrigidos que reaparecerem em outro pacote continuam
   `affected`. Documento com produto único; sem mistura de image IDs.
5. Reexecutar o contrato D7 (`scripts/percival-mcp-runtime-contract.py`) por MCP
   candidato, quatro medições por imagem (dois gestores × EOF/SIGTERM), exigindo
   init único, EOF com exit 0, SIGTERM com exit 143, zero portas publicadas, zero
   sockets em escuta, `CapEff=0` e ausência de healthcheck HTTP.
6. Reexecutar os smokes stdio `initialize` + `tools/list` e conferir o número de tools
   contra a linha de base da D8: Notes 12, AgentMail 24, Weather 9, Khan 12, OSM 37,
   Deep Research 5. **Divergência no número de tools é sinal de regressão funcional**,
   não um detalhe de versão.

**Saída:** novos candidatos com provenance limpa, scans/SBOMs por image ID, OpenVEX
reemitidos e contrato D7 + smokes verdes.

### Fase D — Homologação autenticada do AgentMail

1. Condição de entrada: credencial **aprovada pelo operador** (`AGENTMAIL_API_KEY` +
   `AGENTMAIL_INBOX_ID`) e upstream alcançável. Sem isso, registrar
   `BLOQUEADO POR PRÉ-CONDIÇÃO`, com o requisito exato nomeado.
2. Executar o smoke contra o candidato novo, não contra imagem antiga: `initialize`,
   `tools/list` (24 tools) e uma chamada de leitura segura de caixa de entrada.
3. Verificar que a falha ou o sucesso não dependem de rede do host e que nenhum valor de
   credencial aparece em log, relatório ou JSON de resultado. Usar redaction.
4. Se a credencial não puder ser fornecida, o item permanece **não executado** — nunca
   `PASS` por ausência de falha observável, e nunca por simulação de upstream.

**Saída:** resultado `initialize`/`tools/list`/chamada segura no candidato final, ou
bloqueio explícito com o pré-requisito nomeado.

### Fase E — Verificação do CI remoto

1. Condição de entrada: sessão GitHub autenticada (`gh auth login` ou `GH_TOKEN` com
   escopo de leitura de Actions). Sem isso, registrar `BLOQUEADO POR PRÉ-CONDIÇÃO`.
2. Para cada SHA candidato, registrar a URL do run, `headSha`, jobs e conclusão. O
   `headSha` precisa ser **igual** ao SHA do candidato; run de outro commit não prova o
   candidato.
3. Distinguir falha de CI de falha do candidato. Um workflow vermelho exige
   investigation antes de qualquer reavaliação de severidade.

**Saída:** tabela `repo → SHA → run URL → conclusão` para os sete SHAs candidatos, ou
bloqueio explícito.

### Fase F — Prontidão de promoção, retenção e reconciliação documental

1. Atualizar a §5.1 do runbook com o snapshot vigente: pins A (inalterados), image IDs
   B novos, revisões/CAS e `configurationId`s dos dois gestores, e a marcação do que
   permanece fixture fora de qualquer limpeza (`d6-nopip`). Reler o estado vivo antes de
   registrar; **não** alterar pin, revisão ou configuração.
2. Declarar, por gate, a condição objetiva de prontidão:
   - **B1 — imagem:** build limpo, SHA/labels coerentes, 0 Critical/0 High, Medium/Low
     corrigidos ou avaliados com justificativa técnica por image ID.
   - **B2 — runtime:** contrato D7 e smokes verdes no image ID final de cada serviço.
   - **B3 — rollback:** par A/B retido e verificável, com o caminho de retorno ao image
     ID A reidratado por gestor.
   - **B4 — retenção:** snapshot aprovado; A e B preservados sem prune.
   - **B5 — CI:** Actions remotas verdes nos SHAs candidatos.
   - **B6 — distribuição:** digest OCI publicado, aquisição homologada e B13 aprovado —
     **fora do alcance local; depende de I3/I5 e de autorização do operador.**
3. Registrar explicitamente que o **snapshots de retenção não é autorização**: promoção,
   canário e cutover continuam bloqueados até B5/B6 e até decisão do operador.
4. Reconciliar os documentos de estado (§1.6): o texto do plano mestre §2.9 e do
   relatório F3 passa a refletir que o core foi enviado, mantendo explícito que nenhuma
   imagem foi publicada nem promovida.
5. Atualizar a linha D8 do plano mestre com o estado final, os commits, os image IDs,
   a evidência e o que permanece bloqueado; atualizar §2.9 com o registro de execução.

**Saída:** documentação consistente, snapshot de retenção vigente e matriz B1–B6 com o
estado real de cada gate.

## 4. Critérios de aceite

| Gate | Aceite verificável |
| --- | --- |
| C1 — Pins | Para cada serviço, a versão no lock de cada pacote da §1.1 é ≥ à versão corrigida; override `filelock==4.2.1` preservado. |
| C2 — Testes | Suíte de cada repo MCP verde no commit candidato, com contagem registrada e skips justificados. |
| C3 — Build | Candidato construído de checkout limpo, `linux/amd64`, SHA integral no label `revision`, sem diff de worktree na identidade. |
| C4 — Scan | Trivy sobre o image ID final: 0 Critical, 0 High; Medium/Low corrigidos ou com avaliação por image ID. |
| C5 — SBOM | CycloneDX por image ID com SHA-256 do artefato bruto registrado. |
| C6 — OpenVEX | Um documento por image ID, produto único, `status` coerente com o scan; drafts, não waivers. |
| C7 — Contrato D7 | Quatro medições por imagem conforme: init único, EOF 0, SIGTERM 143, sem porta/TTY/healthcheck. |
| C8 — Smoke | `initialize` + `tools/list` com o número de tools da linha de base por serviço. |
| C9 — AgentMail | Smoke autenticado no candidato final, ou bloqueio explícito nomeando o pré-requisito ausente. |
| C10 — CI | URL, `headSha` e conclusão para os sete SHAs candidatos, ou bloqueio explícito. |
| C11 — Core | Broker sem `zlib` afetado e sem `UNKNOWN` de `musl`; smoke do par core verde. |
| C12 — Retenção | Snapshot A/B vigente e reidratável; pins A intactos nos dois gestores; nenhum prune. |
| C13 — Não mutação | Nenhuma configuração, pin, revisão, allowlist, credencial, container de produto, volume ou registry alterado. |
| C14 — Documentação | Plano mestre §2.9, linha D8, relatório F3 e runbook §5.1 refletem o estado real, inclusive o push do core. |
| C15 — Autoridade | Nenhum comando de promoção entregue; nenhuma promoção, canário, cutover ou publicação executada. |

## 5. Riscos, paradas e rollback

- **Regressão funcional por upgrade de pin.** `fastmcp`, `litellm` e `mcp` são
  dependências centrais de superfície de tools. Se o número de tools divergir da linha de
  base, ou se a suíte do repo falhar, **parar** e reportar. Não aceitar o finding
  corrigido em troca de comportamento alterado sem registro explícito do operador.
- **Re-resolve que reintroduz pins vulneráveis.** O resolvedor preserva versões já
  fixadas; um `uv lock` genérico pode reintroduzir `pillow`/`certifi` antigos. Conferir
  os pins críticos já validados (`certifi==2026.10.23` nos seis, e `pillow==13.0.0`,
  `brotli==1.2.1`, `pypdf==6.21.2`, `filelock==4.2.1` no Deep Research) após cada
  re-resolve.
- **Tensão com o override `filelock==4.2.1`.** Decisão do operador; não negociar.
- **Troca de base do broker.** Se Alpine 3.24 no runtime do broker alterar o
  comportamento do CLI Docker copiado ou do broker, parar e abrir defeito separado.
- **Falso verde por pré-condição ausente.** AgentMail sem credencial e CI sem sessão
  GitHub são **não executados**, nunca PASS. Falha de pré-condição não é defeito do
  candidato, e ausência de falha não é aprovação.
- **Confundir tag local, image ID e digest OCI.** Os três são identidades distintas.
  Nenhum relatório deste plano pode afirmar digest publicado.
- **Perda de proveniência.** Scans e SBOMs brutos ficam fora do Git, referenciados por
  SHA-256; o repositório guarda o resumo redigido.
- **Promoção implícita.** Não preparar nem executar comandos de promoção. Se o
  operador quiser promover, isso é um pedido novo, com seus próprios gates.
- **Rollback do trabalho.** Cada commit de pin é revertível isoladamente por repo. O
  rollback de runtime de imagem é o par A retido; nenhuma imagem promotora existe
  para desfazer.
- Sem `docker image prune -a`, `docker system prune` ou remoção por nome/tag/idade.
  Qualquer limpeza é lista nominal aprovada item a item.

## 6. Dependências e ordem

```
Fase A (pins) ──┐
Fase B (broker) ─┴─→ Fase C (rebuild/scan/OpenVEX) ─→ Fase D (AgentMail) ─┐
                                     │                                    ├─→ Fase F (retenção + docs)
                                     └────── Fase E (CI remoto) ─────────┘
```

Fases A e B são independentes entre si e podem correr em paralelo. A Fase C exige A
(pelo menos para os MCPs afetados) e B (para o broker). As fases D e E dependem de
pré-requisitos externos do operador e podem ficar bloqueadas sem impedir o fechamento
documental — desde que o bloqueio fique registrado como **não executado**, com o
requisito nomeado. A Fase F é a única que fecha a D8, e apenas com C1–C15 em estado
verificável.

A D8 é independente de D11, D12, I3/I9, C1–C4 e A1–A9. Fechar a D8 não fecha nenhum
deles, e o encerramento consolidado continua dependente dos gates externos.
