"""Focused CPU checks for pin refusals and faithful native materialization."""
import base64,copy,hashlib,json,os,sqlite3,unittest
from pathlib import Path

def folder(name):
 p=Path(os.environ['R2_PROOFS'])/name;p.mkdir(parents=True,exist_ok=True);return p

class InputEdges(unittest.TestCase):
 def test_staging_inline_multipart_and_runtime_pins(self):
  from launch_r2.input_check import sources
  p=folder('input_edges');a=p/'first';b=p/'second';a.write_bytes(b'first');b.write_bytes(b'second')
  sha=lambda raw:hashlib.sha256(raw).hexdigest()
  archive=dict(parts=[str(a),str(b)],sha256=sha(b'firstsecond'),inventory={'member':sha(b'body')})
  plan=dict(entries={'one':dict(archive=archive,member='member',sha256=sha(b'body')),
       'two':dict(archive=archive,member='member',sha256=sha(b'body')),
       'inline':dict(payload=base64.b64encode(b'inline').decode(),sha256=sha(b'inline'))},
       bwrap=dict(file=str(a),sha256=sha(b'first')),venv=dict(file=str(b),sha256=sha(b'second')))
  self.assertEqual(sources(plan),dict(sources=1,members=2,status='PASS'))
  changes=[('inline',dict(entries={'bad':dict(payload=base64.b64encode(b'inline').decode(),sha256='0'*64)})),
           ('unpinned',dict(entries={'bad':{}})),
           ('inventory',dict(entries={'bad':dict(archive={**archive,'inventory':{}},member='member',sha256=sha(b'body'))})),
           ('runtime',dict(entries={},venv=dict(file=str(a),sha256='0'*64)))]
  for name,bad in changes:
   with self.subTest(name=name),self.assertRaises(ValueError):sources(bad)

 def test_input_contract_edges(self):
  from student_pilot import b7_inputs as I
  from tests.test_r2_build7 import settings
  cfg=settings()
  for bad in (None,{},dict(artifact_id='x',sha256='a'*64,location='relative'),dict(artifact_id='x',sha256='a'*64,location='/tmp')):
   with self.assertRaises(ValueError):I.pin(bad)
  with self.assertRaisesRegex(ValueError,'stage_pinned'):I.pin(dict(artifact_id='x',sha256='a'*64,location='gs://fixture/a'),verify=True)
  for update in ({'max_pixels':0},{'min_pixels':999999999},{'frame_count':33},{'frame_count':True}):
   with self.assertRaises(ValueError):I.layout({**cfg,**update})
  for update in ({'training_objective':'rl'},{'minority_count':0},{'weight_scale':float('nan')},
                 {'gf1_cache_option':dict(enabled=True,dtype='float32',root='relative')}):
   with self.assertRaises(ValueError):I.validate({**cfg,**update},'a0')
  for stores in ({},dict(vqa=[],routing=[])):
   with self.assertRaises(ValueError):I.row_stores(stores,'a0')
  bad=copy.deepcopy(cfg['row_stores']);bad['routing'][0]['artifact_id']='other'
  with self.assertRaisesRegex(ValueError,'d0_v5'):I.row_stores(bad,'a0')
  manifest=folder('input_edges')/'manifest.json';manifest.write_text(json.dumps(dict(stream='vqa')))
  from student_pilot.p3_provenance import file_pin
  with self.assertRaisesRegex(ValueError,'manifest_bindings_missing'):I.bound_manifests(cfg,[],'a0')
  cfg['row_stores']['vqa'][0]['manifests']=[file_pin(manifest)]
  cfg['row_stores']['vqa'][1]['manifests']=[file_pin(manifest)]
  with self.assertRaisesRegex(ValueError,'bound_twice'):I.bound_manifests(cfg,[],'a0')
  cfg['row_stores']['vqa'][0]['manifests']=[file_pin(manifest)]
  manifest.write_text(json.dumps(dict(stream='routing')))
  cfg['row_stores']['vqa'][0]['manifests']=[file_pin(manifest)]
  with self.assertRaisesRegex(ValueError,'stream_mismatch'):I.bound_manifests(cfg,[],'a0')

 def test_type_gate_and_response_negative_cases(self):
  from student_pilot.routing_type_gate import refusal,sample,validate
  from student_pilot.carrier_c1_routing import POLICIES
  from student_pilot import response_spec as S
  policy=POLICIES['both-path-20261116']
  self.assertEqual(refusal('object_counting','unknown',policy),'unknown_answer_form')
  with self.assertRaisesRegex(ValueError,'unknown_answer_form'):validate(dict(question_type='object_counting',answer_form='unknown'),policy,[])
  row=dict(qid='same',question_type='object_counting',answer_form='direct')
  for rows,count,total in (([row],0,8),([row,row],2,8),([row],2,4),([{**row,'answer_form':'bad'}],2,8)):
   with self.assertRaises(ValueError):sample(rows,policy,{'object_counting':'direct'},{'object_counting':total},count)
  text='<tool_response>turn = +45 deg</tool_response>'
  record=S.check(text)
  self.assertEqual(S.format_response(record),text)
  for bad in ('body','<tool_response>unregistered text</tool_response>'):
   with self.assertRaises(ValueError):S.parse(bad)
  with self.assertRaisesRegex(ValueError,'response_version'):S.format_response({**record,'version':'other'})
  with self.assertRaisesRegex(ValueError,'response_fields'):S.format_response({**record,'kind':'move'})

class FaithfulRows(unittest.TestCase):
 def row(self,kind='camera_displacement'):
  import numpy as np
  from generator.derivgen_v7.derivgen.camera_rows import _row,_Geometry
  codes=np.tile([0.,0.,0.,0.,0.,0.,1.,.8,1.],(32,1))
  for i in range(32):
   angle=(i/24)*np.pi/4;distance=i/24
   codes[i,:3]=[-np.cos(angle)*distance,0.,-np.sin(angle)*distance]
   codes[i,3:7]=[0.,-np.sin(angle/2),0.,np.cos(angle/2)]
  clip=dict(dataset='d1',scene='fixture_clean',recording_id='fixture',frames=[dict(source_index=i) for i in range(32)],
       gt_pose9=codes.tolist(),gt_up=[0.,-1.,0.],
       rgb_manifest=dict(path='fixture-only',sha256='a'*64))
  values=_Geometry(clip).pair(1,25)
  return _row(clip,kind,1,25,values)

 def test_native_encoder_keeps_reasoning_after_own_response(self):
  import numpy as np
  import torch
  from student_pilot import h1_faithful as H,carrier_c1_routing as R
  from tests.test_r2_data_path import TinyProcessor
  raw=self.row();processor=TinyProcessor()
  row=dict(routing=raw,student_input=dict(question=raw['question'],options=raw['options']),target=raw['target'])
  target,spans,segments=R.render_full(raw['events'],raw['answer'])
  ids,train,offsets=R.suffix_tokens(processor,row,target,spans)
  batch=dict(input_ids=torch.tensor([[2,5]+ids]),labels=torch.tensor([[-100,-100]+ids]),
             attention_mask=torch.ones((1,2+len(ids)),dtype=torch.long))
  batch,_=R.finish(batch,ids,train,row,target,spans,'gt',offsets,segments)
  own=np.array(raw['gt_pose9']);own[:,:3]*=2
  _,target,spans,segments=H.faithful(raw,R.OwnGeometry(own,raw['gt_up'],None))
  enabled,on_audit=R.encode_own(processor,row,batch,target,spans,segments,'own',faithful=True)
  disabled,off_audit=R.encode_own(processor,row,batch,target,spans,segments,'own',faithful=False)
  _,train,offsets=R.suffix_tokens(processor,row,target,spans)
  cut=spans[0]['end']-len(R.THINK);start=int(enabled['aux_suffix_start'][0])
  after=[start+i for i,((a,b),keep) in enumerate(zip(offsets,train)) if keep and a>=cut]
  self.assertTrue(after)
  self.assertTrue(all(enabled['labels'][0,i]!=-100 for i in after))
  self.assertTrue(all(disabled['labels'][0,i]==-100 for i in after))
  self.assertGreater(on_audit['trained_tokens'],off_audit['trained_tokens'])
  (folder('faithful')/'MASKS.json').write_text(json.dumps(dict(
      enabled_trainable_after_response=len(after),disabled_trainable_after_response=0,
      own_target_sha256=hashlib.sha256(target.encode()).hexdigest(),
      real_functions=['camera_rows._row','h1_faithful.faithful','routing.encode_own','routing.finish'],
      stand_in='TinyProcessor at the unavailable pretrained processor boundary'),indent=2)+'\n')

 def test_native_readout_runs_even_when_local_row_is_refused(self):
  from student_pilot import h1_faithful as H
  from tests.test_carrier_c1 import fixture
  model,batch,_=fixture();row=self.row();runs=[]
  class Rows:
   h1={}
   def row(self,stream,index):
    if index:raise H.MaterializeRefusal('fixture_missing_row')
    return {'routing':row},{}
  with model.register_forward_hook(lambda *args:runs.append('readout')):
   same,audit=H.own_values(model,Rows(),batch,{},0,(False,False),'cpu')
   self.assertIs(same,batch);self.assertFalse(audit['h1']['any_rank_refused']);self.assertEqual(runs,[])
   same,audit=H.own_values(model,Rows(),batch,{},1,(True,False),'cpu')
   self.assertIs(same,batch);self.assertEqual(runs,['readout'])
   self.assertEqual(audit['h1']['refused'],'fixture_missing_row');self.assertTrue(audit['h1']['any_rank_refused'])
   same,audit=H.own_values(model,Rows(),batch,{},0,(True,False),'cpu')
   self.assertIs(same,batch);self.assertFalse(audit['h1']['any_rank_refused']);self.assertEqual(len(runs),2)

 def test_real_producer_materializer_and_identity_receipts(self):
  from student_pilot import h1_faithful as H,carrier_c1_routing as R
  from student_pilot.p3_provenance import file_pin
  rows=[self.row(),self.row('camera_rotation')]
  for row in rows:
   result,target,spans,segments=H.faithful(row,R.RecordedGeometry(row))
   self.assertEqual(target,row['target']);self.assertEqual(result['answer'],row['answer'])
   self.assertTrue(spans);self.assertTrue(segments)
  import numpy as np
  own=np.array(rows[0]['gt_pose9']);own[:,:3]*=2
  changed,target,_,_=H.faithful(rows[0],R.OwnGeometry(own,rows[0]['gt_up'],None))
  self.assertEqual(changed['answer'],'2.00');self.assertIn('2.00 m',target)
  self.assertEqual(rows[0]['answer'],'1.00')
  p=folder('faithful');source=p/'rows.jsonl';source.write_text(''.join(json.dumps(r)+'\n' for r in rows))
  pin=file_pin(source);cfg=dict(h1={'faithful_own_camera_rows':True},streams={'routing':pin},preparation_output=str(p))
  receipt=H.prepare_identity({},cfg)
  self.assertTrue(receipt['h1_faithful_identity']['passes']);H.require_identity(receipt,cfg)
  self.assertEqual(receipt['h1_faithful_identity']['rows'],2)
  (p/'IDENTITY.json').write_text(json.dumps(receipt,indent=2)+'\n')
  for name,value in (('list',rows),('row',rows[0]),('database',dict(database=pin)),('streams',dict(streams={'routing':{'receipt':pin}}))):
   path=p/(name+'.json');path.write_text(json.dumps(value))
   self.assertEqual(list(H.identity_rows(path)),rows if name!='row' else rows[:1])
  path=p/'rows.sqlite'
  with sqlite3.connect(path) as db:
   db.execute('CREATE TABLE IF NOT EXISTS rows(i INTEGER PRIMARY KEY,row TEXT)')
   for i,row in enumerate(rows):db.execute('INSERT OR REPLACE INTO rows VALUES (?,?)',(i,json.dumps(row)))
  self.assertEqual(list(H.identity_rows(path)),rows)
  packed=dict(routing=copy.deepcopy(rows[0]),student_input=dict(question=rows[0]['question'],options=[]),target=rows[0]['target'])
  self.assertEqual(H.canonical_row(packed)['target'],rows[0]['target'])
  direction=self.row('camera_movement_direction')
  direction={k:v for k,v in direction.items() if k not in ('margin_m','margin_rel','frame_pair_rule','frame_pair_turn')}
  restored=H.canonical_row(direction)
  self.assertEqual(restored['margin_m'],1.);self.assertEqual(restored['margin_rel'],1.)
  self.assertEqual(restored['frame_pair_rule'],'frame_gap');self.assertEqual(restored['frame_pair_turn'],[])
  broken=copy.deepcopy(rows[0]);broken['events']=[];bad_source=p/'bad_rows.jsonl';bad_source.write_text(json.dumps(broken)+'\n')
  cfg['streams']['routing']=file_pin(bad_source)
  with self.assertRaisesRegex(ValueError,'95%'):H.prepare_identity({},cfg)
  self.assertTrue((p/'receipt.json').is_file())
  self.assertEqual(H.prepare_identity({'fixture':True},dict(h1={})),{'fixture':True})
  self.assertEqual(H.identity_check([dict(question_type='room')])['rows'],0)

 def test_faithful_validation_and_printed_refusals(self):
  from student_pilot import h1_faithful as H
  cfg=dict(h1={'faithful_own_camera_rows':True},scheduled_sampling=dict(max_own_probability=.5,force_from_step=1))
  H.validate(cfg)
  for bad in ({**cfg,'h1':{'faithful_own_camera_rows':True,'camera_types':['bad']}},
              {**cfg,'scheduled_sampling':{'max_own_probability':0.,'force_from_step':1}}):
   with self.assertRaises(ValueError):H.validate(bad)
  self.assertTrue(H.camera(self.row(),{}));self.assertFalse(H.camera({'question_type':'room'},{}))
  for name in ('move','turn','pose'):
   row=dict(events=[dict(kind='tool_response',call_id='c1',name=name)])
   with self.assertRaises(H.MaterializeRefusal):H.printed_camera(row,'bad',[dict(call_id='c1',start=0,end=3)])
  self.assertTrue(H.answer_differs('camera_movement_direction','A','B'))
  self.assertTrue(H.answer_differs('camera_displacement','2','1'))
  self.assertFalse(H.answer_differs('camera_rotation','-179','179'))
  self.assertTrue(H.answer_differs('camera_rotation','45','0'))
  with self.assertRaises(ValueError):H.answer_differs('camera_displacement','nan','1')
  with self.assertRaises(ValueError):H.answer_differs('unknown','1','2')

class StopFallback(unittest.TestCase):
 def test_native_step_boundary_checkpoint_export_and_reload(self):
  import torch
  from unittest.mock import patch
  from student_pilot import carrier_c1_run as run
  from student_pilot.carrier_c1 import parameter_groups
  from student_pilot.p3_provenance import file_pin
  from tests.test_carrier_c1 import fixture
  from tests.test_carrier_c1_memory import PoseRows
  from tests.test_c1_blockers import transport
  output=folder('stop_fallback');bound=dict(fixture='single_cpu_rank')
  cfg=dict(training_mode='pose_only',depth_enabled=False,trace_program_version='3.13',
           base_identity='tiny-fixture',steps=3,milestones=[],stop_after_step=1,
           schedule=dict(startup_seconds=0,p95_step_seconds=1,checkpoint_seconds=1,export_seconds=1))
  model,_,_=fixture(4,training_mode='pose_only',depth_enabled=False)
  optimizer=torch.optim.AdamW(parameter_groups(model));rows=PoseRows()
  run.bind_output(output,bound)
  # Synthetic pose batches feed the native loop; one-rank collective transport
  # and FSDP state gathering stand in. This does not qualify the wrapper chain.
  with transport(),patch('student_pilot.fsdp_training.publication_state',side_effect=lambda wrapped:wrapped.state_dict()), \
       patch.dict(os.environ,{'K3':str(output/'absent.stop'),'R1_STOP_FILE':str(output/'absent.stop')}):
   result=run.run_steps(model,model,optimizer,rows,{'pose':9},output,cfg,bound,
                        torch.device('cpu'),distributed=False)
  self.assertEqual(result['last_step'],1);self.assertEqual(len(result['steps']),1)
  self.assertTrue(result['stopped_for_resume'])
  artifact=file_pin(output/'m1/artifact.json')
  checkpoint=run.complete_states(output,bound)
  self.assertEqual(len(checkpoint),1)
  fresh,batch,target=fixture(4,training_mode='pose_only',depth_enabled=False)
  run.load_artifact(fresh,artifact)
  self.assertTrue(fresh.eval().probe(batch,target)['finite'])
  proof=dict(last_step=result['last_step'],artifact=artifact,checkpoint=file_pin(checkpoint[0]),
       real_functions=['run_steps','optimize_step','checkpoint','export','load_artifact'],
       stand_ins=['native tiny model fixture','PoseRows synthetic patch-batch provider',
                  'one-rank collective transport','FSDP full-state collection'],
       limitation='Single CPU rank with fixture batches; this is not a GPU-boundary-only producer/wrapper proof and does not prove multi-rank Gloo.')
  (output/'RESULT.json').write_text(json.dumps(proof,indent=2)+'\n')
