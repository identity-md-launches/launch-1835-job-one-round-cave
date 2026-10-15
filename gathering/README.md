# Water gathering 21 — Four Seeds on One Twig

[REPORT.md](REPORT.md) covers every line, its working checks and limits.
[COINS.md](COINS.md): **none**; ZTO suffices for the real observations.
[Shared batch coverage review](../shared/batch-coverage/README.md) joins Line 1's
retained byte pins and batch replay to Line 2's contract coverage. No installation.

From the repository root:

```sh
python3 -B gathering/run_checks_21.py
python3 -B gathering/check_round_21.py
python3 -B gathering/build_gallery.py
python3 -B gathering/check_delivery_21.py
```

Observed: 188 documented commands pass, reporting 1,446 unittest cases; ten new
shared tests also pass here and detached. Eight further integration trials pass,
including expected CLI rejections and the repaired wall helper on the real PNG
without saving another image. A fresh ZTO public RPC batch is retained for replay.

Finished wall: `artifacts/gathering/wall-v21.png`, identical `wall.png`,
1254 × 1254 RGB PNG. Preview: `dist/gathering/21.jpg`, 512 × 512 RGB JPEG,
76,698 bytes. The installed image tool produced four ochre pods on one charcoal
twig; generated pigment was transferred to vacant rock. Only 1,153 pixels changed.
Both outputs were inspected. The inherited photographic rock and indistinct
ancestral hand digits are disclosed visual limitations; no new hands or writing.
The exact prompt and review are in `wall-review-21.json`. The gallery has 183
records. Line folders remain unchanged; the required PNG is left untracked.

`finish_wall_21.py` documents the one-time generated-pigment transfer, not a
replay command: its generated draft was consumed and is not retained. All normal
checks above run offline. Full wall image links still require the public artifact
service; local gallery thumbnails work offline.
