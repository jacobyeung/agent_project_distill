from pathlib import Path
import ast,io,json,os,sys,unittest
from contextlib import redirect_stdout
from types import SimpleNamespace
from unittest.mock import patch
L=Path(__file__).resolve().parents[2];D=L/'work/build24m4/guard_q';K=L/'work/build24/kits/q'
source=(K/'b/g.py').read_text();hits=set();cases=[]
class Fault:
 def __getattr__(self,name):raise RuntimeError('private diagnostic failure')
def run(*,missing=False,failed=None,name='NVIDIA H100 80GB HBM3',env='0',memory=85520809984):
 def read(label,value):
  if failed==label:raise RuntimeError('private diagnostic failure')
  return value
 class Properties:
  @property
  def name(self):return read('name',name)
  @property
  def total_memory(self):return read('memory',memory)
 t=SimpleNamespace(cuda=SimpleNamespace(is_available=lambda:read('available',True),
  device_count=lambda:read('count',1),get_device_properties=lambda i:read('properties',Properties())))
 if not missing:t.__version__='2.11.0+cu129'
 out=io.StringIO();error=None;filename=str(K/'b/g.py')
 def trace(frame,event,arg):
  if event=='line' and frame.f_code.co_filename==filename:hits.add(frame.f_lineno)
  return trace
 envmap={} if env is None else {'CUDA_VISIBLE_DEVICES':env}
 with patch.dict(sys.modules,torch=t),patch.dict(os.environ,envmap,clear=True),redirect_stdout(out):
  real_get=os.environ.get
  with patch.object(os.environ,'get',side_effect=lambda *a:read('environment',real_get(*a))),patch('os.path.exists',side_effect=lambda p:read('d0' if p.endswith('0') else 'dc',True)):
   prior=sys.gettrace();sys.settrace(trace)
   try:exec(compile(source,filename,'exec'),{})
   except Exception as exc:error=type(exc).__name__+':'+str(exc)
   finally:sys.settrace(prior)
 raw=out.getvalue();lines=raw.splitlines();assert len(lines)==1,raw
 diag=json.loads(lines[0]);assert 'private diagnostic failure' not in raw
 cases.append(dict(missing_version=missing,failure=failed,name=name,env=env,memory=memory,error=error,diagnostic=diag))
 return error,diag,raw
class Guard23d(unittest.TestCase):
 def test_absent_version(self):
  err,d,_=run(missing=True);self.assertEqual(err,'RuntimeError:E42');self.assertTrue(d['x']);self.assertIsNone(d['v'])
 def test_all_diagnostic_read_failures(self):
  for label in ('available','count','environment','d0','dc','properties','name','memory'):
   with self.subTest(label=label):
    err,d,_=run(failed=label);self.assertEqual(err,'RuntimeError:E42');self.assertTrue(d['x'])
 def test_environment_is_summary_only(self):
  for text,count in [(None,0),('',0),('0',1),('0,2',2),(',,',3),('/tmp/private-project/model/secret-DEMO',1),('secret\nDEMO,other',2)]:
   with self.subTest(value=text):
    err,d,raw=run(env=text);self.assertIsNone(err);self.assertEqual(d['e'],text is not None);self.assertEqual(d['ec'],count)
    if text and len(text)>2:self.assertNotIn(text,raw)
 def test_device_name_allowlist(self):
  for name in ('NVIDIA H100 80GB HBM3','A._- 09','A'*64):
   err,d,_=run(name=name);self.assertIsNone(err);self.assertEqual(d['n'],name)
 def test_device_name_rejection(self):
  for name in ('','A'*65,'GPU\n','GPU\nsecret','/tmp/private-project/model/secret-DEMO','GÜP',None,123):
   with self.subTest(name=name):
    err,d,raw=run(name=name);self.assertIsNone(err);self.assertEqual(d['n'],'?')
    if isinstance(name,str) and name:self.assertNotIn(name,raw)
 def test_unknown_memory_refuses(self):
  err,d,_=run(memory=None);self.assertEqual(err,'RuntimeError:E42');self.assertTrue(d['x'])
 def test_torch_import_failure(self):
  out=io.StringIO()
  with patch.dict(sys.modules,torch=None),redirect_stdout(out),self.assertRaisesRegex(RuntimeError,'^E42$'):
   exec(compile(source,str(K/'b/g.py'),'exec'),{})
  self.assertTrue(json.loads(out.getvalue())['x'])
 def test_serialization_failure_becomes_E42(self):
  err,d,_=run(memory='not-an-integer');self.assertEqual(err,'RuntimeError:E42');self.assertTrue(d['x'])
result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Guard23d))
statements={n.lineno for n in ast.walk(ast.parse(source)) if isinstance(n,ast.stmt)}
(D/'GUARD_TESTS.json').write_text(json.dumps(dict(successful=result.wasSuccessful(),tests=result.testsRun,cases=cases,changed_statement_lines=sorted(statements),covered=sorted(hits),missing=sorted(statements-hits),stand_in='torch only; diagnostic node checks mocked; no GPU'),indent=2)+'\n')
assert not statements-hits,statements-hits
raise SystemExit(not result.wasSuccessful())
