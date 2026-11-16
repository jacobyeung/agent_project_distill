<!-- recovered by seal_plan: transcript=71f94277 line=31048 utc=2026-11-14T11:18:38.887Z kind=commands original_path=(bash command)  -->
F=/scratch/jjyeung/orch_cd/evalx/out/NATIVE_PILOT_169501_FAILURE_MEASUREMENTS_S23.json; wc -c $F; /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B - <<'EOF'
import json
d=json.load(open('/scratch/jjyeung/orch_cd/evalx/out/NATIVE_PILOT_169501_FAILURE_MEASUREMENTS_S23.json'))
def show(o,ind=0,maxd=4):
    if isinstance(o,dict):
        for k,v in o.items():
            if isinstance(v,(dict,list)) and ind<maxd:
                print(' '*ind+str(k)+':'); show(v,ind+2,maxd)
            else:
                print(' '*ind+f'{k}: {str(v)[:400]}')
    elif isinstance(o,list):
        for i,v in enumerate(o[:6]):
            if isinstance(v,(dict,list)) and ind<maxd:
                print(' '*ind+f'[{i}]'); show(v,ind+2,maxd)
            else: print(' '*ind+f'[{i}] {str(v)[:400]}')
        if len(o)>6: print(' '*ind+f'... {len(o)} items')
show(d)
EOF