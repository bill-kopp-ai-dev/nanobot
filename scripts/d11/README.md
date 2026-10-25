# D11 skill rehearsal

This runner adapts the disposable Engine 27.5.1 harness in
`../percival-i2-runtime-smoke.py` and the manager rehearsal in
`d9_rehearsal.py`. It transfers only the exact local images passed on the
command line into a uniquely named rootful DinD Engine. The host Docker daemon
owns only the disposable DinD container; all test managers, images, MCPs,
revisions, backups, journals and audit records are inside it. A read-only
checkout copy of the approved skill and local operations runbook is mounted into
the disposable gateway context. The gateway itself has no Docker socket.

Example from the repository root (requires the recorded local candidate and
D9 broker images to be available and Docker Compose):

```sh
python3 scripts/d11/skill_rehearsal.py \
  --gateway-image percival-gateway:0.1.0-40d8eb9-d11-2e4d276142d8 \
  --broker-image percival-mcp-broker:0.1.0-3daabe2 \
  --scratch-parent /tmp
```

The runner writes `results.json` and redacted failure logs to the generated
scratch directory and removes only its uniquely named DinD container in the
`finally` cleanup. It never connects the fixture to production MCPs. The image
arguments must be reviewed by immutable image ID before use; the gateway tag
identifies the locally deployed D11 worktree candidate and is not a release.

The runner verifies Built-in loader/context assembly and a deterministic manager
dry-run, including stale CAS and invalid-field rejection, then repeats D9's
A→B→A, false stdio HTTP healthcheck and current backup/restore checks. It does
not invoke an LLM, so it cannot establish that an agent produces the right dry
run. It also does not yet implement the HTTP profile with failing readiness;
those gates remain open for D11.
