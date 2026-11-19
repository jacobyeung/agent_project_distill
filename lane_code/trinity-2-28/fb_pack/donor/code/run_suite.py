if __name__ != '__main__':
 raise RuntimeError('Task guard refuses multiprocessing suite re-entry')
import os,sys,json,hashlib,time,resource,unittest
from pathlib import Path
W=Path(__file__).resolve().parents[1]; tree=W/'work'/sys.argv[1]; dest=W/'work'/('suite_'+sys.argv[1]);dest.mkdir(exist_ok=True)
for k in ('TMPDIR','LANE_TEST_OUTPUT','STUDENT_PILOT_TEST_OUTPUT','STUDENT_CONVERTER_TEST_OUTPUT','CLEAN_VSI590K_TEST_ROOT','B2_TEST_OUTPUT','B9_TEST_OUTPUT','B11_TEST_OUTPUT'):
 os.environ[k]=str(dest)
os.environ.update(CLEAN_VSI590K_WORKSPACE=str(tree),CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',XDG_CACHE_HOME=str(dest/'cache'),TORCH_HOME=str(dest/'torch'),HF_HOME=str(dest/'hf'))
resource.setrlimit(resource.RLIMIT_AS,(39*1024**3,39*1024**3))
import tempfile
tempfile.tempdir=str(dest)
os.chdir(tree);sys.path.insert(0,str(tree))
import torch
torch.set_num_threads(16)
def guard(event,args):
 if event=='open' and not isinstance(args[0],int):
  p=Path(os.fsdecode(args[0])).absolute(); mode,flags=args[1:]
  if str(p).startswith(('/home/','/data/','/data2/','/data3/')):raise PermissionError('Task forbids NFS reads: '+str(p))
  if ((mode and any(c in mode for c in 'wax+')) or flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND)) and not p.is_relative_to(W) and str(p)!='/dev/null':raise PermissionError('Task write boundary: '+str(p))
 if event in ('os.mkdir','os.remove','os.rmdir','os.chmod','os.utime'):
  p=Path(os.fsdecode(args[0])).absolute()
  if not p.is_relative_to(W):raise PermissionError('Task write boundary: '+str(p))
 if event in ('os.kill','os.killpg','socket.connect','socket.bind','os.system'):raise PermissionError('Task forbids '+event)
 if event in ('subprocess.Popen','os.fork','os.forkpty'):raise PermissionError('CPU suite process isolation: child launch refused by task guard')
sys.addaudithook(guard)
class Results(unittest.TextTestResult):
 def startTest(self,test):
  super().startTest(test)
  with (dest/'progress.txt').open('w') as f:f.write(str(self.testsRun)+' '+test.id()+'\n')
# The sealed tree omits empty __init__.py files; load its namespace explicitly.
import types,importlib
pkg=types.ModuleType('tests');pkg.__path__=[str(tree/'tests')];sys.modules['tests']=pkg
start=time.time();suite=unittest.TestSuite()
for path in sorted((tree/'tests').rglob('test*.py')):
 name='.'.join(path.relative_to(tree).with_suffix('').parts)
 try:
  suite.addTests(unittest.defaultTestLoader.loadTestsFromName(name))
 except Exception as error:
  import traceback
  message=traceback.format_exc()
  def failed(message=message):raise RuntimeError(message)
  suite.addTest(unittest.FunctionTestCase(failed,description=name))
result=unittest.TextTestRunner(verbosity=2,resultclass=Results).run(suite)
files={str(p.relative_to(tree)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(tree.rglob('*.py')) if '__pycache__' not in p.parts}
r={'inputs_sha256':{str(tree/k):v for k,v in files.items()},'command':'nice -n 10 env OMP_NUM_THREADS=16 MKL_NUM_THREADS=16 OPENBLAS_NUM_THREADS=16 /scratch/jjyeung/envs/p1cpu/bin/python -B code/run_suite.py '+sys.argv[1], 'tests_run':result.testsRun,'errors':[(t.id(),s) for t,s in result.errors],'failures':[(t.id(),s) for t,s in result.failures],'skipped':[(t.id(),s) for t,s in result.skipped],'seconds':time.time()-start,'guard':'No NFS, external writes, child processes, signals or sockets. Child-process tests are errors, not claimed passes.'}
r['inputs_sha256'][str(Path(__file__).resolve())]=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
(W/'out'/('SUITE_'+sys.argv[1].upper()+'.json')).write_text(json.dumps(r,indent=2)+'\n')
