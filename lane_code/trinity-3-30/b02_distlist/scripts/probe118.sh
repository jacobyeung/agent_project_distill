cd /scratch/jjyeung/orch_cd 2>/dev/null || { echo NO_ORCH_CD; ls /scratch/jjyeung | head; exit 0; }
echo "== devs1_masks/out"; ls -la devs1_masks/out | head -40
echo "== devs1_direct/out"; ls -la devs1_direct/out | head -40
echo "== devs1_mask_run"; ls -la /scratch/jjyeung/devs1_mask_run | head -40
python3 - <<'PY'
import json, os, hashlib
m='devs1_masks/out/MANIFEST.json'
if os.path.exists(m):
    s=open(m).read(); print('MANIFEST bytes',len(s)); d=json.loads(s)
    def sk(o,dep=0,pre=''):
        if dep>2: return
        if isinstance(o,dict):
            for k,v in list(o.items())[:30]:
                print(pre+k, type(v).__name__, (json.dumps(v)[:160] if not isinstance(v,(dict,list)) else len(v)))
                sk(v,dep+1,pre+'  ')
        elif isinstance(o,list) and o: sk(o[0],dep+1,pre+'[0] ')
    sk(d)
for p in ['devs1_masks/out/ITEMS.jsonl','devs1_direct/out/ITEMS.jsonl']:
    if os.path.exists(p):
        b=open(p,'rb').read(); print(p,len(b),hashlib.sha256(b).hexdigest())
        rows=[json.loads(l) for l in b.decode().splitlines() if l.strip()]
        from collections import Counter
        print(len(rows), Counter((r.get('question_type'),r.get('stratum')) for r in rows).most_common(40))
        d=[r for r in rows if r.get('question_type')=='object_abs_distance']
        if d: print(json.dumps(d[0])[:1500])
PY
