"""Bounded static inventory and production config-path inspection."""
from pathlib import Path
import ast,json,sys
L=Path(__file__).resolve().parents[2];B=L/'work/build19';T=L/'work/tree_r1';O=B/'proofs/review';O.mkdir(parents=True,exist_ok=True)
rows=[]
for p in T.rglob('*.py'):
    if 'tests' in p.relative_to(T).parts:continue
    s=p.read_text()
    if 'unsupported_entry' not in s and 'r1_components' not in s and p.name not in ('r2_contract.py','r1_components.py','p_handover_receipt.py','p_export_receipt.py','b7_inputs.py'):continue
    for n in ast.walk(ast.parse(s)):
        if not isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)):continue
        calls=[x for x in ast.walk(n) if isinstance(x,ast.Call)]
        guarded=[x for x in calls if isinstance(x.func,ast.Name) and x.func.id in ('unsupported_entry','guard','artifact_status')]
        if guarded:rows.append(dict(file=str(p.relative_to(T)),line=n.lineno,function=n.name,guards=[dict(line=x.lineno,call=ast.get_source_segment(s,x)) for x in guarded]))
for name in ('student_pilot/b7_inputs.py','launch_r1/p_handover_receipt.py','launch_r1/p_export_receipt.py'):
    p=T/name
    for n in ast.parse(p.read_text()).body:
        if isinstance(n,ast.FunctionDef) and n.name in ('pin','produce','collect'):
            rows.append(dict(file=name,line=n.lineno,function=n.name,guards=[],qualification='The init pin is a staging selector, not an official item reader; official selection uses r2_contract.selected_init(official=True).' if n.name=='pin' else 'The receipt binds the exact artifact including component status; the official handover reader and bank gateway refuse deferred slots.'))
sources=[L.parent/'ext/r1_ops/work/snap_fac07052/out/config.json',L.parent/'ext/r1_ops/work/snap_6a5c7d00/out/config.json',L.parent/'inputs/p_configs/cprime_31abe087.json']
configs={str(p):dict(output=json.loads(p.read_text()).get('output')) for p in sources}
result=dict(independent_review='NOT RUN: the build explicitly forbids another agent; the ruling requests a separate review.',readers=rows,production_configs=configs,
    limitations=['Pure metric functions and data construction helpers do not select or load model exports; their guarded public entrypoints are listed.',
                  'This static inventory is not the independent review requested by the ruling.'])
(O/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(configs,indent=2));print('reader boundaries',len(rows))
