"""Run legacy modules and identical failing cases on the untouched base."""
import json
import os
from pathlib import Path
import subprocess
import sys
L=Path(__file__).resolve().parents[2]
env={**os.environ,'R2_LANE_ROOT':str(L),'R2_ALL_TESTS':'1','R2_SUITE_GROUP':'legacy',
     'R2_BASE_RESULTS':str(L/'work/build5/proofs/legacy_tree/results.json')}
for kind,path in [('tree',L/'work/tree_r1'),('base',L/'work/base/tree_b01ce449')]:
    output=L/'work/build5/proofs'/('legacy_'+kind);output.mkdir(parents=True,exist_ok=True)
    env['R2_TREE']=str(path)
    with (output/'console.log').open('w') as log:
        result=subprocess.run([sys.executable,'-I','-s','-B',str(L/'work/build5/test_runner.py'),str(output)],
                              env=env,stdout=log,stderr=subprocess.STDOUT)
    if result.returncode<0:raise RuntimeError('Legacy process was killed; stop without retry')
    value=json.loads((output/'results.json').read_text())
    print(json.dumps(dict(kind=kind,tests=value['tests'],passed=len(value['passed']),
                         errors=len(value['errors']),failures=len(value['failures']),complete=value['complete'])),flush=True)
    if not value['complete']:raise ValueError('Legacy suite did not complete')
env['R2_COMPARISON_KIND']='legacy'
subprocess.run([sys.executable,'-I','-s','-B',str(L/'work/build5/compare.py')],env=env,check=True)
