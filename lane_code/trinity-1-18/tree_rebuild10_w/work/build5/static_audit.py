"""Bounded source and storage audit; no imports from the tree."""
import ast
import hashlib
import json
from pathlib import Path
import shutil
L=Path(__file__).resolve().parents[2]
syntax=[]
for p in [*(L/'work/tree_r1').rglob('*.py'),*(L/'work/build5').glob('*.py')]:
    if set(p.relative_to(L).parts)&{'artifacts','.git','__pycache__'}:continue
    try:ast.parse(p.read_text(),filename=str(p))
    except SyntaxError as error:syntax.append(dict(path=str(p.relative_to(L)),reason=str(error)))
pins={}
for name in ('work/tree_r1/student_pilot/trace_grammar.py','work/rows_slices/work/trace_grammar.py',
             'work/tree_r1/student_pilot/r2_dev_merged.json','work/shared/dev_scene_exclusions_d0.json'):
    pins[name]=hashlib.sha256((L/name).read_bytes()).hexdigest()
sizes={str(root.relative_to(L)):sum(p.stat().st_size for p in root.rglob('*') if p.is_file() and not p.is_symlink())
       for root in (L,L/'work/tmp',L/'work/build5')}
result=dict(syntax_errors=syntax,pins=pins,storage_bytes=sizes,scratch_free_bytes=shutil.disk_usage('/scratch').free)
(L/'work/build5/STATIC_AUDIT.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
assert not syntax
assert sizes['.']<=3_000_000_000
assert sizes['work/tmp']<=200_000_000
assert pins['work/tree_r1/student_pilot/trace_grammar.py']==pins['work/rows_slices/work/trace_grammar.py']
assert pins['work/tree_r1/student_pilot/r2_dev_merged.json']==pins['work/shared/dev_scene_exclusions_d0.json']
assert pins['work/tree_r1/student_pilot/trace_grammar.py']=='a41ba19190eb354168ce5837b2047fb6510c868c5d7cbfbf160cbe924777e268'
assert pins['work/tree_r1/student_pilot/r2_dev_merged.json']=='a1869ae28f6d3f1815993da776f4c4798f67bad4c555c3bb80cc48fcecb23af5'
