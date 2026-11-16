"""Synthetic tabletop scenes with known 3D objects, an agentview camera and a wrist camera on a moving end effector.

A ray caster renders RGB, optical-axis depth and per-object segmentation for axis-aligned boxes. Proprio follows
LIBERO's layout (end-effector position 3, axis-angle 3, gripper 2) in the base (= world) frame, z up, table top at
z = 0, metres. The wrist camera sits at HAND_EYE in the end-effector frame with the end-effector's axes (R_he = I).
`episode(seed)` returns the whitelisted Episode plus the GT frames, names and nouns that backends/gt.py's GTStore
binds; GT never enters the Observation.
"""
import numpy as np

from . import geometry as G
from .cache import Episode
from .scale import HandEye

COLOURS = {'table': (150, 110, 70), 'black bowl': (30, 30, 35), 'black bowl 2': (32, 30, 34), 'plate': (230, 230, 225),
           'ramekin': (200, 170, 120), 'cookie box': (180, 40, 40)}
HAND_EYE_T = np.array([0.0, 0.06, 0.0])
HAND_EYE = HandEye(np.eye(3), HAND_EYE_T, sha256='synthetic-hand-eye-0.06y')
SPATIAL = 'pick up the black bowl next to the plate and place it on the plate'
NAMES = {'black bowl next to the plate': 'black bowl', 'plate': 'plate'}
NOUNS = {'black bowl': ['black bowl', 'black bowl 2'], 'plate': ['plate']}


def default_objects(rng):
    names = ['black bowl', 'black bowl 2', 'plate', 'ramekin', 'cookie box']
    sizes = {'black bowl': (0.10, 0.10, 0.05), 'black bowl 2': (0.10, 0.10, 0.05), 'plate': (0.16, 0.16, 0.02),
             'ramekin': (0.07, 0.07, 0.04), 'cookie box': (0.08, 0.14, 0.06)}
    objects, placed = {}, []
    for name in names:
        for _ in range(200):
            xy = rng.uniform([-0.22, -0.25], [0.22, 0.25])
            if all(np.linalg.norm(xy - q) > 0.15 for q in placed):
                break
        placed.append(xy)
        sx, sy, sz = sizes[name]
        objects[name] = dict(centre=np.array([xy[0], xy[1], sz / 2]), size=np.array([sx, sy, sz]))
    objects['table'] = dict(centre=np.array([0.0, 0.0, -0.025]), size=np.array([1.2, 1.2, 0.05]))
    return objects


def render(objects, T_world_cam, K, width, height):
    """(rgb uint8 [H, W, 3], depth [H, W] optical-axis metres, seg {name: [H, W] bool})."""
    rows, cols = np.mgrid[0:height, 0:width]
    rays_cam = G.unproject_pixels(rows.ravel(), cols.ravel(), np.ones(rows.size), K)
    R, o = T_world_cam[:3, :3], T_world_cam[:3, 3]
    d = rays_cam @ R.T
    best = np.full(len(d), np.inf)
    label = np.full(len(d), -1)
    names = list(objects)
    with np.errstate(divide='ignore', invalid='ignore'):
        inv = 1.0 / d
        for i, name in enumerate(names):
            lo = objects[name]['centre'] - objects[name]['size'] / 2
            hi = objects[name]['centre'] + objects[name]['size'] / 2
            t0, t1 = (lo - o) * inv, (hi - o) * inv
            tmin = np.nanmax(np.minimum(t0, t1), axis=1)
            tmax = np.nanmin(np.maximum(t0, t1), axis=1)
            hit = (tmax >= np.maximum(tmin, 1e-6)) & (tmin > 1e-6) & (tmin < best)
            best[hit], label[hit] = tmin[hit], i
    depth = best.reshape(height, width)
    depth[~np.isfinite(depth)] = np.nan
    rgb = np.zeros((height * width, 3), dtype=np.float64)
    for i, name in enumerate(names):
        rgb[label == i] = COLOURS.get(name, (120, 120, 120))
    shade = np.clip(1.2 - 0.3 * np.nan_to_num(best, nan=3.0, posinf=3.0), 0.4, 1.0)
    rgb = (rgb * shade[:, None]).clip(0, 255).astype(np.uint8).reshape(height, width, 3)
    seg = {name: (label == i).reshape(height, width) for i, name in enumerate(names) if name != 'table'}
    return rgb, depth, seg


def eef_pose(pos, yaw):
    """End effector pointing down (its z axis along world -z), rotated by `yaw` about world z."""
    c, s = np.cos(yaw), np.sin(yaw)
    Rz = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])
    return G.rigid(Rz @ np.diag([1.0, -1.0, -1.0]), pos)


class Scene:
    def __init__(self, seed=0, size=128, agent_fovy=45.0, wrist_fovy=75.0):
        self.rng = np.random.default_rng(seed)
        self.seed = seed
        self.objects = default_objects(self.rng)
        self.size = size
        self.K_agent = G.intrinsics_from_fov(size, size, fovy_deg=agent_fovy)
        self.K_wrist = G.intrinsics_from_fov(size, size, fovy_deg=wrist_fovy)
        eye = np.array([0.75, 0.0, 0.65]) + self.rng.normal(0, 0.03, 3)
        self.T_world_agent = G.look_at(eye, np.array([0.0, 0.0, 0.0]))

    def trajectory(self, steps, target='black bowl', speed=0.012, yaw_rate=0.02):
        start = np.array([0.0, 0.0, 0.42]) + self.rng.normal(0, 0.02, 3)
        goal = self.objects[target]['centre'] + np.array([0.0, 0.0, 0.18])
        out, pos, yaw = [], start, 0.0
        for _ in range(steps):
            out.append((pos.copy(), yaw))
            step = goal - pos
            n = np.linalg.norm(step)
            pos = pos + (step / n * min(speed, n) if n > 1e-9 else 0)
            yaw += yaw_rate
        return out

    def view(self, T, K):
        rgb, depth, seg = render(self.objects, T, K, self.size, self.size)
        return rgb, dict(depth=depth, seg=seg, T_base_cam=T, K=K)

    def episode(self, steps=40, instruction=SPATIAL):
        agent_rgb, agent_gt = self.view(self.T_world_agent, self.K_agent)
        wrist, proprio, frames = [], [], {}
        for t, (pos, yaw) in enumerate(self.trajectory(steps)):
            T_eef = eef_pose(pos, yaw)
            rgb, gt = self.view(T_eef @ HAND_EYE.T(), self.K_wrist)
            wrist.append(rgb)
            proprio.append(np.concatenate([pos, G.matrix_to_axis_angle(T_eef[:3, :3]), [0.04, -0.04]]))
            frames[t] = dict(agent=agent_gt, wrist=gt)
        ep = Episode(instruction, np.stack([agent_rgb] * steps), np.stack(wrist), np.stack(proprio))
        return ep, frames


def episode(seed=0, steps=40, **kwargs):
    """(Episode, GT frames, names, nouns) of one synthetic LIBERO-Spatial-like episode."""
    ep, frames = Scene(seed, **kwargs).episode(steps)
    return ep, frames, NAMES, NOUNS
