G=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24z11b/a_zffhb1q8/armed/kits/n_go; P=/scratch/jjyeung/envs/p1cpu/bin/python
cat -n $G/b/v.py | cut -c1-220 | head -40; echo ===BUILD; cat $G/BUILD.json | cut -c1-900; echo; grep -n 'b/a.py' $G/SHA256SUMS.txt
grep -n 'def seal' -A12 $G/b/z.py | cut -c1-200
$P -I -s -B - "$G" <<'PY'
import sys,json;sys.path.insert(0,sys.argv[1]+'/b');from z import load
from pathlib import Path
G=Path(sys.argv[1])
for n in ('k/p.json','k/h.json','k/r.json'):
    d=load(G/n); s=json.dumps(d)
    print(n, 'kit_sha256' in s, [k for k in (d.keys() if isinstance(d,dict) else [])][:30])
    if isinstance(d,dict) and 'kit_sha256' in d: print('  kit_sha256',d['kit_sha256'])
PY
grep -rn 'kit_sha256' $G/b/*.py | cut -c1-200 | head
