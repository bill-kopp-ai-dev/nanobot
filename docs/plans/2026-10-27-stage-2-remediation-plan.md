# Stage-2 — Remediação do Percival (`nanobot`)

**Data / revisão:** 2026-10-28 / 1.4.
**ID / estado:** S2-NB / em execução; aceite local parcial.
**Checkout executor:** `/home/bill/Projects/nanobot`.
**Responsável:** executor técnico local; decisões de produto/operação com bill.

## 1. Objetivo, fontes e baseline

Corrigir ou tratar explicitamente todos os achados da **seção 6** do
[relatório Percival](../../../positronic-bean-IaC/docs/reports/2026-10-27-nanobot-iac-readiness-report.md#6-achados-issues-e-inconsistências),
complementado pelas seções 7 e 9. Origem: 12 achados e 12 ações, sendo 1 P0,
3 P1 e 8 P2. Snapshot diagnosticado: `766d33bfeca997e4159f2cf9561782c668f39b60`.
Na emissão deste plano o HEAD é `62d1e4e2`; não se presume que evidência do snapshot
anterior qualifique esse HEAD. Há exclusões documentais locais preexistentes.

[Plano coordenador stage-2](../../../positronic-bean-IaC/docs/plans/2026-10-27-iac-v1-stage-2-remediation-plan.md)
— atualizar S2-NB nas seções 3 e 7 ao finalizar. Referências comuns:
[consolidação](../../../positronic-bean-IaC/docs/reports/2026-10-26-stage-1-consolidated-readiness-report.md)
e [D-01..D-06](../../../positronic-bean-IaC/docs/decisions/2026-10-27-iac-stage-1-scope-and-pilot-decisions.md).

Este plano permanece o tracker local desta campanha. Não retoma deploy/VPS/cutover,
I3/B13 ou gates adiados. Os planos ativos L*/D* seguem localmente excluídos; o
mapeamento disponível no relatório/coordenador foi preservado sem recriar esses
arquivos. Decisão de Bill em 2026-10-29: trackers L*/D* antigos são obsoletos; seguir
somente os planos ativos vigentes. Referências legadas permanecem como proveniência,
não como trackers ativos. A decisão não fecha automaticamente ações sem destino/owner:
mantê-las abertas neste plano até atribuição rastreável, sem recriar trackers.

## 2. Preparação obrigatória da execução

- [x] Ler `AGENTS.md`, `.agent/workflow.md`, runtime contract, runbook e handoff;
  reconciliar com bill os trackers L*/D* localmente excluídos. A leitura foi feita;
  Bill decidiu em 2026-10-29 que os trackers antigos são obsoletos e que somente os
  planos ativos vigentes serão usados. Arquivos ausentes não foram restaurados.
- [x] Registrar SHA/worktree, ambiente e owner técnico. Baseline de execução:
  HEAD `8c2ac64b68e8428dd1ed38e4474a7e4c91f26720`, worktree dirty preexistente;
  Python 3.12.14 em `nanobot-stage2-env`; owner executor técnico local, decisões
  com bill. O caso 143 foi reproduzido antes da correção; alterações de produto/teste
  foram commitadas em `a51802103a1cfac26e394e469f757fff1072784b`.
- [x] Distinguir IaC **D-01..D-06** de Percival **D01..D12** e usar o mapeamento
  A-001→L06/D08, A-002→L02, A-006→L14/L15/D03 e as dependências das ações abaixo.
- [x] Decisão `R-02` (2026-10-28): registro histórico da receita restrita e da
  proposta `mounts=[]` por default. Em 2026-10-29, Bill supersedeu formalmente
  R-02 quanto ao default de mounts por `R-10`: manter o acesso amplo como default,
  conforme B14/B22/B23–B25; ver seção 8.5. O registro da receita vigente permanece
  histórico. Nenhuma mudança de runtime foi autorizada por essa decisão.
- [x] Decisão `R-03` (2026-10-28): removida a exigência de estimar esforço,
  custo ou prazo.
- [x] Decisão `R-05` (2026-10-28): o tracker F3 canônico será mantido em
  `pblabs-mcp-index`, por imagem publicada; checkouts apontam para ele em vez
  de manter cópias.
- [x] Decisões `R-06` a `R-09` (2026-10-28): metadata MCP usa schema externo
  de `server.json` e extensão operacional `pblabs.app.yaml`, com manifests em
  `pblabs-mcp-index` e sem dependência do Docker MCP Catalog; promoção exige
  VEX por CVE associado ao image ID e assinado pelo owner, herdando CVEs da
  imagem base; operações dependentes usam pin aprovado e janela única datada;
  suporte/limitação de cancelamento e deadlines é registrado por transporte,
  método e deadline, sem obrigação geral de implementar cancelamento.

## 3. Backlog integral e critérios de aceite

O estado por ação após esta execução está na seção 6. Condições externas indicadas
continuam pendentes. Prioridade é a da ação de origem, não uma nova classificação.
Áreas abaixo são as apontadas pelo relatório; caminhos foram conferidos no SHA executor.

| Ação | Achado / P | Trabalho no dono e áreas previstas | Dependência / owner externo | Evidência necessária para verificar |
|---|---|---|---|---|
| A-001 | F-001 / P0 | Corrigir predicado de ownership em `nanobot/mcp_docker/broker.py`, incluindo inspect/mutate/hydrate/recover/start/exclude; vínculo de instância compatível | L06/D08; decidir adoção de containers históricos | Labels owner/managed-by/server-id ausentes ou divergentes recusadas antes de mutar; ID, estado e dados de fixture alheia preservados; fluxo próprio positivo |
| A-002 | F-002 / P1 | Segregar transporte de controle do Engine em `scripts/percival-i2-runtime-smoke.py`/harness e CI; não apenas retirar socket | L02; receita autorizada, IaC D-05 se aplicável | Unix e TCP negados de gateway/MCP; controlador e broker autorizados operam; Engine 27.x continua gate, sem override para esconder falha |
| A-003 | F-003 / P1 | Retirar conteúdo do pedido e argumentos dos logs INFO em loop/progress hook; metadados operacionais e transcript privado separados | Política de opt-in/retencão com bill | Canários sintéticos de pedido e argumentos ausentes de stderr/log operacional; sessão privada suportada permanece íntegra |
| A-004 | F-004 / P2 | Empacotar cliente TUI matching ou declarar TUI externa/origem aprovada em launcher/packaging; impedir download implícito do upstream como produto | B13/D01/D04 históricos | Cliente da revisão compatível, launcher e PTY reais; offline se alegar imagem completa; fallback classic explícito |
| A-005 | F-005 / P2 | Aplicar regra de permissão de config sensível no owner do config, sem mudar todos os writers genéricos | Decisão para arquivos existentes e backups; S2-C01 | Criação e replace com 0600 ou recusa documentada; backup restrito; fixture 0644 não preserva exposição inadvertidamente |
| A-006 | F-006 / P1 | Investigar readiness curta, igualdade de floats, branding WebUI e símbolos indefinidos em `scripts/d11/d9_rehearsal.py`; alinhar comando Ruff/CI | L14/L15/D03; ambiente lock/SDK/toolchains | Suíte, CLI, typecheck, lint e frontend pertinentes verdes no candidato; causas e scope de Ruff explicados; sem mascarar skips/retries; sem `ruff format` |
| A-007 | F-007 / P2 | Manter inventário fonte→imagem→instância, separando saved/observed/connectivity; preparar reconciliação no manager existente | D01/D03; owner e janela próprios para runtime real | Inventário datado e sanitizado; imagem e revisão efetivas identificadas; stopped sob demanda não vira falha por inferência |
| A-008 | F-008 / P2 | Reancorar triagem do Medium no candidato exato, hashes/código/testes e SBOM/scan | D04 histórico; DB/scanner atuais; gate `R-07` | Decisão por CVE ligada ao image ID e VEX assinado pelo owner; CVEs herdados da imagem base seguem a postura por herança; sem mudar metadata para ocultar finding ou reaproveitar waiver de outra imagem |
| A-009 | F-009 / P2 | Integrar catálogo, aquisição, policy independente e export no manager/broker existentes; CAS/migração explícita | D07/D08/D09; S2-C01/C02/C03; etapas 2/4/5 IaC | Matriz negativa de origem/digest/policy; export atômico sem segredo; estado canônico único; local-only permanece até contrato aprovado |
| A-010 | F-010 / P2 | Homologar bridge por app, método e deadline; erro/cancelamento/EOF e attach em `broker.py`/client/MCPProvider | D08; app selecionada, receita isolada; etapa 5 IaC; formato `R-09` | Correlação de respostas, calls concorrentes, EOF/timeout sem attach órfão; registrar suporte ou limitação por transporte/método/deadline; resources/prompts/streaming testados se oferecidos, senão recusados/declarados. Não há obrigação geral de implementar cancelamento |
| A-011 | F-011 / P2 | Especificar restrições do produto e entregar requisito de preflight de writers/instâncias à IaC; produto testa o contrato que controla | Dono IaC implementa bundle/preflight na etapa 3; runtime 1 | Fixture recusa segundo writer e segunda instância no daemon antes de mutar; mudar nome Compose não é isolamento de instalação |
| A-012 | F-012 / P2 | Definir e ensaiar shutdown/recovery carregado no broker, preservando store/journal e dados | Escopo I8 carregado a reautorizar; S2-C01 | Calls ativas têm término/erro limitado documentado; restart reconcilia operação sem duplicação; não confundir idle/crash sintético com recovery real |

### 3.1. Dependências recebidas de outros projetos

Estas subtarefas complementares não alteram as 12 ações de origem.

| ID | Origem / execução aqui | Aceite compartilhado |
|---|---|---|
| S2-NB-X01 | AgentMail A-006/A-008; Research A-005/A-009; Khan A-001/A-002/A-008; OSM A-008 e Weather A-005: implementar perfis explícitos de mounts, init, secrets por arquivo e lifecycle conforme S2-C01 | Default do broker Percival: acesso host amplo R/W, com máscaras/exclusões de superfícies de controle, estado e credenciais conforme B23–B25; sem acesso direto ao socket. Cada app declara e configura seu perfil: `[]` para nenhum bind, mounts estreitos quando necessários; não depender do default para stateless. Aumentar escopo de perfil configurado exige confirmação/auditoria; teste do consumidor |
| S2-NB-X02 | Khan A-005 e gates de qualificação dos MCPs: receber scans/manifests por candidato e coordenar o CI do gateway quando exigido | Evidência por SHA/image ID/manifest digest e DB; CI remoto não fechado por teste local; retorno para cada plano MCP |

O risco de rotação da chave de teste do Deep Research foi explicitamente aceito
em `R-01`; este plano não deve solicitar nem executar essa rotação. A entrega por
arquivo continua sendo requisito de configuração, sem implicar revogação da chave.
Nunca incluir o segredo em evidência ou plano.

## 4. Ordem dos lotes e dependências

1. **Lote NB-1:** A-001, A-003 e A-006; A-002 após receita de ensaio adequada.
   O P0 deve estar comprovadamente fechado antes da integração pelo broker.
2. **Lote NB-2:** A-005 e S2-NB-X01 com revisão mínima de S2-C01; A-004 e A-008
   na qualificação. A-007 prepara inventário sem trocar pins reais.
3. **Lote NB-3:** A-009/A-010 após contratos/ADR; A-011 com a IaC, A-012 após
   retomada de escopo; S2-NB-X02 com candidatos e gate de distribuição.
4. Piloto Percival + Notes só em plano próprio, depois da implementação e
   evidência do perfil de mounts conforme `R-10`/C01, das condições Notes e das autorizações operacionais
   aplicáveis. `R-03` remove qualquer requisito de dimensionamento prévio; este
   documento não cria receita operacional de piloto.

Alterações em ownership podem impedir adoção de recursos legados: recusar adoção
não comprovada é preferível a remover recurso de outro dono. Dados e rollback são
preservados. Não há requisito de estimar esforço, custo ou prazo (`R-03`).

## 5. Qualificação e condições de conclusão técnica

- [x] Regressões de A-001/A-003/A-006 passaram; smoke repetido no candidato local
  atual. Nenhum teste replica literalmente o predicado de ownership.
  - [x] Gates locais: `pytest` amplo 9.209 passed/49 skipped e CLI serial 160 passed;
  `basedpyright` 0 erros/avisos; `ruff check .` passou. WebUI pertinente: 100 testes
  de `remote-instances`, 87 de `app-layout`, lint e build passaram; `npm ci --ignore-scripts
  --dry-run` passou. Não foi executado `ruff format`. A matriz Python 3.14 e CI remoto
  não foram executados.
- [x] Build e smoke com fixtures sintéticas; imagens gateway/broker separadas e
  proveniência local registrada. Sem push/publicação.
- [ ] Reconciliar `V-BUILD`, `V-RUN`, `V-CONFIG`, `V-DATA` e limites
  `V-MCP`/`V-FUNC`/`V-REUSE` no plano final; inventário/aceite de cada app e CI
  remoto ainda não foram revalidados. `V-PILOT` permanece não avaliado.
- [ ] Runtime real só pela interface do owner, após leitura do runbook operacional,
  revisão/CAS, autorização e backup; sem deploy, push ou publicação implícitos.

Aceite local pode ser entregue antes dos externos. Ações transferidas, sem
evidência de seu dono, continuam abertas; remediação integral não está concluída.

## 6. Penúltima etapa — documentar a execução neste plano

- [x] Atualizar ações/lotes, mapeamento L*/D* disponível, comandos/ambiente, testes,
  SHA inicial/candidato, resultados e limites; evidências sintéticas ficam no scratch
  privado indicado abaixo. As alterações de produto estão commitadas; exclusões
  documentais locais preexistentes permanecem fora do commit.
- [ ] Registrar revalidação à seção 9 do relatório de origem após revisão de bill;
  preservar baseline e veredito histórico. Decisões/pendências e respectivos owners
  já constam no estado por ação desta revisão.

| Data / owner | Ações / achados | SHA inicial → final | Mudança e evidências locais | Resultado / V-* / pendências |
|---|---|---|---|---|
| 2026-10-28 / executor local + bill | A-001/A-002/A-003/A-004/A-005/A-006/A-008 verificadas localmente; A-007 parcial por escolha do owner | HEAD inicial `8c2ac64b68e8428dd1ed38e4474a7e4c91f26720`; alterações de produto commitadas em `a51802103a1cfac26e394e469f757fff1072784b`. O candidato F2 foi construído antes do commit, em worktree dirty, com source-diff `3cf4719bf4bdf7b2fd35ae77f7e5aa071bfbc3b8e5ff53563c45d29883577b1a`; não é release/clean-SHA candidate. | Gateway `sha256:301d1a58d6e6e6682c728facc60df47bef72370017e7d7bcec99f1ef898367ac`; broker `sha256:e9343df917b971a6a907670f8029bbff3aabb1ef09d0cf669339802c30636d88`; smoke Engine 27.5.1 completo em `~/.positronic/runtime/tmp/opencode/percival-stage2-8c2ac64/i2-_pclfmoo/results.json`; pytest 9.209 + CLI 160, BasedPyright/Ruff/WebUI/TUI gates verdes | A-007 foi deixada parcial por Bill; A-009–A-012 dependentes/abertas; sem piloto, CI remoto, release, push ou runtime real |

### 6.1. Estado por ação em 2026-10-28

| Ação | Estado nesta execução | Evidência / dependência restante |
|---|---|---|
| A-001 | Verificada localmente | `_inspect()` falha fechado sem owner/managed-by/server-id/UUID; testes negativos e `exclude` preservam fixture sem ownership; smoke exercitou o broker em Engine 27.5.1. Nenhum container real foi alterado. |
| A-002 | Verificada localmente | Causa do 143: `docker exec` externo não encaminhava stdin ao `python -`, então `wait()` aceitava EOF/exit 0 sem executar probes e o gateway era parado durante startup. `-i` agora é encaminhado nos níveis externo/interno; env Compose é reescrito do estado corrente. Smoke final completo: TCP Engine negado no gateway, broker/controlador operantes; sem endpoint TCP publicado no host. |
| A-003 | Verificada localmente | Logs INFO só registram metadados; canários de argumentos/conteúdo ausentes; full pytest preserva transcript privado e resultados de tool. Política bill: sem opt-in de conteúdo. |
| A-004 | Verificada localmente — wheel Percival | Fallback/download HKUDS removido; wheel candidate Linux x64 inclui binário matching (source archive verificado contra checkout) e launcher resolve o binário empacotado offline; source distribution exige `NANOBOT_TUI_BIN` explícito ou `--classic`. Wheel local `nanobot_ai-0.1.0-py3-none-manylinux_2_17_x86_64.whl`, SHA256 `ccda285d1213b349f0130814b6acebe28ec9e6b764d9fac57596974351dfd566`, binary PTY smoke passou. Build local usou Bun 1.4.2 (CI pin 1.3.13); sem publicação/B13. |
| A-005 | Verificada localmente | `save_config` força 0600 em toda substituição, inclusive config existente permissiva; backup root/diretórios 0700 e manifest 0600. Fixture validou 0644→0600 e modos de backup; smoke final verificou reparo do config sintético; nenhum arquivo real foi alterado. |
| A-006 | Verificada localmente | Corrigidos timeout de startup do teste concorrente, igualdade float de TTL, dois títulos de documento rebrandados para `Percival` e lint do D9; CI alinhado para `ruff check .`. Gates e detalhes acima; Python local 3.12, não 3.14 nem Actions remoto. |
| A-007 | Parcial — Bill escolheu deixar parcial | Inventário read-only 2026-10-28 reportou 45 imagens/14 containers/21 referências; config salva revision 18/schema 1 e seis MCPs Percival com estado salvo `running`/image ID local correspondendo aos containers `running` e labels próprios. Bill decidiu não prosseguir com `list()` nesta sessão. MCP handshake/conectividade seguem desconhecidos; gateway/broker ativos são revisions anteriores, sem troca de pins. |
| A-008 | Verificada localmente — escopo candidato | Bill aprovou `not affected` apenas para o image ID final `sha256:301d1a58d6e6e6682c728facc60df47bef72370017e7d7bcec99f1ef898367ac`. Trivy 0.76.1/DB 2026-10-28: gateway 1 Medium `CVE-2026-49138` (`nanobot-ai 0.1.0`, scanner sugere 0.2.1), broker 0. NVD descreve SSRF via auto-redirect; código valida redirects manualmente e pinna DNS, fix commit `545294c` é ancestral e 3 testes de redirect privado passaram. Sem aprovação de publicação nem waiver de release. Evidência em `~/.positronic/runtime/tmp/opencode/percival-stage2-8c2ac64/scan-summary.json`. |
| A-009 | Não iniciada | Aguardando contratos/ADR, S2-C01/C02/C03, D07–D09 e etapas 2/4/5; local-only permanece. |
| A-010 | Não iniciada | Aguardando app/receita aprovada e D08; smoke sintético não homologa resources/prompts/streaming/cancelamento de app real. |
| A-011 | Não iniciada | Entrega à IaC/preflight depende do owner IaC e runtime contract; este retorno só informa o estado. |
| A-012 | Não iniciada | I8 carregado precisa de reautorização; smoke cobre idle/SIGKILL sintéticos, não drain sob carga/recovery real. |

O smoke final registra ainda gateway/API exit 0 em idle, broker exit 143 sem drain,
stdio EOF exit 0, pair recreation/hydrate e identidade alternativa UID/GID 1001.
Os arquivos de imagem tar e resultados estão fora do checkout em
`/home/bill/.positronic/runtime/tmp/opencode/percival-stage2-8c2ac64/`; não contêm
credenciais reais. O scan usou apenas os tarballs e cache Trivy local, sem montar o
Docker socket no scanner.

## 7. Última etapa — atualizar o plano coordenador

- [x] Reler o [stage-2 geral](../../../positronic-bean-IaC/docs/plans/2026-10-27-iac-v1-stage-2-remediation-plan.md);
  atualizar **S2-NB na seção 3** e acrescentar retorno na **seção 7**, com ações
  verificadas/abertas, SHA/evidências, dependências liberadas e condições externas.
- [x] Informar efeitos sobre M1/etapas 2–5; preservar retornos de outros projetos.
  Sem acesso à IaC: entregar resumo e ficar **aguardando sincronização**. Somente
  declarar concluído quando os aceites e o retorno estiverem atendidos; registrar
  parcial/bloqueado se houver pendências, sem converter transferência em solução.

## 8. Plano de execução para os itens ainda abertos

**Revisão:** 2026-10-29. **Owner do produto e das decisões:** Bill Kopp
(`bill.kopp.dev@gmail.com`). **Executor técnico:** Positronic, sob autorização
específica para operações externas ou runtime real. Este plano detalha a execução
dos resíduos identificados em S2-NB e não substitui este tracker nem o plano
coordenador IaC. O relatório de itens abertos de 2026-10-28 é uma fonte de contexto;
onde divergir deste estado local, os critérios e a evidência serão revalidados antes
de declarar aceite. Para providências do owner que destravam CI, manager, contratos
e preflight da IaC, ver o [guia de ações do owner](2026-10-29-stage-2-owner-actions-guide.md).

### 8.1 Regras de execução e fronteiras

- Fechar primeiro as decisões/documentos comuns que destravam vários itens; executar
  em paralelo somente tarefas independentes e locais. Não inferir implementação a
  partir de um contrato aprovado, nem aceite remoto a partir de testes locais.
- Escopo deste plano: A-007 e resíduos de A-002/A-004/A-008; A-009–A-012;
  S2-NB-X01/X02; reconciliação dos trackers L*/D*; revalidação da seção 9 do
  relatório de origem; atualização do plano coordenador IaC. A-001/A-003/A-005/A-006
  e o aceite local já registrado de A-004/A-008 são preservados, sem repetição
  desnecessária de testes se as fontes/evidências permanecerem aplicáveis.
- Nenhuma publicação, push, release, criação de repositório remoto, alteração de
  credenciais, mudança de pin em runtime, adoção/remoção de container real ou piloto
  está autorizada por este plano. Cada operação requer autorização específica,
  janela e procedimento do owner; D-05/R-02/R-10 registram a política/receita, não
  autorizam uma execução operacional.
- A-011 é um requisito entregue à IaC, não uma tarefa cujo aceite pertença somente
  ao Percival. A-012 exige ensaio carregado/recovery real apenas após contrato,
  escopo e autorização; fixtures sintéticas não fecham esse aceite.

### 8.2 Sequência de trabalho e aceites

| Lote | Itens | Trabalho / aceite verificável | Dependências e dono |
|---|---|---|---|
| E0 — Reconciliação | Preparação, L*/D*, estado atual | Relê `AGENTS.md`, workflow, contratos, runbook, handoff e Git; a decisão de Bill em 2026-10-29 declara obsoletos os trackers L*/D* antigos e mantém somente os planos ativos vigentes. Referências históricas servem como proveniência, não como fonte de execução; qualquer ação ainda sem destino/owner permanece aberta neste plano até encaminhamento rastreável. Atualiza baseline SHA/worktree e separa evidência local, externa e histórica. | Decisão de obsolescência registrada. Não restaurar trackers; não inferir que itens sem owner/destino foram resolvidos. Mudança futura de owner exige atualização de um plano ativo, sem criar cópia concorrente. |
| E1 — Contratos e ADR | S2-C01, S2-C02, S2-C03; habilita A-009/A-010/X01 | Revisão com Bill do runtime/lifecycle, perfis de mounts e secrets, init/sinais/drain, limites por transporte; fixa schema externo `server.json` + `pblabs.app.yaml` e destino `pblabs-mcp-index`; registra ADR do executor/transporte a partir do broker existente. Versionar apenas após aceite do owner; verificar compatibilidade com consumidores e defaults existentes. | C01/C03 são documentos comuns no checkout IaC/índice; C02 no owner definido pelo coordenador. Este checkout não existe para C03 no momento da leitura (`docs/mcp-app-contract.md` ausente em nanobot). R-10 registra o default amplo do Percival; R-06/R-09 seguem válidas. Grace/drain e perfis por app ainda requerem especificação/teste. |
| E2 — A-007 + trackers | A-007, NB-11 | Decisão de Bill em 2026-10-29: executar diretamente `list()` pela interface autenticada, aceitando que `recover_pending()` possa reconciliar transições, atualizar journal/config ou acionar o broker. A autorização cobre esse efeito colateral da chamada; antes de invocar, reler revisão/CAS e identidade do manager. Registrar resultado e quaisquer recoveries; gerar inventário datado/sanitizado sem segredos. Recursos históricos sem ownership comprovado ficam recusados/não adotados até decisão explícita. | Consulta e recovery incidental autorizados por Bill em 2026-10-29. Execução aguarda disponibilidade da interface autenticada do manager nesta sessão; não simular nem substituir por edição manual em config/audit/registry. |
| E3 — A-004 residual + A-002 residual | A-004/B13; A-002/CI | Percival mantém o TUI como componente próprio no checkout. Documentar proveniência por arquivo/componente, distinguir código original, herdado e modificado, preservar licenças/avisos aplicáveis e confirmar que o wheel é construído dessa fonte; alinhar Bun com o pin de CI (ou atualizar ambos por mudança justificada), executar B13 e PTY/packaging no candidato de SHA limpo. Rodar CI remoto `main` e matriz Python 3.14; guardar logs/artifacts e reconciliar V-BUILD/V-RUN/V-CONFIG/V-DATA/V-MCP/V-FUNC/V-REUSE sem mascarar skip/retry. | Decisão de origem própria confirmada por Bill em 2026-10-29. Falta inventário de proveniência/licenças e escolha do pin Bun. Acesso e workflows Actions ativos; execução CI não equivale a autorização para publicar. O owner aprova changelog/release notes se houver candidato de release. |
| E4 — A-008 + S2-NB-X02 | Gate de segurança/distribuição | Decisão de Bill em 2026-10-29: reconstruir e escanear primeiro o candidato exato, registrando SBOM e identificadores; se houver atualização corrigida compatível, preferi-la e repetir os gates; caso contrário, avaliar a vulnerabilidade no candidato e então decidir VEX justificado, correção/mitigação ou bloqueio. Integrar scan/manifest e evidência VEX no gate de CI; não reutilizar o parecer `not_affected` do image ID anterior. | Abordagem de triagem decidida por Bill. A postura final depende do scan atual e será assinada por Bill conforme R-07 quando aplicável. CI/gate de distribuição deve estar disponível. Sem push ou promoção implícitos. |
| E5 — Broker e consumidor | S2-NB-X01; A-009 | Implementar/testar o default host amplo R/W conforme R-10/B23, mantendo máscaras de controle, state/credentials e sem socket; perfis explícitos `[]` e binds estreitos continuam disponíveis por app. Ampliação de um perfil já reduzido exige confirmação/auditoria. Preservar valores configurados em migração, sem mutar runtime; init/sinais/secrets por referência e lifecycle conforme C01. Atualizar testes do consumidor Notes, incluindo configuração explícita do vault, e negativos de caminhos protegidos. Usar Notes como app de referência confirmada por Bill em 2026-10-29; depois iniciar A-009: policy independente, catálogo/aquisição sob pin aprovado, CAS/migração e export atômico do único estado canônico. | C01/C02/C03 revisados; contratos IaC das etapas 2/4/5. R-10 reconcilia R-02 com B14/B22/B23 em `.positronic/PROJECT.md`; preservar as mount protections exigidas por `AGENTS.md`. |
| E6 — A-010 bridge | A-010 | Homologar a bridge usando Notes, app de referência confirmada por Bill em 2026-10-29. Por transporte/método/deadline, verificar respostas correlacionadas, chamadas concorrentes, EOF/timeout sem attach órfão; testar capabilities anunciadas (resources/prompts/streaming) ou declarar recusa/limite explícito. Registrar matriz R-09; não implementar cancelamento sem requisito demonstrado. | Receita isolada de Notes, contrato/ADR e candidato aprovado. Fixtures sintéticas podem antecipar depuração, mas não contam como homologação de app real. |
| E7 — A-011 preflight | A-011 | Publicar ao owner IaC o contrato testável: no mesmo daemon, segunda instalação/writer deve ser recusada antes de mutação; Compose project name não prova isolamento. Adicionar fixture de consumidor que demonstra a condição e integrar ao bundle/preflight da etapa 3; receber resultado do owner IaC no aceite. | Owner IaC implementa o preflight. Ação Percival fecha somente quando teste do contrato e evidência do preflight IaC forem vinculados. |
| E8 — A-012 shutdown/recovery | A-012 | Bill autorizou em 2026-10-29 um ensaio isolado descartável: daemon DinD exclusivo, um broker e uma fixture MCP; manter chamada em voo, provocar shutdown/restart e observar término/erro, reconciliação e ausência de duplicação. Usar somente estado/dados sintéticos e não tocar containers ativos do Percival. Após definir C01, registrar limites e evidência de store/journal/dados pelo manager. | Autorização do escopo isolado concedida por Bill em 2026-10-29; execução ainda depende de contrato C01, cenário/falha controlada e ferramentas disponíveis. Nenhum dado/runtime real autorizado. Se o requisito for limitado por design, obter aceite explícito e documentar a limitação; idle/SIGKILL não contam como recovery carregado. |
| E9 — Gate de piloto e retorno | V-PILOT, seção 9, coordenador | Reconciliar V-* no SHA/image ID candidato e por app; resolver dependências de Notes e autorizações operacionais. Só então redigir plano próprio de piloto Percival + Notes para revisão/autorização separada. Acrescentar revalidação à seção 9 do relatório de origem sem alterar baseline; registrar evidência, owners e pendências no plano local e atualizar S2-NB nas seções 3/7 do coordenador. | Aprovação explícita de Bill para piloto e operações correspondentes; owners dos projetos dependentes; CI e gates da distribuição concluídos. Não iniciar deploy/VPS/cutover ou I3/B13 por inferência. |

### 8.3 Decisões e ações requeridas de Bill

As decisões abaixo são gates específicos; até serem resolvidas, somente os lotes
independentes e não mutacionais podem avançar:

1. **A-004 / TUI — origem decidida em 2026-10-29:** declarar o TUI como componente
   próprio do Percival, cuja fonte é o código mantido no checkout. O executor deve
   registrar proveniência e licença e distinguir claramente o que é original,
   herdado e modificado, preservando atribuições/avisos aplicáveis. **Pendente:**
   confirmar se Bun segue o pin atual do CI (`1.3.13`) ou se CI e build local serão
   atualizados em conjunto para outro pin. Até essa escolha, E3 permanece parcialmente
   bloqueado no gate de reprodutibilidade.
2. **A-007 — decisão registrada em 2026-10-29:** Bill autorizou executar diretamente
   `list()` pela interface autenticada, aceitando eventual recovery incidental por
   `recover_pending()`. **Execução ainda pendente** da disponibilidade da interface
   autenticada nesta sessão. Se aparecerem recursos históricos sem ownership
   comprovado, mantê-los recusados/não adotados até Bill decidir com evidência.
3. **A-008/X02 — abordagem decidida em 2026-10-29:** reconstruir e escanear o
   candidato exato, com SBOM e identificadores registrados. Se houver atualização
   corrigida compatível, preferi-la e repetir os gates. Se não houver ou não for
   apropriada, avaliar a vulnerabilidade nesse candidato e então escolher entre VEX
   justificado, correção/mitigação ou bloqueio. A postura final continua pendente
   dos resultados; VEX e promoção não estão aprovados antecipadamente. A herança e
   assinatura do owner seguem R-07; pareceres de outros image IDs não se transferem.
4. **A-009/A-010 — decisão registrada em 2026-10-29:** usar Notes como app de
   referência para catálogo/consumidor e homologação da bridge. A escolha não
   substitui a aprovação de receita isolada nem a evidência de teste exigida.
5. **A-012 — decisão registrada em 2026-10-29:** autorizado ensaio I8 isolado e
   descartável em daemon DinD exclusivo, com um broker e uma fixture MCP, chamada em
   voo, shutdown/restart e verificação de término/erro, reconciliação e ausência de
   duplicação. Somente estado/dados sintéticos; sem tocar containers ativos do
   Percival. Execução aguarda contrato C01 e preparação do cenário. Esta autorização
   não inclui runtime real.
6. **E0 / trackers — decisão registrada em 2026-10-29:** declarar obsoletos os
   trackers L*/D* antigos e seguir somente os planos ativos vigentes. Não restaurar
   nem usar os trackers antigos como fontes de execução. Essa decisão não encerra
   automaticamente ações sem destino ou owner claro; elas permanecem abertas neste
   plano até encaminhamento rastreável.
7. **V-PILOT/publicação:** decidir em etapa própria se autoriza o piloto e, em
   separado, publicação/push. A autorização de DinD descartável já registrada não
   cobre nenhuma dessas operações.
8. **Mounts — decisão `R-10`, 2026-10-29:** Bill determinou manter o acesso amplo
   como default do broker Percival, supersedendo R-02 quanto ao default `[]`. Perfis
   explícitos `[]` (nenhum bind) e mounts estreitos continuam disponíveis; qualquer
   aumento de escopo a partir de um perfil mais restrito requer confirmação e
   auditoria. Nenhuma alteração de runtime foi autorizada.

**Bloqueadores de infraestrutura/coordenação, não decisões de produto:** acesso a
Actions CI remoto e execução de Python 3.14; disponibilidade do manager autenticado;
owner IaC para aceitar/implementar A-011; revisão/versionamento dos contratos nos
checkouts donos; CI de distribuição com armazenamento de SBOM/scan/VEX. Se algum
recurso estiver indisponível, registrar o item como bloqueado com owner e condição
de retomada, sem converter transferência em aceite.

### 8.4 Critério de encerramento

S2-NB só poderá ser marcado concluído quando cada ação A-001–A-012 e S2-NB-X01/X02
tiver resultado rastreável (verificada, limitação aceita ou transferência com dono,
aceite e dependência explicitados), os V-* aplicáveis estiverem reconciliados para
os candidatos exatos, a revalidação histórica estiver anexada e o retorno às seções
3/7 do coordenador estiver atualizado. Transferência sem evidência do dono permanece
pendente; publicação, runtime real e piloto são gates separados e não serão inferidos
do aceite local.

### 8.5 Decisão `R-10` — default amplo de mounts do broker Percival

**Decidido por Bill em 2026-10-29.** O Percival mantém o acesso amplo R/W ao host
como default de mounts, conforme a diretriz histórica B14 e sua revisão B22/B23–B25.
Esta decisão supersede R-02, de 2026-10-28, **somente quanto ao default restrito
`mounts=[]` e à exigência de tornar o Full uma operação excepcional**. O registro da
receita de execução restrita já vigente não é desfeito.

- Estado default equivale ao comportamento legado: bind da raiz do host com as
  exclusões/máscaras existentes para socket/superfícies de controle, estado e
  credenciais Percival; o gateway/MCP não recebe Docker socket. Isso não é isolamento
  total e preserva o risco indireto aceito em B23–B25.
- `mounts=[]` continua significando nenhum bind; paths explícitos continuam
  suportados e precisam ser estreitos. Apps stateless devem declarar/configurar
  explicitamente `[]`, sem depender do default amplo.
- Aumentar o escopo de um perfil já mais restrito para Full exige confirmação tipada
  e auditoria. Registros legados/existentes devem manter sua configuração efetiva;
  não migrar nem mutar runtime implicitamente.
- O contrato comum deve dizer que cada broker declara seu default; o default amplo é
  específico do broker Percival e não concede privilégios por metadata MCP. Owners
  dos consumidores devem confirmar seus perfis por app, inclusive Notes.
- Atualizar C01, C03 quando descrevem perfis de execução, o plano coordenador e os
  planos consumidores. Preservar o relatório de 2026-10-28 como snapshot histórico e
  acrescentar a decisão posterior como adendo, sem reescrever as evidências coletadas.

R-10 decide a política, mas **não autoriza mudança de código/runtime, piloto,
publicação ou deploy**. A implementação permanece pendente de contrato versionado,
testes de broker/consumidores e autorização operacional específica.
