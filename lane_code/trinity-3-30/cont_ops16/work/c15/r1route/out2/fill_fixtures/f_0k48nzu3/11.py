import sys,json,tarfile,types
from pathlib import Path
p=Path(sys.argv[1]);mapping=json.loads(Path(sys.argv[2]).read_text())
with tarfile.open(p/'0.tgz') as t:source=t.extractfile('8.py').read()
m=types.ModuleType('fixture');m.__file__=str(p/'3.py');exec(compile(source,m.__file__,'exec'),m.__dict__)
real=Path;inputs=json.loads((p/'a/1.json').read_text());sizes={v['path']:v['bytes'] for a in inputs['archives'] for v in a['parts']}
def path(v):
 if str(v)=='/project/community/jjyeung/okh7':return p.parent
 if str(v) in mapping:return real(mapping[str(v)])
 if str(v) in sizes:return types.SimpleNamespace(stat=lambda:types.SimpleNamespace(st_size=sizes[str(v)]))
 return real(v)
m.Path=path
v=m.check(p,1,'05:00:00');assert v['passed'] is True
print(json.dumps(v))
