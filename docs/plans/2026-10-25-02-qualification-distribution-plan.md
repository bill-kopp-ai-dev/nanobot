# Plano 2 — Qualificação, distribuição e aquisição

- **Estado:** ativo, consolidado em 2026-10-25; C1 aberto, distribuição não homologada.
  **I3 continua adiado** por decisão de bill; esta organização não inicia sua execução.
- **Objetivo:** um fluxo fonte → candidato → CI → publicação aprovada → digest
  homologado → aquisição autorizada, com identidade e evidência únicas por artefato.
- **Dono:** bill revisa contratos/recursos e assina B13; agente verifica/implementa
  nos repos autorizados. Mantenedores de core/MCP/IaC/índice conservam seus domínios.
- **Baseline:** revisão documental sobre `5f77f438`; snapshots Actions/imagens abaixo
  são herdados, não consultas novas a GitHub ou registry.
- **Interfaces:** [Plano 1](2026-10-25-01-product-readiness-plan.md) entrega provas
  locais. Publicação e aquisição homologada encerram o escopo ativo; promoção em gestor
  vivo, rollout e VPS foram diferidos no
  [registro arquivado](closed/2026-10-25-03-deployment-operations-plan.md).
  [Mapa de transferência](../reports/2026-10-25-three-plan-consolidation.md).

## 1. Fluxo único e limites

Este plano absorve C1 + F5/C1 + B5 remoto + AUTH-A8 em **D03**, e DIST-B6 +
distribuição I3/I5/I6 em D01/D04–D08. Não há checklist remoto paralelo nem novo
aceite do mesmo pull. Os escopos permanecem diferentes: C1 cobre sete repos;
a primeira distribuição I5 usa Weather/OSM, enquanto DIST-B6 exige decisão explícita
sobre os oito artefatos D8 ou um subconjunto. Selecionar dois MCPs não elimina os
outros quatro da obrigação C1 nem reduz B6 silenciosamente.

Contratos canônicos: [ADR I1](../Decisions/2026-10-23-open-iac-contracts.md),
[handoff](../iac-p0-contract-handoff.md), [runtime 1](../agent-runtime-contract.md),
[governança B13](../percival-governance.md) e
[política de postura](../Decisions/2026-10-09-docker-image-posture-policy.md).
I1/I2 e F5 implementação estão fechados nos escopos registrados; não são tarefas novas.

Fonte pública separada `percival`; desenvolvimento privado `bill-kopp-ai-dev/nanobot`.
GitHub atual `bill-kopp-ai-dev`, futuro `p-bean-labs`; Docker Hub `pbeanlabs`.
Core alvo `percival-gateway`/`percival-mcp-broker`. Nomes decididos não comprovam
contas, acesso, disponibilidade, schemas implementados ou publicações existentes.

Organização documental não autoriza login/settings, push de fonte, criação/transferência
de repo, publicação, aquisição em gestor vivo, promoção ou deploy. Credencial de push
fica só no CI protegido; pulls públicos usam ambiente anônimo limpo. Reautorização
I3 e execução B13/publicação continuam decisões explícitas, separadas.

## 2. Atividades canônicas

| ID / origem | Entrega e aceite verificável | Estado / dependências |
| --- | --- | --- |
| D01 / R01, DIST-B6 fase A | Decidir conjunto e método: oito artefatos ou subconjunto aprovado; pull independente versus aquisição por manager/índice **em fixture**. Matriz repo/SHA integral/versão/plataforma/labels/locks/bases/image ID/digests e evidências aplicáveis. Refixar após mudanças, não usar build F3/diagnóstico F5 como HEAD final. Pins A/B por consumidor e seleção para rollout foram diferidos | **Aberto**, bill + agente; preparação pode anteceder conclusão do Plano 1 |
| D02 / R06, R09, B13 preparação | Rever exposição de chaves válidas F0 D-4 antes da publicação; rotação permanece adiada e o risco aceito explícito. Decidir assinatura/proveniência, chave/identidade/verificação ou manutenção sem assinatura com limites; `.mailmap` já aplicado. Revisar owner/fonte pública, histórico/licenças/secrets, labels/attestations e notas finais do candidato. Inspeção de backups/migração de estado foi diferida | **Decisões abertas**, bill. R06 é distinto do segredo legado D1 já encerrado |
| D03 / C1, F5/C1 WP1–WP4, DIST-B5, AUTH-A8/P3 | Uma única matriz de Actions dos sete repos no SHA exato e confronto de artifacts; checklist §3. CI de conformance não publica. Registrar resultado por requisito de core/auth/MCP sem aceitar run de outro SHA | **Bloqueado por acesso/core**, Deep falho no snapshot; bill disponibiliza acesso, agente verifica |
| D04 / I3.1–I3.3, R03, DIST-B6 fase C | Pipeline protegido e candidato: PR build/test/scan sem push, SHA limpo/versão/SPA/locks/bases coerentes, Buildx `linux/amd64`, checks/scans/SBOM/proveniência nos bytes exatos. DB/scanner registrados; Critical/High bloqueiam sem correção ou waiver individual válido; OpenVEX restrito à imagem. Renovar evidência vencida antes de promoção | **I3 adiado**; partes R03 continuam por candidato. DB F3 herdada expira em 2026-10-26; não representa scan novo |
| D05 / I3.4, publicação I5.3, DIST-B6 fase D | Após D03/D04 aplicáveis e B13 por candidato/repo, publicar só imagens/versões autorizadas. Par gateway/broker completo; falha parcial não promove bundle. Sem substituir bytes de tag SemVer já distribuída; divulgação de fonte/URLs aprovada antes de assar labels no digest | **Não autorizado/não iniciado**; I3 adiado e acessos release necessários |
| D06 / I3.5–I3.6, DIST-B6 aceite | Pull anônimo por digest em daemon/cache descartável, verificação plataforma/labels/proveniência e smokes no artefato adquirido. Registrar índice OCI (se houver), manifest de plataforma e ID local separados. Quando D01 exige manager, exercitar D08 em fixture isolada. Homologar artefatos publicados pelo método aprovado; promoção em gestor vivo está diferida | **Pendente**, D05 e método D01; nenhuma publicação por esta revisão |
| D07 / I5.1–I5.6 | Template derivado do Weather, depois OSM; pipelines/README/licença/protocolo e `server.json` no schema oficial pinado. Índice determinístico versionado, dois oficiais homologados e um comunitário upstream por digest, sem mirror/reatribuição. Etapas incrementais §4 | **Pendente**, workspaces/owners a confirmar; releases usam D04–D06 por repo |
| D08 / I6.1–I6.8 | Adapter somente dados + aquisição tipada/restrita + consentimento/policy + commit manager/CAS + lifecycle/protocolo real **em fixture/manager descartável**. Critérios de segurança/timeout/compatibilidade na §5 | **Pendente**; primeiro MCP e índice mínimo D07 para prova real; sem alteração ou promoção em gestor vivo |
| D09 / I7.1–I7.4 | `capabilities.lock` derivado do estado canônico, schema/revisão/identidades comprovadas, export consistente/atômico sem secrets. Falha após config comitada fica “export pendente”, não repete install. Comparar drift localmente, sem restaurar estado ou implantar | **Pendente**; export local independente de D08. Restore diferido |
| D10 / MCP-B7 | Rever pin Arch de CI, registrar tabela de revisão e automação trimestral de issue/renovação ou adiamento explícito. Workflow agendado que reusa pin não o renova; conferir calendário antes de declarar vencimento | **Aberto**, agente/bill; se mudar workflow, refixar candidato D03 |
| D11 / F5/C1 WP5 | Atualizar handoff existente por Journal autorizado e CAS após reler revisão, sem append duplicado. Nota `20261025-193252-f5-conformance-ci-revalidation-local-fix-254a6f58-1d5` teve `JournalNoteError` e permaneceu antiga; registrar blocker se acesso negado | **Pendente externo**, agente/bill; não editar arquivos Journal nem escrever entre escopos sem grant |

## 3. D03 — CI e artifacts em uma campanha

1. Bill habilita/autoriza Actions core e autentica GitHub pelo fluxo interativo
   suportado, fora do chat. Confirmar conta e acesso read-only aos sete repos;
   push SSH não autentica `gh`. Não alterar mise trust como atalho sem aprovação.
2. Reler SHA da branch aprovada de cada repo imediatamente antes de consultar/disparar;
   `f3ad1590…` era snapshot, não candidato futuro. Consultar workflows aplicáveis reais
   (`ci.yml`, `kg-platform.yml`, `tui-release.yml` no core); dispatch só se suportado e
   autorizado. SPA não tinha Actions próprio: seus checks locais não viram run remoto.
3. Diagnosticar Deep CI #15 no SHA `defc943…` ou sucessor identificado: logs autenticados,
   primeiro teste/traceback, Python/uv/locks/comando; reproduzir offline/sintético.
   Corrigir causa demonstrada; se fonte muda, novo SHA/checks/run, sem mascarar falha.
4. Para cada repo: URL/ID, `headSha`, jobs/steps obrigatórios, plataforma e conclusão.
   Ausente/cancelado/skip de job obrigatório não é PASS. Cinco MCPs verdes no snapshot
   não provam HEAD posterior; core sem run não é verde.
5. Baixar arquivos originais, verificar integridade e comparar manifest/SBOM CycloneDX
   com SHA, imagem, labels, plataforma, hashes dos locks e bases pinadas. Core exige
   pares gateway/broker e `results.json` de runtime. Falta/mismatch mantém C1 aberto.
6. Registrar C1 uma vez em D03 e referenciar essa prova em D01/D05 e auth.
   Atualizar handoff D11 sem multiplicar notas; disponibilidade Journal não fabrica CI.

Snapshot herdado de 2026-10-25 (não reconsultado):

| Repo | SHA observado | Resultado e lacuna |
| --- | --- | --- |
| nanobot | `f3ad1590f36af054e1babaf97fdac82c5fb9a9ff` | Sem run; Actions fork desabilitado no snapshot. Refixar SHA atual |
| Notes | `83980418b3239be5476f6d347ceb8dad32d90e8e` | #10 verde; artifacts não confrontados |
| AgentMail | `68751b696b62b53fdcf893c3add9cf9e648e4391` | #30 verde; artifacts não confrontados |
| Weather | `144dd44078bea4c7ba35111e15442cfc6bf14398` | #29 verde; artifacts não confrontados |
| Khan | `919b6ab9bb1b12d3ee48aa95c4d97f9463a738d0` | #31 verde; artifacts não confrontados |
| OSM | `06484259a3bb5371c5c1551dcab0c23ccc166479` | Docker #22 verde; artifacts não confrontados |
| Deep Research | `defc9434487be4db7dbc13003db1709047297471` | #15/#14 pytest falho; teste/causa remota não identificados |

Fonte e histórico diagnóstico: [F5 revalidation](../reports/2026-10-25-f5-ci-conformance-revalidation.md).

## 4. D04–D07 — distribuição sem duplicar pipelines e homologação

- **Proteção:** revisão de ambientes/secrets/gatilhos/permissões mínimas; PR de origem
  não confiável não recebe push token (`pull_request_target` não executa código dele
  com secrets). Scan de secrets e vulnerabilidades complementa SBOM. Aprovação B13
  antecede push; licença/proveniência/histórico e metadados privados entram na revisão.
- **Mesmos bytes:** se publicar exige rebuild, repetir os checks no novo artefato;
  evidência do build A não homologa B. Fonte de versão `pyproject.toml`, `0.1.0` como
  intenção inicial, não release realizada; código posterior pode exigir nova versão.
- **I5a:** template extraído do Weather real e primeiro oficial publicado/homologado,
  usando D04–D06. `server.json` é para MCP no schema aplicável, não para core.
- **I5b:** índice mínimo com fonte revisada Markdown/YAML→JSON, IDs únicos, schemas,
  publisher/licença/versão/transporte/plataforma/digest válidos; sem placeholder nem
  release não homologada. Mesmas entradas geram mesmos bytes; timestamp vem de input
  estável. Catálogo e apps vinculados à mesma revisão/hash. URL HTTPS/raw em commit,
  não `blob/`. Pages/Registry/Docker MCP Catalog opcionais, com autorização própria.
- **I5c:** OSM oficial e um comunitário upstream homologados; seleção/licença/tools,
  credenciais fixture e releases A/B verificáveis. Não espelhar upstream por obrigação.
  Khan adicional exige gates próprios; OSM SHA curto/guards só se ainda reproduzíveis.
- **DIST-B6:** todos os artefatos de D01 precisam de digest e aquisição pelo método
  aprovado; não basta core+Weather/OSM se escopo escolhido ainda inclui oito imagens.

## 5. D08/D09 — aquisição, compatibilidade e lock

1. Reusar manager/broker: busca/inspeção/instalação/update configuram app/release
   homologados, não URL/comando livre. Loja WebUI não é requisito P0; mudanças na UI
   mantêm L05/L06. Rever consumidores `agent-docker`, `@latest`, presets e smoke legado
   antes de corrigir/retirar caminhos que contornem o manager.
2. Adapter valida schema/tamanho/timeout/origem/redirect/hash/revisão e impede URLs
   locais/metadata; Markdown não executa nem muda policy. Cache conserva revisão/data;
   snapshots de app/índice misturados não formam release instalável.
3. Consentimento local vincula publisher/tools/digest/plataforma/permissões/secrets
   por referência. Novo catálogo não ganha mounts/rede por omissão; preservar semântica
   `null`/`[]`/lista dos registros atuais. Recusar isolamento read-only/egress/limites
   não implementados. Schema 2 aprovado exige migração explícita e retorno por snapshot;
   `extra="forbid"` impede acrescentar campos a leitores antigos silenciosamente.
4. Aquisição tipada no broker, confiança/policy verificadas também no executor;
   argumentos estruturados registry/repo/digest/plataforma, sem shell/build/login push
   ou opções Docker livres. Spawn continua `--pull=never`; sem socket/CLI no gateway.
5. Pull longo não mantém lock de config; operação rastreável/idempotente, polling ou
   timeout compatível com cliente 30 s, downloads limitados; após timeout/cancelamento
   reconciliar antes de retry. Revalidar CAS/consentimento após rede e antes do commit.
   Cache residual não é instalação; mismatch/digest ausente/plataforma errada recusa.
6. Provar aquisição com cache vazio e `initialize`/`tools/list`/call segura pelo
   transporte real, não stderr/filesystem. Lifecycle completo nos três apps I5c:
   install/configure/status/call/disable-enable/update/rollback/remove e oito famílias
   existentes; toolsDisabled/opt-in persistente/confirmação tipada/dados preservados.
7. Homologar bridge por método/versão/sessão: sequencial/concorrente, stderr, EOF,
   timeout, restart, ausência de órfãos. Streaming/paginação/notifications/cancelamento
   ou HTTP só se provados; HTTP do broker não prova container MCP HTTP.
  8. Export D09 usa snapshot serializado, não `list()` assumido read-only (`recover_pending`
    tem efeitos). Allowlist sem env/secrets/mask hints/paths privados desnecessários;
    app_id distinto de server_id válido e instância; IDs locais sem RepoDigest marcados
    locais. Observação sem broker é desconhecida, não running inventado.
9. Export com ordenação estável/replace durável/revisão, sem antigo sobrescrever novo;
   falha de export após commit preserva lock anterior e recovery refaz só projeção.
    IaC/WUD não escreve esse lock. Restore do lock/estado real e recuperação em host
    ficam diferidos; lock nunca é suficiente para autorizar lifecycle de owner externo.

**Matriz negativa ativa:** PR/scan/waiver inválido; push parcial; índice/app
inconsistentes; origem não confiável; requisito sem enforcement; digest mismatch;
imagem/plataforma ausentes; 429/timeout/cache; concorrência/CAS/retry; bridge/EOF;
export atrasado/broker fora/falha após commit; owner externo sem permissão. Restore sem
backup/config/secrets é parte diferida. Casos V05/V06/V11–V19 herdados de I3/I5/I6/I7
ficam no escopo de qualificação; extensões de recovery/VPS seguem no
[registro arquivado](closed/2026-10-25-03-deployment-operations-plan.md) e na
[especificação IaC histórica](closed/2026-10-23-iac-alignment-execution-plan.md).

## 6. Sequência sem dependência circular

1. D01/D02 e D10 podem ser preparados; D03 intermediário não precisa esperar todo o
   produto, mas C1 final exige os sete SHAs finais. I3 continua adiado até retomada.
2. D09 export local pode avançar antes de registry/VPS. D07 I5a/I5b desbloqueiam
   primeira prova D08; I5c fecha a matriz dos três.
3. D08 pode usar **core candidato local rastreado** sobre MCP/índice publicados.
   Assim I6/I7 podem entrar na fonte final sem esperar publicação anterior do core.
4. Após engenharia incluída no escopo, refixar D01 → checks locais/scan e D03 final →
   B13 → D05 → D06; regressar D08/D09 em ambiente descartável contra o artefato
   publicado. Promoção/consumo em deployment real está diferido.
5. Homologação pública vem depois de publicar e encerra a distribuição. VPS/I9 e aceites
   no alvo foram diferidos; não são gates ativos nem pré-requisito circular de B13.
   Publicação intermediária autorizada não certifica código posterior.

## 7. Evidência e encerramento

Registro por D*: origem, repo/SHA integral, versão/contrato/bases/locks, image ID e
digests distintos, plataforma, run/headSha/artifacts/hashes, scanner/DB, resultado,
ambiente, decisão/dono/data e blocker. Raw privado, resumos sem secrets. Reaproveitar
evidência pelo diff, sem rebatizar execução antiga. Risco sem assinatura/rotação adiada
permanece explícito; documentação/triagem não é waiver de imagem.

Fecha D03 somente com sete workflows obrigatórios verdes e artifacts confrontados.
Fecha distribuição apenas com D01/D04–D08 aplicáveis atendidos, não pelo push.
O escopo ativo termina na qualificação e homologação dos artefatos em ambiente
descartável. Rollout, backup/restore de estado real, migração KG, EOL legado, VPS e
aceite no alvo foram diferidos no registro arquivado, sem execução imediata. Decisões
pré-publicação e riscos permanecem. Não certifica Positronic nem implica cutover.
Não há novo orçamento/prazo aprovado; estimativas antigas de B5/B6 não foram
revalidadas e não são calendário contratado.

**Próxima ação:** bill decide conjunto/método D01 e libera acesso D03; agente prepara
matriz/confronto. D04/D05 core aguardam a retomada explícita de I3.
