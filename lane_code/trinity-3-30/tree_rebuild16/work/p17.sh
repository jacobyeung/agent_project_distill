K=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/out/kit_qd; grep -n "'dr'\|/dr\|\"dr\"\|discovery\|fresh" $K/b/z.py $K/b/a.py $K/b/ep.py $K/b/rg.py | head -30 | cut -c1-300
nice -n 10 python3 -B -I -s - $K <<'PY'
import sys,base64,json;from pathlib import Path
k=Path(sys.argv[1]);s=base64.b64decode(json.load(open(k/'k/j.json'))['payload']).decode()
lines=s.split('\n');print(len(lines))
for i,l in enumerate(lines):
    if 'k/0.json' in l or '<<' in l or 'a.py' in l or 'dr' in l.split() or 'Q_MODE' in l or 'discover' in l: print(i,l[:220])
PY
