from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
for name in ('p_preparation','p_type_mix'):
 src=W/'work/sel24/evidence'/(name+'.json');target=D/('P_'+name[2:]+'.json');target.write_bytes(src.read_bytes())
print('Authenticated P input copies staged')
