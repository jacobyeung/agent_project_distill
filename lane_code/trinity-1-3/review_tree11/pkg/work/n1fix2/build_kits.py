import json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/n1fix2';sys.path.insert(0,str(L/'work/tree_r1'))
from launch_r1.build import build,verify
path=L/'work/merge11/kits/r1'
result=build(B/'inputs/config.json',B/'inputs',path)
(B/'KIT_RESULT.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
