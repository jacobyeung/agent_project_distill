import json,os,re
v=None;a=False;c=0;e=False;ec=0;n=None;m=None;d0=False;dc=False;x=False;ok=False
try:
 import torch
 v=str(torch.__version__)
 a=bool(torch.cuda.is_available())
 c=int(torch.cuda.device_count())
 s=os.environ.get('CUDA_VISIBLE_DEVICES')
 e=s is not None;ec=len(s.split(',')) if s else 0
 d0=bool(os.path.exists('/dev/nvidia0'))
 dc=bool(os.path.exists('/dev/nvidiactl'))
 if a and c:
  p=torch.cuda.get_device_properties(0)
  s=p.name;n=s if isinstance(s,str) and re.fullmatch(r'[A-Za-z0-9 ._-]{1,64}',s) else '?'
  m=int(p.total_memory)
 ok=a and c>=1 and m is not None and m>=75*(1<<30)
except Exception:
 x=True
print(json.dumps(dict(v=v,a=a,c=c,e=e,ec=ec,n=n,m=m,d0=d0,dc=dc,x=x)),flush=True)
if x or not ok:
 raise RuntimeError('E42')
