# Diagnóstico do KG no runtime Docker local — 2026-10-11

## Conclusão e escopo da evidência

O gateway serve a SPA, mas **não encontra nenhum dos dois bundles nativos no
workspace que seleciona**. Isso explica os dois indicadores *down*, as leituras
que falham e o 404 na tela Brain. Não há evidência de que os dados da memória
normal do agente tenham sido perdidos: `memory/` e os bundles KG são armazenamentos
distintos. O código também exige um rebuild explícito para produzir/atualizar o
artefato do grafo. A investigação foi somente de leitura; não houve inicialização,
migração, rebuild, alteração de configuração nem login automatizado.

### Observações reproduzidas

- Capturas `~/Pictures/screenshot-2026-10-11_21-49-38.png` até
  `screenshot-2026-10-11_21-50-22.png`: `/kg-interface/` renderiza;
  *Memories down* e *Learning down*; Notes/Stats exibem *Network error*;
  Brain exibe *Network error: HTTP 404*; Home exibe zero notas.
- O container `nanobot-nanobot-gateway-1` estava healthy e tinha apenas o bind
  `/home/bill/.nanobot` -> `/home/nanobot/.nanobot` (rw). A imagem declara a
  revisão `c63b8b680d0f12ca1c2b6c271a56ea16ff4bd2d4`; os arquivos KG
  relevantes não mudaram entre essa revisão e o checkout consultado.
- `docker exec nanobot-nanobot-gateway-1 nanobot kg doctor --json` retornou
  `status=fail` para **cm** e **ak**, ambos com `bundle not initialized` sob
  `/home/nanobot/.nanobot/workspace/.collective-memory` e
  `/home/nanobot/.nanobot/workspace/.acquired-knowledge`. `kg bundle path cm/ak`
  confirmou esses destinos. No bind do host, ambos estão ausentes; `memory/`
  existe. Não foi feita busca irrestrita por possíveis bundles legados em outros
  locais nem inspeção de seu conteúdo.
- GET anônimo à SPA retornou HTTP 200 (`text/html`); GET anônimo a
  `/kg-interface/api/memory/healthz` e `/memory/graph` retornou HTTP 401 JSON.
  Isso confirma listener e proteção das rotas, mas **não** testa a resposta
  autenticada diretamente. O HTTP 404 visto na captura e a saída do doctor são
  consistentes com a ordem do dispatch descrita abaixo.

### Cadeia causal no código

1. `nanobot/agent/kg/roots.py` resolve o parent por
   `COLLECTIVE_MEMORY_ROOT`/`ACQUIRED_KNOWLEDGE_ROOT`, depois `kg.cmRoot`/`kg.akRoot`,
   depois workspace; adiciona `.collective-memory` ou `.acquired-knowledge`.
   `nanobot/webui/kg_http.py::_root` usa especificamente
   `workspaces.default_scope()`, sem a seleção da sessão ativa. Se o root não
   contém `notes/`, recusa-o. O Compose monta `~/.nanobot`, mas não cria os
   bundles nem importa a memória anterior (`docker-compose.yml`, `entrypoint.sh`).
2. Em `KgGatewayBridge.read`, **até `healthz` passa por `_root` primeiro**:
   root ausente produz 503 `kg_unavailable` no healthz e 404
   `bundle_or_note_not_found` nas outras leituras. O 404 no Brain não demonstra
   que a rota `/graph` esteja ausente: ela está registrada em `_read`.
   `graph/data` não chegou a ser consultado. A autenticação bearer precede
   essa resolução em `ws_http.py`.
3. A SPA reduz qualquer falha de health a boolean `false` (`api.ts::healthAll`),
   mostra *down* (`useHealth.tsx`) e trata falhas das listas/stats como
   *Network error* (`NotesList.tsx`, `StatsView.tsx`). `HomeView.tsx` usa
   `memory?.notes_total ?? 0` e uma lista vazia para falha: **zero não é uma
   medição válida nesse estado**. `GraphView.tsx` só mostra 404 genérico.
4. Depois de inicializar, `graph_artifact` apenas lê
   `graphify-out/graph.json`. `/graph` retorna `{exists:false}` se faltar;
   `/graph/data` retorna 404. Só `nanobot kg graph rebuild cm|ak` escreve o
   arquivo (`nanobot/cli/kg.py`, `nanobot/agent/kg/maintenance.py`). O builder
   varre `notes/`, não `workspace/memory/`; novas notas ou links não disparam
   rebuild. Uma inicialização vazia seguida de rebuild produzirá **um grafo
   vazio válido**, não conhecimento preexistente.

## Solução recomendada, em ordem

### 1. Recuperação operacional (sem converter dados implicitamente)

Determinar primeiro **qual conjunto de dados deve ser a fonte**: um par CM/AK
legado a migrar ou bundles novos e vazios. O operador é responsável pelo ensaio
B6/B7 com cópias de dados reais e decisão de cutover, conforme
`docs/kg-migration.md` e `docs/percival-governance.md`. Inventariar roots,
`kg.mode`, overrides de env, workspace padrão da WebUI e paths efetivos do
gateway sem expor segredos. Se os bundles já existem fora do bind, montar seus
**parents** ou configurar `kg.cmRoot`/`kg.akRoot` para paths visíveis no
container; não apontar ao próprio bundle. Com escopo WebUI restrito, roots
externos são atualmente recusados pela bridge, mesmo que tools tenham grants:
usar um parent dentro do workspace autorizado ou projetar a concessão
específica na bridge antes de depender de roots externos. Parar outros escritores
e ensaiar/validar em cópias antes do cutover.
Se for uma instalação realmente nova, inicializar cada bundle no workspace
escolhido via `nanobot kg bundle init cm|ak` com confirmação, conferir `doctor`
e só então criar/ingerir notas explicitamente. Nunca executar init sobre
destino com dados e não tratar `memory/MEMORY.md` como bundle KG.

Na cópia autorizada: executar `nanobot kg doctor --json`, comparar contagens,
notas e proveniência; executar `nanobot kg graph rebuild cm --json` e `... ak
--json`, conferir nodes/edges/dangling e os dois `graph.json`; repetir leituras
pela SPA autenticada e uma mutação CAS sob supervisão. Decidir cutover/rollback
somente com as evidências do roteiro B6/B7. As ferramentas do agente podem ser
testadas no workspace da sessão separadamente da SPA.

### 2. Corrigir o contrato de estado (gateway + SPA)

- Centralizar um diagnóstico read-only de **cada** bundle no gateway:
  `ready`, `uninitialized`, `inaccessible`, `native_disabled` e estado do
  artefato `missing`, `stale`, `valid` ou `invalid`; não enviar paths do host
  desnecessários ao browser. Manter 401 sem bearer, 403 para restrição, 404
  para nota realmente ausente e 503 para bundle indisponível. Health deve
  diferenciar readiness de disponibilidade do processo e não exigir que o
  frontend adivinhe a causa pelo 404. Aproveitar a lógica `doctor` sem
  efeitos colaterais, com limites e testes por workspace.
- Exibir **“bundle não configurado/inicializado”** com instrução de setup,
  **“grafo não gerado”** quando há notas mas falta o artefato, e **“sem notas”**
  apenas quando uma consulta bem-sucedida retorna zero. Preservar motivo/status
  por adapter em `healthAll`/hooks, não converter erro em zero; GraphView deve
  distinguir bundle ausente de grafo ausente/corrompido. Evitar que um lado
  indisponível impeça visualizar o outro.
- Acrescentar teste do listener autenticado para root CM/AK ausente, root
  inicializado vazio, artefato ausente, caso com notas e grafo, e workspace
  restrito; no SPA testar a UI desses quatro estados. Os testes F6 atuais
  (`tests/kg/test_gateway_f6.py`) sempre criam os dois roots e os dois
  `graph.json`, portanto não capturam o cenário das capturas.

### 3. Tornar a visualização sustentável

Definir e implementar política de atualização para `graph.json`: após writes
confirmados nos serviços CM/AK, invalidar o artefato e agendar rebuild
coalescido por bundle sob lock, mantendo último artefato válido até a
substituição atômica. Mostrar `last_build`/estado stale; permitir rebuild manual
supervisionado. Testar writes concorrentes, falha de rebuild, restart,
integridade de Git/notas, limites de 8 MiB e render D3 em ambos os bundles.
Não executar rebuild no GET nem prometer atualização em tempo real enquanto
escritores legados editarem arquivos sem passar pelo serviço nativo.

Se a intenção for que a SPA siga o projeto atualmente selecionado na WebUI,
projetar seleção autenticada de escopo no gateway (identificador validado do
lado do servidor) para GET e WS; hoje ela sempre usa o workspace padrão.
Revalidar permissões por leitura/escrita, não aceitar paths arbitrários do
browser. É um requisito de produto a confirmar antes de mudar o escopo.

## Critérios de aceite e limites desta análise

1. Com dois bundles inicializados no workspace selecionado, `kg doctor`
   retorna `ok` (ou `warn` apenas por grafo ainda ausente); health autenticado
   diferencia configuração e retorna ready; Notes/Search/Stats funcionam mesmo
   com grafo ausente. Zero só aparece após resposta válida de lista/stats.
2. Com notas CM/AK de fixture e rebuild, `graph/data` retorna nodes/links e
   Brain renderiza ambos, preservando auth 401 e controles de workspace; após
   alterações, exibe estado stale ou grafo regenerado conforme a política.
3. Para a operação real, B6/B7 em cópias com backup e rollback testados,
   depois gates `pytest`, `basedpyright nanobot`, `ruff check .` e
   `bun run test`, `bun run lint`, `bun run build`, browser smoke autenticado no **SHA/imagem
   candidata**. O gateway healthy, a SPA 200 e os testes sintéticos F6/F7
   históricos não satisfazem sozinhos esse aceite.

**Limitações da verificação:** sem credencial humana para exercitar as rotas
autenticadas ao vivo; nenhuma inspeção do conteúdo de bundles fora do workspace
montado; nenhuma verificação do modo KG/config/env efetivos além dos paths
resolvidos pelo CLI. Tentativa de executar os testes F6/CLI no checkout com
`uv run --no-sync pytest -o addopts='' ...` não iniciou: `.venv` local aponta
para um Python inexistente e `uv` não conseguiu remover `.venv/CACHEDIR.TAG`
por permissão. Não se registrou um resultado de testes como aprovado nesta
investigação.
