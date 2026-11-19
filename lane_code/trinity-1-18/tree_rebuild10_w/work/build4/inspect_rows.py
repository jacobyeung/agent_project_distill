import json
from pathlib import Path
L = Path(__file__).resolve().parents[2]
for folder in ('slices_v3', 'slices_final'):
    for p in sorted((L/'work/rows_slices'/folder).glob('*.jsonl')):
        with p.open() as f:
            row = json.loads(next(f))
        print(p.name, p.stat().st_size, sorted(row))
        if p.stem == 'a0_units':
            from collections import Counter
            print(Counter(json.loads(line)['ground_record'].get('unit') for line in p.open()))
