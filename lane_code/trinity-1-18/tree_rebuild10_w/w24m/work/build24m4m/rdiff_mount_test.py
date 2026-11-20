from common import *
import sqlite3,subprocess,sys,shutil
F=D/'rd_mount';F.mkdir();root=F/'node';root.mkdir();q=root/'dr/p/q';q.mkdir(parents=True)
target=F/'out';target.mkdir();project=F/'project'
for rel in ('community/jjyeung/cp4tk_rt/kit','community/jjyeung/okh7/x_22c714e1'):(project/rel).mkdir(parents=True,exist_ok=True)
(project/'community/jjyeung/cp4tk_rt/kit/bwrap').symlink_to(shutil.which('bwrap'))
os.link(D/'rdiff.py',project/'community/jjyeung/okh7/x_22c714e1/rdiff.py')
for part in ('base','selection'):
 (q/part).mkdir()
 with sqlite3.connect(q/part/'rows.sqlite') as c:
  c.execute('CREATE TABLE rows(i INTEGER,row TEXT,target TEXT)')
  c.execute('INSERT INTO rows VALUES(0,?,?)',(json.dumps(dict(dataset='fixture',scene='room',qid='q')),'{}'))
J.write(q/'n.json',dict(remove_files=[]));shutil.copytree(T,root/'dr/p/s')
child=F/'child.py';child.write_text('''from pathlib import Path
import sys,importlib.util,json
from unittest.mock import patch
L=Path(sys.argv[1]);root=Path(sys.argv[2]);target=Path(sys.argv[3])
sp=importlib.util.spec_from_file_location('rcj_rd',L/'out/rcj/x.py');R=importlib.util.module_from_spec(sp);sp.loader.exec_module(R)
class Z:
 @staticmethod
 def checked(p,h,size=None):
  if str(p).endswith('rdiff.py'):
   import hashlib
   assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h
  return Path(p)
 @staticmethod
 def load(p):
  if str(p).endswith('k/p.json'):return dict(namespace='/tmp/q_22c714e1',n_root='/project/community/jjyeung/okh7/x_22c714e1')
  if str(p).endswith('k/l.json'):return dict(bwrap=dict(file='/project/community/jjyeung/cp4tk_rt/kit/bwrap',sha256='0'*64))
  return json.loads(Path(p).read_text())
native_root=R.host_root
def local_root():
 # The fixture interpreter lives under /scratch; Orchard's lives under /project.
 return native_root()+[v for p in sorted({sys.prefix,sys.base_prefix}) for v in ('--ro-bind',p,p)]
with patch.object(R,'attach',return_value=Z),patch.object(R,'host_root',side_effect=local_root):rc=R.rdiff(L/'out/kit_qd',root,target)
assert rc==2,rc
text=(root/'rd.log').read_text();assert 'P database SHA256 differs:' in text,text
print('RDIFF_MOUNT_AND_PRODUCTION_GATE_PASS')
''')
cmd=['bwrap']
for p in ('/usr','/bin','/lib','/lib64','/etc','/scratch','/tmp','/sys'):
 if Path(p).is_symlink():cmd+=['--symlink',os.readlink(p),p]
 elif Path(p).exists():cmd+=['--ro-bind',p,p]
cmd+=['--bind',str(L),str(L),'--ro-bind',str(project),'/project','--dev-bind','/dev','/dev','--proc','/proc','--remount-ro','/',sys.executable,'-I','-s','-B',str(child),str(L),str(root),str(target)]
p=subprocess.run(cmd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT);(D/'RDIFF_MOUNT_TEST.log').write_text(p.stdout);assert p.returncode==0,p.stdout
J.write(D/'RDIFF_MOUNT_TEST.json',dict(status='PASS',real_script_hash=J.sha(D/'rdiff.py'),real_bwrap=True,native_reader=True,production_full_hash_refusal=True,comparison_completed=False))
print(p.stdout)
