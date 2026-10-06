# Guia operacional: migrar KG MCP para o Percival nativo

**Estado em 2026-10-06:** roteiro para cópias e preflight; ainda não prova
upgrade/rollback de bundles reais. O pacote atual é `nanobot-ai` 0.3.5;
`percival-ai` não foi publicado. Interface nativa no
[`plano F9`](plans/kg-integration-plan.md#f9--skills-documentação-migração-e-release).

**Commit candidato:** o commit **"feat(kg): close F9 with platform CI,
endpoint inventory and migration tests"** no `main` deste fork inclui a
reconciliação do snapshot, as 12 skills KG, o CLI `nanobot kg`, o
inventário de endpoints e a CI matrix de plataforma. A proveniência em
checkout limpo está comprovada (ver
[`docs/kg-release-notes.md`](kg-release-notes.md)); o que falta é o ensaio
em cópia de bundle real (itens B6/B7 do plano de auditoria).

## Antes de tocar dados

1. Registre SHA/versão do fork, do `okf-bundle-core` legado, do cliente SPA e
   dos servidores CM/AK; exporte uma cópia de `config.json`, incluindo
   `tools.mcpServers` e presets/sessões que escolhem MCPs. Nunca copie segredos
   para documentação ou relatórios. Anote os pais das raízes
   `COLLECTIVE_MEMORY_ROOT`, `ACQUIRED_KNOWLEDGE_ROOT` e `kg.cmRoot`/`kg.akRoot`:
   as variáveis legadas têm precedência sobre config, que tem precedência sobre
   workspace. `kg doctor --json` avisa se env e config divergem.
2. Pare **todos os escritores** MCP e nativos. Faça snapshot verificável de
   **cada bundle completo**, incluindo `.git/`, `notes/`, `sources/` (binários
   fora do Git), `assets/`, `_archive/`, `log.md`, `graphify-out/` e arquivos
   ocultos. Preserve permissões e symlinks; armazene hash/inventário de
   arquivos e localização do backup fora do bundle. Não rode `bundle init` em
   destino com conteúdo: o comando o recusa.
3. Restaure cópias em workspace descartável; configure roots para os **pais**
   das cópias, evitando env vars conflitantes. Não abra escritor legado e
   gateway nativo no mesmo bundle. Confirme `nanobot kg doctor --json` e
   `nanobot kg bundle path cm` / `... ak` antes de qualquer write.

## Configuração e capacidades

`kg.mode` aceita `native` (padrão), `mcp` e `both`. `kg.cmRoot` e
`kg.akRoot` apontam para o **diretório pai** dos bundles. `kg.cmEnrichEnabled`
(padrão `true`) e `kg.cmEnrichTimeoutS` (45 s) controlam enrich; as flags
`kg.akImageCaptionEnabled` e `kg.akAudioTranscribeEnabled` não criam suporte
de modalidade no provider. `tools.restrictToWorkspace` impede acesso a roots
fora do workspace sem autorização apropriada. Conferir
[`nanobot/config/kg.py`](../nanobot/config/kg.py) e
[`nanobot/agent/kg/roots.py`](../nanobot/agent/kg/roots.py) antes de alterar
roots, em especial se variáveis legadas ainda estiverem exportadas.

Operações determinísticas e leitura de bundles não exigem credencial de
modelo. Enrich requer runtime do turno; caption de imagem exige
`supports_modality("image", model)` e runtime, sem fallback implícito.
Transcrição de áudio nativa retorna `unsupported_capability`. `diskcache`
é cache opcional/lazy para multimodal; `markitdown` é CLI externo opcional
para converter formatos documentais durante ingest (instale e valide o
binário antes de usar esse path). `networkx`, `markdown-it-py` e as deps do
core estão no pacote Python. O lock KG ainda usa `fcntl`: este gate só
executou em Linux; Windows e macOS carecem de validação explícita antes de
anúncio multiplataforma. A SPA em dev requer Bun; wheel/sdist incluem assets
prebuilt quando a integridade do snapshot passa.

## Ensaio na cópia

1. Compare `cm_notes_read`, `cm_notes_search`, `memory_stats`,
   `ak_source_list`, `ak_source_read(source_id, chunk_index)`,
   `ak_source_stats` e navegação de grafo com o legado sobre **mesmas notas**.
   Use `nanobot kg graph rebuild cm --json` e `... ak --json` apenas na cópia;
   compare contagens, dangling edges e `graphify-out/graph.json` sem esperar
   `graph.html`/rótulos cluster-only. Teste uma nota protegida P11.
2. Para frontmatter AK antigo com `related`/`contradicts`, faça
   `nanobot kg ak-migrate-lateral-links --json` (dry-run padrão). Revise
   `skipped_targets`: `cross-bundle` e `true-broken` não são movidos.
   Use `--apply --json` apenas na cópia após o snapshot; confira `notes/`,
   `log.md` e Git, e repita o dry-run para verificar idempotência.
3. Exercite uma atualização com `cm_notes_write` e CAS, um link AK e
   navegação pelo gateway + SPA autenticados; valide bytes dos binários
   em `sources/` e assets depois. Preserve commits e hashes antes/depois.
   Enrichment usa provider/modelo do **turno**; imagem só se o provider/modelo
   anunciar suporte. Áudio é `unsupported_capability`, não resultado real.

## Cutover e rollback

Somente depois do ensaio e aprovação de release: faça novo snapshot com
escritores parados; selecione `kg.mode="native"` (padrão) e reinicie gateway.
`tools.mcpServers` usa os identificadores dos MCPs legados; o filtro nativo
suprime apenas CM/AK, não outros MCPs. `both` serve para diagnóstico, mas não
é modo seguro para dois escritores. Para novos bundles vazios use
`nanobot kg bundle init cm` e `... ak` com confirmação; não use em dados
existentes.

Para voltar: pare gateway e qualquer escritor nativo; restaure config/binário
compatíveis, selecione `kg.mode="mcp"` com os servidores instalados. Primeiro
teste **leitura de uma cópia** do bundle pós-nativo no servidor legado. Se
schema ou artefatos não forem compatíveis, restaure o snapshot íntegro
anterior em vez de reusar os dados pós-nativo. Isso perde writes feitos depois
do snapshot: reconcilie-os manualmente a partir do Git/log e cópia pós-nativa,
sem sobrescrever o backup. Nunca remova entry points/binários legados antes
de concluir esse exercício.

Config e modos: [`nanobot/config/kg.py`](../nanobot/config/kg.py). `cmEnrichModel`
e `cmEnrichBaseUrl` antigos devem ser removidos; configure o provider/preset
do agente. Raízes externas exigem política de workspace apropriada. O acesso
HTTP da SPA usa bootstrap do gateway e bearer em GET; escritas usam WS
autenticado. A chave de bootstrap não deve ir para URL, log ou localStorage.
