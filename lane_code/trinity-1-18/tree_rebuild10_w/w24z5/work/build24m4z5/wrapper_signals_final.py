from pathlib import Path
import os,sys,shutil,time,subprocess,signal,json
J=Path.cwd();D=J/'work/build24m4z5';R=D/'wrapper_signals_final';R.mkdir();rows=[]
source=(J/'out/jn3.sh').read_text();a=source.index('g=$(nvidia-smi');b=source.index('child=\n',a)
source=source[:a]+source[b:]
for sig in ('TERM','USR1'):
 r=R/sig;r.mkdir();x=r/'x';x.mkdir();k=x/'n';shutil.copytree(J/'out/kit_n',k)
 job='24';n=r/('q_22c714e1_'+job)
 (k/'job.sh').write_text('''#!/bin/bash
N="${SLURM_TMPDIR}/q_22c714e1_${SLURM_JOB_ID}"
finish() { printf '%s\n' "$1" > "$N/child.trap"; echo child-final; exit 17; }
trap 'finish TERM' TERM
trap 'finish USR1' USR1
printf ready > "$N/ready"
while true; do sleep .1; done
''')
 text=source.replace('X="/project/community/jjyeung/okh7/x_22c714e1"','X='+repr(str(x)))
 (r/'wrapper.sh').write_text(text)
 env={**os.environ,'SLURM_TMPDIR':str(r),'SLURM_JOB_ID':job}
 with (r/'outer.log').open('w') as f:
  p=subprocess.Popen(['bash',str(r/'wrapper.sh')],env=env,stdout=f,stderr=f)
  end=time.monotonic()+10
  while not (n/'ready').exists() and time.monotonic()<end:time.sleep(.05)
  assert (n/'ready').exists();os.kill(p.pid,getattr(signal,'SIG'+sig));rc=p.wait(timeout=10)
 assert rc==17,rc
 assert (n/'child.trap').read_text().strip()==sig
 assert (x/'o'/job/'j2.log').read_bytes()==(n/'j2.log').read_bytes()
 assert b'child-final' in (x/'o'/job/'j2.log').read_bytes()
 assert b'SLURM_TMPDIR' in (n/'j2.log').read_bytes() and b'free_bytes' in (n/'j2.log').read_bytes()
 rows.append(dict(signal=sig,child_trap=True,returncode=rc,final_publish_exact=True,start_disk_log=True))
# Exercise the helper's non-OSError path without exposing an exception message.
helper=(R/'TERM/q_22c714e1_24/j2.py').read_text().split("if '--once'",1)[0]
scope={};old=sys.argv;sys.argv=['j2',str(R/'TERM/x/n'),str(R/'TERM/q_22c714e1_24'),str(R/'TERM/x'),'24',str(os.getpid())]
exec(compile(helper,'j2','exec'),scope);sys.argv=old
def fail(*args):raise ValueError('private value')
scope['screen']=fail;scope['publish']()
raw=(R/'TERM/q_22c714e1_24/j2.retry.log').read_text();assert 'EValueError' in raw and 'private value' not in raw
(D/'WRAPPER_SIGNALS.json').write_text(json.dumps(dict(status='PASS',signals=rows,exception_caught=True),indent=2)+'\n');print(json.dumps(rows))
