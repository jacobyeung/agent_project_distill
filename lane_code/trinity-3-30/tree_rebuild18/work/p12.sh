date -u +%TZ; nice -n 10 python3 - <<'PY'
import json
m=json.load(open('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/build24m4/hidden/inputs/0c38bc96bb4566c2dc5aa17e1543995954b51401032fad02f0ce67e15f5d898a'))
print('RD',json.dumps(m['pool_selection_counts'].get('ROUTE_direct'))[:1500])
print('defer',json.dumps(m['source_deferrals'])[:1500])
print('policy',json.dumps(m.get('s1_route_policy'))[:1500])
print('inputs',json.dumps(m['inputs'])[:2500])
print('sources',list(m['pool_selection_counts'].keys()))
print('types',json.dumps(m['types'])[:1500])
PY
