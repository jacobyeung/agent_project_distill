from common import *
import subprocess,sys,shutil
F=D/'mount_k';F.mkdir();root=F/'node';root.mkdir();project=F/'project'
for rel in ('community/jjyeung/c7d31ddd/venvs','community/jjyeung/cp4tk_rt/kit','community/jjyeung/okh7/x_22c714e1/o/123'):(project/rel).mkdir(parents=True)
(project/'community/jjyeung/cp4tk_rt/kit/bwrap').symlink_to(shutil.which('bwrap'))
for rel in ('dr','g','v','f','np','cl/site_alias','cl/provenance_bin'):(root/rel).mkdir(parents=True,exist_ok=True)
(root/'g'/root.relative_to('/scratch')).mkdir(parents=True)
(root/'v/rwtrain_torch211_cu129').symlink_to(sys.prefix,target_is_directory=True)
for dest in (sys.prefix,sys.base_prefix):
 assert dest.startswith('/scratch/')
 (root/'g'/Path(dest).relative_to('/scratch')).mkdir(parents=True,exist_ok=True)
J.write(root/'mode.json',dict(mode='r'));J.write(root/'e.json',{})
J.write(root/'env.json',dict(venv=str(root/'v'),paths=[str(root/'f'),str(root/'np'),str(root/'cl'),str(root/'cl/site_alias')],mounts=[[p,p] for p in {sys.prefix,sys.base_prefix}],scratch=str(root/'g'),record=str(root/'e.json')))
probe=root/'probe.py'
probe.write_text('''import sys,json,errno,os
from pathlib import Path
root=Path(sys.argv[-2]);target=Path('/project/community/jjyeung/okh7/x_22c714e1/o/123')
assert Path('/dev/null').exists() and Path('/proc/self/maps').is_file()
assert Path('/tmp/q_22c714e1').is_dir()
for p in (target/'x',root/'f/x',Path('/project/community/jjyeung/c7d31ddd/x')):
 try:p.write_text('bad')
 except OSError as e:assert e.errno==errno.EROFS,(p,e)
 else:raise AssertionError('read-only mount lost: '+str(p))
(root/'ok.json').write_text(json.dumps(dict(status='PASS',devices=True,proc=True,target_readonly=True,sites_readonly=True,root_writable=True)))
print('ACTUAL_LAUNCH_MOUNTS_PASS')
''')
child=F/'child.py'
child.write_text('''from pathlib import Path
import sys,importlib.util,json
from unittest.mock import patch
L=Path(sys.argv[1]);root=Path(sys.argv[2])
sp=importlib.util.spec_from_file_location('rcj_mount',L/'out/rcj/x.py');R=importlib.util.module_from_spec(sp);sp.loader.exec_module(R)
class Z:
 @staticmethod
 def checked(p,h):return Path(p)
 @staticmethod
 def load(p):
  if str(p).endswith('k/p.json'):return dict(namespace='/tmp/q_22c714e1')
  if str(p).endswith('k/l.json'):return dict(bwrap=dict(file='/project/community/jjyeung/cp4tk_rt/kit/bwrap',sha256='0'*64))
  return json.loads(Path(p).read_text())
R.__file__=str(root/'probe.py')
with patch.object(R,'attach',return_value=Z):raise SystemExit(R.launch(L/'out/kit_qd',root,'123'))
''')
cmd=['bwrap']
for p in ('/usr','/bin','/lib','/lib64','/etc','/scratch','/tmp','/sys'):
 if Path(p).is_symlink():cmd+=['--symlink',os.readlink(p),p]
 elif Path(p).exists():cmd+=['--ro-bind',p,p]
cmd+=['--bind',str(L),str(L),'--ro-bind',str(project),'/project','--dev-bind','/dev','/dev','--proc','/proc','--remount-ro','/',sys.executable,'-I','-s','-B',str(child),str(L),str(root)]
p=subprocess.run(cmd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT);(D/'MOUNT_TESTS.log').write_text(p.stdout)
assert p.returncode==0,p.stdout
v=J.load(root/'ok.json');v.update(scope='Actual nested bwrap launch; fixture runtime assets and binary transport; no production data or GPU')
J.write(D/'MOUNT_TESTS.json',v);print(p.stdout)
