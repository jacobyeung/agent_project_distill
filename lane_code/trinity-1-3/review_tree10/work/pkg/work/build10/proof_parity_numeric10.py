from pathlib import Path
import hashlib,json,sys
L=Path(__file__).resolve().parents[2];B=L/'work/build10';sys.path[:0]=[str(L/'work/tree_r1'),str(B)]
from monitor9 import Monitor
monitor=Monitor(L/'work/tree_r1')
import torch,numpy as np
from student_pilot.carrier_c1 import CarrierC1
from student_pilot.fixed_readout import DepthReadout,HeadingReadout
from student_pilot.carrier_c1_routing import OwnGeometry
from trace_format.calculator import PrintedPointRegistry
from student_pilot.carrier_c1_decode import respond
model=CarrierC1.__new__(CarrierC1);torch.nn.Module.__init__(model)
model.auxiliary_heads=torch.nn.Module()
model.auxiliary_heads.heading=HeadingReadout();model.auxiliary_heads.depth_readout=DepthReadout()
rng=np.random.default_rng(7);counts={};examples=[]
for frame_count in (32,64):
    for index in range(20):
        pose=rng.normal(size=(frame_count,9));pose[:,6]+=2;pose[:,7:9]=1.1
        samples=rng.uniform(.1,10,25)
        old=OwnGeometry(pose,[0,-1,0],lambda frame,uv:samples)
        def depth(frame,uv,fov):
            return model(dict(depth_map=None,fov_hw=fov,uv=uv,frame=frame,depth_head=None,sampled=samples),stream='depth_readout')
        def heading(op,a,b=None):
            return model(dict(operation=op,first_rotation=a,second_rotation=b),stream='heading_readout')
        new=OwnGeometry(pose,[0,-1,0],lambda frame,uv:samples,readout=depth,heading=heading)
        for call in ('<pose frame=2>','<move from=2 to=9>','<turn from=2 to=9>',
                     '<depth_at frame=2 pts=[[500,500],[300,700]]>'):
            left=respond(call,PrintedPointRegistry(frame_count),old)[0]
            right=respond(call,PrintedPointRegistry(frame_count),new)[0]
            kind=call.split()[0][1:];row=counts.setdefault(kind,dict(checked=0,identical=0,different=0))
            row['checked']+=1;row['identical']+=left==right;row['different']+=left!=right
            if left!=right and len(examples)<200:examples.append(dict(call=call,before=left,after=right))
out=B/'proofs/parity';out.mkdir(exist_ok=True)
record=dict(status='PASS' if not examples else 'FAIL',fixture='seeded head outputs; real OwnGeometry, respond, registry and CarrierC1.forward',
            counts=counts,differences=examples,bound_row_parity=False)
(out/'NUMERIC_PARITY.json').write_text(json.dumps(record,indent=2)+'\n');monitor.save(out)
print(json.dumps(record))
