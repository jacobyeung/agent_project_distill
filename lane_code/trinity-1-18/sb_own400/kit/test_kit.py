"""CPU-only refusal and commit tests; never invokes nvidia-smi or CUDA."""
import os,sys
os.environ['CUDA_VISIBLE_DEVICES']='';sys.dont_write_bytecode=True
import unittest,tempfile,io,tarfile
from unittest.mock import patch
import numpy as np
from core import *
from score_400 import choose
from runtime import extract

class KitTests(unittest.TestCase):
 def setUp(self):self.p=pathlib.Path(tempfile.mkdtemp(prefix='case_',dir=ROOT/'out/tests'))
 def bind(self):return {'capture_sha256':'c'*64,'checkpoint':{'step':400,'sha256':'d'*64},'anchor_indices':list(range(32)),'synthetic':True,'input_sha256':{str(KIT/'test_kit.py'):sha(KIT/'test_kit.py')}}
 def test_bars_refusal(self):
  (self.p/'SCORE_RESULT.json').write_text('{}')
  with self.assertRaisesRegex(Refusal,'Bars/scoring'):fresh(self.p)
 def test_busy_memory(self):
  with self.assertRaisesRegex(Refusal,'not empty'):idle_card(0,lambda *a,**kw:'GPU-test, 100\n')
 def test_any_users_process(self):
  values=iter(['GPU-test, 0\n','GPU-test, 12345\n'])
  with self.assertRaisesRegex(Refusal,'any user'):idle_card(0,lambda *a,**kw:next(values))
 def test_two_idle_readings_300_seconds(self):
  values=iter(['GPU-test, 1\n','','GPU-test, 2\n','']);slept=[]
  rec=idle_twice(3,sleep=slept.append,query=lambda *a,**kw:next(values));self.assertEqual(slept,[300]);self.assertEqual(len(rec),2)
 def test_second_reading_busy(self):
  values=iter(['GPU-test, 1\n','','GPU-test, 101\n'])
  with self.assertRaises(Refusal):idle_twice(3,sleep=lambda _:None,query=lambda *a,**kw:next(values))
 def test_killed_refusal(self):
  atomic(self.p/'KILLED.json',{'input_sha256':{},'signal':15})
  with self.assertRaisesRegex(Refusal,'KILLED'):relaunch_gate(self.p)
  relaunch_gate(self.p,True)
 def test_wrong_sha(self):
  p=self.p/'input';p.write_bytes(b'changed')
  with self.assertRaisesRegex(Refusal,'Wrong sha'):checked(p,'0'*64)
 def test_skip_matching_done_and_schema(self):
  bind=self.bind();dep=np.ones((32,51,51));commit(self.p,dep,[0,-1,0],bind,.1,0)
  self.assertTrue(skip_done(self.p,bind));r=read(self.p/'PHASE_COMPLETE.json');self.assertEqual(r['units'],'metres');self.assertEqual(r['shape'],[32,51,51]);self.assertIn('input_sha256',r)
 def test_binding_mismatch_refused(self):
  bind=self.bind();commit(self.p,np.ones((32,51,51)),[0,-1,0],bind,.1,0);bad=dict(bind,capture_sha256='e'*64)
  with self.assertRaisesRegex(Refusal,'binding differs'):skip_done(self.p,bad)
 def test_corrupt_done_refused(self):
  bind=self.bind();commit(self.p,np.ones((32,51,51)),[0,-1,0],bind,.1,0);(self.p/'own.npz').write_bytes(b'corrupt')
  with self.assertRaises(Refusal):skip_done(self.p,bind)
 def test_partial_is_not_done(self):
  (self.p/'own.partial.fixture').write_bytes(b'incomplete');self.assertFalse(skip_done(self.p,self.bind()))
 def test_bad_gravity_refused(self):
  with self.assertRaisesRegex(Refusal,'gravity'):commit(self.p,np.ones((32,51,51)),[float('nan')]*3,self.bind(),.1,0)
 def test_missing_runtime_refused(self):
  from launcher import environment
  with patch('pathlib.Path.is_file',return_value=False):
   with self.assertRaisesRegex(Refusal,'MISSING pinned reader runtime'):environment(self.p)
 def test_deadline_between_captures(self):
  from worker import run
  with patch('runtime.authenticate_frames',return_value={}):
   with self.assertRaisesRegex(Refusal,'deadline'):run([{}],None,self.p,{},True,deadline=1)
 def test_bad_grid_refused(self):
  for a in (np.ones((1,51,51)),np.full((32,51,51),np.nan),np.zeros((32,51,51))):
   with self.assertRaises(Refusal):valid_grid(a)
 def test_decision_requires_three_negative_upper_bounds(self):
  neg={'B-A':{'ci95':[-2.,-.1]}};zero={'B-A':{'ci95':[-2.,0.]}}
  self.assertEqual(choose([neg,neg],neg),544)
  self.assertEqual(choose([neg,zero],neg),400)
 def test_archive_path_escape_refused(self):
  archive=self.p/'bad.tar'
  with tarfile.open(archive,'w') as f:
   m=tarfile.TarInfo('../escape');m.size=1;f.addfile(m,io.BytesIO(b'x'))
  with self.assertRaisesRegex(Refusal,'Unsafe'):extract([archive],self.p/'assets')
 def test_stop_between_captures(self):
  from worker import run
  (self.p/'STOP').write_text('stop')
  with patch('runtime.authenticate_frames',return_value={}):
   with self.assertRaisesRegex(Refusal,'STOP'):run([{}],None,self.p,{},True)

if __name__=='__main__':
 (ROOT/'out/tests').mkdir(exist_ok=True)
 for var,name in [('TMPDIR','tmp'),('XDG_CACHE_HOME','cache'),('HF_HOME','hf'),('TORCH_HOME','torch')]:
  q=ROOT/'out/tests'/name;q.mkdir(exist_ok=True);os.environ[var]=str(q)
 write_guard(ROOT/'out')
 suite=unittest.defaultTestLoader.loadTestsFromTestCase(KitTests);r=unittest.TextTestRunner(verbosity=2).run(suite)
 atomic(ROOT/'out/TEST_RESULTS_BASE_B.json',{'input_sha256':{str(p):sha(p) for p in [KIT/'test_kit.py',KIT/'core.py',KIT/'runtime.py',KIT/'worker.py',KIT/'score_400.py',KIT/'launcher.py']},'command':'env OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 CUDA_VISIBLE_DEVICES= nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -B kit/test_kit.py','tests':r.testsRun,'failures':len(r.failures),'errors':len(r.errors),'passed':r.wasSuccessful(),'GPU_calls':0})
 raise SystemExit(not r.wasSuccessful())
