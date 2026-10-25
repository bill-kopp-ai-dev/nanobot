# Plano 1 — Prontidão local do produto

- **Estado:** ativo, consolidado em 2026-10-25 por solicitação de bill; execução das
  pendências abaixo não realizada nesta reorganização.
- **Objetivo:** resolver lacunas de produto e demonstrar autenticação, WebUI, KG e
  comportamento operacional em ambientes isolados, antes de qualificar os candidatos.
- **Dono:** bill decide escopo, recursos e aceite; agente implementa/verifica no
  repositório responsável quando a execução estiver autorizada.
- **Baseline documental:** `nanobot/main` em `5f77f438`, árvore inicialmente limpa.
  Estados técnicos são herdados dos relatórios datados, não nova inspeção de runtime.
- **Entrada/saída:** contratos I1/runtime 1 existentes → produto localmente verificado
  e limitações explícitas para o [Plano 2](2026-10-25-02-qualification-distribution-plan.md).
  Migração de dados reais, rollout e aceite no alvo foram diferidos; veja o
  [registro arquivado](closed/2026-10-25-03-deployment-operations-plan.md).
- **Rastreabilidade:** [análise e mapa integral da consolidação](../reports/2026-10-25-three-plan-consolidation.md).
  IDs L* são atividades atuais; IDs antigos identificam origem, não trackers paralelos.

## 1. Fronteiras e evidência herdada

I1/I2, implementação A–E de senha única, snapshot SPA limpo `d3b29843`, F1–F5
locais e D1–D12/F7 não são trabalhos a repetir. D11/F8 permanece administrativamente
encerrado; seus gates técnicos não executados continuam abertos aqui. A evidência
herdada conserva SHA/data e precisa de análise do diff para valer no candidato novo.

Referências de detalhe histórico: [senha única](closed/2026-10-11-single-password-acceptance-closure-plan.md),
[KG/MCP integrado](closed/2026-10-23-integracao-pendencias-kg-e-mcp-docker-plan.md),
[D11](closed/2026-10-24-d11-skill-operations-closure-plan.md) e
[resíduos Docker](closed/2026-10-25-docker-standardization-continuation-plan.md).
São especificações/evidências históricas; atualizações de execução pertencem a L*.

Esta campanha autoriza a organização documental. AUTH-P2 permanece adiado pelo
operador até retomada explícita; criar fixtures, invocar provedores, alterar outro
produto ou operar instâncias reais depende da autorização aplicável. O login do
browser-proxy SSH remoto permanece fora do escopo e fail-closed `remote_auth_required`.

## 2. Atividades e critérios de aceite

### 2.1 Preparação compartilhada e segurança do ensaio

| ID / origem | Entrega e aceite verificável | Estado / dependência |
| --- | --- | --- |
| L01 / D11 M-1, C8 | Apurar `notes_rm("x")` usando evidência anterior à chamada ou backup existente. A resposta não prova presença nem ausência de exclusão. Registrar conclusão ou inconclusão; rever a allowlist efetivamente read-only antes de novo dry-run. Distinguir auditoria do rehearsal D11 sem mutação de produto | **Aberto, prioridade alta**; bill/agente, acesso à evidência. Não usar Notes/vault real no novo teste |
| L02 / dependência MCP-B1/B4/B6, KG-A1 e AUTH | Preparar um harness Browser+HTTP/WS+gateway+broker reutilizável, com módulos KG/WebUI separados, estado sintético e reset por cenário. Chromium real para layout/E2E; CDP existente em `tests/kg/test_f7_browser.py` é prior art, não ferramenta WebUI pronta. Resultados identificam executor, SHA/assets, fixture e backend real | **Pendente**; agente. Reutilizar runner D11/DIND, sem presumir que um mesmo teste prova todos os gates |

O harness não monta `~/.nanobot`, `~/.positronic`, vaults ou credenciais reais. DIND
27.5.1 pinado, sem socket do daemon externo; só o broker acessa o socket interno.
Preflight verifica Client/Server no daemon, mounts, GID e namespace. Preparação comum
evita ambientes duplicados; cenários isolados evitam que rotação/revogações contaminem
os outros testes. `happy-dom`, driver CLI e health TCP não são Browser/protocolo real.

### 2.2 Autenticação e cliente MCP

| ID / origem | Entrega e aceite verificável | Estado / dependência |
| --- | --- | --- |
| L03 / AUTH-A1–A6, P2/P2-B–E | Executar a matriz de autenticação abaixo em volume/daemon DIND descartável Server 27.5.1; HTTP/WS real e elevação pela UI, sem chamar só o serviço in-process. Não usar VPS ou instalação persistente | **Adiado pelo operador**; confirmar renovação silenciosa antes do teste; L02 para Browser |
| L04 / MCP-B2, MCP-B5 | Completar os casos de componente/UX abaixo; observação de mounts distingue confirmado/divergente/indisponível, Full destacado e chave morta `mcpDocker.networkFixed` removida no `webui/`, não na SPA KG | **Aberto**; agente, reconferir cobertura no candidato. Pode começar antes de L02 |
| L05 / MCP-B1, MCP-B4, MCP-B6 | Uma campanha Browser WebUI+gateway+broker real **em fixture isolada** cobre mutações, oito famílias, acessibilidade e layout. Weather/OSM e terceiro servidor preservado **exercitado**, não só passivo; estados/audit/recovery verificáveis. Registrar teclado/foco e viewport estreito/largo, choices mounts/rede/env e efeitos reais | **Aberto**; L02 e correções L03/L04 aplicáveis. Um resultado por critério, sem repetir três campanhas; nenhum gestor vivo/VPS |
| L06 / MCP-B3, extensões I2/V04 | Matriz versionada atual/atual, novo/antigo e antigo/novo com fixtures independentes e faixa de protocolo declarada. Campo ausente não concede capacidade; schema incompatível é recusado/migrado explicitamente | **Parcial**; terceira direção e matriz faltam no snapshot. Revalidar após aquisição/schema do Plano 2 |

**Matriz obrigatória de L03:**

1. Verifier ausente recusa bootstrap/MCP; senha errada é recusada; `auth init`
   interativo em CLI do mesmo volume permite login/cookie/bootstrap. Token humano e
   token do broker distintos; gateway sem socket/CLI Docker.
2. Sem elevação ou com senha errada, mutação é negada; elevação válida permite
    operação reversível via manager/CAS **em fixture descartável**, `initialize`/
    `tools/list`/call segura e retorno da própria fixture, com auditoria redigida.
3. `allowRemoteAdmin=false`: WS autenticado/elevado de origem não-loopback é recusado,
   equivalente loopback funciona. Não reintroduzir endpoint/senha legados operator-admin.
4. Em fixture local, túnel e proxy TLS representativo: login e renovação pela sessão, cookie seguro,
   sem senha/token em URL, storage ou logs; senha só no login/elevação suportados,
   nunca no payload de mutação MCP. Sessão cookie atual não é o cookie legado vedado.
5. Confirmar se renovação silenciosa existe; se ausente, implementar sob autorização
   antes de declarar o critério satisfeito. Expiração rejeita requests e operações
   em WS aberto; revogação/logout encerra sessão/elevação conforme contrato.
6. `auth change`: senha nova aceita, antiga recusada; recriar gateway **e** sidecar
   com mesmo volume mantém login sem recadastro, estado/CAS e segregação do broker.
   Sem segredo humano em config/arquivos WebUI/storage. Cutover real não é parte de L03;
   AUTH-A7/P2-F foi diferido com os demais cortes reais.

**Checklist de L04:** install 409; falha/conflito no editor de host;
`stopped-persistent`; `image-missing`; `container-missing`; refresh falho;
cópia de digest; senha recusada; backup não restaurável; zero backups; viewport
estreito. O último caso usa L05 para layout real. A cobertura herdada 1/11 é datada,
não nova contagem. Teste backend de update 409 não prova UI de install 409.

### 2.3 KG nativo — dados antes de custo e migração

| ID / origem | Entrega e aceite verificável | Estado / dependência |
| --- | --- | --- |
| L07 / KG-A1, KG-A3 | Chromium prova 401 anônimo sem vazamento e, após login/bootstrap, aviso `bundle_uninitialized` diante do 503 autenticado, sem erro de rede nem zero fictício. Completar cliente SPA e teste de recusa do build fail-closed; provas GET/WS/Linux-only herdadas não são refeitas sem mudança | **Parcial**; L02. Não enfraquecer autenticação para obter o antigo “503 anônimo” |
| L08 / KG-A5 | Com fontes autorizadas, criar nota CM e Source/ExtractedNote AK, link, rebuild/navegação e `doctor --json valid` com conteúdo. Registrar identidade/proveniência da amostra sem publicar dados | **Bloqueado por dados**; bill fornece/autoriza, agente executa |
| L09 / KG-A2 | Benchmark em conjunto representativo/cópia de L08, duração/custo e escala; decidir limite/política de rebuild automático após escrita. Se adotado, desenho/implementação/teste próprios | **Aberto**, depende L08; rebuild automático não é flag existente desligada no snapshot |
| L10 / KG-A4 | Exercitar `audio_transcribe` com áudio real e provedor autorizado, ou obter aceite formal de paridade ASR não demonstrada. Registrar provedor/amostra/resultado sem expor chave/conteúdo | **Parcial**, bill fornece recurso/decisão. Stub não comprova paridade; ASR desacoplado do par do turno |

A cadeia ativa é L08 → L09. Migração/ensaio de bundle real (KG-A6) e release/upgrade/
EOL dos repositórios legados (KG-A7) foram diferidos junto com o rollout; critérios e
decisões anteriores permanecem no registro arquivado. A falta de dados KG não bloqueia
componentes UI nem qualificação de MCPs sem relação com esses bundles.

### 2.4 Skill operacional e resíduos de engenharia

| ID / origem | Entrega e aceite verificável | Estado / dependência |
| --- | --- | --- |
| L11 / D11-C3/C6/C9, ST-01–ST-16 | Após L01, dry-run **LLM real** em endpoint/fixture isolados, sem VPS/instância persistente e sem chamadas mutáveis: owner, pins, transporte, CAS, backup sintético e retorno da fixture corretos. Fixture HTTP com readiness deliberadamente falha; decisão bill sobre admin/bind/portas, sem alteração ativa presumida. Preservar matriz D11-C1–C10/ST com limites e origem | **Aberto**; endpoint isolado, L01 e política bill. Rehearsal determinístico 24 PASS/1 BLOCKED não fecha comportamento do agente |
| L12 / R08, D4 | Reproduzir acquire→tools-list interrompido e garantir evento terminal/reconexão/cardinalidade por owner/contexto. Os 7/150 sem terminal e HTTP 499 não provam órfãos | **Aberto**, trabalho no Positronic exige escopo daquele repo |
| L13 / R10, D5 | Decidir/anotar os dois relatórios históricos com link à correção do harness; preservar leitura do frame antes do EOF nos smokes. Não apagar evidência nem exigir migração FastMCP como fix obrigatório | **Decisão documental pendente**; bill/agente |
| L14 / R11, D6 | Substituir corrida do fixture SSH por espera de prontidão do sshd e demonstrar regressão determinística antes de fazê-la gate | **Pendente**; correção OpenSSH local encerrada não é reaberta |
| L15 / R13 | Reler commits/ambiente, reproduzir Ruff no runner D11, opcionais basedpyright e `.venv` reportados; corrigir só falhas presentes e executar checks canônicos/afetados no ambiente correto | **Aberto como reconciliação**, não falha runtime nova presumida |
| L16 / D10 residual | Corrigir/reexercitar smoke `install-local` no Positronic antes de recomendar CLI; preservar caminho TUI/delete/restore já documentado e não inventar comandos | **Pendente externo**, repo/owner Positonic e autorização próprios |

L11 reutiliza C1/C2/C4/C5/C7 e stdio C6 já demonstrados no rehearsal D11,
mantendo C8 limitado àquela fixture e C10 à candidata local identificada. Não repete
deploy Built-in/Enabled nem usa `restore-f1` para backup atual. Falta de instruções
no runtime deve produzir parada read-only, nunca pedido de socket Docker no gateway.
Compatibilidade restore-f1 só entra com decisão e cópia sintética próprias. O formato
de persistência/restore de secrets R07 e a validação do profile nginx em runtime de
produção R12 foram diferidos junto com backup/deploy.

## 3. Ordem recomendada e trabalho independente

1. **Primeiro:** L01; em trilha independente, L04/L06/L15 e preparação L02.
2. **Segundo:** resolver engenharia de renovação L03 e regressão L14; executar L03
   quando reautorizado, L07 e campanha L05 sobre harness comum.
3. **Em paralelo lógico:** L08 desbloqueia L09; L10 depende de amostra/provedor;
   L11 depende do endpoint e de L01. L12/L16 ficam explicitamente externos.
4. **Handoff:** consolidar resultados L* aplicáveis em D01/D03, apontando critérios
   ainda bloqueados. Mudança posterior I6/I7 reabre só os checks afetados L05/L06/L03.

Esta ordem é de dependências, não promessa de prazo nem autorização de execução
paralela por outros agentes. Prazo, orçamento e disponibilidade não foram definidos.
Bloqueio de uma trilha não paralisa as independentes nem equivale a aceite.

## 4. Verificação, riscos e encerramento

Cada execução registra item/origem, dono/data, repo/SHA/diff, contrato, fixture,
imagem/plataforma, teste esperado/observado, artefato redigido e próximo passo.
Checks de fonte: `pytest`, `basedpyright nanobot`, `ruff check .` e test/lint/build
dos clientes afetados; sem `ruff format`. Browser/E2E exige evidência no transporte
real, não mock; SKIP não é PASS. Reusar provas conforme [workflow](../../.agent/workflow.md).

Parar diante de owner/revisão divergentes, journal pendente, segredo em evidência,
interferência em dados reais ou dependência de relaxar compatibilidade/segurança.
CAS, backups privados, single-writer e socket só no broker continuam obrigatórios;
o risco indireto B23–B25 não desaparece por falta de acesso direto ao socket.

**Fecha este plano:** L01–L16 têm resultado/decisão verificável ou transferência
explícita de resíduo para dono aceito, com risco e critério preservados. Uma entrega
parcial deve listar os bloqueios; não pode ser anunciada como prontidão integral.
Isso não fecha CI/publicação/homologação do Plano 2; cortes e aceite no alvo foram
retirados do escopo ativo, sem condicionar o trabalho local a VPS.

**Próxima ação:** obter evidência pré-chamada M-1 e preparar o harness compartilhado;
L04/L06/L15 são os primeiros trabalhos locais independentes quando autorizados.
