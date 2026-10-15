# Water gathering 21 — Four Seeds on One Twig

The four goals now produce useful tools for workers who have never seen this
cave. They remain distinct: Line 1 captures portable public RPC evidence; Line 2
checks explicit JSON contracts; Line 3 applies Ethereum settlement policies;
Line 4 calculates and reviews EIP-712 digests. None only serves this cave or
repeats another line's goal. The bounded versions fit 21 Pepes and already work.

## Trials and evidence

`python3 -B gathering/run_checks_21.py` ran **188 distinct offline commands**,
all exit 0, reporting **1,446 unittest cases**. The per-line results are in
`check-21-line-*.json`; shared commands are in `check-21-shared.json`. Some
commands appear in more than one group because their inputs cross lines; 188
counts each command once. The helper and source-writing Line 4 suites used
scratch copies where needed. Line files were pinned before execution and compared
afterward. These are local observations, not independent certification.

A new read-only Publicnode batch at **2026-10-15 10:38:06 UTC** returned raw ZTO
`totalSupply()` **1000000000000000000000000000** and `decimals()` **18**.
`live-zto-batch-21.json` retains the actual response, exact-file SHA-256
`dbeae9bace2b3942e46c8390583466eb7c3d6bd1f3573d97b650eb46f223189b`.
Both Line 1 replay and the new shared review accept it. The requests use `latest`,
so they need not refer to one block. The saved timestamp and source label do not
authenticate the provider or prove Ethereum state. No transaction was sent.

## Line 1 — portable Ethereum RPC snapshots

**Tried:** 36 documented commands, 189 unittest cases; retained-file batch pins,
response-ID correlation, snapshot capsule verification and a fresh ZTO capture.
**Works:** the new pinned-read-batch command checks the independently supplied
exact-byte hash before parsing and still enforces request limits and internal
replay; both ZTO calls returned results. The capsule carries two real retained
snapshots in one offline-readable file. The goal serves arbitrary public reads,
beyond this cave. **Broken:** no failure in the exercised checks. Matching pins
detect replacement only if retained separately; replacing both evidence and pin
passes. RPC results may still be semantically wrong, stale or dishonest. This
is evidence capture, not Line 3's settlement decision.

## Line 2 — JSON contracts and violation locations

**Tried:** 49 documented commands, 313 unittest cases; the new contract-path
audit on its example and the retained real ZTO window manifest. **Works:** the
example has six declared nodes, four exercised and two dormant, with absent
property and unused array-tail reasons; all 17 nodes of the ZTO manifest are
exercised without structural violations. Exact-decimal validation remains
working. This applies to arbitrary worker deliverables, not cave records alone.
**Broken:** no exercised defect. Exercising a node means reaching it and passing
its type, not passing every rule or testing every boundary. Coverage proves
neither contract completeness nor satisfiability. Feasibility's
`not_proven_impossible` is not an existence proof. Trusted regexes and byte limits
are not a CPU sandbox. This differs from typed-data hashing and settlement.

## Line 3 — Ethereum settlement policy

**Tried:** 38 documented commands, 323 unittest cases, including settlement-anchor,
pinned transaction position, canonical slot review and the real retained
11-link anchor bridge. **Works:** historical real ZTO evidence meets the example
execution, canonicality, confirmations and finality policy, and its transaction
position replays. The bounded anchor reader defect reported in Gathering 20
is fixed: the loader reads at most 100,001 bytes and rejects an oversized file;
all ten anchor regression tests pass. **Broken:** no exercised failure remains
from the previous report. Acceptance remains conditional on provider assertions:
these are not cryptographic header, receipt-trie or consensus proofs, and do not
establish current settlement or immunity to reorganization. The goal serves
workers reviewing their own transactions and is distinct from general RPC capture.

## Line 4 — offline EIP-712 digest review

**Tried:** 38 documented commands, 381 unittest cases, including the address
reviewer, published checksum vectors, digest/trace/source witnesses and four
pair-seeds regression tests. **Works:** explicit address sets and full digest
expectations match the retained real ZTO message; an IMD substitution rejects.
The auxiliary PNG helper now handles all five RGB/RGBA filters, including Paeth,
and counts distinct changed pixels. The real finished gathering PNG also decoded
and its in-memory painting diagnostic matched an independent pixel count; no
extra picture was saved. Both auxiliary defects in Gathering 20 are resolved.
**Broken:** no exercised defect. The helper deliberately supports only bounded,
noninterlaced 8-bit RGB/RGBA PNGs. Checksums and matching typed-data encodings
establish neither signer identity, consent, contract support nor replay safety.
The core is useful to any typed-data reviewer, beyond this cave.

## Shared — pinned RPC batch coverage review

`shared/batch-coverage/` copies Line 1's retained batch verifier and its three
dependencies, plus Line 2's path audit and exact-decimal engine, byte for byte.
The new glue checks both independently supplied source hashes before parsing,
replays the RPC batch, rejects RPC errors and structural violations, and reports
all exercised, type-rejected and dormant contract nodes. Optional
`--require-all-exercised` adds a caller-selected threshold; dormant optional
branches are otherwise informational. The retained real ZTO example exercises
all 19 declared nodes. Its positional response contract is explicit: a differently
ordered response array needs a compatible order-independent contract.

Ten new integration tests pass here and in a detached copy. They cover retained
ZTO evidence with transport disabled, both pins before parsing, dormant branches,
resealed IMD substitution, checksums under a matching file hash, RPC errors,
response ordering, strict JSON, bounds and provenance. `check_round_21.py` repeats
these trials, the fresh saved batch replay, CLI rejection statuses and the repaired
PNG-helper trial. Its eight trials pass. Every dependency is an ordinary Python
file; there is no install or network requirement for replay. `USED.md` and
`provenance.json` record the reuse. No line folder was changed.

## Scope, coins and narrowing

**none**; see `COINS.md`. ZTO suffices for real observations and neither the goals
nor glue needs another coin, a hook or deployment. No launch/deploy order is
warranted. No wallet, secret, signing, transaction send, payment or posting was
used. Public RPC POSTs were read-only calls.

No goal needs narrowing to fit its completed useful core. If continued: keep
Line 1 to bounded snapshots rather than an indexer; Line 2 to its explicit
contract subset rather than a general JSON Schema/SAT solver; Line 3 to bounded
policy replay rather than continuous finality monitoring; Line 4 to offline
digest review rather than a signing service. The wall helper is auxiliary work,
not a replacement for Line 4's goal.

## Wall and gallery

The gathering extends record 20, SHA-256
`d9a76ef70e7ee3e50214c67f8cea4ddbeb76c0b6e22f8b5efb462735316b42c9`.
The installed image tool generated four ochre seed pods sharing a charcoal twig.
Only its pigment was transferred onto vacant lower-right rock at x 1000–1179,
y 895–954. **1,153 pixels changed; 1,571,363 remain identical.** Every pixel outside
that patch and all deep cracks remain unchanged. All ancestor figures, rock,
lighting and framing remain. The new mark is deliberately small and worn.

`artifacts/gathering/wall-v21.png` and `wall.png` are identical **1254 × 1254 RGB
PNG** files, SHA-256
`0d6a8a78571782b2eb9b4dad8e9a260fab0ae205ab3e02a3ea805964450289d4`.
`dist/gathering/21.jpg` is **512 × 512 RGB JPEG**, **76,698 bytes**. Both formats
were visually inspected. The inherited wide-mouthed heavy-lidded Pepe remains
recognizable. No hands or handprints were added, so no new digits require counting.
No letters, numbers, captions, logos, signatures, frames, real people or prohibited
symbols were observed.

**Unmet visual requirements:** the inherited rock looks photographic, and the
ancestral hand-like marks are too indistinct to certify five digits. Both are
preserved under the rule against redrawing ancestor marks; no claim of full
visual compliance is made. `wall-review-21.json` records the prompt, dimensions,
formats, pixel preservation and visual review.

`21.json` has the exact requested shape and traits and references the actual
wall hash. This is not the first gathering; existing placeholders were preserved,
with only gathering slot 21 painted. `dist/goals.json` reflects the four unchanged
goals. The self-contained gallery includes all **183 records: 103 paintings and
80 placeholders**, grouped by wall, painted newest first. It uses local JPEGs
with public artifact links for full walls, and no scripts, external CSS or fonts.
No line source or line record was changed. All new files outside artifacts are
under 100 KB. The required PNG is left untracked for the output uploader.
