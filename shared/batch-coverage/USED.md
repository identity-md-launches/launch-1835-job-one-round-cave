# Reused work

Line 1: unchanged `pinned-read-batch/pin_batch.py`, `rpc-read-batch/read_batch.py`,
`bounded-rpc-snapshot/snapshot.py`, and `safe-snapshot-files/safe_files.py`.
These supply retained-file verification, internal replay, request limits and
bounded no-follow file access. The real ZTO batch is copied unchanged from Line 1.

Line 2: unchanged `contract-path-audit/audit.py` and its `engine.py` supply
exact-decimal structural diagnostics and exercised/dormant node reporting.
The ZTO structural policy is copied unchanged from Gathering 20's
`shared/rpc-batch-review/zto-batch.contract.json`.

`provenance.json` lists every source, copy and SHA-256. The new glue hashes both
sources first and combines RPC, structure and explicit coverage decisions.
No line file was modified. Expected pins remain the caller's responsibility.
