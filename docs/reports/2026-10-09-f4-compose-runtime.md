# F4 — Compose e contratos de runtime

- **Data:** 2026-10-09
- **Estado:** implementação local validada por render/estrutura; gate F4 aberto.
- **Plano:** [`padronização Docker`](../plans/2026-10-09-docker-standardization-refactor-plan.md), fase F4.
- **Engine/Compose local:** Docker Compose v5.5.1; `linux/amd64`.
- **Governança:** nenhum commit/push, build/promoção de imagem, cutover,
  operação sobre containers reais ou limpeza foi executado.

## Baseline e preservação

SHAs de entrada das árvores editadas: Percival `508c019b`; Notes `f778326`;
AgentMail `f43aa2e`; Weather `c56ffab`; Khan Calendar `530db73`; OSM `ee73a72`;
Deep Research `1a63f68`. Antes das mudanças, os arquivos rastreados estavam
limpos; foram preservados os arquivos locais ignorados/não rastreados já
existentes (`.positronic/`, `AGENTS.md`, `.env` quando presentes). Nenhum valor
de `.env` foi exibido ou incluído neste relatório.

## Alterações

- **Percival:** removidos `container_name` fixos do gateway e API; listeners
  publicados em loopback por padrão (incluindo 8765); healthchecks locais de
  gateway e API; API usa `api_key` obrigatório do `config.json` e `restart: no`
  para evitar loop se faltar credencial; CLI sem TTY; broker com alias `dev`
  substituível e init Compose único.
- **Notes:** nova receita stdio sem porta/TTY/restart; rootfs read-only, `/tmp`
  tmpfs e único mount de dados `/vault`. O diretório da imagem passa a ser
  propriedade de 65532:65532 para permitir volume copy-up. Bind mount exige
  origem preexistente (`create_host_path: false`); README declara preparação e
  ownership.
- **AgentMail:** `.env` passou a opcional, defaults em Compose continuam
  fail-closed pelo servidor quando credenciais funcionais forem necessárias;
  execução stdio sem TTY e sem restart persistente; exemplos usam `-T`.
- **Khan Calendar:** execução stdio explicitamente sem restart persistente e
  `-T`; caminho do calendário configurável via
  `KHAN_CALENDAR_DATA_HOST_PATH`, bind source preexistente e ownership UID/GID
  1000:1000 documentados.
  `khal` está em `pyproject.toml`/`uv.lock` e foi confirmado no venv local
  (`uv run khal --version` → 0.14.0); documentação Docker agora descreve todas
  as 12 tools como suportadas na imagem.
- **Weather:** criada receita Compose stdio/HTTP em profiles separados; HTTP
  Streamable exige token no runtime, healthcheck próprio e host bind loopback;
  stdio é one-shot, sem TTY/portas/health/restart. Hardened rootfs e tmpfs.
- **OSM:** mantida separação stdio/HTTP e o named cache; token HTTP vazio deixa
  o Compose renderizável, mas o entrypoint/runtime rejeita bind remoto sem
  bearer token; comentários documentam `run --rm -T` e exposição via proxy.
- **Deep Research:** stdio explicitamente sem restart; HTTP fixa
  `MCP_TRANSPORT=streamable-http`, publica somente em loopback, usa healthcheck
  HTTP próprio; nome da network inclui o projeto Compose para evitar colisões.
  Volumes logs/reports exigem paths preexistentes por bind long-form e UID/GID
  1000. README exige proxy/TLS/auth/firewall para tráfego externo.

## Verificação executada

`docker compose config --quiet` passou para as receitas Percival (incluindo o
overlay broker), Notes, AgentMail, Khan e os profiles stdio/HTTP/production de
Deep Research. OSM passou para stdio e HTTP usando apenas valores de identidade
descartáveis para `USER_AGENT`/`FROM_HEADER`; Weather passou para stdio e HTTP
sem necessidade de materializar token no comando de configuração. Compose
renderizado não foi impresso, evitando revelar valores carregados de arquivos
locais.

As verificações estruturais finais por JSON renderizado passaram nos sete
repositórios: listeners Percival loopback e healthchecks; stdio sem TTY,
host ports, HTTP healthchecks ou restart persistente; serviços HTTP com profile,
port binding loopback e healthcheck; mounts de Notes/Khan/Deep Research
configurados com `create_host_path: false`.

`git diff --check` passou nos sete repositórios.

## Limitações e gate

- Nenhuma imagem F4 foi construída. Nenhum container descartável foi iniciado;
  por isso MCP `initialize`/`tools/list`, saída stdout/stderr, parada por
  SIGTERM, probes HTTP, identidade do PID 1 e persistência/restore ainda não
  têm evidência desta execução.
- F3 continua aberta conforme os registros do plano: findings Critical/High e
  builder/checkout limpo pendentes. As alterações F4 foram limitadas à fonte e
  aos contratos Compose; não houve execução contra consumers/instâncias reais.
- `api_key` é lido pelo API do arquivo de configuração montado. A Compose não
  valida esse campo antecipadamente; o runtime recusa host não-loopback sem
  chave e `restart: no` evita ciclo contínuo. Healthcheck verifica somente
  `/health`, sem autenticação.
- O serviço Notes requer host vault existente e gravável por UID/GID 65532.
  Khan requer calendar data gravável por UID/GID 1000. Esses mounts não foram
  criados nem testados para persistência/restore.
- Os profiles HTTP de Weather/OSM/Deep não foram iniciados. Exposição externa
  continua dependendo de proxy/TLS/auth/firewall conforme o servidor.

**Próximo passo:** retomar a triagem/fix dos findings F3 e obter a evidência de
build/scan em checkout limpo. Depois, construir candidatos de F4 e executar os
smokes de handshake/HTTP/SIGTERM e persistência em fixtures isoladas, sem
alterar os consumidores até F6.
