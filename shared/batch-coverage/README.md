# Pinned RPC batch coverage review

Combine Line 1's independently retained byte pin and offline RPC batch replay
with Line 2's exact-decimal structural check and contract path audit. A worker
can see both violations and declared branches that this document never reached.
Python 3.10+, standard library only; no installation, network or line folders
needed. Everything required travels in this directory as ordinary files.

From the repository root, replay the retained real ZTO batch:

```sh
python3 -B shared/batch-coverage/review.py shared/batch-coverage/zto-batch.contract.json shared/batch-coverage/zto-batch.json --contract-sha256 38219d0c9192f3566be0bf9d650c8de7de0666b562f23f3b6be7bb2d01b3dae1 --transcript-sha256 b369c4f39db608ae240242db924f635a10dfb4e7b543a18113d3b110857c497a --require-all-exercised
```

Observed: exit 0, `accepted: true`, two requests, no violations or RPC errors,
all declared contract nodes exercised. The sample preserves real historical
Publicnode ZTO `totalSupply()` and `decimals()` reads, with their original bytes.
The two `latest` requests are not guaranteed to refer to the same block. The
example contract intentionally requires response array order; the RPC replay
itself correlates responses by ID. Use an order-independent contract when your
response arrays may be permuted.

For your own batch, retain the exact contract hash and exact transcript hash
separately when you first accept them. Both hashes are checked before either
input is parsed. Do not calculate replacement expected pins from incoming
evidence and mistake that for approval. The bundled example pins demonstrate
execution, not independent custody or authenticated Ethereum state.

The report contains full structural diagnostics and per-node coverage, source
hashes and byte counts, RPC error count, and the explicit coverage policy.
`exercised` means a value reached that contract node and passed its type check;
other rules can still fail. An absent optional property can be dormant in a
valid document. By default dormant nodes are informational. The optional
`--require-all-exercised` flag declines any document leaving a node dormant or
type-rejected. It does not test every rule boundary or prove a contract complete,
satisfiable or appropriate. It is unsuitable for contracts with intentionally
unused alternatives unless you want that stricter decision.

Exit 0: matching pins, successful replay, no RPC errors, valid structure, and
any requested coverage threshold met. Exit 1: a complete negative review.
Exit 2: invalid input, pin mismatch, invalid RPC replay or oversized report;
`complete` is false. CLI syntax errors also exit 2.

Inputs and complete ASCII output are capped at 99,000 bytes each. Visible
workspace-relative regular files only; descriptor-relative reads refuse hidden,
absolute, parent, symlink and special-file paths. Each source path is captured
once. Duplicate JSON keys and nonfinite numbers reject. Contracts and regular
expressions must be trusted: byte bounds are not CPU limits. Success proves no
provider honesty, current balance, payment, settlement, signer identity, consent
or replay protection. Nothing is signed or sent. No environment or secret is read.

Run the integration checks:

```sh
python3 -B shared/batch-coverage/test_review.py
```

Ten tests passed both here and from a detached copy: real retained ZTO with
transport disabled, both pins before parsing, dormant-branch policy, resealed
IMD substitution, invalid internal checksums under a matching byte pin, RPC
errors under a permissive contract, reordered replies, strict JSON and bounds,
vendor hashes, and external path refusal. Mutations exist only in memory.
`provenance.json` records exact copied source hashes. The implementation does
not depend on sibling shared bundles or the cave gallery.
