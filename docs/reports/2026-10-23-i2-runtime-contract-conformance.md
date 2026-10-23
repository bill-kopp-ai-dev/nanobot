# I2 / P0-B — Agent Runtime Contract Percival: execução local

- **Resultado:** I2.1–I2.6 concluídos no escopo de contrato/conformance **local
  Linux/amd64**. Não é homologação de release, Actions, MCPs públicos ou VPS.
- **Execução final:** `2026-10-23T16:45:21.065892+00:00` (13:45 em São Paulo).
- **Solicitação:** bill pediu seguir I2 após o commit/push documental de I1.
  Executor: agente, sessão `ses_e96f9440affe5HbhNZOSFMAKN4`; revisão de produto: bill.
  Não houve revisão independente nem aceite B13 nesta campanha.
- **Fonte:** `bill-kopp-ai-dev/nanobot`, baseline integral
  `eb4e3555e76e35f52171c61c965d55aa5450dcda` + mudanças I2 no worktree, sem novo commit.
  Labels do build atual explicitam `...-dirty-i2`, não fingem um SHA limpo candidato.
- **Contrato entregue:** [runtime 1](../agent-runtime-contract.md), em conformidade
  com a [ADR I1](../Decisions/2026-10-23-open-iac-contracts.md) e seu [handoff](../iac-p0-contract-handoff.md).

## 1. Ambiente e isolamento

Host Linux x86_64, Docker Client/Server 29.9.1, Compose v5.6.0. O host já executava
Percival e MCPs reais; eles não foram usados como fixtures nem reiniciados.
O ensaio criou um daemon Docker **27.5.1 rootful** descartável, imagem
`docker:27.5.1-dind@sha256:aa3df78ecf320f5fafdce71c659f1629e96e9de0968305fe1de670e0ca9176ce`.
Broker: Docker CLI **29.9.0** copiada da base pinada existente. Nenhuma exceção
`PERCIVAL_DISPOSABLE_ENGINE29` foi usada no caso positivo.

Só o container dind de nome único foi criado no daemon externo; seu socket, mount
inventory, namespace, gateway, API, broker e MCP fixture eram internos. API do dind
publicada em porta efêmera no loopback, removida com o container ao terminar. Não
houve conflito com os nomes/portas da instalação viva. O bind `/fixture` continha
somente estado e credenciais sintéticos desta campanha; nenhum mount Full do host real.
As imagens foram transferidas por `docker save/load`, sem login/push ou registry próprio.

Metadados e wheel instalado foram verificados no runtime Python 3.12 da imagem.
Ambiente de checks separado, Python 3.12.14, uv 0.12.18, baseado nos locks do projeto
e dependências dos channels pela interface oficial do instalador.

## 2. Entregas por subtarefa

| Item | Entrega e resultado observado |
| --- | --- |
| **I2.1** | `docs/agent-runtime-contract.md`: modos gateway/API/CLI/broker, argumentos, paths, writers, UID/GID, caps, rede/probes e sinais. Gateway/API/broker com exatamente um init e um filho principal. API passou a profile `api`, alternativa explícita, não segundo writer default |
| **I2.2** | Overlay agora mapeia CLI/API/gateway ao mesmo bind inventariado. `onboard --refresh`, `status`, `auth init/change/status` reais. Sem verifier, bootstrap protegido 401; init repetido exit 1 preserva bytes da credencial. API sem chave exit 1 antes de bind; com chave, health 200, protegido anônimo/senha humana 401 e bearer API distinto 200 |
| **I2.3** | UID 1000 e UID/GID alternativo 1001 com estado próprio/imports offline; gateway Compose alternativo com auth, health e SIGTERM exit 0. Ownership incorreto exit 1; `setpriv` injetado com falha exit 1, sem executar agente root. Código/venv legíveis independentemente do umask do checkout; `.venv` gravável só por UID 1000. App sem caps efetivas/permitidas/ambientes/herdáveis, NNP=1. Render flag testada com disco novo root-owned e estado existente |
| **I2.4** | `STOPSIGNAL SIGTERM`, grace Compose 60 s no gateway/API. Probe sidecar autenticada `/v1/health` substitui TCP; `doctor` pelo gateway, handshake/list/call reais por MCPProvider. Root init recebe KILL para encaminhar sinais depois do drop. Gateway/API/root-drop encerraram com exit 0; broker com 143, sem promessa de drain; stdio fixture EOF exit 0 |
| **I2.5** | Gateway saudável com broker ainda ausente, doctor exit 1; broker posterior reconecta. Recriação conjunta muda ID do gateway e reata namespace do sidecar. SIGKILL do broker seguido de recriação/hydrate mantém config byte a byte e marcador de persistência; tool volta a responder. Um único MCP fixture gerenciado retido, sem processo `docker attach` órfão ao final das chamadas. Token errado 401/probe exit 1. Server 28.0.0 injetado rejeitado antes do listener |
| **I2.6** | Matriz versionada no contrato: par atual, gateway atual/broker baseline real 0.3.5 com hydrate+initialize/list/call, caller v1 independente/broker atual, health antigo sem campos não concede features, protocolo WebUI 1 e schema MCP 1 estrito. Imagem mínima inclui a probe nova e continua usando o lock Pydantic pinado, sem dependência nova |

### Alinhamento de identidade executável

- `pyproject.toml` é autoridade: versão `0.1.0`, nome `nanobot-ai` preservado.
- `uv lock --offline` regenerou `uv.lock`: **somente** versão do pacote raiz mudou;
  nenhum upgrade de dependência.
- Fallback sem pyproject/dist-info, metadata instalada, dois Dockerfiles/defaults
  Compose e labels usam `0.1.0`. WebUI/TUI mantêm a versão de componente existente.
- Nenhum rename de import/CLI, migration de config/schema, tag ou publicação.
  O alinhamento de metadados não resolve o futuro nome de distribuição Python.

## 3. Artefatos e evidência bruta

Diretório privado da campanha, fora da fonte rastreada:
`/home/bill/.positronic/runtime/tmp/opencode/percival-i2-ses-e96f9440/`.

**Ensaio final:** `i2-5atl75uj/results.json`, `completed: true`, **19 checks PASS**,
incluindo identidades de processos, caps/UID/GID e tempos. Image IDs abaixo foram
observados **no daemon 27.5.1 que executou os containers**:

| Referência local transferida | Image ID observado na execução |
| --- | --- |
| `percival-i2-gateway:ses-e96f9440` | `sha256:a35c8d5ebe35aaf28bbebd5dedfd75fd5ad7e89540e9a2f945f945b6ffe5e487` |
| `percival-i2-broker:ses-e96f9440` | `sha256:8c1f9396111fdce2605dbebcd380554f8d84df3522ee8039d6ca7f91afdca08c` |
| `percival-i2-old-broker:eb4e3555` | `sha256:d56f898d3b81e8faccc4f9c5951d1f5bedd2af57cbe9f4d64dd0722e4647f350` |

O image store externo 29.9.1 retornou outros IDs locais ao inspecionar as referências
antes de save/load: gateway `21ffa1fe9ac073296cafdfc90c73fb493c13df993b7216d728e54df6da33f3af`,
broker `2072ea1484405bbfed3c20fc01729ac37eed19c364fc001d835887a17de1052f`,
baseline `580642c54de8248b0bc8874c36c136a0705e275dc440b0b28c7835971417a481`.
Não intercambiar esses IDs nem apresentá-los como RepoDigests publicados. Nenhum
digest OCI de registry para estes candidatos foi obtido por esta execução.

`gateway-build.log`, `broker-build.log`, `old-broker-build.log` preservam builds.
O broker baseline foi construído de `git archive eb4e3555...` com os arquivos de seu
Dockerfile mínimo; não veio da instância viva, nem de uma tag upstream inferida.
Arquivos de origem/runtime, locks e runner têm hashes no inventário privado
`source-inputs.sha256`; conteúdo e checks devem ser renovados se esses inputs mudarem.

Tempos **amostrais, em idle**, no ensaio final: gateway 1.077 s, API 1.616 s,
root-drop/Render flag 1.768 s. Não são percentis, SLOs, RTOs ou prova de shutdown
durante um turno/chamada externa. Broker encerra por sinal (143) e perde seu store
volátil; isso não indica remoção de MCP persistente nem encerramento de uma transação.

## 4. Verificações reproduzíveis

No checkout; `E` denota o ambiente privado da campanha:

```bash
E=/home/bill/.positronic/runtime/tmp/opencode/percival-i2-ses-e96f9440/env
"$E/bin/python" -m pytest -q tests/test_package_version.py tests/mcp_docker tests/webui/test_client_contract.py tests/cli/test_gateway_runtime.py tests/cli/test_gateway_commands.py tests/access tests/gateway/test_api_runtime.py
"$E/bin/python" -m pytest -q tests/test_package_version.py tests/mcp_docker/test_probe.py tests/test_openai_api.py tests/test_api_stream.py tests/test_api_attachment.py
"$E/bin/ruff" check .
"$E/bin/basedpyright" --pythonpath "$E/bin/python" nanobot
bash -n scripts/percival-f5-compose-smoke.sh
git diff --check
```

- Grupo core/auth/MCP/compatibilidade: **167 passed**, 5 warnings de fixtures
  Pydantic que serializam dicts no lugar de modelos em testes existentes.
- Grupo API/metadata/probe: **69 passed**; três casos de metadata/probe repetem
  o grupo anterior. Não somar as duas contagens como testes distintos.
- Ruff: passou; basedpyright: **0 erros, 0 warnings** usando o interpretador correto.
- O primeiro typecheck sem `--pythonpath` selecionou a `.venv` preexistente com link
  de Python inexistente e produziu milhares de erros de resolução. Foi corrigido o
  ambiente do check, não silenciados erros do código; o ambiente existente foi preservado.
- CI passou a chamar o runner isolado com as duas imagens já construídas. A asserção
  root divergente foi reproduzida e substituída pelas provas efetivas do runner;
  o wrapper F5 mantém o ponto de entrada antigo, com fixtures sem portas do produto
  publicadas no host. `results.json` entra nos artefatos do job, inclusive em falha.

Build atual (executado para ambos os Dockerfiles, trocando `-f`/tag conforme imagem):

```bash
docker build --platform linux/amd64 --build-arg VERSION=0.1.0 \
  --build-arg GIT_SHA=eb4e3555e76e35f52171c61c965d55aa5450dcda-dirty-i2 \
  -t percival-i2-gateway:ses-e96f9440 .
python3 scripts/percival-i2-runtime-smoke.py \
  --gateway-image percival-i2-gateway:ses-e96f9440 \
  --broker-image percival-i2-broker:ses-e96f9440 \
  --old-broker-image percival-i2-old-broker:eb4e3555 \
  --scratch-parent /home/bill/.positronic/runtime/tmp/opencode/percival-i2-ses-e96f9440
```

### Resultados intermediários e correções

Os ensaios anteriores não foram convertidos em PASS retroativamente. Eles expuseram:
arquivos de código sem leitura para outros UIDs, home 0700 bloqueando UID alternativo,
necessidade de descobrir o GID real do socket, tmpfs do broker sem ownership do UID
65532 e falta de KILL no init root restrito. Corrigidos os respectivos owners/inputs;
o caso root sem KILL preservou log fatal do tini em `i2-o0bfijlw/`.

A expectativa inicial de que o gateway inteiro recusaria startup sem verifier estava
errada: o contrato existente recusa **acesso autenticado**, não o listener da página
de login. O teste foi corrigido para 401 real, sem mudar a política do gateway;
`docs/deployment.md` deixou de repetir a afirmação contradita pelo ensaio.

## 5. Limites e handoff

- **V01:** execução local coberta. **V02:** setup/auth/API local coberto; bootstrap IaC
  completo e idempotência de deployment são I4. **V03:** sinais/EOF/crash/recreate
  cobertos em fixture idle; recuperação de trabalho em voo é I8. **V04:** wire/config
  e fixtures de compatibilidade cobertas localmente; Actions/C1 e gate B3 de clientes
  reais conservam seus escopos. Não declarar V01–V24 integralmente encerrados.
- Os três formatos de mount existentes, políticas/permissões dos servidores reais e
  `schemaVersion=1` foram preservados. Nenhuma aquisição ou export de catálogo/lock
  novo foi ativado. Fixture stdio não homologa Weather/OSM/terceiro (I5/I6).
- Broker antigo não contém `probe.py`; sua compatibilidade wire não torna o bundle
  atual e aquele healthcheck automaticamente compatíveis. Usar o par/bundle aprovado.
- Nenhuma chamada LLM paga, credencial real, atualização de instalação ativa, serviço
  Render, VPS, ARM64, scan/SBOM novo, login, Actions remoto, publicação, commit ou push
  foi executado nesta campanha. A suíte pytest completa e o wrapper F5 com autobuild
  não foram executados; seus componentes afetados e o runner real foram verificados.
- **Próximo responsável:** agente prepara I3 quando solicitado; bill confirma canal
  protegido/acesso Docker Hub e aprova publicação em B13. I4 pode consumir runtime 1
  para ensaios locais. I6/I7 e demais gates aplicáveis devem entrar no candidato final
  se a release anunciar integração IaC. Fonte limpa/SHA final, scan e evidência remota
  continuam condições de promoção; estes worktree builds não são releases.
