# F5 — Recuperação, CI e prontidão (evidência local)

**Status:** implementação local concluída; gate global de prontidão permanece
aberto. Esta evidência foi produzida em uma árvore baseada no commit
`3bc43b8a` com alterações F5 ainda não commitadas. Não existe SHA candidato
para aceite do operador.

## Entrega local

- `DockerMcpService` persiste um journal privado por servidor em
  `runtime_data_dir/mcp-docker/transitions/<server_id>.json`, com substituição
  atômica, `fsync` do arquivo/diretório e modo `0600` dentro de diretório
  `0700`. O journal contém intenção anterior, revisão CAS, operação,
  correlation ID e caminho do backup; esses dados ficam sob a proteção local
  do diretório de estado e não são enviados ao broker nem à UI.
- A leitura autenticada da página, mutações e CLI de restore tentam resolver
  transições `preparing`: se a revisão/config ainda é anterior, o broker recebe
  `recover` com o snapshot persistido; se a revisão foi commitada, o broker é
  reconciliado à configuração persistida; exclusão commitada termina de
  remover container órfão (inclusive se o container já não existe). Falhas,
  revisão inesperada ou journal ilegível continuam pendentes e bloqueiam
  mutações.
- O broker ganhou ação tipada `recover`: reconstrói o container ativo do estado
  aprovado, mantém `stopped-persistent` parado e trata `exclude` de container
  ausente/órfão como idempotente. O gate de tool MCP por chamada também nega
  acesso quando o journal está `preparing`, corrompido ou não verificável; a
  recuperação é tentada na próxima leitura/mutação autenticada, não por um
  daemon de recuperação independente.
- A WebUI lista backups sem expor o conteúdo do manifesto, exige operator-admin
  e digitação do `server_id` para restaurar, usa CAS atual, valida checksum e
  recusa substituir um servidor já registrado. Ações de gestão ficam
  indisponíveis enquanto houver transição pendente.
- CI `ci.yml` agora tem execução noturna (03:23 UTC) além do despacho manual,
  push e PR; nessa agenda o detector cobre os jobs Python, WebUI, TUI, Docker,
  Arch e smoke do broker. A matriz Linux-only existente preserva Ubuntu 22.04,
  Arch pinado e targets TUI `linux-arm64`/`linux-x64`. `tui-release.yml` já era
  Linux-only.
- `docker-compose.mcp-broker.yml` continua como overlay explícito do sidecar
  (sem systemd); foi documentado o processo reversível para migrar o estado
  para `.percival`, conferir ownership/modes, recriar gateway+broker e fazer
  rollback sem `down -v` ou apagar a cópia antiga. Nenhuma migração foi feita
  em dados do operador.


- `uv run --no-sync pytest`: **9.273 passed, 49 skipped, 5 warnings** em
  7m45s. Os warnings são serializers Pydantic já presentes e depreciação
  `aiohttp.BasicAuth`; nenhum teste falhou.
- `uv run --no-sync basedpyright nanobot`: **0 errors, 0 warnings, 0 notes**.
- `uv run --no-sync ruff check .`: passou.
- Foco MCP/config final: **43 passed**; inclui recuperação antes/depois do
  commit, fail-closed, restore/exclude e gate de tool sob journal `preparing`.
- WebUI F5 + i18n: **36 passed** (9 management page + 27 i18n); `bun run
  lint` e `bun run build` passaram.
- `tui`: `bun run check` passou e `bun run test` teve **254 passed**.
- Empacotamento TUI Linux local: `python3 scripts/pty_smoke.py`, `bun run
  build`, `bun scripts/release-notices.ts linux-x64` e
  `python3 scripts/package-release.py linux-x64` passaram; `tui-release.yml`
  mantém também o target `linux-arm64` para o runner de release.
- Compose combinado foi renderizado com placeholders de ambiente e uma
  verificação automatizada confirmou que somente o broker monta
  `docker.sock`, usa `network_mode: service:nanobot-gateway` e não publica
  portas. Sintaxe YAML de `.github/workflows/ci.yml` parseada localmente.
- Smoke real de gateway+broker e fixtures Weather/OSM passou no Engine local
  **29.7.2** com Docker CLI do broker **27.5.1**. Exercitou as oito famílias,
  restore de backup e journal interrompido seguido de recuperação forçada,
  mantendo separação de socket. Sources fixas: Weather `b5032f4` / rollback
  `996302b`; OSM `ca3c397` / rollback `5f80a41`. IDs de imagem criados nesta
  execução: Weather `ceffd704…` / rollback `b309f8b0…`; OSM `3c231f75…` /
  rollback `c956ade0…`. Imagens F5 finais: gateway `2ae2e4e6…` e broker
  `83d9137b…`.
- **Follow-up de investigação WebUI (2026-10-08):** as quatro falhas originais
  eram waits de teste curtos para UI que se monta de forma assíncrona em chat
  frio, mais um mock de `setInterval` que devolvia o mesmo handle para todos
  os intervalos. Em `app-layout` e `temporary-chat-navigation`, o fallback
  `StartupShell` continuava visível enquanto o chunk lazy `ThreadShell` era
  carregado; a espera padrão de 1 s expirava em execução fria/carga concorrente.
  Em `remote-instances`, o handle compartilhado `1` violava o contrato de
  `setInterval`/`clearInterval` e o iframe remoto era esperado dentro do mesmo
  limite curto. Os testes agora dão até 5 s para a interface lazy/iframe e o
  teste remoto recebe timeout máximo de 15 s; o mock usa handles nativos
  independentes e clearable, delegando intervalos não observados ao browser
  fake. Não foi necessária alteração do runtime da aplicação.
- Reexecução completa após as correções: `bun run test` **2631 passed, 0
  failed** em 155 arquivos. `bun run lint` e `bun run build` continuam verdes.
  Restaram avisos do Happy DOM sobre carregamento de iframe deliberadamente
  desativado e avisos React `act(...)` em outros testes; não causaram falha.


1. **GitHub Actions no SHA candidato:** workflow YAML foi parseado, mas nenhum
   run remoto aconteceu; a agenda noturna só atuará depois que a alteração
   chegar ao repositório.
2. **F3/F4 end-to-end:** ainda falta Browser WebUI + gateway + broker real com
   estado vazio/erros, auth 401/403, conflito 409/re-fetch, restore, efetividade
   visual, duas fixtures e prova de não afetar outro servidor.
3. **VPS/deployment canônico:** falta executar e anexar o inventário real,
   comprovar Engine Client/Server 27.x e mounts/GIDs/UIDs, ensaiar cópia
   `~/.nanobot` → `.percival`, `docker compose up --force-recreate`, persistência
   e rollback na topologia alvo.
4. **Aceite:** o operador ainda precisa aceitar expressamente o risco residual
   no deployment real e no SHA candidato. O smoke Engine 29.7.2/CLI 27.5.1 não
   substitui essa evidência nem prova isolamento total.

Portanto, F5 tem implementação e evidência local substanciais, mas o plano e a
prontidão de deployment **não podem ser declarados fechados** até os quatro
gates acima, especialmente a suíte WebUI completa e a validação no VPS.
