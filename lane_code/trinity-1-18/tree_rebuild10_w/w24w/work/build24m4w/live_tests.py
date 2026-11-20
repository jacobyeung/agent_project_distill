from pathlib import Path
import sys,importlib.util,json,ast,os,time
from unittest.mock import patch
from types import SimpleNamespace
L=Path(__file__).resolve().parents[2];D=L/'work/build24m4w'
sys.path[:0]=[str(D),str(L/'out/kit_qd/b')]
from common import *
import z

def module(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
x=module('current',L/'out/rcj/x.py');old=module('baseline',L/'attic/build24m4t/out/rcj/x.py')
F=D/('live_'+str(time.time_ns()));F.mkdir();records=[]
for label in ('pass','absent','oversize','budget','invalid','symlink','existing'):
 root=F/label;target=root/'out';target.mkdir(parents=True)
 if label!='absent':
  source=root/'dr/live';source.mkdir(parents=True)
  (source/'s0.json').write_text(json.dumps(dict(status='PASS',text='scannet'))+'\n')
  (source/'s1.json').write_text('{}\n')
 if label=='oversize':(source/'s1.json').write_text(' '*2_000_001)
 if label=='budget':(target/'a').write_bytes(b'x'*(x.LIMIT-65536))
 if label=='invalid':(source/'s1.json').write_text('not json')
 if label=='symlink':
  (source/'s1.json').rename(source/'original');(source/'s1.json').symlink_to(source/'original')
 if label=='existing':(target/'live').mkdir()
 try:files=x.live_publish(kit('qd'),root,target)
 except ValueError as e:
  assert label not in ('pass','absent');assert not (target/'live/s0.json').exists();records.append(dict(case=label,status='EXPECTED_REFUSAL',refusal=str(e)))
 else:
  assert label in ('pass','absent')
  if label=='pass':
   assert set(files)=={'live/s0.json','live/s1.json'}
   assert 'scannet' not in (target/'live/s0.json').read_text()
   assert sum(p.stat().st_size for p in target.rglob('*') if p.is_file())<x.LIMIT
   assert z.sha(source/'s0.json')!=z.sha(target/'live/s0.json')
  else:assert files=={} and not (target/'live').exists()
  records.append(dict(case=label,status='PASS',files=files))
# The command builder and mode-b callable bodies are unchanged.
a=ast.parse((L/'out/rcj/x.py').read_text());b=ast.parse((L/'attic/build24m4t/out/rcj/x.py').read_text())
func=lambda tree,name:next(v for v in tree.body if isinstance(v,ast.FunctionDef) and v.name==name)
for name in ('launch','host_root','stage','plan_r','run_r','run','sample','rdiff'):
 assert ast.dump(func(a,name),include_attributes=False)==ast.dump(func(b,name),include_attributes=False),name
root=F/'commands';root.mkdir();z.write(root/'env.json',dict(venv=str(root/'v'),paths=[],scratch=str(root/'g'),record=str(root/'e.json')))
class Pins:
 @staticmethod
 def load(p):
  if str(p).endswith('k/l.json'):return dict(bwrap=dict(file='/project/community/jjyeung/cp4tk_rt/kit/bwrap',sha256='0'*64))
  return z.load(p)
 checked=staticmethod(lambda p,h:Path(p))
commands=[]
old.__file__=x.__file__
for mode in ('b','r'):
 z.write(root/'mode.json',dict(mode=mode))
 for action in ('plan','run','check','chain'):
  seen=[]
  for m in (old,x):
   with patch.object(m,'attach',return_value=Pins),patch.object(m.subprocess,'run',return_value=SimpleNamespace(returncode=0)) as run:
    assert m.launch(kit('qd'),root,'173724',action)==0
   seen.append(run.call_args)
  assert seen[0]==seen[1]
  commands.append(dict(mode=mode,action=action,command=seen[0].args[0]))
# The exact failing and passing commands used the same paths and argv.
assert z.load(L/'work/build24m4t/BEFORE_COMMAND.json')==z.load(L/'work/build24m4t/AFTER_COMMAND.json')
assert 'pl.py", line 248' in (L/'work/build24m4t/before.log').read_text()
assert 'rv.py", line 63' in (L/'work/build24m4t/before.log').read_text()
assert "OSError: [Errno 30] Read-only file system: '/project/community/jjyeung/okh7/x_22c714e1/o/173724'" in (L/'work/build24m4t/before.log').read_text()
assert 'R1_PLAN_REFUSED:1' in (L/'work/build24m4t/before.log').read_text()
assert 'REAL_PATH_PASS' in (D/'after.log').read_text()
write(D/'LIVE_TESTS.json',dict(status='PASS',cases=records,commands=commands,launch_bytes_unchanged=True,mode_b_commands_identical=True,exact_before_after_command=True))
print('Live publication: seven cases PASS; eight launch commands byte-identical; exact fail/pass command PASS')
