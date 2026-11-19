set -u
R=/scratch/jjyeung/orch_n30; W=$R/tree_rebuild10_w
cd $R/sb_fullinv
P=/scratch/jjyeung/envs/p1cpu/bin/python
$P -B - <<'PY'
import json
d=json.load(open('out/FULL_INVENTORY.json'))
def walk(o,p='',depth=0):
    if depth>3: return
    if isinstance(o,dict):
        for k,v in o.items():
            q=p+'/'+k
            if isinstance(v,(dict,list)): print(q, type(v).__name__, len(v)); walk(v,q,depth+1)
            else:
                s=str(v)
                if any(t in q.lower() for t in ('frame','archive','bundle','byte','stage','map','plan','upstream','png','root')): print(q,'=',s[:160])
    elif isinstance(o,list) and o and depth<2:
        walk(o[0],p+'[0]',depth+1)
walk(d)
PY
echo "== frames dir"; ls -la work/frames | head -30
echo "== w24 work tail"; ls $W/w24/work | tail -15
echo "== w22 out"; ls $W/w22/out | head -60
