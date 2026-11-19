import ast, json
from pathlib import Path
L=Path(__file__).resolve().parents[2];T=L/'work/tree_r1'
errors=[]
for folder in ('student_pilot','launch_r2','tests'):
    for p in (T/folder).glob('*.py'):
        try:ast.parse(p.read_text())
        except SyntaxError as e:errors.append(dict(file=str(p.relative_to(T)),error=str(e)))
print(json.dumps(errors,indent=2))
