from common import *
import ast
from environment21f import scan_python
p=kit('qd')/'b/f0.py'
scan_python(ast.parse(p.read_text()),lambda *a:None,'b/f0.py')
print('Explicit wrapper environment scan PASS')
print('qd',reseal(kit('qd')))
from launch_r1.build import verify
J.write(D/'SEALS.json',{n:verify(kit(n)) for n in NAMES})
