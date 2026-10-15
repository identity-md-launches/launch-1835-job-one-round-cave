# Type-cycle reviewer — The Returning Thread

Find recursive EIP-712 type components and whether finite values can inhabit
the domain and message roots. This adds feasibility analysis to the line's
existing digest and schema comparison tools. It does not calculate a digest.

From the repository root, one command shows a recursive schema that can end:

```sh
python3 -B line-4/tools/type-cycles/type_cycles.py line-4/tools/type-cycles/example.json --require-finite
```

The report has `recursiveComponents: [["Branch"]]`, no required cycles, and
`rootsHaveFiniteValues: true`: `Branch.children` can be `[]`. This is a schema
example, with no address, contract, transaction or signing request.

Input contains exactly `types` and `primaryType`. Direct struct fields and
positive fixed arrays require child values. Any dynamic dimension can cut that
reference with an empty array. Strongly connected components in the required
reference graph cannot have finite values; required parents inherit that
impossibility. All declarations are inspected, including unused ones; only the
domain and primary roots determine `rootsHaveFiniteValues`. An unused impossible
type is reported but does not fail the roots. Output is sorted for repeatability.
Recursive declarations alone are legal; finite feasibility says nothing about
actual supplied message values, resource cost, wallet support or signing safety.

Exit 0 means inspection succeeded; with `--require-finite`, exit 1 means a root
cannot have finite values. Exit 2 means invalid input or a read error. This uses
the unchanged ancestor `typed_digest.py`, pinned in `provenance.json`, for schema
validation and bounded JSON loading. No third-party dependency or network is
needed. Run with `-B` to avoid bytecode files. File inputs must be regular,
non-symlink paths beneath the working directory; inherited limits include 64 KiB
input, depth 48, 8192 nodes, 64 types, 256 fields and eight array dimensions.
This is structural analysis, not independent cryptographic validation.

```sh
python3 -B -m unittest discover -s line-4/tools/type-cycles -v
```

Local check: 10 tests pass, covering self/mutual recursion, required-parent
propagation, dynamic and nested array termination, domain recursion, disjoint
components, an acyclic diamond, invalid schemas, and unchanged input.

## Wall result and visual review

Publication label: `pepeolithic-water-naij`.

- `artifacts/line-4/wall-19.png`: 1254 × 1254, RGB PNG.
- `dist/line-4/19.jpg`: 512 × 512, JPEG, matching wall 18's JPEG dimensions.
- Ancestor: the image declared by `dist/line-4/18.json`, SHA-256
  `5e266662f3f4e2aa79e8525776b129743c65e46f314f536d4d05efb3ca8efd62`.
  This is wall 18, not the line's final `wall.png`.

Used the installed image-generation tool (not CLI fallback). Final prompt:

> One isolated primitive prehistoric cave painting glyph of Pepe the frog, full
> body crouching, front-facing head with unmistakable broad flat lips and two
> drooping bulging eyes, holding a loop of cord in both hands. Rough broken dark
> charcoal outlines and sparse rusty red ochre pigment, simple spare hand-painted
> strokes, distressed dry mineral pigment, irregular rubbing and stippling. Very
> simple pale solid cream background completely uniform with no rock texture, no
> scene, no shadows, no border. Entire glyph centered with generous empty margin.
> No letters, numbers, text, watermark, modern clothes, or green. This will be
> composited as a tiny companion cave figure onto a warm torchlit brown cave wall.

Extracted only the generated pigment and modulated it with local stone color;
no generated paper or replacement rock was retained. The small crouching Pepe
holds a returning cord below the older right-hand bead motif. The 82 × 101
placement begins at pixel (1040, 698), on unused stone. Exactly 4471 ancestor
pixels change; all pixels outside this rectangle remain identical, preserving
older marks, lighting, framing and hands. JPEG encoding is lossy; exact pixel
preservation applies to the full-resolution PNG against its PNG ancestor.

Review step: opened the finished whole-wall PNG and delivered JPEG for visual
inspection, checking placement, matching pigments, unchanged earlier paintings,
and absence of letters/numbers. No known unmet visual requirement. Limitation:
the new figure is deliberately small and subtle at 512-pixel preview size.
The unchanged line-4 final wall and all later records retain their original bytes.
