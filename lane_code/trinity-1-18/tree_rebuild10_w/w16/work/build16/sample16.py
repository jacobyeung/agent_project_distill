from pathlib import Path
import json,sqlite3
R=Path('/scratch/jjyeung/n30_mirror')
for s in ('rows_r1/out/recovery_v3/rows.jsonl','rows_r1/out/vehN_units/repaired/rows_slice.jsonl','rows_r2/out/vehN_pool_abs_distance_full/repaired/rows.jsonl'):
    with (R/s).open() as f:r=json.loads(next(f))
    print(s,json.dumps({k:v for k,v in r.items() if k not in ('ground_record','target','suffix','student_input')})[:6000])
    print('input',r.get('student_input',{}))
c=sqlite3.connect((R/'rows_r1/out/a2_vqa_v7/vqa/rows.sqlite').as_uri()+'?mode=ro',uri=True)
r=json.loads(c.execute('select row from rows limit 1').fetchone()[0]);c.close()
print('vqa',json.dumps({k:v for k,v in r.items() if k not in ('ground_record','target','suffix','student_input')})[:6000])
