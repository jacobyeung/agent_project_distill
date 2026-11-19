"""Coordinator-only GPU launcher. This file is tested through injected CPU mocks."""
import argparse,fcntl,os,socket,signal,sys,time,subprocess,uuid
from core import *
VNICE='/data3/shared/scripts/vnice/vnice.sh'
def validate_environment(actual,required):
 roots=[pathlib.Path(required['base_env']).resolve(),*[pathlib.Path(x).resolve() for x in required['env_roots']]]
 if pathlib.Path(actual['prefix']).resolve()!=roots[0]:raise Refusal('Runtime prefix differs from reader environment')
 for name,want in required['modules'].items():
  got=actual['modules'][name]
  if got['version']!=want['version']:raise Refusal('Runtime version differs: '+name)
  if not any(pathlib.Path(got['path']).resolve().is_relative_to(root) for root in roots):raise Refusal('Runtime import outside pinned reader environment: '+name)

def environment(out):
 required=read(KIT/'inputs/ENV_REQUIRED.json');python=pathlib.Path(required['target_python'])
 if not python.is_file():raise Refusal('MISSING pinned reader runtime: '+str(python)+'; see ENV_REQUIRED.json')
 pins={str(KIT/'inputs/ENV_REQUIRED.json'):sha(KIT/'inputs/ENV_REQUIRED.json'),str(KIT/'env_probe.py'):sha(KIT/'env_probe.py')}
 for arc in required['archives']:
  checked(arc['path'],arc['sha256'],arc['bytes']);pins[arc['path']]=arc['sha256']
 receipt=required['receipt'];checked(receipt['path'],receipt['sha256'],receipt['bytes']);pins[receipt['path']]=receipt['sha256']
 actual=json.loads(subprocess.check_output([str(python),'-B','-I',str(KIT/'env_probe.py')],env={**os.environ,'CUDA_VISIBLE_DEVICES':''},text=True))
 validate_environment(actual,required)
 for path in [python,python.parent/'boot.py',pathlib.Path(actual['python'])]:pins[str(path)]=sha(path)
 pins.update({m['path']:m['sha256'] for m in actual['modules'].values()})
 atomic(out/'ENVIRONMENT.json',{'input_sha256':pins,'required':required,'observed':actual})
 return python

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--card',type=int,required=True);ap.add_argument('--operator-resume',action='store_true',help='Only after an explicit coordinator order; never automatic');a=ap.parse_args()
 if socket.gethostname().split('.')[0]!='trinity-2-28':raise Refusal('Launcher may run only on trinity-2-28')
 out=contained(ROOT/'out/gpu_b');out.mkdir(parents=True,exist_ok=True)
 lock=(out/'LAUNCH.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 pins={str(KIT/'launcher.py'):sha(__file__)}
 attempt=None;child=None
 def interrupted(signum,frame):
  atomic(out/'KILLED.json',{'input_sha256':pins,'signal':signum,'attempt':attempt,'automatic_retry':False})
  if child is not None and child.poll() is None:os.killpg(child.pid,signum)
  raise SystemExit(128+signum)
 for sig in (signal.SIGTERM,signal.SIGINT,signal.SIGHUP):signal.signal(sig,interrupted)
 if (out/'ATTEMPT.json').exists():
  old=read(out/'ATTEMPT.json')
  finished=read(out/'ATTEMPT_FINISHED.json') if (out/'ATTEMPT_FINISHED.json').exists() else {}
  if finished.get('attempt')!=old['attempt'] and not (out/'KILLED.json').exists():atomic(out/'KILLED.json',{'input_sha256':pins,'reason':'Unfinished launch (including SIGKILL or node loss)','attempt':old['attempt']})
 relaunch_gate(out,a.operator_resume)
 if (out/'STOP').exists():raise Refusal('STOP exists; coordinator must move it aside after review')
 pins=verify_seal()
 for var,name in [('TMPDIR','tmp'),('XDG_CACHE_HOME','cache'),('HF_HOME','hf'),('TRITON_CACHE_DIR','triton'),('TORCH_HOME','torch')]:
  p=out/name;p.mkdir(exist_ok=True);os.environ[var]=str(p)
 os.environ.update(PYTHONDONTWRITEBYTECODE='1',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',OMP_NUM_THREADS='8',MKL_NUM_THREADS='8',OPENBLAS_NUM_THREADS='8')
 python=environment(out)
 # Check all frames and archive parts before occupying a GPU.
 from runtime import authenticate_frames
 authenticate_frames(read(KIT/'inputs/TRAIN_CAPTURES.json')['captures'])
 for arc in read(KIT/'inputs/ARCHIVES.json')['archives']:
  for p in arc['parts']:checked(p['path'],p['sha256'],p['bytes'])
 readings=idle_twice(a.card);pins[str(out/'ENVIRONMENT.json')]=sha(out/'ENVIRONMENT.json')
 atomic(out/'IDLE_RECEIPT.json',{'input_sha256':pins,'card':a.card,'readings':readings,'separation_seconds':300})
 attempt=uuid.uuid4().hex;atomic(out/'ATTEMPT.json',{'input_sha256':pins,'attempt':attempt,'unix':time.time(),'card':a.card,'operator_resume':a.operator_resume})
 # The timeout terminates this launched worker only. TERM at 4315 s and KILL at 4320 s.
 argv=[VNICE,'timeout','--signal=TERM','--kill-after=5s','4315s',str(python),'-B','-I',str(KIT/'worker.py'),'--out',str(out)]
 if a.operator_resume:argv+=['--operator-resume']
 env={**os.environ,'CUDA_VISIBLE_DEVICES':str(a.card)}
 try:
  with (out/('worker.'+attempt+'.log')).open('x') as log:
   child=subprocess.Popen(argv,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);rc=child.wait()
  if rc:raise Refusal('Worker exited '+str(rc)+'; no automatic retry')
  atomic(out/'ATTEMPT_FINISHED.json',{'input_sha256':pins,'attempt':attempt,'exit_code':rc})
 except BaseException as e:
  atomic(out/'KILLED.json',{'input_sha256':pins,'attempt':attempt,'error':str(e),'automatic_retry':False});raise
if __name__=='__main__':
 try:main()
 except (Refusal,OSError,ValueError) as e:print('REFUSED: '+str(e),file=sys.stderr);raise SystemExit(2)
