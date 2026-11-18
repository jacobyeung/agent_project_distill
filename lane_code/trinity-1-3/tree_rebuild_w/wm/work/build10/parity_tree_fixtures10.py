"""Compare existing geometric test fixtures through the registered readouts."""
from pathlib import Path
import json,sys
L=Path(__file__).resolve().parents[2];B=L/'work/build10';T=L/'work/tree_r1'
sys.path[:0]=[str(B),str(T)]
from monitor9 import Monitor
monitor=Monitor(T)
import numpy as np,torch
from student_pilot.carrier_c1 import CarrierC1
from student_pilot.fixed_readout import DepthReadout,HeadingReadout
from student_pilot.carrier_c1_routing import OwnGeometry
from student_pilot.carrier_c1_decode import respond
from trace_format.calculator import PrintedPointRegistry
from tests.test_carrier_c1_routing import FixedLayerConventions
fixture=FixedLayerConventions();fixture.setUp();old=fixture.own
model=CarrierC1.__new__(CarrierC1);torch.nn.Module.__init__(model);model.auxiliary_heads=torch.nn.Module()
model.auxiliary_heads.depth_readout=DepthReadout();model.auxiliary_heads.heading=HeadingReadout()
def depth(frame,uv,fov):
    sampled=np.full(len(model.auxiliary_heads.depth_readout.stencil),fixture.depth[frame-1])
    return model(dict(depth_map=None,fov_hw=fov,uv=uv,frame=frame,depth_head=None,sampled=sampled),stream='depth_readout')
def heading(op,a,b=None):return model(dict(operation=op,first_rotation=a,second_rotation=b),stream='heading_readout')
new=OwnGeometry(old.p,-old.down,old.depth,readout=depth,heading=heading)
calls=[f'<pose frame={k}>' for k in (1,2,7,18,32)]
calls += [f'<{kind} from={i} to={j}>' for kind in ('move','turn') for i,j in ((2,8),(18,8),(31,4))]
calls += [f'<depth_at frame={k} pts=[[{u},{v}]]>' for k,u,v in ((2,767,848),(14,148,456),(30,500,120))]
counts={};rows=[]
for call in calls:
    before=respond(call,PrintedPointRegistry(32),old)[0];after=respond(call,PrintedPointRegistry(32),new)[0]
    kind=call.split()[0][1:];count=counts.setdefault(kind,dict(checked=0,identical=0,different=0))
    count['checked']+=1;count['identical']+=before==after;count['different']+=before!=after
    rows.append(dict(call=call,before=before,after=after))
out=L/'work/merge11/proofs/parity_tree';out.mkdir(exist_ok=True)
value=dict(status='PASS' if all(v['different']==0 for v in counts.values()) else 'FAIL',counts=counts,examples=rows,
    fixture='work/tree_r1/tests/test_carrier_c1_routing.py:FixedLayerConventions.setUp',
    limitation='Covers the supplied geometric unit-test response fixture. Full external derivgen review-pool geometry and bound real-row operands are unavailable.')
(out/'RESULT.json').write_text(json.dumps(value,indent=2)+'\n');monitor.save(out)
print(json.dumps({'status':value['status'],'counts':counts}))
