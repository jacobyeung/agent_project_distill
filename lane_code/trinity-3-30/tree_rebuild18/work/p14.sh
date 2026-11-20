date -u +%TZ; nice -n 10 python3 - <<'PY'
import json
m=json.load(open('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/build24m4/hidden/inputs/0c38bc96bb4566c2dc5aa17e1543995954b51401032fad02f0ce67e15f5d898a'))
print('resolved_selection',m['resolved_selection']); print('relocation',m['relocation'])
print('inputs keys',[k for k in m['inputs'] if k!='catalog'])
for k,v in m['inputs'].items():
    if k!='catalog': print(k, json.dumps(v)[:300])
print('source_denominator',m['source_denominator'])
for k,v in m['pool_selection_counts'].items(): print(k,v.get('status'),v.get('reason'),v.get('retained'))
PY
T=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24c/work/tree_r1; grep -n "def refresh" -A30 /scratch/jjyeung/orch_n30/tree_rebuild10_w/w24e/out/kit_qd/b/i.py | head -50
