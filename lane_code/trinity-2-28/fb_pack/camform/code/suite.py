"""Run the tree's full offline suite under this lane's CPU and filesystem limits."""
import os,sys,runpy,resource,json,hashlib,unittest,importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
which=sys.argv[1]; tree=ROOT/'work'/which; output=ROOT/'out'/('suite_'+which)
output.mkdir(exist_ok=True)
os.environ.update(OMP_NUM_THREADS='16',MKL_NUM_THREADS='16',OPENBLAS_NUM_THREADS='16',CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',TMPDIR=str(output),HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
for key in ('B2_TEST_OUTPUT','B9_TEST_OUTPUT','B11_TEST_OUTPUT','R2_PROOFS','R2_FIXTURES','STUDENT_PILOT_TEST_OUTPUT','STUDENT_CONVERTER_TEST_OUTPUT','LANE_TEST_OUTPUT','CLEAN_VSI590K_TEST_ROOT'):
 os.environ[key]=str(output/'fixtures')
import torch
torch.set_num_threads(16)
resource.setrlimit(resource.RLIMIT_AS,(38*1024**3,38*1024**3))
def guard(event,args):
 if event in ('socket.connect','socket.bind','socket.getaddrinfo','os.kill','os.killpg'):
  raise PermissionError('camform CPU-only guard: '+event)
 if event=='subprocess.Popen':
  cmd=args[1];parts=cmd if isinstance(cmd,(list,tuple)) else str(cmd).split()
  if any(Path(str(x)).name in ('ssh','scp','rsync','git','tmux','kill','pkill','killall') for x in parts):raise PermissionError('camform prohibited subprocess')
 if event=='open' and isinstance(args[0],(str,bytes)):
  p=Path(os.fsdecode(args[0])).absolute()
  if str(p).startswith(('/home/','/data/','/data2/','/data3/')):raise PermissionError('camform NFS read denied: '+str(p))
sys.addaudithook(guard)
os.chdir(tree)
# The tree has duplicate test_training.py basenames in two directories. Load
# namespace-qualified names so unittest cannot confuse their source files.
sys.path[:0]=[str(tree),str(tree/'tests')]
def discover(start_dir, pattern='test_*.py', **kwargs):
 suite=unittest.TestSuite()
 for p in sorted(Path(start_dir).rglob(pattern)):
  name='.'.join(p.relative_to(tree).with_suffix('').parts)
  try: suite.addTests(unittest.defaultTestLoader.loadTestsFromName(name))
  except Exception as error: suite.addTest(unittest.loader._FailedTest(name,error))
 return suite
unittest.defaultTestLoader.discover=discover

sys.argv=[str(tree/'scripts/run_clean_offline_tests.py'),'--workspace',str(tree),'--output',str(output)]
# The upstream runner requires its output under --workspace. Use the lane root;
# source imports and discovery still use the exact selected source tree.
sys.argv[2]=str(ROOT)
runner=runpy.run_path(sys.argv[0],run_name='camform_offline_runner')
# The upstream dependency table expects unqualified discovery names.
original_dependencies=runner['integration_dependencies']
class TestIdentity:
 def __init__(self,test):self.test=test
 def id(self):return self.test.id().removeprefix('tests.')
def dependencies(test):return original_dependencies(TestIdentity(test))
runner['main'].__globals__['integration_dependencies']=dependencies
try:code=runner['main']()
except SystemExit as e:code=e.code
else:code=0
p=output/'TEST_RESULTS.json'
if p.exists():
 value=json.loads(p.read_text());value['input_sha256']={str(ROOT/'out/SETUP.json'):hashlib.sha256((ROOT/'out/SETUP.json').read_bytes()).hexdigest(),str(Path(__file__)):hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),**{str(tree/k):v for k,v in value['tested_source_sha256'].items()}}
 value['command']='nice -n 10 env OMP_NUM_THREADS=16 MKL_NUM_THREADS=16 OPENBLAS_NUM_THREADS=16 OPENBLAS_NUM_THREADS=16 /scratch/jjyeung/envs/p1cpu/bin/python -B code/suite.py '+which
 p.write_text(json.dumps(value,indent=2)+'\n')
raise SystemExit(code)
