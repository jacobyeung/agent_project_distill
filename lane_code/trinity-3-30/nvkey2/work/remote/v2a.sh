K=/scratch/jjyeung/orch_n30/nvkey1/work; cd $K || exit 1; P=/scratch/jjyeung/envs/p1cpu/bin/python
date -u +%T; cat meter/METER.json; wc -l out/4*.jsonl out/5*.jsonl analysis_only/out/5*.jsonl 2>/dev/null | tail -9; tail -2 v6/chain.log
$P -B - <<'PY'
import json, gzip, os, collections
d = json.load(gzip.open('v2/noprop/caps/arkitscenes__41048124.json.gz'))
def show(x, depth=0, key='root'):
    pad = '  ' * depth
    if isinstance(x, dict):
        print(pad + key, 'dict', len(x), list(x)[:12])
        for k in list(x)[:6]:
            if depth < 3: show(x[k], depth + 1, str(k))
    elif isinstance(x, list):
        print(pad + key, 'list', len(x))
        if x and depth < 3: show(x[0], depth + 1, key + '[0]')
    else: print(pad + key, repr(x)[:150])
show(d)
PY
