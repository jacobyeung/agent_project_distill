/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B - <<'PY'
import json
d=json.load(open('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w23/work/build23b/CAPACITY.json'))
def walk(x,p=''):
    if isinstance(x,dict):
        for k,v in x.items(): walk(v,p+'.'+k)
    elif isinstance(x,list) and len(x)<=8 and all(isinstance(i,(int,float)) for i in x) and 'loss' in p.lower(): print(p,x)
    elif isinstance(x,(str,int,float,bool)) and (p.endswith('status') or 'first' in p.lower() or 'finite' in p.lower() or p.lower().endswith('loss')): print(p,x)
walk(d)
PY
