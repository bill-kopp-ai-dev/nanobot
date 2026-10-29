# A-011 consumer fixture

This fixture models the Percival bundle invoking the IaC-owned installation
preflight. It deliberately does not implement daemon ownership or locking; those
remain owned by `positronic-bean-IaC/scripts/preflight.py`.

Run it only against a disposable Docker Engine. Pass the IaC script explicitly:

```bash
python tests/mcp_docker/fixtures/a011/consumer.py \
  --preflight-script /path/to/positronic-bean-IaC/scripts/preflight.py \
  --installation-id percival-fixture -- python -c 'print("fixture mutation")'
```

The Stage-2 acceptance also requires testing concurrent calls and a conflicting
installation against a disposable Engine, then verifying that the rejected
consumer command made no change to that daemon.
