from pathlib import Path
import os,sys,subprocess,time,shutil,json
W=Path(__file__).resolve().parent;J=W.parents[1];R=W/'wrapper2';R.mkdir();X=R/'x';X.mkdir();B=R/'bin';B.mkdir();N=R/'q_22c714e1_24046'
subprocess.run(['mount','-t','tmpfs','-o','size=16m','tmpfs',str(X)],check=True)
shutil.copytree(J/'out/kit_n_go',X/'n')
text=(J/'out/jn3.sh').read_text().split('g=$(nvidia-smi',1)[0]
text=text.replace('X="/project/community/jjyeung/okh7/x_22c714e1"','X='+repr(str(X)))
text+='''python3 -I -s -B "$SLURM_TMPDIR/child.py" "$N" 2>&1 | python3 -I -s -B "$ROOT/b/l.py" "$ROOT"
while [[ ! -f "$SLURM_TMPDIR/finish" ]]; do sleep .1; done
'''
(R/'prefix.sh').write_text(text)
(R/'child.py').write_text('from pathlib import Path\nimport sys\nn=Path(sys.argv[1])\nfor i in range(300):print("q",i,flush=True)\n(n/"c.local").write_bytes(b"q"*4096)\n')
(R/'runner.py').write_text('''import sys,runpy,time,types
from pathlib import Path
args=sys.argv[1:]
if '-c' in args:
 i=args.index('-c');code=args[i+1];sys.argv=['-c']+args[i+2:];exec(code);raise SystemExit(0)
while args[0].startswith('-'):args.pop(0)
sys.argv=args
if Path(args[0]).name=='j2.py':
 original=time.sleep
 time.sleep=lambda seconds:original(seconds*.003)
runpy.run_path(args[0],run_name='__main__')
''')
(B/'python3').write_text('#!/bin/bash\nexec '+sys.executable+' -I -s -B '+str(R/'runner.py')+' "$@"\n');(B/'python3').chmod(0o755)
with (R/'fill.log').open('w') as f:
 subprocess.run(['dd','if=/dev/zero','of='+str(X/'fill'),'bs=1M','count=32'],stdout=f,stderr=f)
 subprocess.run(['df','-B1',str(X)],stdout=f,stderr=f)
assert shutil.disk_usage(X).free==0
env={**os.environ,'SLURM_TMPDIR':str(R),'SLURM_JOB_ID':'24046','PATH':str(B)+':'+os.environ['PATH']}
with (R/'outer.log').open('w') as f:
 p=subprocess.Popen(['bash',str(R/'prefix.sh')],env=env,stdout=f,stderr=f)
 end=time.monotonic()+20
 while time.monotonic()<end and not (N/'c.local').exists():time.sleep(.1)
 assert p.poll() is None and (N/'c.local').stat().st_size==4096
 time.sleep(2)
 assert 'OSError' in (N/'j2.retry.log').read_text()
 with (R/'recovery.log').open('w') as out:
  subprocess.run(['mount','-t','tmpfs','-o','remount,size=64m','tmpfs',str(X)],check=True,stdout=out,stderr=out)
 end=time.monotonic()+10
 while time.monotonic()<end:
  target=X/'o/24046/j2.log'
  if target.exists() and target.read_bytes()==(N/'j2.log').read_bytes():break
  time.sleep(.1)
 assert (X/'o/24046/j2.log').read_bytes()==(N/'j2.log').read_bytes()
 (R/'finish').write_text('1\n');rc=p.wait(timeout=10);assert rc==0
 time.sleep(2)
result=dict(status='PASS',returncode=rc,checkpoint=4096,wrapper_prefix_exact_except_X=True,helper_exact=True,helper_clock_scale=.003,local_stdout=True,local_stderr=True,retry_E28=True,automatic_recovery=True,scope='Exact jn2.sh prefix through local redirection and helper startup; fixture substitutes GPU/resolver/job boundary')
(R/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
