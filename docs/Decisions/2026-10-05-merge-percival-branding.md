# Integração de `feat/percival-branding` em `main`

- **Data:** 2026-10-05
- **Status:** decisões de produto confirmadas; integração em andamento
- **Branches:** `main` (`7b3f19df`) e `origin/feat/percival-branding` (`c92f7321`)

## Decisões confirmadas pelo operador

1. **Base da WebUI:** preservar a UI atual de `main` e adaptar nela os elementos
   próprios do Percival. Não substituir a Sidebar atual pela implementação
   antiga isolada da feature.
2. **Identidade da WebUI:** aplicar Percival à marca/título da aplicação, ao
   splash, às descrições da interface principal e aos assets. Manter referências
   a nanobot quando nomeiam especificamente o runtime/servidor remoto, comandos,
   caminhos, chaves de configuração ou um destino upstream (por exemplo,
   `nanobot gateway` e as telas de conexão a um nanobot remoto).
3. **Links da Sidebar:** incluir os dois destinos externos da feature —
   `p-brain` (Knowledge Graph) e Positronic Bean — também no modo compacto,
   preservando os controles e interações recentes de `main`.
4. **Schemas OpenAI Responses:** preservar o contrato de `main`, que emite
   `strict: false` quando a ferramenta não especifica o campo; o `strict: true`
   opcional do MCP continua sendo carregado. O operador escolheu essa opção
   porque manter `false` explícito impede o provider de impor exigências strict
   a schemas com parâmetros opcionais.

## Contexto e plano de integração

No início do trabalho, `main` estava 960 commits à frente e a feature 33 commits
à frente do ancestral comum (`760af5ac`). A simulação de merge identificou 20
caminhos em conflito: 16 conflitos de conteúdo e quatro conflitos por remoção
em `main` versus alteração na feature. O merge real foi iniciado com
`--no-commit --no-ff` e permanece sem resolução final.

Plano aprovado: manter as implementações e testes mais recentes de `main`,
adaptando sobre eles branding, URLs/links externos e recursos Percival da
feature. Em JSON de localização, preservar as chaves/traduções que `main`
adicionou e rebrandear apenas a identidade da aplicação Percival; conservar
menções que identificam o runtime nanobot e conexões a servidores nanobot.
Em testes, unir cobertura nova e existente em
vez de descartar a cobertura de qualquer lado.

## Principais conflitos observados

- `.github/workflows/ci.yml`: job de TUI/Docker recente em `main` versus
  renomeação do job Docker no fork.
- `nanobot/providers/openai_responses/converters.py`: suporte a `strict` em
  schemas de ferramentas; preservar o `false` explícito de `main` e carregar
  `true` do opt-in do fork. O teste de ausência foi atualizado para refletir
  essa decisão.
- `webui/index.html`, `webui/src/App.tsx`, `webui/src/components/Sidebar.tsx` e
  locales: UI evoluída e strings recentes de `main` versus marca Percival e
  destinos externos da feature.
- Logos e `webui/src/tests/settings-view.test.tsx`: removidos em `main`, mas
  alterados pela feature; manter somente assets e testes compatíveis com a
  arquitetura atual e a decisão de branding acima.
- `webui/src/tests/app-layout.test.tsx`: preservar cobertura nova de ambos os
  lados, incluindo sidebar redimensionável, novas telas e branding.

## Verificação e entrega

Resultados na árvore integrada:

- WebUI: lint e build passaram. A suíte completa teve 2.621/2.622 testes
  aprovados; o único restante é
  `remote instance UX > tolerates transient health failures and covers, rather
  than reloads, the remote frame`, um teste de reconexão remota que falha em
  pontos diferentes entre a execução completa e a isolada. A implementação
  remota não foi alterada neste merge.
- Python: 366 testes focados de MCP/Responses passaram e `uv run ruff check .`
  passou. `uv run basedpyright` nos cinco arquivos Python alterados passou
  (`0 errors`). A verificação global `basedpyright nanobot` não passou no
  ambiente por dependências opcionais de canais ausentes (`telegram`, WeCom,
  WhatsApp); os diagnósticos estão concentrados nesses módulos.
- Git: não restam caminhos com conflito.

O merge, commit e push de `main` serão concluídos após a revisão final do
diff e do estado da branch.
