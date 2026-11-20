from pathlib import Path
import os,sys,subprocess,json,resource
resource.setrlimit(resource.RLIMIT_AS,(14*1024**3,14*1024**3))
J=Path.cwd();D=J/'work/build24m4z7';W=J/'work/enospc7';P=sys.executable
env={**os.environ,'OMP_NUM_THREADS':'4','OPENBLAS_NUM_THREADS':'4','MKL_NUM_THREADS':'4','NUMEXPR_NUM_THREADS':'4','TMPDIR':str(J/'tmp'),'TEST_W':str(W)}
commands=[('signals',['unshare','-Urmn','bash','-c','mount -t tmpfs -o size=16m tmpfs '+str(W/'mnt4')+' && '+P+' -I -s -B '+str(W/'signals_current.py')]),
 ('current',[P,'-I','-s','-B',str(D/'current_tests.py')]),('archive',[P,'-I','-s','-B',str(D/'archive_tests.py')]),('legacy',[P,'-I','-s','-B',str(D/'legacy_tests.py')]),
 ('enospc',['unshare','-Urmn','bash','-c','mount -t tmpfs -o size=16m tmpfs '+str(W/'mnt')+' && '+P+' -I -s -B '+str(W/'retest.py')]),
 ('existing_enospc',['unshare','-Urmn','bash','-c','mount -t tmpfs -o size=16m tmpfs '+str(W/'mnt5')+' && '+P+' -I -s -B '+str(W/'check_current.py')]),
 ('wrapper',['unshare','-Urmn',P,'-I','-s','-B',str(W/'wrapper_prefix2.py')])]
rows=[]
for name,cmd in commands:
 print('START',name,flush=True)
 with (D/(name+'.log')).open('w') as f:r=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,env=env)
 row=dict(name=name,returncode=r.returncode,log=str((D/(name+'.log')).relative_to(J)));rows.append(row)
 (D/'SUITES.json').write_text(json.dumps(rows,indent=2)+'\n');print('END',name,r.returncode,flush=True)
 if r.returncode:print((D/(name+'.log')).read_text()[-6000:],flush=True)
 if r.returncode<0:raise SystemExit('STOP_KILLED')
