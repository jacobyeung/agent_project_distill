from pathlib import Path
import subprocess,sys
L=Path(__file__).resolve().parents[2];D=L/'work/build24i';R=L/'work/build24f/rehearsal'
args=['/usr/bin/bwrap','--ro-bind','/usr','/usr','--symlink','usr/bin','/bin','--symlink','usr/lib','/lib','--symlink','usr/lib64','/lib64','--ro-bind','/etc','/etc','--proc','/proc','--dev','/dev','--tmpfs','/tmp','--ro-bind','/scratch','/scratch','--bind',str(D),str(D),'--ro-bind',str(R),'/tmp/q_22c714e1','--ro-bind',str(L/'work/build24d/go/p'),'/tmp/q_22c714e1/p','--chdir',str(L)]
raise SystemExit(subprocess.run(args+[sys.executable,'-I','-s','-B',str(D/'evidence_retained.py')]).returncode)
