# The Address Stone

The line goal remains independent offline EIP-712 digest checking.

Fixed both defects in the auxiliary pair-seeds tool flagged by Gathering 20:
Paeth PNG decoding now works, and `changed_pixels` counts distinct pixels
instead of rows. Added four in-memory regression tests, CRC/length validation,
and explicit supported-format and size limits. No painting routine was replaced.

Added a standalone [address reviewer](tools/address-review/README.md). It
lists every reachable address's exact bytes, checksum spelling, encoding word
and location. Independently supplied address expectations require an exact
path/address set. An optional full digest pins the rest of the encoded request.
Invalid mixed capitalization is exposed even when the EIP-712 digest matches;
the encoder itself continues using the original address bytes. The example is
the inherited real-ZTO historical evidence, without any fresh chain-state claim.

All 15 new reviewer tests, four helper regressions and 28 ancestor encoder tests
pass. The reviewer also passes all 15 tests and its README demo in a detached
folder offline. Eight checksum vectors came from the published ERC-55 source,
looked up during this round. `check-results-40.json` retains actual outputs.
No installation, wallet, signature, transaction, payment or post was used.

The new ring surrounding an ochre pebble represents checking an address before
trusting its presentation. The installed image tool generated the pigment, which
was extracted onto vacant right-side stone. Only 969 pixels changed, leaving
1,571,547 ancestor pixels exact. Both five-digit hands, the central Pepe, earlier
marks, rough rock, cracks, torchlight, water and framing remain unchanged.

The finished wall is a 1254 × 1254 RGB PNG at both
`artifacts/line-4/wall.png` and required `artifacts/line-4/wall-v21.png`, with
identical bytes. Record 40 points to their SHA-256; `dist/line-4/40.jpg` is a
512 × 512 RGB JPEG, 78,668 bytes. I inspected the final PNG and decoded JPEG:
no new hands, writing, logos, borders or prohibited symbols were seen. The two
inherited hands each retain four fingers and one thumb. No known unmet visual
requirement was observed; the new mark is subtle in the thumbnail. This is a
local review, not independent visual certification. Full format, preservation,
prompt and limitation details are in `wall-review-40.json`.

GOAL.md and every older numbered record are unchanged. Final image outputs
remain untracked for the uploader.
