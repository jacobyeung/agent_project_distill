import json,os,torch
a=False;c=0;n=None;m=None;x=False
try:
 a=torch.cuda.is_available()
 c=torch.cuda.device_count()
 if a and c:
  p=torch.cuda.get_device_properties(0)
  n=p.name;m=p.total_memory
except Exception:
 x=True
print(json.dumps(dict(v=torch.__version__,a=a,c=c,e=os.environ.get('CUDA_VISIBLE_DEVICES'),n=n,m=m,d0=os.path.exists('/dev/nvidia0'),dc=os.path.exists('/dev/nvidiactl'),x=x)),flush=True)
if x or not a or c<1 or m is None or m < 75*(1<<30):
 raise RuntimeError('E42')
