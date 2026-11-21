from pathlib import Path
import os,sys,subprocess,json,resource
resource.setrlimit(resource.RLIMIT_AS,(14*1024**3,14*1024**3))
J=Path.cwd();D=J/'work/build24m4z4';W=J/'work/enospc4';PY=sys.executable
env={**os.environ,'OMP_NUM_THREADS':'4','OPENBLAS_NUM_THREADS':'4','MKL_NUM_THREADS':'4','NUMEXPR_NUM_THREADS':'4','TMPDIR':str(J/'tmp')}
rows=[]
commands=[('current',[PY,'-I','-s','-B',str(D/'current_tests.py')]),
 ('legacy',[PY,'-I','-s','-B',str(D/'legacy_tests.py')]),
 ('enospc',['unshare','-Urmn','bash','-c','mount -t tmpfs -o size=16m tmpfs '+str(W/'mnt')+' && '+PY+' -I -s -B '+str(W/'retest.py')]),
 ('existing_enospc',['unshare','-Urmn','bash','-c','mount -t tmpfs -o size=16m tmpfs '+str(W/'mnt5')+' && '+PY+' -I -s -B '+str(W/'check_current.py')]),
 ('signals',['unshare','-Urmn','bash','-c','mount -t tmpfs -o size=16m tmpfs '+str(W/'mnt4')+' && '+PY+' -I -s -B '+str(W/'signals_current.py')]),
 ('wrapper',['unshare','-Urmn',PY,'-I','-s','-B',str(W/'wrapper_prefix2.py')]),
 ('e2',['unshare','-Urmn',PY,'-I','-s','-B',str(D/'e2_local.py')]),
 ('readback',[PY,'-I','-s','-B',str(D/'readback_test.py')])]
for name,command in commands:
 print('START',name,flush=True)
 with (D/(name+'.log')).open('w') as f:p=subprocess.run(command,stdout=f,stderr=subprocess.STDOUT,env=env)
 rows.append(dict(name=name,returncode=p.returncode,log=str((D/(name+'.log')).relative_to(J))))
 (D/'SUITES.json').write_text(json.dumps(rows,indent=2)+'\n')
 print('END',name,p.returncode,flush=True)
 if p.returncode:print((D/(name+'.log')).read_text()[-12000:],flush=True)
 if p.returncode<0:raise SystemExit('STOP_KILLED')
