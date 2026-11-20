from pathlib import Path
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
