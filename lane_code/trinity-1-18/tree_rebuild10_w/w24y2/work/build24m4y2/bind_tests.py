from pathlib import Path
import importlib.util,json,os,sys,unittest
from unittest.mock import patch
from common import L,D,kit,NAMES,write
import student_pilot
import time
F=D/('bind_checks_'+str(time.time_ns()));F.mkdir()
class BindTests(unittest.TestCase):
 def test_missing_sources_refuse_before_launch(self):
  for name in NAMES:
   sp=importlib.util.spec_from_file_location('sc_'+name,kit(name)/'b/sc.py');sc=importlib.util.module_from_spec(sp);sp.loader.exec_module(sc)
   for kind in ('source','scratch','kit','closure','pythonpath','trainer','dangling'):
    with self.subTest(kit=name,kind=kind):
     folder=F/(name+'_'+kind);folder.mkdir();scratch=folder/'i';scratch.mkdir();missing=folder/'absent'
     sources={};k=kit(name);env={};patches=[]
     if kind=='source':sources={'a'*64:str(missing)}
     if kind=='scratch':scratch=missing
     if kind=='kit':k=missing
     if kind=='closure':env['ANYHOST_JOBS']=str(missing)
     if kind=='pythonpath':env['PYTHONPATH']=str(missing)
     if kind=='trainer':patches.append(patch.object(student_pilot,'__file__',str(missing/'student_pilot/__init__.py')))
     if kind=='dangling':
      link=folder/'link';link.symlink_to(missing);sources={'a'*64:str(link)}
     from contextlib import ExitStack
     with ExitStack() as stack:
      stack.enter_context(patch.dict(os.environ,env,clear=True))
      for context in patches:stack.enter_context(context)
      run=stack.enter_context(patch.object(sc.subprocess,'run'))
      with self.assertRaisesRegex(ValueError,'^R1_SCENE_BIND_SOURCE_MISSING:'):
       sc.bind({},sources,scratch,folder/'q',k)
      run.assert_not_called()
      self.assertFalse((scratch/'sc').exists())
 def test_actual_commands_and_imports(self):
  result=json.loads((D/'REAL_PATH_TESTS.json').read_bytes())
  for record in result['records']:
   access=record['access'];self.assertEqual(len(access['compare_calls']),40)
   self.assertEqual(set(access['readonly'].values()),{30})
   self.assertTrue(all(v['result']=='PASS' for v in access['compare_calls']))
   for cmd in record['inner_commands']:
    writable=[cmd[i+1:i+3] for i,v in enumerate(cmd) if v=='--bind']
    self.assertEqual(len(writable),1);self.assertTrue(writable[0][0].endswith('/i/sc'))
    self.assertEqual(cmd[-1],str(Path(access['trainer']).parent.parent))
    self.assertNotIn('/tmp/q_22c714e1/z/s',cmd)
  self.assertEqual({r['mode'] for r in result['records']},{'q','r'})
  before=json.loads((L/'work/build24m4t/BEFORE.json').read_bytes())
  self.assertFalse(before['state']['z_s_exists']);self.assertTrue(before['state']['z_exists'])
  self.assertIn("Can't find source path /tmp/q_22c714e1/z/s",before['stderr'])
if __name__=='__main__':
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(BindTests))
 write(D/'BIND_TESTS.json',dict(status='PASS' if r.wasSuccessful() else 'FAIL',tests=r.testsRun,missing_source_cases=28,failures=len(r.failures),errors=len(r.errors)))
 raise SystemExit(not r.wasSuccessful())
