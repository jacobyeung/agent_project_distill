from pathlib import Path
import subprocess,sys
L=Path(__file__).resolve().parents[2];D=L/'work/build24h';F=D/'receipt_fixture';F.mkdir();(F/'node/p').mkdir(parents=True)
ns='/tmp/q_22c714e1'
a=['/usr/bin/bwrap','--ro-bind','/usr','/usr','--symlink','usr/bin','/bin','--symlink','usr/lib','/lib','--symlink','usr/lib64','/lib64','--ro-bind','/etc','/etc','--proc','/proc','--dev','/dev','--tmpfs','/tmp','--ro-bind','/scratch','/scratch','--bind',str(D),str(D),'--bind',str(F/'node'),ns,'--ro-bind',str(L/'work/build24d/go/p2'),ns+'/p2','--ro-bind',str(L/'work/tree_r1'),ns+'/p/s','--chdir',str(L)]
raise SystemExit(subprocess.run(a+[sys.executable,'-I','-s','-B',str(D/'receipt_tests.py')]).returncode)
