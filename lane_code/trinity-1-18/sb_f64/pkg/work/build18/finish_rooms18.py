from pathlib import Path
import sys,json
L=Path(__file__).resolve().parents[2];B=L/'work/build18';I=B/'inputs';O=B/'proofs/rooms'
sys.path.insert(0,str(L/'work/tree_r1'))
from student_pilot.p3_provenance import load,pinned,file_pin
from tests.test_r2_build_n1 import write
from student_pilot import r1_rooms as R
cfg=load(I/'config.json');result=load(O/'RESULT.json');post=load(pinned(cfg['r1_training']['room_audit']))
keys={json.loads(line)['row_key'] for line in (I/'u.json').read_text().splitlines()}
intersections={}
for kind,spec in load(pinned(cfg['r1_training']['row_sources'])).items():
    if kind not in ('recovery','units','absolute_distance'):continue
    with pinned(spec['source']).open() as source:intersections[kind]=sum(json.loads(line)['qid'] in keys for line in source)
assert not any(intersections.values())
for key in ('mix','row_sources','source_membership'):
    cfg['r1_training'][key]=write(I/(key+'.json'),load(pinned(cfg['r1_training'][key])))
cfg['streams']['vqa']=write(I/'v7_receipt.json',load(pinned(cfg['streams']['vqa'])))
cfg['r1_training']['store_parameter']=cfg['streams']['vqa']
for key,pin in cfg['r1_training']['room_authority'].items():
    local=I/(pin['sha256']+'.json');local.write_bytes(pinned(pin).read_bytes());cfg['r1_training']['room_authority'][key]=file_pin(local)
post['row_sources']=cfg['r1_training']['row_sources'];post['authority']=cfg['r1_training']['room_authority']
post['store']['certification']=post['authority']['build']
cfg['r1_training']['room_audit']=write(I/'room_audit.json',post)
R.verify_audit(cfg,cfg['r1_training']['room_audit'])
for name in ('config.json','kit_config.json'):write(I/name,cfg)
result['audit_after']=post;result['slice_v7_key_intersections']=intersections;write(O/'RESULT.json',result)
print(json.dumps(dict(intersections=intersections,cells=result['eligible_by_cell'],changed=result['card_cells_changed']),indent=2))
