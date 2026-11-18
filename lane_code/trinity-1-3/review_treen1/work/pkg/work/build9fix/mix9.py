from pathlib import Path
import json,sys,hashlib
L=Path(__file__).resolve().parents[2];B=L/'work/build9fix'
sys.path.insert(0,str(L/'work/tree_r1'))
from student_pilot.r2_mix import table
from launch_r2.build import capsule_json
(L/'out/MIX_R1.json').write_bytes((B/'inputs/mix.json').read_bytes())
(L/'out/MIX_A0.json').write_bytes(capsule_json(table()))
(L/'out/MIX_A2.json').write_bytes(capsule_json(table()))
result={name:dict(path='out/'+name,sha256=hashlib.sha256((L/'out'/name).read_bytes()).hexdigest()) for name in ('MIX_R1.json','MIX_A0.json','MIX_A2.json')}
(B/'MIX_BINDINGS.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
