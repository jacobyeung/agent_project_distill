import os,sys,subprocess,json,resource
from pathlib import Path
resource.setrlimit(resource.RLIMIT_AS,(14*1024**3,14*1024**3))
J=Path.cwd();D=J/'work/build24m4z12';rows=[]
env={**os.environ,'OMP_NUM_THREADS':'4','OPENBLAS_NUM_THREADS':'4','MKL_NUM_THREADS':'4','NUMEXPR_NUM_THREADS':'4','TMPDIR':str(J/'tmp')}
cases=[('suites','run_suites_final.py'),('findings','findings_tests.py','final'),('core','core_tests.py','final'),('advanced','advanced_tests.py','final'),('exit','exit_tests.py','final'),('final_loop','final_loop_final.py'),('e3','e3_local.py','release'),('readback','readback_final.py'),('tgcs','tgcs_final_test.py'),('tgcs_observers','tgcs_observers_final_test.py'),('trinity','trinity_release_test.py')]
for name,file,*args in cases:
 print('START',name,flush=True)
 with (D/('all_'+name+'.log')).open('w') as f:
  p=subprocess.run(['unshare','-Urmn',sys.executable,'-I','-s','-B',str(D/file),*args],env=env,stdout=f,stderr=subprocess.STDOUT)
 rows.append(dict(name=name,returncode=p.returncode,log=str((D/('all_'+name+'.log')).relative_to(J))))
 (D/'ALL_FINAL.json').write_text(json.dumps(rows,indent=2)+'\n')
 print('END',name,p.returncode,flush=True)
 if p.returncode:print((D/('all_'+name+'.log')).read_text()[-5000:],flush=True)
 if p.returncode<0:raise SystemExit('STOP_KILLED')
raise SystemExit(any(r['returncode'] for r in rows))
