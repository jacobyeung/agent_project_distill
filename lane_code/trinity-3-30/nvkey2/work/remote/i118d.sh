echo "== $(hostname -s) $(date -u +%T)"
cd /scratch/jjyeung/orch_n30/sb_alias2
/scratch/jjyeung/envs/p1cpu/bin/python - <<'PY'
import json, hashlib, os
scan = json.load(open('work/CANDIDATE_SCENES_FINAL.json')); krec = json.load(open('work/K1_RECOVERY.json'))
pins = dict(scan['list_pins']); pins['4d4736cf'] = krec['recovered']
print(json.dumps(pins, indent=0)[:3000])
for k, p in pins.items():
    path = p['path']; raw = open(path, 'rb').read(); print('==', k, path, len(raw), hashlib.sha256(raw).hexdigest()[:16])
    try:
        d = json.loads(raw)
        if isinstance(d, dict):
            for kk, v in d.items():
                ex = v[:3] if isinstance(v, list) else (list(v.items())[:2] if isinstance(v, dict) else v)
                print('  ', kk, type(v).__name__, len(v) if hasattr(v, '__len__') else '', str(ex)[:300])
        else: print('  list', len(d), str(d[:3])[:300])
    except Exception as e: print('  not json', raw[:300])
prior = json.load(open('/scratch/jjyeung/orch_n30/tree_rebuild10_w/proofs/rooms/RESULT.json')) if os.path.exists('/scratch/jjyeung/orch_n30/tree_rebuild10_w/proofs/rooms/RESULT.json') else None
print('prior authority', json.dumps(prior['audit']['authority'] if prior else None)[:1500])
PY
