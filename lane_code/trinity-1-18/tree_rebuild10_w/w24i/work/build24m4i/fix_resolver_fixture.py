import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
p=L/'work/build24/UPLOADS_n.json';assert not p.exists();p.write_bytes((W/'w24/work/build24/UPLOADS_n.json').read_bytes())
a=L/'attic/build24m4i/resolver600_first';a.mkdir(parents=True)
for p in (D/'resolver600_tests.log',D/'proofs/resolver600_v2'):
 p.rename(a/p.name)
print('Restored missing read-only manifest fixture; retained failed log and fixture tree')
