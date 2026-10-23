# Fechamento da padronização Docker — F4/F5/F7

- **Preparado em:** 2026-10-23, por fusão dos dois planos de fechamento da padronização
  Docker: o [F4/F5](closed/2026-10-10-f4-f5-closure-plan.md) e o
  [F7 — aceite de operação](closed/2026-10-10-f7-operations-acceptance-closure-plan.md).
- **Estado:** abertura, com itens **reverificados contra o código em 2026-10-23**. A evidência de
  restore e rollback de F4 existe; nenhum item abaixo foi executado por este plano. A reverificação
  não fechou item algum, mas reduziu o escopo de D4, D7, D8, D9 e D11, corrigiu a premissa de D3 e
  **reescreveu D10**, cujo objeto não existe nesta máquina. Veredictos e evidência `arquivo:linha`:
  [auditoria planos × código](../reports/2026-10-23-auditoria-planos-vs-codigo.md) §3.4.
- **Plano de fase de origem:** [padronização Docker](2026-10-09-docker-standardization-refactor-plan.md),
  seções F4, F5, F7 e F8. Este plano substitui os dois planos de fechamento e passa a ser a
  fonte de verdade do quadro de pendências, hoje desatualizado no plano de fase.
- **Autoridade:** não autoriza reescrita de histórico, push, remoção de containers/imagens,
  rotação de credencial pelo agente, alteração de allowlist ativa, deploy em VPS, tag ou
  publicação. Cada mutação real exige a autorização aplicável e a interface suportada.
- **Numeração:** neste documento, F4/F5/F7 designam sempre as fases do plano de **padronização**
  Docker. As fases homônimas do plano MCP Docker first-class (arquivado) são outras e estão
  consolidadas no [plano integrado](2026-10-23-integracao-pendencias-kg-e-mcp-docker-plan.md).
- **Revisão IaC (2026-10-23):** [I1–I9](2026-10-23-iac-alignment-execution-plan.md)
  tratam distribuição, contratos e handoff IaC. D1–D12 continuam donos das pendências
  locais abaixo; atualização de plano não é execução nem aceite público.

### Contratos de integração aplicáveis a D1–D12

- Docker Hub é o alvo das imagens oficiais abertas, não escolha ainda livre de registry;
  namespace/nomes públicos e publicação dependem de I1/I3/I5/B13. CI de conformance C1
  não faz push. Tags locais/IDs permanecem úteis, sem substituir digest OCI publicado.
- `0.1.0` é a primeira versão pretendida já decidida; metadado herdado `0.3.5` deve ser
  alinhado em I1 antes da distribuição. D2/D8 preservam rastreabilidade, não renomeiam
  pacote/paths nem reescrevem histórico.
- Runtime real é gateway/manager + broker separado. Compose controla core; manager
  controla MCPs e exporta `capabilities.lock`; tooling IaC controla `deployment.lock`.
  D4/D10/D11 devem preservar essa fronteira, sem duplicar gestão por Compose/WUD.
- I4/C2 aprovam o destino de estado no layout `/srv/pblabs/`, mapeando `~/.nanobot` e
  a proposta `.percival` sem migrar automaticamente. D7/D9 validam paths/UID/GID reais,
  incluindo token e coberturas; `chmod 777` de fixture não é política de instalação.
- D6 exige avaliação do candidato exato, não contagem de vulnerabilidades de imagem
  antiga. Fechar triagem F3 não concede waiver nem revoga a política Critical/High.
  D7 verifica usuário efetivo e probes por modo; não exige HTTP healthcheck na CLI.
- D9 cobre o manual MCP; I8 cobre recuperação do core e estado completo, incluindo
  auth/KG/workspace/locks. Aceite local D12 não fecha integração IaC I9, publicação ou
  gates de outro produto. Se um contrato mudar, revalidar só as evidências afetadas.

## 1. Evidência já produzida (não refazer sem mudança de artefato)

| Fechamento | Evidência | Origem |
| --- | --- | --- |
| Restore byte a byte de Notes e Khan, nas quatro fixtures (Positronic e Percival), SHA-256 igual e leitura OK após restore | [relatório F4/F5](../reports/2026-10-10-f4-f5-closure-report.md) | F4, item 2 |
| Rollback de imagem/configuração A→B→A nos dois gestores (Notes e Khan), com CAS e `tools/list` | [relatório F4/F5](../reports/2026-10-10-f4-f5-closure-report.md) | F4/F6, item 3 |
| Commits dos candidatos publicados nos seis MCPs | [relatório F4/F5](../reports/2026-10-10-f4-f5-closure-report.md) | F5, item 4a |
| Seis MCPs ativos nos dois gestores, 4 `update-image` + 2 `install`, 99 tools observadas | [canário F7](../reports/2026-10-10-f7-canary-execution.md) e [stack local](../reports/2026-10-10-f7-local-stack-provisioning.md) | F7 |
| Inventário de proveniência em 8 repos, 6 identidades distintas, sem `.mailmap` e sem reescrita | [proveniência e identidade](../reports/2026-10-10-f7-provenance-and-identity.md) | F7 P1 |
| Diagnóstico do Khan e das duplicatas (sem órfãos confirmados no snapshot) | [Khan e duplicatas](../reports/2026-10-10-f7-khan-allowlist-and-duplicates.md) | F7 P2 |
| Bloqueios de runtime, segurança e CI | [P4/P5 blockers](../reports/2026-10-10-f7-p4-p5-blockers.md) | F7 P4/P5 |

**Lacunas residuais dessa evidência** (que os itens abaixo precisam fechar): a prova Khan usa
verificação em filesystem/stderr como proxy, não chamada MCP real; os builds locais de
Notes/AgentMail carregam diff pré-commit na label e não reproduzem o HEAD dos commits atuais;
o stack F7 usou overlay local de Engine 29, que não prova o gate VPS Engine 27.x; e as fixtures
A/B foram removidas ao final do ensaio, então não há par de rollback retido.

## 2. Itens abertos

Responsáveis: **agente** levanta evidência e propõe; **operador** decide, autoriza e assina.
Cada item registra a pendência da tabela do plano de fase entre parênteses.

| # | Item | Critério de aceite | Origem | Resp. | Estado |
| --- | --- | --- | --- | --- | --- |
| D1 | Rotacionar a credencial `operator-admin` e avaliar a exposição no histórico | Rotação pela interface suportada, autenticação com o segredo novo e invalidação do anterior sem registrar nenhum dos dois; inventário de commits/arquivos afetados; decisão explícita sobre histórico privado/remoto. Sem este gate, nenhuma mutação autenticada em instância real | F7 P0 / Extra | operador (rotação) + agente (inventário) | **parcial, com o inventário feito** — o literal foi redigido da árvore em `07f28314`, que registra que o valor segue no histórico e no arquivo em disco; `~/.nanobot/mcp-docker/operator-password` **existe** (9 bytes, 0600) e o histórico contém o literal removido em ao menos `07f08314`, `07f28314`, `824b1db0`, `c17a4e23`, `a9ad9bf9`. Falta a rotação, adiada pelo operador (`f7-p4-p5-blockers.md:15`). **Não reproduzir o valor em documento versionado** |
| D2 | Matriz de proveniência e política de identidade | Matriz repo → SHA → autor/committer bruto → atribuição confirmada → mapeamento aprovado → image ID/revision revisada; `.mailmap` apenas quando duas identidades forem comprovadamente a mesma pessoa; nenhuma reescrita de `main` publicado | F7 P1 (#10) | agente + operador | **parcial** — levantamento feito; falta decisão de atribuição |
| D3 | Permissão do Khan e projeção efetiva | Decisão registrada do operador sobre a superfície por gestor; lista efetiva extraída do protocolo e verificada nos dois consumidores; `allowedProjects` não confundido com permissão de tool | F7 P2 (#7) | operador | **aberto, e o critério estava errado** — o servidor expõe 17 identificadores `khan_*` (7 de escrita, entre eles `khan_delete_event` e `khan_update_event`) enquanto o canário observou 12 tools: a discrepância precisa ser explicada. **Não existe modo somente leitura** no servidor (busca por `read_only`/`readonly` em `percival-khan-calendar/src/` não retorna nada), então "somente leitura ou subset" não é alternativa de configuração: ou se aceita a superfície, ou se implementa a restrição |
| D4 | Atribuição das duplicatas por container ID | Mapa container → processo/sessão cliente/registry/escopo, com ciclo de vida demonstrado e cardinalidade esperada documentada; limpeza apenas com autorização específica e zero referências confirmadas | F7 P2 (#8) | agente | **parcial, e o mapeamento já é ferramenta** — `nanobot/mcp_docker/inventory.py:136` coleta `containerId` e `:299` renderiza tabela com `percival.mcp-docker.owner`, `.managed-by`, `.server-id` e `.instance-id`. O que falta é o que o inventário não prova: ciclo de vida demonstrado e cardinalidade esperada documentada |
| D5 | Regressão Khan `tools/call` | Chamada MCP real de leitura com evidência no protocolo, não em filesystem/stderr; reproduzir em fixture sem tocar calendário real; investigar a versão do FastMCP/`mcp[cli]` ou registrar limitação aprovada | relatório F4/F5 | agente | **aberto, confirmado** — **não existe** teste de protocolo: buscas por `tools/call`, `call_tool`, `ClientSession`, `stdio_client`, `jsonrpc` em `tests/` e `src/` do Khan não retornam nada, e todos os testes chamam a função por trás do tool (`tests/_helpers.py:24`-`:34`). O isolamento do calendário real está garantido (`tests/conftest.py:11` redireciona `DATA_DIR`/`DB_FILE` e desliga o lock). Versões em jogo: `mcp` 1.30.0 e `fastmcp` 3.4.4 (`uv.lock`), faixas `mcp[cli]>=1.28.1,<2.0.0` e `fastmcp>=3.2.0` (`pyproject.toml:13`-`:14`) |
| D6 | Resíduo OpenSSH `CVE-2026-60002` no gateway (#11a) | Build do gateway em base corrigida com OpenSSH >= 10.4 e regressão de Percival Remote SSH na imagem, **ou** exceção individual documentada e aprovada; OpenVEX do gateway não estendido aos MCPs sem análise por imagem | F7 P4.2 (#11a) | agente + operador | **aberto, e é o de maior severidade** — o runtime do gateway é `ghcr.io/astral-sh/uv:0.9.30-python3.12-trixie-slim@sha256:41eb2281…` (`Dockerfile:11`) e instala `openssh-client=1:10.0p1-7+deb13u4` (`Dockerfile:32`), abaixo do exigido; `openssh-server` não é instalado e o OpenVEX declara `not_affected` por `component_not_present`, restrito ao image ID do gateway e **sem** qualquer declaração sobre esta CVE. A triagem de F3 classificou como "Critical não resolvido" e propôs waiver **não aprovado** (`2026-10-10-f3-remediation-triage.md:168`). Não há waiver, build em base corrigida nem teste dentro da imagem; o "OpenSSH Forky 10.5p1 testado fora da imagem" do plano de fase **não** substitui o build do gateway |
| D7 | Consolidar evidência de runtime nos artefatos finais | SIGTERM/PID 1 sem init duplicado (F6 relatou dois inits em Deep Research), stdio sem porta/TTY, healthcheck só em serviço HTTP, falha fechada e auth; evidência nos SHAs/imagens finais | F4/F5 closure, item 2 | agente | **parcial, e dividido entre dois caminhos que se contradizem** — cumprido e testado: tini como PID 1 em OSM (`Dockerfile:146`) e Deep Research (`:155`), ENTRYPOINT em forma exec nos seis, healthcheck desabilitado no servidor stdio de OSM (`:142`, `test_d6_docker.py:54`) e ausência de healthcheck em Deep Research (`tests/test_docker.py:226`). **Defeito de código, não de evidência:** o consumidor Positronic passa `--init` incondicional (`alternative-positronic/packages/positronic-mcp-docker/src/managed.ts:640`), empilhando `docker-init` sobre o tini — é o achado de F6 (`2026-10-10-f6-local-cutover.md:49`) ainda vivo. O broker do Percival não faz isso (`percival_mcp_broker_f0.py:370`). **Falta de teste:** Notes, Khan e AgentMail não têm contrato de imagem |
| D8 | Reconciliar pins com builds de checkout limpo e promover | Rebuilder Notes/AgentMail (e qualquer candidato alterado) a partir de commit limpo, sem diff pré-commit na label; promover por gestor só com aprovação, canário e rollback independentes; reter o último bom e um par A/B de rollback conhecido | F7 P4.1 (#4, #6) | agente + operador | **parcial, e metade do critério já existe** — o gateway **já tem** o guard pedido: `scripts/percival-docker-build.py:71` lê `git rev-parse HEAD`, `:75` detecta árvore suja rastreada, `:96`/`:98` **recusam** o build inconsistente e `:157` rotula `io.percival.build.worktree=dirty`. Nenhum dos seis MCP tem guard equivalente. **Defeito novo, fora de qualquer plano:** o OSM grava SHA curto na label (`percival-osm/scripts/docker-build.sh:80`) enquanto o verificador exige igualdade com o SHA completo (`write_docker_ci_manifest.py:28`) — o build do OSM não passa na verificação de provenance se a CI passar `$GITHUB_SHA`. Não há manifest ou digest commitado nos seis, logo não há prova versionada de rebuild limpo |
| D9 | Exercitar o manual operacional e assinar a retenção | Walkthrough em fixture descartável de update, rollback, restore e falsa falha de health, comparando o texto do manual com os comandos e APIs instalados; política de retenção de imagens e revisão trimestral assinada | F7 P3 (#2, #5) | agente (redige) + operador (aprova) | **parcial** — [manual criado](../operations/mcp-docker-local-runbook.md) e vinculado, e a **consistência texto↔comando foi verificada**: o runbook referencia `nanobot auth init` e `nanobot mcp-docker doctor`, ambos registrados (`nanobot/cli/auth.py:50`, `nanobot/cli/mcp_docker_f1.py:23`, grupo montado em `nanobot/cli/commands.py:108`). Falta o walkthrough em fixture e a retenção assinada; a tabela de revisão trimestral que o próprio runbook exige (`:111`) não foi produzida |
| D10 | Caminho de reinstalação do MCP Docker no consumidor Positronic (**item reescrito em 2026-10-23**) | (a) Determinar e registrar qual é o caminho de reinstalação **suportado**, pela interface suportada; (b) corrigir a documentação que promete comandos inexistentes — a skill global `mcp-docker-workflow` lista 11 comandos `positronic mcp server …` (`SKILL.md:31`-`:43`) que **não existem** no pacote de CLI do fork; (c) remover o workaround de edição direta do registry | F7 P3 / relatório F4/F5 | agente + operador | **premissa errada → reescrito** — não há binário `positronic` no PATH, o CLI do fork é `packages/cli` (`@opencode-ai/cli`, bin `lildax`) e a busca por `install-local` em todo o TypeScript do fork, fora de `node_modules` e docs, **não retorna nada**: **não existe comando para corrigir**. O estado real é o registry gerido pelo servidor (`~/.positronic/mcp/registry.json`, `schemaVersion` + 6 servidores) |
| D11 | Skill de gestão F8 e instruções nos `AGENTS.md` | Matriz efetiva dos `AGENTS.md`; skill revisada com dry-run e fixture; ativação pelo operador | F8 (#9) | agente + operador | **parcial, com a matriz mensurável** — não existe skill de gestão para o Percival (as globais são `docker-desktop`, `mcp-docker-workflow` — do Positronic —, `journaling-*`, `memory-*`, `project-bootstrap`, `skill-creator`), e a única de containers é justamente a que o plano de fase manda comparar antes de decidir extensão ou skill separada: **essa decisão ainda não foi tomada**. `AGENTS.md`: global, raiz do Percival e do consumidor presentes; Khan, Weather, OSM e Deep Research presentes; **Notes e AgentMail ausentes** na raiz — exatamente os dois que o gate exige criar. A raiz do Percival não menciona MCP Docker |
| D12 | Assinatura F7 e registro de encerramento único | Relatório único com `pendência → decisão → SHA/image ID → verificação → evidência → operador/data`, inventário pós-cutover sem segredos, URLs dos runs e declaração de risco residual; **aceite local**, **aceite VPS/deploy** e **aprovação B13 de release** registrados como atos separados | F7 P5 | operador (assina) + agente (consolida) | **bloqueado** por D1–D10, C1–C4 e A1–A9 |

**Complementos de aceite após a harmonização:**

- **D7:** separar receita Compose de desenvolvimento de deployment e os modos
  gateway/API/CLI/broker (I2/I4). Preservar um init por processo e inspecionar `user:`
  efetivo; a imagem iniciar como root com drop fail-closed não prova execução como root
  no Compose. Exceções/alterações de permissões precisam de justificativa e teste.
- **D8:** para candidatos locais, manter o build limpo e ID verificável; para os
  publicados, aquisição homologada por digest em I3/I5/I6, registrando tag, digest OCI
  e image ID separadamente. Promover só pelo manager, não via capabilities Compose.
  Retenção inclui imagem/configuração/dados compatíveis; rebuild não é instalação padrão
  no VPS. Corrigir a discrepância de SHA do OSM antes de alegar proveniência conforme.
- **D9:** acrescentar ao walkthrough o handoff para I4/I8: `deployment.lock` pelo tooling
  de deploy, `capabilities.lock` pelo manager, backup/retorno de estado completo e
  classificação de migrações. Não alegar que rollback MCP substitui recovery do core.
- **D10/D11:** comandos por gestor precisam ser verificados no checkout/launcher instalado,
  sem copiar o CLI proposto de outro documento. Catálogo/manifest não é script autorizado;
  nenhuma skill assume capacidade de pull ainda inexistente nem edita registry/locks
  diretamente. Revisão/ativação de skill permanece no fluxo próprio de D11.
- **D12:** anexar o status dos contratos I1/I2/I4 aplicáveis ao candidato. Sign-off local
  pode avançar sem catálogo público pronto; sign-off IaC I9 requer suas próprias provas.

## 3. Itens transferidos (fora de escopo, com dono)

| Gate | Dono |
| --- | --- |
| Actions remotas nos sete SHAs candidatos; inventário do VPS; migração/rollback para destino aprovado em I4/C2 no Engine 27.x; novo aceite do risco no alvo | [plano integrado, C1–C4](2026-10-23-integracao-pendencias-kg-e-mcp-docker-plan.md) |
| Distribuição OCI, bootstrap/Compose de deployment, índice, aquisição e locks | [integração IaC, I1–I9](2026-10-23-iac-alignment-execution-plan.md); não duplica D/C |
| Browser WebUI + gateway + broker, matriz end-to-end das oito famílias, testes de UI e acessibilidade | [plano integrado, B1–B6](2026-10-23-integracao-pendencias-kg-e-mcp-docker-plan.md) |
| Autenticação de senha única: ensaio em Engine 27.x, elevação, proxy TLS, expiração, cutover real | [fechamento de senha única, A1–A9](2026-10-11-single-password-acceptance-closure-plan.md) |
| KG nativo: dados reais, ensaio B6/B7, release dos repositórios legados | [plano integrado, A1–A7](2026-10-23-integracao-pendencias-kg-e-mcp-docker-plan.md) |

Uma execução pode satisfazer gates de planos diferentes, desde que cada plano registre a própria
evidência e aponte para o run, inventário ou relatório comum.

## 4. Ordem de execução

```
D1 (credencial) ─┬─→ D8 (promoção) ─┐
D2 (proveniência)┤                  ├─→ D12 (assinatura F7)
D3, D4, D5 (Khan)┘                  │
D6 (OpenSSH) ───────────────────────┤
D7, D9, D10 (runtime/manual) ───────┘
D11 (skill F8) — independente, pode correr em qualquer momento
C1–C4 (Actions/VPS) ───────────────→ D12
```

- **D1 é pré-requisito** de qualquer mutação autenticada em instância real.
- **D3** bloqueia a projeção efetiva do Khan e, junto com **D5**, o item 2 do aceite. Se a decisão
  for restringir a superfície, ela vira trabalho de engenharia: não há modo somente leitura.
- **D6** bloqueia F7 e a publicação da primeira versão 0.1.0, e é hoje o item de maior severidade da
  lista: um Critical conhecido no candidato local do gateway. Não há evidência aqui de
  publicação dessa imagem em registry; reavaliar o finding no candidato final.
- **D7** tem uma parte que é **defeito de código** (o `--init` do consumidor Positronic) e outra que
  é teste faltante (contrato de imagem em Notes, Khan e AgentMail). A parte de código não espera
  decisão do operador.
- **D9** e **D10** são executáveis localmente, sem dependência externa. **D10** passou a ser
  verificação de caminho suportado e correção de documentação, não correção de handler.
- **D11** não bloqueia F7, mas fica fechado no mesmo plano por pertencer à mesma padronização; exige
  a decisão extensão-versus-skill-separada e a criação de dois `AGENTS.md`.

## 5. Riscos e critérios de parada

| Risco | Controle |
| --- | --- |
| Apagar evidência ao limpar fixtures | reter um par A/B de imagem conhecido por gestor antes de qualquer nova promoção; `docker image prune -a` e `system prune` nunca são atalho de limpeza |
| Confundir proxy de evidência com prova | verificação em filesystem/stderr não fecha `tools/call`; o critério exige protocolo MCP real |
| `chmod 777` de fixture local virar política de produção | registrar modo e owner reais no inventário antes de qualquer promoção |
| Estender o VEX do gateway aos MCPs | reavaliar findings por imagem e escopo; sem extensão automática |
| Reescrever `main` publicado | `mailmap` altera apresentação, não objetos nem SHA; reescrita é ato separado com autorização específica |
| Evidência de Engine 29 ser lida como gate de Engine 27.x | o overlay local não prova o alvo; o gate VPS é C2–C4, fora deste plano |
| Preservar `local-only` como veto permanente à proposta IaC | manter o baseline de execução e exigir I1 para o aditamento de contrato; I3/I5 têm publicação separada e B13 continua obrigatório |

**Parar e escalar** se a credencial exposta ainda der acesso, se uma duplicata não puder ser
atribuída com confiança, se uma imagem de retorno não existir, se a observação divergir da
configuração, se houver Critical sem correção ou decisão, ou se a topologia do alvo divergir do
aprovado. Não eliminar incerteza por `docker rm`, waiver implícito ou edição manual de estado.

## 6. Registo de execução

_Vazio na abertura (2026-10-23). Registrar por item: data, responsável, SHA/imagem/digest,
comando, resultado, artefato de evidência, limitações e decisão do operador. Não declarar item
fechado por teste local, por `Client.Version` ou por ausência de runs._

**2026-10-23 — reverificação contra o código (não é execução).** Todos os itens foram confrontados
com o repositório, com as imagens dos seis MCP e com o host; veredictos em
[auditoria planos × código](../reports/2026-10-23-auditoria-planos-vs-codigo.md) §3.4. Nenhum item
foi executado e nenhum foi fechado. Mudanças de conteúdo: **D10 reescrito** (o comando objeto não
existe nesta máquina), D3 corrigido (não há modo somente leitura), D7 dividido entre defeito de
código e falta de teste, D8 reduzido ao que falta nos seis MCP mais um defeito novo do OSM, D4 e D9
reduzidos ao que falta, D11 desmembrado em tarefas verificáveis.

Quando D12 for assinado, o relatório único deve substituir os snapshots de pendência hoje
dispersos entre o plano de fase, o relatório F4/F5 e os relatórios F7, mantendo os links.

**2026-10-23 — harmonização IaC (não é execução).** Incluídas fronteiras de ownership,
handoff de D7–D11, separação de aceite F7/I9 e dependências de layout e distribuição.
Preservadas as evidências existentes e o estado aberto de D1–D12.

**2026-10-23 — instruções do Percival atualizadas.** O `AGENTS.md` raiz agora cobre
responsabilidades IaC/produto/índice, ownership core/MCP, aquisição por digest, locks,
persistência, testes e gates, com links aos planos ativos. Isso resolve a ausência
dessas orientações na raiz citada no snapshot D11, mas **D11 continua parcial**:
matriz dos demais repositórios, decisão de skill, fixture/dry-run e ativação ainda
exigem suas próprias evidências. A revisão não fecha F8 nem altera runtime.
