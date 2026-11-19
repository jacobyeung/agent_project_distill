from pathlib import Path
import sys,json
L=Path(__file__).resolve().parents[2];B=L/'work/build19';O=B/'proofs/configuration';O.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(L/'work/tree_r1'))
from student_pilot.p3_provenance import load,file_pin,pinned
from student_pilot.r1_components import NOTICE
old=load(L/'work/build18/inputs/config.json');new=load(B/'inputs/config.json')
keys=('init_artifact','r2_identity','remove_files','dev_scene_exclusions','benchmark_scene_exclusions','exclusions','scene_division','routing_opener_init','camera_overrides')
equal={k:old[k]==new[k] for k in keys};assert all(equal.values())
card=load(pinned(new['r1_training']['mix']));before=load(pinned(old['r1_training']['mix']))
assert card['cells']==before['cells'] and card['component_evidence']==NOTICE
assert new['r1_training']['weight_scale']==card['weight_scale']==.04
result=dict(status='PASS',unchanged=equal,card_cells_unchanged=True,parent=new['r2_identity']['init'],
    weight_scale=.04,card=file_pin(pinned(new['r1_training']['mix'])),record=new['r1_training']['component_rows'])
result['list_counts']={p['sha256']:sum(bool(line.strip()) for line in pinned({k:p[k] for k in ('path','sha256')}).open()) for p in new['remove_files']}
assert result['list_counts']['02315a74ed9020a9b7aa2f1a70ac765701bf17c71d4027d4424b9fdf0678a411']==601
(O/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n')
