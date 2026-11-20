W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; cd $W; ls inputs/p_configs; for f in inputs/p_configs/*; do echo "== $f"; nice -n 10 python3 -c "
import json,sys
d=json.load(open('$f'))
def walk(x,p=''):
    if isinstance(x,dict):
        for k,v in x.items():
            if k in ('max_pixels','min_pixels','frame_layout','frame_markers','frame_count','b7_inputs'): print(p+'/'+k, json.dumps(v)[:200])
            walk(v,p+'/'+k)
    elif isinstance(x,list):
        for i,v in enumerate(x[:50]): walk(v,p+'/%d'%i)
print('top keys',sorted(d)[:80] if isinstance(d,dict) else type(d)); walk(d)
" 2>&1 | head -30; done
ls w24j/work/build24m4j | head -40
