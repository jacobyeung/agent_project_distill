import os,sys,subprocess,json,resource
from pathlib import Path
resource.setrlimit(resource.RLIMIT_AS,(14*1024**3,14*1024**3))
J=Path.cwd();D=J/'work/build24m4z12';rows=[]
env={**os.environ,'OMP_NUM_THREADS':'4','OPENBLAS_NUM_THREADS':'4','MKL_NUM_THREADS':'4','NUMEXPR_NUM_THREADS':'4','TMPDIR':str(J/'tmp')}
commands=[('core','core_tests.py','guard'),('advanced','advanced_tests.py','guard'),('exit','exit_tests.py','guard'),('wrapper_signals','wrapper_signals.py','final'),('wrapper_race','wrapper_race_test.py'),('wrapper_exception','wrapper_exception.py'),('final_loop','final_loop_guard_test.py'),('readback','readback_guard_test.py'),('tgcs','tgcs_verified.py')]
for name,file,*args in commands:
 print('START',name,flush=True)
 with (D/(name+'.log')).open('w') as f:
  p=subprocess.run([sys.executable,'-I','-s','-B',str(D/file),*args],env=env,stdout=f,stderr=subprocess.STDOUT)
 rows.append(dict(name=name,returncode=p.returncode,log=str(D/(name+'.log'))))
 (D/'EXTENDED.json').write_text(json.dumps(rows,indent=2)+'\n')
 print('END',name,p.returncode,flush=True)
 if p.returncode:print((D/(name+'.log')).read_text()[-5000:],flush=True)
 if p.returncode<0:raise SystemExit('STOP_KILLED')
