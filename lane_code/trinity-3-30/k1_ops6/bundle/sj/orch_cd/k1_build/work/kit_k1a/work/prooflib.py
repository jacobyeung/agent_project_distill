import ast,json,sys,traceback
from pathlib import Path
LANE=Path(__file__).resolve().parents[1]
def run(name,fn):
 hits={}
 def trace(frame,event,arg):
  p=frame.f_code.co_filename
  if not p.startswith('/scratch/jjyeung/orch_cd/'):return None
  if event=='line' and p.startswith('/scratch/jjyeung/orch_cd/'):
   hits.setdefault(p,set()).add(frame.f_lineno)
  return trace
 sys.settrace(trace)
 try:result=dict(proof=name,status='PASS',**(fn() or {}))
 except Exception as e:result=dict(proof=name,status='FAIL',error=repr(e),traceback=traceback.format_exc())
 finally:sys.settrace(None)
 cov={}
 for p,lines in hits.items():
  statements={n.lineno for n in ast.walk(ast.parse(Path(p).read_text())) if isinstance(n,ast.stmt)}
  cov[p]=dict(executed_lines=sorted(lines),statement_lines=sorted(statements),missing_statements=sorted(statements-lines))
 (LANE/f'out/{name}_COVERAGE.json').write_text(json.dumps(cov,indent=2)+'\n')
 result['coverage']=str(LANE/f'out/{name}_COVERAGE.json')
 (LANE/f'out/{name}_RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
 return result['status']=='PASS'
