import json
from pathlib import Path
L=Path(__file__).resolve().parents[2]
for name,group in [('a0_pool_abs_distance_reworded','slices_final'),('pool_abs_distance','slices_v3'),('pool_route_planning','slices_v3')]:
    r=json.loads(next((L/'work/rows_slices'/group/(name+'.jsonl')).open()))
    print(name,sorted(r))
    print('audit',str(r.get('program_audit'))[:3000])
    print('join',str(r.get('source_join'))[:800])
rates=json.loads((L/'work/kit07ca49df_meta/m/k/frame_rates.json').read_text())['by_scene']
print('clock example',next(iter(rates.items())))
