F=/scratch/jjyeung/orch_n30/fb_pack; /scratch/jjyeung/envs/p1cpu/bin/python -c "
import json;d=json.load(open('$F/pointrec/work/k1_overlap.json'))
def show(x,p=''):
  if isinstance(x,dict):
    for k,v in x.items():
      if isinstance(v,(dict,list)) and len(json.dumps(v))>300: print(p+k,':',type(v).__name__,len(v)); show(v,p+'  ') if isinstance(v,dict) else None
      else: print(p+k,':',json.dumps(v)[:300])
show(d)"
