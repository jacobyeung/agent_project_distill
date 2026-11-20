from common import *
import tempfile,copy
from unittest.mock import patch
from student_pilot.r1_persisted import scope
from tests.test_host24l4s import RoomResolution
from student_pilot import r1_rooms, r1_direction_twins
F=D/'vqa_complete';F.mkdir();tempfile.tempdir=str(F)
paths={v['sha256']:v['local_path'] for v in J.load(L/'work/build24m2c/UPLOADS_q.json')['files'] if v['opaque_name'].startswith('u/')}
paths.update({p.name:str(p) for p in (D/'u').iterdir()})
records=[]
for name in ('q','n','n_go','qd'):
 for mod in ('cs','sv','rv','z'):sys.modules.pop(mod,None)
 sys.path.insert(0,str(kit(name)/'b'))
 import cs,sv
 f=RoomResolution('test_vqa_native_tiered_clean_alias_passes');f.setUp()
 try:
  mapping,source=f.vqa_authority()
  cfg=copy.deepcopy(J.load(kit(name)/'k/n.json'))
  cfg['r1_training'].update({k:f.cfg0['r1_training'][k] for k in ('room_authority','direction_twins','v7_k1_removal')})
  entries=[dict(population=cfg['r1_training']['direction_twins']['source_database'],count=1)]
  assert r1_rooms.Rooms(f.pins).status(source)[0]=='unresolved'
  calls=[];native=r1_direction_twins.Binding.room
  def traced(self,row):calls.append(row['qid']);return native(self,row)
  with scope(paths),patch.object(r1_direction_twins.Binding,'room',traced):
   classify=sv.classifier(cfg)
   result,keys=cs.evaluate(cfg,'vqa',entries,lambda:iter([source]),classify)
   assert result['result'] is not None and result['result']['admitted_rows']==1 and result['refusals']==[] and keys==[],result
   assert len(calls)>=2,calls
   bad=dict(qid='heldout',dataset='d1',scene='opaque_heldout')
   result,keys=cs.evaluate(cfg,'vqa',entries,lambda:iter([bad]),classify)
   assert 'R1_PROTECTED_ROOM_ROWS:vqa' in result['refusals'] and 'heldout' in keys,result
  records.append(dict(kit=name,strict_room='unresolved',native_binding_room='scannet/scene9000',clean='PASS',protected='R1_PROTECTED_ROOM_ROWS:vqa',native_binding_calls=len(calls)))
 finally:f.doCleanups()
J.write(D/'VQA_KIT_TESTS.json',dict(status='PASS',records=records,boundary='Pinned synthetic full Binding files and authority constants; real kit classifier and census evaluate; no production-store claim.'))
print('Native VQA Binding through all four kits PASS')
