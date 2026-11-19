/scratch/jjyeung/envs/p1cpu/bin/python -B - <<'PY'
import json
m=json.load(open('/scratch/jjyeung/orch_n30/fb_pack/route/out/ROUTE_MANIFEST.json'))
print([k for k in m.keys()])
print(m['passed_slices'])
s=m.get('slices') or {}
print(type(s).__name__, list(s.keys()) if isinstance(s,dict) else len(s))
k=list(s.keys())[0] if isinstance(s,dict) else 0
print(json.dumps(s[k])[:2500])
c=json.load(open('/scratch/jjyeung/orch_n30/fb_pack/route/out/CONFIG_HANDOFF.json'))
print(list(c.keys())); print(json.dumps(c)[:1500])
b=json.load(open('/scratch/jjyeung/orch_n30/fb_pack/cam/out/BUILD.json')); print(list(b.keys())[:30])
r=json.load(open('/scratch/jjyeung/orch_n30/fb_pack/cam/out/REBIND.json')); print(list(r.keys())[:30])
PY
ls /scratch/jjyeung/orch_n30/fb_pack/cam/out/envelopes /scratch/jjyeung/orch_n30/fb_pack/cam/out/upstream /scratch/jjyeung/orch_n30/fb_pack/cam/out/coverage /scratch/jjyeung/orch_n30/fb_pack/cam/out/rows
