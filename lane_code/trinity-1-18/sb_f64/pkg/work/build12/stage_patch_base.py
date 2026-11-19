"""Retain the exact supplied harness baseline for the review patch."""
from pathlib import Path
import hashlib,json
L=Path(__file__).resolve().parents[2];B=L/'work/build12'
source=L.parent/'work/design/eat1_v7/eat1';target=B/'harness_base'
rows=[]
for p in sorted(source.rglob('*.py')):
    q=target/p.relative_to(source);q.parent.mkdir(parents=True,exist_ok=True)
    raw=p.read_bytes();q.write_bytes(raw)
    rows.append(dict(file=str(p.relative_to(source)),sha256=hashlib.sha256(raw).hexdigest()))
assert rows
(B/'HARNESS_BASE.json').write_text(json.dumps(dict(source=str(source),files=rows,
    scope='Untouched read-only baseline bytes; never executed.'),indent=2)+'\n')
print(json.dumps(dict(files=len(rows),bytes=sum(p.stat().st_size for p in target.rglob('*.py')))))
