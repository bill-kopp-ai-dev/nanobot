# Stage-2 — Remediação do Percival (`nanobot`)

**Data / revisão:** 2026-10-27 / 1.0.  
**ID / estado:** S2-NB / planejado; execução não iniciada.  
**Checkout executor:** `/home/bill/Projects/nanobot`.  
**Responsável:** executor técnico Percival a designar por bill; decisões de produto/operação com bill.

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

Este plano é emitido documentalmente agora e executado futuramente neste checkout.
Não retoma deploy/VPS/cutover, I3/B13 ou gates adiados. É um recorte rastreável dos
achados, a reconciliar com os owners L*/D* dos dois planos ativos citados em
`AGENTS.md`; estes arquivos estão localmente excluídos na emissão. Não criar um
segundo tracker de implementação nem restaurar as exclusões automaticamente.

## 2. Preparação obrigatória da execução

- [ ] Ler `AGENTS.md`, `.agent/workflow.md`, runtime contract e handoff disponíveis;
  identificar tracker vigente e reconciliar referências a planos/ADRs removidos
  com bill, preservando alterações preexistentes.
- [ ] Registrar SHA/worktree, ambiente pinado pelo lock/CI e responsável de cada lote.
  Reproduzir o caso de falha antes da correção; discriminar defeito de ambiente.
- [ ] Distinguir decisões IaC **D-01..D-06** dos gates históricos Percival
  **D01..D12**. Mapear cada A-* ao L*/D* aplicável, com um único owner.
- [ ] Confirmar receita do ensaio quando houver Docker privilegiado/daemon real.
  IaC D-05 continua pendente; não executar piloto nem receita DinD implicitamente.
  O P0 A-001 precede qualquer ensaio integrado via broker com MCPs.

## 3. Backlog integral e critérios de aceite

Estado inicial de todas as linhas: **não iniciada**; condições externas indicadas
continuam pendentes. Prioridade é a da ação de origem, não uma nova classificação.
Áreas abaixo são as apontadas pelo relatório; confirmar caminhos no SHA executor.

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

- [ ] Regressões dos caminhos observados falham antes/passam depois, sem copiar a
  implementação nos testes; repetir os cenários `V-*` afetados no candidato.
- [ ] Executar gates locais declarados (`pytest`, `basedpyright nanobot`, `ruff check .`)
  no ambiente suportado; confirmar escopo real CI e gates UI/MCP afetados. **Não
  executar `ruff format`**. Não registrar contagens históricas como atuais.
- [ ] Build/start/probes/signals/config/dados com fixture sintética quando o lote
  os alterar; gateway e broker são imagens distintas e têm proveniência própria.
- [ ] Reconciliar `V-BUILD`, `V-RUN`, `V-CONFIG`, `V-DATA`, `V-PILOT` e os limites
  `V-MCP`/`V-FUNC`/`V-REUSE` de agente. Piloto ausente permanece não avaliado.
- [ ] Runtime real só pela interface do owner, após leitura do runbook operacional,
  revisão/CAS, autorização e backup; sem deploy, push ou publicação implícitos.

Aceite local pode ser entregue antes dos externos. Ações transferidas, sem
evidência de seu dono, continuam abertas; remediação integral não está concluída.

## 6. Penúltima etapa — documentar a execução neste plano

- [ ] Atualizar ações/lotes, tracker L*/D* mapeado, comandos/ambiente, testes,
  SHA inicial/final, resultados e limites; anexar evidências sanitizadas locais.
- [ ] Registrar decisões/pendências com dono; acrescentar revalidação à seção 9 do
  relatório de origem quando autorizado, preservando baseline e veredito histórico.

| Data / owner | Ações / achados | SHA inicial → final | Mudança e evidências locais | Resultado / V-* / pendências |
|---|---|---|---|---|
| Pendente | A-001–A-012; S2-NB-X01/X02 | A registrar | Nenhuma execução por esta emissão | Não iniciada |

## 7. Última etapa — atualizar o plano coordenador

- [ ] Reler o [stage-2 geral](../../../positronic-bean-IaC/docs/plans/2026-10-27-iac-v1-stage-2-remediation-plan.md);
  atualizar **S2-NB na seção 3** e acrescentar retorno na **seção 7**, com ações
  verificadas/abertas, SHA/evidências, dependências liberadas e condições externas.
- [ ] Informar efeitos sobre M1/etapas 2–5; preservar retornos de outros projetos.
  Sem acesso à IaC: entregar resumo e ficar **aguardando sincronização**. Somente
  declarar concluído quando os aceites e o retorno estiverem atendidos; registrar
  parcial/bloqueado se houver pendências, sem converter transferência em solução.
