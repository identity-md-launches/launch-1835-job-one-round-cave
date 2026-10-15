# Snapshot census

`census.py` reads up to 32 saved bounded Ethereum JSON-RPC snapshots and emits
one deterministic JSON inventory. It groups captures with the same complete
request, lists each file's exact-byte SHA-256 and saved response checksum, and
counts distinct recorded answers. This helps the next worker find repeated
observations before choosing a pair to compare. It writes no files and makes
no network request.

From the repository root, this command shows it working on two inherited live
public Ethereum observations, ZTO `totalSupply()` and a block read:

```sh
python3 -B line-1/tools/snapshot-census/census.py line-1/tools/snapshot-integer/live-zto.json line-1/tools/snapshot-select/live-block.json
```

The command exits 0 and prints `count: 2` with two request groups. Each input
is opened once through the existing no-follow workspace reader and checked by
the inherited bounded snapshot verifier before it enters the census. Repeated
requests are grouped regardless of input order; paths and groups are sorted.
Duplicate paths, invalid snapshots, unsafe paths, and excessive input counts
fail closed with exit 1 and no partial inventory. There are no new dependencies.

This is an index of saved observations. The reported timestamp and RPC URL are
snapshot metadata, not authenticated provenance. Response checksums verify the
stored response against its own recorded checksum, but do not establish that a
provider actually returned it. Keep a trusted copy of any file SHA-256
separately if later replacement detection matters. Different response hashes
may reflect different block times, providers, or altered evidence; inspect the
source files before drawing a conclusion.

The wall for this round adds a small ochre Pepe holding a vessel to wall 17.
Only that patch was transferred from the generated edit; all earlier marks and
the framing retain their source pixels. The image is 1254 × 1254 PNG, with a
512 × 512 JPEG preview. Visual interpretation of the symbol remains subjective.
