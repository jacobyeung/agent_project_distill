from pathlib import Path
from collections import Counter
import json
B=Path(__file__).resolve().parent
source=(B/'make_delivery.py').read_text().split('size=sum',1)[0]
scope={'__file__':str(B/'make_delivery.py')};exec(compile(source,str(B/'make_delivery.py'),'exec'),scope)
sizes=Counter()
for p in scope['members']:
    rel=p.relative_to(scope['L']);sizes['/'.join(rel.parts[:3])]+=p.stat().st_size
sizes['packet_inputs']=sum(r['bytes'] for r in scope['packet_inputs'])
print(json.dumps(dict(total=sum(sizes.values()),groups=sizes),indent=2))
