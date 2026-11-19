from pathlib import Path
import sys,runpy
L=Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24')
sys.path[:0]=[str(L/'work/build24'),str(L/'work/build21'),str(L/'work/tree_r1')]
import native24
sys.argv=sys.argv[1:]
runpy.run_path(sys.argv[0],run_name='__main__')
