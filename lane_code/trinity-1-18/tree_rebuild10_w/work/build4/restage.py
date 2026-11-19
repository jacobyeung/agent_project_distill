from pathlib import Path
import runpy
import sys
L=Path(__file__).resolve().parents[2]
old=L/'work/build4/kits'
old.rename(L/'work/build4'/(sys.argv[1] if len(sys.argv)>1 else 'kits_before_test_fixes'))
sys.argv=[str(L/'work/build4/build_kits.py'),'kits']
runpy.run_path(sys.argv[0],run_name='__main__')
