"""Keep the initial packet as evidence and stage the final packet from empty."""
import json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/n1fix3'
sys.path.insert(0,str(L/'work/tree_r1'))
from launch_r1.build import build
old=B/'kits/r1';archive=B/'proofs/kit_build/initial'
archive.parent.mkdir(parents=True,exist_ok=True)
if old.exists() and not archive.exists():old.rename(archive)
result=build(B/'inputs/config.json',B/'inputs',old)
(B/'KIT_RESULT.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
