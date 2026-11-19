from pathlib import Path
import sys,json
L=Path(__file__).resolve().parents[2];D=L/'work/build22';B=L/'work/build21'
sys.path[:0]=[str(B),str(L/'work/tree_r1')]
from naming21 import scan_decoded
K=D/'kits/q' if (D/'kits/q').exists() else B/'kits/q'
v=scan_decoded(K);(D/'SCAN.json').write_text(json.dumps(v,indent=2)+'\n');print(v['status'],v['checked_strings'])
