from pathlib import Path
from contextlib import redirect_stdout
from unittest.mock import patch
from types import SimpleNamespace
import ast,io,json,os,sys,unittest
L=Path(__file__).resolve().parents[2];D=L/'work/build24m2/guard_n';K=L/'work/build24/kits/n'
before=(L/'attic/build24b/work/build24/kits/q/b/g.py').read_text();after=(K/'b/g.py').read_text();records=[];hits=set()
def run(source,a=True,c=1,m=85520809984,error=False,exists=True):
 calls=[]
 def props(index):
  calls.append(index)
  if error:raise RuntimeError('unavailable')
  return SimpleNamespace(name='NVIDIA H100 80GB HBM3',total_memory=m)
 t=SimpleNamespace(__version__='2.11.0+cu129',cuda=SimpleNamespace(is_available=lambda:a,device_count=lambda:c,get_device_properties=props))
 out=io.StringIO();result='PASS';filename=str(K/'b/g.py')
 def trace(frame,event,arg):
  if event=='line' and frame.f_code.co_filename==filename:hits.add(frame.f_lineno)
  return trace
 with patch.dict(sys.modules,torch=t),patch.dict(os.environ,CUDA_VISIBLE_DEVICES='0'),patch('os.path.exists',return_value=exists),redirect_stdout(out):
  previous=sys.gettrace();sys.settrace(trace if source==after else None)
  try:exec(compile(source,filename,'exec'),{})
  except Exception as e:result=type(e).__name__+':'+str(e)
  finally:sys.settrace(previous)
 lines=out.getvalue().splitlines();diag=json.loads(lines[0]) if lines else None
 if source==after:
  assert len(lines)==1
  assert set(diag)=={'v','a','c','e','ec','n','m','d0','dc','x'}
  assert diag['v']==t.__version__ and diag['a']==a and diag['c']==c and diag['e'] is True and diag['ec']==1
  assert diag['d0']==exists and diag['dc']==exists and diag['x']==error
  if a and c and not error:assert diag['n']=='NVIDIA H100 80GB HBM3' and diag['m']==m
  else:assert diag['n'] is None and diag['m'] is None
 records.append(dict(version='after' if source==after else 'before',available=a,count=c,bytes=m,query_error=error,device_nodes=exists,result=result,diagnostic=diag,property_calls=calls))
 return result
class Guard(unittest.TestCase):
 def test_reported_80gb(self):
  self.assertEqual(run(before),'RuntimeError:E42');self.assertEqual(run(after),'PASS')
 def test_no_cuda(self):
  self.assertEqual(run(before,a=False,c=0),'RuntimeError:E42');self.assertEqual(run(after,a=False,c=0),'RuntimeError:E42')
 def test_70gib(self):
  self.assertEqual(run(before,m=70*(1<<30)),'RuntimeError:E42');self.assertEqual(run(after,m=70*(1<<30)),'RuntimeError:E42')
 def test_exact_threshold(self):self.assertEqual(run(after,m=75*(1<<30)),'PASS')
 def test_below_threshold(self):self.assertEqual(run(after,m=75*(1<<30)-1),'RuntimeError:E42')
 def test_zero_count(self):self.assertEqual(run(after,c=0),'RuntimeError:E42')
 def test_properties_unavailable(self):self.assertEqual(run(after,error=True),'RuntimeError:E42')
 def test_missing_nodes_are_diagnostic(self):self.assertEqual(run(after,exists=False),'PASS')
 def test_generator_matches(self):
  source=(L/'work/build21/kit.py').read_text()
  strings=[n.value for n in ast.walk(ast.parse(source)) if isinstance(n,ast.Constant) and isinstance(n.value,str)]
  self.assertIn(after,strings);self.assertNotIn(before,strings);self.assertIn('minimum_gpu_gib=75',source)
result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Guard))
statements={n.lineno for n in ast.walk(ast.parse(after)) if isinstance(n,ast.stmt)}
(D/'LEGACY_GUARD_TESTS.json').write_text(json.dumps(dict(successful=result.wasSuccessful(),tests=result.testsRun,cases=records,changed_statement_lines=sorted(statements),covered=sorted(hits),missing=sorted(statements-hits),stand_in='torch module only; no CUDA/GPU calls'),indent=2)+'\n')
assert not statements-hits
raise SystemExit(not result.wasSuccessful())
