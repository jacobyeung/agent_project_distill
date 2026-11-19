import json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/build_n1'
sys.path.insert(0,str(L/'work/tree_r1'))
from launch_r1.build import build
target=B/'kits/r1';target.rename(B/'proofs/kit_build/opener_binding')
result=build(B/'inputs/config.json',B/'inputs',target)
(B/'KIT_RESULT.json').write_text(json.dumps(result,indent=2)+'\n')
prior=B/'proofs/contracts/kit';prior.rename(B/'proofs/kit_build/contracts_metadata')
print(json.dumps(result))
