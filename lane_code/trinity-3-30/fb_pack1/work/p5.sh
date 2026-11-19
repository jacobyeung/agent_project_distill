W=/scratch/jjyeung/orch_n30/tree_rebuild10_w
sed -n 1,60p $W/ext/pwrap/LISTING_k_arm_runs.txt | cut -c1-220
echo ==; /scratch/jjyeung/envs/p1cpu/bin/python -B - <<'PY'
import json
d=json.load(open('/scratch/jjyeung/orch_n30/tree_rebuild10_w/ext/pwrap/k/0.json'))
s=json.dumps(d)
import re
for h in ['17aa3e9e','7cc01f36','frame_map','frame_plan','k6tk','kr9c','cp4tk_fr']:
    for m in list(re.finditer(h,s))[:3]:
        print(h,'::',s[max(0,m.start()-300):m.start()+200].replace('\n',' '))
print(type(d).__name__, list(d.keys())[:30] if isinstance(d,dict) else len(d))
PY
