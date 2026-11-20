from pathlib import Path
import sys,json,os,traceback
sys.path[:0]=['/tmp/k/b','/tmp/t']
import z,pl
boundary=z.load('/tmp/f/boundary.json');native=z.checked;calls=[]
def checked(p,h,size=None):
 p=Path(p);calls.append(dict(path=str(p),sha256=h,size=size,boundary=boundary.get(h)==str(p)))
 if str(p).startswith(('/scratch/','/home/','/data','/lustre/')):raise RuntimeError('LITERAL_HOST_PATH:'+str(p))
 if boundary.get(h)==str(p):return p
 return native(p,h,size)
z.checked=pl.checked=checked
v=z.load('/tmp/f/resolved.json');v['kit_sha256']=z.seal('/tmp/k')
try:pl.plan_payload('/tmp/k',v,Path('/tmp/node/p'),regeneration=sys.argv[1]=='r')
except Exception as error:
 z.write('/tmp/node/result.json',dict(refusal=str(error),calls=calls,mode=sys.argv[1],traceback=traceback.format_exc()))
else:z.write('/tmp/node/result.json',dict(refusal=None,calls=calls,mode=sys.argv[1],planner_returned=True))
