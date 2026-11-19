import hashlib,json,sys
from pathlib import Path
import torch
torch.set_num_threads(8)
L=Path('/scratch/jjyeung/orch_n30/so_read');events=[]
def stamp(t):return dict(object_id=id(t),data_ptr=t.data_ptr(),version=t._version)
def check(name,mutate,expected):
 t=torch.nn.Parameter(torch.ones(2));before=stamp(t)
 with torch.no_grad():mutate(t)
 after=stamp(t)
 event=dict(operation=name,before=before,after=after,version_changed=before['version']!=after['version'],
            pointer_changed=before['data_ptr']!=after['data_ptr'],object_changed=before['object_id']!=after['object_id'])
 assert event['version_changed']==expected,event
 events.append(event)
check('parameter.add_',lambda t:t.add_(1),True)
check('detach().add_',lambda t:t.detach().add_(1),True)
check('parameter.data.add_',lambda t:t.data.add_(1),False)
check('parameter.data assignment to cloned storage',lambda t:setattr(t,'data',t.clone()+1),False)
check('parameter.data assignment to same storage',lambda t:setattr(t,'data',t.data),False)
check('numpy raw storage write',lambda t:t.detach().numpy().fill(2),False)
def step(t):
 t.grad=torch.ones_like(t);torch.optim.SGD([t],lr=.1,foreach=False).step()
check('SGD.step foreach=False',step,True)
with torch.inference_mode():t=torch.ones(2)
try:version=t._version
except RuntimeError as error:events.append(dict(operation='inference tensor _version',error=str(error)))
root=Path(torch.__file__).parent
files=['include/c10/core/TensorImpl.h','include/torch/csrc/autograd/VariableTypeUtils.h','autograd/graph.py','optim/sgd.py']
receipt=dict(torch=torch.__version__,threads=torch.get_num_threads(),events=events,
 sources={str(root/p):hashlib.sha256((root/p).read_bytes()).hexdigest() for p in files})
(L/'out/checks/TORCH_VERSIONS3.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
print(json.dumps(receipt,indent=2,sort_keys=True))
