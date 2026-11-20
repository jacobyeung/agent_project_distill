K=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/build22/upload/u/27126674a57111585615308cb3e779e169b5693b1c87afafe691ce8e56c2b390
F=/scratch/jjyeung/orch_n30/fb_pack/k1point/REMOVE_POINTING_K1_HELDOUT.jsonl
sha256sum $K
python3 - <<P
import json,collections
k=json.load(open('$K'))
print(type(k).__name__, list(k.keys())[:12] if isinstance(k,dict) else len(k))
for kk,v in (k.items() if isinstance(k,dict) else []):
    print(kk, type(v).__name__, (len(v) if hasattr(v,'__len__') else v), str(v)[:160])
rows=[json.loads(l) for l in open('$F')]
print(collections.Counter((r.get('room'),r.get('reason')) for r in rows), len(set(r['row_key'] for r in rows)))
P
