from common import *
from unittest.mock import patch
sys.path.insert(0,str(kit('q')/'b'))
import px,z
F=D/'pin_tests';F.mkdir();k=F/'kit';(k/'k').mkdir(parents=True);node=F/'node';node.mkdir()
content=b'authenticated fixture bytes\n';h=hashlib.sha256(content).hexdigest()
cases=[]
for kind in ('joined','tar','package','direct','small'):
 root=node/kind;root.mkdir();mapping={}
 if kind=='joined':mapping={'extra':[dict(dest=px.AWS+'/ap/8865619b/k/fixture',sha256=h,parts=[])]};target=root/'x/k/fixture'
 elif kind=='tar':mapping={'tars':[dict(files={'ap/abc/u/member':h},parts=[])]};target=root/'s/aws/u/ap/abc/u/member'
 elif kind=='package':mapping={'staged_inputs':{'packages':[dict(destination='u/fixture',inventory=[dict(name='member',sha256=h,bytes=len(content))])]}};target=root/'s/aws/u/ap/8865619b/u/fixture/member'
 elif kind=='direct':mapping={'staged_inputs':{'files':[dict(destination='u/fixture',sha256=h,bytes=len(content))]}};target=root/'s/aws/u/ap/8865619b/u/fixture'
 else:mapping={'small':{'sha256':'a'*64}};target=root/('s/aws/raw.'+'a'*64)/'arbitrary/member'
 target.parent.mkdir(parents=True);target.write_bytes(content);J.write(k/'k/l.json',mapping)
 with patch.dict(os.environ,Q_ROOT=str(root)):
  resolve=px.resolver(k,root/'p',{});assert resolve(h,'config.streams.routing.database')==str(target)
  # A host-looking literal with valid bytes has no authority over resolution.
  unknown='0'*64
  try:resolve(unknown,'config.x')
  except ValueError as e:assert str(e)=='R1_STAGED_PIN_MISSING:'+unknown+':config.x'
  else:raise AssertionError('unlisted input accepted')
  # Native checked() must reject changed bytes, even at the listed location.
  target.write_bytes(b'corrupted')
  try:px.resolver(k,root/'p',{})(h,'config.x')
  except ValueError as e:assert str(e).startswith(('E10:','R1_STAGED_PIN_MISSING:'))
  else:raise AssertionError('corruption accepted')
 cases.append(kind)
assert len({J.sha(kit(name)/'b/px.py') for name in ('q','n','n_go','qd')})==1
J.write(D/'PIN_TESTS.json',dict(status='PASS',sources=cases,corruption_refuses=True,unknown_refuses=True,all_kits_same_resolver=True))
print('five staged source classes, missing pins and corruption PASS')
