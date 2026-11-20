"""CPU suite: original refusals plus actual head parity and source isolation."""
import os,sys
os.environ['CUDA_VISIBLE_DEVICES']='';sys.dont_write_bytecode=True
for k in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS'):os.environ[k]='8'
import unittest,tempfile,copy
from unittest.mock import patch
from types import SimpleNamespace as NS
import numpy as np
from core import *
from test_kit import KitTests
from fov_variants import *

class VariantTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  import torch
  torch.set_num_threads(8)
  cls.out=pathlib.Path(tempfile.mkdtemp(prefix='variant_',dir=ROOT/'out/tests'))
  from runtime import code
  cls.src=code(cls.out)
 def test_real_head_pose_path_parity(self):
  import torch
  from student_pilot.point_depth_head import PointDepthHead
  from student_pilot.carrier_c1_decode import HeadState
  from student_pilot import decoupled_v
  torch.manual_seed(88)
  head=PointDepthHead(8,{'d_proj':16,'mlp_hidden':16,'num_heads':2,'context_depth':1},vit_dim=8).eval()
  head.group_embed=torch.nn.Parameter(torch.zeros(32,16))
  # Nonzero FiLM makes an FoV ordering/value error observable.
  torch.nn.init.normal_(head.fov_film[-1].weight,std=.15)
  cap=NS(grids=[torch.randn(32,2,2,8)],vits=[[torch.randn(32,4,4,8) for _ in range(3)]],states=torch.randn(1,32,8))
  fov=torch.stack((torch.linspace(.6,1.1,32),torch.linspace(1.2,1.7,32)),-1)
  pose9=torch.cat((torch.zeros(1,32,7),fov[None]),-1)
  pose=NS(carrier_states=lambda h,p:h,predict_all=lambda *args,**kw:([pose9],[torch.tensor([[0.,-1.,0.]])],None))
  model=NS(auxiliary_heads=NS(pose=pose,depth=NS(auxiliary_heads=NS(camera=NS(point_depth=head)))),depth_fov_source='pose_head')
  uv=torch.rand(32,2601,2)*1000
  with torch.no_grad(),patch.object(decoupled_v,'features',return_value=cap):
   state=HeadState(model,{'aux_camera_positions':torch.arange(32)[None]},torch.zeros(1,32,8))
   expected=head.query(state.depth_map,uv).double().numpy().reshape(32,51,51)
   actual=encode_grid_with_fov(head.encode,head.query,cap,fov,uv)
   swapped=encode_grid_with_fov(head.encode,head.query,cap,fov.flip(-1),uv)
  np.testing.assert_array_equal(expected,actual)
  self.assertGreater(float(np.max(np.abs(actual-swapped))),1e-7)
 def test_shared_pass_and_preserved_base(self):
  import torch
  from cpu_stub import fixture
  b,restore=fixture(self.src,self.out)
  c=read(KIT/'inputs/TRAIN_CAPTURES.json')['captures'][0];grid=NS(grid_uv=np.linspace(0,1000,51,dtype=np.float32));count=[]
  hook=b.model.model.language_model.register_forward_hook(lambda *x:count.append(1))
  try:
   expected,g=b.own(c,[],grid);count.clear()
   actual,g,v=own_with_fov_variants(b,c,[],grid)
   np.testing.assert_array_equal(expected,actual);self.assertEqual(len(count),1);self.assertEqual(v['private_vit_passes'],1)
   self.assertEqual(set(v['depths']),{'V1','V2'});self.assertEqual(set(v['fovs']),{'B','V1','V2'})
   self.assertNotEqual(float(np.mean(v['depths']['V1'])),float(np.mean(v['depths']['V2'])))
  finally:hook.remove();restore()
 def test_variants_are_independent_of_pose_fov(self):
  from cpu_stub import fixture
  b,restore=fixture(self.src,self.out)
  c=read(KIT/'inputs/TRAIN_CAPTURES.json')['captures'][0];grid=NS(grid_uv=np.linspace(0,1000,51,dtype=np.float32))
  pose=b.model.auxiliary_heads.pose;original=pose.predict_all
  try:
   base,_,v=own_with_fov_variants(b,c,[],grid)
   def changed(*args,**kwargs):
    stages,gravity,other=original(*args,**kwargs);stages[-1][...,7:9]=1.5
    return stages,gravity,other
   pose.predict_all=changed
   base2,_,v2=own_with_fov_variants(b,c,[],grid)
   self.assertFalse(np.array_equal(base,base2))
   for arm in ('V1','V2'):np.testing.assert_array_equal(v['depths'][arm],v2['depths'][arm])
  finally:restore()
 def test_missing_private_fov_is_explicit(self):
  from cpu_stub import fixture
  b,restore=fixture(self.src,self.out)
  c=read(KIT/'inputs/TRAIN_CAPTURES.json')['captures'][0];grid=NS(grid_uv=np.linspace(0,1000,51,dtype=np.float32))
  del b.model.auxiliary_heads.depth.fov
  try:
   _,_,v=own_with_fov_variants(b,c,[],grid)
   self.assertIn('MISSING',v['missing']['V1']);self.assertNotIn('V1',v['depths']);self.assertIn('V2',v['depths'])
  finally:restore()
 def test_g3t_anchor_mapping_and_units(self):
  c=read(KIT/'inputs/TRAIN_CAPTURES.json')['captures'][0]
  with np.load(KIT/'inputs/TOWER_ONE.npz') as z:expected=z['raw_pose'][z['anchor_slots'],7:9]
  np.testing.assert_array_equal(g3t_fov(c),expected)
  bad=copy.deepcopy(c);bad['anchor_indices'][0]+=1
  with self.assertRaisesRegex(Refusal,'mismatch'):g3t_fov(bad)
 def test_private_fov_matches_native_forward_formula(self):
  import torch,math
  depth=NS(fov=torch.nn.Linear(4,2));states=torch.randn(1,32,4)
  expected=1e-4+(math.pi-2e-4)*depth.fov(states.float()).sigmoid()
  torch.testing.assert_close(private_fov(depth,NS(states=states)),expected,rtol=0,atol=0)
 def test_invalid_fov_refused(self):
  for a in (np.ones((2,32)),np.full((32,2),90),np.full((32,2),np.nan)):
   with self.assertRaises(Refusal):validate_fov(a)
 def test_environment_wrong_version_and_root_refused(self):
  from launcher import validate_environment
  req=read(KIT/'inputs/ENV_REQUIRED.json');actual={'prefix':req['base_env'],'modules':{k:{'version':v['version'],'path':req['base_env']+'/lib/'+k+'/__init__.py'} for k,v in req['modules'].items()}}
  validate_environment(actual,req)
  bad=copy.deepcopy(actual);bad['modules']['torch']['version']='2.11.0+cu129'
  with self.assertRaisesRegex(Refusal,'version'):validate_environment(bad,req)
  bad=copy.deepcopy(actual);bad['modules']['torch']['path']='/tmp/torch/__init__.py'
  with self.assertRaisesRegex(Refusal,'outside'):validate_environment(bad,req)
 def test_float32_fallback_is_specific(self):
  from cpu_check_228 import bf16_unsupported
  self.assertTrue(bf16_unsupported(RuntimeError('operation not implemented for BFloat16')))
  for message in ('out of memory','invalid shape','unsupported attention mask'):
   self.assertFalse(bf16_unsupported(RuntimeError(message)))
 def test_report_only_variants_and_paired_support(self):
  from score_400b import summarize,choose
  from score_400 import module,S1
  s=module(S1,'test_scale_source')
  records=[{'room':'r','gt':np.array([1.]),'pred':{'A':np.array([1.]),'B':np.array([2.]),'V1':np.array([1.]),'V2':np.array([1.])}},{'room':'r','gt':np.array([1.]),'pred':{'A':np.array([2.]),'B':np.array([1.])}}]
  report=summarize(s,records)
  self.assertEqual(report['V1-A']['points'],0);self.assertEqual(report['V1-B']['points'],100)
  self.assertEqual(choose([report,report],report),400)

if __name__=='__main__':
 (ROOT/'out/tests').mkdir(exist_ok=True)
 for var,name in [('TMPDIR','tmp'),('XDG_CACHE_HOME','cache'),('HF_HOME','hf'),('TORCH_HOME','torch')]:
  p=ROOT/'out/tests'/name;p.mkdir(exist_ok=True);os.environ[var]=str(p)
 write_guard(ROOT/'out')
 suite=unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromTestCase(c) for c in (KitTests,VariantTests)])
 r=unittest.TextTestRunner(verbosity=2).run(suite)
 atomic(ROOT/'out/TEST_RESULTS_B.json',{'input_sha256':{str(p):sha(p) for p in KIT.glob('*.py')},'tests':r.testsRun,'failures':len(r.failures),'errors':len(r.errors),'passed':r.wasSuccessful(),'command':'env OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 CUDA_VISIBLE_DEVICES= nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -B kit/test_400b.py'})
 raise SystemExit(not r.wasSuccessful())
