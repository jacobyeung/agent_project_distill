"""Check the generator insertion on the exact sealed baseline shell bytes."""
from pathlib import Path
import ast,base64,datetime,hashlib,json,sys
L=Path(__file__).resolve().parents[2];B=L/'work/build21';D=L/'work/build21g'
print(datetime.datetime.now(datetime.timezone.utc).isoformat(),flush=True)
def shell(path):return base64.b64decode(json.loads(path.read_text())['payload']).decode()
old=shell(L/'attic/build21g/q/k/j.json');expected=shell(B/'kits/q/k/j.json')
tree=ast.parse((B/'kit.py').read_text(),filename=str(B/'kit.py'))
statements=[node for node in tree.body if isinstance(node,ast.Assign) and isinstance(node.value,ast.Call)
    and any(isinstance(x,ast.Constant) and x.value=='BW+=(--dev-bind /dev /dev --proc /proc' for x in node.value.args)]
assert len(statements)==1
hits=set()
def trace(frame,event,arg):
    if frame.f_code.co_filename!=str(B/'kit.py'):return None
    if event=='line':hits.add(frame.f_lineno)
    return trace
values={'shell':old};sys.settrace(trace)
exec(compile(ast.Module(body=statements,type_ignores=[]),str(B/'kit.py'),'exec'),values)
sys.settrace(None)
assert values['shell']==expected
(D/'TRACE_generator.json').write_text(json.dumps({'work/build21/kit.py':dict(sha256=hashlib.sha256((B/'kit.py').read_bytes()).hexdigest(),hits=sorted(hits),
    method='Execute the exact changed generator statement against the old sealed shell; assert byte equality to the new sealed shell tested by bwrap.')},indent=2)+'\n')
print('PASS: generator emits the exact shell exercised in the before/after view test')
