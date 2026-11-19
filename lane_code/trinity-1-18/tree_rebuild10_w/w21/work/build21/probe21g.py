from pathlib import Path
import datetime,json,sys
L=Path(__file__).resolve().parents[2];B=L/'work/build21';D=L/'work/build21g'
sys.path[:0]=[str(B),str(L/'work/tree_r1')]
from naming21 import scan_decoded
print(datetime.datetime.now(datetime.timezone.utc).isoformat(),flush=True)
try:
    result=scan_decoded(B/'kits/q')
except ValueError as e:
    print(str(e));raise SystemExit(1)
(D/'SCAN.json').write_text(json.dumps(result,indent=2)+'\n')
print(result['status'],result['checked_strings'])
