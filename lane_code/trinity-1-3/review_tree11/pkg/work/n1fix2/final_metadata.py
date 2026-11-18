import json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/n1fix2';D=B/'inputs'
sys.path.insert(0,str(L/'work/tree_r1'))
from student_pilot.p3_provenance import file_pin,load
from launch_r1.build import build
rows=load(D/'row_sources.json')
rows['room_programs_excluded']=dict(source=file_pin(L/'work/rows_slices/slices_final/a0_room.jsonl'),
    remote_source=None,status='Excluded from routing and the launch room cell; retained square-foot source binding only')
(D/'row_sources.json').write_text(json.dumps(rows,sort_keys=True,indent=2)+'\n')
cfg=load(D/'config.json');cfg['r1_training']['row_sources']=file_pin(D/'row_sources.json')
(D/'config.json').write_text(json.dumps(cfg,sort_keys=True,indent=2)+'\n')
target=L/'work/merge11/kits/r1';target.rename(L/'work/merge11/proofs/n1/kit_build/metadata_binding')
result=build(D/'config.json',D,target)
(B/'KIT_RESULT.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
