import os
from pathlib import Path
import sys
import unittest
import uuid
B=Path(__file__).resolve().parents[2];sys.path.insert(0,str(B/'out/guard_kit'))
from guard_core import read,write,sha
from transport import Publisher
from worker import child,coordinate
sys.path.insert(0,str(Path(__file__).parent))
from stage_fixture import stage_fixture
class Processes(unittest.TestCase):
 def setUp(self):
  self.d=B/'work/process_tests'/uuid.uuid4().hex;self.d.mkdir(parents=True)
  self.pub=Publisher(dict(kind='local',root=str(self.d/'store')),'c'*16,self.d/'pub')
 def command(self,role):return [sys.executable,'-I','-s','-B',str(B/'out/tests/phase_fixture.py'),'--role',role,'--out',str(self.d)]
 def test_fresh_process_and_early_receipt(self):
  proof=child(self.command('proof'),dict(os.environ),self.d,self.pub,'proof',10)
  self.assertTrue((self.d/'store'/('c'*16)/'PROOF.json').is_file())
  candidate=child(self.command('candidate'),dict(os.environ),self.d,self.pub,'candidate',10)
  self.assertNotEqual(proof['pid'],candidate['pid'])
  self.assertTrue(read(self.d/'TAIL_STARTED.json')['after_ack'])
  write(B/'out/PROCESS_TEST.json',dict(status='PASS',fixture=True,backend_executed=False,
      proof_pid=proof['pid'],candidate_pid=candidate['pid'],publication=str(self.d/'store'),tail=str(self.d/'TAIL_STARTED.json')))
 def test_proof_failure_stops_before_candidate(self):
  with self.assertRaises(RuntimeError):child(self.command('proof')+['--fail'],dict(os.environ),self.d,self.pub,'proof',10)
  self.assertEqual(read(self.d/'store'/('c'*16)/'PROOF.json')['status'],'FAIL')
  self.assertFalse((self.d/'CANARY.json').exists())
 def test_publication_failure_no_tail(self):
  def fail(p):raise OSError('Fixture publication failure')
  with self.assertRaisesRegex(OSError,'publication failure'):child(self.command('candidate'),dict(os.environ),self.d,fail,'candidate',10)
  self.assertFalse((self.d/'TAIL_STARTED.json').exists())
 def test_coordinator_archives_failed_proof_without_candidate(self):
  commands={role:self.command(role)+(['--fail'] if role=='proof' else []) for role in ('proof','candidate')}
  root=self.d.with_name(self.d.name+'_coordinator');root.mkdir()
  config=dict(stage_fixture(root),plan_sha256='d'*64,gpu_seconds=310)
  result=coordinate(root,config,self.d,self.pub,lambda:commands,dict(os.environ),fixture=True)
  self.assertEqual(result['status'],'FAIL')
  self.assertFalse((self.d/'CANARY.json').exists());self.assertFalse((self.d/'TAIL_STARTED.json').exists())
  self.assertEqual(read(self.d/'store'/('c'*16)/'EXIT.json')['status'],'FAIL')
 def test_coordinator_stage_failure_publishes_failure_receipt(self):
  def fail():raise ValueError('Fixture stage failure')
  root=self.d.with_name(self.d.name+'_coordinator');root.mkdir()
  result=coordinate(root,dict(plan_sha256='e'*64,gpu_seconds=310),self.d,self.pub,fail,dict(os.environ),fixture=True)
  self.assertEqual(result['status'],'FAIL')
  self.assertFalse((self.d/'CANARY.json').exists())
  self.assertFalse(read(self.d/'store'/('c'*16)/'PROOF.json')['candidate_started'])
  self.assertEqual(read(self.d/'store'/('c'*16)/'EXIT.json')['status'],'FAIL')
if __name__=='__main__':
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Processes))
 write(B/'out/PROCESS_TESTS.json',dict(tests=r.testsRun,failures=len(r.failures),errors=len(r.errors),status='PASS' if r.wasSuccessful() else 'FAIL'))
 sys.exit(not r.wasSuccessful())
