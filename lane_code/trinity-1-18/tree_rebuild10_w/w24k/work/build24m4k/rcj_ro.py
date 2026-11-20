from common import *
import importlib.util
from unittest.mock import patch
sp=importlib.util.spec_from_file_location('rcj_ro',L/'out/rcj/x.py');R=importlib.util.module_from_spec(sp);sp.loader.exec_module(R)
v=J.load(D/'rcj_k/ro_params.json');orig=J.load
class Z:
 sha=staticmethod(J.sha);write=staticmethod(J.write)
 @staticmethod
 def load(p):return dict(n_root=v['target']) if str(p).endswith('k/p.json') else orig(p)
for case,root,rc in (('success',v['root'],0),('refusal',v['root'],1),('stage',v['stage_root'],1)):
 with patch.object(R,'attach',return_value=Z):
  try:R.publish(kit('qd'),root,'401',rc)
  except ValueError as e:assert str(e)=='R1_PUBLICATION_INCOMPLETE'
  else:raise AssertionError('read-only target accepted')
 r=J.load(Path(root)/'publication.json');assert any(x['file']=='timings.json' for x in r['publication_errors']);assert len(r['publication_errors'])>5 and r['returncode']==rc
 J.write(D/('RO_'+case+'.json'),r)
 print('READ_ONLY_TARGET_PASS',case,len(r['publication_errors']))
