"""Which head outputs depend on the frame-1 heading, and does respond() refuse exactly those?"""
import json, sys
import numpy as np
from scipy.spatial.transform import Rotation as Rot
TREE = sys.argv[1]
sys.path.insert(0, TREE)
from trace_format.contracts import contract_epoch
from student_pilot.carrier_c1_routing import OwnGeometry
from student_pilot.carrier_c1_decode import respond
from student_pilot.p3_printed_calculator import PrintedPointRegistry

BASE = np.array([[1., 0, 0], [0, 0, 1], [0, -1, 0]])
def cam(pitch=0., roll=0., yaw=0.):
    return (Rot.from_euler('z', yaw, degrees=True).as_matrix() @ BASE
            @ Rot.from_euler('x', -pitch, degrees=True).as_matrix() @ Rot.from_euler('z', roll, degrees=True).as_matrix())

def geometry(c2w, centres, tilt=None):
    """c2w[k], centres[k] in a z-up world; frame 1 = index 0."""
    R1, c1 = c2w[0], centres[0]
    p = np.zeros((32, 9)); p[:, 6] = 1; p[:, 7:9] = [.9, 1.1]
    for k in range(1, 32):
        Rk1 = R1.T @ c2w[k]; ck = R1.T @ (centres[k] - c1)
        r_rel = Rk1.T
        p[k, :3] = -Rk1.T @ ck
        p[k, 3:7] = Rot.from_matrix(r_rel).as_quat()
    upw = np.array([0, 0, 1.])
    if tilt is not None:
        upw = Rot.from_euler('z', tilt[1], degrees=True).as_matrix() @ Rot.from_euler('x', tilt[0], degrees=True).as_matrix() @ upw
    up = R1.T @ upw
    depth = lambda k, pts: np.full(len(pts), 2.0)
    return OwnGeometry(p, up, depth)

def outputs(g):
    raw = dict(pose2=g.pose_text(2), move23=g.move_text(2, 3), turn23=g.turn_text(2, 3), move12=g.move_text(1, 2))
    reg = PrintedPointRegistry()
    served = {}
    with contract_epoch(True):
        for call in ('<pose frame=2>', '<move from=2 to=3>', '<turn from=2 to=3>', '<move from=1 to=2>', '<depth_at frame=2 pts=[[500,500]]>'):
            served[call] = respond(call, reg, g)[0]
    with contract_epoch(False):
        served_off = {c: respond(c, PrintedPointRegistry(), g)[0] for c in ('<move from=2 to=3>', '<turn from=2 to=3>')}
    return raw, served, served_off

n = 32
centres = np.array([[0.1 * k, 0.05 * k * k % 1, 1.5] for k in range(n)])
out = {}
# A: frame 1 near nadir; frames 2..32 upright with distinct yaws. Re-roll frame 1 about its optical axis (= heading at nadir).
for tilt in (None, (3, 0), (3, 90), (3, 180), (3, 270)):
    c2w = [cam(-88)] + [cam(0, 0, 20 * k) for k in range(1, n)]
    out[f'A_frame1_nadir_gravitynoise{tilt}'] = outputs(geometry(c2w, centres, tilt))
# B: frame 1 upright; frame 2 near nadir, re-rolled about its optical axis.
for tilt in (None, (3, 0), (3, 90), (3, 180), (3, 270)):
    c2w = [cam(0)] + [cam(-88)] + [cam(0, 0, 20 * k) for k in range(2, n)]
    out[f'B_frame2_nadir_gravitynoise{tilt}'] = outputs(geometry(c2w, centres, tilt))
for k, (raw, served, off) in out.items():
    print('==', k)
    print('  raw   :', raw)
    print('  served:', {c: v.replace('\n', ' | ') for c, v in served.items()})
json.dump({k: dict(raw=a, served=b, served_off=c) for k, (a, b, c) in out.items()}, open(sys.argv[2], 'w'), indent=1)
