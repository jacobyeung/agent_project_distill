<!-- recovered by seal_plan: transcript=71f94277 line=18013 utc=2026-11-13T07:54:11.514Z kind=commands original_path=(bash command)  -->
cd /scratch/jjyeung/orch_cd/leg_s1_canary/out; /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B -c '
import json
d=json.load(open("DELIVERY.json"))
def show(x,ind=0,maxd=2):
    if isinstance(x,dict):
        for k,v in x.items():
            if isinstance(v,(dict,list)) and ind<maxd:
                print(" "*ind+str(k)+":"); show(v,ind+2,maxd)
            else:
                print(" "*ind+str(k)+": "+str(v)[:230])
    elif isinstance(x,list):
        for v in x[:12]: print(" "*ind+"- "+str(v)[:230])
show(d)
' | head -n 70; sha256sum CANARY_BUNDLE_4d573f215a7956c8.tar | cut -c1-64; tar tf CANARY_BUNDLE_4d573f215a7956c8.tar | head -n 30