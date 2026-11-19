"""CPU regressions for N propagation, dense-depth state, bars, formatting and resume."""
import os,unittest,tempfile
assert os.environ.get('CUDA_VISIBLE_DEVICES')==''
from common import *
import numpy as np
import metrics,camera

class KitTests(unittest.TestCase):
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
if __name__=='__main__':
 result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(KitTests))
 code_pins();write_json(ROOT/'out/TESTS.json',dict(status='PASS' if result.wasSuccessful() else 'FAIL',tests=result.testsRun,failures=len(result.failures),errors=len(result.errors)));sys.exit(not result.wasSuccessful())
