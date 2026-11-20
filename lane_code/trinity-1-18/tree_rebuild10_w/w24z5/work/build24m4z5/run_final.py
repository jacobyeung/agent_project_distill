from pathlib import Path
import subprocess,os,sys,json,resource
resource.setrlimit(resource.RLIMIT_AS,(14*1024**3,14*1024**3))
J=Path.cwd();D=J/'work/build24m4z5';W=J/'work/enospc5_final';P=sys.executable
env={**os.environ,'OMP_NUM_THREADS':'4','OPENBLAS_NUM_THREADS':'4','MKL_NUM_THREADS':'4','NUMEXPR_NUM_THREADS':'4','TMPDIR':str(J/'tmp')}
commands=[]
for name,script in [('archive','archive_validated_tests.py'),('current','current_validated_tests.py'),('legacy','legacy_validated_tests.py'),('final_loop','final_loop_test.py')]:commands.append((name,[P,'-I','-s','-B',str(D/script)]))
for name,mnt,script in [('enospc','mnt','retest.py'),('existing_enospc','mnt5','check_current.py'),('signals','mnt4','signals_current.py')]:commands.append((name,['unshare','-Urmn','bash','-c','mount -t tmpfs -o size=16m tmpfs '+str(W/mnt)+' && '+P+' -I -s -B '+str(W/script)]))
commands.extend([('wrapper',['unshare','-Urmn',P,'-I','-s','-B',str(W/'wrapper_prefix2.py')]),('e3',['unshare','-Urmn',P,'-I','-s','-B',str(D/'e3_final.py')]),('readback',[P,'-I','-s','-B',str(D/'readback_final_test.py')]),('probes',[P,'-I','-s','-B',str(D/'probes.py'),'after'])])
rows=[]
for name,cmd in commands:
 print('START',name,flush=True);log=D/(name+'_final.log')
 with log.open('w') as f:r=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,env=env)
 rows.append(dict(name=name,returncode=r.returncode,log=str(log.relative_to(J))))
 (D/'FINAL_SUITES.json').write_text(json.dumps(rows,indent=2)+'\n')
 print('END',name,r.returncode,flush=True)
 if r.returncode:print(log.read_text()[-8000:],flush=True)
 if r.returncode<0:raise SystemExit('STOP_KILLED')
raise SystemExit(any(r['returncode'] for r in rows))
