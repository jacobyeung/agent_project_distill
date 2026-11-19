"""Count repaired test cases only when the final packaged suite passes them."""
import json
from pathlib import Path
L=Path(__file__).resolve().parents[2]
def read(path):return json.loads((L/path).read_text())
final=read('work/build5/proofs/suite_tree/results.json')
passed=set(final['passed']);initial={}
def add(name,error,source):
    method=name.split(' (',1)[0]
    if method in passed:
        initial.setdefault(method,[]).append(dict(test=name,error=error,source=source))
path='work/build5/EXPLORATORY.json';old=read(path)
for name,error in old['r2_errors']:add(name,error,path)
for row in old.get('legacy_errors',[]):add(row['test'],row['reason'],path)
for path in ('work/build5/proofs/r2/results.json','work/build5/proofs/legacy_tree/results.json'):
    value=read(path)
    for name,error in value['errors']+value['failures']:add(name,error,path)
rows=[]
for name,evidence in sorted(initial.items()):
    text='\n'.join(v['error'] for v in evidence)
    if "'NoneType' object has no attribute 'mlp'" in text:
        kind='native artifact reader handles the absent camera connector; legacy checks preserve visual-only behavior'
    elif 'authenticated R2 bank adapter' in text:
        kind='legacy expectation aligned with the required bank refusal'
    elif name.startswith('tests.test_gf1') and '1 != 2' in text:
        kind='legacy tower count aligned with a single visual-only reconstruction'
    elif name.startswith('tests.test_gx_dense_binding'):
        kind='cache identity must invalidate after the required pose-row change'
    elif name.startswith('tests.test_gx_carrier') and "'NoneType' object is not subscriptable" in text:
        kind='checkpoint fixture returns the native path receipt'
    elif any(value in text for value in ('cannot import name','has no attribute','No such file or directory')):
        kind='harness import isolation or writable local fixture setup'
    elif 'FileExistsError' in text:kind='owned fixture overwrite corrected'
    elif 'traceback' in text.lower() and 'source' in text.lower():kind='stable-source proof rerun or fixture repair'
    else:kind='test or implementation repair; inspect the initial traceback and current test'
    rows.append(dict(test=name,kind=kind,initial=evidence,
                     passing_source='work/build5/proofs/suite_tree/results.json'))
record=dict(counting_note='Unique previously failing test methods that pass in the final packaged suite; includes harness and fixture repairs, not a count of distinct production defects.',cases=rows)
(L/'work/build5/FIXES.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(dict(fixed=len(rows))))
