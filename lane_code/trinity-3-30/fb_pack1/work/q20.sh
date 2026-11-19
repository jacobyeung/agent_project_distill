F=/scratch/jjyeung/orch_n30/fb_pack
/scratch/jjyeung/envs/p1cpu/bin/python -B - <<'PY'
import json
m=json.load(open('/scratch/jjyeung/orch_n30/fb_pack/route/out/ROUTE_MANIFEST.json'))
def sk(o,p='',d=0):
    if d>3: return
    if isinstance(o,dict):
        for k,v in list(o.items())[:14]:
            if isinstance(v,(dict,list)): print(p+'/'+k, type(v).__name__, len(v)); sk(v,p+'/'+k,d+1)
            else: print(p+'/'+k,'=',str(v)[:110])
    elif isinstance(o,list) and o: sk(o[0],p+'[0]',d+1)
sk(m)
c=json.load(open('/scratch/jjyeung/orch_n30/fb_pack/route/out/CONFIG_HANDOFF.json')); print('## HANDOFF keys', list(c.keys()))
PY
ls $F/cam/out/envelopes $F/cam/out/upstream $F/cam/out/coverage; head -c 1200 $F/cam/out/REBIND.json
