from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import ast,base64,hashlib,importlib.util,json,os,runpy,shutil,subprocess,sys,unittest
L=Path(__file__).resolve().parents[2];D=L/'work/build24c'
sys.path[:0]=[str(D),str(L/'work/build24'),str(L/'work/build21'),str(L/'work/tree_r1')]
import joblib as J
from runtime import shell,harden_kit
from launch_r1.build import verify
from student_pilot.source_seal import inventory

class Runtime24c(unittest.TestCase):
 def test_sealed_tree_and_configs_identical(self):
  self.assertEqual(inventory(L/'work/tree_r1'),J.load(L/'work/build24b/TREE_FILES.json'))
  for name in ('q','n'):
   k=L/'work/build24/kits'/name;old=L/'attic/build24c'/('kit_'+name)
   for p in (k/'k').iterdir():
    if p.name!='j.json':self.assertEqual(p.read_bytes(),(old/'k'/p.name).read_bytes())
   self.assertEqual((k/'b/g.py').read_bytes(),(old/'b/g.py').read_bytes())
   self.assertEqual(J.load(k/'k/a.json')['source']['tree_sha256'],'e1e64652087c2cde689620e4fb6edca57123feccae78c8a0a4b70ce8f7b35c10')
   self.assertFalse(J.load(k/'k/a.json')['GO']);self.assertFalse(J.load(k/'BUILD.json')['GO'])
   verify(k)
 def test_resolver_semantics_identical(self):
  before=ast.parse((L/'attic/build24c/work/build24/joblib.py').read_text());after=ast.parse((L/'work/build24/joblib.py').read_text())
  before={n.name:ast.dump(n,include_attributes=False) for n in before.body if isinstance(n,ast.FunctionDef)}
  after={n.name:ast.dump(n,include_attributes=False) for n in after.body if isinstance(n,ast.FunctionDef)}
  self.assertEqual(set(before),set(after))
  self.assertEqual([k for k in before if before[k]!=after[k]],['launch_shell'])
 def test_all_shell_starts_and_scheduler_directives(self):
  for name in ('q','n'):
   k=L/'work/build24/kits'/name
   s=(k/'job.sh').read_text();self.assertLess(s.rindex('#SBATCH'),s.index('export '))
   self.assertIn('#SBATCH --output=/tmp/q_%j.log',s)
   self.assertIn('cd "$N"',s)
   self.assertGreaterEqual(len(J.load(D/('STARTS_'+name+'.json'))),31)
   for p in k.rglob('*.sh'):subprocess.run(['/bin/bash','-n',str(p)],check=True)
 def test_generator_integration(self):
  for name in J.load(D/'CHANGES.json')['generators']:
   s=(L/name).read_text();self.assertIn('harden_kit(',s);ast.parse(s)
  self.assertIn("module.main()",(L/'work/build24/kit.py').read_text())
 def test_generator_reproduces_both_final_kits(self):
  from patch import reseal
  for name in ('q','n'):
   target=D/'generated'/name;target.parent.mkdir(exist_ok=True)
   shutil.copytree(L/'attic/build24c'/('kit_'+name),target,dirs_exist_ok=True)
   harden_kit(target);seal=reseal(target)
   self.assertEqual(seal,J.seal(L/'work/build24/kits'/name))
   self.assertEqual({str(p.relative_to(target)):J.sha(p) for p in target.rglob('*') if p.is_file()}, {str(p.relative_to(L/'work/build24/kits'/name)):J.sha(p) for p in (L/'work/build24/kits'/name).rglob('*') if p.is_file()})
 def test_bootstrap_environment(self):
  with patch.object(J.subprocess,'run',return_value=SimpleNamespace(returncode=0)) as run:
   J.launch_shell('j.sh','node','kit','ns','home','job')
  self.assertEqual(run.call_args.kwargs['env']['PYTHONDONTWRITEBYTECODE'],'1')
 def test_distributed_launcher_explicit_worker_python(self):
  k=L/'work/build24/kits/n'
  spec=importlib.util.spec_from_file_location('z',k/'b/z.py');z=importlib.util.module_from_spec(spec);spec.loader.exec_module(z)
  original=z.load
  with patch.dict(sys.modules,z=z),patch.object(z,'load',side_effect=lambda p:{'GO':True} if Path(p)==k/'k/a.json' else original(p)),patch.object(sys,'argv',[str(k/'b/t.py'),'node','cfg']),patch.object(subprocess,'run',return_value=SimpleNamespace(returncode=0)) as run:
   with self.assertRaises(SystemExit) as error:runpy.run_path(str(k/'b/t.py'),run_name='__main__')
  self.assertEqual(error.exception.code,0);cmd=run.call_args.args[0]
  self.assertEqual(cmd[:5],[sys.executable,'-s','-B','-m','torch.distributed.run'])
  self.assertIn('--no-python',cmd);self.assertIn('/bin/bash',cmd);self.assertIn(str(k/'b/e.sh'),cmd)
  self.assertEqual(run.call_args.kwargs['env']['PYTHONDONTWRITEBYTECODE'],'1')
 def test_worker_refuses_GO_and_cannot_write_kit(self):
  k=L/'work/build24/kits/n';before={str(p.relative_to(k)):J.sha(p) for p in k.rglob('*') if p.is_file()}
  r=subprocess.run(['/bin/bash',str(k/'b/e.sh'),sys.executable,'node','cfg'],capture_output=True,text=True,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'0'})
  self.assertNotEqual(r.returncode,0);self.assertIn('E03',r.stderr)
  self.assertEqual(before,{str(p.relative_to(k)):J.sha(p) for p in k.rglob('*') if p.is_file()});verify(k)
 def test_hardener_idempotent(self):
  for name in ('q','n'):
   k=D/'sequence'/name/'kit'
   before={str(p.relative_to(k)):J.sha(p) for p in k.rglob('*') if p.is_file()}
   harden_kit(k)
   self.assertEqual(before,{str(p.relative_to(k)):J.sha(p) for p in k.rglob('*') if p.is_file()})
 def test_regression_sequence_evidence(self):
  for value in J.load(D/'BEFORE.json').values():self.assertEqual(value['error'],'R1_KIT_CONTENT_DIFFERS')
  for name,value in J.load(D/'SEQUENCE.json').items():
   self.assertEqual(value['status'],'PASS');self.assertTrue(value['staging_unchanged']);self.assertTrue(value['pipeline_unchanged'])
   self.assertEqual(value['production_kit_seal'],J.seal(L/'work/build24/kits'/name))
if __name__=='__main__':
 hits=set();tracked=str(D/'runtime.py')
 def trace(frame,event,arg):
  if event=='line' and frame.f_code.co_filename==tracked:hits.add(frame.f_lineno)
  return trace
 sys.settrace(trace)
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Runtime24c))
 sys.settrace(None)
 nodes=ast.parse((D/'runtime.py').read_text())
 statements={n.lineno for top in nodes.body if isinstance(top,ast.FunctionDef) for n in ast.walk(top) if isinstance(n,ast.stmt) and not isinstance(n,ast.FunctionDef)}
 J.write(D/'COVERAGE.json',dict(source='work/build24c/runtime.py',scope='Executable statements in the external kit hardener; exact generated programs execute in the decoded-sequence regression',total=len(statements),covered=len(statements & hits),missing=sorted(statements-hits),hits=sorted(hits)))
 J.write(D/'RUNTIME_TESTS.json',dict(tests=r.testsRun,successful=r.wasSuccessful(),failures=len(r.failures),errors=len(r.errors)))
 raise SystemExit(not r.wasSuccessful())
