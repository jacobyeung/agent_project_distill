from pathlib import Path
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
with patch.object(R,'attach',return_value=Z):rc=R.rdiff(L/'out/kit_qd',root,target)
assert rc==2,rc
text=(root/'rd.log').read_text();assert 'P database SHA256 differs:' in text,text
print('RDIFF_MOUNT_AND_PRODUCTION_GATE_PASS')
