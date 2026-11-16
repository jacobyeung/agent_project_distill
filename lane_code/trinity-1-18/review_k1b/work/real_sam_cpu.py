"""Real SAM 3 weights on CPU through the kit's real GPU.tower/GPU.sam; device moves forced to real copies."""
import sys,json,time,types
from pathlib import Path
kit=Path(sys.argv[1]);out=Path(sys.argv[2])
sys.path.insert(0,str(kit/'native_kit'))
import torch
assert not torch.cuda.is_available(), 'CPU only'
torch.set_num_threads(8)

import functools
def _cpu(dev):
    return 'cpu' if (dev is not None and str(dev).startswith('cuda')) else dev
for _n in ('zeros','ones','empty','full','arange','linspace','tensor','randn','rand','as_tensor','eye','zeros_like','ones_like','empty_like','full_like'):
    _f=getattr(torch,_n)
    def _w(*a,_f=_f,**k):
        if 'device' in k:k['device']=_cpu(k['device'])
        return _f(*a,**k)
    setattr(torch,_n,_w)
_to=torch.Tensor.to
def _tto(self,*a,**k):
    a=tuple(_cpu(x) if isinstance(x,(str,torch.device)) else x for x in a)
    if 'device' in k:k['device']=_cpu(k['device'])
    return _to(self,*a,**k)
torch.Tensor.to=_tto
torch.Tensor.cuda=lambda self,*a,**k:self
import boundaries, bindings as B
from student_pilot import tower_read as G3T
from PIL import Image
m=json.load(open('/scratch/jjyeung/orch_n30/k1_ops3/work/codex_arkit_timing/K1_MANIFEST.arkit_timing.json'))
s=dict(m['gpu'])
b=boundaries.GPU.__new__(boundaries.GPU);b.settings=s;b.device='cpu';b.model=None;b.sam_model=None
caps=[m['captures'][0],m['captures'][1],m['captures'][0]]
log=[]
def forced(self,device):
    self._apply(lambda t:t.to(device='cpu',copy=True));return self
class DummyTower:
    def __init__(self,*a,**k):pass
    def run(self,*a,**k):return None
G3T.FrozenG3TTower=DummyTower
feats0=None
try:
  for i,c in enumerate(caps):
    pin=c['dense_frames'][c['anchor_slots'][0]]
    img=Image.open(B.checked(pin)).convert('RGB')
    t=time.time();b.tower(c,[img])
    sam=b.sam()
    rec=dict(capture=i,canonical=c['canonical'])
    if sam._backend is not None:rec['params_inference_before_encode']=all(q.is_inference() for q in sam._backend.model.parameters())
    f=sam.encode([img]);d=[]
    if i==0:sam._backend.model.to=types.MethodType(forced,sam._backend.model)
    rec.update(encode_detect_s=round(time.time()-t,1),n_det=len(d),feat_sum=float(f.frames[0]['backbone_fpn'][-1].double().sum()))
    if i==0:feats0=f.frames[0]
    if i==2:rec['capture3_equals_capture1']=all(torch.equal(x,y) for k in feats0 for x,y in zip(feats0[k],f.frames[0][k]))
    log.append(rec);print(json.dumps(rec),flush=True)
  res=dict(ok=True)
except Exception as e:
  import traceback;traceback.print_exc();res=dict(ok=False,error=repr(e),at_capture=len(log)+1)
res.update(kit=str(kit),boundaries_sha=B.sha(kit/'native_kit/boundaries.py'),torch=torch.__version__,captures=log)
out.write_text(json.dumps(res,indent=1));print(json.dumps(res))
