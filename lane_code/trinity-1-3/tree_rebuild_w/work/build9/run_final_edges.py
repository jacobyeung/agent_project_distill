import hashlib,json,os,subprocess,sys
from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/build9';output=B/'proofs/coverage_final'
env={**os.environ,'R2_TREE':str(L/'work/tree_r1'),'R2_LANE_ROOT':str(L),'R2_ALL_TESTS':'0','R2_SUITE_GROUP':'','R2_PACKAGE_MEMBERS':''}
names=sys.argv[1:] or ['coverage_b7.FaithfulRows.test_native_readout_runs_even_when_local_row_is_refused','coverage_final']
if names!=['coverage_b7.FaithfulRows.test_native_readout_runs_even_when_local_row_is_refused','coverage_final']:
 raw=(output/'results.json').read_bytes()
 prior=output/'history'/hashlib.sha256(raw).hexdigest()[:12];prior.mkdir(parents=True,exist_ok=True)
 for name in ('results.json','hits.json','source_hashes.json','tests.log'):
  target=prior/name
  if not target.exists():target.write_bytes((output/name).read_bytes())
with (B/'coverage_final.log').open('w') as log:
 result=subprocess.run([sys.executable,'-I','-s','-B',str(B/'test_runner.py'),str(output),*names],env=env,stdout=log,stderr=subprocess.STDOUT)
if result.returncode<0:raise RuntimeError('Proof process was killed; no retry')
value=json.loads((output/'results.json').read_text())
print(json.dumps({k:len(value[k]) if isinstance(value[k],list) else value[k] for k in ('tests','passed','errors','failures','complete')}))
sys.exit(result.returncode)
