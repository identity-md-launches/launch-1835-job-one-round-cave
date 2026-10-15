# Settlement anchor

`settlement-anchor` joins three retained facts before a worker relies on a
settlement: the requested policy, a successful settlement verdict, and the
transaction's recorded `(block number, block hash, transaction index)` slot.
It refuses a transaction mismatch, block-anchor mismatch, reverted verdict,
bad confirmation arithmetic, insufficient confirmations, or missing required
finality. It uses only Python's standard library and never opens a wallet,
signs, sends, or posts.

From the repository root, run the bundled example:

```sh
python3 -B line-3/tools/settlement-anchor/anchor.py --demo
```

The command exits 0 with `anchored: true`. A worker-owned bundle can be checked
with `--bundle path/to/bundle.json`; paths are bounded to regular files inside
the workspace. The loader now reads at most 100,001 bytes before refusing an
oversized bundle, and opens each path component without following symlinks.
Hidden paths, traversal, directories and special files are refused. Safe opens
require POSIX descriptor-relative file support and fail closed elsewhere. The
bundle is a join boundary, not a replacement for the
settlement verifier or independent hash custody.

What happened when tried: the demo passed, and ten focused tests passed. The
new tests cover the exact size boundary, an oversized file, a symlink, a FIFO,
and unsafe paths. The gathering report's unbounded read finding is repaired.
Run them with `python3 -B -m unittest discover -s line-3/tools/settlement-anchor -p 'test_*.py'`.
The
demo replays a retained real ZTO transaction and its historical settlement
position offline; it is not a fresh chain observation. It does not prove
consensus, receipt inclusion by a cryptographic trie proof, payment amount or
authorization, and a later reorganization remains possible.
