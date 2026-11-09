"""Print each paragraph of the text storages that contain a substring, with its list level and paragraph style id.

Usage: python3 levels.py <unzipped Index dir> <substring>
"""
import glob, os, sys
from iwa import fields, iwa, objs, uvar

def runs(fs, n):
    return [dict((a, c) for a, _, c in fields(x)) for fn, w, v in fs if fn == n for _, _, x in fields(v)]

def at(rs, pos, key):
    val = None
    for e in rs:
        if e.get(1, 0) <= pos:
            val = e.get(key)
    return val

if __name__ == '__main__':
    for f in glob.glob(sys.argv[1] + '/Slide-*.iwa'):
        for i, t, b in objs(iwa(open(f, 'rb').read())):
            fs = fields(b)
            txt = [v for fn, w, v in fs if fn == 3]
            if t != 2001 or not txt or sys.argv[2].encode() not in txt[0]:
                continue
            print('==', os.path.basename(f), 'obj', i)
            lv, ps, pos = runs(fs, 6), runs(fs, 5), 0
            # ponytail: offsets are code points; Keynote counts UTF-16 units, so emoji etc. shift later lines
            for p in txt[0].decode().split('\n'):
                st = at(ps, pos, 2)
                print(f'  L{at(lv, pos, 2)} style {uvar(st, 1)[0] if st else "-"}: {p}')
                pos += len(p) + 1
