from pathlib import Path
from copy import deepcopy
from unittest.mock import patch
import ast,base64,json,runpy,sys,unittest
L=Path(__file__).resolve().parents[2];D=L/'work/build24e';O=D/'launch_tests';O.mkdir(exist_ok=True)
sys.path[:0]=[str(L/'work/build24'),str(L/'work/tree_r1')]
import joblib as J
from launch_r1.build import verify
class Launch(unittest.TestCase):
 def setUp(self):
  self.k=L/'work/build24/kits/n';self.r=O/'p';(self.r/'q').mkdir(parents=True,exist_ok=True)
  self.cfg=J.load(self.k/'k/n.json');self.pin=J.write(O/'config.json',self.cfg)
  J.write(self.r/'q/RESULT.json',dict(status='ADMIT',init_milestone=400,config=self.pin))
 def invoke(self):
  with patch.object(sys,'argv',[str(self.k/'b/h.py'),str(self.r),str(O/'v.json')]):runpy.run_path(str(self.k/'b/h.py'),run_name='__main__')
 def test_before_no_v_producer(self):
  k=L/'attic/build24d/work/build24/kits/n';s=base64.b64decode(J.load_raw(k/'k/j.json')['payload']).decode()
  self.assertIn('"$Q_NS/v.json"',s);self.assertNotIn('b/h.py',s)
  self.assertFalse((k/'b/h.py').exists())
  with self.assertRaises(FileNotFoundError):J.load(O/'never_created/v.json')
 def test_after_authenticated_config_is_written(self):
  self.invoke();self.assertEqual(J.load(O/'v.json'),self.cfg)
 def test_bad_canary_refuses(self):
  for q in (dict(status='REFUSE',init_milestone=400),dict(status='ADMIT',init_milestone=600)):
   J.write(self.r/'q/RESULT.json',q)
   with self.assertRaisesRegex(ValueError,'E81'):self.invoke()
 def test_bad_pin_refuses(self):
  J.write(self.r/'q/RESULT.json',dict(status='ADMIT',init_milestone=400,config=dict(self.pin,sha256='0'*64)))
  with self.assertRaisesRegex(ValueError,'E10'):self.invoke()
 def test_wrong_policy_or_world_refuses(self):
  for key in ('policy','world'):
   cfg=deepcopy(self.cfg)
   if key=='policy':cfg['r1_training'].pop('init_policy')
   else:cfg['world_size']=8
   J.write(self.r/'q/RESULT.json',dict(status='ADMIT',init_milestone=400,config=J.write(O/'bad.json',cfg)))
   with self.assertRaisesRegex(ValueError,'E85'):self.invoke()
 def test_shell_order_and_go_false(self):
  s=base64.b64decode(J.load_raw(self.k/'k/j.json')['payload']).decode()
  self.assertLess(s.index('b/h.py'),s.index('b/t.py'));self.assertLess(s.index('b/t.py'),s.index('b/o.py'))
  self.assertIn('rc=${PIPESTATUS[0]}\nif [[ "$rc" == 0 ]]; then',s)
  with patch.object(sys,'argv',[str(self.k/'b/t.py')]),patch('subprocess.run',side_effect=AssertionError('unexpected process')):
   with self.assertRaises(SystemExit) as e:runpy.run_path(str(self.k/'b/t.py'),run_name='__main__')
  self.assertEqual(e.exception.code,0)
 def test_go_copy_only_expected_files_differ(self):
  go=L/'out/kit_n_go';dif=[str(p.relative_to(go)) for p in go.rglob('*') if p.is_file() and p.read_bytes()!=(self.k/p.relative_to(go)).read_bytes()]
  self.assertEqual(sorted(dif),['BUILD.json','SHA256SUMS.txt','k/a.json']);verify(go);verify(self.k)
  self.assertTrue(J.load(go/'k/a.json')['GO']);self.assertFalse(J.load(self.k/'k/a.json')['GO'])
if __name__=='__main__':
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Launch))
 J.write(D/'LAUNCH_TESTS.json',dict(tests=r.testsRun,successful=r.wasSuccessful(),errors=len(r.errors),failures=len(r.failures)))
 raise SystemExit(not r.wasSuccessful())
