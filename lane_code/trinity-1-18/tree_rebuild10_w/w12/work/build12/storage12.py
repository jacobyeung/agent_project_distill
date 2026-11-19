"""Count local file sizes without reading contents or following directory links."""
from pathlib import Path
import json,os
L=Path(__file__).resolve().parents[2];N=L.parent;totals={};count=0
for root,dirs,files in os.walk(N,followlinks=False):
    dirs[:]=[d for d in dirs if not (Path(root)/d).is_symlink()]
    for name in files:
        p=Path(root)/name
        if p.is_symlink():continue
        bucket=p.relative_to(N).parts[0];totals[bucket]=totals.get(bucket,0)+p.stat().st_size;count+=1
record=dict(scope=str(N),bytes=sum(totals.values()),files=count,by_top_level=totals,
    method='Metadata only; file contents and symlink targets were not read.',limit_bytes=14_000_000_000)
(L/'work/build12/STORAGE.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record))
assert record['bytes']<record['limit_bytes']
