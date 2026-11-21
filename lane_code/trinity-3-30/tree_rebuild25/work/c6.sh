W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; cd $W/w24z11b; python3 - <<'PY'
import json
s=open('/scratch/jjyeung/orch_n30/tree_rebuild10_w/work/arm_0216Z.log').read()
i=s.find('{'); d=json.loads(s[i:s.rfind('}')+1])
def walk(o,p=''):
  if isinstance(o,dict):
    for k,v in o.items(): walk(v,p+'.'+k)
  elif isinstance(o,list) and len(o)<12 and all(not isinstance(x,(dict,list)) for x in o): print(p,o)
  elif isinstance(o,list):
    for j,x in enumerate(o[:20]): walk(x,p+'[%d]'%j)
  else: print(p,str(o)[:200])
walk(d)
PY
