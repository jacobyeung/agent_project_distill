R=/scratch/jjyeung/orch_n30; cd $R/sb_fullinv
/scratch/jjyeung/envs/p1cpu/bin/python -B - <<'PY'
import json
d=json.load(open('out/FULL_INVENTORY.json'))
fh=d['frame_host']
for k in ['frame_map','frame_plan']:
    print('##',k); print(json.dumps(fh['metadata'][k])[:1800])
print('## db', json.dumps(fh['required_store_databases'])[:2500])
u=json.load(open('work/frames/units.json'))
print('## units.json type', type(u).__name__, list(u.keys())[:20] if isinstance(u,dict) else len(u))
for k,v in (u.items() if isinstance(u,dict) else []):
    print(k, str(v)[:300])
PY
ls work/frames
