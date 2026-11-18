from pathlib import Path
import ast,json,sys
L=Path(__file__).resolve().parents[2];T=L/'work/tree_r1';B=L/'work/n1fix2'
sys.path.insert(0,str(T))
parsed=ast.parse((T/'tests/test_r2_n1fix.py').read_text())
method=next(n for n in ast.walk(parsed) if isinstance(n,ast.FunctionDef) and n.name=='test_M07_room_frames')
space={};exec(compile(ast.Module(body=[method.body[0]],type_ignores=[]),'<fixture>','exec'),space)
from student_pilot.trace_grammar import validate_row
errors=validate_row(dict(space['row'],form='direct'))
assert not errors,errors
from student_pilot.r1_training import row_check
try:row_check(space['row'],'vqa')
except ValueError as error:assert str(error)=='ONE_LINE_ROOM_REFUSED'
else:raise AssertionError('The one-frame room trace was admitted')
print('The room fixture passes grammar and fails only the required frame-count gate.')
