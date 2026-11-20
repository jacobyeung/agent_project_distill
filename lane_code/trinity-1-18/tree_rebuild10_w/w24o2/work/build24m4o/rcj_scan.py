import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
import ast
from unittest.mock import patch
sys.path.insert(0,str(L/'work/build24m4n'))
import environment21f as env
from launch_r2.build import bad_string
wh=z.load(kit('qd')/'b/wh.json');checks=[]
def check(value,where):
    if bad_string(value,wh):raise ValueError('NAME:'+where+':'+value)
    checks.append(where)
with patch.object(env,'__file__',str(L/'work/build24m4m/rcj_scanner/environment21f.py')):
    for p in (L/'out/rcj').iterdir():
        check('rcj/'+p.name,'file')
        if p.suffix=='.py':env.scan_python(ast.parse(p.read_bytes()),check,'rcj/'+p.name)
        if p.suffix=='.sh':
            for i,line in enumerate(p.read_text().splitlines(),1):check(line,'rcj/'+p.name+':'+str(i))
            env.scan_shell(p.read_text(),check,'rcj/'+p.name)
write(D/'RCJ_SCAN.json',dict(status='PASS',checks=len(checks),files=sorted(p.name for p in (L/'out/rcj').iterdir())))
print('rcj name/environment PASS',len(checks))
