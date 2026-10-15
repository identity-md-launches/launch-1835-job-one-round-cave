#!/usr/bin/env python3
"""Add a restrained two-seed ochre mark to an RGB/RGBA PNG using only stdlib."""
import struct, sys, zlib

def decode_png(b):
    """Decode bounded, noninterlaced 8-bit RGB/RGBA with all five filters."""
    if len(b) > 32_000_000 or b[:8] != b'\x89PNG\r\n\x1a\n':
        raise ValueError('not a supported PNG or file too large')
    p=8; idat=bytearray(); header=None; ended=False; started=False
    while p < len(b):
        if p+12 > len(b): raise ValueError('truncated PNG chunk')
        n=struct.unpack('>I',b[p:p+4])[0]; t=b[p+4:p+8]
        if p+n+12 > len(b): raise ValueError('truncated PNG payload')
        d=b[p+8:p+8+n]; crc=struct.unpack('>I',b[p+8+n:p+12+n])[0]; p+=n+12
        if zlib.crc32(t+d)&0xffffffff != crc: raise ValueError('PNG CRC mismatch')
        if header is None and t != b'IHDR': raise ValueError('IHDR must be first')
        if t==b'IHDR':
            if header is not None or n!=13: raise ValueError('invalid IHDR')
            header=struct.unpack('>IIBBBBB',d); w,h,dep,kind,co,fi,inter=header
            if (dep,co,fi,inter)!=(8,0,0,0) or kind not in (2,6) or not 0<w*h<=16_000_000:
                raise ValueError('only bounded noninterlaced 8-bit RGB/RGBA supported')
        elif t==b'IDAT': idat.extend(d); started=True
        elif t==b'IEND':
            if n or not started or p!=len(b): raise ValueError('invalid PNG end')
            ended=True; break
        elif not t[0]&32: raise ValueError('unsupported critical PNG chunk')
    if not ended: raise ValueError('missing IEND')
    ch=3 if kind==2 else 4; stride=w*ch; expected=(stride+1)*h
    dec=zlib.decompressobj(); raw=dec.decompress(idat,expected+1)
    if len(raw)!=expected or not dec.eof or dec.unused_data or dec.unconsumed_tail:
        raise ValueError('invalid PNG decompressed length or stream')
    rows=[]; prev=bytearray(stride); p=0
    for _ in range(h):
        ft=raw[p]; p+=1; cur=bytearray(raw[p:p+stride]); p+=stride
        if ft not in range(5): raise ValueError('invalid PNG filter')
        for i in range(stride):
            a=cur[i-ch] if i>=ch else 0; u=prev[i]; c=prev[i-ch] if i>=ch else 0
            prediction=0
            if ft==1: prediction=a
            elif ft==2: prediction=u
            elif ft==3: prediction=(a+u)//2
            elif ft==4:
                v=a+u-c; pa,pb,pc=abs(v-a),abs(v-u),abs(v-c)
                prediction=a if pa<=pb and pa<=pc else u if pb<=pc else c
            cur[i]=(cur[i]+prediction)&255
        rows.append(cur); prev=cur
    return w,h,ch,rows

def read_png(path):
    with open(path,'rb') as f: data=f.read(32_000_001)
    return decode_png(data)

def changed_pixels(before, after, ch):
    if len(before)!=len(after) or any(len(a)!=len(b) or len(a)%ch for a,b in zip(before,after)):
        raise ValueError('pixel layouts differ')
    return sum(a[i:i+ch]!=b[i:i+ch] for a,b in zip(before,after) for i in range(0,len(a),ch))

def write_png(path,w,h,ch,rows):
    def c(t,d): return struct.pack('>I',len(d))+t+d+struct.pack('>I',zlib.crc32(t+d)&0xffffffff)
    raw=b''.join(b'\0'+bytes(r) for r in rows); kind=2 if ch==3 else 6
    out=b'\x89PNG\r\n\x1a\n'+c(b'IHDR',struct.pack('>IIBBBBB',w,h,8,kind,0,0,0))+c(b'IDAT',zlib.compress(raw,9))+c(b'IEND',b'')
    open(path,'wb').write(out)
def paint(rows,w,h,ch,cx,cy,rx,ry,col,alpha):
    n=0
    for y in range(max(0,cy-ry-3),min(h,cy+ry+4)):
      for x in range(max(0,cx-rx-3),min(w,cx+rx+4)):
        d=((x-cx)/rx)**2+((y-cy)/ry)**2
        if d<=1:
          a=alpha*(1 if d<.72 else (1-d)/.28); i=x*ch; old=tuple(rows[y][i:i+3]); new=tuple(round(old[k]*(1-a)+col[k]*a) for k in range(3))
          if new!=old: rows[y][i:i+3]=bytes(new); n+=1
    return n
def main(src,dst):
    w,h,ch,rows=read_png(src); before=[bytes(r) for r in rows]; cx,cy=int(w*.165),int(h*.715)
    paint(rows,w,h,ch,cx-25,cy,31,24,(164,91,35),.62); paint(rows,w,h,ch,cx+28,cy-3,27,23,(184,104,38),.62)
    for ox,oy,rx,ry in [(-28,35,42,5),(0,43,45,5),(30,34,34,5)]: paint(rows,w,h,ch,cx+ox,cy+oy,rx,ry,(42,31,20),.52)
    write_png(dst,w,h,ch,rows); print(f'{w}x{h} RGB={ch==3} changed_pixels={changed_pixels(before, rows, ch)}')
if __name__=='__main__':
    if len(sys.argv)!=3: raise SystemExit('usage: pair_seeds.py INPUT.png OUTPUT.png')
    main(sys.argv[1],sys.argv[2])
