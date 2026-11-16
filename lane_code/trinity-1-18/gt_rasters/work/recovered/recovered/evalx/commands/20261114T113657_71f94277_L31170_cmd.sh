<!-- recovered by seal_plan: transcript=71f94277 line=31170 utc=2026-11-14T11:36:57.882Z kind=commands original_path=(bash command)  -->
D=/scratch/jjyeung/orch_cd/evalx/work/milestone/reports/step400_e3da9a577; /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B - <<'EOF'
import json
D='/scratch/jjyeung/orch_cd/evalx/work/milestone/reports/step400_e3da9a577'
n=json.load(open(D+'/NONROUTED_BUDGET.json'))
def show(o,ind=0,maxd=3):
    if isinstance(o,dict):
        for k,v in o.items():
            if isinstance(v,(dict,list)) and ind<maxd*2:
                print(' '*ind+str(k)+':'); show(v,ind+2,maxd)
            else: print(' '*ind+f'{k}: {str(v)[:300]}')
    elif isinstance(o,list):
        for i,v in enumerate(o[:14]):
            if isinstance(v,(dict,list)): print(' '*ind+f'[{i}] {json.dumps(v)[:300]}')
            else: print(' '*ind+f'[{i}] {str(v)[:300]}')
show(n)
d=json.load(open(D+'/DECISION.json'))
print('--- R3'); print(json.dumps(d['R3'])[:1500]); print(json.dumps(d['R3_budget_policy'])[:800]); print('--- cap'); print(json.dumps(d['cap_statistics'])[:2500])
EOF