K=/scratch/jjyeung/orch_n30/k1_ops3/work/partb/build7
cd $K; cat packet/PACKAGE.json packet/UPLOAD.json inputs/depth_heads.json INPUTS_PLAN.json; echo; tar tvf inputs/model.tar
echo "== grep CONFIG"; python3 - <<'PY'
import json,re
c=json.load(open('packet/CONFIG.json'))
def walk(o,p=''):
    if isinstance(o,dict):
        for k,v in o.items(): walk(v,p+'.'+k)
    elif isinstance(o,list):
        if len(o)>20: print(p,'list',len(o)); return
        for i,v in enumerate(o): walk(v,p+'[%d]'%i)
    else:
        s=str(o)
        if len(s)<400: print(p,'=',s)
        else: print(p,'str',len(s))
print(list(c.keys()))
walk({k:v for k,v in c.items()})
PY
echo "== REPORT6"; cat REPORT6.txt | head -120
echo "== BRIEF6"; cat BRIEF6.md BRIEF6B.md
