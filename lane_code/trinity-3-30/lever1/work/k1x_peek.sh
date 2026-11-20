cd /scratch/jjyeung/orch_n30/lever1_c/r2/out; ls -la; /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B - <<'PY'
import json
d=json.load(open('K1X.json'))
print(list(d.keys()))
for k,v in d.items():
    print(k, type(v).__name__, (len(v) if hasattr(v,'__len__') else v) if not isinstance(v,(int,float,str)) else v)
rows=d.get('rows') or d.get('per_row') or []
if rows: print(json.dumps(rows[0])[:1500])
PY
