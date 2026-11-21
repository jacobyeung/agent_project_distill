cd /scratch/jjyeung/orch_n30/tree_rebuild10_w/w27fix && /scratch/jjyeung/envs/p1cpu/bin/python -I -B - <<'PY'
import sys,re,collections
sys.path.insert(0,'n_go/b')
import z
from pathlib import Path
cands=['i_bb09a77d','db3954b2','d9c35d0a','probe37845077','i_1be16f28']
skip=('student_pilot','tests','generator','launch_','scripts','headcall','trace_format','tools','rk','verifykit','evalpath','hrp','ofs','configs','docs','step0_runtime_v1','vendor','development','k/','u/')
out=collections.defaultdict(set)
def walk(v,f,path):
    if isinstance(v,dict):
        for k,x in v.items(): walk(x,f,path+'.'+str(k))
    elif isinstance(v,list):
        for i,x in enumerate(v): walk(x,f,path+'[]')
    elif isinstance(v,str):
        if any(c in v for c in cands): out['HIT'].add(f+path[:60]+' = '+v[:160])
        if '/' in v and len(v)<300 and not v.startswith('/project') and not v.startswith(skip) and not re.match(r'^[a-z_0-9]+/[a-z_0-9/]+\.py$',v):
            out[f].add(path[:50]+' = '+v[:140])
for p in sorted(Path('n_go/k').glob('*.json')):
    if p.name in ('7.json','c0.json'): continue
    try: d=z.load(p)
    except Exception as e: continue
    walk(d,p.name,'')
for f,s in out.items():
    print('==',f,len(s))
    for x in sorted(s)[:14]: print('  ',x)
PY
