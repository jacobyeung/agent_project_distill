import sys,json,ast
from pathlib import Path
sys.path.insert(0,sys.argv[1])
from student_pilot import s1_pool
from student_pilot.p3_provenance import load,file_pin
s=load(sys.argv[2]);assert s['implementation']==s1_pool.implementation()
p=Path(sys.argv[1])/'student_pilot/s1_routing.py';t=ast.parse(p.read_text())
n=next(n for n in ast.walk(t) if isinstance(n,ast.If) and any(isinstance(x,ast.Constant) and x.value=='Routing selection belongs to another implementation' for x in ast.walk(n)))
exec(compile(ast.Module(body=[n],type_ignores=[]),str(p),'exec'),dict(selection=s,s1_pool=s1_pool))
try:next(s1_pool.selected_rows(file_pin(sys.argv[2]),'ARKIT_gaps'))
except ValueError as e:
 assert 'implementation differs' not in str(e);print('NATIVE_READER_POST_GUARD',str(e))
else:raise AssertionError('Production row body unexpectedly available')
print('P_IMPLEMENTATION_GUARDS_PASS',len(s['implementation']))
