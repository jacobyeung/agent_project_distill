"""Observe final reader execution without changing any EAT-1 clause."""
from pathlib import Path
import runpy,sys
L=Path(__file__).resolve().parents[2];B=L/'work/build10'
sys.path.insert(0,str(B))
from monitor9 import Monitor
monitor=Monitor(L/'work/tree_r1')
name=sys.argv[1]
out=L/'work/merge11/proofs/eat1'/name/'coverage';out.mkdir(parents=True,exist_ok=True)
try:runpy.run_path(str(B/'run_eat10.py'),run_name='__main__')
finally:monitor.save(out)
