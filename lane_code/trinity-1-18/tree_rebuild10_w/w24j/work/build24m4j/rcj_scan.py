from common import *
import ast,subprocess
from unittest.mock import patch
import environment21f as E
from launch_r2.build import bad_string
wh=J.load(kit('qd')/'b/wh.json');checked=[]
def check(value,where):
 if bad_string(value,wh):raise ValueError('NAME:'+where+':'+value)
 checked.append(where)
with patch.object(E,'__file__',str(D/'rcj_scanner/environment21f.py')):
 for p in (L/'out/rcj').iterdir():
  check('rcj/'+p.name,'file')
  for i,line in enumerate(p.read_text().splitlines(),1):check(line,'rcj/'+p.name+':'+str(i))
  if p.suffix=='.py':E.scan_python(ast.parse(p.read_text()),check,'rcj/'+p.name)
  if p.suffix=='.sh':E.scan_shell(p.read_text(),check,'rcj/'+p.name)
with patch.object(E,'__file__',str(D/'rcj_scanner/environment21f.py')):
 try:E.scan_shell((L/'out/rcj/rcj.sh').read_text()+'\nexport ${DYNAMIC}=q\n',check,'rcj/rcj.sh')
 except ValueError as e:assert str(e).startswith('ENV_UNRESOLVED:')
 else:raise AssertionError('Changed shell accepted certificate')
subprocess.run(['/bin/bash' ,'-n',str(L/'out/rcj/rcj.sh')],check=True)
J.write(D/'RCJ_SCAN.json',dict(status='PASS',checks=len(checked),files=['rcj/rcj.sh','rcj/x.py'],helper_bytes=sum(p.stat().st_size for p in (L/'out/rcj').iterdir())))
print('RCJ naming/environment scan PASS',len(checked))
