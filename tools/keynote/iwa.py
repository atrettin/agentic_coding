"""Read-only decoder for Keynote .iwa files (Snappy-framed protobuf, no schema).

Usage: python3 iwa.py <file.iwa> [x]   lists objects (id, type, size); "x" also dumps fields.
Unzip <deck>.key/Index.zip first. Never write .iwa files; edit decks via AppleScript.
Types: 5 slide, 7/2011 shape, 2001 text storage (3 text, 5 para styles, 6 list levels, 8 char styles).
"""
import sys
def uvar(b,i):
    r=s=0
    while True:
        c=b[i];i+=1;r|=(c&0x7f)<<s;s+=7
        if c<0x80:return r,i
def snappy(b):
    n,i=uvar(b,0);o=bytearray()
    while i<len(b):
        t=b[i];i+=1;k=t&3
        if k==0:
            l=t>>2
            if l>=60:
                nb=l-59;l=int.from_bytes(b[i:i+nb],'little');i+=nb
            l+=1;o+=b[i:i+l];i+=l;continue
        if k==1:l=((t>>2)&7)+4;off=((t>>5)<<8)|b[i];i+=1
        elif k==2:l=(t>>2)+1;off=int.from_bytes(b[i:i+2],'little');i+=2
        else:l=(t>>2)+1;off=int.from_bytes(b[i:i+4],'little');i+=4
        for _ in range(l):o.append(o[-off])
    return bytes(o)
def iwa(b):
    i=0;out=b''
    while i<len(b):
        assert b[i]==0;l=int.from_bytes(b[i+1:i+4],'little');out+=snappy(b[i+4:i+4+l]);i+=4+l
    return out
def fields(b):
    i=0;r=[]
    while i<len(b):
        k,i=uvar(b,i);f,w=k>>3,k&7
        if w==0:v,i=uvar(b,i)
        elif w==1:v=b[i:i+8];i+=8
        elif w==5:v=b[i:i+4];i+=4
        elif w==2:l,i=uvar(b,i);v=b[i:i+l];i+=l
        else:raise ValueError
        r.append((f,w,v))
    return r
def objs(d):
    i=0
    while i<len(d):
        l,i=uvar(d,i);info=fields(d[i:i+l]);i+=l
        ident=[v for f,w,v in info if f==1][0]
        for f,w,v in info:
            if f==2:
                mi=fields(v);typ=[x for g,_,x in mi if g==1][0];ln=[x for g,_,x in mi if g==3][0]
                yield ident,typ,d[i:i+ln];i+=ln
def dump(b,ind=0,depth=6):
    try:fs=fields(b)
    except Exception:fs=None
    if fs is None or depth==0:return False
    for f,w,v in fs:
        if w==2:
            try:s=v.decode();printable=s.isprintable() or '\n' in s or ' ' in s
            except: printable=False
            if printable and len(v)>0 and not (len(v)<3 and not s.isalpha()):
                print(' '*ind+f'{f}: {s!r}');continue
            print(' '*ind+f'{f} {{');
            if not dump(v,ind+2,depth-1):print(' '*(ind+2)+v[:40].hex())
            print(' '*ind+'}')
        else:print(' '*ind+f'{f}: {v if w==0 else v.hex()}')
    return True
if __name__=='__main__':
    d=iwa(open(sys.argv[1],'rb').read())
    for ident,typ,body in objs(d):
        print(f'=== obj {ident} type {typ} ({len(body)}B)')
        if len(sys.argv)>2:dump(body,2)
