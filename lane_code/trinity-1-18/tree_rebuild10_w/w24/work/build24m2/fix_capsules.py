import sys;from pathlib import Path;sys.path.insert(0,str(Path(__file__).resolve().parent))
from buildlib import *
for name in ('q','n','n_go','qd'):
 k=kit(name)
 for p in (k/'k').glob('*.json'):
  doc=json.loads(p.read_text())
  if doc.get('encoding')!='base64':continue
  try:json.loads(base64.b64decode(doc['payload']))
  except (ValueError,UnicodeError):continue
  doc['encoding']='base64-json';replace(p,json.dumps(doc)+'\n')
 cfg=J.load(k/'k/c.json');cfg['code']['sha256']=J.sha(k/'k/7.json');cap(k,'k/c.json',cfg)
 print(name,reseal(k))
