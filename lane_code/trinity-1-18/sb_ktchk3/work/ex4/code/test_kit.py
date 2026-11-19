"""CPU regressions for N propagation, dense-depth state, bars, formatting and resume."""
import os,unittest,tempfile
assert os.environ.get('CUDA_VISIBLE_DEVICES')==''
from common import *
import numpy as np
import metrics,camera

class KitTests(unittest.TestCase):
 def test_served_scale_and_guard(self):
  from evaluate import geometry
  from e2e_reader.geometry import from_arrays
  from student_pilot.geometry_profiles import GeometryError
  pose=np.zeros((32,9));pose[:,6]=1;pose[:,7:]=1;pose[:,0]=np.arange(32)*.01
  tw=dict(raw_pose=pose,anchor_slots=np.arange(32),frame_indices=np.arange(32),depth_grid=np.ones((32,51,51)),depth_conf_grid=np.linspace(0,1,32*51*51).reshape(32,51,51),grid_uv=np.linspace(0,1000,51),source_hw=[480,640])
  own=dict(depth=np.ones((32,51,51))*1.234567891,gravity=np.array([0.,1.,0.]))
  g,raw=geometry(tw,own)
  self.assertEqual(g.contract.scale,float(torch.tensor(float(np.log(raw)),dtype=torch.float32).exp()))
  self.assertNotEqual(g.contract.scale,raw)
  # Serving accepts the opposing up convention but retains finite-intrinsic validation.
  bad=np.array(g.K);bad[0,0,0]=np.nan
  with self.assertRaises(GeometryError):from_arrays(K=bad,canvas_to_source=g.A,camera_to_world=g.contract.camera_to_world,scale=g.contract.scale,depth_grid=tw['depth_grid'],grid_uv=tw['grid_uv'],anchor_frame_indices=np.arange(32))
 def test_no_object_variant_single_gain(self):
  from evaluate_v2 import gains_once,arm
  from policy import row_ids
  from unittest.mock import patch
  import evaluate_v2
  self.assertEqual(read_json(ROOT/'configs/KBOX_WINNING_BOX_RULE.json')['status'],'NO_OBJECT_VARIANT')
  ids=sorted(row_ids('train'));rows=[]
  from exclusions import population
  rooms=population()['row_rooms']
  for name,score in [(arm(32,32,'today'),20.),(arm(64,64,'today'),23.)]:
   rows.extend(dict(row_id=i,room=rooms[i],split='train',arm=name,score=score) for i in ids)
  result=gains_once(rows)
  self.assertEqual(result['status'],'OK');self.assertEqual(set(result['gains']),{'added_frame_gain'})
  self.assertEqual(result['gains']['added_frame_gain']['point'],3.)
  self.assertEqual(gains_once(rows[:-1])['status'],'MISSING')
 def test_tower_depth_shapes_preserve_lm(self):
  from student_pilot.tower_read import TowerState
  pose=np.zeros((64,9));pose[:,6]=1;pose[:,7:]=1;indices=np.arange(64);anchors=np.r_[0,np.arange(3,64,2)]
  small=np.ones((32,51,51));big=np.ones((64,51,51))
  a=TowerState(pose,small,small,indices,anchors)
  b=TowerState(pose,big,big,indices,anchors,depth_slots=indices)
  self.assertEqual(a.depth_grid.shape,(32,51,51));self.assertEqual(b.depth_grid.shape,(64,51,51));self.assertEqual(len(b.anchor_slots),32)
  with self.assertRaises(Exception):TowerState(pose,big,big,indices,anchors)
 def test_geometry64_and_printed32(self):
  from e2e_reader.geometry import from_tower
  from student_pilot.routed_features import Geometry
  from replay import make_session,printed_frames
  p=np.zeros((64,9));p[:,6]=1;p[:,7:]=1.;p[:,0]=np.arange(64)*-.01
  grid=np.ones((64,51,51))*2;g=from_tower(p,np.arange(64),np.arange(64),grid,np.linspace(0,1000,51),[0,-1,0],1,(480,640))
  self.assertTrue(g.has(64));self.assertFalse(g.has(65));self.assertEqual(len(Geometry(g,64).frames),64)
  self.assertEqual(printed_frames([1,2,64],[0,*range(3,64,2)]),[1,32])
  masks=np.zeros((64,20,20),bool);masks[[0,63],5:15,5:15]=True
  # A varying depth surface ensures a nondegenerate box.
  grid[:]=2+np.linspace(0,.3,51)[None,:,None]
  g=from_tower(p,np.arange(64),np.arange(64),grid,np.linspace(0,1000,51),[0,-1,0],1,(480,640))
  s=make_session(g,lambda name:[dict(instance_id='fixture',masks=masks)],list(np.r_[0,np.arange(3,64,2)]))
  text=s.execute('<ground obj="fixture" mode="box">');self.assertIn('frames 1,32',text);self.assertNotIn('64',text.splitlines()[0])
 def test_empty_values_and_nonanchor_refusal(self):
  from student_pilot.routed_candidates import empty_values,values_for
  self.assertEqual(empty_values(1,64)['mask'].shape[1],64)
  self.assertEqual(values_for(['missing'],{},64)['uv'].shape,(1,64,2))
  from e2e_reader.geometry import from_tower
  from replay import make_session
  pose=np.zeros((64,9));pose[:,6]=1;pose[:,7:]=1
  grid=np.ones((64,51,51))*2+np.linspace(0,.3,51)[None,:,None]
  geo=from_tower(pose,np.arange(64),np.arange(64),grid,np.linspace(0,1000,51),[0,-1,0],1,(480,640))
  masks=np.zeros((64,20,20),bool);masks[1,5:15,5:15]=True
  session=make_session(geo,lambda name:[dict(instance_id='fixture',masks=masks)],[0,*range(3,64,2)])
  self.assertIn('not seen',session.execute('<ground obj="fixture" mode="box">'))
 def test_camera_formatter(self):self.assertEqual(camera.synthetic()['status'],'PASS')
 def test_camera_parity_gate(self):self.assertEqual(camera.parity([])['status'],'BLOCKER')
 def test_scale_bridge(self):self.assertEqual(camera.ratio_scale(3,np.ones((32,51,51))*4,np.ones((32,51,51))*2),6.)
 def test_room_bootstrap_identity_and_weighting(self):
  rows=[dict(room='a',delta=2),dict(room='a',delta=2),dict(room='b',delta=-1)]
  a=metrics.paired(rows);b=metrics.paired(rows);self.assertEqual(a,b);self.assertEqual(a['point'],1.)
  z=metrics.paired([dict(room='a',delta=0),dict(room='b',delta=0)]);self.assertEqual([z['point'],z['low'],z['high']],[0,0,0])
 def test_bars(self):
  self.assertTrue(metrics.a_bars([],[])['part_B_runs'])
  self.assertEqual(metrics.b_bar([dict(split='train',room=str(i),delta=2) for i in range(4)])['status'],'PASS')
  with self.assertRaises(AssertionError):metrics.b_bar([dict(split='heldout',room='h',delta=100)])
  with self.assertRaises(AssertionError):metrics.a_bars([dict(split='heldout')],[])
  self.assertEqual(metrics.c_bar([])['status'],'REPORT_ONLY')
 def test_scale_is_median_of_ratios(self):
  from e2e_reader.stage1 import median_ratio
  d=np.array([1.,2.,100.,1.,1.,1.]);own=np.array([1.,8.,200.,1.,1.,1.]);conf=np.array([1.,2.,3.,0.,0.,0.])
  self.assertEqual(median_ratio(d,conf,own),2.)
  self.assertNotEqual(float(np.median(own[:3])/np.median(d[:3])),2.)
 def test_r0_one_look(self):
  import policy,uuid
  from unittest.mock import patch
  root=ROOT/'runtime'/('one_look_'+uuid.uuid4().hex);(root/'configs').mkdir(parents=True)
  data=root/'fixture.json';data.write_text('{"fixture_only":true}')
  frozen=dict(status='FROZEN',selection_split='K1_train',categories={'distance':['base','treatment']},input_files={data.name:sha(data)})
  (root/'configs/PRIMARY_ARMS.json').write_text(json.dumps(frozen))
  with patch.object(policy,'ROOT',root):
   self.assertTrue(policy.read_r0dev_once('distance',data)['fixture_only'])
   with self.assertRaises(FileExistsError):policy.read_r0dev_once('distance',data)
 def test_heldout_requires_decision_and_consumes_once(self):
  import policy,uuid
  from unittest.mock import patch
  root=ROOT/'runtime'/('heldout_'+uuid.uuid4().hex);(root/'out/tower_frames').mkdir(parents=True)
  decision=root/'out/tower_frames/DECISION.json';decision.write_text('{"train_complete":false}')
  with patch.object(policy,'ROOT',root):
   with self.assertRaises(ValueError):policy.consume_heldout()
   decision.write_text('{"train_complete":true}');policy.consume_heldout()
   with self.assertRaises(FileExistsError):policy.consume_heldout()
 def test_context_factors(self):
  from evaluate_v2 import arm
  self.assertEqual(arm(64,32,'today'),'C64_V32_today')
  with self.assertRaises(AssertionError):arm(32,64,'today')
 def test_shared_ledger_budget(self):
  import budget,uuid
  from unittest.mock import patch
  root=ROOT/'runtime'/('budget_'+uuid.uuid4().hex);(root/'inbox').mkdir(parents=True)
  ledger_path=root/'ledger.json';code={'fixture':'only'}
  reservation=dict(id='fixture',part='tower_B',workspace=str(root),code_sha256=digest(code),hard_seconds=10800,card='0',status='RESERVED')
  ledger=dict(order=budget.ORDER,next_authorized_part='tower_B',completed=[dict(gpu_seconds=14*3600)],reservations=[reservation])
  def write():
   ledger_path.write_text(json.dumps(ledger))
   (root/'inbox/SHARED_GPU_RESERVATION.json').write_text(json.dumps(dict(ledger_path=str(ledger_path),ledger_sha256=sha(ledger_path),reservation_id='fixture')))
  write()
  with patch.object(budget,'ROOT',root),patch.object(budget,'code_pins',lambda:code),patch.dict(os.environ,{'CUDA_VISIBLE_DEVICES':'0'}):
   with self.assertRaises(AssertionError):budget.admit('B',{'hard_seconds':{'B':10800}})
   ledger['completed']=[dict(gpu_seconds=12*3600)];write()
   self.assertEqual(budget.admit('B',{'hard_seconds':{'B':10800}})['reservation_id'],'fixture')
   with self.assertRaises(FileExistsError):budget.admit('B',{'hard_seconds':{'B':10800}})
 def test_resume_hashes(self):
  p=ROOT/'out/test_fixture_resume';p.mkdir(exist_ok=True);(p/'value.txt').write_text('fixture')
  finish(p,{'part':'fixture'},['value.txt'],0)
  self.assertTrue(done_valid(p,{'part':'fixture'}));self.assertFalse(done_valid(p,{'part':'other'}))
  (p/'value.txt').write_text('corrupt');self.assertFalse(done_valid(p,{'part':'fixture'}))
 def test_raw_name_filter(self):
  from replay import cached_detections
  cache=dict(phrases=['chairs'],frames={'0':dict(phrases={'chairs':dict(presence=1.,instances=[dict(score=.99,source_prompt='chair',source_presence=1.,mask=dict(size=[1,1],counts=[0,1])),dict(score=.8,source_prompt='chairs',source_presence=.5,mask=dict(size=[1,1],counts=[0,1]))])})})
  got=cached_detections(cache,'chairs',1);self.assertEqual(len(got[0]),1);self.assertEqual(got[0][0]['presence'],.5)
 def test_direction_uses_reader(self):
  from student_pilot.head_programs import hp_answer
  text=camera.synthetic()['outputs']['<move from=1 to=2>']
  self.assertEqual(hp_answer('camera_movement_direction',['A. Left','B. Right','C. Forward'],text),'B')
 def test_pose_sign_lifting_arm_and_camera_license(self):
  pose=[dict(capture='p',split='train',G32=dict(move_mra=.2,short_displacement_mra=.3),G64=dict(move_mra=.4,short_displacement_mra=.5))]
  distance=[dict(room='r',split='train',arm='A2',delta=3.),dict(room='r',split='train',arm='today',delta=-7.)]
  bars=metrics.a_bars(pose,distance)
  self.assertEqual(bars['context_pays_pose'],'PASS');self.assertAlmostEqual(bars['move_mra']['train']['point'],20.)
  self.assertEqual(bars['lifting']['train']['point'],3.)
  pose[0]['G64']=dict(move_mra=.1,short_displacement_mra=.1)
  bars=metrics.a_bars(pose,distance)
  self.assertEqual(bars['context_pays_pose'],'FAIL');self.assertEqual(bars['reader_C64_licensed'],'FAIL')
 def test_update_discards_placeholder_and_retains_bars(self):
  import evaluate_v2 as E,uuid
  from unittest.mock import patch
  root=ROOT/'runtime'/('decision_'+uuid.uuid4().hex);root.mkdir(parents=True)
  write_json(root/'DECISION.json',dict(status='MISSING',bars=dict(added_frame_gain='MISSING')))
  with patch.object(E,'OUT',root):
   E.update('A',dict(context_pays_pose='FAIL'),True)
   E.update('B',dict(added_frame_gain=dict(status='OK',verdict='PASS',low=1.)),True)
   d=read_json(root/'DECISION.json')
   self.assertNotIn('status',d);self.assertEqual(set(d['bars']),{'A','B'})
   self.assertEqual(d['bars']['A']['context_pays_pose'],'FAIL')
   self.assertEqual(d['bars']['B']['added_frame_gain']['verdict'],'PASS');self.assertTrue(d['train_complete'])
 def test_heldout_labels_guard(self):
  import evaluate_v2 as E
  from unittest.mock import patch
  with patch.object(E,'_HELDOUT_ACTIVE',False),patch.object(E,'read_json',return_value={'rows':[]}) as read,patch.object(E,'row_ids',return_value=set()):
   with self.assertRaisesRegex(ValueError,'heldout_once'):E.labels('heldout')
   read.assert_not_called()
 def run_a_fixture(self,stored=None):
  import evaluate_v2 as E,uuid
  from unittest.mock import patch
  from contextlib import ExitStack
  root=ROOT/'runtime'/('run_a_'+uuid.uuid4().hex);root.mkdir(parents=True)
  from process_guard import freeze
  freeze(root,'A')
  c=dict(canonical='fixture/no_convert',room='fixture',k1_split='train',gt={'path':str(root/'gt.npz')})
  tw=dict(raw_pose=np.zeros((1,9)),anchor_slots=np.array([0]),depth_grid=np.ones((1,2,2)),depth_conf_grid=np.arange(4).reshape(1,2,2))
  own=dict(depth=np.ones((1,2,2)),gravity=np.array([0.,1.,0.]))
  np.savez(root/'tower.npz',**tw);np.savez(root/'own.npz',**own)
  np.savez(root/'gt.npz',c2w=np.eye(4)[None],depth=np.ones((1,2,2)),valid=[True]);c['gt']['sha256']=sha(root/'gt.npz')
  write_json(root/'candidates.json',{})
  if stored is not None:np.savez(root/'geometry.npz',scale=stored)
  dense=dict(tw,context=64)
  def pricing(c,g,**kw):return [dict(row_id='row',room='fixture',split='train',prediction=2. if g==32 else 1.)]
  mocks=dict(decision_rows=lambda rows:rows,OUT=root,labels=lambda split:{'row':1.},captures=lambda split:[c],row_ids=lambda split:{'row'},capdir=lambda *a:root,stored_tower=lambda c:dense,geometry=lambda tw,own:(tw.get('context',32),1.),price=pricing,winning_box=lambda context:None,emit=lambda *a,**k:None,items_file=lambda *a:None)
  with ExitStack() as stack:
   for name,value in mocks.items():stack.enter_context(patch.object(E,name,value))
   stack.enter_context(patch.object(E.metrics,'c2w_pose',lambda x:x))
   stack.enter_context(patch.object(E.metrics,'poses',lambda *a:dict(move_mra=.5,short_displacement_mra=.5)))
   stack.enter_context(patch.object(E.metrics,'depth_metrics',lambda *a:{}))
   result=E.run_a()
  return result,read_json(root/'DECISION.json'),read_json(root/'A_SCALE.json')
 def test_run_a_no_geometry_and_a2_direction(self):
  result,decision,scale=self.run_a_fixture()
  self.assertTrue(result['complete']);self.assertEqual(result['missing'],[])
  self.assertEqual(result['scales'][0]['status'],'NO_CONVERT_EXPORT')
  self.assertIsNone(scale['agreement_fraction']);self.assertEqual(scale['stored_rule'],'MISSING')
  self.assertEqual(decision['bars']['A']['lifting']['status'],'PASS')
  self.assertGreater(decision['bars']['A']['lifting']['train']['point'],0.)
 def test_run_a_asserts_convert_scale(self):
  with self.assertRaisesRegex(AssertionError,'scale disagrees'):self.run_a_fixture(stored=2.)
 def test_run_b_persists_added_frame_gain(self):
  import evaluate_v2 as E,uuid
  from unittest.mock import patch
  from process_guard import freeze
  for status,low,want in [('OK',2.,'PASS'),('OK',0.,'FAIL'),('MISSING',None,'MISSING')]:
   root=ROOT/'runtime'/('gain_'+uuid.uuid4().hex);root.mkdir(parents=True);freeze(root,'B')
   gain=dict(status=status,low=low)
   with patch.object(E,'OUT',root),patch.object(E,'labels',return_value={}),patch.object(E,'captures',return_value=[]),patch.object(E,'row_ids',return_value={'absent'}),patch.object(E,'emit'),patch.object(E,'items_file'),patch.object(E,'gains_once',return_value=dict(gains={'added_frame_gain':gain})),patch.object(E,'a_train_rows',return_value=[]):
    E.run_b()
   d=read_json(root/'DECISION.json');self.assertEqual(d['bars']['B']['added_frame_gain']['verdict'],want)
 def test_dense_best_uses_remapped_anchor_areas(self):
  from e2e_reader.geometry import from_tower
  from replay import make_session
  pose=np.zeros((64,9));pose[:,6]=1;pose[:,7:]=1.;pose[:,0]=np.arange(64)*-.01
  grid=np.ones((64,51,51))*2+np.linspace(0,.3,51)[None,:,None]
  geo=from_tower(pose,np.arange(64),np.arange(64),grid,np.linspace(0,1000,51),[0,-1,0],1,(480,640))
  masks=np.zeros((64,20,20),bool);masks[0,5:10,5:10]=True;masks[63,5:15,5:15]=True
  session=make_session(geo,lambda name:[dict(instance_id='fixture',masks=masks)],[0,*range(3,64,2)])
  text=session.execute('<ground obj="fixture" mode="box">')
  self.assertIn('frames 1,32',text);self.assertIn('best 32',text)
 def test_part_c_requires_standalone_da3_go(self):
  import runner,uuid
  from unittest.mock import patch
  root=ROOT/'runtime'/('preflight_'+uuid.uuid4().hex);(root/'inbox').mkdir(parents=True)
  code={'fixture':'code'}
  def read(path):
   if path.name=='GPU_GO.json':return dict(status='GO',parts=['C'],code_sha256=digest(code))
   if path.name=='DRYRUN.json':return dict(status='PASS',code_sha256=digest(code))
   return {}
  (root/'inbox/GPU_GO.json').write_text('fixture')
  with patch.object(runner,'ROOT',root),patch.object(runner,'read_json',side_effect=read),patch.object(runner,'code_pins',return_value=code),patch('camera_records.frame_binding',return_value={'status':'PASS'}):
   for contents in (None,'NOT GO','GO pending'):
    if contents is not None:(root/'inbox/DA3_GO.txt').write_text(contents)
    with self.assertRaisesRegex(PermissionError,'DA3_GO.txt'):runner.preflight('C')
   (root/'inbox/DA3_GO.txt').write_text('  GO  \n');self.assertEqual(runner.preflight('C'),{})
 def test_halted_before_admission_and_not_admitted_receipt(self):
  import runner,uuid
  from unittest.mock import patch
  root=ROOT/'runtime'/('admission_'+uuid.uuid4().hex);root.mkdir(parents=True)
  write_json(root/'HALTED_A.json',dict(reason='fixture'))
  with patch.object(runner,'OUT',root),patch('budget.admit') as admit:
   with self.assertRaisesRegex(RuntimeError,'HALTED'):runner.admit_ready('A',{})
   admit.assert_not_called()
   admit.side_effect=AssertionError('budget exhausted')
   self.assertIsNone(runner.admit_ready('B',{}))
   r=read_json(root/'NOT_ADMITTED_B.json');self.assertEqual(r['status'],'NOT_ADMITTED');self.assertTrue(r['skipped'])
 def test_compare_requires_complete_row_set(self):
  import kbox_hook
  from unittest.mock import patch
  with patch.object(kbox_hook,'evidence',return_value=([dict(capture='c',row_id='missing')],{})):
   with self.assertRaisesRegex(AssertionError,'row set'):kbox_hook.compare({'canonical':'c'},[])
 def test_missing_heldout_does_not_consume(self):
  import evaluate_v2 as E,policy,uuid
  from unittest.mock import patch
  root=ROOT/'runtime'/('heldout_missing_'+uuid.uuid4().hex)
  write_json(root/'out/tower_frames/DECISION.json',dict(train_complete=True))
  missing=Path('/scratch/jjyeung/orch_n30/sb_kbox2/heldout_labels.json')
  self.assertFalse(missing.is_file(),'This regression binds the missing box-kit label input')
  self.assertFalse((ROOT/'out/looks/HELDOUT_once.json').exists())
  from process_guard import freeze
  freeze(root/'out/tower_frames','H')
  with patch.object(E,'OUT',root/'out/tower_frames'),patch.object(policy,'ROOT',root),patch.object(E,'run_a') as a,patch.object(E,'run_b') as b:
   with self.assertRaisesRegex(FileNotFoundError,'held-out look not consumed'):E.heldout_once()
   a.assert_not_called();b.assert_not_called()
  self.assertFalse((root/'out/looks/HELDOUT_once.json').exists())
  self.assertFalse((ROOT/'out/looks/HELDOUT_once.json').exists())
 def test_24gb_ampere_policy(self):
  from runner import validate_card
  for mem in (24_000_000_000,48_000_000_000,80_000_000_000):validate_card(mem,(8,0))
  with self.assertRaisesRegex(ValueError,'24 GB'):validate_card(23_999_999_999,(8,0))
  with self.assertRaisesRegex(ValueError,'Ampere'):validate_card(80_000_000_000,(7,5))
 def test_vendored_backend_gpu_policy_without_gpu(self):
  from geo_bakeoff.backends import Backend
  import geo_bakeoff.backends as B
  from unittest.mock import patch
  from types import SimpleNamespace
  for memory,cap,ok in [(24_000_000_000,(8,0),True),(80_000_000_000,(9,0),True),(23_999_999_999,(8,0),False),(80_000_000_000,(7,5),False)]:
   with patch.object(B,'validate_device'),patch.object(torch.cuda,'get_device_properties',return_value=SimpleNamespace(total_memory=memory)),patch.object(torch.cuda,'get_device_capability',return_value=cap),patch.object(torch.cuda,'set_per_process_memory_fraction') as frac,patch.object(Backend,'load') as load:
    if ok:
     Backend('da3','cuda');frac.assert_called_once_with(min(1.,40_000_000_000/memory));load.assert_called_once()
    else:
     with self.assertRaises(RuntimeError):Backend('da3','cuda')
     load.assert_not_called()
  self.assertTrue(Path(B.__file__).is_relative_to(ROOT/'code/vendor'))
 def test_five_exclusions_and_withheld_planted_row(self):
  from exclusions import authority,check_row,population,decision_rows
  pop=population();self.assertEqual(pop['decision_rows'],1012);self.assertEqual(pop['full_rows'],1037)
  self.assertEqual(len(pop['excluded']),6);self.assertEqual(sum(len(c['row_ids']) for c in pop['excluded']),25)
  for name,rooms in authority()[2].items():
   room=next(r for r in sorted(rooms) if r.startswith('scannet/'))
   row=dict(dataset='scannet',scene=room.split('/')[1]+'_99')
   self.assertIn(name,check_row(row)['hits'])
  rows=[dict(row_id=i,room=room,split='train') for i,room in pop['row_rooms'].items()]
  self.assertEqual({r['row_id'] for r in decision_rows(rows)},set(pop['allowed_row_ids']))
  poses=[dict(capture=c,room=r,split='train') for c,r in pop['capture_rooms'].items()]
  self.assertEqual(len(decision_rows(poses)),233)
  with self.assertRaisesRegex(ValueError,'Unresolved'):check_row(dict(dataset='scannet',scene='invented'))
 def test_withheld_rows_cannot_flip_gains(self):
  from exclusions import population
  from evaluate_v2 import gains_once,arm
  pop=population();allowed=set(pop['allowed_row_ids']);rows=[]
  for i,room in pop['row_rooms'].items():
   rows.append(dict(row_id=i,room=room,split='train',arm=arm(32,32,'today'),score=0.))
   rows.append(dict(row_id=i,room=room,split='train',arm=arm(64,64,'today'),score=-1. if i in allowed else 100.))
  gain=gains_once(rows)
  self.assertEqual(gain['gains']['added_frame_gain']['n_items'],1012)
  self.assertEqual(gain['gains']['added_frame_gain']['point'],-1.)
  self.assertGreater(gain['full_1037_report_only']['gains']['added_frame_gain']['point'],0.)
 def guard_refusal(self,condition):
  import subprocess,uuid
  from process_guard import freeze,directory
  for part in 'ABCH':
   with self.subTest(part=part,condition=condition):
    root=ROOT/'runtime'/('guard_'+uuid.uuid4().hex)
    freeze(root,part)
    folder=directory(root,part)
    if condition=='missing':(folder/'BARS.json').rename(root/'preserved_bars.json')
    if condition=='planted':(folder/'per_item_scores.jsonl').write_text('{"planted":true}\n')
    if condition=='altered':(folder/'BARS.json').write_text('{}')
    before={str(p.relative_to(root)):p.read_bytes() for p in root.rglob('*') if p.is_file()}
    call={'A':'E.run_a()','B':'E.run_b()','C':'E.run_c()','H':'E.heldout_once()'}[part]
    script="import sys;sys.path.insert(0,'code');from pathlib import Path;import evaluate_v2 as E,evaluate as V,camera_pricing as C;E.OUT=V.OUT=C.OUT=Path(sys.argv[1]);"+call
    result=subprocess.run([sys.executable,'-B','-c',script,str(root)],cwd=ROOT,capture_output=True,text=True)
    self.assertNotEqual(result.returncode,0,result.stdout)
    self.assertIn('REFUSE:',result.stderr)
    self.assertIn({'planted':'per-item score file','missing':'missing frozen bars','altered':'sha256 differs'}[condition],result.stderr)
    after={str(p.relative_to(root)):p.read_bytes() for p in root.rglob('*') if p.is_file()}
    self.assertEqual(before,after,'Refused scoring wrote output')
 def test_process_planted_per_item_refuses_without_output(self):self.guard_refusal('planted')
 def test_process_missing_bars_refuses_without_output(self):self.guard_refusal('missing')
 def test_process_altered_bars_refuses_without_output(self):self.guard_refusal('altered')
 def test_freeze_is_first_file_and_resumes_unchanged(self):
  import uuid
  from unittest.mock import patch
  from process_guard import freeze,require_score,directory
  for part in 'ABCH':
   root=ROOT/'runtime'/('freeze_'+uuid.uuid4().hex);writes=[];original=Path.open
   def opening(path,mode='r',*args,**kwargs):
    if any(c in mode for c in 'wax+'):writes.append(path)
    return original(path,mode,*args,**kwargs)
   with patch.object(Path,'open',opening):freeze(root,part)
   self.assertEqual([p.name for p in writes],['BARS.json','FREEZE.json'])
   before={p.name:p.read_bytes() for p in directory(root,part).iterdir()}
   freeze(root,part);require_score(root,part)
   self.assertEqual(before,{p.name:p.read_bytes() for p in directory(root,part).iterdir()})
 def test_freeze_refuses_existing_model_output(self):
  import uuid
  from process_guard import freeze,directory
  for part,unit in [('A','A'),('B','B'),('C','C32'),('C','C64')]:
   root=ROOT/'runtime'/('late_freeze_'+uuid.uuid4().hex);model=root/'captures'/unit/'capture/tower.npz'
   model.parent.mkdir(parents=True);model.write_bytes(b'fixture')
   with self.assertRaisesRegex(RuntimeError,'model output exists'):freeze(root,part)
   self.assertFalse(directory(root,part).exists())
 def test_runner_freezes_before_preflight(self):
  import runner,uuid
  from unittest.mock import patch
  from process_guard import require_score
  for part in 'ABC':
   root=ROOT/'runtime'/('runner_freeze_'+uuid.uuid4().hex)
   def preflight(p):require_score(root,p);raise PermissionError('fixture stop before GPU')
   with patch.object(runner,'OUT',root),patch.object(runner,'preflight',preflight),patch.object(sys,'argv',['runner.py',part]):
    with self.assertRaisesRegex(PermissionError,'fixture stop'):runner.main()
   self.assertFalse((root/'captures').exists())
 def test_process_legacy_per_item_refuses(self):
  import uuid
  from process_guard import freeze,require_score
  for part in 'ABCH':
   root=ROOT/'runtime'/('legacy_scores_'+uuid.uuid4().hex);freeze(root,part)
   path=root/'PER_ITEM.jsonl';path.write_text('{"score":1}\n')
   with self.assertRaisesRegex(RuntimeError,'per-item score file'):require_score(root,part)
   self.assertEqual(path.read_text(),'{"score":1}\n')
 def test_process_missing_receipt_and_changed_code_refuse(self):
  import uuid
  from unittest.mock import patch
  import process_guard as G
  for part in 'ABCH':
   root=ROOT/'runtime'/('receipt_'+uuid.uuid4().hex);G.freeze(root,part)
   with patch.object(G,'code_pins',return_value={'changed':'code'}):
    with self.assertRaisesRegex(RuntimeError,'code differs'):G.require_score(root,part)
   (G.directory(root,part)/'FREEZE.json').rename(root/'preserved_freeze.json')
   with self.assertRaisesRegex(RuntimeError,'missing frozen bars'):G.require_score(root,part)
 def test_item_writer_refuses_overwrite_and_preserves_other_parts(self):
  import evaluate,uuid
  from unittest.mock import patch
  from process_guard import freeze,directory,require_score
  root=ROOT/'runtime'/('items_'+uuid.uuid4().hex)
  for part in 'ABCH':freeze(root,part)
  with patch.object(evaluate,'OUT',root):
   for part in 'ABCH':
    require_score(root,part);evaluate.items_file([dict(row_id='fixture',score=0)],part,'fixture')
    path=directory(root,part)/f'PER_ITEM_{part}_fixture.jsonl';before=path.read_bytes()
    with self.assertRaisesRegex(RuntimeError,'per-item score file'):evaluate.items_file([],part,'fixture')
    self.assertEqual(path.read_bytes(),before)

if __name__=='__main__':
 from test_fix3 import Fix3Tests,PROBES
 suite=unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromTestCase(c) for c in (KitTests,Fix3Tests)])
 result=unittest.TextTestRunner(verbosity=2).run(suite)
 for p in (ROOT/'work/ktchk_probes').glob('*'):
  if p.is_file():sha(p)
 write_json(ROOT/'out/FIX3_PROBES.json',dict(status='PASS' if result.wasSuccessful() else 'FAIL',probes=PROBES,command='bash scripts/cpu.sh code/test_kit.py'))
 code_pins();write_json(ROOT/'out/TESTS.json',dict(status='PASS' if result.wasSuccessful() else 'FAIL',tests=result.testsRun,failures=len(result.failures),errors=len(result.errors)));sys.exit(not result.wasSuccessful())
