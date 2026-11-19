import ast,subprocess,sys
from pathlib import Path
L=Path('/scratch/jjyeung/orch_n30/so_read')
sys.path.insert(0,str(L/'work/src'))
from orchard_h10.common import opaque
code=ast.parse((L/'work/operator4/package/a/5.py').read_text())
script=next(ast.literal_eval(n.value) for n in code.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='GATE_ARCHIVE' for t in n.targets))
ast.parse(script,feature_version=(3,6))
opaque(['/usr/bin/python3','-I','-s','-B','-c',script,'/scratch/jjyeung/b01ec87a6f29b/d'])
print('PASS: link-validation/tar argv passes the real production opaque-command guard; namespace script parses as Python 3.6.')
