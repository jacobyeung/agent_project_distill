import math
import numpy as np
from student_pilot.camera_targets import rotation_from_xyzw
FLIP = np.diag([1., -1., 1.])
STENCIL = np.array([(dx,dy) for dx in np.linspace(-10,10,5) for dy in np.linspace(-10,10,5)])

class RenderError(ValueError):
    pass

def r2(x):
    return round(float(x), 2) + 0.0

def f2(x):
    return f'{r2(x):.2f}'

def s2(x):
    return f'{r2(x):+.2f}'

def vec(p):
    return '(' + ', '.join(f2(x) for x in p) + ')'

def wrap(deg):
    return (deg + 180) % 360 - 180 if (deg + 180) % 360 else 180

def r8(a):
    return np.round(np.asarray(a, dtype=np.float64), 8) + 0.0

def level_basis(rotation, down):
    forward = np.asarray(rotation, dtype=np.float64)[:, 2].copy()
    forward -= float(forward @ down) * down
    if np.linalg.norm(forward) < 1e-6:
        raise RenderError('vertical_camera_heading')
    forward /= np.linalg.norm(forward)
    right = np.cross(down, forward)
    return np.column_stack((right, down, forward))

class OwnGeometry:
    """Fixed, parameter-free unprojection and pose layer over own (or hybrid) head outputs.

    pose9: [32, 9] per-frame camera codes E_k = inv(C_k) C_1 (t, q xyzw, FoV vertical,
    FoV horizontal), frame 1 = slot 0. up: frame-1 OpenCV gravity-up vector (None means
    frame-1 camera -y). depth(frame, uv[n, 2]) -> optical-axis metric depth [n].
    Conventions match derivgen's GT layer: frame-1 level frame, public y up, p30 depth
    over a 5x5 +-10 stencil, spread (p80-p20)/max(p50, 1e-3), centred-FoV rays.
    The FoV that conditioned depth (pose slots 7:9) is the FoV used here: `fov` [32, 2]
    overrides pose9's slots when pose comes from GT but depth from the own head.
    depth None means GT clicks: `recorded` {label: (public camera, spread)} supplies them
    and the pose source places them in frame 1 (the reverse hybrid).
    Production refuses a missing gravity vector (require_up).
    """
    def __init__(self, pose9, up, depth, fov=None, recorded=None, require_up=True):
        self.p = np.asarray(pose9, dtype=np.float64)
        if self.p.shape != (32, 9) or not np.isfinite(self.p).all():
            raise RenderError('own pose readout must be finite [32, 9]')
        if up is None and require_up:
            raise RenderError('gravity_unavailable')
        self.fov_override = None if fov is None else np.asarray(fov, dtype=np.float64)
        if self.fov_override is not None and (self.fov_override.shape != (32, 2) or not np.isfinite(self.fov_override).all()):
            raise RenderError('own FoV readout must be finite [32, 2]')
        self.recorded = recorded or {}
        up = np.array([0., -1., 0.]) if up is None else np.asarray(up, dtype=np.float64)
        if up.shape != (3,) or not np.isfinite(up).all() or np.linalg.norm(up) < 1e-6:
            raise RenderError('invalid own gravity')
        self.down = -up / np.linalg.norm(up)
        self.depth = depth
        self.to_l1 = FLIP @ level_basis(np.eye(3), self.down).T
        self._poses = {}

    def camera(self, k):
        if type(k) is not int or not 1 <= k <= 32:
            raise RenderError('frame_out_of_range')
        if k == 1:
            return np.eye(3), np.zeros(3)
        q = self.p[k - 1, 3:7]
        if np.linalg.norm(q) < 1e-6:
            raise RenderError('zero quaternion')
        r_rel = rotation_from_xyzw(q / np.linalg.norm(q))
        rotation = r_rel.T
        return rotation, -rotation @ self.p[k - 1, :3]

    def fov(self, k):
        vertical, horizontal = self.p[k - 1, 7:9] if self.fov_override is None else self.fov_override[k - 1]
        if not (0 < vertical < math.pi and 0 < horizontal < math.pi):
            raise RenderError('invalid own FoV')
        return vertical, horizontal

    def pose(self, k):
        if k not in self._poses:
            rotation, centre = self.camera(k)
            level = r8(self.to_l1 @ level_basis(rotation, self.down))
            self._poses[k] = dict(camera_R_L1=r8(self.to_l1 @ rotation), camera_t_L1=r8(self.to_l1 @ centre),
                                  level_R_L1=level,
                                  yaw_degree=round(math.degrees(math.atan2(-level[0][2], level[2][2]))))
        return self._poses[k]

    def click(self, k, uv, label=None):
        if self.depth is None:
            cam, spread = self.recorded[label]
            pose = self.pose(k)
            f1 = pose['camera_R_L1'] @ (np.asarray(cam, dtype=np.float64) * [1, -1, 1]) + pose['camera_t_L1']
            return list(cam), [r2(x) for x in f1], spread
        uv = np.asarray(uv, dtype=np.float64)
        points = np.clip(uv[None] + STENCIL, 0, 999.9)
        values = np.asarray(self.depth(k, points), dtype=np.float64)
        if values.shape != (len(STENCIL),) or not np.isfinite(values).all() or (values <= 0).any():
            raise RenderError('invalid own depth')
        p20, p30, p50, p80 = (np.percentile(values, q) for q in (20, 30, 50, 80))
        spread = (p80 - p20) / max(p50, 1e-3)
        vertical, horizontal = self.fov(k)
        ray = np.array([(uv[0] / 500 - 1) * math.tan(horizontal / 2), (uv[1] / 500 - 1) * math.tan(vertical / 2), 1.])
        cam = r8(ray * p30)
        pose = self.pose(k)
        f1 = pose['camera_R_L1'] @ cam + pose['camera_t_L1']
        return [r2(x * s) for x, s in zip(cam, (1, -1, 1))], [r2(x) for x in f1], r2(spread)

    def pose_text(self, k):
        p = self.pose(k)
        return f"f1 centre {vec(p['camera_t_L1'])} m, yaw {p['yaw_degree']} deg"

    def move_text(self, i, j):
        pi, pj = self.pose(i), self.pose(j)
        local = pi['level_R_L1'].T @ (pj['camera_t_L1'] - pi['camera_t_L1'])
        distance = float(np.linalg.norm(local))
        local[1] *= -1
        return f'dx = {s2(local[0])} m, dy = {s2(local[1])} m, dz = {s2(local[2])} m, distance = {f2(distance)} m'

    def turn_text(self, i, j):
        a, b = (self.pose(k)['level_R_L1'][[0, 2], 2] for k in (i, j))
        turn = wrap(round(math.degrees(math.atan2(a[0] * b[1] - a[1] * b[0], float(a @ b)))))
        return f'turn = {turn:+d} deg'
