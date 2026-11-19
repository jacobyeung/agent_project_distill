"""Run full discovery with cluster restrictions, retained fixtures and bounded resources."""
import os,sys,json,hashlib,time,unittest,tempfile,resource
from pathlib import Path
W=Path(__file__).resolve().parents[1];name=sys.argv[1];T=W/'work'/name
out=W/'work/suite'/name;out.mkdir(parents=True,exist_ok=True)
for key in ('R2_PROOFS','LANE_TEST_OUTPUT','STUDENT_PILOT_TEST_OUTPUT','STUDENT_CONVERTER_TEST_OUTPUT','CLEAN_VSI590K_TEST_ROOT','TMPDIR','XDG_CACHE_HOME','HF_HOME','TRITON_CACHE_DIR','CONDA_PKGS_DIRS','TORCH_HOME','B2_TEST_OUTPUT'):
 p=out/key;p.mkdir(exist_ok=True);os.environ[key]=str(p)
for key in ('R2_LANE_ROOT','S1_LANE_ROOT','CLEAN_VSI590K_WORKSPACE'):os.environ[key]=str(W)
os.environ.update(CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',S1_CPU_REHEARSAL='0')
tempfile.tempdir=os.environ['TMPDIR'];sys.dont_write_bytecode=True
os.chdir(T);sys.path.insert(0,str(T));sys.path.extend([str(T/'generator/derivgen_v7'),str(T/'generator/ground_rows_out')])
resource.setrlimit(resource.RLIMIT_AS,(38*1024**3,38*1024**3))
import torch
torch.set_num_threads(16)
# Block side effects forbidden by the task. A refusal remains a test error, never a skip or pass.
def guard(event,args):
 if event in ('subprocess.Popen','os.system','os.posix_spawn','os.fork','socket.connect','socket.bind','os.kill','os.killpg'):
  raise PermissionError('TASK_RESTRICTION:'+event)
 if event in ('os.listdir','os.scandir'):
  p=str(args[0])
  if p.startswith(('/home/','/data/','/data2/','/data3/')):raise PermissionError('TASK_NFS_RESTRICTION:'+p)
 if event=='open':
  p,mode,flags=args
  if isinstance(p,(str,bytes)):
   p=os.path.abspath(os.fsdecode(p))
   if p.startswith(('/home/','/data/','/data2/','/data3/')):raise PermissionError('TASK_NFS_RESTRICTION:'+p)
   if flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC) and not (p.startswith(str(W)+'/') or p=='/dev/null'):
    raise PermissionError('TASK_WRITE_RESTRICTION:'+p)
 if event in ('os.remove','os.rmdir'):raise PermissionError('TASK_NO_DELETE:'+str(args[0]))
 if event in ('os.mkdir','os.rename','os.symlink','os.link'):
  paths=args[:2] if event in ('os.rename','os.link') else args[1:2] if event=='os.symlink' else args[:1]
  for p in paths:
   if isinstance(p,(str,bytes)) and not os.path.abspath(os.fsdecode(p)).startswith(str(W)+'/'):
    raise PermissionError('TASK_WRITE_RESTRICTION:'+str(p))
sys.addaudithook(guard)
class Result(unittest.TextTestResult):
 def __init__(self,*a,**kw):super().__init__(*a,**kw);self.records=[]
 def addSuccess(self,t):super().addSuccess(t);self.records.append({'id':t.id(),'status':'PASS'})
 def addError(self,t,e):super().addError(t,e);self.records.append({'id':t.id(),'status':'ERROR','error':str(e[1])})
 def addFailure(self,t,e):super().addFailure(t,e);self.records.append({'id':t.id(),'status':'FAIL','error':str(e[1])})
 def addSkip(self,t,r):super().addSkip(t,r);self.records.append({'id':t.id(),'status':'SKIP','reason':r})
start=time.monotonic()
with (W/'out'/('CPU_'+name+'.log')).open('w') as f:
 suite=unittest.TestSuite()
 for p in sorted((T/'tests').glob('test*.py')):
  module='tests.'+p.stem
  try: suite.addTests(unittest.defaultTestLoader.loadTestsFromName(module))
  except Exception as error:
   suite.addTest(unittest.loader._FailedTest(module,error))
 result=unittest.TextTestRunner(stream=f,verbosity=2,resultclass=Result).run(suite)
files={str(p.relative_to(T)):hashlib.sha256(p.read_bytes()).hexdigest() for p in T.rglob('*.py') if '/artifacts/' not in str(p)}
inputs=[{'path':str(T/n),'sha256':h} for n,h in sorted(files.items())]
inputs.append({'path':str(Path(__file__).resolve()),'sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()})
record={'tree':name,'tests_run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skips':len(result.skipped),'seconds':time.monotonic()-start,'records':result.records,'inputs':inputs,'restrictions':'No subprocesses, forks, sockets, NFS access, deletion or external writes; refusals are recorded as errors.'}
(W/'out'/('CPU_'+name+'.json')).write_text(json.dumps(record,indent=2)+'\n');print({k:v for k,v in record.items() if k not in ('records','inputs')},flush=True)
