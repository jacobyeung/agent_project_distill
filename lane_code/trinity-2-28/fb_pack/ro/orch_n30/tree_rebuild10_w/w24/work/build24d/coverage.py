from pathlib import Path
import ast,difflib,json,runpy,sys
L=Path(__file__).resolve().parents[2];D=L/'work/build24d'
targets=[L/'work/build24/joblib.py',L/'work/build24/kits/n/b/h.py',L/'work/build24/kits/n/b/i.py']
hits={str(p):set() for p in targets}
def trace(frame,event,arg):
 if event=='line' and frame.f_code.co_filename in hits:hits[frame.f_code.co_filename].add(frame.f_lineno)
 return trace
old=L/'attic/build24d/work/build24/joblib.py';changes={}
for p in targets:
 lines=p.read_text().splitlines()
 changed=set(range(1,len(lines)+1))
 if p.name=='joblib.py':
  changed=set()
  for op,a,b,c,d in difflib.SequenceMatcher(a=old.read_text().splitlines(),b=lines).get_opcodes():
   if op in ('replace','insert'):changed.update(range(c+1,d+1))
 executable={n.lineno for n in ast.walk(ast.parse('\n'.join(lines))) if isinstance(n,ast.stmt) and not isinstance(n,(ast.FunctionDef,ast.Import,ast.ImportFrom))}
 changes[str(p)]=changed&executable
previous=D/'refresh_tests'
if previous.exists():previous.rename(L/'attic/build24d/refresh_tests')
outcomes=[]
sys.settrace(trace)
try:
 for name in ('resolver_tests','launch_tests','refresh_tests'):
  try:runpy.run_path(str(D/(name+'.py')),run_name='__main__')
  except SystemExit as e:
   outcomes.append(dict(name=name,code=e.code));assert e.code in (None,0),outcomes
finally:sys.settrace(None)
record={str(Path(p).relative_to(L)):dict(changed_statements=len(changes[p]),covered=len(changes[p]&h),missing=sorted(changes[p]-h),hits=sorted(h)) for p,h in hits.items()}
(D/'COVERAGE.json').write_text(json.dumps(dict(scope='Changed executable statements; selected resolver, launcher-config and refresh tests',files=record,outcomes=outcomes),indent=2)+'\n')
