# F0 — Baseline e inventário Docker

**Data da observação:** 2026-10-09
**Estado:** baseline e decisões F0 concluídos; execution gates F1+ ainda não iniciados.
**Plano:** [padronização Docker do Percival](../plans/2026-10-09-docker-standardization-refactor-plan.md)

## Escopo e método

Inspecionados os worktrees do Percival, dos seis servidores MCP e do runtime
Positronic; metadados de Compose, containers, imagens, config broker e registry
Positronic. Valores de ambiente e conteúdo dos arquivos de credenciais não foram
lidos nem registrados. Nenhuma imagem, container, configuração, mount ou serviço
foi alterado. A listagem é um snapshot local, não uma série temporal.

## Host/runtime observado

- Docker Engine **29.7.2**, Linux `x86_64`; as imagens de aplicação observadas
  abaixo são `linux/amd64`.
- Gateway ativo `nanobot-gateway`, imagem
  `nanobot-nanobot-gateway:latest`, ID
  `sha256:fb516d1469100fd7500a89a60fce1cd332575ebe0aae654210aa0c7a502891d5`.
  OCI metadata efetiva identifica a base uv 0.9.30, não o Percival.
- Compose publica `8765` em todas as interfaces; `18790` fica em loopback.
  Gateway está `Up`, sem healthcheck Docker; API não aparece entre containers.
  Mount do gateway: `/home/bill/.nanobot` → `/home/nanobot/.nanobot`, read/write.
- Broker ativo `nanobot-percival-mcp-broker-1`, ID
  `sha256:14fc47c55982077c3c093f69f449d6ca7335a8043479bdbd81b8028ae233cb3d`,
  healthy, UID/GID 65532. É o único serviço Percival observado com Docker
  socket. A configuração inclui também mounts host/inventory em read-only,
  conforme a arquitetura aprovada B14–B25; esta revisão não reavalia nem altera
  esse contrato.
- Quatro containers MCP estão em execução: duas instâncias Deep Research e
  duas AgentMail, todas sem labels de instância/gestor. As duas Deep Research
  estão `unhealthy` pelo probe HTTP embora configuradas para stdio. Os quatro
  mounts observados são somente os arquivos `.env` Positronic correspondentes,
  read-only. Duplicatas e causa de criação não foram atribuídas a processos
  individuais.
- Há também containers Percival MCP parados: AgentMail, Weather, OSM e Deep
  Research; versões/identidades abaixo. Os três primeiros e Deep Research têm
  labels de `server-id` do broker; não há label de consumidor.
- Esses quatro containers parados observam binds read/write para `/host`,
  `/host/boot`, `/host/home`, `/host/tmp`, `/host/var/log` e
  `/host/var/cache/pacman/pkg`, alinhados à política B14. Isto registra o
  contrato Docker observado, não solicita nem autoriza mudança de mounts.
- Um container descartável `percival-f2-engine27` está exited; imagens/tag de
  fixtures F1/F2, builds `ui-test`, imagens `localhost:5000/5001` e cópias de
  teste continuam presentes. **Nada foi removido:** retenção/limpeza fica fora
  do inventário e exige lista aprovada após reconciliação de referências.

| container | container ID | image ID | status / observação |
| --- | --- | --- | --- |
| `nanobot-gateway` | `7d429a786d8156378f66e639e51612cb4fca7d0c518e2764ec093d81ad5346c4` | `fb516d1469100fd7500a89a60fce1cd332575ebe0aae654210aa0c7a502891d5` | Up; gateway; host port 8765 em todas interfaces |
| `nanobot-percival-mcp-broker-1` | `6140857448bfbf50607c34812e67a5ea287f6c38647c67b00eb1969fc1726dd2` | `14fc47c55982077c3c093f69f449d6ca7335a8043479bdbd81b8028ae233cb3d` | Up, healthy; único serviço Percival com socket |
| `amazing_lumiere` | `772c21952ca12c23d7368ac13584fc83b29208705c1e9b465449ff8561eb55cc` | `f7acd7fa97c3201adb4c9fc26fc3be6e6cdac5c4a485e71a5ca9f1f9e11ac7c0` | Up; Positronic AgentMail |
| `sleepy_swanson` | `159fc40181dbce9d0bb086c48b26442671655422201ba85a46e5aa9e77a20c2a` | `f7acd7fa97c3201adb4c9fc26fc3be6e6cdac5c4a485e71a5ca9f1f9e11ac7c0` | Up; Positronic AgentMail duplicado |
| `priceless_rosalind` | `3bbeb9ca2efe1da4c7d0b85207519bbffba740009035096a2d596a7b1363db02` | `fa1e3cec8cd3c1423f87987f41c0d3c5f15505826953224924f015194c30ac99` | Up, unhealthy; Positronic Deep Research |
| `flamboyant_leavitt` | `8495da2d8ce124c80edc030b7794bd61d3916ad235a9b792f59c155a28f57877` | `fa1e3cec8cd3c1423f87987f41c0d3c5f15505826953224924f015194c30ac99` | Up, unhealthy; Positronic Deep Research duplicado |
| `percival-mcp-deep-research` | `7c316aabc88a9ddbc6ecda9929c7b5bdecd78630bf50dfae59756dc0a896042f` | `4882d99a41460c68ebbff893e736b8fce1715c5b972f99b7c62fafa26a151989` | Exited (143); broker |
| `percival-mcp-osm` | `07ebc17b9e0f2554817dbf9736ee92d3f649b58d3485b1108ae10cc31dad609e` | `53c8e3cfac1120cca0963e7bc01220ea53aa0c3a8d908609` | Exited (143); broker |
| `percival-mcp-weather` | `45eac8a44f184c4b8191976af11ec46b5787adb04ac32ee2ac8702aa4d7c710e` | `1f87321f15c4a607bcb555d970b7c18851605a4a5f0492a57c1e7af5b8f11cce` | Exited (255); broker |
| `percival-mcp-agentmail` | `ebd9d4c92b3d28cb651d5255b2936c02421d0bbfe2e20462d113c0b74950a86e` | `d4eb9e2e6f800c741d15703889719f1965575757546f0ee9fe03fd97e9c7b99e` | Exited (255); broker |
| `percival-f2-engine27` | `bc419f4b20b3f469cf3add8963ebebcce30adffde47f3b1d672f371cb529d8ef` | `aa3df78ecf320f5fafdce71c659f1629e96e9de0968305fe1de670e0ca9176ce` | Exited (0); disposable Engine fixture, left intact |

## Worktrees e versão declarada

SHAs abreviados são os HEADs lidos durante o inventário. Estado dirty/untracked
é resumido; esses arquivos preexistentes foram preservados.

| repositório | HEAD | versão no `pyproject.toml` | estado local observado |
| --- | --- | --- | --- |
| Percival `/home/bill/Projects/nanobot` | `0475065` | metadados do projeto ainda `nanobot-ai` | `.gitignore` modificado; plano e relatórios F0/diagnóstico não rastreados na leitura |
| Notes | `4db7ddb` | `0.1.5` | limpo |
| AgentMail | `e03781b` | `0.4.0` | `.gitignore` modificado |
| Weather | `b5032f4` | `0.9.0` | `.gitignore` modificado |
| Khan Calendar | `9fd1451` | `0.4.0` | `.gitignore` modificado; `.positronic/policy.json` e `project.json` não rastreados |
| OSM | `ca3c397` | `0.5.0` | `.gitignore` e `uv.lock` modificados; `.positronic/` e `AGENTS.md` não rastreados |
| Deep Research | `28e1c3d` | `3.0.1` | `.gitignore` modificado; `.positronic/` e `AGENTS.md` não rastreados |
| Positronic consumer (`alternative-positronic/positronic`) | `82bc487` | TypeScript; sem versão Python aplicável | limpo |

Os SHAs não provam a revisão embutida em cada imagem. Alguns Dockerfiles recebem
`GIT_SHA=local`/`unknown`, Weather não expõe version/revision OCI convencional,
Deep Research não expõe revision, e o gateway herda labels uv. Não vincular
esses artefatos a um checkout por suposição.

## Inventário de imagens de aplicação

`image ID` é a identidade observada. O Engine também devolveu RepoDigest local
com o mesmo hash para tags locais; isso não constitui evidência de push ou de
manifest digest em registry remoto. SemelVer vem dos manifests da fonte quando
indicado; alias/tag `dev`, `local`, `audit` e similares não são release.

| serviço | tags locais observadas relevantes | image ID observado | metadados efetivos relevantes |
| --- | --- | --- | --- |
| Notes | `positronic/notes:0.1.5-local`; `percival-notes-mcp:docker-test` | `a677143c5b249352658242863d174a01b5e856beb56179a9f4f4b6ea477ffe65` e `0e71715bef0f7d92251024eb1e686577c4fd5ed35daf87b873f5d44539a3c52c` | dois conteúdos; ID `a677…` está na registry Positronic, sem container ativo |
| AgentMail | `percival-agentmail-mcp:dev` | `d4eb9e2e6f800c741d15703889719f1965575757546f0ee9fe03fd97e9c7b99e` | OCI 0.4.0, revision `local-r2`, `linux/amd64`; cópia antiga em execução ID `f7acd7fa97c3201adb4c9fc26fc3be6e6cdac5c4a485e71a5ca9f1f9e11ac7c0`, OCI 0.0.0/unknown |
| Weather | `percival-weather-mcp:audit` | `1f87321f15c4a607bcb555d970b7c18851605a4a5f0492a57c1e7af5b8f11cce` | revision ausente; projeto declara 0.9.0; `linux/amd64` |
| Khan Calendar | `percival-khan-calendar:dev`; `positronic/khan-calendar:0.4.0-local` | `5cd6989b753f040733b42cdce71143f551ee6bb2b9e7c2639800c57039ea6ab0` e `01b960c604772a6e671686af8fdf5ccd7676c7564c7bf99af55f7c6a542fafbb` | a imagem `:dev` é 0.4.0/revision `local-test`; a outra é 0.0.0/unknown |
| OSM | `percival-osm:local` | `53c8e3cfacdde02e91bfde06df34bc15ff635d28acd52014cc6b0c3a8d908609` | version ausente, revision `5f80a41`; projeto declara 0.5.0 |
| Deep Research Percival | `percival-deep-research:dev`; `localhost:5000/percival/deep-research:3.0.1-5b68148-bench` | `4882d99a41460c68ebbff893e736b8fce1715c5b972f99b7c62fafa26a151989` e `15acf1c3f039ad78cced3ea69206c7a66e8df5e09261c5531a7398a0f4ab7271` | primeiro tem version 3.0.1, revision ausente; segundo idem |
| Deep Research Positronic | sem tag | `fa1e3cec8cd3c1423f87987f41c0d3c5f15505826953224924f015194c30ac99` | OCI 3.0.1, revision ausente; duas instâncias em execução |
| Gateway | `nanobot-nanobot-gateway:latest`, `:dev` | `fb516d1469100fd7500a89a60fce1cd332575ebe0aae654210aa0c7a502891d5`; `c45f7911b6767aa895f91a1b21d170d7ba4dd05d3b50915ef3eb1f6a032a003e` | imagem em execução identifica uv em vez de Percival; conteúdo em execução não é associado ao HEAD atual por esta evidência |
| Broker | `percival-mcp-broker:local` e tags temporárias `f2`, `ui-test`, `f5-*` | `14fc47c55982077c3c093f69f449d6ca7335a8043479bdbd81b8028ae233cb3d` em execução | local-only; identificadores de fixture/candidato preservados |

### Imagens temporárias/candidatas ainda presentes

Identidades distintas permanecem separadas mesmo quando os tags aparentam
representar a mesma revisão. Todas as referências abaixo foram observadas no
snapshot; nenhum fixture foi classificado como descartável.

| tags/repositório | image ID |
| --- | --- |
| `percival-f2-gateway:ui-test` | `7d30cd28d15e6fb93ef4499025610ab5e5ee67c0fedbb34bfb23449f9c314692` |
| `percival-mcp-broker:ui-test` | `a3c5384ff3d43350b514726afeae4c2be770de7999f1a761605d387f69c4bec3` |
| `percival-mcp-broker:f5-final` | `83d9137b74c93c5b926eb7f61b2bfb42d209b0e0a3835e68700c6f6a048adac2` |
| `percival-f5-final-gateway:local` | `2ae2e4e68a9dbd8723dac04f2da78823d11f520515a1c861e97a6f275171149f` |
| `percival-mcp-broker:f5` | `bfb90f4f7e02ef73d1d81c9ef73afd782b4d207715fa109eed48f65e294090df` |
| `percival-f5-gateway:local` | `b872f30bb12dc847322542aa631f149f49f5b7814c6455c45ee5d032ac0cf10b` |
| `percival-f2-gateway:dev` | `1341c6842f08e3353a68b1de633c3726db1730b342c78d7977ec4368ed7b6796` |
| `percival-mcp-broker:f2` | `5bcd9c8fbc8a283477f490f9ea823c2acc3e4603fd398cc5b7a317747c18ae9e` |
| `percival-f1-gateway:dev` | `80046b162bc636925bd78324818d7d053b755c80d6cbea683c190862135288f6` |
| `percival-f1-osm:source-5f80a41` | `40a01b1bc82104e300266c66656d50091b16b71a37b6cd9273d30311938bc980` |
| `percival-f2-osm:source-5f80a41` | `c956ade0aa55fff9904f9d1af2597a718de1b9dbe361b9008797186e9108bfb2` |
| `percival-f1-weather:source-996302b` | `7d9b94a1ca61d777e50953c79b3ac51d52dac81f97d57102374aec1f1336c640` |
| `percival-f2-weather:source-996302b` | `b309f8b0347fc35e1caa09c522937ae5711603b2803a6a77a9bbcfd30a215439` |
| `percival-f1-osm:source-ca3c397`, `localhost:5001/percival-f1/osm:source-ca3c397` | `d3f674b6e1dc6c420e85ed27b558fd88d33f9e3daffe8dd18d571a132327aeb7` |
| `percival-f2-osm:source-ca3c397` | `3c231f7534d63d65bb6e0a035c0c70c448a43bdb9b36587eaebf4aa3316bd888` |
| `percival-f1-weather:source-b5032f4`, `localhost:5001/percival-f1/weather:source-b5032f4` | `cc9f087fac1120cca0963e7bc56d5e7ccc515f939ba29fb5d1976d8938e1d4dd` |
| `percival-f2-weather:source-b5032f4` | `ceffd70433881e3e8709d4c8fb01220ea53aa8c3fa29274b43d2f5c4394e4fa0` |
| `localhost:5000/percival/deep-research:3.0.1-5b68148-bench` | `15acf1c3f039ad78cced3ea69206c7a66e8df5e09261c5531a7398a0f4ab7271` |
| `localhost:5000/percival/deep-research:<untagged>` | `973fecf4f38757b91d66411c7679245499ff1163d43ef6674d895d80cc82bc5d` |
| `percival-deep-research:smoke` | `9ae300f7a0a2470753c1b49de193f0a6a40f29538e6a534a7e8a32ad504cd0c6` |

Other local base/tool images present: `node:24-bookworm-slim`, `archlinux`
(untagged), `alpine:3.20`, `docker:27.5.1-dind`, `registry:2` and
`positronic-mcp-local-smoke:latest`. None is classified as disposable in F0.

## Consumidores e referência por `server_id`

### Percival broker

`~/.nanobot/config.json` declara `tools.mcpDocker` schemaVersion 1, revisão 4;
quatro servidores ativos por configuração, todos com source local-image:

| `server_id` | image ID fixado | container observado |
| --- | --- | --- |
| `agentmail` | `d4eb9e2e6f800c741d15703889719f1965575757546f0ee9fe03fd97e9c7b99e` | `percival-mcp-agentmail`, exited (255), label `server-id=agentmail` |
| `weather` | `1f87321f15c4a607bcb555d970b7c18851605a4a5f0492a57c1e7af5b8f11cce` | `percival-mcp-weather`, exited (255), label `server-id=weather` |
| `osm` | `53c8e3cfacdde02e91bfde06df34bc15ff635d28acd52014cc6b0c3a8d908609` | `percival-mcp-osm`, exited (143), label `server-id=osm` |
| `deep-research` | `4882d99a41460c68ebbff893e736b8fce1715c5b972f99b7c62fafa26a151989` | `percival-mcp-deep-research`, exited (143), label `server-id=deep-research` |

As quatro referências configuradas correspondem aos IDs completos vistos na
inspeção Docker. O status `active` é intenção de config; não implica container
em execução ou handshake atual.

### Positronic

`~/.positronic/mcp/registry.json` schemaVersion 2, revisão de entrada por
servidor: AgentMail (global/activated, revisão 12, `f7acd7fa…`), Khan Calendar
(global/activated, revisão 6, `01b960c6…`), Deep Research (global/activated,
revisão 12, `fa1e3cec…`) e Notes (local/activated, revisão 14,
`a677143c…`, atribuído a alternative-positronic e cevap-unesp). Não há entradas
Weather/OSM nessa registry.

Os containers aleatórios `amazing_lumiere` (AgentMail), `sleepy_swanson`
(AgentMail), `priceless_rosalind` (Deep Research) e `flamboyant_leavitt` (Deep
Research) usam exatamente as imagens AgentMail/Deep Research referenciadas pela
registry e montam, read-only, os arquivos de configuração de segredo
Positronic correspondentes. Portanto, o **consumidor Positronic está
comprovado**; porém a registry descreve uma entrada por servidor e há duas
instâncias Docker para cada um. Criador/ownership operacional de cada duplicata
e razão de coexistência permanecem não confirmados. Khan/Notes não tinham
container ativo no snapshot.

### Convenções atuais de labels

- Broker containers observados usam `percival.mcp-docker.server-id` para o
  serviço, mas não distinguem owner, gestor nem instance ID.
- Containers Positronic ativos não têm labels de identificação do servidor/
  gestor/container; mapeamento veio da imagem ID + bind config observado.
- OCI image labels são inconsistentes: AgentMail tem version/revision; Khan
  candidate sim, outra imagem obsoleta não; Weather sem conventional version /
  revision; OSM sem version; Deep Research sem revision; gateway herda uv.

## Decisões registradas para Gate F0

As decisões abaixo foram aprovadas pelo operador nesta conversa e formalizadas
em [`docs/Decisions/2026-10-09-docker-standardization.md`](../Decisions/2026-10-09-docker-standardization.md).
O plano continua sem autorizar publicação, push, release, deploy, mutação de
servidor real ou limpeza.

1. **Nome/tag local — aprovado:** manter service IDs/API existentes, usar
   repos locais `percival-<service>` e tags imutáveis
   `<semver>-<shortsha>`; manter `:dev` só como alias mutável de desenvolvimento.
   Prefixo `percival-` elimina a ambiguidade dos nomes atuais Positronic/Nanobot.
2. **Namespace/registry — local-only:** adiar registry público ou
   privado para decisão própria, sem login/push/pull. Isto segue o escopo e a
   governança atual.
3. **Plataforma — aprovado:** `linux/amd64` apenas nesta refatoração; ARM64 está
   fora do escopo atual.
4. **Lock gateway — aprovado:** o Dockerfile principal instala `.` sem lock versionado e
   `.gitignore` exclui `uv.lock`. Rastrear `uv.lock` com exceção explícita no
   ignore, e tornar o build locked incluindo dependências de canal de forma
   reproduzível.
5. **Khan `khal` — aprovado:** a imagem 0.4.0 não contém `khal`; quatro ferramentas CLI
   dependem do binário, e oito tools adapters funcionam sem ele. Incluir
   `khal` pinado na imagem para disponibilizar a superfície completa; aceitar
   crescimento estimado de ~150 MB e validar dependências de SO/licença e
   workspace persistente.
6. **API e porta 8765 — aprovado:** API sempre configurada/ativa com `api_key`
   obrigatória; host binding de 8765 e API em loopback por padrão. Exposição
   externa requer opt-in, auth, proxy/TLS e firewall explícitos.
7. **Labels container — aprovado:** preservar
   `percival.mcp-docker.server-id` por compatibilidade e padronizar junto a
   `percival.mcp-docker.owner`, `.managed-by` e `.instance-id`; usar valores
   explícitos `percival`/`positronic` para owner e broker/TUI manager conforme
   quem lança. Revisar se os labels devem ser aplicados por cada manager, sem
   presumir que o broker pode escrever labels em containers Positronic.

## Gate F0

- **Concluído:** worktrees, imagens (ID e RepoDigest separados), Compose, mounts,
  ports, init, health, labels e config sources foram inventariados sem conteúdo
  de credenciais.
- **Concluído:** consumers Percival/Positronic mapeados por referências de
  image ID/`server_id`/registry e binds correspondentes, sem inferência pelo
  nome aleatório do container.
- **Concluído:** decisões registradas na ADR vinculada acima: tags/names,
  platform `amd64`, lock, `khal`, API/binds e labels. Registry remoto fica
  adiado por governança e escopo.
- **Acompanhamento para F6, antes de cleanup/cutover das duplicatas:** registry
  e mounts comprovam Positronic como consumer das duas instâncias AgentMail e
  duas Deep Research, mas não explicam por que há duas instâncias por servidor.
  Não matar ou remover nenhuma para investigar.
- Nenhuma imagem/contêiner foi removido ou mutado. Containers/imagens antigos,
  aliases ambíguos, Worktrees dirty e recursos de fixture permanecem intactos.
