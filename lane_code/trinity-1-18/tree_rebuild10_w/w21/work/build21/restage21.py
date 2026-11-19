from pathlib import Path
import json,sys
L=Path(__file__).resolve().parents[2];B=L/'work/build21';K=B/'kits/q'
if not (B/'RESTAGED.json').exists():
 K.rename(B/'retained_q')
 (B/'KIT_Q_INITIAL.json').rename(B/'KIT_Q_INITIAL_RETAINED.json')
 (B/'RESTAGED.json').write_text(json.dumps(dict(from_empty=True,GO=False,kits=['q','r1'])))
sys.path.insert(0,str(L/'work/tree_r1'))
from launch_r1.build import build
if not (B/'kits/r1').exists():print(build(B/'inputs/kit_config.json',L/'work/n1fix2/inputs',B/'kits/r1'))
