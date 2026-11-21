from pathlib import Path
import os,sys,subprocess,json,resource,shutil
resource.setrlimit(resource.RLIMIT_AS,(14*1024**3,14*1024**3))
J=Path.cwd();D=J/'work/build24m4z2';W=J/'work/enospc2';K=J/'out/kit_n_go'
env={**os.environ,'OMP_NUM_THREADS':'4','OPENBLAS_NUM_THREADS':'4','MKL_NUM_THREADS':'4','TMPDIR':str(W/'tmp')}
rows=[]
def run(name,cmd):
 log=D/(name+'.log')
 with log.open('w') as f:p=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,env=env)
 rows.append(dict(name=name,returncode=p.returncode,log=str(log.relative_to(J))))
 (D/'SUITES.json').write_text(json.dumps(rows,indent=2)+'\n');print(name,p.returncode,flush=True)
 if p.returncode<0:raise SystemExit('STOP_KILLED')

# Retain all original assertions. Only imports, fixture roots and copied source
# paths change so this legacy suite actually exercises the adopted kit bytes.
s=(J/'work/build24m4c/live_tests.py').read_text()
s=s[s.index('from pathlib import Path'):]
s=s.replace("L=Path(__file__).resolve().parents[2];D=L/'work/build24m4c'", "L=Path("+repr(str(J))+");D=Path("+repr(str(D))+')')
s=s.replace('import live as C',"import importlib.util\nsp=importlib.util.spec_from_file_location('current_pc',"+repr(str(K/'b/pc.py'))+");C=importlib.util.module_from_spec(sp);sp.loader.exec_module(C)")
s=s.replace("(D/'live.py')",'Path('+repr(str(K/'b/pc.py'))+')').replace("(D/'live.sh')",'Path('+repr(str(K/'b/pc.sh'))+')')
s=s.replace("(Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24')/'work/build24k/sr.py')",'Path('+repr(str(K/'b/sr.py'))+')')
(D/'legacy_live_tests.py').write_text(s)
run('legacy_live_tests',[sys.executable,'-I','-s','-B',str(D/'legacy_live_tests.py')])

# Existing ENOSPC suite: exact current kit; retain its full assertions.
s=(J/'inputs/enospc/check_proposed_final.py').read_text().replace("K=W/'proposed'","K=W/'kit'")
(W/'check_current.py').write_text(s)
(W/'mnt5').mkdir(exist_ok=True)
run('existing_proposed_final',['unshare','-Urmn','bash','-c','mount -t tmpfs -o size=16m tmpfs '+str(W/'mnt5')+' && '+sys.executable+' -I -s -B '+str(W/'check_current.py')])

# Reuse the existing real TERM/USR1 descendant-worker tests with the newly
# mandatory session fixture installed before dd fills X.
s=(J/'inputs/enospc/final_cases.py').read_text().split('# Real archive persistence function',1)[0]
needle="with (L/'fill.log').open('wb') as f:"
insert="""import base64
(X/'n_s').mkdir(mode=0o700)
names=json.loads(base64.b64decode(json.loads((K/'k/y.json').read_text())['payload']))['objects']
values={key+'.j24009'+f'.part{i:02d}-of-04':'https://local.invalid/'+label+'/'+str(i) for label,key in names.items() for i in range(4)}
session=X/'n_s/sess_24009.json';session.write_text(json.dumps(values));session.chmod(0o600)
"""
s=s.replace(needle,insert+needle)
s+="\nassert all(r['ok'] and r['result']['returncode']==0 and r['result']['checkpoint'] for r in results),results\n"
(W/'signals_current.py').write_text(s);(W/'mnt4').mkdir(exist_ok=True)
run('existing_signals',['unshare','-Urmn','bash','-c','mount -t tmpfs -o size=16m tmpfs '+str(W/'mnt4')+' && '+sys.executable+' -I -s -B '+str(W/'signals_current.py')])

# Compile the actual import closure and parse launch shells without writing pyc.
run('syntax',['bash','-n',str(K/'b/pc.sh'),str(J/'out/jn2.sh'),str(J/'out/e2/e2.sh'),str(J/'out/e2/run.sh')])
for root in (K/'b',J/'out/e2'):
 for p in root.glob('*.py'):compile(p.read_bytes(),str(p),'exec')
print('Actual kit and E2 Python syntax PASS',flush=True)
