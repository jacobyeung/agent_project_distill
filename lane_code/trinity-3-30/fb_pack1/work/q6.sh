/scratch/jjyeung/envs/p1cpu/bin/python -B - <<'PY'
import json
d=json.load(open('/scratch/jjyeung/orch_n30/fb_pack/route/out/BLOCKER_DIAGNOSTICS.json'))
for k,v in d.items():
    if k in ('inputs',): continue
    print('##',k, json.dumps(v)[:1600])
r=json.load(open('/scratch/jjyeung/orch_n30/fb_pack/route/out/INTAKE_RESULTS.json'))
print('## INTAKE keys', list(r.keys())[:20])
for k,v in r.items():
    if 'camera_wording' in k or k=='summary': print(k, json.dumps(v)[:1500])
PY
