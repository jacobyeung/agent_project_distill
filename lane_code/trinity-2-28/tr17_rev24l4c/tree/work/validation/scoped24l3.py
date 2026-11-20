import json, runpy, sys
from pathlib import Path
j=Path(__file__).resolve().parents[2]
modules=json.loads((j/'out/regression_after24ln.json').read_text())['modules']
sys.argv=[str(j/'work/validation/run_tests.py'), *sys.argv[1:3], *modules]
runpy.run_path(sys.argv[0],run_name='__main__')
