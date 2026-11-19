from pathlib import Path
from collections import Counter
from fractions import Fraction
import json,sys,datetime
L=Path(__file__).resolve().parents[2];D=L/'work/build22';I=D/'inputs'
sys.path[:0]=[str(L/'work/tree_r1'),str(L/'work/build21')]
import joblib as J
from student_pilot import r1_coverage as C,r1_training,r2_contract,s1_routing,extent_receipt,r0_exclusion,carrier_c1_routing as cr
from student_pilot.p3_provenance import file_pin,load,pinned,digest
from student_pilot.r1_rooms import Rooms
from student_pilot.r1_routing import Filters
cfg=load(I/'config.json');value=cfg['r1_training'];inventory=load(D/'INVENTORY.json')
pin={k:inventory['CAMERA_ROWS.jsonl'][k] for k in ('path','sha256')}
wp={k:inventory['WORDINGS.json'][k] for k in ('path','sha256')}
guard=C.WordingExclusion(value['wording_exclusion'],wp)
filters=Filters(cfg,cfg['scene_division']);rooms=Rooms(value['room_authority'])
counts=Counter();qids=[];examples=[];errors=Counter()
with pinned(pin).open() as f:
 for line in f:
  row=json.loads(line);guard.check(row);kind=row['routing']['question_type'];counts[kind]+=1
  r1_training.row_check(row,'routing');r2_contract.frame_metadata(row['student_input'])
  s1_routing.legacy_replay(row);extent_receipt.Extents(None).check(row,'routing');r0_exclusion.reserve().check(row,'routing')
  rooms.admit(row)
  reason=filters.reason(row,'routing')
  if reason:errors[reason]+=1
  else:qids.append(row['qid'])
  if len(examples)<20:examples.append(dict(qid=row['qid'],type=kind,row_sha256=digest(row)))
assert len(qids)==6000 and len(set(qids))==6000 and not errors,(len(qids),errors)
sources=load(pinned(value['row_sources']));sources['camera_wording']=dict(source=pin,variant='wording_only',status='Pinned native routing rows; host envelopes required')
value['row_sources']=J.write(I/'row_sources.json',sources)
catalog=load(pinned(value['source_membership']));catalog['sources']['camera_wording']=dict(source=pin,qids=qids)
value['source_membership']=J.write(I/'source_membership.json',catalog);value['camera_wording_exclusion']=wp
card=load(pinned(value['mix']));programs=('camera_displacement','camera_movement_direction','camera_rotation','absolute_distance')
prior={c['type']:int(Fraction(str(c['rows_per_step']))*1000) for c in card['cells'] if c['type'] in programs}
total=sum(prior.values());ideal={k:Fraction(3000*v,total) for k,v in prior.items()};cuts={k:int(v) for k,v in ideal.items()}
for k in sorted(prior,key=lambda k:(ideal[k]-cuts[k],k),reverse=True)[:3000-sum(cuts.values())]:cuts[k]+=1
for cell in card['cells']:
 if cell['type'] in cuts:cell['rows_per_step']=(prior[cell['type']]-cuts[cell['type']])/1000
card['cells'].append(dict(type='camera_wording',stream='routing',rows_per_step=3.0,ceiling_rows_per_step=24.0))
value['mix']=J.write(I/'mix.json',card);J.write(I/'config.json',cfg)
C.validate_binding(cfg)
J.write(D/'CAMERA.json',dict(timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),source=pin,wordings=wp,counts=dict(counts),admitted=len(qids),heldout_hits=0,room_hits=0,refused=dict(errors),card=value['mix'],quota=3.0,ceiling=24.0,pro_rata=dict(prior=prior,cuts=cuts),examples=examples,validators=['r1_training.row_check','r2_contract.frame_metadata','s1_routing.legacy_replay','extent_receipt.Extents.check','r0_exclusion.reserve.check','Rooms.admit','Filters.reason']))
print('PASS',dict(counts),len(qids))
