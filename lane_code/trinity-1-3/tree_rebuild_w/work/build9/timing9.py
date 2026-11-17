import json
from pathlib import Path
L=Path(__file__).resolve().parents[2]
for group in ('generator','legacy','r2'):
    p=L/'work/build8/proofs/suite_tree'/group/'temporary_sizes.json'
    rows=json.loads(p.read_text())
    print(group,dict(tests=len(rows),recorded_seconds=sum(r['seconds'] for r in rows),
        slowest=[{'test':r['test'],'seconds':r['seconds']} for r in sorted(rows,key=lambda r:r['seconds'],reverse=True)[:3]]))
