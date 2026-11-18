import json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/n1fix3'
sys.path.insert(0,str(L/'work/tree_r1'))
from launch_r1.build import build
target=B/'kits/r1';prior=B/'proofs/kit_build/receipt_binding'
target.rename(prior)
result=build(B/'inputs/config.json',B/'inputs',target)
(B/'KIT_RESULT.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
