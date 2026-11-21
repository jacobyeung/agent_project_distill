import sys,json
K='/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24z12/out/kit_n_go'
sys.path.insert(0,K+'/b')
from z import load
from pathlib import Path
def walk(x,path,out):
    if isinstance(x,dict):
        for k,v in x.items():
            if k in ('weights','device','first_batch','forward'): out.append((path+'/'+k, json.dumps(v)[:150]))
            walk(v,path+'/'+k,out)
    elif isinstance(x,list):
        for i,v in enumerate(x[:50]): walk(v,path+'[%d]'%i,out)
for p in sorted(Path(K+'/k').glob('*.json')):
    try: v=load(p)
    except Exception as e: print(p.name,'ERR',e); continue
    out=[];walk(v,'',out)
    if out: print(p.name,out[:10])
src=open(K+'/b/pl.py').read()
i=src.find('def plan_payload'); print(src[i:i+2500])
