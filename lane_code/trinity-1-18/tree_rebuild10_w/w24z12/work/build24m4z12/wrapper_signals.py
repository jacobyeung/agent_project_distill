from pathlib import Path
import os,sys,subprocess,signal,time,json
J=Path.cwd();D=J/'work/build24m4z12';W=D/('wrapper_signals_'+sys.argv[1]);W.mkdir();rows=[]
for version in ('before','after'):
 for sig in ('TERM','USR1'):
  r=W/(version+'_'+sig);r.mkdir();x=r/'x';k=x/'n';(k/'b').mkdir(parents=True);(k/'k').mkdir();b=r/'bin';b.mkdir()
  (k/'b/z.py').write_text('def load(p):return {}\ndef screen(s,*a):return s\n')
  (k/'b/v.py').write_text('pass\n')
  (k/'b/resolve.py').write_text('import sys\nfrom pathlib import Path\nPath(sys.argv[sys.argv.index("--output")+1]).write_text("{}")\n')
  (k/'b/l.py').write_text('import sys\nsys.stdout.write(sys.stdin.read())\n')
  (b/'nvidia-smi').write_text('#!/bin/bash\nprintf "H100\\nH100\\nH100\\nH100\\n"\n');(b/'nvidia-smi').chmod(0o700)
  (b/'python3').symlink_to(sys.executable)
  (k/'job.sh').write_text('''#!/bin/bash
trap 'echo child_TERM; printf TERM > "$SLURM_TMPDIR/caught"; exit 7' TERM
trap 'echo child_USR1; printf USR1 > "$SLURM_TMPDIR/caught"; exit 9' USR1
printf ready > "$SLURM_TMPDIR/ready"
while true; do sleep .1; done
''')
  src=J/('inputs/jn2.sh' if version=='before' else 'out/jn3.sh');s=src.read_text()
  s=s.replace('X="/project/community/jjyeung/okh7/x_22c714e1"','X='+repr(str(x)))
  line=next(v for v in s.splitlines() if v.startswith('setsid python3'))
  s=s.replace(line,line+'\nprintf "%s" "$!" > "$SLURM_TMPDIR/helper_pid"')
  (r/'wrapper.sh').write_text(s)
  env={**os.environ,'SLURM_JOB_ID':'24070','SLURM_TMPDIR':str(r),'PATH':str(b)+':'+os.environ['PATH']}
  with (r/'outer.log').open('w') as f:
   p=subprocess.Popen(['bash',str(r/'wrapper.sh')],env=env,stdout=f,stderr=f)
   end=time.monotonic()+10
   while not (r/'ready').exists() and time.monotonic()<end:time.sleep(.05)
   assert (r/'ready').exists()
   p.send_signal(getattr(signal,'SIG'+sig));rc=p.wait(timeout=10)
  assert (r/'caught').read_text()==sig and rc==(7 if sig=='TERM' else 9),(version,sig,rc)
  local=r/'q_22c714e1_24070/j2.log';target=x/'o/24070/j2.log'
  exact=target.exists() and target.read_bytes()==local.read_bytes()
  if version=='after':assert exact
  else:
   assert not exact
   os.kill(int((r/'helper_pid').read_text()),signal.SIGTERM)
  rows.append(dict(version=version,signal=sig,child_trap=True,returncode=rc,final_publish=exact))
(W/'RESULT.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(rows))
