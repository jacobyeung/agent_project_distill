<!-- recovered by seal_plan: transcript=71f94277 line=8748 utc=2026-11-12T01:47:23.606Z kind=commands original_path=(bash command)  -->
cd /scratch/jjyeung/orch_cd; sed -n 5,30p leg_s1_tree/events/20261112T0146Z_QUESTION_pool_routing_materialization.md | cut -c1-1500; echo ---- FRAMES_GATE; ls -la dose_pool/out/POOL_S1/ | head -30; python3 - <<'EOF'
import json
p='/scratch/jjyeung/orch_cd/dose_pool/out/POOL_S1/FRAMES_GATE.json'
d=json.load(open(p))
def show(x,depth=0,maxk=14):
    if isinstance(x,dict):
        for i,(k,v) in enumerate(x.items()):
            if i>=maxk: print('  '*depth+'...'); break
            if isinstance(v,(dict,list)):
                print('  '*depth+str(k)+': '+type(v).__name__+' len '+str(len(v)))
                if depth<1: show(v,depth+1,8)
            else: print('  '*depth+str(k)+': '+str(v)[:200])
    elif isinstance(x,list):
        for v in x[:3]: print('  '*depth+str(v)[:300])
show(d)
EOF