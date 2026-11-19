from pathlib import Path
import sys,subprocess
L=Path(__file__).resolve().parents[2];D=L/'work/build24h';F=D/'capture';F.mkdir()
a=['/usr/bin/bwrap','--ro-bind','/usr','/usr','--symlink','usr/bin','/bin','--symlink','usr/lib','/lib','--symlink','usr/lib64','/lib64','--ro-bind','/etc','/etc','--proc','/proc','--dev','/dev','--tmpfs','/tmp','--ro-bind','/scratch','/scratch','--bind',str(D),str(D),'--bind',str(F),'/tmp/q_22c714e1','--chdir',str(L)]
raise SystemExit(subprocess.run(a+[sys.executable,'-I','-s','-B',str(D/'host_capture.py')]).returncode)
