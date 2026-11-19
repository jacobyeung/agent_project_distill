"""Run the existing harness while keeping build-21c/d evidence immutable."""
from pathlib import Path
import runpy,sys
L=Path(__file__).resolve().parents[2];B=L/'work/build21';D=L/'work/build21e'
sys.path[:0]=[str(B),str(L/'work/tree_r1')]
import naming_test21c,naming_test21d
for module,field,name in ((naming_test21c,'C','regression21c'),(naming_test21d,'D','regression21d')):
    output=D/name;(output/'proofs').mkdir(parents=True,exist_ok=True);setattr(module,field,output)
runpy.run_path(str(B/'test21.py'),run_name='__main__')
