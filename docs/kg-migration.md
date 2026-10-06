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
`kg.akImageCaptionEnabled` habilita a tool de imagem (sujeita ao suporte do
modelo do turno); `kg.akAudioTranscribeEnabled` habilita a tool de áudio.
Para áudio, configurar `transcription.provider=groq` (padrão),
`providers.groq.apiKey` ou `GROQ_API_KEY`, e opcionalmente
`transcription.model` (`whisper-large-v3` por padrão; `whisper-large-v3-turbo`
para menor custo) e `transcription.language`. `tools.restrictToWorkspace` impede acesso a roots
fora do workspace sem autorização apropriada. Conferir
[`nanobot/config/kg.py`](../nanobot/config/kg.py) e
[`nanobot/agent/kg/roots.py`](../nanobot/agent/kg/roots.py) antes de alterar
roots, em especial se variáveis legadas ainda estiverem exportadas.

Operações determinísticas e leitura de bundles não exigem credencial de
modelo. Enrich requer runtime do turno; caption de imagem exige
`supports_modality("image", model)` e runtime, sem fallback implícito.
Áudio AK envia os bytes à API da Groq mesmo se o modelo do turno não for
Groq; `ak_audio_transcribe` usa `transcription.language` (ou `pt` se não definida)
por padrão e aceita um código ISO-639-1 de dois caracteres. Com STT desativado, sem chave ou outro provider
configurado retorna `unsupported_capability`; falha de transcrição não
produz uma nota de ingest. O limite padrão de upload é 25 MB
(`transcription.maxUploadMb`); confira o limite do plano Groq antes de
aumentá-lo. `diskcache`
é cache opcional/lazy para multimodal; `markitdown` é CLI externo opcional
para converter formatos documentais durante ingest (instale e valide o
binário antes de usar esse path). `networkx`, `markdown-it-py` e as deps do
core estão no pacote Python. O lock KG ainda usa `fcntl`; o Percival é
**Linux-only** (decisão do operador 2026-10-06 — `docs/reports/2026-10-05-kg-f0-execution-status.md`
§B4). O backend `msvcrt` permanece no vendor para quem desenvolve em
Windows, sem CI nem gate de release. A SPA em dev requer Bun; wheel/sdist
incluem assets prebuilt quando a integridade do snapshot passa.

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
    anunciar suporte. Para áudio use uma amostra consentida na cópia, confirme
    a transcrição e o registro de origem; o arquivo será enviado à Groq.

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

## Status dos repos legados (2026-10-06)

Os repos [`bill-kopp-ai-dev/percival-collective-memory`](https://github.com/bill-kopp-ai-dev/percival-collective-memory)
e [`bill-kopp-ai-dev/percival-acquire-knowledge`](https://github.com/bill-kopp-ai-dev/percival-acquire-knowledge)
foram **congelados** em 2026-10-06 (D5/D10 — ver `docs/reports/2026-10-05-kg-f0-execution-status.md`):
banner EOL em cada `README.md`, novo `MIGRATION.md` com mapeamento para as
tools nativas e rollback via tag `legacy-final`. `mode="mcp"` continua
suportado para rollback, mas não há mais commits upstream, PRs ou
releases; a flag `Archive this repository` no GitHub ainda depende de
`gh auth login`. Para usuários fora do Percival, a recomendação oficial
é adotar a distribuição `nanobot-ai` e parar de instalar cópias novas
dos MCPs legados.
