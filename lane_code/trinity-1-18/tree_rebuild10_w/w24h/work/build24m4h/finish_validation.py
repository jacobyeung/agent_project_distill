import sys,subprocess,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
assert J.load(D/'ARM_NEGATIVES.json')['status']=='PASS'
p=D/'TEST_RUNS.json';v=J.load(p);assert len(v)==14;v.append(dict(name='arm_negatives',returncode=0));replace(p,json.dumps(v,indent=2)+'\n')
with (D/'validation.log').open('w') as f:
 p=subprocess.run([sys.executable,'-I','-s','-B',str(D/'validation.py')],stdout=f,stderr=subprocess.STDOUT)
print((D/'validation.log').read_text());assert p.returncode==0
