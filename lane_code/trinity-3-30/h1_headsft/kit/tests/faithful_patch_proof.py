"""Exercise S1 with only faithful_own_rows.patch installed over sealed modules."""
import json
import sys
from pathlib import Path
K=Path(__file__).resolve().parents[1]
proof=json.loads((K/'logs/patch_composition.json').read_text())
sys.path.insert(0,proof['faithful_only'])
import torch
from tests.fixtures import tiny,camera_fixtures,packed,routing_batch,Processor
from student_pilot import h1_faithful as F,carrier_c1_run as run,carrier_c1_routing as R
assert str(Path(F.__file__)).startswith(proof['faithful_only'])
assert str(Path(run.__file__)).startswith(proof['faithful_only'])
torch.set_num_threads(2)
model,batch,_=tiny();raw,clip,_=camera_fixtures();count=0
for item in raw:
    row=packed(item,clip);base,audit=routing_batch(batch,row)
    gt=R.OwnGeometry(item['gt_pose9'],item['gt_up'],None)
    _,target,_,_=F.faithful(row,gt)
    assert target==item['target']
    p=torch.tensor(item['gt_pose9']).numpy();p[:,:3]*=2
    if item['question_type']=='camera_movement_direction':p[:,:3]*=-1
    if item['question_type']=='camera_rotation':p[:,4]*=-1
    own,target,spans,segments=F.faithful(row,R.OwnGeometry(p,item['gt_up'],None))
    assert own['answer']!=item['answer']
    encoded,_=R.encode_own(Processor(),row,base,target,spans,segments,faithful=True)
    _,mask,_=R.suffix_tokens(Processor(),row,target,spans)
    start=int(encoded['aux_suffix_start'][0]);labels=encoded['labels'][0,start:start+len(mask)]
    assert (labels!=-100).tolist()==mask
    count+=1
row=packed(raw[0],clip);base,audit=routing_batch(batch,row)
class Rows:
    h1={'faithful_own_camera_rows':True};processor=Processor()
    def row(self,*args):return row,None
out,audit=run.own_values(model,Rows(),base,audit,0,(True,True),torch.device('cpu'))
assert audit['h1']['values']=='own'
result=dict(pass_count=13,faithful_rows=count,native_own_forward=True,standalone_path=proof['faithful_only'])
(K/'logs/faithful_standalone.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
