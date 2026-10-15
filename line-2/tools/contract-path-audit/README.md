# Offline JSON contract path audit

Check one JSON document against an explicit structural contract and see which
declared contract branches the document actually reached. A valid document may
leave optional properties or array tails untested. This tool reports those
dormant branches separately from violations; it never treats coverage as proof
that the contract itself is complete. Python 3.10+, standard library only.

From the repository root, one command demonstrates it:

```sh
python3 -B line-2/tools/contract-path-audit/audit.py line-2/tools/contract-path-audit/handoff.contract.json line-2/tools/contract-path-audit/handoff.example.json
```

Observed: exit **0**, `valid: true`, `complete: true`, six declared nodes,
four exercised and two dormant. `/properties/note` says `property_absent`;
`/properties/items/items` says `no_tail_items`. The example contains no
address, key, payment, chain claim or requester-owned value.

The retained real ZTO transaction-window manifest can be audited with:

```sh
python3 -B line-2/tools/contract-path-audit/audit.py line-2/tools/field-relations/window.contract.json line-2/tools/field-relations/window-plan.json
```

Observed: exit **0**, all 17 declared nodes exercised, zero dormant or
violations. This checks the retained manifest's JSON structure only; evidence
paths inside it are data and are never opened. It makes no fresh chain or
settlement claim.

## Reading the result

`errors` are the inherited exact-decimal checker's structural diagnostics,
with escaped JSON Pointer paths into the document. `nodes` lists every
declared contract node with its escaped `contractPath`, type, local rule names,
visit count, type-pass count and up to three example document paths.
`exercised` means at least one value reached the node and passed its type
check; it does not say all its rules passed. `type_rejected` means values
reached it, but none passed its type check. `dormant` means no value reached
it. Dormant reasons distinguish an absent object property, a short array,
no array tail, a dormant parent and a parent rejected by type.

Both inputs are captured once from visible relative workspace paths. The
included engine refuses symlinks, hidden or parent components, absolute paths,
directories and special files, using no-follow POSIX reads capped at
1,000,000 bytes per file. Optional `--contract-sha256 HEX` and
`--document-sha256 HEX` check independently retained lowercase digests before
either source is parsed. The report includes both byte counts and digests;
pins do not authenticate authors. Complete output is capped at 1,000,000
bytes. Exit **0** means valid, **1** means structural violations, **2** means
input or output failure. Require `complete: true` and exit 0 for acceptance.

This audits branches actually reached by **one** document. It does not prove
untested branches are possible, prove a regex satisfiable, check cross-field
relationships or establish semantic truth. Trusted regular expressions and
the inherited uniqueness check are not CPU sandboxes. It reads no environment,
secret or external path, contacts no network and writes only stdout.

`engine.py` is a byte-for-byte ordinary-file copy of the prior
`contract-feasibility/engine.py` (SHA-256
`58aadca2f4c75626e115f689e26dd2167a679e966b610d8924595c0723f05cd5`).
No package installation is needed. `python3 -B
line-2/tools/contract-path-audit/test_audit.py` passed seven focused tests,
including missing required and optional fields, escaped pointers, array
prefixes and tails, parent type rejection, exact decimals, pin order and the
retained ZTO plan.
