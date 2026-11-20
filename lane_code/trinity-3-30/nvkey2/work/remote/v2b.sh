K=/scratch/jjyeung/orch_n30/nvkey1/work; cd $K || exit 1; P=/scratch/jjyeung/envs/p1cpu/bin/python
$P -B - <<'PY'
import json, gzip, os, collections
d = json.load(gzip.open('v2/noprop/caps/arkitscenes__41048124.json.gz'))
print('rows[0]', json.dumps(d['rows'][0])[:800])
print('names', json.dumps(d['names'])[:1200])
it = d['items']; print('items type', type(it).__name__, len(it))
x = it[0] if isinstance(it, list) else it[list(it)[0]]
print('item0', json.dumps(x)[:1500])
print('arms', d.get('arms_built'))
PY
