from pathlib import Path
from collections import Counter
import json
L=Path(__file__).resolve().parents[2];D=L/'work/build22'
m=json.loads((D/'PACKAGE_MANIFEST.json').read_text())['files']
print('Total bytes',sum(v['bytes'] for v in m.values()),'files',len(m))
print('Largest files')
for name,v in sorted(m.items(),key=lambda kv:kv[1]['bytes'],reverse=True)[:45]:print(v['bytes'],name)
groups=Counter()
for name,v in m.items():groups['/'.join(name.split('/')[:3])]+=v['bytes']
print('Groups',groups.most_common(18))
for p in (L/'out').glob('tree_rebuild_b22_*.tar'):
    target=L/'attic'/('oversize_'+p.name)
    assert not target.exists();p.rename(target);print('Retained',str(target),target.stat().st_size)
