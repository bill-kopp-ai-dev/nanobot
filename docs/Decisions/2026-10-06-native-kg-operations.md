# KG nativo: operação, distribuição e rollback

- **Data:** 2026-10-06
- **Status:** decisão de implementação; autorização de release pendente
- **Escopo:** [plano KG, F9](../plans/kg-integration-plan.md#f9--skills-documentação-migração-e-release)

## Decisão

As 20 operações CM e 14 AK são tools nativas; os doze prompts legados viram
skills **diretamente** em `nanobot/skills/{cm,ak}-*/SKILL.md`, pois o
`SkillsLoader` só percorre um nível de diretórios. A SPA fala com o gateway
autenticado na porta 8765; em desenvolvimento, Vite na 5174 faz proxy de
bootstrap e leituras, enquanto mutações trafegam pelo WebSocket autenticado.
`nanobot kg graph rebuild cm|ak` gera `graphify-out/graph.json` determinístico
sob lock, sem rótulos de LLM/HTML. Snapshot da SPA e vendor core são
verificados por hashes no hook Hatch; atualizar apenas com fonte/revisão
declarada e revisão das alterações locais.

`kg.mode="mcp"` mantém o caminho legível para rollback; `native` (padrão)
suprime apenas os MCPs legados CM/AK, `both` mantém ambos sem permitir escrita
simultânea segura. Backup integral e teste de compatibilidade em **cópias**
antecedem a troca; rollback de binário/config não reverte writes em dados.

## Motivos, limites e alternativas

Skills evitam 12 tools adicionais e a descoberta não recursiva impõe o layout.
Manter adapters HTTP no runtime de produção duplicaria autenticação e política
de workspace. Reusar `graphify cluster-only` ou inferência própria alteraria o
artefato servido e a seleção de provider do turno. O bundle Git sozinho não
preserva `sources/` e todos os assets; a cópia integral é necessária.

O lock do core ainda depende de `fcntl`; o Percival é **Linux-only** (decisão
do operador 2026-10-06 — `docs/reports/2026-10-05-kg-f0-execution-status.md`
§B4). O backend `msvcrt` em `okf_bundle_core/lock.py` permanece no vendor
para quem desenvolve em Windows, sem CI nem gate de release. Áudio AK usa
o serviço de transcrição Groq Whisper (decisão D12 — ver B5 e
`kg-migration.md`); publicar release KG exige validação de áudio com
credencial e arquivo reais, ainda pendente. Não mudar estado de repos
legados (D5/D10) até validação de dados copiados e aprovação do operador.
Consulte [migração](../kg-migration.md) e [release](../kg-release-notes.md).
