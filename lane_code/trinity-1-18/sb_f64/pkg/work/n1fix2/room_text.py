import json
from pathlib import Path
p=Path('/scratch/jjyeung/orch_n30/rows_r1/out/room_v2/rows.jsonl')
with p.open() as f:
    for _ in range(2):
        r=json.loads(next(f));print(r.get('target',r.get('suffix')))
