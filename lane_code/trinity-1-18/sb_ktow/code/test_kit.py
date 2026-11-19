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
 def test_camera_formatter(self):self.assertEqual(camera.synthetic()['status'],'PASS')
 def test_camera_parity_gate(self):self.assertEqual(camera.parity([])['status'],'BLOCKER')
 def test_scale_bridge(self):self.assertEqual(camera.ratio_scale(3,np.ones((32,51,51))*4,np.ones((32,51,51))*2),6.)
 def test_room_bootstrap_identity_and_weighting(self):
  rows=[dict(room='a',delta=2),dict(room='a',delta=2),dict(room='b',delta=-1)]
  a=metrics.paired(rows);b=metrics.paired(rows);self.assertEqual(a,b);self.assertEqual(a['point'],1.)
  z=metrics.paired([dict(room='a',delta=0),dict(room='b',delta=0)]);self.assertEqual([z['point'],z['low'],z['high']],[0,0,0])
 def test_bars(self):
  self.assertEqual(metrics.a_bars([],[])['run_64_arms'],'MISSING')
  rows=[dict(type=t,room=str(i),delta=d) for i in range(4) for t,d in [('camera_displacement',3),('camera_rotation',-1),('camera_movement_direction',-1)]]
  self.assertEqual(metrics.c_bar(rows)['status'],'PASS')
  rows[-1]['delta']=-1.1;self.assertEqual(metrics.c_bar(rows)['status'],'FAIL')
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
