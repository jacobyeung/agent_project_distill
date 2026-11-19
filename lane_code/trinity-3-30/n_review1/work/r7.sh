W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; K=$W/w24/out/kit_n_go
python3 - <<'P'
import json,base64,hashlib
v=json.load(open('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/out/kit_n_go/k/l.json'))
d=json.loads(base64.b64decode(v['payload'])) if 'payload' in v else v
print(type(d).__name__, list(d)[:10] if isinstance(d,dict) else len(d))
s=json.dumps(d)
for h in ['4e8e6c04','c09bb5ca','b32359ce','0b95850a','210b2534','5083243c','1d6eeb28','30612832','1e7b491b']:
    i=s.find(h); print(h, s.count(h), s[max(0,i-300):i+200] if i>=0 else '')
P
ls -la $W/work/k1check; head -c 3000 $W/work/k1check/K1R0_CHECK.json; echo
ls /scratch/jjyeung/n30_mirror/ 2>&1 | head; ls -la /scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/ 2>&1
