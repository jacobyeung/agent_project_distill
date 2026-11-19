"""Run the final host arm-binding refusal against stable current source."""
import json
import os
from pathlib import Path
import subprocess
import sys
L=Path(__file__).resolve().parents[2]
output=L/'work/build5/proofs/host'
output.mkdir(parents=True,exist_ok=True)
env={**os.environ,'R2_LANE_ROOT':str(L),'R2_TREE':str(L/'work/tree_r1')}
with (output/'console.log').open('w') as log:
    result=subprocess.run([sys.executable,'-I','-s','-B',str(L/'work/build5/test_runner.py'),str(output),
        'tests.test_r2_build3_gaps.Gaps.test_host_packet_refusals'],env=env,stdout=log,stderr=subprocess.STDOUT)
if result.returncode<0:raise RuntimeError('Proof process was killed; stop without retry')
value=json.loads((output/'results.json').read_text())
print(json.dumps({key:len(value[key]) if isinstance(value[key],list) else value[key]
                  for key in ('tests','passed','errors','failures','complete','fatal')}))
if result.returncode:raise RuntimeError('Host proof requires a repair; inspect its fixed output folder')
