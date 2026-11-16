import os
from pathlib import Path
import runpy
import sys
L=Path(__file__).resolve().parents[2]
os.environ['B3_PREFIX']=os.environ.get('B3B_PREFIX','B3B_FOCUSED_')
if sys.argv[1:]==['all']:
    sys.argv[1:]=['tests.'+p.stem for p in sorted((L/'work/tree_r1/tests').glob('test_r2_*.py'))]+['shared_grammar_tests']
runpy.run_path(str(L/'work/build3b/snapshot_runner.py'),run_name='__main__')
