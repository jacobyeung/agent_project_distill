from pathlib import Path
import sys,json,os
sys.path[:0]=['/tmp/k/b','/tmp/t']
import z,pl
boundary=z.load('/tmp/f/boundary.json');native=z.checked;calls=[]
def checked(p,h,size=None):
 p=Path(p);calls.append(str(p))
 if str(p).startswith(('/scratch/','/home/','/data','/lustre/')):
  raise RuntimeError('LITERAL_HOST_PATH:'+str(p))
 if boundary.get(h)==str(p):return p
 return native(p,h,size)
z.checked=pl.checked=checked
v=z.load('/tmp/f/resolved.json');v['kit_sha256']=z.seal('/tmp/k')
try:pl.plan_payload('/tmp/k',v,Path('/tmp/node/p'),regeneration=sys.argv[1]=='r')
except Exception as error:
 z.write('/tmp/node/result.json',dict(refusal=str(error),calls=calls,mode=sys.argv[1]))
else:raise AssertionError('expected production boundary')
