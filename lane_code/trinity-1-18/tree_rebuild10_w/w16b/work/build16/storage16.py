from pathlib import Path
from collections import Counter
import os,json
L=Path(__file__).resolve().parents[2];B=L/'work/build16';sizes=Counter();files=0
for root,dirs,names in os.walk(L,followlinks=False):
    dirs[:]=[d for d in dirs if not (Path(root)/d).is_symlink()]
    for name in names:
        p=Path(root)/name
        if p.is_symlink():continue
        sizes[str(p.relative_to(L)).split('/')[0]]+=p.stat().st_size;files+=1
value=dict(bytes=sum(sizes.values()),files=files,by_root=dict(sizes),limit_bytes=1_500_000_000)
(B/'STORAGE.json').write_text(json.dumps(value,indent=2));print(json.dumps(value))
assert value['bytes']<=value['limit_bytes']
