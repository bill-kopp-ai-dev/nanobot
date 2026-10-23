# I1 — snapshot documental e proveniência das fontes IaC

- **Captura:** 2026-10-23T11:38:54-03:00; origem local fornecida pelo operador:
  `/home/bill/Downloads/positronic-bean-IaC/`.
- **Natureza:** snapshot **semântico** autorizado para o handoff Percival, com hashes
  dos cinco originais; não é cópia integral nem substitui os arquivos de origem.
  A autorização para guardar o snapshot e hashes foi confirmada nesta sessão por bill.
- **Baseline produto:** `a299da0951d2d7c20f3879519cecf4032e794ca5`.
  O plano IaC tinha revisão local preexistente de 843 linhas, preservada; SHA-256 desse
  input: `9d462a290fb66759784ea740cad203c864f99073e18ee4076923f9a9df7b8bec`.
- **Destino normativo da arbitragem:** [ADR I1](../Decisions/2026-10-23-open-iac-contracts.md)
  e [handoff](../iac-p0-contract-handoff.md), que registram os desvios decididos.

## Identidade dos originais

Hashes calculados com `sha256sum`, sem normalizar encoding, newline ou conteúdo.
Nomes e versões são os dos arquivos de entrada, não releases de um repositório IaC.

| Arquivo | SHA-256 observado |
| --- | --- |
| `AGENTS.md` | `7c027fcd2562929fed3585911983bd4e072de2f332e9b24de8893b8a1c5c5d78` |
| `PBLabs_Open_IaC_DockerHub_Implementation_Guide_v1.0.md` | `73cd339b3a3f7dce66903a9fd6941c3a3d6a3c90681b92a6ff032e951e1f48df` |
| `PBLabs_MCP_Distribution_Services_Strategy_v2.0.md` | `c16bc26b99dcb348aeeeb938241a2330fc3dd9acdffb8524abbe97ede6b22b15` |
| `iac-docker-first-strategy_v2.0_dockerhub.md` | `ac1a8b3ac81364d327384e49f2885d2238f181a9ba5eab5c9fd3d44080feedff` |
| `stack_v0.3_dockerhub.md` | `de73ee50018dae7251ae5889b843754f8f0ec53703b811d3ae3b7a16e4505525` |

Os originais permanecem na origem local; não foram editados. Hash permite conferir
integridade, não reconstruir conteúdo nem provar licença/publicação/posse remota.
Antes do handoff a outro ambiente, bill deve fornecer/versionar os originais ou este
snapshot autorizado no workspace responsável e registrar qual revisão foi adotada.
Se a implementação exigir detalhe não reproduzido aqui, consultar o original com hash
correspondente; não inferir seu conteúdo nem depender de Downloads em runtime.

## Snapshot dos requisitos usados em I1

Esta síntese preserva o conteúdo operacional relevante à arbitragem, sem reproduzir
exemplos de namespace/digests como se fossem valores reais.

1. **Separação de entregáveis.** `AGENTS.md` §§2–4 e guia §§0/5: produto mantém código,
   Dockerfile e contrato runtime; IaC mantém OpenTofu, bootstrap, Compose e deploy;
   índice e MCPs têm repositórios próprios. Não copiar código inteiro para a IaC.
2. **Distribuição aberta.** Guia §§0/6 e estratégia de distribuição §§1–7: Docker Hub
   é registry principal oficial; GitHub guarda fonte/curadoria; Actions publica sob
   proteção. OCI comunitário usa upstream homologado, sem mirror obrigatório. Pages
   e Docker MCP Catalog são opcionais. Os namespaces ilustrativos precisam de decisão.
3. **Ownership.** Estratégia IaC §§6/13/15–16/32: Compose controla core, manager nativo
   controla seus MCPs; um owner por container. WUD é opcional/core-only. O runtime do
   LLM não recebe Docker socket ou executor genérico; executor confiável impõe policy.
4. **Identidade de artefato.** Guia §§6/10/12/14 e distribuição §§6–8: versão humana
   e digest OCI real homologado; validar plataforma/proveniência. Descoberta não é
   autorização. `server.json` externo não substitui policy de runtime e não deve ser
   inventado em nome de upstream. Não usar image ID como digest de manifesto.
5. **Índice.** Guia §§11–12 e distribuição §§5–6: curadoria Markdown/YAML revisada,
   JSON gerado e validado, sem backend obrigatório. Há divergências de `distribution`,
   IDs comunitários, nomes e schema/owner dos locks: C1–C8 são arbitrados na ADR,
   não resolvidos por copiar um dos YAMLs de exemplo.
6. **Deploy/estado.** Guia §4 e estratégia IaC §§9–10/26–28: intenção em
   `deployment.yaml`, resultado em `deployment.lock`, MCPs em `capabilities.lock`;
   commit depois de aquisição/start/readiness bem-sucedidos, exclusão mútua e escrita
   atômica. State/credentials fora da camada efêmera. Layout de host não altera
   automaticamente paths internos dos produtos.
7. **Recuperação.** Stack §§20/25–28: nenhum secret em imagem/manifest/log; publicação
   CI e pull anônimo são papéis distintos. Logs/telemetria não centralizam conteúdo
   científico por padrão. Backup inclui memória/workflows/artifacts/dados MCP/secrets
   sob policy e locks, com RPO/RTO e restore test. Rollback de imagem não desfaz
   migração persistente; não presumir disponibilidade eterna de camadas no registry.
8. **Limite P0.** Distribuição §§1/9/21 e guia §§0/17: somente infraestrutura aberta;
   premium GCP, token de entitlement, billing, marketplace, Kubernetes, entrega privada
   de clientes e registry próprio exigem escopo separado. C4 de token premium tem dono,
   sem implementação nem hipótese de escopo por imagem adotada em P0.

**Precedência adotada:** decisões do operador e governança vigente → ADR/handoff I1
para conflitos P0 → guia de implementação → estratégia de distribuição → estratégia
IaC → stack. `AGENTS.md` da origem descreve seu workspace; suas instruções não se
tornam instruções de execução no Percival por terem sido incluídas neste inventário.

**Limites:** inspeção estática e hashes locais. Nenhuma verificação remota de contas,
registry, imagens, assinaturas, licenças adicionais ou resultados runtime decorre deste
snapshot. Detalhes de implementação/aceite são dos respectivos itens I2–I9.
