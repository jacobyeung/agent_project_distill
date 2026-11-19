"""Run the tree's full offline suite under this lane's CPU and filesystem limits."""
import os,sys,runpy,resource,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
which=sys.argv[1]; tree=ROOT/'work'/which; output=ROOT/'out'/('suite_'+which)
output.mkdir(exist_ok=True)
os.environ.update(OMP_NUM_THREADS='16',MKL_NUM_THREADS='16',OPENBLAS_NUM_THREADS='16',CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',TMPDIR=str(output),HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
for key in ('STUDENT_PILOT_TEST_OUTPUT','STUDENT_CONVERTER_TEST_OUTPUT','LANE_TEST_OUTPUT','CLEAN_VSI590K_TEST_ROOT'):
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
sys.argv=[str(tree/'scripts/run_clean_offline_tests.py'),'--workspace',str(tree),'--output',str(output)]
# The upstream runner requires its output under --workspace. Use the lane root;
# source imports and discovery still use the exact selected source tree.
sys.argv[2]=str(ROOT)
try:runpy.run_path(sys.argv[0],run_name='__main__')
except SystemExit as e:code=e.code
else:code=0
p=output/'TEST_RESULTS.json'
if p.exists():
 value=json.loads(p.read_text());value['input_sha256']={str(ROOT/'out/SETUP.json'):hashlib.sha256((ROOT/'out/SETUP.json').read_bytes()).hexdigest(),str(Path(__file__)):hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),**{str(tree/k):v for k,v in value['tested_source_sha256'].items()}}
 value['command']='nice -n 10 env OMP_NUM_THREADS=16 MKL_NUM_THREADS=16 OPENBLAS_NUM_THREADS=16 OPENBLAS_NUM_THREADS=16 /scratch/jjyeung/envs/p1cpu/bin/python -B code/suite.py '+which
 p.write_text(json.dumps(value,indent=2)+'\n')
raise SystemExit(code)
