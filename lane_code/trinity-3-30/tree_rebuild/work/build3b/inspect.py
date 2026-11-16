import json
from pathlib import Path
L=Path(__file__).resolve().parents[2]
for name in ('work/kit07ca49df_meta/m/k/b02e4385.json','work/kit07ca49df_meta/m/k/pool_manifest.json'):
    value=json.loads((L/name).read_text())
    print(name)
    if isinstance(value,dict):
        for k,v in value.items():
            if name.endswith('b02e4385.json') and k not in ('streams','dev_scene_exclusions','benchmark_scene_exclusions','scene_coverage'):continue
            if name.endswith('pool_manifest.json'):
                if k=='sets':print('first set',v[0])
            else:print(k,str(v)[:4000])
    else:print(str(value)[:700])
print('tmp entries',len(list((L/'work/tmp').iterdir())))
print('lane bytes',sum(p.stat().st_size for p in L.rglob('*') if p.is_file()))
