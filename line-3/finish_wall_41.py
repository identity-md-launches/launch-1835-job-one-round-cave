"""Place image-tool pigment on open rock; preserve every other wall pixel."""
import base64
import hashlib
import json
import sys
from pathlib import Path

from finish_wall_39 import read_rgba
from image_bytes import jpeg, png, read_png, resize

ROOT = Path(__file__).resolve().parent.parent
WALL = ROOT / "artifacts/line-3/wall.png"
OUT = ROOT / "artifacts/line-3/wall-v21.png"
PREVIEW = ROOT / "dist/line-3/41.jpg"
RECORD = ROOT / "dist/line-3/41.json"
ANCESTOR = "3dd8528511a97bdcedcac38a61d8867491ed1780d1989d5810cac7caaa42786b"
RECTANGLE = (1020, 595, 115, 105)
PROMPT = (
    "A single isolated prehistoric cave-painting motif: a small irregular charcoal-black "
    "protective arch around one red-ochre pebble, with a few short yellow-ochre mineral "
    "strokes inside the arch. Flat hand-daubed pigment, sparse, worn and uneven, as if "
    "painted on warm stone with burnt stick and thumb. Keep the shape compact and clearly "
    "separated from the transparent background. Earth pigments only: red ochre, yellow "
    "ochre, charcoal black, chalk white. No frog, no hands, no handprints, no letters, "
    "no numbers, no captions, no signatures, no logos, no watermarks, no border, no "
    "frame, no people, no symbols. PNG with actual transparent background."
)


def main():
    old_bytes = WALL.read_bytes()
    if hashlib.sha256(old_bytes).hexdigest() != ANCESTOR:
        raise ValueError("ancestor wall hash differs")
    w, h, old = read_png(old_bytes)
    if (w, h) != (1254, 1254):
        raise ValueError("unexpected wall dimensions")
    encoded_mark = sys.stdin.readline().strip()
    mark_bytes = base64.b64decode(encoded_mark, validate=True)
    mw, mh, mark = read_rgba(mark_bytes)
    points = [(x, y) for y in range(mh) for x in range(mw)
              if mark[(y * mw + x) * 4 + 3] > 40]
    if not points or len(points) > mw * mh * 3 // 4:
        raise ValueError("expected isolated transparent pigment")
    sx0 = min(x for x, _ in points)
    sy0 = min(y for _, y in points)
    sx1 = max(x for x, _ in points) + 1
    sy1 = max(y for _, y in points) + 1
    x0, y0, width, height = RECTANGLE
    final = bytearray(old)
    changed = 0
    for dy in range(height):
        ya = sy0 + dy * (sy1 - sy0) // height
        yb = sy0 + (dy + 1) * (sy1 - sy0) // height
        for dx in range(width):
            x, y = x0 + dx, y0 + dy
            i = (y * w + x) * 3
            rock = old[i:i + 3]
            if max(rock) < 75:  # Deep fissures and existing charcoal survive.
                continue
            xa = sx0 + dx * (sx1 - sx0) // width
            xb = sx0 + (dx + 1) * (sx1 - sx0) // width
            samples = []
            for gy in range(ya, yb):
                for gx in range(xa, xb):
                    j = (gy * mw + gx) * 4
                    r, g, b, a = mark[j:j + 4]
                    if a <= 40:
                        continue
                    if r > g * 1.35 and r > b * 1.4 and r > 80:
                        pigment = (151, 65, 39)  # Red ochre pebble.
                    elif r > 105 and g > 85 and b < g * .82:
                        continue  # Leave the generated rays as bare rock.
                    else:
                        pigment = (49, 39, 31)  # Charcoal arch.
                    samples.append((pigment, a / 255))
            if not samples:
                continue
            total = sum(a for _, a in samples)
            coverage = total / ((xb - xa) * (yb - ya))
            color = [sum(pig[k] * a for pig, a in samples) / total for k in range(3)]
            alpha = min(.77, coverage * .77)
            for k in range(3):
                final[i + k] = round(rock[k] * (1 - alpha) + color[k] * alpha)
            if final[i:i + 3] != rock:
                changed += 1
    if changed < 500:
        raise ValueError("pigment transfer too faint")
    for y in range(h):
        for x in range(w):
            i = (y * w + x) * 3
            if not (x0 <= x < x0 + width and y0 <= y < y0 + height) or max(old[i:i + 3]) < 75:
                if final[i:i + 3] != old[i:i + 3]:
                    raise ValueError("ancestor pixel changed outside pigment mask")

    wall_bytes = png(w, h, final)
    sha = hashlib.sha256(wall_bytes).hexdigest()
    preview = jpeg(512, 512, resize(w, h, final), 52)
    if len(preview) > 100_000:
        raise ValueError("preview exceeds 100 KB")
    OUT.write_bytes(wall_bytes)
    WALL.write_bytes(wall_bytes)
    PREVIEW.write_bytes(preview)
    record = {
        "name": "The Guarded Pebble",
        "image": "https://api.imd.fun/artifacts/" + sha,
        "attributes": [
            {"trait_type": "Cave", "value": "Water"},
            {"trait_type": "Wall", "value": "Line 3"},
            {"trait_type": "Number", "value": 41},
            {"trait_type": "Left behind", "value": "settlement-anchor"},
            {"trait_type": "Meaning", "value": "Pepe shelters a proof stone inside a bounded arch before trusting its place."},
            {"trait_type": "One thing", "value": "verify Ethereum transaction settlement"},
        ],
    }
    RECORD.write_text(json.dumps(record, indent=2) + "\n")
    review = {
        "number": 41,
        "ancestorSha256": ANCESTOR,
        "wall": {"paths": ["artifacts/line-3/wall.png", "artifacts/line-3/wall-v21.png"],
                 "dimensions": [w, h], "format": "PNG", "mode": "RGB", "sha256": sha},
        "preview": {"path": "dist/line-3/41.jpg", "dimensions": [512, 512],
                    "format": "JPEG", "bytes": len(preview)},
        "additionRectangle": list(RECTANGLE), "changedPixels": changed,
        "unchangedPixels": w * h - changed,
        "allPixelsOutsideAdditionUnchanged": True,
        "imageTool": "built-in image_gen imagegen",
        "prompt": PROMPT,
        "reviewStatus": "requires final visual inspection",
        "unmetVisualRequirements": [],
    }
    (ROOT / "line-3/wall-review-41.json").write_text(json.dumps(review, indent=2) + "\n")
    print(json.dumps({"wallSha256": sha, "changedPixels": changed,
                      "jpegBytes": len(preview), "wallDimensions": [w, h]}))


if __name__ == "__main__":
    main()
