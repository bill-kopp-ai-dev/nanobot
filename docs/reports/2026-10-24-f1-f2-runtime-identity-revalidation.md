# F1/F2 — Revalidação de runtime e fechamento local de identidade

- **Data:** 2026-10-24, America/Sao_Paulo (UTC-03:00).
- **Estado:** F1 revalidada nos candidatos atuais; critérios locais do gate F2
  atendidos, com implementação complementar de inventário no worktree.
- **Plano:** [padronização Docker](../plans/2026-10-09-docker-standardization-refactor-plan.md),
  fases F1 e F2, após o [fechamento da reexecução F0](2026-10-24-f0-closure-record.md).
- **Fonte Percival:** HEAD `3ae3098e`, mais o diff de inventário/testes/documentação
  desta execução. Nenhuma alteração nos seis repositórios MCP.
- **Ambiente:** Docker Engine 29.9.2, Compose 5.6.1, `linux/amd64`.
  Evidência local; não é homologação do Engine 27.x nem gate remoto de CI/release.

## 1. Escopo, critério e reaproveitamento de evidência

F1 já estava implementada e validada historicamente. A execução atual verifica
novamente stdio, profiles HTTP, health, bind/auth e sinais dos dois candidatos
vigentes. O critério de sucesso foi definido antes do ensaio: MCP `initialize` e
`tools/list` válidos em stdio, sem TTY/portas/probe HTTP; endpoint HTTP real e
probe saudável; auth OSM; um init e SIGTERM sem SIGKILL por modo.

O gate F2 ainda dizia faltar seis builds de checkout limpo. Essa evidência já
foi produzida em D8: [§7.1 e §7.3/C3 do fechamento D8](../plans/closed/2026-10-24-d8-promotion-readiness-closure-plan.md).
Nesta execução, os seis IDs foram **reinspecionados**, confrontados com os SHAs
completos, versões TOML e estado Git limpo dos seis repositórios. Fonte e imagens
continuam idênticas à evidência D8. Portanto os builds são reaproveitados conforme
`.agent/workflow.md`; **nenhum build foi repetido**, nenhuma tag canônica foi
sobrescrita e não se atribui à execução atual o build histórico.

Também foram exercitados o inventário JSON/Markdown, a distinção entre gestores
que compartilham imagem e a preservação de pins. Os testes do broker verificam
UUID v4 novo a cada spawn do mesmo servidor.

## 2. Identidades verificadas dos seis candidatos

Todas as imagens abaixo são `linux/amd64`, têm os oito labels OCI não vazios,
`version` igual ao TOML, `revision` igual ao HEAD completo e source/documentation
do respectivo repositório. Os seis checkouts estão limpos e as imagens não têm
label `worktree=dirty` nem hash de diff de candidato.

| Serviço | Tag canônica local | Revisão completa | Image ID |
| --- | --- | --- | --- |
| Notes | `percival-notes-mcp:0.1.5-c104735` | `c1047355bce2512cc50ca89c0c8af0b82837909a` | `sha256:3abd363f5a354a293b7c5ef5bf58a30cfd245800814f6b800c4545fba994822a` |
| AgentMail | `percival-agentmail-mcp:0.4.0-cd55a2f` | `cd55a2fe7121f41e8bd5470973ff84e1ba5e58f8` | `sha256:9591d7786a5234b9a5635a5d9fb49d010c66233de25cdf955b4508063c8a53c1` |
| Weather | `percival-weather-mcp:0.9.0-437a41c` | `437a41c3fd55ae7994c71894e639a6c4ca6d8d43` | `sha256:b805919db8fb10af2dd5ea527402449aa743ebcb3762b4d84085f99f97b2d70f` |
| Khan Calendar | `percival-khan-calendar:0.4.0-e8c5d8c` | `e8c5d8c0ad2ed498f96985dd77f6247539f62cfb` | `sha256:9aa02922d5163b992032eafcdaef7f49e009d8e0c855b2f93c258b3bb881db1f` |
| OSM | `percival-osm:0.5.0-04d4399` | `04d4399c8f8d1a9ce24c8d5ac4cb2208b1801b76` | `sha256:ce6de5ccd164ec8c89d4f5b195b140f1dd12f1405f50919614aaf8f93252159b` |
| Deep Research | `percival-deep-research:3.0.1-af3b23b` | `af3b23be6d3bdec88bc0da3e419d62ecd55e9aa4` | `sha256:bab6d3ced1b3b20497f0ef61e36e14f2362eca3523b2492519d6596802eb30ff` |

Os `RepoDigests` locais observados têm o nome do repositório seguido de
`@sha256:<mesmo hash do Image ID>`. Foram registrados separadamente no artefato
`identity-results.json`; não são prova de digest OCI remoto nem de publicação.
O artefato também registra SHA-256 do `uv.lock` de cada checkout e todos os labels.

## 3. F1 — Execução por modo

Foram usadas as receitas Compose dos próprios repositórios, em projetos
`f1-r2-osm-2780953` e `f1-r2-deep-research-2780953`. Um overlay de fixture:

- seleciona o **image ID completo** local, remove `build` e usa `pull_policy: never`;
- remove `env_file` e volumes reais, substitui o ambiente por valores sintéticos e
  dados por tmpfs com o UID/GID da imagem;
- conserva o contrato de init/TTY/stdio e o comando de health do profile HTTP;
- usa porta efêmera publicada em `127.0.0.1`, restart desabilitado e intervalos de
  health de 1 s para reduzir o tempo do ensaio;
- não solicita pesquisa, geocodificação ou outra operação upstream. O único
  `tools/call` foi `osm_get_version`, local, sem credenciais reais.

| Verificação | OSM | Deep Research |
| --- | --- | --- |
| Imagem sem init embutido | entrypoint sem tini/docker-init | entrypoint sem tini/docker-init |
| Stdio `initialize` | passou, protocolo `2024-11-05` | passou, protocolo `2024-11-05` |
| Stdio `tools/list` | 37 tools | 5 tools |
| Stdio stdout | somente JSON-RPC nas respostas observadas | somente JSON-RPC nas respostas observadas |
| TTY / stdin aberto / portas stdio | `false` / `true` / `{}` | `false` / `true` / `{}` |
| Healthcheck stdio / estado health | `NONE` / `none` | ausente / `none` |
| PID 1, stdio e HTTP | `docker-init`, `HostConfig.Init=true` | `docker-init`, `HostConfig.Init=true` |
| Endpoint HTTP exercitado | Streamable HTTP `/mcp` | modo SSE, `GET /health` |
| Bind observado | `127.0.0.1:32787` | `127.0.0.1:32788` |
| HTTP sem auth | `/mcp` retorna 401 | `/health` retorna 200; não é teste de auth |
| HTTP com auth | `initialize` retorna 200/JSON-RPC com bearer sintético | não aplicável ao health |
| Healthcheck efetivo do profile | `GET /`, aceita 200/401/404/405; healthy | `GET /health`, aceita 200/503; healthy |
| SIGTERM stdio / HTTP | 143 / 143, dentro de 10 s | 143 / 143, dentro de 10 s |

O body `/health` do Deep Research retornou `healthy`, versão `3.0.1`, com
`inference_configured=true` e `retriever_configured=true`, **mesmo com chave
sintética**. Isso prova listener/configuração presente, não validade da chave nem
readiness de provider. O encerramento foi observado em idle, não durante pesquisa.
O profile `production`/nginx não foi iniciado.

As tentativas iniciais do harness foram corrigidas antes do ensaio final: Compose
`run` nesta versão não aceita `--no-build`; rede Docker `internal` não forneceu
publicação host utilizável (`compose port` retornou `:0`). O ensaio final usa uma
bridge própria e fixtures com dados/chaves sintéticos. Esses erros eram do
harness; não exigiram mudança de runtime dos produtos.

Containers e redes desses projetos foram removidos pelo próprio Compose após
stop/inspeção. As imagens e os containers históricos foram preservados.

## 4. F2 — Complementos de inventário e testes

Alterações em `nanobot/mcp_docker/inventory.py`:

1. Allowlist explícita dos seis labels `io.positronic.*` aprovados por D-6,
   preservando os labels broker `percival.mcp-docker.*`. O inventário reconhece
   containers Positronic pelos labels mesmo com nome e imagem não descritivos.
2. Preservação dos labels de build `worktree`, `source-diff-sha256` e `phase`, para
   distinguir candidatos dirty das imagens canônicas limpas.
3. Labels Compose de projeto, serviço, arquivos e diretório de configuração;
   descoberta também de `docker-compose*.yml/yaml`, incluindo o override Engine 29.
   `.Image` permanece a identidade efetiva; labels Compose não a substituem.
4. Markdown mostra owner/gestor/server/instância dos dois esquemas, healthcheck e
   init/TTY/stdin; corrige a coluna ausente de labels e escapa pipes/newlines nas
   células. Não infere owner pelo Image ID compartilhado.

O comando read-only continua sendo:

```bash
python -m nanobot.mcp_docker.inventory --format json
python -m nanobot.mcp_docker.inventory --format markdown
```

Resultado observado: **58 imagens relevantes, 15 containers relevantes e 21
referências**. O host continua com 16 containers; `d7host-noinit` não é selecionado
pelo filtro de relevância, portanto essas contagens não são inventário de todo o
Engine. Há **12 MCPs gerenciados, 12 UUIDs v4 únicos e seis pins distintos**:
para cada imagem, um container Percival e um Positronic, com identidades distintas.
Os seis pins nos dois arquivos de configuração coincidem com F0. Os hashes dos
arquivos de configuração permaneceram iguais durante as consultas de identidade.

Não se consulta `Config.Env` nem conteúdo de arquivo de segredo no Docker; a
extração das referências JSON em config/registry não emite os demais valores.
A allowlist não inclui labels arbitrários. Mounts de segredo continuam redigidos.

## 5. Verificações de código e limites globais

Ambiente reutilizado de testes: `/home/bill/.positronic/runtime/tmp/opencode/nanobot-f7-test-env/bin`.
As invocações abaixo usam os executáveis desse diretório; `basedpyright` focado
recebe `--pythonpath` apontando para seu `python`.

| Check | Resultado |
| --- | --- |
| `python -m pytest tests/mcp_docker --no-cov -q` | 87 passed, 5 warnings de serializer Pydantic; antes do último ajuste de escape Markdown e da asserção adicional de recreate |
| `python -m pytest tests/mcp_docker/test_inventory.py --no-cov -q` após o escape | 8 passed |
| `python -m pytest tests/mcp_docker/test_broker.py --no-cov -q` após a asserção de recreate | 33 passed |
| `ruff check nanobot/mcp_docker/inventory.py tests/mcp_docker/test_inventory.py tests/mcp_docker/test_broker.py` | passou |
| `basedpyright --pythonpath <ambiente>/bin/python nanobot/mcp_docker/inventory.py` | 0 errors, 0 warnings |
| `git diff --check` | passou |
| `ruff check .` | falhou: 7 erros em `scripts/d11/d9_rehearsal.py`, arquivo não alterado; os mesmos 7 erros foram reproduzidos no conteúdo de `HEAD` via `git show`/stdin |
| `basedpyright nanobot` | sem interpreter explícito: 12.413 erros, com imports básicos ausentes; com o interpreter de testes: 1.580 erros fora do inventário, associados a canais/providers opcionais ausentes (Telegram, Discord, Azure, boto3 etc.) |

A suíte completa do produto e os checks remotos não foram executados. Os checks
focados cobrem a alteração; **não se declara lint/typecheck global verde**.
O teste de recreate conserva nome/pin do servidor e exige UUID v4 diferente em
dois spawns. A regressão de inventário usa dois gestores sobre o mesmo image ID,
sem nomes descritivos, verifica labels permitidos, rejeição de label de segredo e
alinhamento das colunas Markdown incluindo um healthcheck com `||`.

## 6. Evidência bruta e reprodução local

Diretório fora da fonte: `/home/bill/.positronic/runtime/tmp/opencode/f1-f2-20261024/`.
Para reproduzir a fixture local, com as mesmas imagens presentes:

```bash
python /home/bill/.positronic/runtime/tmp/opencode/f1-f2-20261024/verify_runtime.py
python /home/bill/.positronic/runtime/tmp/opencode/f1-f2-20261024/verify_identity.py
```

O primeiro cria/remove somente seus projetos Compose sintéticos. O segundo é
read-only para Docker/gestores e grava apenas evidência nesse diretório. Não são
comandos de promoção. Os overlays e stderr da fixture também ficam nesse diretório.

| Artefato | SHA-256 |
| --- | --- |
| `verify_runtime.py` | `ec569608e621867bb697b1f7dc9afd97feda1ea8cab51c14948d830f4abe9003` |
| `runtime-results.json` | `9f0a1eeb94fb843cca225de9f3ac87b4c4dc56eabb0ad7fe7f71721f3fd7d51d` |
| `verify_identity.py` | `5497ed3fa6b2b4415de41bdecafd85760472cf63e7d44940094c239b80cae729` |
| `identity-results.json` | `f378aa8e1d0a2a2bd8889f97cf5a4e6e783d956aabcd77f597e8d18fbe020d3d` |
| `inventory.json` | `df0ad23908d5e47bd9dd11d0786a0684dc13ab11f45ead4844a0d863884a5d19` |
| `inventory.md` | `0d410fb7ba0f671d3f8b66f87f6932d04c291cd7dad67de43c32794079dd482a` |

## 7. Resultado e próximo passo

- **F1 local:** revalidada nos IDs atuais, com evidência funcional stdio/HTTP e
  sinais, sem mascarar a falha por simples remoção de probe.
- **F2 local:** critérios atendidos. Builds limpos comprovados por D8 e
  reinspecionados agora; pins imutáveis preservados; inventário diferencia as
  instâncias e os dois gestores. A melhoria complementar está validada no
  worktree, ainda sem commit/push.
- A5 (duplo init nas imagens antigas ainda pinadas) e A6 (artefatos dirty ainda em
  execução) permanecem desvios **dos consumidores ativos**. Esta validação não os
  corrige por cutover. D-4 segue com o risco aceito em F0; não houve rotação nem
  alteração do formato de gravação de segredos.
- Próxima ação de versionamento: operador revisar o diff e autorizar commit/push
  desta nova execução. CI remoto, distribuição e promoção continuam com seus
  critérios próprios em B5/B6, I3/I5 e F6.
