from pathlib import Path
import json,hashlib
R=Path('/scratch/jjyeung/n30_mirror/dist_diag/coverage_v2h')
for p in (R/'COVERAGE_UNITS_V2H.jsonl',R/'COVERAGE_DISTANCE_V2H.jsonl'):
    with p.open() as f:row=json.loads(next(f))
    print(p.name,p.stat().st_size,hashlib.sha256(p.read_bytes()).hexdigest())
    print('keys',list(row));print(json.dumps({k:v for k,v in row.items() if k not in ('native_row','source_row','row')},indent=2)[:3500])
    for k in ('native_row','row'):
        if k in row:print(k,'keys',list(row[k]));print('question',row[k].get('question'),row[k].get('student_input',{}).get('question'))
print('u2 exists',Path('/scratch/jjyeung/orch_n30/sb_k1list/out/u2.json').exists())
