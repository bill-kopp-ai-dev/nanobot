# F3 — remediação local e triagem de findings

- **Data:** 2026-10-10 UTC.
- **Estado:** candidatos reconstruídos e triados localmente; **a pendência #1
  do plano é fechada pelo critério "documentação e triagem completas"** — o
  resíduo (Critical `CVE-2026-60002` no gateway e ausência de Actions remotas
  nos SHAs candidatos) é tratado pela pendência #11 do plano
  [`2026-10-09-docker-standardization-refactor-plan.md`](../plans/2026-10-09-docker-standardization-refactor-plan.md).
  Nenhum waiver foi aprovado, nenhum commit/push foi feito e nenhum
  consumidor foi alterado nesta execução.
- **Plano:** [padronização Docker, F3](../plans/2026-10-09-docker-standardization-refactor-plan.md#f3--reprodutibilidade-contextos-e-postura-base).
- **Política:** [postura e manutenção de imagens Docker](../Decisions/2026-10-09-docker-image-posture-policy.md).
- **Scanner:** Trivy 0.67.2,
  `aquasec/trivy@sha256:ac2f9d0197456a8ce460884b113e49d65b667f506c31d014c9955869a7a5d682`.
  Rescan executado em 2026-10-10T13:06–13:09Z usando uma mesma cache DB; target
  `linux/amd64`. Vulnerability DB metadata:
  `UpdatedAt=2026-10-10T07:01:36.894063512Z`,
  `DownloadedAt=2026-10-10T13:07:05.12596446Z`. O JSON registra timestamp,
  imagem e DiffIDs; metadata da DB está em `trivy-cache/db/metadata.json`.
- **Artefatos integrais:** scans e SBOM CycloneDX estão em
  `/home/bill/.positronic/runtime/tmp/opencode/trivy-reports/`; hashes SHA-256
  e IDs estão abaixo. Esses arquivos temporários não foram adicionados ao Git.

## Candidatos examinados

Todos os oito candidatos foram reconstruídos por
`scripts/percival-docker-build.py` em 2026-10-10, com SHA base, diff hash e
image ID explícitos. Os seis MCPs, gateway e broker têm alterações locais
identificadas por hash; são artefatos de validação, não imagens publicáveis.

| Imagem/tag local | SHA de fonte | `sourceDiffSha256` (prefixo) | Docker image ID (`inspect`) | Trivy Critical / High |
|---|---|---|---|---:|
| Notes `percival-notes-mcp:0.1.5-b66e897-f3-84f429e065d5` | `b66e897b276b038d0e6ea4f602fd1e6c0e96a3ca` | `84f429e065d5` | `sha256:d406b51657c3bcfaadbe3a373d7b21ce57cc71544f974d1221d0bb7e97bdeda1` | 0 / 44 |
| AgentMail `percival-agentmail-mcp:0.4.0-34312b9-f3-91a24f005774` | `34312b9966efb946a7fb16ea53c205bf4abb71c9` | `91a24f005774` | `sha256:1fa2ca61c3685e8f0a7a33993d5e4d8b4ba8546c75ccec817fe5d010616d9fb4` | 0 / 44 |
| Weather `percival-weather-mcp:0.9.0-94c7fde-f3-c0ae6523cf2f` | `94c7fdeffdb02f738ceee6dd8ae246736ac803f4` | `c0ae6523cf2f` | `sha256:e75fdd4abc8a0e34a76ff7fea790bffc4b4a7681396cccc393038b6478600aa6` | 0 / 44 |
| Khan `percival-khan-calendar:0.4.0-d8d4122-f3-2500221a747e` | `d8d412255c4b556e228572ad3c30dd1c06e4c01f` | `2500221a747e` | `sha256:55cd5a038d22e253693d1d0681e108f57b41f060ecbeb231dad3e2f7edd51914` | 0 / 44 |
| OSM `percival-osm:0.5.0-311a49d-f3-c71c69ddb5b2` | `311a49da1f05c13060fdb0cd3ce01ca1d08fc585` | `c71c69ddb5b2` | `sha256:67f8ada639897af9ca4ca8f02e38932376f73f454db76028a3920f076011cfeb` | 0 / 44 |
| Deep Research `percival-deep-research:3.0.1-9e8272b-f3-608be1420abd` | `9e8272be8dd728ad132f030c361a7447147cacb2` | `608be1420abd` | `sha256:265891c14514c809e9c05587549631426ef080219c03fde21e5d703623d3793d` | 0 / 44 |
| Gateway `percival-gateway:0.3.5-ed07024-f3-672a08bf4531` | `ed070244f6b94140248f407293a61a8b9f1959f6` | `672a08bf4531` | `sha256:c6a1498c06b84737595173bb9a7b7c441ad461447f984c87728257b80929da28` | 1 / 64 |
| MCP broker `percival-mcp-broker:0.3.5-ed07024-f3-672a08bf4531` | `ed070244f6b94140248f407293a61a8b9f1959f6` | `672a08bf4531` | `sha256:27cbfbcba34405de261296f54fb7b6cf6e8920b10dffcb789b384122d8008b83` | 0 / 0 |

Total scan observations are **1 Critical and 328 High** (findings per image,
not unique CVEs). The Critical/High sets are unchanged for the base-system
findings; Deep Research no longer reports `CVE-2026-81726` after NLTK was
excluded from its runtime. Each full scan and CycloneDX file is listed below
with SHA-256; all are local temporary evidence, not committed artifacts.

| Nome | SHA-256 do scan JSON | Componentes SBOM | SHA-256 do SBOM CycloneDX |
|---|---|---:|---|
| Notes | `a3e89e8e2e819639951959baf8aabf942e2f43cf39ff1ed79513ad3e12433bf7` | 129 | `645db7654df2a14b11416a88187bff698df59a7c29221990307dc78830809c8c` |
| AgentMail | `baa14352099c0348e79e4175ca590f6a53c30fa6bc5e5e0aea170b765ba4b3bd` | 131 | `dbc60ed1aa438edd04885c9463be9db28d3a572b100b3a867f4c66c892b7b787` |
| Weather | `4a15dfebf9154be1c13a962438fa8c788d11ebb5361f5bdc66dc319c01f48f6e` | 130 | `f30dbc2b32e56cc6d5c8a44d53a9d885d705c7942d62ff297a58b6b363fec560` |
| Khan | `368ce734f5f6890bbf96d905a9f7fe4c9f2b18d776c54d68c867feb8c2a436e5` | 174 | `15167c82dee927ea5c9be41ea8d87724331179f94a77779ab700d321a05202e4` |
| OSM | `251c8126b9c79600c3275299d2016a1dafee34bcf19e9ddbaa25c7253be2720a` | 132 | `a6d58e00bfbbb59e2954c61b4d35b50afbfe20774e30a94005e5f567c9c7b039` |
| Deep Research | `83d6cb74a732c5fef512d352e8ed34a284929bc854fe8e7fb167ab174d1fbd11` | 326 | `00c7de4d892675a7c642d85d9b72b8e78c02a0c88825dbb55ad9f3333510faad` |
| Gateway | `3c6c30480fa6377a004d9f4e06546fe2efcf49551f87ebbede3ce43ad898fd17` | 260 | `c0b88d8be5d7ba0b5a422ab43a50afce2547dcff861c80767d093d46e028b616` |
| Broker | `0e1e97936eee886132655e65a48ac9dab99ea64d2db1d57bf8cf8cd2fbe0bce3` | 49 | `7a08daae579303307bac52520e7b87079310bdf2f36204fc11dbd926d0b3bfcd` |

## Remediações e verificações

- **Broker:** `Dockerfile.mcp-broker` agora usa Docker CLI 29.9.0 de base
  digest-pinned, copia somente `/usr/local/bin/docker` para Python 3.12 Alpine
  fixado e deixa de carregar os plugins Buildx/Compose e utilitários do container
  Docker upstream. O scan caiu de 5 Critical/132 High no candidato anterior para
  **0/0**. O broker candidate executou `docker version` contra Engine 27.5.1
  descartável e retornou `Client=29.9.0 | Server=27.5.1`. `pytest
  tests/mcp_docker`: **72 passed**; runtime Python 3.12.15, Pydantic 2.13.5 e
  Docker CLI 29.9.0 confirmados. Nenhum socket do host foi exposto ao teste.
- **Deep Research:** `uv.lock` atualizou `urllib3` 2.7.0→2.8.0,
  `weasyprint` 69.0→70.0 e resolveu `jaraco-context` em 6.1.2; a imagem real
  contém essas versões. `wheel` vulnerável só aparecia embutido no setuptools do
  Python base; o Dockerfile remove o setuptools global não usado, mas mantém o
  setuptools 83.0.0 do venv. O runtime deixou de instalar `curl`; Compose e
  smoke usam `http.client`. O Dockerfile também exclui NLTK, transitiva não
  importada pelo código do projeto. No ambiente temporário sem NLTK: **414
  passed, 3 skipped**; smoke da imagem recém-construída confirmou que NLTK não
  está instalado, todos os cinco tools aparecem no handshake stdio e `/health`
  respondeu `200 healthy` em loopback. Scan atualizado: 44 High, sem finding
  `CVE-2026-81726`. O container HTTP de teste foi parado após a verificação.
- **OSM:** o runtime deixou de instalar `curl`; Compose e smoke usam
  `http.client`. `uv run pytest -v`: **75 passed**; Compose config passou com
  os envs exigidos; um container HTTP isolado, sem rede e com a nova probe ficou
  `healthy`. No candidato recém-reconstruído, `initialize` + `tools/list`
  sequenciais passaram com 37 tools, incluindo `osm_find_nearby`. O script legado
  `docker-smoke-test.sh` ainda envia `initialize` e `tools/list` em pipeline sem
  aguardar a resposta de initialize e acusa `osm_find_nearby` ausente; o mesmo
  tool está registrado no código e aparece no handshake sequencial correto.
  Ruff integral do OSM reporta 99 findings preexistentes em código/testes fora
  desta alteração; o AGENTS do repo define pytest como verificação canônica.
   Scan: 54→44 High.
- **Gateway:** o digest da base UV foi atualizado para
  `sha256:41eb228142f776ed8df9e51fba89ee31f018c04a0452645c014783546b164c03`.
  A imagem runtime contém `urllib3==2.8.0`, sem `msgpack` nem setuptools no venv
  ou no Python global. Mesmo assim, Trivy reporta msgpack 1.1.2, setuptools
  70.3.0 e urllib3 2.7.0 sem `PkgPath` e emite aviso de terceiro SBOM impreciso;
  inspeção direta nos interpretadores do venv e do sistema confirma ausência de
  msgpack/setuptools globais e `urllib3==2.8.0` somente no venv. Registrei no
  OpenVEX avaliações limitadas a este image ID: `not_affected` para CVEs de
  `sshd` ausente, msgpack e setuptools ausentes, e para as duas CVEs de urllib3
  cujo runtime está na versão fixa. O Trivy raw scan continua contando esses
  achados; a supressão/consumo CI da VEX e a reconciliação do terceiro SBOM ainda
  precisam ser reproduzidos no builder limpo.
- **Hardening Debian aplicado e verificado nos sete candidatos Debian** (seis
  MCPs e gateway): `/usr/bin/mount` está mode 755, sem setuid; `/usr/bin/nsenter`
  e `/usr/bin/infocmp` estão ausentes. Este hardening não remove as bibliotecas
  vulneráveis e, por si só, não supre a avaliação VEX/revisão de reachability.
- **OpenSSH Forky:** `debian:forky-slim` instalou `openssh-client 1:10.5p1-1`
  (`OpenSSH_10.5p1 Debian-1`). Um teste local client/server com chave ed25519
  autenticou e executou comando com sucesso. É evidência da versão corrigida e
  de interoperabilidade básica do OpenSSH 10.5; não é build do gateway em Forky
  nem valida a integração Percival Remote SSH sob essa distro. O gateway atual
  permanece Trixie/OpenSSH 10.0p1 e o Critical continua bloqueando.

As seis avaliações VEX locais para o gateway estão em
[`2026-10-10-f3-openvex.json`](2026-10-10-f3-openvex.json). São declarações
restritas ao image ID `sha256:c6a1498c…`; não são waivers, não se estendem a
outros candidates e ainda dependem de validação equivalente no builder CI.

### Notas F3 por servidor MCP

Para que cada repositório carregue seu próprio espelho do status F3 e possa
tratar os blockers remanescentes de forma isolada, esta seção lista as notas
já publicadas (commit local, sem push) em cada projeto. As notas referenciam
este relatório como fonte canônica e citam o SHA, o image ID e os hashes dos
artefatos de scan/SBOM correspondentes. Cada nota foi registrada com
Conventional Commits (`docs(issues):` ou `docs(security):` para o AgentMail
cujo `.gitignore` reserva `docs/issues/` para rascunhos locais).

| MCP | Caminho no repositório do MCP | SHA do commit | Caminho equivalente no gateway |
|---|---|---|---|
| Notes | `docs/issues/2026-10-10-f3-status.md` | `ab0f07d` | `percival-notes-mcp` |
| AgentMail | `docs/security/f3-status.md` | `d2d6458` | `percival-agentmail-mcp` |
| Weather | `docs/issues/2026-10-10-f3-status.md` | `9746453` | `percival-weather-mcp` |
| Khan | `docs/issues/2026-10-10-f3-status.md` | `7f6bd4f` | `percival-khan-calendar` |
| OSM | `docs/issues/2026-10-10-f3-status.md` | `3588a45` | `percival-osm` |
| Deep Research | `docs/issues/2026-10-10-f3-status.md` | `1db41fc` | `percival-deep-research` |

Nenhuma das notas altera Dockerfiles, dependências, consumidores ou política
de release. Os commits permanecem locais até o operador autorizar o push.
- **Percival:** `uv sync --locked --all-extras` e o instalador com hash de todos
  os channel manifests prepararam um ambiente temporário fora do repo. `pytest`:
  **9313 passed, 49 skipped**; `basedpyright nanobot`: **0 errors/warnings/notes**;
  `ruff check .`: **All checks passed**. O primeiro teste executado antes de
  instalar os extras dos canais falhou por falta de `nh3`; foi repetido com os
  channel manifests e passou. Nenhuma alteração foi feita no `.venv` protegido
  do checkout.

## Findings remanescentes e aplicabilidade

Cada um dos seis MCPs Debian tem 44 High distribuídos por oito CVEs de pacote
base. Deep Research deixou de reportar `CVE-2026-81726` depois da exclusão do
NLTK. Gateway tem 1 Critical e 64 High brutos, dos quais seis receberam
avaliações OpenVEX limitadas ao image ID atual. Broker não tem Critical/High.

Verificações sobre os candidatos Debian confirmaram: nenhum contém
`systemd-homed` nem `sshd`; nenhum dos seis MCPs contém `Archive::Tar`, mas o
gateway contém. Nos candidatos recém-construídos, `/usr/bin/infocmp` e
`/usr/bin/nsenter` estão ausentes e `/usr/bin/mount` está mode 755 (sem setuid).
Os seis MCPs usam UID não-root e `CapEff=0000000000000000` no container; o
entrypoint do gateway cai para UID 1000 via `setpriv`, também com
`CapEff=0000000000000000`.
A imagem OSM adicionalmente usa `cap_drop: ALL` em Compose.
Isso sustenta reavaliação de aplicabilidade, mas **não é um waiver** nem altera o
resultado do scanner.

| CVE / pacote | Evidência primária e avaliação local | Estado / decisão necessária |
|---|---|---|
| `CVE-2026-60002` / `openssh-client 1:10.0p1-7+deb13u4` no gateway | Debian Trixie ainda vulnerável; o teste Forky confirmou que a linha 10.5p1 oferece client/server local funcional. O gateway usa OpenSSH para Remote SSH, então não é não-aplicável. | **Critical não resolvido.** Próximo passo é build isolado do gateway numa base Forky e testes Percival Remote SSH; se tecnicamente impraticável, solicitar decisão de waiver individual (não aprovada). |
| `CVE-2026-59999`, `CVE-2026-60000` / OpenSSH | As descrições do tracker são falhas do servidor `sshd`; o gateway contém somente `openssh-client`; `/usr/sbin/sshd` está ausente. | VEX `not_affected` por componente ausente registrado para o image ID exato em [`f3-openvex`](2026-10-10-f3-openvex.json); confirmar a mesma ausência no builder CI. Não se aplica a outros digests. |
| `CVE-2025-69720` / ncurses | Debian descreve overflow em `infocmp`; o binário está ausente nos sete candidatos Debian após rebuild. As bibliotecas ncurses permanecem instaladas. | Candidato a `vulnerable_code_not_present` para a falha de `infocmp`; verificar componente/caminho afetado e formalizar VEX antes de excluir o High. |
| `CVE-2026-16742` / libsystemd/libudev | Debian descreve LPE em `systemd-homed`, classifica Trixie `<no-dsa> (Minor issue)`; executável/serviço `systemd-homed` não está instalado. | Forte candidato a `vulnerable_code_not_present`; registrar VEX por imagem e verificar no builder CI. |
| `CVE-2026-54369` / libacl | Symlink traversal nas funções `acl_*_file` com caller privilegiado; Debian diz Trixie vulnerável, sem backport individual. MCPs executam non-root; gateway só executa trecho root de ownership antes de iniciar o runtime non-root. | Triage de alcance privilegiado ainda precisa de decisão registrada; continua scanner High. |
| `CVE-2026-76642`, `CVE-2026-78408/09/10` / util-linux | Os advisories descrevem fluxos privilegiados de `mount`/`nsenter`, `fstab` ou acesso a cgroups; Debian marca Trixie vulnerável com `<no-dsa> (Minor issue)`. Nos sete runtimes, `mount` não é setuid, `nsenter` está ausente; processos MCP non-root não têm `CAP_SYS_ADMIN`. | Hardening reduz os caminhos privilegiados e os binários afetados, mas os pacotes/libs vulneráveis continuam presentes. Exige VEX por CVE com revisão de reachability e confirmação no builder CI; não atribuir como resolvido só pelas mudanças de modo/remoção de executáveis. |
| `CVE-2026-9538` / Perl Archive::Tar | Debian Trixie lista o problema como `postponed (Minor issue)`. `Archive::Tar` ausente nos MCPs, presente no gateway. | N/A provável nos MCPs; no gateway, remover ou limitar a biblioteca se funcionalmente dispensável, ou solicitar waiver individual. |
| `CVE-2026-81726` / NLTK 3.10.3 | NLTK foi excluído com `uv sync --no-install-package nltk`; imagem runtime verificada sem módulo; suite sem NLTK passou 414 testes e smoke da imagem passou. | **Remediado no candidato Deep Research atual**; ausente no novo scan. Manter a exclusão e rescan após qualquer alteração de lock/base. |
| CVEs de curl/GnuTLS em OSM/Deep | Debian lista Trixie vulnerável; os Dockerfiles não precisam mais do curl CLI porque o único uso era healthcheck. As duas imagens atuais não contêm `/usr/bin/curl` nem `libcurl.so*`; as probes seguem funcionando com Python. | **Remediados localmente**; o High caiu 10 em OSM e 15 em Deep Research após a soma das atualizações Python, remoção do curl/libcurl e retirada do setuptools/wheel base não usados. |
| Findings Python no gateway vindos do terceiro SBOM | Trivy reporta `msgpack 1.1.2`, `setuptools 70.3.0` e `urllib3 2.7.0` sem `PkgPath`. Execução do Python do venv e do sistema mostra msgpack/setuptools ausentes; o venv contém `urllib3==2.8.0`, a versão fixa nos dois advisories citados. | Seis declarações VEX restritas ao image ID atual registram os dois componentes ausentes, urllib3 corrigido e CVEs do sshd ausente. Continuam findings brutos até reprodutibilidade no builder CI e reconciliação da SBOM de terceiro. |

Fontes Debian primárias: [CVE-2025-69720](https://security-tracker.debian.org/tracker/CVE-2025-69720),
[CVE-2026-16742](https://security-tracker.debian.org/tracker/CVE-2026-16742),
[CVE-2026-54369](https://security-tracker.debian.org/tracker/CVE-2026-54369),
[CVE-2026-76642](https://security-tracker.debian.org/tracker/CVE-2026-76642),
[CVE-2026-78408](https://security-tracker.debian.org/tracker/CVE-2026-78408),
[CVE-2026-78409](https://security-tracker.debian.org/tracker/CVE-2026-78409),
[CVE-2026-78410](https://security-tracker.debian.org/tracker/CVE-2026-78410),
[CVE-2026-9538](https://security-tracker.debian.org/tracker/CVE-2026-9538),
[CVE-2026-81726](https://security-tracker.debian.org/tracker/CVE-2026-81726),
[CVE-2026-12064](https://security-tracker.debian.org/tracker/CVE-2026-12064),
[CVE-2026-59999](https://security-tracker.debian.org/tracker/CVE-2026-59999),
[CVE-2026-60000](https://security-tracker.debian.org/tracker/CVE-2026-60000) e
[CVE-2026-60002](https://security-tracker.debian.org/tracker/CVE-2026-60002).

## Próximos passos para fechar F3

1. Build isolado do gateway sobre Debian Forky (ou atualizar Trixie quando houver
   pacote corrigido compatível) e executar testes Percival Remote SSH com
   OpenSSH >=10.4; depois regenerar candidato, scan e SBOM. Se não houver caminho
   tecnicamente viável, pedir ao operador waiver específico de `CVE-2026-60002`.
   → **Executado em 2026-10-24 (D6):** ver §Fechamento da D6.
2. Registrar VEX/decisão por imagem para os CVEs de pacote base, distinguindo
   `not_affected` comprovado de risco aceito. Não aprovar waiver blanket para
   “Debian Trixie”.
3. Resolver a discrepância do SBOM Trivy no gateway: scan atual ainda apresenta
   findings Python sem `PkgPath` e aviso de SBOM de terceiro impreciso; comparar
   com rootfs e SBOM CycloneDX e documentar uma fonte reproduzível.
   → **Resolvido em 2026-10-24 (D6):** a fonte reproduzível era o SBOM
   vendorizado do `pip` 25.0.1 (`pip/_vendor/bom.cdx.json`), que declarava
   msgpack 1.1.2, setuptools 70.3.0 e urllib3 2.7.0. Removendo o `pip` do
   runtime, o artefato desapareceu na origem.
4. Levar os diffs necessários a commits/candidatos aprovados; rodar builds limpos,
   SBOM/scan e CI GitHub nos SHAs exatos. `gh auth status` em 2026-10-10
   confirmou que a CLI não está autenticada em nenhum host GitHub; execuções
   remotas aguardam autenticação do operador. Esta execução local não satisfaz o
   builder CI nem F5.
5. Só então avaliar fechamento de F3. Nenhum desses passos autoriza alterar pins
   de consumidores, cutover, push ou release.

## Fechamento da D6 — gateway em Debian Forky (2026-10-24)

Esta seção fecha a pendência #11a sobre o resíduo OpenSSH do gateway. **Não
altera o histórico acima**: as triagens, contagens e OpenVEX de 2026-10-10
pertencem aos image IDs que analisaram.

- **Decisões do operador:** reconstruir o gateway em base Debian Forky
  (recomendado) e absorver no mesmo rebuild os advisories Python adicionais.
- **Candidato final:** `percival-gateway:0.1.0-92eeff9`, revisão
  `92eeff90cdb81c27c80ff239e84325021b9bd840`, image ID
  `sha256:1ad324379fa94b8e7b4768f703ea10213eda0986c4b4a3e8e9bb70de486f0368`,
  `linux/amd64`, construído por `scripts/percival-docker-build.py` com
  provenance limpa (`worktree: clean`).
- **Base:** `debian:forky-slim@sha256:4cee6ff3…`, snapshot Debian
  `20261020T000000Z`, `openssh-client=1:10.6p1-1`
  (`OpenSSH_10.6p1 Debian-1`). Python 3.12.12 e uv 0.9.30 preservados.

### Remediação do Critical e do resíduo do scanner

`CVE-2026-60002` era um resíduo estrutural: Trixie e Trixie-backports não
têm pacote corrigido, e o `1:10.6p1-1` do Forky exige `glibc >= 2.42`, que o
Trixie (2.41) não carrega. Trocar só o `.deb` do OpenSSH sobre Trixie é
impossível; a base runtime inteira migrou para Forky.

O primeiro build já corrigido, `percival-gateway:0.1.0-b49dd8b`, zerou o
Critical, mas ainda reportava **4 High** vindos de msgpack 1.1.2, setuptools
70.3.0 e urllib3 2.7.0 (dois advisories). A origem reproduzível era o SBOM
vendorizado do `pip` 25.0.1 (`pip/_vendor/bom.cdx.json`), que o Trivy lia como
pacotes instalados da imagem — o `pip` 26.2.2 do venv não tem esse arquivo, e
é por isso que os achados não traziam `PkgPath`.

Em vez de emitir waiver, o `pip` foi removido na origem: do interpretador do
sistema, do venv (criado sem `--seed`) e da wheel de `ensurepip`. O `uv`
instala as dependências travadas e `optional_features.install_extra` já
recorre a ele quando o `pip` está ausente. **Achado adicional nesta rodada:** os
channel locks mantinham `pillow==12.3.0` e `certifi==2026.7.22` porque o
`uv pip compile` preserva as versões já fixadas no arquivo de saída — recompilar
nunca as avançava, e habilitar um canal reinstalava as versões vulneráveis no
runtime. Causa corrigida (`--upgrade-package` em
`scripts/compile_channel_locks.py`) e locks re-resolvidos para esses dois
pacotes.

### Evidência do candidato final

| Verificação | Resultado |
|---|---|
| Scan Trivy 0.67.2 do candidato final | **0 Critical, 0 High, 1 Medium** (`CVE-2026-49138` / `nanobot-ai` 0.1.0, cujo fix upstream `545294c62` é ancestra de `HEAD` e cujo código do gateway é mais forte) |
| SBOM CycloneDX (syft) | 6129 componentes |
| Regressão Remote SSH dentro da imagem | **5/5 PASS** — versão do cliente, ausência de `openssh-server`, scan de host key, probe de credencial, túnel de transporte, contra um `sshd` em fixture separado |
| Smoke I2 runtime (gateway + broker) | **19/19 PASS**, incluindo SIGTERM, init, caps, recreation/hydrate do broker e UID alternado |
| Suíte do core | 8459 passed, 66 skipped, 2 falhas pré-existentes (`test_session_absolute_ttl_present`, `test_every_runtime_channel_field_has_a_webui_contract`) |
| `compile_channel_locks --check` | 13 manifestos travados verificados |

O OpenVEX reemitido para este image ID está em
[`2026-10-24-d6-openvex.json`](2026-10-24-d6-openvex.json) — oito declarações
`not_affected` restritas a `sha256:1ad32437…`: `CVE-2026-60002` (cliente
corrigido), `CVE-2026-59999` e `CVE-2026-60000` (`sshd` ausente), msgpack e
setuptools (componentes ausentes), as duas CVEs de urllib3 (runtime na versão
2.8.0) e `CVE-2026-49138` (o SSRF de redirect do `web_fetch`: o fix upstream
`545294c62` é ancestra de `HEAD` e o código shipped é mais forte — redirects
manuais com `follow_redirects=False`, validação de cada hop, DNS resolvido e
fixado por requisição). **Não é waiver** e não se estende a outros image IDs.

### Análise por imagem dos seis MCPs — sem extensão do VEX do gateway

O critério da D6 exige que o OpenVEX do gateway **não** seja estendido aos MCPs
sem análise por imagem. Cada MCP foi escaneado e inspecionado separadamente.
**Conclusão: nenhuma declaração do gateway se aplica a estas imagens**, porque
todas as seis são Debian 13 (Trixie), não contêm `openssh-client` nem `sshd`,
e cada uma carrega o seu próprio `pip` 25.0.1 (Deep Research, `pip` 24.0) com
o mesmo SBOM vendorizado.

| Imagem | Image ID | Revisão | OS | `sshd` | `certifi` | Critical | High |
|---|---|---|---|---|---:|---:|---:|
| Notes `0.1.5-78c2810` | `sha256:5a802a63…` | `78c2810` | Trixie | ausente | 2026.7.22 | 1 | 44 |
| AgentMail `0.4.0-54461f4` | `sha256:7f8a2ab5…` | `54461f4` | Trixie | ausente | 2026.7.22 | 1 | 44 |
| Weather `0.9.0-b5dd4eb` | `sha256:6da5d43f…` | `b5dd4eb` | Trixie | ausente | 2025.1.31 | 1 | 44 |
| Khan `0.4.0-ce69267` | `sha256:b7d56ee4…` | `ce69267` | Trixie | ausente | 2026.7.22 | 1 | 44 |
| OSM `0.5.0-55aa673` | `sha256:bb88ae35…` | `55aa673` | Trixie | ausente | 2025.1.31 | 1 | 44 |
| Deep Research `3.0.1-e076f29` | `sha256:bad6defa…` | `e076f29` | Trixie | ausente | 2026.7.22 | 12 | 94 |

Os Criticals são `GHSA-6q48-6c7w-9gw2` (`certifi` com as raízes emSign
comprometidas) em todas as seis, mais `pillow 12.3.0` e `brotli 1.2.0` no Deep
Research. **Nenhum waiver foi emitido para nenhuma delas**: os `uv.lock` dos
seis repositórios MCP ainda fixam `certifi` 2026.7.22/2025.1.31, `pillow`
12.3.0 e `brotli` 1.2.0. A remediação é do D8, em cada repositório. As imagens
analisadas também estão **atrasadas em relação ao HEAD** dos respectivos
repositórios (divergência de revisão em todas as seis), o que reforça que
qualquer avaliação final exige reconstrução a partir de commit limpo.

### Limitações e estado

- **A D8 continua aberta:** este candidato é local. Promoção, canário, rollback,
  retenção do par A/B e a publicação limpa dependem de checkout limpo e
  aprovação do operador, sob a D8.
- **O gateway não foi promovido nem publicado**; nenhum registry foi tocado.
- **O broker não foi alterado** na D6: o smoke I2 reusou o broker
  `percival-i2-broker:ses-e96f9440`, e o contrato do broker segue coberto pela D7.
- **Os 44 High de base dos MCPs** (oito CVEs de pacote Debian) seguem sem
  avaliação por imagem; a avaliação por imagem feita aqui cobre o Critical de
  `certifi` e o resíduo OpenSSH, não o conjunto de base.
- **O `CVE-2026-49138` do próprio `nanobot-ai` 0.1.0** permanece como Medium no
  scan: o fix upstream está presente no código e o código vigente é mais
  forte, mas o scanner reporta pela versão do pacote. É finding do próprio
  produto, não do runtime — e é por isso que ele **não** é uma pendência da
  D6: o que a D6 tinha de fechar era o resíduo OpenSSH e o Critical de
  `certifi`. A reavaliação do `CVE-2026-49138` está registrada como
  statement `not_affected` no OpenVEX do image ID final, e a versão do
  pacote pode ser elevada em release própria, fora deste plano.
