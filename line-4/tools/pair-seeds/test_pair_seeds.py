"""In-memory RGB/RGBA PNG vectors; no picture fixtures are saved."""
import contextlib
import io
import struct
import unittest
from unittest.mock import patch
import zlib
import pair_seeds as ps


def png_vector(ch, filters):
    width=5
    rows=[bytes((x*67+y*41+11)%256 for x in range(width*ch)) for y in range(len(filters))]
    raw=bytearray(); prev=bytes(width*ch)
    for row,ft in zip(rows,filters):
        raw.append(ft)
        for i,value in enumerate(row):
            a=row[i-ch] if i>=ch else 0; b=prev[i]; c=prev[i-ch] if i>=ch else 0
            if ft==0: pred=0
            elif ft==1: pred=a
            elif ft==2: pred=b
            elif ft==3: pred=(a+b)//2
            else:
                v=a+b-c; distances=[abs(v-p) for p in (a,b,c)]
                pred=(a,b,c)[distances.index(min(distances))]
            raw.append((value-pred)%256)
        prev=row
    def chunk(kind,data):
        return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
    data=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',width,len(rows),8,2 if ch==3 else 6,0,0,0))
    return data+chunk(b'IDAT',zlib.compress(raw))+chunk(b'IEND',b''),rows


class PNGTests(unittest.TestCase):
    def test_all_filters_both_pixel_layouts(self):
        for ch in (3,4):
            for filters in ([0,1,2,3,4], [4,4,4,4,4]):
                data,rows=png_vector(ch,filters)
                w,h,c,decoded=ps.decode_png(data)
                self.assertEqual((w,h,c),(5,5,ch))
                self.assertEqual(decoded,rows)

    def test_corrupt_truncated_and_trailing_data(self):
        data,_=png_vector(3,[4,4]); bad=bytearray(data); bad[30]^=1
        for value in (data[:-1],bytes(bad),data+b'x',b'not PNG',png_vector(3,[6])[0]):
            with self.assertRaises(ValueError): ps.decode_png(value)

    def test_pixel_count_not_rows_or_channels(self):
        before=[bytes([0]*12),bytes([0]*12)]
        after=[bytes([1,1,1,0,0,0,2,0,0,3,3,3]),bytes([0]*12)]
        self.assertEqual(ps.changed_pixels(before,after,3),3)
        self.assertEqual(ps.changed_pixels(before,before,3),0)
        self.assertEqual(ps.changed_pixels([b'1234'],[b'1235'],4),1)

    def test_main_diagnostic_matches_independent_count(self):
        for ch in (3,4):
            rows=[bytearray([120]*(300*ch)) for _ in range(300)]
            before=[bytes(r) for r in rows]
            with patch.object(ps,'read_png',return_value=(300,300,ch,rows)),patch.object(ps,'write_png') as writer:
                with contextlib.redirect_stdout(io.StringIO()) as out: ps.main('input','output')
            expected=sum(tuple(a[i:i+ch])!=tuple(b[i:i+ch]) for a,b in zip(before,rows) for i in range(0,len(a),ch))
            self.assertGreater(expected,300)
            self.assertIn('changed_pixels='+str(expected),out.getvalue())
            self.assertEqual(writer.call_count,1)
            if ch==4:
                self.assertTrue(all(row[i]==120 for row in rows for i in range(3,len(row),4)))


if __name__=='__main__': unittest.main()
