from common import *
import importlib.util,tarfile,io,ast
from unittest.mock import patch
sp=importlib.util.spec_from_file_location('rcj_transport',L/'out/rcj/x.py');R=importlib.util.module_from_spec(sp);sp.loader.exec_module(R)
sp=importlib.util.spec_from_file_location('stage_transport',L/'work/build24m4j/p_tree/launch_s1/b/s.py');S=importlib.util.module_from_spec(sp);sp.loader.exec_module(S)
sys.path.insert(0,str(kit('qd')/'b'));import px,z
F=D/'transport';F.mkdir();pool=F/'pool';(pool/'m400').mkdir(parents=True)
x=R.Inputs.__new__(R.Inputs);x.kit=kit('qd');x.root=F/'node';x.root.mkdir();x.z=z;x.px=px;x.sources={};x.records={};x.archives={};x.stage=S.Stage(F,x.root/'s')
raw=b'{"q":1}\n';h=hashlib.sha256(raw).hexdigest();manifest=dict(schema='r7-handover-small-files-v1',run='6ed2c7aa',step=400,files=[dict(path='/tmp/a.json',sha256=h,bytes=len(raw),match=True)])
m=(json.dumps(manifest)+'\n').encode()
with tarfile.open(pool/'m400/s.tar','w') as t:
 for name,data in [('MANIFEST.json',m),('files/tmp/a.json',raw)]:
  member=tarfile.TarInfo(name);member.size=len(data);t.addfile(member,io.BytesIO(data))
x.spec=dict(uploads=[],p_files={},pool=str(pool),milestone='m400',m4=dict(v=hashlib.sha256(m).hexdigest()));x.current={}
result=x.need(h);assert Path(result).read_bytes()==raw
x.spec['m4']['v']='0'*64
try:x.need('a'*64)
except ValueError as e:assert str(e)=='R1_STAGED_PIN_MANIFEST_DIFFERS'
else:raise AssertionError('Changed manifest accepted')
# The literal pin/size transport uses the actual Stage.file path.
f=F/'in';f.write_bytes(b'file input');fh=J.sha(f)
x.current=dict(staged_inputs=dict(files=[dict(source=str(f),sha256=fh,bytes=f.stat().st_size,destination='u/q')]))
assert Path(x.need(fh)).read_bytes()==f.read_bytes()
# Legacy multipart payloads retain exact hashes without joining unrelated files.
parts=[]
for i,data in enumerate((b'part1',b'part2')):
 p=F/('p'+str(i));p.write_bytes(data);parts.append(str(p))
h2=hashlib.sha256(b'part1part2').hexdigest();x.current=dict(extra=[dict(dest=px.AWS+'/ap/8865619b/u/r',parts=parts,sha256=h2)])
assert Path(x.need(h2)).read_bytes()==b'part1part2'
for a in x.archives.values():a.close()
import re
def pathlike(s):return '/' in s or bool(re.search(r'\.(?:jsonl?|txt|log|tar|gz|py|sh|bin|pt|safetensors|sqlite|png)$',s))
from launch_r2.build import bad_string
wh=J.load(kit('qd')/'b/wh.json');count=0
for p in (L/'out/rcj').glob('*.py'):
 for node in ast.walk(ast.parse(p.read_text())):
  if isinstance(node,ast.Constant) and isinstance(node.value,str):
   v=node.value
   if v and not any(c.isspace() for c in v) and pathlike(v):
    assert not bad_string(v,wh),(node.lineno,v);count+=1
J.write(D/'TRANSPORT_TESTS.json',dict(status='PASS',handover_reader=True,manifest_change_refused=True,native_file_staging=True,native_multipart_staging=True,path_literals_checked=count))
print('TRANSPORT PASS; handover manifest refusal; native file/parts staging; path literals',count)
