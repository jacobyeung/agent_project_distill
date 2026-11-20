from pathlib import Path
import sys,os,json,types,unittest,resource,tempfile
L=Path.cwd();D=L/'work/build24m4y';tree=Path(sys.argv[1]);label=sys.argv[2]
resource.setrlimit(resource.RLIMIT_AS,(14*1024**3,14*1024**3))
root=D/('q5_'+label);root.mkdir(exist_ok=True);tmp=root/'tmp';tmp.mkdir(exist_ok=True);tempfile.tempdir=str(tmp)
os.environ.update(TMPDIR=str(tmp),R2_FIXTURES='/scratch/jjyeung/orch_n30/tree_rebuild10_w/w21/fixtures',R2_PROOFS=str(root/'proofs'),R2_LANE_ROOT='/scratch/jjyeung/orch_n30/tree_rebuild10_w/w21',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1')
(root/'proofs').mkdir(exist_ok=True)
(root/'lane').mkdir(exist_ok=True);os.environ['LANE_TEST_OUTPUT']=str(root/'lane')
sys.path.insert(0,str(tree));package=types.ModuleType('tests');package.__path__=[str(tree/'tests')];sys.modules['tests']=package
names=sys.argv[3:] or ['test_r1_build13','test_r2_build9fix','test_r2_build3b','test_r2_build4','test_r2_build5','test_r2_build9_cpu','test_r2_build9_identity','test_r2_build9_recovery','test_r2_data_path','test_r2_policy','test_r2_refusals','test_carrier_c1_run','test_carrier_c1_routing','test_carrier_c1_cp2','test_r1_build16','test_r1_build17','test_r2_build8']
results=[]
def audit(event,args):
 if event in ('os.remove','os.rmdir'):raise RuntimeError('NO_DELETION:'+str(args))
sys.addaudithook(audit)
# Retain TemporaryDirectory fixtures under J instead of deleting them.
def retained_cleanup(self):
 self._finalizer.detach()
tempfile.TemporaryDirectory.cleanup=retained_cleanup
for name in names:
 with (root/(name+'.log')).open('w') as f:
  try:
   suite=unittest.defaultTestLoader.loadTestsFromName('tests.'+name)
  except Exception as error:
   import traceback
   f.write(traceback.format_exc());results.append(dict(name=name,tests=0,import_error=traceback.format_exc(),success=False));(root/'RESULTS.json').write_text(json.dumps(results,indent=2)+'\n');print(label,name,type(error).__name__,flush=True);continue
  r=unittest.TextTestRunner(stream=f,verbosity=2).run(suite)
 record=dict(name=name,tests=r.testsRun,failures=[dict(test=str(t),output=o) for t,o in r.failures],errors=[dict(test=str(t),output=o) for t,o in r.errors],skipped=[dict(test=str(t),reason=reason) for t,reason in r.skipped],success=r.wasSuccessful())
 results.append(record);(root/'RESULTS.json').write_text(json.dumps(results,indent=2)+'\n')
 print(label,name,r.testsRun,len(r.failures),len(r.errors),flush=True)
