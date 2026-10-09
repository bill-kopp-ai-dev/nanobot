# Padronização Docker do Percival — decisões de F0

- **Data:** 2026-10-09
- **Status:** decisões de produto confirmadas pelo operador; implementação
  pendente das fases do [plano de refatoração](../plans/2026-10-09-docker-standardization-refactor-plan.md)
- **Evidência de baseline:** [inventário F0](../reports/2026-10-09-f0-docker-baseline-inventory.md)

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
   compatibilidade e adicionar labels de owner, manager e instance ID. Os
   managers devem aplicar seus próprios labels; o broker não altera containers
   Positronic. Valores distinguem owner (`percival`/`positronic`) e manager
   (`percival-broker`/gestor Positronic). Semântica de persistência do
   `instance-id` e os nomes finais das novas chaves serão fixados em F2 junto ao
   modelo de instância, antes de implementação incompatível.

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
