import json
from pathlib import Path
L = Path(__file__).resolve().parents[2]
M = L/'work/kit07ca49df_meta/m'
for name in ['k/1.json', 'k/b02e4385.json', 'k/0.json']:
    data = json.loads((M/name).read_text())
    print(name, 'keys:', list(data))
    if name.endswith('b02e4385.json'):
        for key in ['recipe','streams','init_artifact','depth_init','geometry_online','mix','route_table','world_size']:
            print(key, json.dumps(data.get(key))[:6500])
    if name.endswith('0.json'):
        for entry in data.get('extra', []):
            if '/a3v2/' in entry.get('dest','') or '/a2v3/' in entry.get('dest',''):
                print(json.dumps(entry))
print('Sizes', sum(p.stat().st_size for p in L.rglob('*') if p.is_file()),
      sum(p.stat().st_size for p in (L/'work/tmp').rglob('*') if p.is_file()))
print('withheld keys', list(json.loads((L/'work/shared/WITHHELD_ROOMS_80.json').read_text())))
