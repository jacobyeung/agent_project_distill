"""Check neutral configuration spelling before replacing the running fixture's source."""
from pathlib import Path
import json,shutil,sys
L=Path(__file__).resolve().parents[2];D=L/'work/build22';B=L/'work/build21';K=D/'kits/q';O=D/'proofs/neutral_preview'
sys.path[:0]=[str(D),str(B),str(L/'work/tree_r1')]
import joblib as J,naming22 as N
from launch_r2.build import capsule_json
shutil.copytree(K,O,dirs_exist_ok=True)
for name in ('k/c.json','k/n.json'):
 p=O/name;v=J.load(p);v['r1_training']['not_present_slots']=['0','1'];p.write_bytes(capsule_json(v))
result=N.scan_decoded(O)
J.write(D/'NEUTRAL_SCAN_PREVIEW.json',dict(preview_only='Scanner-only spelling preview; runtime source has not changed and this is not a runnable kit.',**result))
print(result['status'],result['checked_strings'])
