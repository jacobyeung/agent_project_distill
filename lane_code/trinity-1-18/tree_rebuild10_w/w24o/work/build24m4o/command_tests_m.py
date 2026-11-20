from common import *
import importlib.util,copy,ast
from unittest.mock import patch
def module(name,p):
 s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
R=module('new_rcj',L/'out/rcj/x.py')
B=module('old_rcj',L/'attic/build24m4o/out/rcj/x.py')
B.__file__=R.__file__
F=D/'commands';F.mkdir();root=F/'node';root.mkdir()
original=J.load
class Z:
 @staticmethod
 def checked(p,h):return Path(p)
 @staticmethod
 def load(p):
  if str(p).endswith('k/l.json'):return dict(bwrap=dict(file='/project/community/jjyeung/cp4tk_rt/kit/bwrap',sha256='a'*64))
  if str(p).endswith('k/p.json'):return dict(namespace='/tmp/q_22c714e1',n_root=str(F/'remote'))
  return original(p)
J.write(root/'env.json',dict(venv=str(root/'v'),scratch=str(root/'g'),paths=[str(root/'f'),'/usr/lib'],mounts=[['/usr/lib','/usr/lib']],record=str(root/'e.json')))
records=[]
for mode in ('b','r'):
 J.write(root/'mode.json',dict(mode=mode))
 for action in ('plan','run','check'):
  calls=[]
  for m in (B,R):
   def capture(cmd,**kwargs):calls.append(dict(cmd=cmd,kwargs=kwargs));return type('P',(),dict(returncode=0))()
   with patch.object(m,'attach',return_value=Z),patch.object(m.subprocess,'run',side_effect=capture):
    if m is R:
     with patch.object(R,'host_root',wraps=R.host_root) as h:
      assert R.launch(kit('qd'),root,'123',action)==0
      assert h.call_count==int(mode=='r')
    else:assert m.launch(kit('qd'),root,'123',action)==0
  if mode=='b':assert calls[0]==calls[1]
  else:
   assert calls[0]['cmd'][1:4]==['--ro-bind','/','/']
   assert calls[1]['cmd']==[calls[0]['cmd'][0],*R.host_root(),*calls[0]['cmd'][4:]]
   assert calls[0]['kwargs']==calls[1]['kwargs']
  records.append(dict(mode=mode,action=action,byte_identical=mode=='b',only_root_prefix_changed=mode=='r',command=calls[1]['cmd']))
entries=['usr','bin','etc','proc','dev','tmp','file','scratch']
with patch.object(R.os,'listdir',return_value=entries),patch.object(R.os.path,'islink',side_effect=lambda p:p=='/bin'),patch.object(R.os,'readlink',return_value='usr/bin'),patch.object(R.os.path,'isdir',side_effect=lambda p:p in ('/usr','/etc')):
 assert R.host_root()==['--symlink','usr/bin','/bin','--ro-bind','/etc','/etc','--ro-bind','/usr','/usr']
J.write(root/'mode.json',dict(mode='r'))
with patch.object(R,'attach',return_value=Z),patch.object(R,'host_root',return_value=['--ro-bind','/usr','/usr']) as h,patch.object(R.subprocess,'run',return_value=type('P',(),dict(returncode=0))()) as run:
 assert R.rdiff(kit('qd'),root,F/'out')==0
 assert h.call_count==1 and run.call_args.args[0][1:4]==['--ro-bind','/usr','/usr']
sys.path.insert(0,str(kit('qd')/'b'));import rb
cmd=rb.command(root,root/'ctl',T,{},dict(binds=[],executable=sys.executable))
assert not any(cmd[i:i+3]==['--ro-bind','/','/'] for i in range(len(cmd)))
assert J.sha(L/'out/rcj/pc.py')==J.load(D/'BASE_RCJ.json')['pc.py']['sha256']
J.write(D/'COMMAND_TESTS.json',dict(status='PASS',records=records,host_root_symlinks_dirs_and_exclusions=True,rdiff_uses_host_root=True,processor_children_already_assemble_root=True,pc_unchanged=True))
print('Mode b command bytes identical for plan/run/check; mode r changes only root prefix; rdiff uses host_root; processor children already assemble root')
