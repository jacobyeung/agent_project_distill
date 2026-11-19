T=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/tree_r1/student_pilot
grep -n "SLICE_CELLS\|camera_wording\|coverage_units\|recovery" $T/r1_population.py | head -20
/scratch/jjyeung/envs/p1cpu/bin/python -B - <<'PY'
import json
c=json.load(open('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/out/N_LAUNCH_CONFIG.json'))
s=json.dumps(c)
import re
for k in ['routing','rows_per_step','cells','per_step','camera','batch']:
    for m in list(re.finditer(k,s))[:3]: print(k,'::',s[max(0,m.start()-150):m.start()+250])
PY
