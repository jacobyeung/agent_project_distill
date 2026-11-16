"""Bounded build metadata inspection; no shared storage access."""
import json
from pathlib import Path

L = Path(__file__).resolve().parents[2]
tmp = L/'work/tmp'
tmp.mkdir(exist_ok=True)
print('tmp_bytes', sum(p.stat().st_size for p in tmp.rglob('*') if p.is_file()))
print('lane_bytes', sum(p.stat().st_size for p in L.rglob('*') if p.is_file()))
for name in ('k/launch.json', 'k/0.json', 'k/4.json', 'k/7.json', 'k/b02e4385.json'):
    obj = json.loads((L/'work/kit07ca49df_meta/m'/name).read_text())
    if name == 'k/0.json':
        obj = {k: (v if k not in ('extra','tars') else {'count':len(v), 'example':v[:1]}) for k,v in obj.items()}
    if name == 'k/7.json':
        obj = {k:(v if k not in ('files','sources','operation_sources') else len(v)) for k,v in obj.items()}
    print(name, json.dumps(obj, indent=2))
