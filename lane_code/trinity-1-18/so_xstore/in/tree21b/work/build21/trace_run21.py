from pathlib import Path
import sys,os,runpy
L=Path(__file__).resolve().parents[2];B=L/'work/build21';T=L/'work/tree_r1'
sys.path[:0]=[str(B),str(T),str(L/'work/n1fix2')]
from monitor9 import Monitor
root=Path(os.environ.get('B21_TRACE_ROOT',str(T)));m=Monitor(root)
out=B/'proofs'/os.environ.get('B21_PROOF','trace');out.mkdir(parents=True,exist_ok=True)
script=str(Path(sys.argv[1]).resolve());sys.argv=sys.argv[1:]
try:runpy.run_path(script,run_name='__main__')
finally:m.save(out)
