"""Check the monitoring fingerprint against actual imported current functions."""
import ast
import hashlib
import importlib
import json
from pathlib import Path
import sys
import types
L=Path(__file__).resolve().parents[2];tree=L/'work/tree_r1'
sys.path.insert(0,str(tree))
parsed=ast.parse((L/'work/build5/test_runner.py').read_text())
node=next(n for n in parsed.body if isinstance(n,ast.FunctionDef) and n.name=='code_digest')
scope=dict(hashlib=hashlib,types=types)
exec(compile(ast.Module(body=[node],type_ignores=[]),'instrumentation-check','exec'),scope)
fingerprint=scope['code_digest'];records=[]
for name,objects in [('student_pilot.r2_mix',('table','reindex','plans')),
                     ('student_pilot.trace_grammar',('_value','validate_trace','main')),
                     ('launch_r2.checklist',('Checklist.step','Checklist.roundtrip','Checklist.finish'))]:
    module=importlib.import_module(name);path=Path(module.__file__)
    pending=[compile(path.read_bytes(),str(path),'exec',dont_inherit=True)];expected=set()
    while pending:
        code=pending.pop();expected.add(fingerprint(code))
        pending.extend(c for c in code.co_consts if isinstance(c,types.CodeType))
    for item in objects:
        value=module
        for key in item.split('.'):value=getattr(value,key)
        record=dict(file=str(path.relative_to(L)),function=item,matched=fingerprint(value.__code__) in expected)
        records.append(record)
    mutant=compile('raise ValueError("fixture mutation")',str(path),'exec')
    assert fingerprint(mutant) not in expected
output=L/'work/build5/proofs/instrumentation';output.mkdir(parents=True,exist_ok=True)
(output/'CHECK.json').write_text(json.dumps(records,indent=2)+'\n')
assert all(r['matched'] for r in records)
print(json.dumps(dict(functions=len(records),matched=all(r['matched'] for r in records),mutants_refused=True)))
