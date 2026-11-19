"""Coordinator-only GPU launcher. This file is tested through injected CPU mocks."""
import argparse,fcntl,os,socket,signal,sys,time,subprocess,uuid
from core import *
VNICE='/data3/shared/scripts/vnice/vnice.sh'
def environment(out):
 required=read(KIT/'inputs/ENV_REQUIRED.json');python=out/'env/bin/python'
 if not python.is_file():raise Refusal('MISSING exact step-544 runtime: '+str(python)+'; see ENV_REQUIRED.json')
 # Interpreter probe imports frameworks without CUDA allocation. Receipt paths must be local.
 probe="import importlib,json,sys,hashlib; names="+repr(list(required['modules']))+"; print(json.dumps({'python':sys.executable,'modules':{n:{'version':getattr((m:=importlib.import_module(n)),'__version__',None),'path':m.__file__,'sha256':hashlib.sha256(open(m.__file__,'rb').read()).hexdigest()} for n in names}}))"
 actual=json.loads(subprocess.check_output([str(python),'-B','-c',probe],env={**os.environ,'CUDA_VISIBLE_DEVICES':''},text=True))
 for name,want in required['modules'].items():
  got=actual['modules'][name]
  if got['version']!=want['version'] or got['sha256']!=want['sha256']:raise Refusal('Runtime differs from step-544 receipt: '+name)
  if not pathlib.Path(got['path']).resolve().is_relative_to(out/'env'):raise Refusal('Runtime import outside staged env: '+name)
 files={str(p):sha(p) for p in (out/'env').rglob('*') if p.is_file()}
 atomic(out/'ENVIRONMENT.json',{'input_sha256':{str(KIT/'inputs/ENV_REQUIRED.json'):sha(KIT/'inputs/ENV_REQUIRED.json'),**files},'observed':actual})
 return python

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--card',type=int,required=True);ap.add_argument('--operator-resume',action='store_true',help='Only after an explicit coordinator order; never automatic');a=ap.parse_args()
 if socket.gethostname().split('.')[0]!='trinity-2-28':raise Refusal('Launcher may run only on trinity-2-28')
 out=contained(ROOT/'out/gpu');out.mkdir(parents=True,exist_ok=True)
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
 argv=[VNICE,'timeout','--signal=TERM','--kill-after=5s','4315s',str(python),'-B',str(KIT/'worker.py'),'--out',str(out)]
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
