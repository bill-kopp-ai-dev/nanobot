# F5 — Revalidação de conformance e CI por repositório

- **Data:** 2026-10-25.
- **Escopo:** verificar o F5 documentado para o core Percival e seis MCPs, inspecionar Actions nos SHAs enviados após F4, reproduzir falhas localmente e corrigir causas demonstráveis.
- **Estado:** correções em seis MCPs commitadas/enviadas a `main`; **F5/C1 permanece aberto** até Actions e artefatos no SHA final, incluindo o core. Nenhum workflow foi manualmente iniciado e nenhuma imagem foi publicada.
- **Limite local:** Docker Engine 29.9.2 linux/amd64; builds/smokes locais são evidência de desenvolvimento, não homologação do Engine 27.5.1 nem substituto dos Actions.

Builds locais de diagnóstico (não publicados; image IDs distintos de RepoDigest OCI):

| Repo | Tag local | Image ID | `revision` |
|---|---|---|---|
| Notes | `percival-notes-mcp:f5-recheck` | `sha256:d60843218c695d93c9e75fcb435638ce1b59ef1a3bf9356c284fe23ec297754d` | `269edd43cc9c8461339284e956854ae88fe36389` |
| Weather | `percival-weather-mcp:f5-recheck` | `sha256:2dd136f016a9816cfb51b5e6e0b0777046a552eb4593c50a5fe59b3f67a20304` | `afcbc20c48415aa2481f86f16285ffb31f48baaf` |
| OSM | `percival-osm:f5-recheck` | `sha256:2743864333a4e7275001c5695f1824b7ed50d77afdab1e9bb01220b54ae622ad` | `8eb0a621d697769c7432642c90740eedf25f534c` |
| Deep Research | `percival-deep-research:f5-real-recheck` | `sha256:f460a9c43be76c18f7e75c798de2d1755afe178429312e68c169af1479043ceb` | `92080e7fe733ccc901f9720ed90f23b282e4bd9d` |

**Anomalia de fixture:** uma primeira tentativa de build Deep Research foi disparada com o diretório Notes como contexto e criou a tag local `percival-deep-research:f5-recheck`, image ID `sha256:47e72b1ba7c35e7546fe454b5e5821f79fba25423f7b24e25b1fccdebb66008a`; seu usuário `65532:65532` confirma que não é a imagem Deep Research. Não foi usada por smoke, consumer ou workflow. Ela permanece no daemon, sem remoção/prune; o candidato correto é `f5-real-recheck` acima.

## Actions nos SHAs observados

| Repositório / SHA | Run mais recente | Resultado observado |
|---|---|---|
| `nanobot` (snapshot inicial `f3ad1590f36af054e1babaf97fdac82c5fb9a9ff`) | [check-runs](https://api.github.com/repos/bill-kopp-ai-dev/nanobot/commits/f3ad1590f36af054e1babaf97fdac82c5fb9a9ff/check-runs) | 0 checks; a página pública informa workflows desabilitados neste fork. Reler `main` após habilitação, antes de dispatch. |
| Notes `83980418b3239be5476f6d347ceb8dad32d90e8e` | run #10, [Actions](https://github.com/bill-kopp-ai-dev/percival-notes-mcp/actions) | **success** (test + Docker image conformance). |
| AgentMail `68751b696b62b53fdcf893c3add9cf9e648e4391` | run #30, [Actions](https://github.com/bill-kopp-ai-dev/percival-agentmail-mcp/actions) | **success** (Python 3.11/3.12 + Docker smoke); manifest/SBOM artifact present. |
| Weather `144dd44078bea4c7ba35111e15442cfc6bf14398` | run #29, [Actions](https://github.com/bill-kopp-ai-dev/percival-weather-mcp/actions) | **success** (Python matrix + Docker profile/conformance after file-permission correction). |
| Khan `919b6ab9bb1b12d3ee48aa95c4d97f9463a738d0` | run #31, [Actions](https://github.com/bill-kopp-ai-dev/percival-khan-calendar/actions) | **success** (Python 3.11/3.12 + Docker build/smoke); manifest/SBOM artifact present. |
| OSM `06484259a3bb5371c5c1551dcab0c23ccc166479` | run #22, [Actions](https://github.com/bill-kopp-ai-dev/percival-osm/actions) | **success** (Docker build/conformance, Python tests and catalog schema). |
| Deep Research `defc9434487be4db7dbc13003db1709047297471` | run #15, [Actions](https://github.com/bill-kopp-ai-dev/percival-deep-research/actions) | **failure** in the pytest job; local suite passes, but remote logs are unavailable unauthenticated. |

As listagens públicas confirmam nomes de jobs, steps e `head_sha`; páginas de execução confirmam Notes, AgentMail, Khan, Weather e OSM verdes. Deep Research falhou no follow-up. Logs/artefatos não-verificados requerem sessão GitHub: o shim local `gh` não executa sem trust da configuração mise, e endpoints de download de logs retornam HTTP 403. O core continua sem execução no SHA atual.

## Correções preparadas e validação local

- **Notes:** corrigido o quoting do Go-template do label OCI no workflow; a forma anterior passava `\"` literalmente ao Docker. Build local do SHA `269edd4` verificou `linux/amd64`, UID `65532:65532`, sem healthcheck e revision exata; conformance MCP stdio passou (12 tools).
- **AgentMail:** alinhado `tests/test_docker_contract.py` ao formatter do lock. Ruff check/format passaram; suíte CI local: **236 passed, 1 skipped, 92.42% coverage**. O job Docker remoto já passou neste SHA.
- **Weather:** metadata Docker agora usa Python 3.12 explícito; corrigido o Go-template do label; workflow cria secret file sintético para render/up do profile HTTP com permissões de leitura compatíveis com o UID runtime. Build amd64 local e conformance passaram (9 tools, UID 999). `pyproject.toml` reporta versão `0.9.0` no comando de metadata.
- **Khan:** formatado o teste de contrato Docker. Ruff check/format passaram; suíte local: **231 passed, 87.47% coverage**. O job Docker remoto já passou neste SHA.
- **OSM:** testes estáticos atualizados para o contrato F4 (credencial HTTP via secret file, health MCP autenticado, valores USER_AGENT opcionais no render e falha fail-closed no entrypoint); workflow fixa Python 3.12 para build metadata/testes e cria secret file sintético legível pelo UID runtime; o smoke substitui o harness FIFO com espera fixa pelo probe MCP comum. `uv sync --locked --group dev`, suíte, render Compose e `bash -n` passaram localmente. Build + smoke local: 37 tools, HTTP loopback, 401 sem bearer, initialize autenticado saudável e SIGTERM exit 143. Actions #21 e #22 passaram, inclusive `uv sync`, testes e conformance.
- **Deep Research:** workflows corrigidos para citar o revision OCI sem barras literais; criado `.env` sintético em `$RUNNER_TEMP`, legível pelo UID runtime, para o bind read-only exigido pelos profiles Compose. Testes Docker atualizados ao contrato streamable-http e ao `.env` montado, sem credenciais em `Config.Env`; o probe foi formatado. Ruff check/format passaram; suíte local: **414 passed, 3 skipped**. Build local do SHA `92080e7` verificou amd64, usuário `percival` (UID 1000), sem healthcheck, revision exata; conformance MCP stdio passou (5 tools). Runs #14 e #15 falharam em pytest; causa não identificada por falta de logs autenticados.

Os valores de credencial usados em fixtures são sentinelas sintéticos; nenhum serviço externo foi chamado. O F4 reportado em `2026-10-25-f4-compose-runtime-revalidation.md` permanece a evidência local dos smokes HTTP dos MCPs.

**Pushes desta campanha:** Notes `8398041`, AgentMail `68751b6`, Weather `0bb1497` → `144dd44`, Khan `919b6ab`, OSM `69e25be` → `43164bb` → `0648425`, Deep Research `268c7ca` → `defc943`. Todos os SHAs foram enviados para `main`; Notes, AgentMail, Khan, Weather e OSM passaram Actions. Deep Research continua falhando no job Python.

## Gate e próximo passo

O aceite F5 requer todos os workflows obrigatórios verdes nos SHAs finais e manifest/SBOM obtidos e comparados. Cinco dos seis MCPs passaram Actions (Notes, AgentMail, Khan, Weather, OSM); Deep Research falhou no SHA atual. A causa remota de Deep não pode ser determinada sem logs autenticados. O core não tem run no SHA atual. O shim `gh` local exige trust da configuração mise, que não foi alterada; logs/artefatos não foram baixados.

**Próximo responsável:** bill habilitar Actions no core e fornecer sessão GitHub autorizada para logs/artefatos. Obter logs autenticados do pytest Deep antes de correções adicionais. Baixar/comparar manifests/SBOMs dos sete repos e só fechar F5/C1 com sete pipelines verdes e `headSha` exato. Nenhuma promoção, publicação, pin, gestor, container ou dado real foi alterado.
