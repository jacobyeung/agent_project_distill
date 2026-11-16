import os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'kit'))
def test_child_argv_media_resolution_and_logs(tmp_path):
    import xnames
    scan=xnames.scan
    (tmp_path/'xnames.py').write_bytes((ROOT/'kit/xnames.py').read_bytes())
    code=r"""import os,sys,subprocess
from pathlib import Path
import xnames as X
root=Path.cwd();(root/'v').mkdir();target=root/'v'/('a'*64+'.mp4');target.write_bytes(b'fixture')
X.media_alias('/project/community/jjyeung/3e0e8a36/arkitscenes/1.mp4',target)
X.install(root)
import av
try:av.open('/project/community/jjyeung/3e0e8a36/arkitscenes/1.mp4')
except av.error.InvalidDataError:pass
else:raise AssertionError('fixture bytes unexpectedly decoded')
for name in ('WATCHDOG.json.log','chain.log'):
 before=len(os.listdir('/proc/self/fd'))
 with open(root/name,'wb') as log:
  fd=log.fileno()
  for i in range(30):assert log.fileno()==fd
  subprocess.run([sys.executable,'-B','-c',"from pathlib import Path;assert Path('/project/community/jjyeung/3e0e8a36/arkitscenes/1.mp4').read_bytes()==b'fixture';print('child retained');print('vsi')"],check=True,stdout=log,stderr=log)
 assert len(os.listdir('/proc/self/fd'))==before
 assert b'child retained' in (root/name).read_bytes()
 assert b'vsi' not in (root/name).read_bytes()
for args in (['/bin/echo','arkitscenes'],['/bin/sh','-c','echo scannet'],['/bin/echo','767369']):
 try:subprocess.run(args,check=True)
 except ValueError:pass
 else:raise AssertionError('argv leak admitted')
print('passed')
"""
    result=subprocess.run([sys.executable,'-B','-c',code],cwd=tmp_path,capture_output=True,text=True,timeout=60)
    assert result.returncode==0,result.stderr
    assert result.stdout.strip()=='passed'
    for name in ('WATCHDOG.json.log','chain.log'):scan((tmp_path/name).read_bytes())
