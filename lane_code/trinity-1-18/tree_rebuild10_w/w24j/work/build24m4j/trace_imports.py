from common import *
import subprocess
sys.path.insert(0,str(kit('qd')/'b'));import rb
F=D/'trace';F.mkdir();env=rb.environment()
control=F/'control.json';J.write(control,dict(root=str(F),directory='x',environment=env,probe_only=True))
p=F/'trace.py';p.write_text('''import sys,json
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
 (Path(value['root'])/'external.json').write_text(json.dumps(modules,indent=2)+'\\n')
''')
v=J.load(control);v['helper']=str(kit('qd')/'b');J.write(control,v)
cmd=rb.command(F,control,D/'p_tree',{},env);cmd[-3]=str(p)
r=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True);(F/'trace.log').write_text(r.stdout);assert r.returncode==0,r.stdout
values=J.load(F/'external.json');print('LOCAL EXTERNAL',sorted(values))
J.write(D/'LOCAL_IMPORT_TRACE.json',dict(status='PASS',packages=values,scope='Trinity p1cpu environment; no Orchard package versions inferred'))
