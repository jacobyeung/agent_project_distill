"""Run the delivered package wrapper from a newly empty local directory."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
L=Path(__file__).resolve().parents[2]
delivery=json.loads((L/'work/build6/DELIVERY.json').read_text())
empty=Path(tempfile.mkdtemp(prefix='delivery_empty_',dir=L/'work/tmp'))
assert not any(empty.iterdir())
output=L/'work/build6/proofs/package';output.mkdir(exist_ok=True)
(output/'INVOCATION.json').write_text(json.dumps(dict(
    cwd=str(empty),empty=True,archive=delivery['path'],wrapper='work/build6/PACKAGE_TEST.sh'),indent=2)+'\n')
result=subprocess.run(['bash',str(L/'work/build6/PACKAGE_TEST.sh'),str(L/delivery['path'])],cwd=empty,env=os.environ)
if result.returncode<0:raise RuntimeError('Package process was killed; stop without retry')
raise SystemExit(result.returncode)
