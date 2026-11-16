"""OwnGeometry fixes to_l1 at construction; heading_available is evaluated at call time.
Construct under one (epoch, threshold) and respond under another."""
import sys, json
T=sys.argv[1]; sys.path[:0]=[T,'/scratch/jjyeung/orch_n30/contracts_rebuild/work/tests_r6']
import numpy as np
from trace_format.contracts import contract_epoch
import fixtures_contracts as F
from student_pilot.carrier_c1_decode import respond
from student_pilot.p3_printed_calculator import PrintedPointRegistry
CALLS=['<depth_at frame=2 pts=[[300,500]]>','<pose frame=3>','<move from=1 to=3>']
def geo(pitch):
    contract, make = F.fixture('landscape')
    contract.camera_to_world[0,:3,:3]=F.rotations(pitch,0)
    contract.camera_to_world[1:,:3,:3]=np.array([F.rotations(0,0)@np.array([[np.cos(a),0,np.sin(a)],[0,1,0],[-np.sin(a),0,np.cos(a)]]) for a in np.radians(np.arange(1,32)*7.)])
    return make()
def run(build, use, pitch):
    with contract_epoch(*build[:1], heading_plane_min=build[1]):
        own=F.own_geometry(geo(pitch))
    with contract_epoch(*use[:1], heading_plane_min=use[1]):
        reg=PrintedPointRegistry(); return {c:respond(c,reg,own)[0] for c in CALLS}
out={}
pitch=-80   # plane norm ~0.17: unavailable at 0.3, available at 0.1
for build,use in (((False,.3),(False,.3)),((True,.3),(False,.3)),((True,.1),(True,.1)),((True,.3),(True,.1)),((True,.3),(True,.3))):
    out[f'build={build} use={use}']=run(build,use,pitch)
for k,v in out.items():
    print(k); [print('   ',c,'->',t.replace('\n',' | ')[:150]) for c,t in v.items()]
