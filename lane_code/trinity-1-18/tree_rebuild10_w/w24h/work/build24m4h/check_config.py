import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
for n in ('q','n'):
 for f in ('k/c.json','k/n.json','k/r.json','k/h.json','k/a.json','k/p.json','BUILD.json'):
  v=J.load(kit(n)/f)
  print(n,f,{k:x for k,x in v.items() if ('config' in k or 'sha256' in k or k in ('source','GO')) and len(str(x))<250})
print('bytes', (D/'p.tar').stat().st_size)
