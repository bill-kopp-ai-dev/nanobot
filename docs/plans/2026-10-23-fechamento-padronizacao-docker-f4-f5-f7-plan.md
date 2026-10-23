# Fechamento da padronização Docker — F4/F5/F7

- **Preparado em:** 2026-10-23, por fusão dos dois planos de fechamento da padronização
  Docker: o [F4/F5](closed/2026-10-10-f4-f5-closure-plan.md) e o
  [F7 — aceite de operação](closed/2026-10-10-f7-operations-acceptance-closure-plan.md).
- **Estado:** abertura. A evidência de restore e rollback de F4 já existe; os itens abaixo
  permaneceram abertos e **nenhum** foi executado por este plano.
- **Plano de fase de origem:** [padronização Docker](2026-10-09-docker-standardization-refactor-plan.md),
  seções F4, F5, F7 e F8. Este plano substitui os dois planos de fechamento e passa a ser a
  fonte de verdade do quadro de pendências, hoje desatualizado no plano de fase.
- **Autoridade:** não autoriza reescrita de histórico, push, remoção de containers/imagens,
  rotação de credencial pelo agente, alteração de allowlist ativa, deploy em VPS, tag ou
  publicação. Cada mutação real exige a autorização aplicável e a interface suportada.
- **Numeração:** neste documento, F4/F5/F7 designam sempre as fases do plano de **padronização**
  Docker. As fases homônimas do plano MCP Docker first-class (arquivado) são outras e estão
  consolidadas no [plano integrado](2026-10-23-integracao-pendencias-kg-e-mcp-docker-plan.md).

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
| D1 | Rotacionar a credencial `operator-admin` e avaliar a exposição no histórico | Rotação pela interface suportada, autenticação com o segredo novo e invalidação do anterior sem registrar nenhum dos dois; inventário de commits/arquivos afetados; decisão explícita sobre histórico privado/remoto. Sem este gate, nenhuma mutação autenticada em instância real | F7 P0 / Extra | operador (rotação) + agente (inventário) | **parcial** — literal removido da árvore corrente; histórico ainda contém |
| D2 | Matriz de proveniência e política de identidade | Matriz repo → SHA → autor/committer bruto → atribuição confirmada → mapeamento aprovado → image ID/revision revisada; `.mailmap` apenas quando duas identidades forem comprovadamente a mesma pessoa; nenhuma reescrita de `main` publicado | F7 P1 (#10) | agente + operador | **parcial** — levantamento feito; falta decisão de atribuição |
| D3 | Permissão do Khan e projeção efetiva | Decisão registrada do operador entre as 12 tools atuais (com escrita/exclusão), somente leitura ou subset nominal, por gestor; lista efetiva verificada nos dois consumidores; `allowedProjects` não confundido com permissão de tool | F7 P2 (#7) | operador | **aberto** |
| D4 | Atribuição das duplicatas por container ID | Mapa container → processo/sessão cliente/registry/escopo, com ciclo de vida demonstrado e cardinalidade esperada documentada; limpeza apenas com autorização específica e zero referências confirmadas | F7 P2 (#8) | agente | **parcial** — sem órfãos confirmados no snapshot; ciclo de vida não demonstrado |
| D5 | Regressão Khan `tools/call` | Chamada MCP real de leitura com evidência no protocolo, não em filesystem/stderr; reproduzir em fixture sem tocar calendário real; investigar a versão do FastMCP/`mcp[cli]` ou registrar limitação aprovada | relatório F4/F5 | agente | **aberto** |
| D6 | Resíduo OpenSSH `CVE-2026-60002` no gateway (#11a) | Build do gateway em base corrigida com OpenSSH >= 10.4 e regressão de Percival Remote SSH na imagem, **ou** exceção individual documentada e aprovada; OpenVEX do gateway não estendido aos MCPs sem análise por imagem | F7 P4.2 (#11a) | agente + operador | **aberto** — bloqueia F7 e a publicação do 0.1.0 |
| D7 | Consolidar evidência de runtime nos artefatos finais | SIGTERM/PID 1 sem init duplicado (F6 relatou dois inits em Deep Research), stdio sem porta/TTY, healthcheck só em serviço HTTP, falha fechada e auth; evidência nos SHAs/imagens finais | F4/F5 closure, item 2 | agente | **aberto** |
| D8 | Reconciliar pins com builds de checkout limpo e promover | Rebuilder Notes/AgentMail (e qualquer candidato alterado) a partir de commit limpo, sem diff pré-commit na label; promover por gestor só com aprovação, canário e rollback independentes; reter o último bom e um par A/B de rollback conhecido | F7 P4.1 (#4, #6) | agente + operador | **aberto** |
| D9 | Exercitar o manual operacional e assinar a retenção | Walkthrough em fixture descartável de update, rollback, restore e falsa falha de health, comparando o texto do manual com os comandos e APIs instalados; política de retenção de imagens e revisão trimestral assinada | F7 P3 (#2, #5) | agente (redige) + operador (aprova) | **parcial** — [manual criado](../operations/mcp-docker-local-runbook.md) e vinculado; walkthrough não executado |
| D10 | `mcp server install-local` do Positronic falha silenciosamente | Corrigir o caminho suportado (yargs 18 + handler que imprime o literal `local`) e testar, **ou** registrar limitação/alternativa aprovada antes de declarar reinstalação recuperável; remover o workaround de edição direta de `registry.json` | F7 P3 / relatório F4/F5 | agente + operador | **aberto** |
| D11 | Skill de gestão F8 e instruções nos `AGENTS.md` | Matriz efetiva dos `AGENTS.md`; skill revisada com dry-run e fixture; ativação pelo operador | F8 (#9) | agente + operador | **aberto** — gate independente; não bloqueia F7 |
| D12 | Assinatura F7 e registro de encerramento único | Relatório único com `pendência → decisão → SHA/image ID → verificação → evidência → operador/data`, inventário pós-cutover sem segredos, URLs dos runs e declaração de risco residual; **aceite local**, **aceite VPS/deploy** e **aprovação B13 de release** registrados como atos separados | F7 P5 | operador (assina) + agente (consolida) | **bloqueado** por D1–D10, C1–C4 e A1–A9 |

## 3. Itens transferidos (fora de escopo, com dono)

| Gate | Dono |
| --- | --- |
| Actions remotas nos sete SHAs candidatos; inventário do VPS; migração/rollback de `~/.nanobot` → `.percival` no Engine 27.x; novo aceite do risco no alvo | [plano integrado, C1–C4](2026-10-23-integracao-pendencias-kg-e-mcp-docker-plan.md) |
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
- **D3** bloqueia a projeção efetiva do Khan e, junto com **D5**, o item 2 do aceite.
- **D6** bloqueia F7 e a publicação da primeira versão 0.1.0.
- **D7**, **D9** e **D10** são executáveis localmente com fixtures, sem dependência externa.
- **D11** não bloqueia F7, mas fica fechado no mesmo plano por pertencer à mesma padronização.

## 5. Riscos e critérios de parada

| Risco | Controle |
| --- | --- |
| Apagar evidência ao limpar fixtures | reter um par A/B de imagem conhecido por gestor antes de qualquer nova promoção; `docker image prune -a` e `system prune` nunca são atalho de limpeza |
| Confundir proxy de evidência com prova | verificação em filesystem/stderr não fecha `tools/call`; o critério exige protocolo MCP real |
| `chmod 777` de fixture local virar política de produção | registrar modo e owner reais no inventário antes de qualquer promoção |
| Estender o VEX do gateway aos MCPs | reavaliar findings por imagem e escopo; sem extensão automática |
| Reescrever `main` publicado | `mailmap` altera apresentação, não objetos nem SHA; reescrita é ato separado com autorização específica |
| Evidência de Engine 29 ser lida como gate de Engine 27.x | o overlay local não prova o alvo; o gate VPS é C2–C4, fora deste plano |

**Parar e escalar** se a credencial exposta ainda der acesso, se uma duplicata não puder ser
atribuída com confiança, se uma imagem de retorno não existir, se a observação divergir da
configuração, se houver Critical sem correção ou decisão, ou se a topologia do alvo divergir do
aprovado. Não eliminar incerteza por `docker rm`, waiver implícito ou edição manual de estado.

## 6. Registo de execução

_Vazio na abertura (2026-10-23). Registrar por item: data, responsável, SHA/imagem/digest,
comando, resultado, artefato de evidência, limitações e decisão do operador. Não declarar item
fechado por teste local, por `Client.Version` ou por ausência de runs._

Quando D12 for assinado, o relatório único deve substituir os snapshots de pendência hoje
dispersos entre o plano de fase, o relatório F4/F5 e os relatórios F7, mantendo os links.