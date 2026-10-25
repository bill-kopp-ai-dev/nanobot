# Plano adicional B5/B6 — CI remoto e distribuição por digest

- **Preparado em:** 2026-10-24.
- **Estado:** planejado e adiado por decisão do operador; nenhuma fase foi iniciada.
- **Objetivo:** assumir as pendências B5 (CI remoto) e B6 (distribuição/aquisição por digest) transferidas do escopo local concluído da D8, sem reabrir seus trabalhos já aceitos.
- **Estimativa inicial:** B5, aproximadamente 4–8 dias de engenharia; B6, 1–3 semanas para publicação e homologação no escopo acordado. A integração completa de aquisição pelo manager pode exigir várias semanas adicionais se depender da implementação I6. Esperas por acesso, decisões e aprovações não estão incluídas.
- **Referências:** [plano mestre D1–D12](2026-10-23-fechamento-padronizacao-docker-f4-f5-f7-plan.md) §2.9; [plano D8 arquivado](closed/2026-10-24-d8-promotion-readiness-closure-plan.md) §§7.3–7.6; [relatório F3](../reports/2026-10-10-f3-remediation-triage.md); [plano IaC I1–I9](2026-10-23-iac-alignment-execution-plan.md) §§5.3–5.6 e §10; [ADR I1](../Decisions/2026-10-23-open-iac-contracts.md); [runbook operacional](../operations/mcp-docker-local-runbook.md) §5.1.
- **Autoridade:** este plano não autoriza publicação, promoção, canário, cutover, alteração de gestores, pins/allowlists/credenciais, deploy em VPS ou preparação/entrega de comandos de promoção. Publicação exige aprovação B13 e autorização explícita do operador para a execução correspondente. Em qualquer gate que exija acesso ou ação manual do operador, **parar e informar** antes de prosseguir.

## 1. Contexto e escopo

A D8 foi encerrada no escopo local em 2026-10-24: os oito candidatos locais, scans,
SBOMs, runtime, retenção e evidência documental foram reconciliados. O encerramento
não declarou B5 ou B6 atendidos:

- **B5:** os seis runs MCP registrados estão vermelhos; cinco repetem o step que já
  falhava no run anterior, o OSM tem um delta no smoke legado diagnosticado como
  flake, e o core não tem run porque Actions está desabilitado no fork.
- **B6:** não há digests OCI publicados para os image IDs locais nem caminho de
  aquisição por digest homologado. B13 e a autorização de publicação continuam
  pendentes.

Este plano é o único dono dessas duas pendências. A evidência e as conclusões
históricas permanecem no plano D8 arquivado e no relatório F3; resultados antigos
não serão reinterpretados como gates verdes.

**Decisão de escopo obrigatória antes da Fase B:** confirmar se a distribuição cobre
os oito artefatos D8 (seis MCPs, gateway e broker) ou um subconjunto selecionado
formalmente por I3/I5. A aquisição a homologar também precisa ser definida:
pull independente por digest ou aquisição pelo fluxo real do manager/catálogo. A
segunda opção requer I5/I6 aplicáveis e não pode ser substituída por um pull manual.

## 2. Fronteiras

Incluído: diagnosticar e corrigir falhas de workflows, habilitar evidência remota
válida para os SHAs finais, refazer candidatos e evidências quando uma alteração
mudar sua identidade, desenhar o fluxo seguro de publicação, registrar digests OCI
e provar aquisição no escopo aprovado.

Fora do escopo sem autorização separada: publicar imagens ou tags; promover imagens
em qualquer gestor; alterar pins, revisões, CAS, `configurationId`, allowlists ou
credenciais; executar canário/cutover; instalar imagens nos gestores; alterar estado
em VPS; assinar waivers; limpar imagens, containers ou volumes; preparar ou entregar
comandos de promoção.

Não considerar `image ID` local, tag local, commit ou digest de imagem diferente
como evidência intercambiável. A prova de B6 deve identificar os bytes exatos
publicados e adquiridos.

## 3. Plano de execução

### Fase A — Pré-condições e congelamento de escopo

1. Registrar a decisão do operador sobre o conjunto de imagens abrangido por B6 e
   o significado de “aquisição homologada”. Comparar essa decisão com I3, I5 e I6;
   abrir dependência explícita se algum contrato ainda não existir.
2. Confirmar acesso de leitura às Actions dos seis repositórios MCP e do core.
   Verificar a política atual do fork e identificar o owner que pode habilitar ou
   aprovar workflows, sem alterar configurações durante a auditoria.
3. Identificar o owner que pode preparar o secret de registry e o ambiente
   protegido de release. Não solicitar, copiar ou imprimir valores de credenciais.
4. Preparar a matriz inicial `artefato → repo → SHA → workflow → estado → gate`.
   As revisões e image IDs da D8 são baseline; não são automaticamente os candidatos
   finais após correções.
5. **Parar e informar** se a seleção de artefatos, o método de aquisição, a sessão
   GitHub, o owner de Actions ou o ambiente de release não estiver disponível.

**Saída:** escopo B6 decidido, owners externos nomeados e matriz de candidatos
inicializada; nenhum workflow ou registry alterado.

### Fase B — Fechar B5: Actions remotas verdes

1. Reexaminar os runs e os logs de cada SHA final. Distinguir falha de código,
   configuração do workflow, ambiente/cache e bloqueio de plataforma; não inferir
   causa apenas porque um step também falhou no run anterior.
2. Resolver os failures conhecidos por repositório:
   - Notes e Deep Research: diagnosticar `Inspect identity and privilege posture`.
   - AgentMail: diagnosticar os steps `Lint` nas matrizes Python 3.11 e 3.12.
   - Weather: diagnosticar `Resolve image metadata`.
   - Khan Calendar: diagnosticar `Lint (ruff)` e o job cancelado.
   - OSM: corrigir o smoke FIFO para aguardar a resposta do protocolo antes de
     fechar stdin; investigar separadamente a falha de `uv sync` no job Python.
   - Core: confirmar com o owner por que Actions não executa no fork e obter uma
     execução autorizada para o SHA final. Se o owner não puder habilitar/executar
     workflows, manter B5 bloqueado, nunca PASS.
3. Corrigir apenas a causa demonstrada. Para mudanças no OSM ou em outro
   repositório independente, confirmar que estão dentro da autorização aplicável;
   não ampliar a mudança para refatoração não necessária.
4. Executar os workflows requeridos nos SHAs finais. Registrar URL/run ID,
   `headSha`, jobs/steps e conclusão. Aceitar apenas runs cujo SHA corresponda
   exatamente ao candidato.
5. Se um workflow precisar de novo commit, congelar o novo SHA e repetir as
   verificações locais e de artefato afetadas. Uma mudança em Dockerfile,
   dependências, código de runtime ou contexto de build exige rebuild e atualização
   de image ID, scan, SBOM, OpenVEX e snapshot de retenção; não atribuir evidência
   anterior ao novo candidato.
6. Verificar todos os checks obrigatórios, inclusive os jobs de imagem e os
   artefatos de CI. Um run parcial, cancelado, sem execução ou de outro SHA não
   satisfaz B5.

**Aceite B5:** todos os workflows obrigatórios dos SHAs finais dos repositórios
abrangidos terminam verdes; URLs, `headSha`, jobs e evidências estão registrados.
Bloqueio administrativo ou de plataforma mantém o gate aberto.

### Fase C — Projeto e preparação técnica de B6

1. Aplicar os contratos I3/I5 ao subconjunto de imagens decidido na Fase A. Separar
   publicação do fluxo de conformance; builds de PR não confiável não recebem
   credencial de push nem acesso ao ambiente de release.
2. Definir permissões mínimas, gatilhos confiáveis, proteção do ambiente e
   armazenamento de credenciais. Revisar divulgação involuntária de URLs privadas,
   labels OCI, attestations e metadados antes de qualquer publicação.
3. Para cada artefato aprovado tecnicamente, fixar SHA, versão, base digest,
   plataforma, lock, image ID, scan e SBOM. A publicação posterior deve corresponder
   ao mesmo artefato; se houver rebuild, repetir as verificações nos novos bytes.
4. Preparar a prova independente de aquisição: daemon/cache isolado, configuração
   Docker limpa e pull por digest. Se o escopo escolhido exige aquisição via
   catálogo/manager, definir a prova sobre a interface suportada e confirmar as
   dependências I5/I6 antes de declarar que a prova está pronta.
5. **Stop and inform:** antes de qualquer push ao registry, apresentar o inventário
   dos artefatos, origem, versões, scans/SBOMs, metadados públicos e plano de
   verificação ao operador. Aguardar B13 e autorização explícita de publicação.
   Este plano não contém comandos de publicação ou promoção.

**Saída:** pipeline e prova de aquisição revisados, artefatos candidatos fixados e
pacote de evidência preparado para decisão B13; nenhuma imagem publicada.

### Fase D — Publicação autorizada e homologação de aquisição

Esta fase só pode começar após B5 verde, decisão de escopo, B13 registrado e
autorização explícita do operador para publicar o conjunto identificado. Sem essas
condições, **parar e informar** e manter B6 aberto.

1. Publicar somente as versões e imagens autorizadas, sem sobrescrever tags já
   publicadas. Se parte do conjunto falhar, não declarar o conjunto completo nem
   avançar à promoção.
2. Registrar separadamente tag, digest OCI do índice (quando aplicável), digest do
   manifest de plataforma, plataforma, image ID após pull e SHA de origem.
3. Em ambiente limpo e sem cache herdado, adquirir cada artefato por digest.
   Verificar digest, plataforma, labels, proveniência, SBOM e scan no artefato
   adquirido; executar startup e smoke/conformance aplicáveis.
4. Se a decisão da Fase A exigir aquisição por catálogo/manager, provar descoberta,
   validação de origem/digest, consentimento exigido, aquisição e handshake na
   interface suportada. Não alterar configuração ou pin de gestor vivo neste plano;
   usar fixture autorizada e descartável. Se I6 ainda não suportar o fluxo, registrar
   bloqueio e não substituir a prova por pull manual.
5. Atualizar o catálogo/índice curado conforme I5, quando aplicável, mantendo os
   metadados vinculados à revisão imutável e aos digests publicados.
6. Registrar evidência redigida e reconciliar o plano mestre, o relatório F3 e o
   runbook sem expor secrets.

**Aceite B6:** todos os artefatos incluídos no escopo têm digest OCI registrado e
verificado, aquisição homologada pelo método decidido na Fase A, evidência vinculada
aos bytes exatos e aprovação B13 documentada. B6 não autoriza promoção, canário ou
cutover.

## 4. Critérios de encerramento

| Gate | Aceite verificável |
| --- | --- |
| Escopo | Lista aprovada de artefatos B6 e método de aquisição; dependências I3/I5/I6 explícitas |
| B5 — CI | Workflows obrigatórios verdes para cada SHA final; URLs/run IDs, `headSha`, jobs e conclusão registrados |
| Candidatos | Imagens reconstruídas e evidências renovadas sempre que o conteúdo/identidade mudou |
| B13 | Aprovação de publicação registrada antes de qualquer push ao registry |
| B6 — digest | Tags e digests OCI de índice/plataforma registrados separadamente e associados à revisão de origem |
| B6 — aquisição | Pull limpo por digest e smoke; aquisição via manager/catalog quando essa for a decisão de escopo |
| Segurança | Nenhum secret exposto; workflow de publicação protegido e com privilégio mínimo |
| Não mutação | Nenhum pin, gestor vivo, canário, cutover ou deploy alterado por este plano |
| Documentação | Plano mestre, F3, runbook e inventário de release refletem evidência e resíduos atuais |

## 5. Paradas e tratamento de falhas

- **Acesso GitHub ausente ou workflows do core indisponíveis:** parar e registrar o
  owner e a ação manual necessária. Não tratar ausência de run como sucesso.
- **Falha persistente em SHA final:** corrigir a causa e gerar novo candidato quando
  necessário; evidência de run anterior não satisfaz o SHA novo.
- **Novo finding, regressão funcional ou divergência de tools:** parar antes de
  publicar; atualizar análise por image ID e buscar decisão do operador.
- **B13 ou autorização ausente:** nenhuma publicação. Aprovação textual em plano não
  é credencial nem autorização de execução de um push futuro.
- **Digest, plataforma, label ou proveniência divergente após pull:** B6 falha;
  não adquirir por tag móvel nem promover.
- **Aquisição manager/catalog não implementada:** registrar dependência I5/I6 e
  manter B6 aberto; pull manual não é substituto.
- **Falha parcial na publicação:** preservar logs redigidos, não completar por
  sobrescrita ou retag e aguardar decisão do operador.
- **Qualquer pedido de promoção, canário, cutover, alteração de gestor ou deploy:**
  parar; exige autorização e plano próprios, fora deste escopo.

## 6. Estado e estimativa

**Estado em 2026-10-24:** planejado, não iniciado. Nenhum workflow foi alterado,
nenhuma imagem foi publicada e nenhum gestor foi modificado nesta etapa.

| Trabalho | Esforço de engenharia | Dependência que pode alongar o calendário |
| --- | --- | --- |
| B5 | Aproximadamente 4–8 dias | Acesso a Actions; decisão do owner sobre workflows no fork; revisão/push de correções nos repositórios |
| B6 — publicação e pull por digest | Aproximadamente 1–3 semanas | Escopo de release, configuração protegida do registry, B13 e autorização explícita |
| B6 — aquisição completa pelo manager/catalog | A estimar após Fase A; várias semanas se I6 exigir implementação | Contratos I5/I6 e fixture/integração homologável |
