#!/usr/bin/env python3
"""One-time transfer of image-tool pigment onto vacant ancestral rock."""
import hashlib
import json
from pathlib import Path
from image_bytes import read_png, png, resize, jpeg

ANCESTOR = 'd9a76ef70e7ee3e50214c67f8cea4ddbeb76c0b6e22f8b5efb462735316b42c9'
PROMPT = ('An isolated small prehistoric cave painting motif on plain pure white background, '
          'centered with wide empty white margins: a single handmade irregular curved '
          'charcoal twig with four small red and yellow ochre seed pods attached, worn dry '
          'earth pigment, uneven burnt-stick strokes. Flat simple primitive mark, roughly '
          'horizontal, much wider than tall. No shadows, no photography, no realistic '
          'objects, no letters, no numbers, no symbols, no hands, no people, no frog, '
          'no frame, no watermark. Only the charcoal twig and four ochre pods.')


def main():
    parent = Path('artifacts/gathering/wall.png')
    target = parent.with_name('wall-v21.png')
    ancestor, draft = parent.read_bytes(), target.read_bytes()
    assert hashlib.sha256(ancestor).hexdigest() == ANCESTOR
    w, h, old = read_png(ancestor)
    gw, gh, generated = read_png(draft)
    assert (w, h) == (1254, 1254)
    # Normalized source crop includes the whole generated twig, without white margins.
    source = (int(gw*.08), int(gh*.25), int(gw*.95), int(gh*.84))
    destination = (1000, 895, 180, 60)
    x0, y0, width, height = destination
    result = bytearray(old)
    for dy in range(height):
        for dx in range(width):
            xa = source[0] + dx*(source[2]-source[0])//width
            xb = source[0] + (dx+1)*(source[2]-source[0])//width
            ya = source[1] + dy*(source[3]-source[1])//height
            yb = source[1] + (dy+1)*(source[3]-source[1])//height
            totals = [0, 0, 0]
            for sy in range(ya, yb):
                for sx in range(xa, xb):
                    i = (sy*gw+sx)*3
                    for c in range(3):
                        totals[c] += generated[i+c]
            r, g, b = (v/((xb-xa)*(yb-ya)) for v in totals)
            if min(r,g,b) > 210 or (dx*17+dy*31) % 29 == 0:
                continue
            color = ((43,31,20) if max(r,g,b)-min(r,g,b) < 38 else
                     (153,64,31) if r > 1.7*max(g,1) else (161,109,44))
            i = ((y0+dy)*w+x0+dx)*3
            rock = old[i:i+3]
            if max(rock) < 80:
                continue
            alpha = min(.76, (255-min(r,g,b))/255*.87)
            for c in range(3):
                result[i+c] = min(rock[c], round(rock[c]*(1-alpha)+color[c]*alpha))
    changed = 0
    for y in range(h):
        for x in range(w):
            i = (y*w+x)*3
            different = result[i:i+3] != old[i:i+3]
            if different:
                assert x0 <= x < x0+width and y0 <= y < y0+height
                assert max(old[i:i+3]) >= 80
                changed += 1
    assert changed > 500
    output = png(w, h, result)
    target.write_bytes(output)
    parent.write_bytes(output)
    preview = jpeg(512,512,resize(w,h,result),quality=52)
    assert len(preview) <= 100000
    Path('dist/gathering/21.jpg').write_bytes(preview)
    review = dict(ancestorSha256=ANCESTOR, wallSha256=hashlib.sha256(output).hexdigest(),
                  wallSize=[w,h], wallFormat='PNG', wallMode='RGB',
                  generatedDraftSha256=hashlib.sha256(draft).hexdigest(), generatedDraftRetained=False,
                  sourceRectangle=list(source), additionRectangle=list(destination),
                  changedPixels=changed, unchangedPixels=w*h-changed,
                  allPixelsOutsideAdditionUnchanged=True, deepCracksProtected=True,
                  previewSize=[512,512],previewFormat='JPEG',previewBytes=len(preview),
                  newHands=0,newHandprints=0,imageTool='mcp__image__generate_image',prompt=PROMPT,
                  reviewStatus='requires final visual inspection',
                  unmetVisualRequirements=[
                      'Inherited cave rock has a photographic appearance; preserved as required.',
                      'Inherited hand-like marks are too indistinct to certify five digits; no new hands added.'])
    Path('gathering/wall-review-21.json').write_text(json.dumps(review,indent=2)+'\n')
    print(json.dumps(review,indent=2))


if __name__ == '__main__':
    main()
