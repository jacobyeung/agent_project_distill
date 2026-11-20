W=/scratch/jjyeung/orch_n30/tree_rebuild10_w
grep -ho '"local_path": "[^"]*27126674[^"]*"' $W/w24/out/UPLOADS_*.json $W/w24c/out/UPLOADS_*.json | sort -u | head
python3 - <<'P'
import json,glob
for f in sorted(glob.glob('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/out/UPLOADS_*.json')):
    d=json.load(open(f))
    for r in d.get('files',[]):
        if r.get('sha256','').startswith('27126674'): print(f, r); break
P
