#!/bin/bash
set -u
W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; B16=$W/w16b/work/build16
nice -n 10 /usr/bin/python3 - <<'PY'
import json
from collections import Counter
C='/scratch/jjyeung/orch_n30/tree_rebuild10_w/w16b/work/build16/proofs/census/'
m=json.load(open(C+'membership.json'))
def sk(d,depth=0,p=''):
    if isinstance(d,dict):
        for k,v in list(d.items())[:14]:
            if isinstance(v,(dict,list)): print(p+str(k)+': '+type(v).__name__+' len %d'%len(v)); sk(v,depth+1,p+'  ') if depth<2 else None
            else: print(p+str(k)+': '+json.dumps(v)[:200])
    elif isinstance(d,list) and d: print(p+'[0]: '+json.dumps(d[0])[:240])
print('== membership.json'); sk(m)
c=json.load(open(C+'CENSUS.json')); print('== CENSUS slices', json.dumps(c.get('slices'))[:2500])
PY
echo "== census16.py grep"; grep -n "units\|recovery\|absolute_distance\|pack\|validate\|s.json\|remove" $B16/census16.py | cut -c1-200 | head -50
echo "== done $(date -u +%FT%TZ)"
