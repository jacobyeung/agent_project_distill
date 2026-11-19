/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B - <<'PY'
import json,math
d=json.load(open('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w23/work/build23b/CAPACITY.json'))
out=[]
def walk(x,p=''):
    if isinstance(x,dict):
        for k,v in x.items(): walk(v,p+'.'+str(k))
    elif isinstance(x,list):
        for i,v in enumerate(x): walk(v,p+'[%d]'%i)
    elif isinstance(x,float) and ('loss' in p.lower()): out.append((p,x))
walk(d)
print(len(out),'loss floats; finite',all(math.isfinite(v) for _,v in out))
for p,v in out[:10]: print(p,v)
PY
