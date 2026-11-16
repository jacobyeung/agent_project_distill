"""Compare legacy failures using the untouched packaged base code and writable scratch artifacts."""
import json
import os
from pathlib import Path
import subprocess
import sys
L=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(L/'work/tree_r1'))
from student_pilot.source_seal import inventory
base=L/'work/tmp/package/work/base/tree_b01ce449'
expected=inventory(L/'work/base/tree_b01ce449')
assert inventory(base)==expected,'Comparison base differs from the untouched original'
output=L/'work/build5/proofs/legacy_base';output.mkdir(parents=True,exist_ok=True)
env={**os.environ,'R2_LANE_ROOT':str(L),'R2_TREE':str(base),'R2_ALL_TESTS':'1','R2_SUITE_GROUP':'legacy',
     'R2_BASE_RESULTS':str(L/'work/build5/proofs/legacy_tree/results.json'),'R2_COMPARISON_KIND':'legacy'}
with (output/'console.log').open('w') as log:
    result=subprocess.run([sys.executable,'-I','-s','-B',str(L/'work/build5/test_runner.py'),str(output)],
                          env=env,stdout=log,stderr=subprocess.STDOUT)
if result.returncode<0:raise RuntimeError('Base process was killed; stop without retry')
assert inventory(base)==expected,'Comparison tests changed base source'
value=json.loads((output/'results.json').read_text())
assert value['complete'],'Base comparison did not complete'
subprocess.run([sys.executable,'-I','-s','-B',str(L/'work/build5/compare.py')],env=env,check=True)
