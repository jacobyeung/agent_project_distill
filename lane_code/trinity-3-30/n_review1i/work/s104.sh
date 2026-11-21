A=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24z11b/a_zffhb1q8; P=/scratch/jjyeung/envs/p1cpu/bin/python
date -u +%TZ
cd /tmp && nice -n 10 $P -I -s -B - <<'PY'
import json,base64,hashlib
A='/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24z11b/a_zffhb1q8'
def dec(p):
    v=json.load(open(p))
    if isinstance(v,dict) and 'payload' in v:
        r=base64.b64decode(v['payload']); return json.loads(r), hashlib.sha256(r).hexdigest()
    return v, None
def walk(x,y,p=''):
    if isinstance(x,dict) and isinstance(y,dict):
        for k in sorted(set(x)|set(y)): walk(x.get(k,'<absent>'),y.get(k,'<absent>'),p+'/'+str(k))
    elif isinstance(x,list) and isinstance(y,list) and len(x)==len(y):
        for i,(u,v) in enumerate(zip(x,y)): walk(u,v,p+'['+str(i)+']')
    elif isinstance(x,list) and isinstance(y,list):
        sx=[json.dumps(e,sort_keys=True) for e in x]; sy=[json.dumps(e,sort_keys=True) for e in y]
        print('  LIST',p,len(x),'->',len(y),'removed',[s[:300] for s in sx if s not in sy],'added',[s[:300] for s in sy if s not in sx])
    elif x!=y: print('  DIFF',p,'|',json.dumps(x)[:300],'->',json.dumps(y)[:300])
for k,src in (('q','kit_q'),('n','kit_n'),('n_go','kit_n_go')):
    print('########',k)
    for f in ('k/h.json','k/p.json','k/r.json','BUILD.json'):
        x,hx=dec(A+'/sources/'+src+'/'+f); y,hy=dec(A+'/armed/kits/'+k+'/'+f); print('##',f,'payload',hx,'->',hy); walk(x,y)
PY
