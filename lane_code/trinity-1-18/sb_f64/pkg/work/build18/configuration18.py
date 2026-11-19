"""Bind the unchanged configuration contracts and the single new row list."""
from pathlib import Path
import sys,json
L=Path(__file__).resolve().parents[2];B=L/'work/build18';O=B/'proofs/configuration';O.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(L/'work/tree_r1'))
from student_pilot.p3_provenance import load,pinned,file_pin
from student_pilot.r1_handover import pin_values
from student_pilot.r1_rooms import V7_K1_LIST,N_LIST
old=load(L/'work/build17/inputs/config.json');new=load(B/'inputs/config.json')
before=[p['sha256'] for p in old['remove_files']];after=[p['sha256'] for p in new['remove_files']]
assert [h for h in after if h!=V7_K1_LIST]==before
assert after.count(V7_K1_LIST)==1 and after.index(V7_K1_LIST)+1==after.index(N_LIST)
counts={}
for pin in new['remove_files']:
    p=pinned({k:pin[k] for k in ('path','sha256')})
    counts[pin['sha256']]=sum(bool(line.strip()) for line in p.open())
assert counts[N_LIST]==601 and counts[V7_K1_LIST]==2637
card=load(pinned(new['r1_training']['mix']));prior=load(pinned(old['r1_training']['mix']))
assert card['cells']==prior['cells'] and card['weight_scale']==new['r1_training']['weight_scale']==new['camera_overrides']['weight_scale']==.04
keys=('init_artifact','r2_identity','dev_scene_exclusions','benchmark_scene_exclusions','exclusions','scene_division','routing_opener_init')
equal={k:pin_values(old.get(k))==pin_values(new.get(k)) for k in keys}
assert all(equal.values())
result=dict(status='PASS',configuration=file_pin(B/'inputs/config.json'),comparison=file_pin(L/'work/build17/inputs/config.json'),
    only_added_removal=V7_K1_LIST,list_counts=counts,remove_order=after,unchanged=equal,card_cells_equal=True,
    parent=new['r2_identity']['init'],weight_scale=.04)
(O/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
