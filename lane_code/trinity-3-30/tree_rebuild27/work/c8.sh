cd /scratch/jjyeung/orch_n30/tree_rebuild10_w/w27fix && /scratch/jjyeung/envs/p1cpu/bin/python -I -B - <<'PY'
import sys,json,re,collections
sys.path.insert(0,'n_go/b')
import z
from pathlib import Path
cands=['i_bb09a77d','db3954b2','d9c35d0a','probe37845077','i_1be16f28']
tops=collections.Counter(); hits=collections.defaultdict(set)
def walk(v,f):
    if isinstance(v,dict):
        for k,x in v.items(): walk(k,f); walk(x,f)
    elif isinstance(v,list):
        for x in v: walk(x,f)
    elif isinstance(v,str):
        for c in cands:
            if c in v: hits[c].add(f+': '+v[:160])
        m=re.match(r'^(?:/project/community/jjyeung/okh7/)?([A-Za-z0-9_.-]+)/',v)
        if '/' in v and len(v)<400 and m: tops[(f,m.group(1))]+=1
        if v.startswith('/project') or v.startswith('/scratch'): tops[(f,'ABS '+'/'.join(v.split('/')[:6]))]+=1
for p in sorted(Path('n_go/k').glob('*.json')):
    try: d=z.load(p)
    except Exception as e: print('ERR',p,e); continue
    walk(d,p.name)
for (f,t),n in sorted(tops.items()): print(f,t,n)
print('HITS',{c:sorted(s)[:3] for c,s in hits.items()})
PY
