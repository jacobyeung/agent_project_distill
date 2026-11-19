"""Test each builder's actual binding-admission block without model archives."""
import ast
import copy
import importlib
import json
from pathlib import Path
import sys
import tempfile
root=Path(__file__).resolve().parent
kind=sys.argv[1];folder=root/('hcam' if kind=='H' else 'dbuild');sys.path.insert(0,str(folder))
build=importlib.import_module('build_'+kind.lower())
body=next(n for n in ast.parse((folder/('build_'+kind.lower()+'.py')).read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='build').body
start=next(i for i,n in enumerate(body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='binding' for t in n.targets))
end=next(i for i,n in enumerate(body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='timing' for t in n.targets))
m=ast.parse('');m.body=body[start:end];code=compile(m,'<actual builder binding checks>','exec')
work=Path(tempfile.mkdtemp(prefix='binding400_'+kind,dir=str(root/'validation')))
binding=json.loads((folder/('bind_'+kind+'400.json')).read_text());old=json.loads((folder/('bind_'+kind+'200.json')).read_text())
def check(b):
    p=work/'binding.json';p.write_text(json.dumps(b))
    exec(code,dict(build.__dict__,binding_path=p,plan={'export_binding':{k:old[k] for k in build.KEYS}},walltime='04:00:00'))
check(binding);bad_cases=[]
for key,value in [('run','wrong'),('step',401),('archive_sha256','0'*64),('object','wrong'),('done','wrong'),('member_directory','m544'),('preparation_sha256',dict(binding['preparation_sha256'],config='0'*64)),('parts',[dict(p,sha256='0'*64) for p in binding['parts']])]:
    bad=copy.deepcopy(binding);bad[key]=value
    try:check(bad)
    except (AssertionError,ValueError,FileNotFoundError):bad_cases.append(key)
    else:raise AssertionError('Accepted '+key)
print(json.dumps(dict(passed=True,kind=kind,accepted400=True,refused=bad_cases)))
