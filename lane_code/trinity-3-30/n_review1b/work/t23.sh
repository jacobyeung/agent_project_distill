F=/scratch/jjyeung/orch_n30/fb_pack/k1point/REMOVE_POINTING_K1_HELDOUT.jsonl; K=/scratch/jjyeung/orch_n30/tree_rebuild10_w/ext/b12/K1SPLIT_R0.json
sha256sum $F $K; wc -l $F; head -2 $F
python3 - <<P
import json,collections
k=json.load(open('$K')); print(type(k), list(k.keys())[:10] if isinstance(k,dict) else len(k))
for kk,v in (k.items() if isinstance(k,dict) else []):
    print(kk, type(v).__name__, (len(v) if hasattr(v,'__len__') else v), str(v)[:150])
rows=[json.loads(l) for l in open('$F')]
print(collections.Counter((r.get('room'),r.get('canonical'),r.get('reason')) for r in rows))
print(len(set(r['row_key'] for r in rows)))
P
