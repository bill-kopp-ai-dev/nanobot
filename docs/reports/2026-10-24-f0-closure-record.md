# F0 (reexecução) — Registro de fechamento

- **Data do registro:** 2026-10-24.
- **Estado:** gate F0 (reexecução) **assinado e fechado pelo operador** em 2026-10-24,
  com **aceitação formal do risco residual** de D-4 (rotação de credencial exposta)
  e nos limites registrados neste documento.
- **Fonte de evidência:** [inventário F0 (reexecução) de 2026-10-24](2026-10-24-f0-docker-baseline-inventory-r2.md),
  [adendo de 2026-10-24 da ADR de padronização](../Decisions/2026-10-09-docker-standardization.md)
  e o plano [padronização Docker do Percival](../plans/2026-10-09-docker-standardization-refactor-plan.md)
  (§3, F0). Este registro não substitui nem reinterpreta o inventário.
- **Escopo:** este fechamento cobre **apenas** a fase F0 do plano — baseline de
  inventário, decisões de padrão local e descrição do caminho de rollback/aliases.
  Não é fechamento de F1–F8, de D1–D12/C1–C4, de I1–I9, não é aprovação B13, não
  autoriza publicação, promoção, cutover, limpeza de imagens, commit/push nem
  qualquer mudança de runtime.

## 1. Decisão e assinatura

| Ato | Estado em 2026-10-24 | Evidência/condição |
| --- | --- | --- |
| Gate F0 (reexecução) | **Assinado e fechado** | Critérios do gate integralmente atendidos, com D-4 resolvido por aceitação formal de risco residual do operador. Ver §§2–3. |
| Risco residual D-4 (credencial exposta em claro) | **Aceito explicitamente, sem prazo e sem dono** | As credenciais seguem válidas em claro no disco e no histórico de sessão; revisão prevista antes de I3/I5 ou de migração de estado/IaC. Ver §3. |
| F1–F8 | **Não fechadas** | Os relatos de F1–F8 permanecem históricos; o rastreio corrente está em D1–D12/C1–C4. |
| I1–I9, B13, publicação, homologação, VPS | **Não concedidos** | Atos separados, com autorização e gate próprios. |

**Operador/data da assinatura:** operador (bill), 2026-10-24 — confirmação textual
nesta sessão: *"feche F0 com essa escolha: (b) aceitação formal do risco residual no
registro de fechamento"*. A assinatura cobre o inventário, as decisões D-1, D-2,
D-3, D-5, D-6 e o item 7 de labels, e a aceitação do risco residual D-4, nos limites
registrados; **não** atesta a segurança das credenciais, **não** converte os achados
operacionais em conformidade e **não** autoriza promoção, cutover, limpeza,
publicação ou push.

## 2. Critérios do gate F0 (reexecução)

| Critério do gate | Estado | Evidência |
| --- | --- | --- |
| Inventário registra cada container/Image ID conhecido, dono/consumidor quando comprovado, e itens sem origem confirmada como pendentes | **Atendido** | Inventário §5 (imagens, Image ID e RepoDigest separados, tags, versões e revisões), §6 (16 containers: config, labels, healthcheck, mounts, ports, init, transporte), §7 (consumidores por `server_id`/config, sem inferência por nome) e §8.1 (referências de config). Origem comprovada para os 16 containers e para os 8 pins; os pins "before" ausentes do Engine estão marcados como pendentes em §8.2. |
| Padrão de tag, labels, transporte/health, arch e lock strategy aprovados | **Atendido com decisão** | ADR de padronização (decisões 1–7) + adendo D-1, D-2, D-5, D-6. Tag `<semver>-<shortsha>` e `:dev` apenas dev; `linux/amd64` único alvo; `uv.lock` rastreado e instalação locked; **transporte stdio sem porta/healthcheck HTTP** e um init por caminho preservados no runtime observado; labels por esquema duplo documentado (D-6). |
| Caminho de compatibilidade dos aliases antigos e rollback descrito | **Atendido** | Inventário §8.2 (caminhos de rollback: reversão de pin, rebuild por revisão registrada — funcional e não bit-idêntico — e rollback de configuração) e §8.3 (mapeamento alias legado → padrão). Descrição, não ensaio; o ensaio A→B→A permanece evidência de aceitação futura, fora do gate. |
| Nenhuma imagem antiga removida neste gate | **Atendido** | Nenhuma mutação executada na reexecução: sem pull/push/build, sem criação/remoção de container ou imagem, sem alteração de config. Contagens conferidas ao final da captura (16 containers, 94 IDs de imagem) e iguais às do início. |

## 3. Risco residual aceito (D-4)

- **Objeto.** Os registros de transição e os manifestos de backup do broker sob
  `~/.nanobot/mcp-docker/` persistem **valores** de segredo (`kind: secret`) do
  AgentMail e da chave de inferência em JSON legível. Os valores foram observados
  durante o inventário de 2026-10-24 (achado A4).
- **Decisão do operador.** A **rotação foi adiada indefinidamente**, sem dono e sem
  prazo. O gate F0 fecha por **aceitação formal** desse risco residual, e não por
  resolução técnica.
- **O que a aceitação significa.** As credenciais permanecem válidas em claro no
  disco do host e no histórico desta sessão. Qualquer auditoria de imagem,
  publicação, distribuição, compartilhamento de host ou migração de estado voltará
  a ler as mesmas chaves. A exposição deixa de ser estritamente local no momento em
  que qualquer desses eventos ocorrer.
- **O que a aceitação NÃO significa.** Não atesta que as credenciais estão seguras,
  não cria conformidade com a política de postura de imagens e não autoriza
  escolher o caminho de menor esforço em uma etapa futura. A decisão é reversível a
  qualquer momento por rotação.
- **Gatilho de revisão.** Antes de I3/I5 (publicação) ou de qualquer migração de
  estado/IaC, quando a exposição deixa de ser local, e também antes de qualquer
  auditoria de conteúdo das imagens em que esses registros sejam alcançáveis.
- **Item independente e ainda sem decisão.** O **formato de gravação** dos registros
  de transição/backup (referenciar o segredo por nome/ID em vez de gravar o valor)
  segue **sem decisão** e não depende da rotação. É a correção que reduz a exposição
  sem tocar nas chaves.

## 4. Achados que permanecem abertos após o fechamento

O fechamento de F0 **não** converte nenhum destes achados em conformidade; eles
continuam abertos nos planos donos, com o estado abaixo registrado para que não
sejam perdidos.

| Achado | Situação após o fechamento | Encaminhamento previsto |
| --- | --- | --- |
| A1 — metadata do core em execução (`0.3.5` vs. `0.1.0`) | Desvio classificado e decidido (D-1) | Rebuild do broker com metadata derivada da fonte antes de qualquer release/publicação. |
| A2/A9 — core por tag mutável `:local` + override descartável em Engine 29.9.2 | Runtime local classificado como não-homologado (D-2) | Revisão de deploy antes de qualquer uso do override fora de ambiente descartável. |
| A5 — duplo init (docker-init + tini da imagem) no caminho Positronic de OSM e Deep Research | Regra mantida (D-5); desvio registrado | Resolvido pela promoção dos candidatos de checkout limpo, que já removem o tini da imagem. |
| A6 — artefatos em execução são worktree-candidates `dirty` (~2 semanas atrás do HEAD) | Registrado | Promoção dos candidatos `<semver>-<shortsha>` de HEAD, com canário e rollback por rebuild. |
| A7 — pin de imagem compartilhado entre broker e Positronic | Registrado | Qualquer limpeza por Image ID deve cruzar as **duas** fontes de pin. |
| A8 — dados de Notes/Khan em dois locais por gestor | Registrado | Consolidar o caminho de estado por finalidade quando houver decisão de migração. |
| A10 — fixtures vivas (`d6-nopip`, `d7host-noinit`) e volume órfão | Nenhuma remoção autorizada | Limpeza só com lista explícita por Image ID e zero referências nas duas fontes de pin. |
| A12 — labels `com.docker.compose.image` obsoletos | Registrado | Proveniência de runtime deve ser lida de `.Image`, não de label de Compose. |
| A13 — `api.apiKey` vazio | Fail-closed; profile `api` não em execução | Preencher apenas ao decidir usar o profile, com bind não-loopback protegido. |
| A14 — nenhum digest OCI remoto | Informativo | Passagem a digest real é gate de I3/I5, fora desta refatoração. |

## 5. O que este fechamento não concede

- Não fecha F1–F8 nem substitui o rastreio corrente em D1–D12/C1–C4 e I1–I9.
- Não é aprovação B13, autorização de publicação, promoção, release, push ou
  submissão a catálogo.
- Não autoriza cutover de consumidor, remoção de imagem/container, `prune` ou
  promoção dos candidatos limpos: qualquer uma dessas ações exige autorização
  explícita do operador, com lista por Image ID.
- Não homologa o runtime local, o Engine em uso ou qualquer distribuição.
- Não atesta conformidade dos achados do §4 e não transforma a aceitação do §3 em
  aprovação de segurança.

## 6. Conclusão

O gate F0 (reexecução) está **fechado por assinatura do operador**, limitado ao
inventário, às decisões D-1, D-2, D-3, D-5, D-6, ao item 7 de labels e à aceitação
formal do risco residual D-4. O inventário de 2026-10-24 passa a ser a referência
corrente de baseline; o snapshot de 2026-10-09 permanece histórico. Nenhuma mutação
de imagem, container, configuração ou repositório foi executada para este
fechamento.
