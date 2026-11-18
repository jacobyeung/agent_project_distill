import json
from pathlib import Path
B=Path(__file__).resolve().parent
for name in ('live_failures.json','live_errors.json'):
    p=L/'work/merge11/proofs/suite_tree/legacy'/name
    rows=json.loads(p.read_text())
    print(name,len(rows))
    print(json.dumps(rows[-5:],indent=2)[:6000])
