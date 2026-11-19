"""Inspect selected local archive metadata before a bounded repack."""
from pathlib import Path
from collections import Counter
import json
L=Path(__file__).resolve().parents[2];B=L/'work/build17'
path=B/'delivery17.py';text=path.read_text().split('size=sum(')[0]
scope=dict(__file__=str(path));exec(compile(text,str(path),'exec'),scope)
groups=Counter()
for p in scope['members']:
    parts=p.relative_to(L).parts
    groups['/'.join(parts[:6] if len(parts)>3 and parts[2]=='proofs' else parts[:3])]+=p.stat().st_size
large=[dict(path=str(p.relative_to(L)),bytes=p.stat().st_size)
       for p in sorted(scope['members'],key=lambda p:p.stat().st_size,reverse=True)[:30]]
result=dict(groups=groups.most_common(35),largest=large)
(B/'PACKAGE_PLAN.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
