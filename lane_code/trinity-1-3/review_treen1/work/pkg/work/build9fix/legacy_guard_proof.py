"""Authenticate preserved reader refusals against the prior source receipt."""
import ast
import hashlib
import json
from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/build9fix'
prior=L/'work/contracts_r6/tree_copy';current=L/'work/tree_r1'
hashes=json.loads((L/'work/build5/proofs/suite_tree/source_hashes.json').read_text())
names=['student_pilot/r2_policy.py','student_pilot/benchmark_eval/prepare.py',
       'student_pilot/orchard_eval/contracts.py','student_pilot/mdg_eval.py','rk/programs.py']
rows=[]
for name in names:
    after=(current/name).read_bytes()
    old_hash=hashes[name];new_hash=hashlib.sha256(after).hexdigest()
    same=old_hash==new_hash
    row=dict(file=name,build5_sha256=old_hash,current_sha256=new_hash,byte_identical=same)
    if name=='student_pilot/r2_policy.py':
        before=(prior/name).read_bytes()
        assert hashlib.sha256(before).hexdigest()==old_hash
        def guard(raw):
            return next(n for n in ast.parse(raw).body if isinstance(n,ast.FunctionDef) and n.name=='unsupported_entry')
        old_guard=ast.dump(guard(before),include_attributes=False)
        new_guard=ast.dump(guard(after),include_attributes=False)
        row.update(function='unsupported_entry',function_identical=old_guard==new_guard,
                   function_sha256=hashlib.sha256(new_guard.encode()).hexdigest())
        assert row['function_identical']
    else:assert same
    rows.append(row)
value=dict(source='work/build5/proofs/suite_tree/source_hashes.json',
           prior_tree='work/contracts_r6/tree_copy',guards=rows,verified=True)
(B/'LEGACY_GUARDS.json').write_text(json.dumps(value,indent=2)+'\n')
print(json.dumps(value))
for variant in ('tree','base'):
    result_path=B/'proofs'/('suite_'+variant)/'results.json'
    if not result_path.exists():continue
    result=json.loads(result_path.read_text())
    for name,error in result['errors']:
        if '.T0Teacher.' in name:
            print(json.dumps(dict(variant=variant,test=name,last=error.strip().splitlines()[-1])))
