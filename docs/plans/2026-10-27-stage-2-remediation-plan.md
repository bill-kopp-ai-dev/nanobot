# Stage-2 — Remediação do Percival (`nanobot`)

**Data / revisão:** 2026-10-28 / 1.3.
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
arquivos. A reconciliação final dos owners L*/D* ainda depende de bill; não criar um
segundo tracker nem restaurar exclusões automaticamente.

## 2. Preparação obrigatória da execução

- [ ] Ler `AGENTS.md`, `.agent/workflow.md`, runtime contract, runbook e handoff;
  reconciliar com bill os trackers L*/D* localmente excluídos. A leitura foi feita;
  os trackers ausentes não foram restaurados e sua reconciliação segue pendente.
- [x] Registrar SHA/worktree, ambiente e owner técnico. Baseline de execução:
  HEAD `8c2ac64b68e8428dd1ed38e4474a7e4c91f26720`, worktree dirty preexistente;
  Python 3.12.14 em `nanobot-stage2-env`; owner executor técnico local, decisões
  com bill. O caso 143 foi reproduzido antes da correção.
- [x] Distinguir IaC **D-01..D-06** de Percival **D01..D12** e usar o mapeamento
  A-001→L06/D08, A-002→L02, A-006→L14/L15/D03 e as dependências das ações abaixo.
- [x] D-05 continua pendente para a prova vertical/piloto. Bill autorizou apenas
  o ensaio local descartável DinD; A-001 foi corrigida antes da integração sintética
  com o broker. Nenhum piloto foi executado.

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
| A-008 | F-008 / P2 | Reancorar triagem do Medium no candidato exato, hashes/código/testes e SBOM/scan | D04 histórico; DB/scanner atuais | Decisão por CVE/artefato; evidência dos bytes corrigidos; sem mudar metadata para ocultar finding ou reaproveitar waiver de outra imagem |
| A-009 | F-009 / P2 | Integrar catálogo, aquisição, policy independente e export no manager/broker existentes; CAS/migração explícita | D07/D08/D09; S2-C01/C02/C03; etapas 2/4/5 IaC | Matriz negativa de origem/digest/policy; export atômico sem segredo; estado canônico único; local-only permanece até contrato aprovado |
| A-010 | F-010 / P2 | Homologar bridge por app, método e deadline; erro/cancelamento/EOF e attach em `broker.py`/client/MCPProvider | D08; app selecionada, receita isolada; etapa 5 IaC | Correlação de respostas, calls concorrentes, EOF/timeout sem attach órfão; resources/prompts/streaming testados se oferecidos, senão recusados/declarados |
| A-011 | F-011 / P2 | Especificar restrições do produto e entregar requisito de preflight de writers/instâncias à IaC; produto testa o contrato que controla | Dono IaC implementa bundle/preflight na etapa 3; runtime 1 | Fixture recusa segundo writer e segunda instância no daemon antes de mutar; mudar nome Compose não é isolamento de instalação |
| A-012 | F-012 / P2 | Definir e ensaiar shutdown/recovery carregado no broker, preservando store/journal e dados | Escopo I8 carregado a reautorizar; S2-C01 | Calls ativas têm término/erro limitado documentado; restart reconcilia operação sem duplicação; não confundir idle/crash sintético com recovery real |

### 3.1. Dependências recebidas de outros projetos

Estas subtarefas complementares não alteram as 12 ações de origem.

| ID | Origem / execução aqui | Aceite compartilhado |
|---|---|---|
| S2-NB-X01 | AgentMail A-006/A-008; Research A-005/A-009; Khan A-001/A-002/A-008; OSM A-008 e Weather A-005: implementar perfis explícitos de mounts, init, secrets por arquivo e lifecycle conforme S2-C01 | API stateless sem bind do host (`mounts=[]`); vault/workspace com bind estreito; nenhum caminho protegido reaberto; credencial por referência; defaults legados preservados ou migração aprovada; teste do consumidor |
| S2-NB-X02 | Khan A-005 e gates de qualificação dos MCPs: receber scans/manifests por candidato e coordenar o CI do gateway quando exigido | Evidência por SHA/image ID/manifest digest e DB; CI remoto não fechado por teste local; retorno para cada plano MCP |

Rotação D-04 é pessoalmente do owner do broker; implementar entrega por arquivo
não revoga a chave anterior. Nunca incluir o segredo em evidência ou plano.

## 4. Ordem dos lotes e dependências

1. **Lote NB-1:** A-001, A-003 e A-006; A-002 após receita de ensaio adequada.
   O P0 deve estar comprovadamente fechado antes da integração pelo broker.
2. **Lote NB-2:** A-005 e S2-NB-X01 com revisão mínima de S2-C01; A-004 e A-008
   na qualificação. A-007 prepara inventário sem trocar pins reais.
3. **Lote NB-3:** A-009/A-010 após contratos/ADR; A-011 com a IaC, A-012 após
   retomada de escopo; S2-NB-X02 com candidatos e gate de distribuição.
4. Piloto Percival + Notes só em plano próprio depois de IaC D-05/D-06 e
   condições Notes. Este documento não cria receita operacional de piloto.

Alterações em ownership podem impedir adoção de recursos legados: recusar adoção
não comprovada é preferível a remover recurso de outro dono. Dados e rollback são
preservados. Sem prazo/horas prometidos; dimensionar por lote com bill (IaC D-06).

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
  privado indicado abaixo. O HEAD não foi commitado e continua dirty.
- [ ] Registrar revalidação à seção 9 do relatório de origem após revisão de bill;
  preservar baseline e veredito histórico. Decisões/pendências e respectivos owners
  já constam no estado por ação desta revisão.

| Data / owner | Ações / achados | SHA inicial → final | Mudança e evidências locais | Resultado / V-* / pendências |
|---|---|---|---|---|
| 2026-10-28 / executor local + bill | A-001/A-002/A-003/A-004/A-005/A-006/A-008 verificadas localmente; A-007 parcial | `8c2ac64b68e8428dd1ed38e4474a7e4c91f26720` → mesmo HEAD, worktree dirty; candidato F2 source-diff `3cf4719bf4bdf7b2fd35ae77f7e5aa071bfbc3b8e5ff53563c45d29883577b1a` | Gateway `sha256:301d1a58d6e6e6682c728facc60df47bef72370017e7d7bcec99f1ef898367ac`; broker `sha256:e9343df917b971a6a907670f8029bbff3aabb1ef09d0cf669339802c30636d88`; smoke Engine 27.5.1 completo em `~/.positronic/runtime/tmp/opencode/percival-stage2-8c2ac64/i2-_pclfmoo/results.json`; pytest 9.209 + CLI 160, BasedPyright/Ruff/WebUI/TUI gates verdes | A-007: Bill autorizou list, mas sessão WebUI autenticada não está conectada, então nenhuma chamada/recovery foi executada; A-009–A-012 dependentes/abertas; sem piloto, CI remoto, release, push ou runtime real |

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
