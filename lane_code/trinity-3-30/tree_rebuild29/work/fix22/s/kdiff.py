"""Leaf diff of decoded capsules between two kits: python -I kdiff.py KIT_A KIT_B"""
import json,base64,sys
from pathlib import Path
def load(p):
    v=json.loads(Path(p).read_bytes())
    return json.loads(base64.b64decode(v['payload'])) if isinstance(v,dict) and v.get('encoding')=='base64-json' else v
def walk(x,p=''):
    if isinstance(x,dict):
        for k,v in x.items(): yield from walk(v,p+'/'+k)
    elif isinstance(x,list):
        for i,v in enumerate(x): yield from walk(v,p+f'[{i}]')
    else: yield p,x
a,b=Path(sys.argv[1]),Path(sys.argv[2])
for f in sorted(set(str(p.relative_to(a)) for p in a.rglob('*.json'))|set(str(p.relative_to(b)) for p in b.rglob('*.json'))):
    da=dict(walk(load(a/f))) if (a/f).exists() else {}; db=dict(walk(load(b/f))) if (b/f).exists() else {}
    d=[k for k in sorted(set(da)|set(db)) if da.get(k)!=db.get(k)]
    if d: print(f, len(d), 'leaves:', '; '.join(f'{k} {str(da.get(k))[:16]}->{str(db.get(k))[:16]}' for k in d[:12]))
