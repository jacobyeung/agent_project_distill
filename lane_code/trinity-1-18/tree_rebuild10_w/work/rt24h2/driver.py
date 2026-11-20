import os,sys,json,time,resource,subprocess
from pathlib import Path
R=Path(__file__).resolve().parent
PY='/scratch/jjyeung/envs/p1cpu/bin/python'
resource.setrlimit(resource.RLIMIT_AS,(7*1024**3,)*2)
resource.setrlimit(resource.RLIMIT_FSIZE,(64*1024**2,)*2)
os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:4])
os.umask(0o077)
for name in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):os.environ[name]='1'
os.environ.update(PYTHONDONTWRITEBYTECODE='1',CUDA_VISIBLE_DEVICES='',TMPDIR=str(R/'tt/tmp'))
assert not (R/'RUN_STARTED.json').exists(),'Single-use task'
(R/'RUN_STARTED.json').write_text(json.dumps(dict(utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),pid=os.getpid()))+'\n')
sys.path.insert(0,str(R/'tt'))
from common import *
prepare_sandbox()
raw(T/'bin/python3', '#!/bin/bash\nexec '+PY+' -I -s -B '+str(T/'exec_python.py')+' "$@"\n')
(T/'bin/python3').chmod(0o755)
base=T/'cases/preflight'
pre=command('tempfile_preflight',base/'root',base/'project','2459',[str(T/'bin/python3'),'-c',"import tempfile,resource,json,os; from pathlib import Path; p=Path(tempfile.gettempdir()); f=tempfile.NamedTemporaryFile(); f.write(b'test'); f.flush(); name=f.name; f.close(); assert not Path(name).exists(); print(json.dumps(dict(tmpdir=str(p),fsize=resource.getrlimit(resource.RLIMIT_FSIZE),nice=os.getpriority(os.PRIO_PROCESS,0),mountinfo=Path('/proc/self/mountinfo').read_text())))"])
assert pre['exit_code']==0,pre['stderr']
base=T/'cases/publication_build_raises'
record=command('publication_build_raises',base/'root',base/'project','2460',[str(T/'bin/python3'),'-I','-s','-B',str(T/'publication_case.py')])
if record['exit_code']<0:raise SystemExit('Unexpected kill: no retry')
argv=[PY,'-I','-s','-B',str(R/'cps/run_verified.py')]
start=time.monotonic()
with (R/'cps.stdout').open('w') as out,(R/'cps.stderr').open('w') as err:
 proc=subprocess.run(argv,stdout=out,stderr=err)
ledger=[dict(label='cps_suite',argv=argv,exit_code=proc.returncode,seconds=time.monotonic()-start)]
put(R/'suite_commands.json',ledger)
print(json.dumps(ledger[-1]),flush=True)
if proc.returncode<0:raise SystemExit('Unexpected kill: no retry')
put(R/'RUN_FINISHED.json',dict(utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())))
