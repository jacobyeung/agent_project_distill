import json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/build9fix';sys.path.insert(0,str(L/'work/tree_r1'))
from student_pilot.p3_provenance import load
from student_pilot.carrier_c1_run import validate
cfg=load(B/'inputs/config.json')
try:validate(cfg);result={'status':'PASS'}
except Exception as e:result={'status':'BLOCKED','reason':type(e).__name__+': '+str(e)}
(B/'NATIVE_CONFIG.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
