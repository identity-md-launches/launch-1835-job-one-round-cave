"""Transfer only generated earth pigment; preserve all other ancestor pixels."""
import hashlib
import json
from pathlib import Path
import subprocess
from image_bytes import read_png, png

ANCESTOR = 'eb2ed3b198086de5e1810d97d5fde21abd8525688073f02f4d0bd7676330cb1d'
GENERATED = '638c6cc9a20394ef71a2b34a6ad7b14431d5650bf5547b74e7cd48656480bc8c'
PROMPT = ('Use case: illustration-story. Pigment insert to be composited onto an '
          'existing prehistoric cave wall. A single small irregular red ochre pebble '
          'nestled inside an uneven charcoal loop, like a stone kept safe inside a '
          'cord ring. Centered on plain pale warm stone, object fills central half. '
          'Very simple flat Lascaux style burnt stick and thumb mark with worn pigment '
          'gaps, rough earth pigments red ochre and charcoal only. No shadows, '
          'photorealism, 3D, hands, letters, numbers, symbols, writing, signature, '
          'logos, frame, border or watermark. Keep all outer corners plain unmarked '
          'pale stone.')


def main():
    wall = Path('artifacts/line-1/wall.png')
    named = Path('artifacts/line-1/wall-v21.png')
    old, draft = wall.read_bytes(), named.read_bytes()
    assert hashlib.sha256(old).hexdigest() == ANCESTOR
    assert hashlib.sha256(draft).hexdigest() == GENERATED
    w, h, original = read_png(old)
    gw, gh, generated = read_png(draft)
    assert (w, h) == (1254, 1254)
    assert (gw, gh) == (1536, 1024)
    result = bytearray(original)
    # Isolated generated ring/pebble, reduced to a small unoccupied rock patch.
    # No generated background replaces the cave's surface.
    for dy in range(80):
        for dx in range(90):
            colors = []
            for sy in range(130 + dy*9, 130 + (dy+1)*9):
                for sx in range(300 + dx*10, 300 + (dx+1)*10):
                    index = (sy*gw+sx)*3
                    r, g, b = generated[index:index+3]
                    if (r < 100 and g < 90 and b < 75) or (g < .60*r and g < 130):
                        colors.append((r, g, b))
            if not colors:
                continue
            alpha = .85*len(colors)/90
            index = ((200+dy)*w+810+dx)*3
            for c in range(3):
                pigment = sum(color[c] for color in colors)/len(colors)
                result[index+c] = min(original[index+c], round(
                    original[index+c]*(1-alpha) + pigment*alpha))
    changed = [(i//3 % w, i//3//w) for i in range(0, len(original), 3)
               if original[i:i+3] != result[i:i+3]]
    assert 500 < len(changed) < 7200
    assert all(810 <= x < 900 and 200 <= y < 280 for x, y in changed)
    final = png(w, h, result)
    wall.write_bytes(final)
    named.write_bytes(final)
    thumb = subprocess.run([
        '/opt/tools/bin/ffmpeg', '-hide_banner', '-loglevel', 'error',
        '-i', str(wall), '-vf', 'scale=512:512:flags=area', '-frames:v', '1',
        '-q:v', '4', '-f', 'image2pipe', '-vcodec', 'mjpeg', '-'],
        check=True, capture_output=True, env={}).stdout
    assert thumb[:2] == b'\xff\xd8' and thumb[-2:] == b'\xff\xd9'
    assert len(thumb) < 100000
    thumb_path = Path('dist/line-1/40.jpg')
    assert not thumb_path.exists()
    thumb_path.write_bytes(thumb)
    digest = hashlib.sha256(final).hexdigest()
    record = {'name': 'The Kept Stone',
        'image': 'https://api.imd.fun/artifacts/' + digest,
        'attributes': [{'trait_type': k, 'value': v} for k, v in (
            ('Cave', 'Water'), ('Wall', 'Line 1'), ('Number', 40),
            ('Left behind', 'Pinned read batch'),
            ('Meaning', 'An ochre stone inside a charcoal loop marks evidence kept against a separate memory.'),
            ('One thing', 'portable live Ethereum JSON-RPC snapshots'))]}
    record_path = Path('dist/line-1/40.json')
    assert not record_path.exists()
    record_path.write_text(json.dumps(record, indent=2) + '\n')
    review = {
        'record': 40, 'ancestor_sha256': ANCESTOR,
        'wall': {'paths': [str(wall), str(named)], 'format': 'PNG',
                 'dimensions': [w, h], 'mode': 'RGB', 'sha256': digest,
                 'bytes': len(final)},
        'thumbnail': {'path': str(thumb_path), 'format': 'JPEG',
                      'dimensions': [512, 512], 'bytes': len(thumb)},
        'generation': {'tool': 'mcp__image__generate_image', 'prompt': PROMPT,
                       'draft_sha256': GENERATED, 'draft_retained': False},
        'changed_pixels': len(changed), 'unchanged_pixels': w*h-len(changed),
        'changed_bounds_inclusive': [min(x for x,y in changed), min(y for x,y in changed),
                                     max(x for x,y in changed), max(y for x,y in changed)],
        'ancestor_pixels_outside_patch_identical': True,
        'visual_review': 'Pending final inspection', 'unmet_visual_requirements': []}
    Path('line-1/wall-review-40.json').write_text(json.dumps(review, indent=2) + '\n')
    print(json.dumps(review, indent=2))


if __name__ == '__main__':
    main()
