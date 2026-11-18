<!-- recovered by seal_plan: transcript=71f94277 line=31174 utc=2026-11-14T11:37:07.591Z kind=commands original_path=(bash command)  -->
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B - <<'EOF'
import json
D='/scratch/jjyeung/orch_cd/evalx/work/milestone/reports/step400_e3da9a577'
d=json.load(open(D+'/DECISION.json'))
c=d['cap_statistics']
for arm in ('leg_B2048','parent_B2048','leg_ON16k'):
    a=c[arm]; print(arm, {k:(v.get('count') if isinstance(v,dict) else v) for k,v in a['overall'].items() if k!='items'})
    for t,v in a['per_type'].items():
        b=v.get('bounded_budget_reached') or {}; o=v.get('output_cap') or {}
        print('   ',t, 'budget',b.get('count'),'outcap',o.get('count'),'of',v['items'])
print(json.dumps(d['facing_away'])[:900])
print(json.dumps(d.get('routed_read'))[:600])
print(json.dumps(d.get('requires_orch_ruling'))[:600])
t=d['tables']; print(list(t.keys())[:20])
EOF