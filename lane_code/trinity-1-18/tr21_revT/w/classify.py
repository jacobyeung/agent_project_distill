import json, glob, os, sys
side = sys.argv[1]
out = {}
for f in sorted(glob.glob(f'res3/{side}/*.json')):
    d = json.load(open(f))
    for name in (d.get('failures') or []) + (d.get('errors') or []):
        txt = str((d.get('failure_text') or {}).get(name, ''))
        lines = [l for l in txt.strip().splitlines() if l.strip()]
        out[name] = lines[-1][:140] if lines else ''
for k, v in out.items():
    print(k[:80], '|', v)
json.dump(out, open(f'classify_{side}.json', 'w'), indent=1)
