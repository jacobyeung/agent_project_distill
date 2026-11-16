import json
from pathlib import Path
L=Path(__file__).resolve().parents[2]
z=json.loads((L/'work/kit07ca49df_meta/m/k/0.json').read_text())
print('keys', sorted(z))
for k in ('venv','bwrap','small','trainer','extra','tars'):
    v=z[k]
    print(k, json.dumps(v)[:7000])
print('counts',len(z['extra']),len(z['tars']))
print('parent launch', (L/'work/kit07ca49df_meta/m/k/launch.json').read_text()[:2000])
