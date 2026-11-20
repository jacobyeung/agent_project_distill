K=/scratch/jjyeung/orch_n30/nvkey1/work; cd $K || exit 1; P=/scratch/jjyeung/envs/p1cpu/bin/python
date -u +%T; cat meter/METER.json; wc -l out/5*.jsonl 2>/dev/null; tail -2 runner.log; ls faults
$P -B - <<'PY'
import json
d = json.load(open('scores/C1_C1_all24.json'))
for k, v in d.items():
    if 'astra' not in k and 'argon' not in k: continue
    print(k, json.dumps({x: v[x] for x in v if x.startswith(('point_>=1%_', 'presence_>=1%_', 'presence_absent_'))}))
PY
