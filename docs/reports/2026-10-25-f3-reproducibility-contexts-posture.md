# F3 — Reprodutibilidade, contextos e postura base (execução 2026-10-25)

- **Escopo:** gate F3 do [plano de padronização Docker](../plans/2026-10-09-docker-standardization-refactor-plan.md)
  para o core Percival (gateway + broker) e os seis MCPs, em `linux/amd64`.
- **Autoridade:** execução local. Nenhuma imagem foi publicada, promovida, removida
  ou instalada; nenhum pin, revisão, allowlist, credencial ou container de produto
  foi alterado. Push das fontes depende de autorização do operador.
- **Evidência bruta:** `/home/bill/.positronic/runtime/tmp/opencode/f3-20261024/`
  (scans JSON, SBOMs CycloneDX, contexts exportados, logs de build, resultados de
  smoke e de runtime). Os artefatos brutos ficam fora do repositório; aqui entram
  apenas o resumo e os hashes.

## 1. Resultado

| Critério do gate F3 | Estado | Evidência |
| --- | --- | --- |
| Mesmo source+lock+base → mesmo conjunto resolvido | **atendido (nível: conjunto resolvido)** | §4 |
| Build limpo (checkout commitado, sem diff de worktree) | **atendido** | §3 |
| Contexto sem estado local/segredos | **atendido** | §5 |
| SBOM e scan por candidato, com scanner/DB registrados | **atendido** | §6 |
| Exceções com owner e expiração | **atendido (1 avaliação; nenhum waiver)** | §6 |
| Build clean em builder de CI | **não executado** | §8 |

O gate F3 fica **concluído no escopo local**. O nível de repetibilidade
comprovado é a igualdade do **conjunto resolvido** (pacotes Python e de sistema,
com versões), não a igualdade bit a bit da imagem: rebuilds com `--no-cache`
produzem image IDs diferentes, como esperado em timestamps, ordem de camadas e
metadados de build.

## 2. Candidatos limpos

Construídos por `scripts/percival-docker-build.py` a partir de checkouts
**commitados e limpos**, sem `--worktree-candidate`. Cada imagem carrega a
revisão completa no label `org.opencontainers.image.revision`.

| Serviço | Tag | Revisão | Image ID |
| --- | --- | --- | --- |
| Gateway | `percival-gateway:0.1.0-f2173bb` | `f2173bbe3f9c887f2db118e35fc792485c2681dd` | `sha256:72195df6c5818e0b22d2bb5f5dcc349f38c70b787a5ed8db1935c39d88d32ee3` |
| MCP broker | `percival-mcp-broker:0.1.0-f2173bb` | `f2173bbe3f9c887f2db118e35fc792485c2681dd` | `sha256:a3c469a0b6e5799ab322fea5ba7f3782b73e177d6dfbec3aadeab0f2ee1a4685` |
| Notes MCP | `percival-notes-mcp:0.1.5-c104735` (candidato D8, **reaproveitado**) | `c1047355bce2512cc50ca89c0c8af0b82837909a` | `sha256:3abd363f5a354a293b7c5ef5bf58a30cfd245800814f6b800c4545fba994822a` |
| AgentMail MCP | `percival-agentmail-mcp:0.4.0-89acdf4` | `89acdf4653681f14f5466185fce8f0dcb9f85908` | `sha256:114f938fdcfca2832f661484a70b1fa24c37f783ea09c0d23af1de45d56d159c` |
| Weather MCP | `percival-weather-mcp:0.9.0-9583059` | `958305997ff11606586316c0ac0537c7aa48d5b6` | `sha256:7e3c03db89a649afc82f3da156710c154abd29143dace6bde0ba9f07cf53a69f` |
| Khan Calendar | `percival-khan-calendar:0.4.0-4f4521a` | `4f4521a177153c0258d596c69fcfbf4f5cf70a7e` | `sha256:620dbbc4b04d9e131c85e692fd1a6d44ee2a222977b0c65b53449abf33cca4c0` |
| OSM | `percival-osm:0.5.0-4204213` | `4204213449a3c5905c853c9c8815a109aaa7ff3b` | `sha256:6d0e8e5f4aad13b4a98eb7f50cfeef32463f18b777b5c44dae325c045e0a2ab6` |
| Deep Research | `percival-deep-research:3.0.1-dd6451e` | `dd6451ecb213c0e64fffe9ef690287542e934b66` | `sha256:7d015e3359363df00db47f9b8678fb76d601f64fb471314a163a36f5a1e75e07` |

O Notes MCP não foi reconstruído: o repositório não mudou nesta rodada (o
`.dockerignore` dele já era allowlist explícita) e a tag imutável do candidato
limpo da D8 já existe localmente. O candidato foi **reescaneado** com a base de
vulnerabilidades atualizada (§6) e o contexto foi reauditado (§5).

Tag local, image ID e digest OCI são identidades distintas: **nenhum digest
publicado existe** para estes artefatos.

## 3. Mudanças de fonte desta rodada

- **Core** (`bill-kopp-ai-dev/nanobot`): `d4cd28a2` (build) e `f2173bbe` (docs).
  - `scripts/install_channel_dependencies.py`: novo caminho `--locked` usado pelo
    build. Ele valida o manifesto de channel-locks, instala a união dos locks com
    `--require-hashes --no-deps` e **falha** em pins conflitantes. O instalador
    nativo por manifestos permanece para desenvolvimento.
  - `Dockerfile`: canais instalados em build time a partir da lista
    `NANOBOT_CHANNELS`, seguido de `uv pip check`; `ENV NANOBOT_RUNTIME_PACKAGE_INSTALL=0`.
  - `nanobot/optional_features.py`: política de imagem imutável. Sem
    `NANOBOT_RUNTIME_PACKAGE_INSTALL=0` o comportamento nativo é preservado
    (variável ausente = `1`).
  - `scripts/check_docker_context.py`: auditoria de contexto efetivo (§5).
  - `scripts/percival-docker-build.py`: manifest passa a registrar o hash de
    **todos** os channel-locks, não apenas do WhatsApp.
  - `.github/workflows/ci.yml`: passo de auditoria de contexto, verificação
    offline de dependências imutáveis e manifest com `webui/package-lock.json`.
  - `docs/agent-runtime-contract.md` e `docs/deployment.md`: contrato atualizado.
- **MCPs**: allowlist explícita de contexto em AgentMail, Weather, Khan, OSM e
  Deep Research (`89acdf4`, `9583059`, `4f4521a`, `4204213`, `dd6451e`); Khan e
  OSM passaram a embarcar `LICENSE`.

### 3.1 Dependências de canal congeladas no build

O gateway instalava os canais a partir dos **manifests** (faixas de versão), de
modo que um range já satisfeito podia ser resolvido fora dos pins revisados. O
build passa a instalar os **locks** (`--require-hashes --no-deps`) e a falhar em
conflito. Em runtime, `NANOBOT_RUNTIME_PACKAGE_INSTALL=0` faz o startup reportar
dependência ausente sem instalar e a WebUI devolver 409 **antes** de alterar
configuração; canais já pré-instalados continuam habilitáveis. A política é de
aplicação, não de isolamento: o UID 1000 continua sendo dono do venv, e
instalar fora do build invalida a afirmação de conjunto fixo.

Provas: `tests/channels/test_channel_plugins.py` ganhou quatro regressões
(instalação recusada em imagem imutável; canal pré-instalado segue habilitável;
instalador de build usa pins mesmo com range satisfeito; lock adulterado nunca
chega ao instalador).

## 4. Repetibilidade do conjunto resolvido

Para cada candidato, um segundo build `--no-cache` foi feito a partir do mesmo
conteúdo commitado, em diretório isolado, e os conjuntos instalados foram
comparados dentro do runtime:

| Serviço | Pacotes Python | Pacotes de sistema | Conjunto idêntico |
| --- | ---: | ---: | --- |
| Gateway | 104 | 126 | sim |
| MCP broker | 5 | 38 | sim |
| AgentMail MCP | 41 | 104 | sim |
| Weather MCP | 40 | 104 | sim |
| Khan Calendar | 84 | 104 | sim |
| OSM | 41 | 104 | sim |
| Deep Research | 215 | 104 | sim |

Os hashes do conjunto resolvido estão em `clean-repeat-results.json`. O Notes
MCP não foi repetido: seu candidato é o da D8, já auditado na rodada anterior.

O que **não** é provado: igualdade bit a bit da imagem, determinismo de
timestamps/metadados de build, nem resolução offline (o build ainda consulta
PyPI, npm e o snapshot Debian; as bases são pinadas por digest, os locks por
hash).

## 5. Contextos de build

`scripts/check_docker_context.py` exporta o contexto efetivo com BuildKit
(`COPY . /context/` para `scratch`) a partir do checkout commitado, sem copiar
estado real do operador: os canários são arquivos sintéticos criados no
diretório temporário. Foram 19 canários por repositório — `.env*`,
`.positronic/`, `.venv/`, `secrets/`, `AGENTS.md`, `__pycache__/`,
`.pytest_cache/`, `node_modules/`, `reports/`, `logs/`, `tests/` — em diretório
raiz e aninhado.

| Repositório | Antes (bytes / canários vazados) | Depois (bytes / canários vazados) | Orçamento |
| --- | --- | --- | --- |
| Core | 23.956.554 / 9 | 22.003.812 / **0** | 40 MiB |
| Notes MCP | 233.260 / 0 | 233.260 / **0** | 512 KiB |
| AgentMail MCP | 375.420 / 11 | 329.184 / **0** | 1 MiB |
| Weather MCP | 562.422 / 10 | 514.068 / **0** | 1 MiB |
| Khan Calendar | 511.074 / 10 | 473.143 / **0** | 1 MiB |
| OSM | 445.732 / 10 | 402.196 / **0** | 1 MiB |
| Deep Research | 1.642.181 / 11 | 1.403.443 / **0** | 2 MiB |

A métrica é **bytes de arquivo exportados**, não bytes incrementais de
transferência do BuildKit; a transferência observada nos builds foi de 22,03 MB
(core), 793 B–2,26 kB (MCPs) e 11,68 kB (broker). O core caiu ~8% porque o
`.dockerignore` passou a ser allowlist; os MCPs, 5–15%.

## 6. Postura de segurança

Scanner: Trivy 0.67.2 por imagem pinada
(`aquasec/trivy@sha256:ac2f9d0197456a8ce460884b113e49d65b667f506c31d014c9955869a7a5d682`),
scanner `--offline-scan` sobre o archive da imagem, DB com
`UpdatedAt 2026-10-25T01:20:33Z` (`DownloadedAt 2026-10-25T02:11:45Z`). O
vínculo entre o image ID e o scan foi conferido pelo digest da config do
archive: `scanImageId` = `sha256(config)`.

| Candidato | C/H/M/L/U | Componentes no SBOM |
| --- | --- | ---: |
| Gateway | 0/0/**1**/0/0 (`CVE-2026-49138`) | 240 |
| MCP broker | 0/0/0/0/0 | 46 |
| Notes MCP | 0/0/0/0/0 | 144 |
| AgentMail MCP | 0/0/0/0/0 | 146 |
| Weather MCP | 0/0/0/0/0 | 145 |
| Khan Calendar | 0/0/0/0/0 | 189 |
| OSM | 0/0/0/0/0 | 146 |
| Deep Research | 0/0/0/0/0 | 340 |

**Critical/High: zero nos oito candidatos.** Nenhum waiver foi concedido, e
nenhum é necessário para estes image IDs.

O único finding remanescente é o Medium `CVE-2026-49138` do gateway, atribuído
ao metadata de `nanobot-ai 0.1.0`. A avaliação `not_affected`
(`vulnerable_code_not_present`) foi **reancorada** neste candidato: os hashes de
`nanobot/agent/tools/web.py` e `nanobot/security/network.py` dentro da imagem são
idênticos aos do candidato da D8, e o commit de correção `545294c` é ancestral
da revisão `f2173bbe`. Documento:
[`OpenVEX do gateway (F3)`](2026-10-25-f3-openvex-gateway.json). É rascunho
técnico por image ID, não é waiver nem aprovação do operador.

SBOMs CycloneDX 1.6 por image ID, com SHA-256 do artefato bruto em
`clean-<serviço>-posture.json`.

## 7. Runtime dos candidatos

- **Core:** rehearsal I2 em daemon descartável (Server 27.5.1) — **18/18 PASS**
  para o par `0.1.0-f2173bb` (`i2-kydui4s8/results.json`): bind único de estado,
  init único, capabilities zeradas, SIGTERM 0 no gateway e 143 no broker,
  recreate do par, auth do bootstrap e da API, UID alternativo 1001 e
  recuperação de crash/hydrate.
- **Gateway offline:** `docker run --network none` com UID 1000 e UID 1001 — os 20
  pins do channel-lock do WhatsApp conferem com as versões instaladas, `neonize`
  e `segno` importam, e a instalação em runtime é recusada com orientação de
  rebuild.
- **MCPs:** conformidade stdio offline pelo próprio harness de cada repo —
  AgentMail 24 tools (com mock local), Weather 9, Khan 12 + `tools/call`
  `khan_get_status`, Notes 12, OSM 37 e Deep Research 5 (fixtures F1, sem API
  externa real).
- Nenhuma chamada a serviço real, nenhuma credencial real e nenhum container de
  produto foram usados.

## 8. Fora do escopo e pendências

- **CI remoto (B5/C1):** os workflows de GitHub Actions não rodaram neste SHA;
  o fork continua sem runs para o core. `build clean em builder de CI` fica
  **não executado**.
- **Distribuição (B6/I3):** nenhum digest OCI publicado, nenhuma aquisição por
  digest, nenhuma promoção. Os candidatos acima são locais.
- **Promoção:** os doze containers MCP dos dois gestores seguem nos image IDs A
  da §5.1 do runbook; nenhum pin foi tocado.
- **A5/A6:** os consumidores ativos mantêm a imagem antiga (init interno,
  provenance de worktree) — sem cutover, por decisão de gate.
- **D-4:** mantém a aceitação formal de risco residual do F0 (rotação de
  credencial exposta adiada); o formato de gravação dos segredos segue sem
  decisão e independente desta etapa.
- **Checks globais:** `ruff check .` mantém 7 erros preexistentes em
  `scripts/d11/d9_rehearsal.py` (reproduzidos no conteúdo de `HEAD`) e
  `basedpyright nanobot` global segue falhando por dependências opcionais
  ausentes no ambiente — fora do diff desta rodada. Foco verde:
  `tests/channels/test_channel_plugins.py` + `tests/mcp_docker` = 225 passed,
  Ruff dos arquivos alterados e basedpyright de `nanobot/optional_features.py`
  com 0 erros.
- **Periodicidade:** a base de vulnerabilidades usada aqui expira em
  2026-10-26; a revisão trimestral do runbook (§4.1) deve reexecutar scan e
  SBOM antes de qualquer promoção.

## 9. Próximo passo

1. Autorização do operador para enviar as fontes dos seis repositórios
   (2 commits no core, 1 em cada MCP alterado).
2. Promoção dos candidatos limpos continua condicionada a B5 (CI remoto verde no
   SHA exato) e B6 (digest publicado e aquisição homologada), com autorização
   própria; nenhum comando de promoção foi preparado.
