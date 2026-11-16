"""Review regression checks; all generated data stays outside operator runs."""
import ast
import difflib
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import tarfile
import sys
import unittest
import uuid
from unittest.mock import patch

B=Path(__file__).resolve().parents[2];K=B/'out/guard_kit'
sys.path[:0]=[str(K),str(Path(__file__).parent)]
from guard_core import read,write,sha
from transport import Publisher,verify_return
from worker import coordinate,report_command,REPORT_SHA256
from stage_fixture import stage_fixture
spec=importlib.util.spec_from_file_location('governed_transfer',B/'out/operator/governed_transfer.py')
gov=importlib.util.module_from_spec(spec);spec.loader.exec_module(gov)

class G4(unittest.TestCase):
 def setUp(self):
  self.d=B/'work/g4_tests'/uuid.uuid4().hex;self.d.mkdir(parents=True)
 def returned(self,proof=True):
  out=self.d/'result';out.mkdir()
  config=dict(stage_fixture(self.d,proof=proof),plan_sha256='e'*64,gpu_seconds=310)
  publisher=Publisher(dict(kind='local',root=str(self.d/'store')),'d'*16,self.d/'publication')
  def phase(command,environment,output,publish,role,timeout):
   self.assertTrue((output/'CANDIDATE_STAGE.json').is_file())
   self.assertTrue((output/'CHECK.json').is_file())
   self.assertEqual((output/'CANDIDATE_STAGE.json').read_bytes(),(self.d/'CANDIDATE_STAGE.json').read_bytes())
   label='PROOF' if role=='proof' else 'CANARY'
   write(output/(label+'.json'),dict(status='PASS',fixture=True))
   publish(output/(label+'.json'))
   if role=='candidate':
    write(output/'R1.json',dict(arms={'unflagged':[]},fixture=True))
    write(output/'IN_JOB_ADMISSION.json',dict(status='PASS',fixture=True,bundle=dict(sha256=sha(output/'R1.json'))))
   return dict(pid=1 if role=='proof' else 2,returncode=0)
  with patch('worker.child',side_effect=phase):
   result=coordinate(self.d,config,out,publisher,lambda:dict(proof=[],candidate=[]),dict(os.environ),fixture=True)
  self.assertEqual(result['status'],'PASS')
  archive=self.d/'store'/('d'*16)/'result.tar.gz'
  receipt=read(archive.with_name('EXIT.json'))
  verify_return(receipt,archive,config['plan_sha256'],allow_fixture=True)
  return receipt,archive,config['plan_sha256']
 def test_rehearsal_shaped_return_carries_stage_and_checker(self):
  receipt,archive,plan=self.returned()
  with tarfile.open(archive) as stream:
   names=set(stream.getnames())
   self.assertTrue({'CANDIDATE_STAGE.json','CHECK.json','step544/STAGING.json',
     'step544/exports/469ddece_m544/RECEIPT.json','step544/exports/469ddece_m544/CHECK.json'}<=names)
  write(B/'out/G4_RETURN_EVIDENCE.json',dict(status='PASS',fixture=True,archive=str(archive),sha256=sha(archive),
        scope='Shared production coordinator and return transport; checkpoint phases are stand-ins.'))
 def test_missing_candidate_receipts_refused_even_with_rehashed_archive(self):
  receipt,archive,plan=self.returned()
  for omitted in ('CANDIDATE_STAGE.json','CHECK.json','STAGE_RECEIPTS.json',
                  'step544/exports/469ddece_m544/CHECK.json'):
   with self.subTest(omitted=omitted):
    mutant=self.d/(omitted.replace('/','_')+'.tar.gz')
    with tarfile.open(archive) as source,tarfile.open(mutant,'w:gz') as target:
     for member in source:
      if member.name!=omitted:target.addfile(member,source.extractfile(member))
    changed=dict(receipt,archive=dict(bytes=mutant.stat().st_size,sha256=sha(mutant)))
    with self.assertRaisesRegex(ValueError,'missing'):verify_return(changed,mutant,plan,allow_fixture=True)
 def test_optional_proof_receipts_may_be_absent_at_staging(self):self.returned(proof=False)
 def test_missing_checker_stops_before_candidate(self):
  out=self.d/'result';out.mkdir()
  write(self.d/'CANDIDATE_STAGE.json',dict(status='complete'))
  publisher=Publisher(dict(kind='local',root=str(self.d/'store')),'c'*16,self.d/'publication')
  with patch('worker.child') as child:
   result=coordinate(self.d,dict(step=50,artifact_sha256='a'*64,plan_sha256='f'*64,gpu_seconds=310),
      out,publisher,lambda:dict(proof=[],candidate=[]),{},fixture=True)
  self.assertEqual(result['status'],'FAIL');child.assert_not_called()
 def test_report_command_binds_config_artifact_and_source(self):
  script=B.parent/'report/guard_read.py'
  with patch('worker.sha',return_value=REPORT_SHA256):
   command=report_command(dict(artifact_sha256='a'*64),script,'candidate','baseline',self.d)
  self.assertEqual(command[command.index('--candidate-artifact')+1],'a'*64)
  self.assertNotIn('--self-pair',command)
  with self.assertRaises(KeyError):report_command({},script,'candidate','baseline',self.d)
  with patch('worker.sha',return_value='0'*64),self.assertRaisesRegex(ValueError,'source pin'):
   report_command(dict(artifact_sha256='a'*64),script,'candidate','baseline',self.d)
 def test_report_source_matches_authorized_pin(self):
  self.assertEqual(sha(B.parent/'report/guard_read.py'),REPORT_SHA256)
 def test_step544_as_candidate_refuses_with_explicit_artifact(self):
  spec=importlib.util.spec_from_file_location('g4_report',B.parent/'report/guard_read.py')
  module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
  fixture=B.parent/'report/tests/fixtures/R1_544_COMPACT.json'
  code=module.main(['--candidate',str(fixture),'--step544',str(fixture),'--candidate-artifact',module.STEP544_ARTIFACT,'--out',str(self.d/'report')])
  self.assertEqual(code,3)
 def test_diff_lists_every_new_production_module(self):
  with tarfile.open(B/'out/code_g2.tar') as archive:
   names={m.name for m in archive if m.name.endswith('.py') and not m.name.startswith(('sj/','reviewed/'))}
  listed=set(re.findall(r'`out/guard_kit/([a-z_]+\.py)`',(B/'out/DIFF.md').read_text()))
  self.assertFalse(names-listed)
 def test_c8r_patch_matches_sealed_archive_and_current_production_bytes(self):
  baseline=B.parent/'build/in_c8r_kit/code_c8r.tar'
  with tarfile.open(baseline) as archive:
   old={str(Path(m.name)):archive.extractfile(m).read() for m in archive if m.isfile()}
  current={name:(K/name).read_bytes() for name in read(B/'out/CODE_MANIFEST.json')['members']}
  patch_text=[]
  for name in sorted(set(old)|set(current)):
   before,after=old.get(name,b''),current.get(name,b'')
   if before!=after:
    patch_text.extend(difflib.unified_diff(before.decode().splitlines(keepends=True),
      after.decode().splitlines(keepends=True),fromfile='C8r/'+name,tofile='G4/'+name))
  self.assertEqual(''.join(patch_text),(B/'out/DIFF_C8R.patch').read_text())
  self.assertEqual((B/'out/DIFF.patch').read_bytes(),(B/'out/DIFF_C8R.patch').read_bytes())
 def test_every_documented_fetch_and_upload_registers(self):
  text=(B/'out/RUN.md').read_text()
  self.assertNotIn('pv -q -L',text);self.assertNotIn('rsync --bwlimit',text)
  lines=[line for line in text.splitlines() if line.startswith('governed_transfer "g4_')]
  self.assertEqual(len(lines),5)
  for name in ('closure','done','exit','return','packet'):
   self.assertTrue(any('g4_${TOKEN}_'+name in line for line in lines))
  for line in text.splitlines():
   if line.startswith('bash ') and any(token in line for token in ('cat /','tar ')):
    self.fail('Ungoverned payload command: '+line)
  command=gov.registration('g4_test',100,101,123)
  for flag in ('--tier','--allow-resume','--io-weight','--member-pid','--rl-pid'):self.assertIn(flag,command)
  self.assertEqual(command[command.index('--tier')+1],'3')
  self.assertEqual(command[command.index('--io-weight')+1],'1')
  self.assertNotIn('--writes-nfs',command)
  self.assertIn('--writes-nfs',gov.registration('g4_nfs',100,101,123,True))
 def test_governor_requires_exact_running_lane(self):
  self.assertTrue(gov.running('| g4_test | node | running (the one serial stream) |','g4_test'))
  for state in ('waiting (position 1)','running_outside','not running'):
   self.assertFalse(gov.running('| g4_test | '+state+' |','g4_test'))
  self.assertFalse(gov.running('| g4_test_other | running |','g4_test'))
 def test_stopped_root_never_execs_and_waits_before_producer(self):
  source=(B/'out/operator/governed_transfer.py').read_text();tree=ast.parse(source)
  func=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='gated_source')
  calls=[ast.unparse(n.func) for n in ast.walk(func) if isinstance(n,ast.Call)]
  self.assertTrue(calls.index('os.kill')<calls.index('wait_running')<calls.index('subprocess.Popen'))
  self.assertFalse(any(name.startswith('os.exec') for name in calls))
  self.assertIn("'.done.'",source)
  self.assertIn("comm.read_text().strip()=='ratelimit'",source)

if __name__=='__main__':
 result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(G4))
 write(B/'out/G4_TESTS.json',dict(tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),status='PASS' if result.wasSuccessful() else 'FAIL'))
 sys.exit(not result.wasSuccessful())
