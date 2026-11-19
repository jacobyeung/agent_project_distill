import json
import os
from pathlib import Path
L=Path(__file__).resolve().parents[2]
for name in ('work/kit07ca49df_meta/m/k/b02e4385.json',):
    v=json.loads((L/name).read_text())
    print(name, json.dumps(v.get('s1_routing'),indent=2))
root=L/'work/tmp'
sizes=[]
for p in root.iterdir():
    n=sum(q.stat().st_size for q in p.rglob('*') if q.is_file()) if p.is_dir() else p.stat().st_size
    sizes.append((n,p.name))
print('temporary_largest',sorted(sizes,reverse=True)[:15])
