<!-- recovered by seal_plan: transcript=71f94277 line=21844 utc=2026-11-13T14:24:08.485Z kind=commands original_path=(bash command)  -->
cd /scratch/jjyeung/orch_cd/orchard_cp2/out/canary3_169009; /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B -c '
import json
d=json.load(open("resume_live_20261113T141805Z.json"))
def walk(x,pre="",depth=0):
    if isinstance(x,dict):
        for k,v in x.items():
            if isinstance(v,(dict,list)) and depth<3: walk(v,pre+str(k)+".",depth+1)
            else: print((pre+str(k))[:70],"=",str(v)[:300])
    elif isinstance(x,list):
        for i,v in enumerate(x[:6]):
            if isinstance(v,(dict,list)) and depth<3: walk(v,pre+str(i)+".",depth+1)
            else: print((pre+str(i))[:70],"=",str(v)[:300])
walk(d)
' | head -n 60