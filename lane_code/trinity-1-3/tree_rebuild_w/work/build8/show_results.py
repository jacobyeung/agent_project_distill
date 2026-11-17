import json,sys
from pathlib import Path
p=Path(sys.argv[1]);r=json.loads(p.read_text())
print(json.dumps({k:v for k,v in r.items() if k in ('tests','complete','fatal')},indent=2))
print('passed',len(r.get('passed',[])),'skips',len(r.get('skips',[])))
for k in ('failures','errors'):
 for name,error in r.get(k,[]):print(k,name,error[-5000:])
