import hashlib,json,sys,os
from pathlib import Path
tree=Path(sys.argv[1]);output=Path(sys.argv[2]);sys.path.insert(0,str(tree))
os.environ['R2_FIXTURES']=str(Path(__file__).resolve().parents[2]/'fixtures')
import torch
torch.set_num_threads(1)
def value(item):
 if isinstance(item,torch.Tensor):
  t=item.detach().cpu().contiguous()
  return dict(shape=list(t.shape),dtype=str(t.dtype),sha256=hashlib.sha256(t.reshape(-1).view(torch.uint8).numpy().tobytes()).hexdigest())
 if isinstance(item,dict):return {k:value(v) for k,v in item.items() if k!='aux_gf1_cache'}
 if isinstance(item,(list,tuple)):return [value(v) for v in item]
 return item if isinstance(item,(str,int,float,bool,type(None))) else type(item).__name__
result={}
from tests.test_carrier_c1 import fixture
model,batch,target=fixture(training_mode='final')
out=model(batch,target,stream='pose');out['loss'].backward()
result['plain']=dict(batch=value(batch),targets=value(target),loss=float(out['loss'].detach()),
 gradients={n:value(p.grad) for n,p in model.named_parameters() if p.grad is not None})
from tests.test_gf1 import fixture as gf
for stage in (1,2):
 model,batch,cfg=gf(stage=stage)
 assert 'cached_bank' not in model.geometry_online['gf1']
 model.eval()
 with torch.no_grad(): out=model(batch,{},stream='vqa')
 result['gf1_stage'+str(stage)]=dict(batch=value(batch),loss=float(out['loss']),output=value(out))
from tests.test_r2_data_path import fixture as row_fixture
from student_pilot import carrier_c1_routing as routing
root=Path(os.environ['TMPDIR'])/'b7_off_row';root.mkdir(exist_ok=True)
row=row_fixture(root,stream='routing')
target,spans,segments=routing.render_full(row['events'],row['answer'])
suffix=target[len(routing.THINK):]
ids=[7+i%40 for i in range(len(suffix))]
offsets=[(i,i+1) for i in range(len(ids))]
train=[not any(s['start']<=i+len(routing.THINK)<s['end'] for s in spans) for i in range(len(ids))]
batch=dict(input_ids=torch.tensor([[2,5]+ids]),labels=torch.tensor([[-100,-100]+ids]))
encoded,audit=routing.finish(batch,ids,train,dict(routing=row),target,spans,'own',offsets,segments)
result['h1_off']=dict(batch=value(encoded),audit=audit,target=target,spans=spans,
 policies={k:v for k,v in routing.POLICIES.items() if k!='both-path-20261116'})
output.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
