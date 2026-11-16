import ast,hashlib,importlib.util,json,os,pathlib,sys,tempfile,unittest,uuid
B=pathlib.Path(__file__).resolve().parents[1];R=B.parents[1]/'guard_kit/report';D=B/'out/tests/mutants';D.mkdir(exist_ok=True)
sys.path.insert(0,str(B/'work'))
from report_review_tests import suite as review_suite
class RetainedDirectory:
 def __init__(self,*a,**k):
  p=B/'work/mutant_fixtures'/uuid.uuid4().hex;p.mkdir(parents=True);self.name=str(p)
 def __enter__(self):return self.name
 def __exit__(self,*a):return False
 def cleanup(self):pass
tempfile.TemporaryDirectory=RetainedDirectory
source=(R/'guard_read.py').read_text();tree=ast.parse((R/'tests/mutants.py').read_text())
mutants=ast.literal_eval(next(n.value for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='MUTANTS' for t in n.targets)))
results=[]
for name,old,new in mutants:
 if source.count(old)!=1:raise ValueError('Mutant source pattern differs')
 p=D/(name+'.py');p.write_text(source.replace(old,new));os.environ['GUARD_READ_PATH']=str(p)
 spec=importlib.util.spec_from_file_location('test_'+name,R/'tests/test_guard_read.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 suite=review_suite(m)
 suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(m))
 with (D/(name+'.log')).open('w') as stream:r=unittest.TextTestRunner(stream=stream,verbosity=1,failfast=True).run(suite)
 results.append(dict(name=name,killed=not r.wasSuccessful(),tests=r.testsRun,failures=[t.id() for t,e in r.failures],errors=[t.id() for t,e in r.errors],log=str(D/(name+'.log'))))
 (B/'out/MUTANTS.json').write_text(json.dumps(dict(complete=False,results=results),indent=2)+'\n')
 print(name,not r.wasSuccessful(),flush=True)
assert source==(R/'guard_read.py').read_text(),'Report changed during mutant validation'
(B/'out/MUTANTS.json').write_text(json.dumps(dict(complete=True,total=len(results),killed=sum(r['killed'] for r in results),results=results,
 report_sha256=hashlib.sha256(source.encode()).hexdigest(),local_review_tests=str(B/'work/report_review_tests.py')),indent=2)+'\n')
sys.exit(not all(r['killed'] for r in results))
