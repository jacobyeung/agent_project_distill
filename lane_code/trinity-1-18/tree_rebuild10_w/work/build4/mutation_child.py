"""Apply one review statement mutation to live code objects, preserving disk pins."""
import importlib
import json
import os
from pathlib import Path
import runpy
import sys
import types
L=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(L/'work/tree_r1'))
spec=json.loads(Path(sys.argv[1]).read_text())
path=L/'work/tree_r1'/spec['file']
module=importlib.import_module(spec['file'][:-3].replace('/','.'))
text=path.read_text();assert text.count(spec['old'])>=1
namespace=dict(module.__dict__)
offset=text.rfind(spec['old']) if spec.get('last') else text.find(spec['old'])
changed=text[:offset]+spec['new']+text[offset+len(spec['old']):]
exec(compile(changed,str(path),'exec'),namespace)
def patch(old,new):
    if isinstance(old,types.FunctionType) and isinstance(new,types.FunctionType):
        old.__code__=new.__code__
    elif isinstance(old,type) and isinstance(new,type) and old.__module__==module.__name__:
        for key,value in vars(old).items():
            if key in vars(new):patch(value,vars(new)[key])
for key,value in module.__dict__.items():
    if key in namespace:patch(value,namespace[key])
sys.argv=[str(L/'work/build4/test_runner.py'),spec['output'],*spec['tests']]
runpy.run_path(sys.argv[0],run_name='__main__')
