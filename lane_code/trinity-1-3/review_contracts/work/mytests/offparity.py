"""Responses of one tree on reviewer fixtures; epoch OFF (or base tree) for byte parity, ON for change list."""
import sys, json, dataclasses, traceback
TREE, MODE, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
sys.path[:0] = [TREE, '/scratch/jjyeung/orch_n30/review_contracts/work/btests']
import numpy as np
from pathlib import Path
from scipy.spatial.transform import Rotation as Rot
import fixtures_contracts as F
from fixtures_contracts import fixture, rotations, session, response
from contextlib import nullcontext
if MODE == 'base':
    ctx = nullcontext
else:
    from trace_format.contracts import contract_epoch
    ctx = lambda: contract_epoch(MODE == 'on')

NAMES = [('chair', 'table'), ('chairs', 'tables'), ('trash can', 'refrigerator'), ('Table Lamp', 'microwave'), ('glasses', 'shelves')]
def calls(a, b):
    return [f'<ground obj="{a}" mode="box">', f'<ground obj="{b}" mode="box">', f'<gap a="{a}" b="{b}" rule="box_grid_5cm">',
            f'<gap camera="3" b="{a}" rule="box_grid_5cm">', f'<gap camera="3" b="{a}" b="{b}" rule="box_grid_5cm">',
            f'<ground obj="{a}">', f'<ground obj="{b}">', f'<gap a="{a}" b="{b}">', f'<ground obj="{a}" mode="instances">',
            '<ground mode="room">', '<ground obj="sofa" mode="box">', f'<gap a="{a}" b="sofa" rule="box_grid_5cm">',
            '<pose frame=3>', '<move from=2 to=5>', '<turn from=2 to=5>', '<depth_at frame=2 pts=[[500,500],[100,900]]>',
            '<dist P1 P2>']

def pose_set():
    out = {}
    for name, (p, r) in dict(level=(0, 0), pitch_m60=(-60, 0), pitch_p40=(40, 0), roll45=(0, 45), roll_m80=(0, -80),
                             zenith80=(80, 0), m70=(-70, 0), m75=(-75, 0), nadir_m85=(-85, 0)).items():
        out[name] = (p, r)
    return out

res = {}
for kind in ('landscape', 'portrait'):
    for pname, (p, r) in pose_set().items():
        for small in (False, True):
            for policy in (False, True):
                for names in NAMES:
                    key = f'{kind}|{pname}|small{int(small)}|pol{int(policy)}|{names[0]}'
                    try:
                        with ctx():
                            c, make = fixture(kind)
                            C = c.camera_to_world.copy()
                            for i in range(32):
                                C[i, :3, :3] = rotations(p, r) @ Rot.from_euler('y', 7 * i, degrees=True).as_matrix()
                            c2 = dataclasses.replace(c, camera_to_world=C)
                            from student_pilot.geometry_profiles import ProfileGeometry
                            geo = ProfileGeometry(c2, make().depth_grid)
                            mk = lambda name, small=small: F.masks(name, small)
                            F_masks = F.masks
                            s = session(geo, Path(f'/scratch/jjyeung/orch_n30/review_contracts/work/tmp/offp_{MODE}') / key.replace('|', '_').replace(' ', '_'),
                                        small=small, policy=policy, names=names)
                            res[key] = {cl: _r for cl in calls(*names) for _r in [None]}
                            for cl in calls(*names):
                                try:
                                    res[key][cl] = response(s, cl)
                                except Exception as e:
                                    res[key][cl] = 'EXC ' + type(e).__name__ + ': ' + str(e)[:200]
                    except Exception as e:
                        res[key] = 'SETUP_EXC ' + type(e).__name__ + ': ' + str(e)[:200]
json.dump(res, open(OUT, 'w'), indent=0, sort_keys=True)
print(len(res), 'cases', sum(isinstance(v, dict) for v in res.values()), 'served-setup')
