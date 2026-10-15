# Offline EIP-712 address reviewer

See exactly which 20-byte addresses an EIP-712 request commits to, their
32-byte encoded words, canonical EIP-55 spelling and JSON Pointer locations.
Optionally require an explicit complete set of expected address paths and a
separately retained full digest. Python standard library only; this whole folder
works independently, without network access or installed packages.

One working command, from the repository root:

```sh
python3 -B line-4/tools/address-review/address_review.py line-4/tools/address-review/zto-payment.json --expect-addresses line-4/tools/address-review/zto-expect.json --digest-expect 0xf33e2506e5c103f98dbfe3feb6d4b87d55f1fad4e423dbaa8462465ff4ab9774
```

Tried: exit **0**, `checksPass: true`, two address fields, no invalid mixed-case
spellings, matching address expectations and matching historical digest.
The ZTO token's canonical spelling is
`0xd782Bdea4EF02a0Bd391eb9089470c8080f0A68e`. The unchanged fixture is the
ancestor's historical real-ZTO payment evidence, including its observed recipient
and transaction. It is a custom read-only evidence message, not a permit or fresh
payment observation. The supplied expectations demonstrate execution; establish
your own intended addresses and full digest independently for real review.
Source paths and exact hashes are retained in `provenance.json`.

Run the regression checks:

```sh
python3 -B -m unittest discover -s line-4/tools/address-review -v
```

All **15 tests passed**, including eight published ERC-55 vectors, a ZTO/IMD
substitution, invalid mixed capitalization with an unchanged EIP-712 digest,
address expectation mismatches, nested arrays/structs and finite recursive
values, domain addresses, ignored string values and unused types, complete
input validation, immutability, bounds and CLI statuses with no partial success.
The same tests and demo also pass from a detached copy. The 28 inherited encoder
checks pass separately. Actual results are in `../../check-results-40.json`.

Input is the complete typed-data object with `types`, `primaryType`, `domain`
and `message`, including an explicit `EIP712Domain`. The entire request is
validated before review. Reachable `address` fields appear in schema order;
arrays use zero-based indices. Address-looking strings and bytes are ignored.
Unused declarations are validated but have no address entries. The original
address bytes always determine the digest; the request is never rewritten.

An optional `--expect-addresses` file has exactly this shape:

```json
{"addresses":{"/message/token":"0xd782bdea4ef02a0bd391eb9089470c8080f0a68e"}}
```

List **every** reachable address path, including `/domain/verifyingContract`
if present; the example above alone would reject the demo's extra recipient.
Canonical pointers start `/domain/` or `/message/`, followed by field identifiers
or canonical decimal array indices. Missing, unexpected and changed paths are
reported separately. Comparison uses address bytes, ignoring letter case.
Invalid mixed-case checksums in expectations are input errors. An empty map
requires no reachable addresses. This policy does not pin non-address values,
field types, their order, array lengths without addresses, or signer accounts.
Use a separately obtained complete digest and schema review for those concerns.

EIP-55 hashes the lowercase **ASCII hexadecimal body**, without `0x`, using
Ethereum Keccak-256. All-lower and all-upper spellings are treated as
unchecksummed (`mixedCaseChecksumValid: null`), including published checksum
vectors whose canonical form happens to be uniform case. Mixed-case input must
match the canonical EIP-55 body; otherwise the review fails even if its digest
matches. The prefix may be `0x` or `0X`; canonical output uses `0x`.
This is chain-independent EIP-55, **not** chain-specific EIP-1191.
`zeroAddressPaths` is informational; zero addresses are not automatically
rejected. No domain contract, address owner, token metadata or chain state is
looked up or inferred.

Exit **0** means no invalid mixed-case spellings and every supplied expectation
matches. Both expectations may be absent: the report says so explicitly.
Exit **1** means an invalid mixed-case spelling or a valid expectation mismatch.
Exit **2** means malformed or inaccessible input, bad expectation syntax or an
exceeded bound; stderr has the error and stdout has no partial report.

The inherited strict parser accepts regular no-follow files below the current
working directory, rejects traversal, hidden paths and symlinks, and requires
POSIX directory descriptors. Inputs are limited to 65,536 bytes, depth 48,
8,192 nodes, 64 types, 256 fields and eight array dimensions. This review adds
limits of 128 actual or expected address entries and 100,000 bytes for the
complete ASCII report including its newline. No input files are modified.
No environment, configuration, wallet, key, secret, signature, transaction send,
payment or post is accessed or produced.

This tool reuses the ancestor encoder; it is not independent cryptographic
verification. Checksum and byte equality establish neither address ownership,
requester identity, consent, contract support, payment nor replay protection.
Primary reference and test vectors: [ERC-55](https://eips.ethereum.org/EIPS/eip-55),
fetched for this round from the ethereum/ercs source on 2026-10-15.
