from pathlib import Path
import os,sys,subprocess,json,resource
resource.setrlimit(resource.RLIMIT_AS,(14*1024**3,14*1024**3))
J=Path.cwd();D=J/'work/build24m4z3';W=J/'work/enospc3'
env={**os.environ,'OMP_NUM_THREADS':'4','OPENBLAS_NUM_THREADS':'4','MKL_NUM_THREADS':'4','NUMEXPR_NUM_THREADS':'4','TMPDIR':str(J/'tmp'),'PYTHONDONTWRITEBYTECODE':'1'}
rows=[]
def run(name,cmd):
 with (D/(name+'.log')).open('w') as out:p=subprocess.run(cmd,stdout=out,stderr=subprocess.STDOUT,env=env)
 rows.append(dict(name=name,returncode=p.returncode,log=str((D/(name+'.log')).relative_to(J))))
 (D/'SUITES.json').write_text(json.dumps(rows,indent=2)+'\n');print(name,p.returncode,flush=True)
 if p.returncode<0:raise SystemExit('STOP_KILLED')
def ns(name,script,mount=None):
 cmd=[sys.executable,'-I','-s','-B',str(script)]
 if mount:cmd=['bash','-c','mount -t tmpfs -o size=16m tmpfs '+str(mount)+' && '+' '.join(cmd)]
 run(name,['unshare','-Urmn',*cmd])
ns('enospc',W/'retest.py',W/'mnt')
ns('existing_proposed_final',W/'check_current.py',W/'mnt5')
ns('existing_signals',W/'signals_current.py',W/'mnt4')
ns('wrapper',W/'wrapper_prefix2.py')
run('current_tests',[sys.executable,'-I','-s','-B',str(D/'current_tests.py')])
ns('e2_final',D/'e2_final.py')
run('readback',[sys.executable,'-I','-s','-B',str(D/'readback_test.py')])
