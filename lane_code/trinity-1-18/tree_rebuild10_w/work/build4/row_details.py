import json
from pathlib import Path
L=Path(__file__).resolve().parents[2]
for name in ('pool_route_planning','pool_abs_distance','a0_pool_abs_distance_reworded','d0_facing_easy'):
    g='slices_final' if name.startswith('a0_pool') else 'slices_v3'
    row=json.loads(next((L/'work/rows_slices'/g/(name+'.jsonl')).open()))
    si=row.get('student_input',{})
    print(name, {k:(si.get(k)[:3] if isinstance(si.get(k),list) else si.get(k)) for k in ('fps','total_num_frames','frames','frame_indices')})
    if 'suffix' in row:
        print(row['suffix'][:2500])
        print('provenance keys',list(row.get('provenance',{})), 'canonical',row.get('canonical'), 'spec',row.get('spec_version'))
fps=json.loads((L/'work/kit07ca49df_meta/m/k/frame_rates.json').read_text())
print('fps summary', {k:v for k,v in fps.items() if not isinstance(v,(dict,list))})
print('fps object keys',[(k, list(v)[:4]) for k,v in fps.items() if isinstance(v,dict)])
