# Padronização Docker do Percival — decisões de F0

- **Data:** 2026-10-09
- **Status:** decisões de produto confirmadas pelo operador; implementação
  pendente das fases do [plano de refatoração arquivado](../plans/closed/2026-10-09-docker-standardization-refactor-plan.md)
- **Evidência de baseline:** [inventário F0](../reports/2026-10-09-f0-docker-baseline-inventory.md)
- **Aditamento 2026-10-23:** a [ADR I1](2026-10-23-open-iac-contracts.md) decide
  registry/naming e evolução P0 de aquisição/índice. O item 2 abaixo conserva o escopo
  histórico desta refatoração; a nova decisão não autoriza publicação/deploy nem
  altera o spawn `--pull=never` ou os registros existentes.

## Decisões confirmadas

1. **Naming e tags locais:** usar repositórios locais `percival-<service>`;
   gateway `percival-gateway` e broker `percival-mcp-broker`. Preservar
   `server_id`, nomes/API MCP e contratos de tools. Tag imutável de candidato
   segue `<semver>-<shortsha>`; `:dev` é alias mutável apenas para
   desenvolvimento, nunca identidade de deployment. Broker continua fixando
   ID completo/RepoDigest e `--pull=never`.
2. **Registry:** esta refatoração permanece local-only. Não escolher registry e
   não fazer pull/push, publicação, release ou Catalog submission; requerem
   autorização/decisão próprias.
3. **Plataforma:** `linux/amd64` é a única plataforma-alvo nesta refatoração.
   ARM64 não faz parte do escopo aprovado atual.
4. **Lock do gateway:** rastrear `uv.lock` no Percival, corrigir a regra de
   ignore de maneira explícita e tornar a instalação da imagem locked. As
   dependências de canal também precisam de estratégia reprodutível. O lock
   será alterado/revisado em F3, não nesta decisão F0.
5. **Khan Calendar:** incluir `khal` pinado na imagem Docker de runtime para
   disponibilizar as 12 tools no ambiente Docker-first. Aceitar o aumento
   estimado de aproximadamente 150 MB, sujeito à verificação de tamanho,
   dependências de SO/licenças e workspace persistente em F4. Não depender de
   binário `khal` no host como caminho padrão.
6. **API e exposição local:** API permanece sempre configurada/ativa, mas deve
   exigir `api_key` e falhar com erro claro se ela estiver ausente. A porta
   gateway/WebUI 8765 e a porta da API mantêm bind host em loopback por padrão.
   Exposição externa requer opt-in e configuração explícita de autenticação,
   proxy/TLS e firewall. Não remover autenticação para evitar restart loops.
7. **Labels de container:** manter `percival.mcp-docker.server-id` por
   compatibilidade e adicionar `percival.mcp-docker.owner`,
   `percival.mcp-docker.managed-by` e `percival.mcp-docker.instance-id`. Os
   managers aplicam seus próprios labels; o broker não altera containers
   Positronic. Valores distinguem owner (`percival`/`positronic`) e manager
   (`percival-broker`/gestor Positronic). F2 fixa a identidade de uma
   encarnação Docker: cada novo container recebe UUID v4; recreate/restart
   gera outro ID, enquanto o `server-id` permanece estável.

## Consequências e limites

- F1–F5 implementam e verificam os contratos aprovados; esta ADR não autoriza
  cutover em runtime real, remoção de imagens, atualização de VPS ou mudança em
  outros repositórios além dos patches necessários e aprovados fase a fase.
- Mudanças devem preservar as alterações locais preexistentes nos seis MCPs.
- O snapshot de 2026-10-09 comprovou as referências configuradas do Percival e
  Positronic. Permanecem sem causa atribuída as duas instâncias Docker de cada
  AgentMail/Deep Research no Positronic; isso deve ser entendido antes de
  qualquer cleanup/cutover que as afete.

- F8 da skill/instruções operacionais continua recomendação do plano e será
  executada após o aceite de operação, com revisão da skill existente.

## Adendo 2026-10-24 — reexecução de F0 (baseline e inventário correntes)

- **Data:** 2026-10-24.
- **Responsável:** bill (operador) confirmou as decisões abaixo; preparação
  técnica: agente. Sem revisão humana independente.
- **Evidência:** [inventário F0 (reexecução) de 2026-10-24](../reports/2026-10-24-f0-docker-baseline-inventory-r2.md).
  Captura read-only; nenhuma mutação de imagem, container, config ou repositório.
- **Efeito:** as decisões 1–7 acima **permanecem vigentes**. Este adendo não reabre
  F1–F8 nem altera o rastreamento corrente em D1–D12/C1–C4 e I1–I9; fixa o
  baseline de inventário e as decisões que a reexecução exigia.

### Decisões confirmadas nesta reexecução

- **D-1 — Fonte de versão e desvio do core em execução.** A fonte única da versão
  do produto permanece `[project].version` do `pyproject.toml` (`0.1.0`), conforme
  ADR I1 §3. A imagem do broker **em execução** (`percival-mcp-broker:local`,
  image ID `6ea63b38852c`) carrega `org.opencontainers.image.version = 0.3.5` e
  `revision = 29a482c`, enquanto o gateway em execução e o HEAD do repositório
  declaram `0.1.0`. Isso é **desvio de metadata a corrigir antes de qualquer
  release, publicação ou claim de homologação** — não nova série de versão.
  Rebuild com metadata derivado da fonte é o caminho; a tag legível mutável
  `percival-mcp-broker:local` permanece sem valor de identidade.
- **D-2 — Valor probatório do runtime local.** O stack local do core é iniciado com
  `image: percival-mcp-broker:local` via
  `docker-compose.engine29-override.yml`, override que se declara descartável e
  relaxa a verificação de Engine (`PERCIVAL_DISPOSABLE_ENGINE29=1`) num host em
  Engine **29.9.2**. Portanto o runtime local **não** está no contrato aprovado
  (Engine 27.x, pin imutável) e **nenhuma evidência local de runtime vale como
  homologação** de Engine, distribuição ou release. O override permanece marcado
  como não-homologado e não deve preceder revisão de deploy.
- **D-3 — Caminho oficial de rollback.** O rollback por `transitions` do broker só
  é válido se a imagem anterior existir localmente; os seis image IDs `before`
  gravados em 2026-10-10 **não existem** no Engine. O caminho oficial passa a ser
  **rebuild a partir da revisão registrada** (commits `ab0f07d`, `d2d6458`,
  `94c7fde`, `d8d4122`, `311a49d`, `9e8272b` e `29a482c`, todos presentes nos
  repositórios locais), aceito como **funcional e não bit-idêntico**. As tags
  `rollback-d11-*` preservam apenas o passo D11 do core, não o cutover dos MCPs.
  Rollback de configuração usa as transições/backups de cada gestor e não toca no
  runtime.
- **D-4 — Segredos de servidor MCP gravados em claro (adiada).** Os registros de
  transição e os manifestos de backup do broker sob `~/.nanobot/mcp-docker/`
  persistem **valores** de segredo (`kind: secret`) de AgentMail e da chave de
  inferência em JSON legível; os valores foram observados durante o inventário de
  2026-10-24. A **rotação foi adiada indefinidamente pelo operador** nesta sessão,
  sem dono nem prazo. Risco residual registrado de forma explícita e deliberada:
  as credenciais permanecem válidas em claro no disco e no histórico de sessão, e
  qualquer auditoria de imagem, publicação, distribuição ou compartilhamento de
  host passa a expor as mesmas chaves. Revisão prevista: antes de I3/I5 (publicação)
  ou de qualquer migração de estado/IaC, quando a exposição deixa de ser local.
  A correção do **formato de gravação** (referenciar segredo por nome/ID em vez de
  gravar o valor) segue sem decisão e não depende da rotação.
- **D-5 — Um único init por caminho de execução.** F1 continua vigente: nunca
  `init: true` do Docker **e** tini embutido na imagem no mesmo caminho. Os
  containers do gestor Positronic de OSM e Deep Research violam a regra hoje
  (docker-init + tini na imagem F3 em execução). A promoção dos candidatos de
  checkout limpo — que já removem o tini da imagem — é o caminho de resolução;
  até lá, o desvio fica registrado e deve ser citado em qualquer claim de
  conformidade de runtime.
- **D-6 — Labels: esquema duplo documentado.** A decisão 7 **não** é estendida ao
  gestor Positronic neste ciclo. O broker mantém
  `percival.mcp-docker.{owner,managed-by,instance-id,server-id}`; o gestor
  Positronic mantém seu esquema próprio `io.positronic.*`
  (`managed`, `run`, `server`, `server-name`, `context`, `home`). Consequência
  aceita: o inventário de consumer exige leitura por gestor, e `io.positronic.run`
  é o equivalente funcional de `instance-id` do lado Positronic. Unificar os
  esquemas fica como recomendação futura, fora do gate F0.

### Efeito no gate F0

O gate F0 (reexecução) está **fechado por assinatura do operador** em 2026-10-24,
com o registro em
[relatório de fechamento F0](../reports/2026-10-24-f0-closure-record.md). D-4 foi
encerrada por **aceitação formal do risco residual** (§3 do registro): a rotação
permanece adiada, sem dono e sem prazo, e o risco — credenciais válidas em claro no
disco e no histórico de sessão, expostas de novo em qualquer auditoria de imagem,
publicação, distribuição ou migração de estado — fica registrado de forma explícita
e revisável. O gate fecha porque o item deixou de estar pendente sem decisão, e
**não** porque o risco deixou de existir.

Os demais critérios — inventário completo, padrão de tag/labels/transporte/arch/lock,
caminho de rollback descrito, nenhuma imagem removida — estão satisfeitos e
evidenciados no inventário de 2026-10-24. O fechamento não converte os achados
A1/A2/A5/A6/A7/A9/A10/A12/A13/A14 em conformidade: permanecem abertos nos planos
donos, listados na §4 do registro de fechamento.

Nenhuma destas decisões autoriza commit, push, publicação, release, cutover,
remoção de imagem ou alteração de runtime.
