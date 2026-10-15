# Pinned read batch

Check a saved public Ethereum RPC batch against a SHA-256 retained separately,
then replay its request IDs, allowed read methods and internal checksums offline.
Unlike the earlier two-source ZTO pin tool, this accepts any batch supported by
`rpc-read-batch`, and reports each request and its result or RPC error in request
order. `--require-results` additionally refuses batches containing RPC errors.
It is standard-library Python, needs no installation, and writes nothing.

From the repository root, replay the inherited real Publicnode ZTO observation:

```sh
python3 -B line-1/tools/pinned-read-batch/pin_batch.py line-1/tools/rpc-read-batch/live-zto-batch.json --expected-sha256 b369c4f39db608ae240242db924f635a10dfb4e7b543a18113d3b110857c497a --require-results
```

I ran this successfully on 2026-10-15: both calls returned results, raw supply
`1000000000000000000000000000` and decimals `18`. This replays the retained real
ZTO capture from 09:02:52 UTC; it makes no fresh chain request. Its `latest` calls
do not guarantee both results came from the same block. The sample hash is a
demonstration reference, not an independently approved chain observation.

For your own evidence, retain its exact-file SHA-256 when you first accept it,
in a separate trusted record. Supply that retained value later. Do not calculate
a new expected hash from the file during review: a replacer can rewrite the file
and recompute all its internal checksums. The expected hash includes whitespace
and differs from the canonical `transcript_sha256` stored inside the batch.
This tool neither updates pins nor automatically accepts changed evidence.

Exit 0 means the pin and batch replay match (and, if requested, no RPC errors).
Exit 1 means a failed check; CLI syntax errors exit 2. Without `--require-results`,
a valid RPC error is accepted as retained evidence and explicitly reported;
an RPC result itself can still be null or semantically wrong.

Input is bounded to 99,000 bytes using descriptor-relative POSIX no-follow file
access. Absolute, hidden, parent, symlink and nonregular paths are refused.
Duplicate JSON keys, NaN and Infinity are rejected. Keep the sibling source
folders `rpc-read-batch`, `bounded-rpc-snapshot`, and `safe-snapshot-files` with
this folder. There are no third-party dependencies.

Run the tests:

```sh
python3 -B -m unittest discover -s line-1/tools/pinned-read-batch -p 'test_*.py' -v
```

Nine tests passed, covering retained real evidence with network transport disabled,
resealed replacement, exact whitespace, malformed pins before file reads, replay
checks even with a matching pin, RPC errors, out-of-order responses, strict JSON,
byte limits and path boundaries. Replacing both the file and expected pin passes;
the tests explicitly demonstrate that limit.

A retained hash establishes byte equality, not provider honesty, Ethereum state,
freshness, ownership, payment, or independent custody of the hash. No wallet,
key, secret, environment lookup, signature, transaction send or network is used.
