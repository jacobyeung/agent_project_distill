import os,sys,json,time,resource,subprocess
from pathlib import Path
R=Path(__file__).resolve().parent
PY='/scratch/jjyeung/envs/p1cpu/bin/python'
resource.setrlimit(resource.RLIMIT_AS,(7*1024**3,7*1024**3))
os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:4])
os.umask(0o077)
for name in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):os.environ[name]='1'
os.environ.update(PYTHONDONTWRITEBYTECODE='1',CUDA_VISIBLE_DEVICES='',TMPDIR=str(R/'tt/tmp'))
assert not (R/'RUN_STARTED.json').exists(),'Single-use task'
(R/'RUN_STARTED.json').write_text(json.dumps(dict(utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),pid=os.getpid()))+'\n')
ledger=[]
for suite,leaf in [('cps','run_verified.py'),('tt','run_once.py')]:
 argv=[PY,'-I','-s','-B',str(R/suite/leaf)]
 start=time.monotonic()
 with (R/(suite+'.stdout')).open('w') as out,(R/(suite+'.stderr')).open('w') as err:
  proc=subprocess.run(argv,stdout=out,stderr=err)
 ledger.append(dict(label=suite,argv=argv,exit_code=proc.returncode,seconds=time.monotonic()-start))
 (R/'suite_commands.json').write_text(json.dumps(ledger,indent=2)+'\n')
 print(json.dumps(ledger[-1]),flush=True)
 if proc.returncode<0:
  raise SystemExit('Suite unexpectedly killed; stop without retry')
sys.path.insert(0,str(R/'tt'))
from common import command
base=R/'tt/cases/publication_build_raises'
record=command('publication_build_raises',base/'root',base/'project','2460',[str(R/'tt/bin/python3'),'-I','-s','-B',str(R/'tt/publication_case.py')])
(R/'RUN_FINISHED.json').write_text(json.dumps(dict(utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())))+'\n')
