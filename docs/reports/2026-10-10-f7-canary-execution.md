# F7 — execução parcial de pins e canary local (snapshot intermediário)

- **Data:** 2026-10-10 UTC (snapshot antes do canário Percival).
- **Escopo:** ação 3 do plano F7. Antes da instalação Percival.
- **Substituído por:** [`2026-10-10-f7-local-stack-provisioning.md`](2026-10-10-f7-local-stack-provisioning.md).

## Estado no snapshot

- Positronic: 5 MCPs configurados/atualizados (Notes, AgentMail, Deep
  Research, Khan, Weather). OSM instalado, desativado, aguardando
  identidade local.
- Percival: registro rev4, pins antigos, broker `ready`, sem mutações.
- Mudanças locais pendentes: builds Notes (`ef4082ef…`) e AgentMail
  (`e104ac75…`) com `PERCIVAL_NOTES_VAULT_PATH` e
  `AGENTMAIL_API_KEY_FILE` respectivamente; patches Positronic para
  `env` tipado em ServerConfig; 13/13 pacotes typecheck, 28/28 managed
  tests, 232/1 AgentMail tests, 48/48 Notes tests.
- Permissões do home ajustadas de 700 para 755 em `/home/bill`,
  `/home/bill/.local/share/percival-test-mcp` e seus subdiretórios
  (vault/calendar) com modo 777 para escrita dos containers Notes/Khan.
- Senha `operator.json` ainda não validada: a primeira tentativa
  correspondeu ao hash já armazenado, não à senha real. O usuário
  forneceu `meusMCPs` em sessão subsequente, que verificou.

## Pendências para continuar

1. Receber `operator-password` com a senha real (após `meusMCPs`, foi
   gravada e validada).
2. Configurar/discover/ativar OSM no Positronic.
3. Instalar/atualizar os 6 MCPs no Percival via domínio autenticado.
4. Limpar imagens e containers antigos.
5. Atualizar relatório final e plano.
