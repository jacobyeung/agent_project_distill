from pathlib import Path
import sys,runpy,os,json
L=Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24');D=L/'work/build24k'
sys.path[:0]=[str(L/'work/build24'),str(L/'work/build21'),str(L/'work/tree_r1'),str(Path(sys.argv[1]).parent)]
import native24 as N
N.C.processor_for=N.processor
import rg
native=rg.regenerate
rg.regenerate=lambda cfg,root:native(cfg,root,compare=False)
helper=sys.argv[1];sys.argv=sys.argv[1:]
runpy.run_path(helper,run_name='__main__')
