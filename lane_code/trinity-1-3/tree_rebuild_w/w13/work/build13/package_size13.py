from pathlib import Path
from collections import Counter
import json,tarfile,os
L=Path(__file__).resolve().parents[2];B=L/'work/build13';d=json.loads((B/'DELIVERY.json').read_text());totals=Counter();largest=[];growth=0
root=B/'proofs/final/package/frozen'
with tarfile.open(L/d['path']) as f:
    for m in f.getmembers():
        if not m.isfile():continue
        parts=Path(m.name).parts;totals['/'.join(parts[:5])]+=m.size;largest.append((m.size,m.name))
        dest=root/m.name;growth+=max(0,m.size-(dest.stat().st_size if dest.exists() else 0))
total=sum(p.stat().st_size for p in L.rglob('*') if p.is_file() and not p.is_symlink())
print(json.dumps(dict(workspace=total,positive_growth=growth,projected=total+growth,largest=sorted(largest,reverse=True)[:15],groups=totals.most_common(12)),indent=2))
