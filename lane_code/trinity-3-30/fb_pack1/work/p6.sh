W=/scratch/jjyeung/orch_n30/tree_rebuild10_w
head -5 $W/ext/pwrap/LISTING_k_arm_runs.txt; ls $W/ext/pwrap
/scratch/jjyeung/envs/p1cpu/bin/python -B - <<'PY'
import json
d=json.load(open('/scratch/jjyeung/orch_n30/tree_rebuild10_w/ext/pwrap/k/0.json'))
for k in ['f3','f4','f6','f7','f9','f14','f5','f8','f4_manifest','f14_manifest','f3_manifest','f3_parts','bundle_parts']:
    v=d.get(k); print('##',k, type(v).__name__, json.dumps(v)[:500])
PY
