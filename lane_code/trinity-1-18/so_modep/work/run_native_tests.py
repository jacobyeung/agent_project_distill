from pathlib import Path
import os,sys,tempfile,unittest,json
os.sched_setaffinity(0, sorted(os.sched_getaffinity(0))[:8])
L=Path(__file__).resolve().parents[1]
T=Path(os.environ.get('MODEP_TREE',L/'work/tree'))
F=Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w21')
label=os.environ.get('MODEP_TEST_LABEL','off')
O=L/'work/tests'/label;O.mkdir(parents=True,exist_ok=False)
for d in ('tmp','proofs'):(O/d).mkdir()
sys.path[:0]=[str(T),str(F/'work/n1fix2'),str(F/'work/build16'),str(F/'work/build17'),str(F/'work/build18'),str(F/'work/build19'),str(F/'work/build20')]
os.environ.update(R2_FIXTURES=str(F/'fixtures'),R2_PROOFS=str(O/'proofs'),R2_LANE_ROOT=str(F),
 LANE_TEST_OUTPUT=str(O/'tmp'),TMPDIR=str(O/'tmp'),STUDENT_CONVERTER_TEST_OUTPUT=str(O/'tmp'))
tempfile.tempdir=str(O/'tmp')
class RetainedDirectory:
 def __init__(self,suffix=None,prefix=None,dir=None,**kw):self.name=tempfile.mkdtemp(suffix=suffix,prefix=prefix,dir=O/'tmp')
 def __enter__(self):return self.name
 def __exit__(self,*args):return False
 def cleanup(self):pass
tempfile.TemporaryDirectory=RetainedDirectory
# Refuse writes outside the dispatched workspace and never allow test cleanup.
def guard(event,args):
 if event in ('os.remove','os.rmdir'):raise RuntimeError('Fixture deletion forbidden: '+str(args))
 target=None
 if event=='open':
  path,mode,flags=args
  if isinstance(path,(str,bytes,os.PathLike)) and flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND):target=path
 elif event in ('os.mkdir','os.rename','os.link','os.symlink'):
  target=args[1] if event in ('os.rename','os.link','os.symlink') else args[0]
 if target is not None and not Path(target).resolve().is_relative_to(L):raise RuntimeError('Fixture write outside lane: '+str(target))
sys.addaudithook(guard)
import torch
torch.set_num_threads(8);torch.set_num_interop_threads(1)
modules=sys.argv[1:] or ['tests.test_r1_build20','tests.test_r1_build19','tests.test_r1_build18','tests.test_r1_build17','tests.test_r1_export17','tests.test_r1_build16','tests.test_r1_build15','tests.test_r1_build14','tests.test_r2_build_n1','tests.test_r2_n1fix','tests.test_r2_n1fix3','tests.test_r2_build12','tests.test_r1_build13','tests.test_r2_build3.Build3.test_opener_export_keep_and_reset','export_mutation17.HashTwin.test_same_size_shard_refuses']
suite=unittest.defaultTestLoader.loadTestsFromNames(modules)
r=unittest.TextTestRunner(verbosity=2).run(suite)
(O/'RESULT.json').write_text(json.dumps(dict(tests=r.testsRun,failures=[(str(t),s) for t,s in r.failures],errors=[(str(t),s) for t,s in r.errors],skipped=[(str(t),s) for t,s in r.skipped],successful=r.wasSuccessful()),indent=2))
raise SystemExit(not r.wasSuccessful())
