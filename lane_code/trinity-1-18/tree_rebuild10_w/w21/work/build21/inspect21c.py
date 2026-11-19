from pathlib import Path
import json,sys,base64
L=Path(__file__).resolve().parents[2];B=L/'work/build21';sys.path[:0]=[str(B),str(L/'work/tree_r1')]
import joblib as J
from launch_r2.build import bad_string
K=B/'kits/q';wh=J.load(K/'b/wh.json')
def walk(v,loc):
    if isinstance(v,dict):
        for k,x in v.items():
            if bad_string(k,wh): hits.append((loc+'/KEY',k))
            walk(x,loc+'/'+k)
    elif isinstance(v,list):
        for i,x in enumerate(v):walk(x,loc+'/'+str(i))
    elif isinstance(v,str) and bad_string(v,wh):hits.append((loc,v[:220]))
for p in sorted((K/'k').glob('*.json')):
    if p.name=='j.json':continue
    hits=[];v=J.load(p);walk(v,'')
    print(p.name, 'type',type(v).__name__,'keys',list(v)[:30] if isinstance(v,dict) else '', 'hits',len(hits))
    if p.name in ('p.json','l.json','s.json'):print(json.dumps(hits,indent=2))
    else:print(json.dumps(hits[:8],indent=2))
spec=J.load(K/'k/p.json')
print('P_FILES',json.dumps(spec['p_files'],indent=2))
print('L_MAP',json.dumps(J.load(K/'k/l.json'),indent=2)[:15000])
