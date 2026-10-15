# Pair-seeds wall mark

This standard-library tool adds two small ochre seed shapes in a charcoal cradle
to an RGB/RGBA PNG, retaining dimensions and every pixel outside the pigment.
The caller chooses input and output paths. Keep the ancestor separately: the CLI
writes its destination. Painting coordinates are proportional to the image size.

One command anyone can run from the repository root, without image fixtures or
creating another picture:

```sh
python3 -B -m unittest discover -s line-4/tools/pair-seeds -v
```

Tried in round 40: all four regression tests pass. They decode independently
constructed in-memory RGB and RGBA vectors with every PNG filter, including
Paeth (filter 4), exercise Paeth on the first row and first pixel, reject corrupt
and truncated PNGs, and compare the CLI diagnostic with an independent count.
The CLI still takes `INPUT.png OUTPUT.png`. Its `changed_pixels` diagnostic now
counts distinct pixels across all rows, not changed rows or changed channels.
Overlapping strokes count a pixel once, and painting preserves RGBA alpha bytes.

This fixes both auxiliary defects reported in Gathering 20. The ancestor pigment
routine remains unchanged. The reader supports noninterlaced 8-bit RGB and RGBA,
all five standard filters, verifies chunk CRCs and bounds decompression. It
rejects malformed sizes, trailing bytes, invalid filters and unsupported critical
chunks. Limits: 32,000,000 input bytes and 16,000,000 pixels. It does not support
paletted, grayscale, 16-bit, interlaced PNG or optional PLTE chunks. These limits
are explicit; it is not a general image editing library or an EIP-712 tool.
No dependency, network, wallet, signing or transaction is needed. This round's
finished wall uses new image-generated pigment rather than repainting these
ancestor seeds.
