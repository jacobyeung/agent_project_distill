from pathlib import Path
import json
L=Path(__file__).resolve().parents[2]
for p in [L.parent/'work/rows_slices/slices_final/a0_recovery.jsonl',Path('/scratch/jjyeung/orch_n30/rows_r1/out/recovery_v3/rows.jsonl'),Path('/scratch/jjyeung/orch_n30/rows_r1/out/vehN_units/repaired/rows_slice.jsonl')]:
    with p.open() as f:
        row=json.loads(next(f));repaired=next((r for line in f if (r:=json.loads(line)).get('provenance',{}).get('repair')),None)
    print(p,'keys',list(row),'events',row.get('events',[])[:1],'spans',row.get('tool_output_spans',[])[:1])
    if repaired:print('REPAIR',json.dumps(repaired['provenance']['repair'])[:6500])
for name in ('vehN_pool_abs_distance/repaired','vehN_units/repaired'):
    root=Path('/scratch/jjyeung/orch_n30/rows_r1/out')/name
    print(name,[(p.name,p.stat().st_size) for p in root.iterdir() if p.is_file()])
print('LOCAL',[(p.name,p.is_dir()) for p in (L/'work').iterdir()])
print('SOURCE',json.loads((L/'work/n1fix/inputs/row_sources.json').read_text()))
