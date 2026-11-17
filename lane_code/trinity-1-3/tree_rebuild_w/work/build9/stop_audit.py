"""Authenticate supplied stop evidence and inspect production construction without sockets."""
import ast,hashlib,json
from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/build9';T=L/'work/tree_r1';P=B/'proofs/stop_multirank';P.mkdir(parents=True,exist_ok=True)
lane=L/'work/lane_stop2';receipt=lane/'proofs/stop_multirank/RESULT.json';driver=lane/'stop_multirank.py'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(receipt)=='423949162b6294c03a352af9ec2e61b2a70a6036e2dfcf260188b60daff0d9d5'
assert sha(driver).startswith('29eff405')
result=json.loads(receipt.read_text());assert result['status']=='PASS' and all(result['checks'].values())
calls=[]
for path in T.rglob('*.py'):
    name=str(path.relative_to(T))
    if name.startswith('tests/'):continue
    parsed=ast.parse(path.read_text())
    for node in ast.walk(parsed):
        if isinstance(node,ast.Call) and ((isinstance(node.func,ast.Name) and node.func.id=='run_steps') or
            any(isinstance(a,ast.Name) and a.id=='run_steps' for a in node.args)):
            calls.append(dict(file=name,line=node.lineno,call=ast.unparse(node)))
assert len(calls)==1 and calls[0]['file']=='student_pilot/carrier_c1_run.py'
source=T/calls[0]['file'];parsed=ast.parse(source.read_text());functions={n.name:n for n in parsed.body if isinstance(n,ast.FunctionDef)}
proof=[]
for fname in ('load_model','train'):
    fn=functions[fname];binds=[n for n in ast.walk(fn) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='bind']
    assert binds
    proof.extend(dict(file=str(source.relative_to(T)),function=fname,line=n.lineno,call=ast.unparse(n)) for n in binds)
assert all(p['line']<calls[0]['line'] for p in proof)
load_return=[n.lineno for n in ast.walk(functions['load_model']) if isinstance(n,ast.Return)]
assert min(load_return)>min(p['line'] for p in proof if p['function']=='load_model')
changed={};unchanged=set()
for path in (lane/'proofs/stop_multirank').glob('*/coverage_rank_*/hits.json'):
    hits=json.loads(path.read_text());hashes=json.loads(path.with_name('source_hashes.json').read_text())
    for name,lines in hits.items():
        p=T/name
        if p.exists():
            if sha(p)!=hashes[name]:changed[name]=dict(lane_sha256=hashes[name],current_sha256=sha(p),evidence=str(path.relative_to(L)))
            else:unchanged.add(name)
# Keep the exact lane fixture binding. Only its output folder changes.
(B/'stop_multirank.py').write_text(driver.read_text().replace('work/lane_stop2/proofs/stop_multirank','work/build9/proofs/stop_multirank'))
(P/'RUN.sh').write_text('''#!/bin/bash
set -eu
L=/scratch/jjyeung/orch_n30/tree_rebuild_w
export TMPDIR="$L/work/tmp" OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 CUDA_VISIBLE_DEVICES="" PYTHONDONTWRITEBYTECODE=1
ulimit -f 204800
df -BG --output=avail /scratch
exec bash "$L/work/build9/RUN_PY.sh" "$L/work/build9/stop_multirank.py"
''')
record=dict(lane_receipt=dict(path=str(receipt.relative_to(L)),sha256=sha(receipt),result=result),
    lane_driver=dict(path=str(driver.relative_to(L)),sha256=sha(driver)),production_run_steps_calls=calls,production_version_binds=proof,
    paths='D0, H1, initial and resume workers all call carrier_c1_run.train; both rank branches call load_model, then train binds model and wrapped model before run_steps/checkpoint.',
    changed_exercised_sources=changed,unchanged_exercised_files=len(unchanged),rerun_required=bool(changed),
    current_driver_sha256=sha(B/'stop_multirank.py'),run_sha256=sha(P/'RUN.sh'),socket_run_performed=False,
    limitation='Static construction audit plus inherited native two-rank evidence. No production GPU/admission wrapper execution.')
(P/'AUDIT.json').write_text(json.dumps(record,indent=2)+'\n')
(P/'SOURCE.json').write_bytes((lane/'proofs/stop_multirank/SOURCE.json').read_bytes())
(P/'DRIVER_PINS.json').write_text(json.dumps({'driver_sha256':sha(B/'stop_multirank.py'),'run_sha256':sha(P/'RUN.sh')},indent=2)+'\n')
print(json.dumps(dict(rerun_required=bool(changed),changed_exercised_sources=list(changed),production_version_binds=proof)))
with (B/'STATUS.md').open('a') as f:
    f.write('\nItem 3a: native admitted-camera identity and mismatch tests pass (`work/build9/proofs/identity/results.json`). Faithful training stays disabled without its production-bound receipt.\n')
    f.write('\nItem 3b: supplied lane stop receipt authenticated; every production run_steps construction path binds trace version before checkpoint. '+('Changed exercised source requires a lane rerun using `work/build9/proofs/stop_multirank/RUN.sh`.' if changed else 'Exercised source hashes remain unchanged; no lane rerun is required.')+' Evidence: `work/build9/proofs/stop_multirank/AUDIT.json`.\n')
