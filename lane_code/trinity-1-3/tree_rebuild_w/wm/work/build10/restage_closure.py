import json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/build10'
sys.path.insert(0,str(L/'work/tree_r1'))
from launch_r1.build import build
target=B/'kits/r1';target.rename(L/'work/merge11/proofs/kit_build/opener_binding')
result=build(B/'inputs/config.json',B/'inputs',target)
(B/'KIT_RESULT.json').write_text(json.dumps(result,indent=2)+'\n')
prior=L/'work/merge11/proofs/contracts/kit';prior.rename(L/'work/merge11/proofs/kit_build/contracts_metadata')
print(json.dumps(result))
