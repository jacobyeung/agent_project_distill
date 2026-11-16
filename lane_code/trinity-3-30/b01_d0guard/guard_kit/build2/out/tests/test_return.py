from pathlib import Path
import sys,unittest,uuid
from unittest.mock import patch
B=Path(__file__).resolve().parents[2];sys.path.insert(0,str(B/'out/guard_kit'))
import pool
from transport import archive_result,verify_return
from guard_core import write,sha,read
class Returns(unittest.TestCase):
 def setUp(self):
  self.d=B/'work/return_tests'/uuid.uuid4().hex;self.d.mkdir(parents=True)
 def test_fresh_pool(self):
  with patch.object(pool,'POOL',self.d):
   pool.reserve(self.d,'e'*16)
   with self.assertRaises(FileExistsError):pool.reserve(self.d,'e'*16)
 def test_pool_quota(self):
  with patch.object(pool,'POOL',self.d),patch.object(pool,'POOL_LIMIT',10):
   with self.assertRaisesRegex(ValueError,'quota'):pool.reserve(self.d,'e'*16)
 def test_pool_readback(self):
  source=self.d/'PROOF.json';write(source,dict(status='PASS'))
  with patch.object(pool,'POOL',self.d):
   pool.reserve(self.d,'e'*16);r=pool.publish(self.d,'e'*16,source)
  self.assertEqual(r['sha256'],sha(source))
 def result(self,fixture=False,changed=False):
  source=self.d/'result';source.mkdir();plan='f'*64
  write(source/'R1.json',dict(arms={'unflagged':[]},expected_keys=[]))
  write(source/'COMPLETE.json',dict(plan_sha256=plan,fixture=fixture))
  write(source/'PROOF.json',dict(status='PASS',fixture=fixture,backend_identity_proven=not fixture))
  write(source/'CANARY.json',dict(status='PASS',fixture=fixture))
  write(source/'IN_JOB_ADMISSION.json',dict(status='PASS',fixture=fixture,bundle=dict(sha256='0'*64 if changed else sha(source/'R1.json'))))
  r=archive_result(source,self.d/'return',plan,fixture)
  return r,self.d/'return/result.tar.gz',plan
 def test_return_binds_admission(self):verify_return(*self.result())
 def test_changed_bundle_refused(self):
  with self.assertRaisesRegex(ValueError,'bundle differs'):verify_return(*self.result(changed=True))
 def test_fixture_cannot_admit_production(self):
  with self.assertRaisesRegex(ValueError,'authority'):verify_return(*self.result(fixture=True))
if __name__=='__main__':
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Returns))
 write(B/'out/RETURN_TESTS.json',dict(tests=r.testsRun,failures=len(r.failures),errors=len(r.errors),status='PASS' if r.wasSuccessful() else 'FAIL'))
 sys.exit(not r.wasSuccessful())
