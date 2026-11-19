import os
from pathlib import Path
from copy import deepcopy
from unittest.mock import patch,Mock
from contextlib import ExitStack
import sys,json,unittest,importlib.util
L=Path(__file__).resolve().parents[2];D=L/'work/build24/proofs/tests23b';B=L/'work/build21';T=Path(os.environ.get('R2_TREE',L/'work/tree_r1'));R=D/'unit';R.mkdir(parents=True,exist_ok=True)
sys.path[:0]=[str(T),str(B),str(L/'work/n1fix2')]
from monitor9 import Monitor
monitor=Monitor(T)
from student_pilot import r1_coverage as C
from student_pilot.p3_provenance import file_pin,load,pinned,write
from student_pilot.r1_persisted import scope
from launch_r1 import production_proof as Q,entry,build
from student_pilot import r1_population as P,r1_rooms as Rooms,s1_admission as S
import joblib as J
PATHS={v['sha256']:v['local_path'] for v in load(L/'work/build24/UPLOADS_q.json')['files']}
BASE=load(L/'work/build24/kits/q/k/n.json')
RECORDS=[]
def pin(name,v):
 (R/(name+'.json')).write_text(json.dumps(v));return file_pin(R/(name+'.json'))
def cfg():return deepcopy(BASE)
def request(c):return dict(config=pin('config',c),staged_pins=[pin('config',c)],routing_base=c['streams']['routing'],room_audit=c['r1_training']['room_audit'])
def card():
 with scope(PATHS):return deepcopy(load(pinned(BASE['r1_training']['mix'])))
def bound(c,field,name):
 row={'path':str(R/'UNREADABLE_SOURCE'), 'sha256':'0'*64}
 if field in ('row_slice_inputs','routing_inputs'):c['r1_training'][field]={name:row}
 elif field=='row_sources':c['r1_training'][field]=pin('sources',{name:{'source':row}})
 elif field=='source_membership':c['r1_training'][field]=pin('membership',dict(schema='r1-source-catalog-v1',sources={name:dict(source=row,qids=[])}))
 elif field in ('mix','sampling_card','quota_ceiling'):
  v=card();v['cells'].append(dict(type=name,stream='routing',rows_per_step=0 if field=='quota_ceiling' else 1,ceiling_rows_per_step=1 if field=='quota_ceiling' else 0))
  p=pin('card',v)
  if field=='sampling_card':c['r2_sampling']['card']=p
  else:c['r1_training']['mix']=p
 elif field in ('population','indices'):
  if field=='population':c['r2_sampling'][field]=pin('population',dict(counts={name:1}))
  else:c['r2_sampling'][field]=pin('indices',dict(cells={name:[0]}))
 elif field=='population_membership':
  p=pin('membership',dict(schema='r1-source-membership-v1',sources={name:dict(source=row,rows={})}))
  c['r2_sampling']['population']=pin('population',dict(counts={},source_membership=p))
 return c
class MinimalBound(unittest.TestCase):
 def test_review_mutation_after(self):
  c=bound(cfg(),'row_slice_inputs','recovery')
  with scope(PATHS):r=Q._run(request(c),R/'review')
  self.assertEqual(r['refusal'],'ValueError:R1_MINIMAL_SLICE_BOUND:r1_training.row_slice_inputs:recovery')
  J.write(D/'AFTER.json',dict(mutation='review23',result=r))
 def test_clean_kit_boundary(self):
  with scope(PATHS):r=Q._run(request(cfg()),R/'clean')
  self.assertEqual(r['refusal'],'ValueError:R1_PROOF_FRAME_HOST_REQUIRED')
 def test_full_bypasses_new_gate(self):
  c=bound(cfg(),'row_slice_inputs','recovery');c['r1_training'].pop('routing_slices')
  with patch.object(C,'pinned',side_effect=AssertionError('unexpected metadata read')):
   self.assertFalse(C.deferred(c,{'routing_inputs':{'recovery':{}}},read_pins=True))
  self.assertEqual(C.source_names({}),('recovery','absolute_distance','units'))
  self.assertEqual(C.source_names(dict.fromkeys(C.PINS)),('recovery','absolute_distance','units','coverage_distance','coverage_units'))
 def test_audit_provenance_is_not_composed(self):
  with scope(PATHS):
   c=cfg();self.assertTrue(C.deferred(c,read_pins=True));self.assertEqual(C.source_names(load(pinned(c['r1_training']['row_sources'])),c),())
 def test_dynamic_extra_pin_on_nonrouting_cell(self):
  c=cfg();v=card();v['cells'].append(dict(type='future_extra',stream='vqa',rows_per_step=1));c['r1_training']['mix']=pin('extra',v)
  with scope(PATHS),patch.object(C,'EXTRA_PINS',{'future_extra':'1'*64},create=True):
   with self.assertRaisesRegex(ValueError,'R1_MINIMAL_SLICE_BOUND:.*future_extra'):C.deferred(c,read_pins=True)
 def test_source_names_does_not_hide_catalog_binding(self):
  with self.assertRaisesRegex(ValueError,'R1_MINIMAL_SLICE_BOUND:r1_training.row_sources:recovery'):
   C.source_names({'recovery':{}},dict(r1_training={'routing_slices':'deferred_first_boundary'}))
 def test_request_card_binding(self):
  c=cfg();v=card();v['cells'].append(dict(type='camera_wording',stream='routing',rows_per_step=1))
  with scope(PATHS):
   with self.assertRaisesRegex(ValueError,'R1_MINIMAL_SLICE_BOUND:request.card.cells:camera_wording'):
    C.routing_request(c,dict(routing_base=c['streams']['routing'],card=pin('request_card',v)))
 def test_request_composed_receipt_binding(self):
  c=cfg();p=pin('request_composed',dict(source_membership={'path':'unread','sha256':'0'*64}))
  with scope(PATHS):
   with self.assertRaisesRegex(ValueError,'R1_ROUTING_BASE_DIFFERS'):
    C.routing_request(c,dict(routing_base=p))
 def test_source_names_authenticates_config_catalog(self):
  c=bound(cfg(),'row_sources','recovery')
  with scope(PATHS):
   with self.assertRaisesRegex(ValueError,'R1_MINIMAL_SLICE_BOUND:r1_training.row_sources:recovery'):C.source_names({},c)
 def test_member_constructor_checks_before_source_reader(self):
  p=pin('member',dict(schema='r1-source-membership-v1',sources={'camera_wording':{}}))
  with self.assertRaisesRegex(ValueError,'R1_MINIMAL_SLICE_BOUND:source_membership:camera_wording'):P.Membership(p,minimal=True)
 def test_all_paths_refuse_inline_before_readers(self):
  c=bound(cfg(),'row_slice_inputs','recovery');p=pin('path_config',c)
  paths=[('production_proof',lambda:Q._run(request(c),R/'path_q')),
   ('entry.admit',lambda:entry.admit(c)),('entry.frame_host',lambda:entry.frame_host(c,R/'path_host',{})),
   ('s1_admission',lambda:S.admit(p,R/'path_admission',[],threads=8,memory_gib=16)),
   ('r1_population.bind_prepared',lambda:P.bind_prepared(c,R/'path_population')),
   ('r1_population.produce',lambda:P.produce(Mock(),c['r1_training']['mix'],None,[],R/'path_produce',cfg=c)),
   ('r1_rooms.census',lambda:Rooms.census(c)),('r1_rooms.verify_audit',lambda:Rooms.verify_audit(c,None)),
   ('build',lambda:build.build(p['path'],B/'inputs',R/'path_build'))]
  (R/'path_admission').mkdir(exist_ok=True)
  for label,call in paths:
   with self.subTest(path=label),scope(PATHS),ExitStack() as stack:
    for target in ('student_pilot.carrier_c1_run.Rows','student_pilot.carrier_c1_run.prepared','student_pilot.carrier_c1_run.validate','student_pilot.carrier_c1_data.build_stream','student_pilot.s1_routing.build','student_pilot.r1_routing.compose_native','student_pilot.r1_rooms.Rooms','launch_r2.staging.stage_inputs'):
     stack.enter_context(patch(target,side_effect=AssertionError('reader ran before refusal: '+target)))
    try:r=call()
    except ValueError as e:error=str(e)
    else:error=r['refusal'].removeprefix('ValueError:')
    self.assertEqual(error,'R1_MINIMAL_SLICE_BOUND:r1_training.row_slice_inputs:recovery')
    RECORDS.append(dict(path=label,refusal=error,readers=0))
 def test_regenerated_stream_membership_refuses(self):
  c=cfg();c['streams']['routing']=pin('routing',dict(source_membership={'path':'not_read','sha256':'0'*64}))
  with scope(PATHS),patch('student_pilot.carrier_c1_run.prepared',side_effect=AssertionError('reader ran')):
   with self.assertRaisesRegex(ValueError,'R1_MINIMAL_SLICE_BOUND:streams.routing.source_membership'):P.bind_prepared(c,R/'bound_stream')
 def test_central_stream_receipt_membership_refuses(self):
  c=cfg();c['streams']['routing']=pin('receipt_bound',dict(source_membership={'path':'unread_source','sha256':'0'*64}))
  with scope(PATHS):
   with self.assertRaisesRegex(ValueError,'R1_MINIMAL_SLICE_BOUND:streams.routing.source_membership'):C.deferred(c,read_pins=True)
 def test_request_base_membership_refuses(self):
  c=cfg();c['streams']['routing']=pin('routing2',dict(source_membership={'path':'not_read','sha256':'0'*64}))
  with scope(PATHS):
   with self.assertRaisesRegex(ValueError,'R1_MINIMAL_SLICE_BOUND:streams.routing.source_membership'):C.routing_request(c,{'routing_base':c['streams']['routing']})

families=['recovery','absolute_distance','units','coverage_distance','coverage_units','camera_wording','future_extra']
fields=['row_slice_inputs','routing_inputs','row_sources','source_membership','mix','sampling_card','quota_ceiling','population','indices','population_membership']
def case(field,name):
 def test(self):
  c=bound(cfg(),field,name)
  with scope(PATHS),patch.object(C,'EXTRA_PINS',{'future_extra':'1'*64},create=True):
   with self.assertRaisesRegex(ValueError,'R1_MINIMAL_SLICE_BOUND:.*'+name):C.deferred(c,read_pins=True)
  RECORDS.append(dict(field=field,name=name,result='REFUSE'))
 return test
for field in fields:
 for name in families:setattr(MinimalBound,'test_field_'+field+'_'+name,case(field,name))
def request_case(field,name):
 def test(self):
  c=cfg();mut=bound(cfg(),field,name);r={'routing_base':c['streams']['routing']}
  r[field]=mut['r1_training'][field]
  with scope(PATHS):
   with self.assertRaisesRegex(ValueError,'R1_MINIMAL_SLICE_BOUND:request.'+field+':'+name):C.routing_request(c,r)
  RECORDS.append(dict(field='request.'+field,name=name,result='REFUSE'))
 return test
for field in ('row_slice_inputs','routing_inputs','row_sources','source_membership'):
 for name in families:setattr(MinimalBound,'test_request_'+field+'_'+name,request_case(field,name))
if __name__=='__main__':
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(MinimalBound))
 monitor.save(R);J.write(D/'TESTS.json',dict(tests=r.testsRun,failures=len(r.failures),errors=len(r.errors),successful=r.wasSuccessful(),mutations=RECORDS))
 raise SystemExit(not r.wasSuccessful())
