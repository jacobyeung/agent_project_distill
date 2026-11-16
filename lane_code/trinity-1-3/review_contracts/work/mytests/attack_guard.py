"""Reviewer's own pose attack on the patched guard, heading policy and decode path (CPU)."""
import json, math, sys
import numpy as np
from scipy.spatial.transform import Rotation as Rot

TREE = sys.argv[1]
sys.path.insert(0, TREE)
from trace_format.contracts import contract_epoch, heading_available
from student_pilot.geometry_profiles import validate_up_convention, GeometryError, GeometryContract
from student_pilot.scene_state import FrameMap

# c2w rotation for a camera with OpenCV axes (x right, y down, z forward) in a z-up world.
# Upright level camera looking along world +y: x_cam=world x, y_cam=-world z, z_cam=world y.
BASE = np.array([[1., 0, 0], [0, 0, 1], [0, -1, 0]])  # columns = camera axes in world


def cam(pitch=0., roll=0., yaw=0.):
    """pitch>0 looks up; roll about optical axis; returns c2w (world <- camera)."""
    Rp = Rot.from_euler('x', pitch, degrees=True).as_matrix()  # about camera x
    Rr = Rot.from_euler('z', roll, degrees=True).as_matrix()   # about camera z (optical)
    Ry = Rot.from_euler('z', yaw, degrees=True).as_matrix()    # world yaw
    # camera x rotation: positive pitch should tilt forward (z) towards up (-y_cam)
    return Ry @ BASE @ Rot.from_euler('x', -pitch, degrees=True).as_matrix() @ Rr


def stats(R):
    up = R[2]  # world up in camera coords (row 2 of c2w)
    return dict(plane=float(np.linalg.norm(up[:2])), margin=float(-up[1]),
                pitch=float(math.degrees(math.asin(np.clip(up[2], -1, 1)))) * -1)


def sealed(Rs):
    return 'refuse' if -Rs[0][2, 1] <= 0 else 'serve'


def patched(Rs):
    try:
        validate_up_convention(np.asarray(Rs)); return 'serve'
    except GeometryError:
        return 'refuse'


def contract_verdict(Rs, epoch):
    C = np.repeat(np.eye(4)[None], 32, 0); C[:, :3, :3] = Rs
    K = np.repeat(np.array([[512., 0, 320], [0, 512, 240], [0, 0, 1]])[None], 32, 0)
    A = np.repeat(np.diag([.64, .48, 1.])[None], 32, 0)
    with contract_epoch(epoch):
        try:
            GeometryContract('legacy_v3122', FrameMap(tuple(range(32))), 0, K, A, C, 1., 'vc', 'metric', 'metric', 0, 1).validate()
            return 'serve'
        except GeometryError as e:
            return 'refuse:' + str(e)


class G:  # minimal geometry for heading_available via cam()
    def __init__(self, R1): self.R1 = R1
    def cam(self, k): return self.R1, np.zeros(3)


rows = []
def case(name, first, rest=None, note=''):
    rest = first if rest is None else rest
    Rs = [first] + [rest] * 31
    r = dict(case=name, **stats(first), sealed=sealed(Rs), patched=patched(Rs),
             contract_on=contract_verdict(Rs, True), contract_off=contract_verdict(Rs, False))
    with contract_epoch(True):
        r['heading_available_on'] = heading_available(G(first))
    with contract_epoch(False):
        r['heading_available_off'] = heading_available(G(first))
    r['note'] = note
    rows.append(r)

up = cam()
case('upright_landscape', up)
case('upright_portrait_storage', up, note='storage hw does not enter R')
for r in (89, 90, 91, -89, -90, -91, 179, 180):
    case(f'roll_{r}', cam(roll=r))
case('pitch_+30', cam(30)); case('pitch_-60', cam(-60))
for p in (-72.0, -72.5, -72.54, -72.55, -73.0):
    case(f'pitch_{p}_upright', cam(p), cam(0))
    case(f'pitch_{p}_inverted_all', cam(p, 180), cam(0, 180))
case('nadir_-88_rest_upright', cam(-88), cam(0))
case('nadir_-88_roll180_rest_upright', cam(-88, 180), cam(0), note='frame1 sign flipped, rest upright: should serve')
case('nadir_-88_rest_inverted', cam(-88), cam(0, 180), note='true inversion seen by frames 2-32')
case('nadir_-88.2_rec41069053_like', cam(-88.2, 130), cam(-30))
case('nadir_-90_exact_rest_upright', cam(-90), cam(0))
case('nadir_all_frames', cam(-89), cam(-89.5), note='no usable frame')
case('nadir_all_frames_inverted', cam(-89, 180), cam(-89.5, 180), note='no usable frame: inversion undetectable')
case('zenith_+88_rest_upright', cam(88), cam(0))
case('zenith_+88_rest_inverted', cam(88), cam(0, 180))
case('nadir_rest_rolled90', cam(-88), cam(0, 90.5), note='median over rolled frames ~ -0.009')
# mixed: frame1 near nadir, half frames upright half inverted
Rs = [cam(-88)] + [cam(0)] * 15 + [cam(0, 180)] * 16
rows.append(dict(case='nadir_15up_16inv', **stats(Rs[0]), sealed=sealed(Rs), patched=patched(Rs),
                 contract_on=contract_verdict(Rs, True), contract_off=contract_verdict(Rs, False), note='median decides'))
# non-orthonormal input
bad = 2 * cam(-80)
rows.append(dict(case='scaled_R_x2_pitch-80_direct', **stats(bad), patched=patched([bad] + [bad] * 31),
                 note='validate_up_convention alone: plane doubles, threshold shifts; contract rejects first'))
rows.append(dict(case='scaled_R_x2_contract', contract_on=contract_verdict([bad] * 32, True)))
nan = cam(); nan = nan.copy(); nan[0, 0] = np.nan
rows.append(dict(case='nan_R_direct', patched=patched([nan] * 32), contract_on=contract_verdict([nan] * 32, True)))
shear = cam(-85) + np.array([[0, 0, 0], [0, 0, 0], [0, .35, 0]])
rows.append(dict(case='sheared_row2_direct', **stats(shear), patched=patched([shear] + [cam(0, 180)] * 31),
                 contract_on=contract_verdict([shear] + [cam(0, 180)] * 31, True)))

for r in rows:
    print(json.dumps(r))
json.dump(rows, open(sys.argv[2], 'w'), indent=1)
