from pathlib import Path
import json
L=Path(__file__).resolve().parents[2]
for path in sorted((L.parent/'work/rows_slices').rglob('*.jsonl')):
    with path.open() as f:row=json.loads(next(f))
    print(path.name,json.dumps({k:(list(v)[:10] if isinstance(v,dict) else v[:90] if isinstance(v,str) else type(v).__name__) for k,v in row.items() if k not in ('qid','question','answer')}))
