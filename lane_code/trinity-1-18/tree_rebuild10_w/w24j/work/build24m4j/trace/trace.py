import sys,json
from pathlib import Path
value=json.loads(Path(sys.argv[1]).read_text())
sys.path.insert(0,value['helper'])
import rb
try:rb.child(sys.argv[1],sys.argv[2])
finally:
 modules={}
 for name,m in list(sys.modules.items()):
  p=getattr(m,'__file__',None)
  if p and ('site-packages' in p or 'dist-packages' in p):
   top=name.split('.')[0];topmod=sys.modules.get(top)
   modules[top]=dict(path=getattr(topmod,'__file__',p),version=getattr(topmod,'__version__',None))
 (Path(value['root'])/'external.json').write_text(json.dumps(modules,indent=2)+'\n')
