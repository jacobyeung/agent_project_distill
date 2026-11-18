from pathlib import Path
import runpy,sys
p=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(p))
runpy.run_path(str(p/'test_score_r1route.py'),run_name='__main__')
