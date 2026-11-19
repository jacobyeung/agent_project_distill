"""Repair the frozen metadata layout and rerun only its missing-path failures."""
from pathlib import Path
import json,hashlib,sys,os,subprocess
L=Path(__file__).resolve().parents[2];B=L/'work/build15';O=B/'proofs/final';F=O/'frozen'
target=O/'suite_tree/r2';initial=json.loads((target/'results.json').read_text())
assert not initial['failures'] and len(initial['errors'])==3
assert all('FileNotFoundError' in error and '/frozen/work/build_n1/inputs/' in error for _,error in initial['errors'])
(target/'INITIAL_RESULTS.json').write_text(json.dumps(initial,indent=2))
q=F/'work/build_n1/inputs';q.parent.mkdir(parents=True,exist_ok=True)
if not q.exists():q.symlink_to(L/'work/build_n1/inputs',target_is_directory=True)
bound={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (L/'work/build_n1/inputs').glob('*.json')}
names=[name for name,_ in initial['errors']]
repair=O/'suite_repair/r2';repair.mkdir(parents=True,exist_ok=True)
env={**os.environ,'R2_TREE':str(F/'work/tree_r1'),'R2_LANE_ROOT':str(L),'R2_ALL_TESTS':'1','R2_SUITE_GROUP':'r2'}
runner=L/'work/n1fix2/test_runner.py'
with (repair/'console.log').open('w') as log:
    result=subprocess.run([sys.executable,'-I','-s','-B',str(runner),str(repair),*names],cwd=O/'empty',env=env,stdout=log,stderr=subprocess.STDOUT)
if result.returncode<0:raise SystemExit('Process killed; stop without retry')
assert result.returncode==0
fixed=json.loads((repair/'results.json').read_text());assert set(fixed['passed'])==set(names) and fixed['tests']==3
assert json.loads((target/'source_hashes.json').read_text())==json.loads((repair/'source_hashes.json').read_text())
combined=dict(initial,errors=[],passed=initial['passed']+fixed['passed'])
assert len(combined['passed'])==combined['tests']==449
(target/'results.json').write_text(json.dumps(combined,indent=2))
receipt=dict(reason='Frozen source snapshot omitted available build_n1 metadata. Added a read-only link to the exact packaged metadata; no stand-in.',
    initial='work/build15/proofs/final/suite_tree/r2/INITIAL_RESULTS.json',rerun='work/build15/proofs/final/suite_repair/r2/results.json',
    repaired_tests=names,bound_input_hashes=bound,runner_sha256=hashlib.sha256(runner.read_bytes()).hexdigest(),
    exact_source_hashes_equal=True,unique_tests=449,initial_executions=449,repair_executions=3)
(target/'RESUME_RECEIPT.json').write_text(json.dumps(receipt,indent=2))
runs=json.loads((B/'SUITE_RUNS.json').read_text());runs['r2'].update(returncode=0,repair=str((target/'RESUME_RECEIPT.json').relative_to(L)))
(B/'SUITE_RUNS.json').write_text(json.dumps(runs,indent=2));print('Frozen R2 qualification: 449 unique tests passed; three layout failures repaired and rerun.')
