"""One-time preservation pass for mark 40; refuses a different ancestor."""
import hashlib
import json
from pathlib import Path
from image_bytes import read_png, png, jpeg, resize


def main():
    folder = Path('artifacts/line-4')
    ancestor = (folder/'wall.png').read_bytes()
    draft = (folder/'wall-v21.png').read_bytes()
    ancestor_hash = '0e4ca864e080890bc8d36b94ba85c2fd5c1bf34548bde90c7ae62ef729309cd1'
    if hashlib.sha256(ancestor).hexdigest() != ancestor_hash:
        raise ValueError('requires unmodified record 39 wall')
    w,h,old = read_png(ancestor)
    dw,dh,generated = read_png(draft)
    assert (w,h)==(1254,1254)
    final = bytearray(old); changed=[]
    # Sample only image-generated pigment, not its unrelated stone background.
    # The source motif's ring and pebble are inside this central crop.
    for oy in range(80):
        for ox in range(80):
            sx = int((280+ox*700/80)*dw/1254)
            sy = int((270+oy*700/80)*dh/1254)
            sample=[]
            for dy in range(4):
                for dx in range(4):
                    j=((sy+dy)*dw+sx+dx)*3
                    sample.append(generated[j:j+3])
            r,g,b = [sum(p[c] for p in sample)//len(sample) for c in range(3)]
            charcoal=max(r,g,b)<100
            red=65<r<200 and r>1.65*g and r-g>35
            yellow=125<r<210 and 70<g<155 and b<75 and r>1.3*g
            if not (charcoal or red or yellow): continue
            x,y=1078+ox,710+oy; i=(y*w+x)*3
            original=old[i:i+3]
            if sum(original)<95: continue  # retain deep inherited cracks
            # Warm pigment is translucent on the inherited rough rock.
            color=(37,28,20) if charcoal else (159,69,30) if red else (177,112,33)
            alpha=.65 if charcoal else .60
            new=bytes(round(a*(1-alpha)+c*alpha) for a,c in zip(original,color))
            if new!=original:
                final[i:i+3]=new; changed.append((x,y))
    assert 700<len(changed)<4000
    wall=png(w,h,final)
    preview=jpeg(512,512,resize(w,h,final),52)
    assert len(preview)<100000
    sha=hashlib.sha256(wall).hexdigest()
    for name in ('wall.png','wall-v21.png'): (folder/name).write_bytes(wall)
    Path('dist/line-4/40.jpg').write_bytes(preview)
    meaning='An ochre pebble inside a worn ring marks checking the exact address behind a request.'
    record={'name':'The Address Stone','image':'https://api.imd.fun/artifacts/'+sha,
        'attributes':[{'trait_type':'Cave','value':'Water'},{'trait_type':'Wall','value':'Line 4'},
        {'trait_type':'Number','value':40},{'trait_type':'Left behind','value':'offline EIP-712 address reviewer'},
        {'trait_type':'Meaning','value':meaning},
        {'trait_type':'One thing','value':'offline EIP-712 typed-data digest checking'}]}
    Path('dist/line-4/40.json').write_text(json.dumps(record,indent=2)+'\n')
    review={'wall':{'paths':['artifacts/line-4/wall.png','artifacts/line-4/wall-v21.png'],
        'width':w,'height':h,'format':'PNG','mode':'RGB','bytes':len(wall),'sha256':sha},
        'preview':{'path':'dist/line-4/40.jpg','width':512,'height':512,'format':'JPEG','bytes':len(preview)},
        'ancestorSha256':ancestor_hash,'generatedMotifSha256':hashlib.sha256(draft).hexdigest(),
        'imageTool':'installed mcp image generate_image through imagegen skill',
        'prompt':'A rough charcoal ring enclosing one red ochre pebble with three tiny yellow ochre dots along the inside curve; prehistoric worn stick and thumb pigment on plain tan stone; no text, hands, people, numbers, logos or framing.',
        'compositing':'Extracted generated charcoal and ochre pigment only, scaled onto vacant right-side stone. Preserved every original pixel outside the new pigment and deep original cracks.',
        'changedPixels':len(changed),'unchangedPixels':w*h-len(changed),
        'additionBoundsExclusive':[min(x for x,y in changed),min(y for x,y in changed),max(x for x,y in changed)+1,max(y for x,y in changed)+1],
        'visualReview':'Pending final PNG and decoded JPEG inspection.',
        'unmetVisualRequirements':[],
        'limitations':['Local visual review is not independent certification.','Small mark is subtle in the preview.']}
    Path('line-4/wall-review-40.json').write_text(json.dumps(review,indent=2)+'\n')
    print(json.dumps(review,indent=2))


if __name__=='__main__': main()
