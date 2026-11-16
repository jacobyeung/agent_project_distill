"""r2 heading policy: served fields must not move when a 3-degree gravity error rotates the ill-defined frame-1 basis."""
import sys, json, dataclasses, re
TREE, OUT = sys.argv[1], sys.argv[2]
sys.path[:0] = [TREE, '/scratch/jjyeung/orch_n30/review_contracts/work/btests']
import numpy as np
from pathlib import Path
from scipy.spatial.transform import Rotation as Rot
from fixtures_contracts import fixture, session, response, CALLS
from trace_format.contracts import contract_epoch
from student_pilot.geometry_profiles import ProfileGeometry
from student_pilot.carrier_c1_routing import OwnGeometry
from student_pilot.carrier_c1_decode import respond
from student_pilot.p3_printed_calculator import PrintedPointRegistry

BASE = np.array([[1., 0, 0], [0, 0, 1], [0, -1, 0]])
def cam(pitch=0., roll=0., yaw=0.):
    return (Rot.from_euler('z', yaw, degrees=True).as_matrix() @ BASE
            @ Rot.from_euler('x', -pitch, degrees=True).as_matrix() @ Rot.from_euler('z', roll, degrees=True).as_matrix())

HEAD = ['<pose frame=3>', '<pose frame=1>', '<move from=2 to=5>', '<move from=1 to=4>', '<turn from=2 to=5>', '<turn from=1 to=5>',
        '<move from=6 to=7>', '<turn from=6 to=7>', '<pose frame=6>', '<depth_at frame=2 pts=[[500,500],[100,900]]>',
        '<depth_at frame=1 pts=[[500,500]]>', '<depth_at frame=6 pts=[[500,500]]>']
EXTRA = ['<ground obj="chair" mode="box">', '<ground obj="table" mode="box">', '<gap a="chair" b="table" rule="box_grid_5cm">',
         '<gap camera="3" b="chair" rule="box_grid_5cm">', '<gap camera="3" b="chair" b="table" rule="box_grid_5cm">',
         '<ground obj="chair">', '<ground obj="table">', '<ground obj="chair" mode="instances">', '<ground mode="room">']

def scenario(first, sixth_nadir, tilt):
    c, make = fixture('landscape')
    C = c.camera_to_world.copy()
    noise = np.eye(3) if tilt is None else (Rot.from_euler('z', tilt[1], degrees=True) * Rot.from_euler('x', tilt[0], degrees=True)).as_matrix()
    for i in range(32):
        R = first if i == 0 else (cam(-87) if (sixth_nadir and i == 5) else cam(0, 0, 3 * i))
        C[i, :3, :3] = noise @ R
        C[i, :3, 3] = noise @ C[i, :3, 3]
    c2 = dataclasses.replace(c, camera_to_world=C)
    geo = ProfileGeometry(c2, make().depth_grid)
    s = session(geo, Path('/scratch/jjyeung/orch_n30/review_contracts/work/tmp/r2inv') / f'{tilt}_{sixth_nadir}_{abs(hash(first.tobytes()))}')
    out = {cl: response(s, cl) for cl in EXTRA}
    # heads: OwnGeometry from the same poses, gravity from the (tilted) world
    p = np.zeros((32, 9)); p[:, 6] = 1; p[:, 7:9] = [.9, 1.1]
    R1, c1 = C[0, :3, :3], C[0, :3, 3]
    for k in range(1, 32):
        Rk1 = R1.T @ C[k, :3, :3]; ck = R1.T @ (C[k, :3, 3] - c1)
        p[k, :3] = -Rk1.T @ ck; p[k, 3:7] = Rot.from_matrix(Rk1.T).as_quat()
    own = OwnGeometry(p, R1.T @ np.array([0, 0, 1.]), lambda k, pts: np.full(len(pts), 2.0))
    for cl in HEAD:
        out['HEAD ' + cl] = respond(cl, PrintedPointRegistry(), own)[0]
    return out

res = {}
with contract_epoch(True):
    for label, first, sixth in (('frame1_nadir', cam(-88), False), ('frame1_upright_frame6_nadir', cam(0), True),
                                ('frame1_nadir_frame6_nadir', cam(-88), True)):
        runs = {str(t): scenario(first, sixth, t) for t in (None, (3, 0), (3, 90), (3, 180), (3, 270))}
        res[label] = runs
json.dump(res, open(OUT, 'w'), indent=1)
num = lambda s: [float(x) for x in re.findall(r'-?\d+\.\d+|-?\d+(?= deg)', s)]
for label, runs in res.items():
    print('=====', label)
    keys = list(next(iter(runs.values())))
    for k in keys:
        vals = [runs[t][k] for t in runs]
        if len(set(vals)) == 1:
            print('  SAME  ', k, '->', vals[0].replace('\n', ' | ')[:150])
        else:
            spread = 0.
            try:
                arr = np.array([num(v) for v in vals]); spread = float(np.abs(arr - arr[0]).max())
            except Exception:
                spread = float('nan')
            print('  VARY  ', k, f'max|d|={spread:.2f}', '->', ' || '.join(v.replace('\n', ' | ')[:90] for v in vals[:3]))
