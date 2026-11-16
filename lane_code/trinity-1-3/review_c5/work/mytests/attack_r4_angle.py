"""Calculator angle/turn after heading-unavailable points: are u and v invariant under rotation of frame 1 about gravity?"""
import sys, json, dataclasses
TREE, OUT = sys.argv[1], sys.argv[2]
sys.path[:0] = [TREE, '/scratch/jjyeung/orch_n30/review_c5/work/tests_r5', '/scratch/jjyeung/orch_n30/review_c5/work/mytests']
import numpy as np
from scipy.spatial.transform import Rotation as Rot
from fixtures_contracts import fixture
from trace_format.contracts import contract_epoch
from student_pilot.carrier_c1_routing import OwnGeometry
from student_pilot.carrier_c1_decode import respond
from student_pilot.p3_printed_calculator import PrintedPointRegistry
BASE = np.array([[1., 0, 0], [0, 0, 1], [0, -1, 0]])
def cam(pitch=0., roll=0., yaw=0.):
    return (Rot.from_euler('z', yaw, degrees=True).as_matrix() @ BASE @ Rot.from_euler('x', -pitch, degrees=True).as_matrix() @ Rot.from_euler('z', roll, degrees=True).as_matrix())
CALLS=['<depth_at frame=2 pts=[[200,300],[800,350],[450,800]]>','<angle S=P1 F=P2 Q=P3 rule=hard>','<turn from=P1 at=P2 to=P3>','<dist P1 P2>','<area C=P1,P2,P3>']
def run(yaw):
    c, make = fixture('landscape'); C = c.camera_to_world.copy()
    for i in range(32): C[i,:3,:3] = cam(-88,0,yaw) if i==0 else cam(0,0,3*i)
    R1, c1 = C[0,:3,:3], C[0,:3,3]
    p = np.zeros((32,9)); p[:,6]=1; p[:,7:9]=[.9,1.1]
    for k in range(1,32):
        Rk1 = R1.T @ C[k,:3,:3]; ck = R1.T @ (C[k,:3,3]-c1)
        p[k,:3] = -Rk1.T @ ck; p[k,3:7] = Rot.from_matrix(Rk1.T).as_quat()
    own = OwnGeometry(p, R1.T @ np.array([0,0,1.]), lambda k, pts: 1.5 + np.asarray(pts)[:,0]/400.)
    reg = PrintedPointRegistry(); out={}
    for cl in CALLS: out[cl]=respond(cl, reg, own)[0]
    return out
res={}
for arm in ('on',):
    with contract_epoch(True):
        res={y:run(y) for y in (0,40,130,250)}
json.dump(res, open(OUT,'w'), indent=1)
for cl in CALLS:
    print('==', cl)
    for y,v in res.items(): print('  yaw',y,':',v[cl].replace('\n',' | ')[:230])
