from common import *
import ast,difflib,types,unittest,importlib.util,io
from unittest.mock import patch
from student_pilot import carrier_c1_run as C
text=(T/'student_pilot/carrier_c1_run.py').read_text().replace("if receipt.get('b7_inputs') or receipt.get('r1_training'):","if receipt.get('b7_inputs'):").replace("processor._b7_layout = layout(receipt.get('b7_inputs') or receipt)","processor._b7_layout = layout(receipt['b7_inputs'])")
node=next(n for n in ast.parse(text).body if isinstance(n,ast.FunctionDef) and n.name=='processor_for_receipt')
code=compile(ast.Module(body=[node],type_ignores=[]),'<proposed-function>','exec')
function=types.FunctionType(next(c for c in code.co_consts if isinstance(c,types.CodeType)),vars(C))
path=D/'test_r1_processor_compat.py';sp=importlib.util.spec_from_file_location('proposed_tests',path);M=importlib.util.module_from_spec(sp);sp.loader.exec_module(M)
out=io.StringIO()
with patch.object(C,'processor_for_receipt',function):
 result=unittest.TextTestRunner(stream=out,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(M))
replace(D/'PATCH_UNIT_TESTS.log',out.getvalue());assert result.wasSuccessful(),out.getvalue()
p=L/'out/TREE_CHANGE_24M4K.patch';raw=p.read_text()
raw+=''.join(difflib.unified_diff([],path.read_text().splitlines(True),fromfile='/dev/null',tofile='b/tests/test_r1_processor_compat.py'))
replace(p,raw)
J.write(D/'PATCH_UNIT_TESTS.json',dict(status='PASS',tests=result.testsRun,tree_modified=False,scope='Proposed function compiled in memory; patch file includes portable unittest file'))
print(out.getvalue())
