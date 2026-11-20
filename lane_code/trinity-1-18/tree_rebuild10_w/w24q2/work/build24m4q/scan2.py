from pathlib import Path
import runpy,sys
L=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(L/'work/build24m4p'))
import environment21f as env
env.__file__=str(L/'work/build24m4m/rcj_scanner/environment21f.py')
runpy.run_path(str(L/'work/build24m4q/scan.py'),run_name='__main__')
