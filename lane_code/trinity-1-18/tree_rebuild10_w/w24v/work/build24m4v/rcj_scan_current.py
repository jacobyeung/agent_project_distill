from pathlib import Path
import ast,sys,json
L=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(L/'work/tree_r1c'),str(L/'out/kit_qd/b'),str(L/'work/build24m4v')]
import environment21f as env,z
from launch_r2.build import bad_string
env.__file__=str(L/'work/build24m4m/rcj_scanner/environment21f.py')
wh=z.load(L/'out/kit_qd/b/wh.json');checks=[]
def check(v,where):
 if bad_string(v,wh):raise ValueError('NAME:'+where+':'+v)
 checks.append(where)
for p in (L/'out/rcj').iterdir():
 check('rcj/'+p.name,'file')
 if p.suffix=='.py':env.scan_python(ast.parse(p.read_bytes()),check,'rcj/'+p.name)
 if p.suffix=='.sh':
  for i,line in enumerate(p.read_text().splitlines(),1):check(line,'rcj/'+p.name+':'+str(i))
  env.scan_shell(p.read_text(),check,'rcj/'+p.name)
z.write(L/'work/build24m4v/RCJ_SCAN.json',dict(status='PASS',checks=len(checks)))
print('rcj scan PASS',len(checks))
