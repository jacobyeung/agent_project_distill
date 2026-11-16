"""NU navigation (schema 8): the model clicks its next waypoint; the floor-plane lift and the controller turn the click
into primitives. The grammar is vla_heads' `nav_grammar_v1` (vendored by sha256 in vendor/nav_text.py).

Sensor (schema 8.2): level camera (pitch 0, roll 0) at h = 1.25 m, HFOV 90, 512 x 512; f = (W/2) / tan(HFOV/2);
principal point at the image centre.
- `floor_plane` (default): for y > 0.5, z = h f / (y W - W/2), P_x = z (x W - W/2) / f, P_z = z. For y <= 0.5 the range
  is undefined and the bearing follows from x with z = 1.
- `g3t_depth` (evaluation check only): z = s d_G3T(x, y), s = h / h_G3T, h_G3T the camera height above the plane fitted
  to G3T points of the lower image half whose normals lie within 10 degrees of G3T's gravity; >= 500 inliers and a
  median residual <= 0.02 h_G3T, else `floor_plane`.
- Bearing beta = atan2(-P_x, P_z) degrees, positive = left; r = sqrt(P_x^2 + P_z^2); L = clamp(r - 0.5, 0, 2.0);
  undefined range -> L = 0.5 m.
- Controller: round(|beta| / 15) turns in the sign of beta, then round(L / 0.25) forward, then a new decision (Python
  round, as navrun.click.controller). Big turns and stop map through nav_text.primitives.
The backend reads only the schema 8.4 observation {frames, instruction, executed, decision_index, constants} and
receives commanded forward metres through executed_commanded(m).
"""
import math

import numpy as np

from .vendor import nav_text as NT

FORWARD, LEFT, RIGHT, STOP = 'forward', 'turn_left', 'turn_right', 'stop'
OBS_KEYS = frozenset(('frames', 'instruction', 'executed', 'decision_index', 'constants'))
SENSOR = dict(rgb_px=512, hfov_deg=90.0, height_m=1.25)
CLICK = dict(range_source='floor_plane', standoff_m=0.5, max_leg_m=2.0, undefined_leg_m=0.5, turn_quantum_deg=15.0,
             forward_step_m=0.25)


def focal(width, hfov_deg):
    return (width / 2) / math.tan(math.radians(hfov_deg) / 2)


def floor_plane(x, y, width=512, hfov_deg=90.0, height_m=1.25):
    """(P_x, P_z) of a click on the floor, or (P_x at z = 1, None) when y <= 0.5 (range undefined)."""
    f = focal(width, hfov_deg)
    if y > 0.5:
        z = height_m * f / (y * width - width / 2)
        return z * (x * width - width / 2) / f, z
    return (x * width - width / 2) / f, None


def bearing_range(px, pz):
    """(beta degrees, positive = left; horizontal range or None)."""
    if pz is None:
        return math.degrees(math.atan2(-px, 1.0)), None
    return math.degrees(math.atan2(-px, pz)), math.hypot(px, pz)


def travel(range_m, standoff_m=0.5, max_leg_m=2.0, undefined_leg_m=0.5):
    return undefined_leg_m if range_m is None else min(max(range_m - standoff_m, 0.0), max_leg_m)


def controller(beta_deg, leg_m, turn_quantum_deg=15.0, forward_step_m=0.25):
    turns = int(round(abs(beta_deg) / turn_quantum_deg))
    return [LEFT if beta_deg > 0 else RIGHT] * turns + [FORWARD] * int(round(leg_m / forward_step_m))


def g3t_floor_scale(depth, K, up, height_m, max_normal_deg=10.0, min_inliers=500, max_residual=0.02):
    """s = h / h_G3T from G3T depth [H, W] (G3T units), K and G3T's camera-frame up vector; None when the fit fails."""
    depth = np.asarray(depth, dtype=np.float64)
    H, W = depth.shape
    rows, cols = np.mgrid[0:H, 0:W]
    P = np.stack([((cols + 0.5) - K[0, 2]) / K[0, 0] * depth, ((rows + 0.5) - K[1, 2]) / K[1, 1] * depth, depth], -1)
    dx, dy = P[1:-1, 2:] - P[1:-1, :-2], P[2:, 1:-1] - P[:-2, 1:-1]
    n = np.cross(dy, dx)
    norm = np.linalg.norm(n, axis=-1, keepdims=True)
    with np.errstate(invalid='ignore', divide='ignore'):
        n = n / norm
    up = np.asarray(up, dtype=np.float64) / np.linalg.norm(up)
    cos = np.abs(n @ up)
    inner = P[1:-1, 1:-1]
    lower = (rows[1:-1, 1:-1] + 0.5) > H / 2
    ok = lower & np.isfinite(cos) & (cos >= math.cos(math.radians(max_normal_deg))) & np.isfinite(inner).all(-1) \
        & (inner[..., 2] > 0)
    heights = -(inner[ok] @ up)
    if heights.size < min_inliers:
        return None, dict(inliers=int(heights.size), why='inliers')
    h = float(np.median(heights))
    resid = float(np.median(np.abs(heights - h)))
    info = dict(inliers=int(heights.size), h_g3t=h, median_residual=resid)
    if h <= 0 or resid > max_residual * h:
        return None, dict(info, why='residual')
    return height_m / h, info


class ClickTranslator:
    """decide(text, obs) -> (primitive names, waypoint {heading_deg, distance_m, stop}, info).

    obs is schema 8.4's whitelist. g3t (only for range_source 'g3t_depth'): frame -> dict(depth=[H, W] G3T units,
    K=3x3, up=[3] camera-frame gravity up), e.g. ViewSetG3T.run([frame]) adapted by the caller. A failed parse returns
    no primitives (the runner re-queries once, then runs the grammar's fallback)."""

    def __init__(self, sensor=None, click=None, g3t=None, history_frames=32):
        self.sensor, self.click = dict(SENSOR, **(sensor or {})), dict(CLICK, **(click or {}))
        if self.click['range_source'] not in ('floor_plane', 'g3t_depth'):
            raise ValueError('range_source must be floor_plane or g3t_depth')
        if self.click['range_source'] == 'g3t_depth' and g3t is None:
            raise ValueError('g3t_depth needs a G3T callback')
        self.g3t, self.history_frames = g3t, history_frames
        self.reset()

    def reset(self):
        self.commanded_m = []

    def executed_commanded(self, metres):
        """Commanded forward metres of the last decision (forward primitives x 0.25), never the simulator's motion."""
        self.commanded_m.append(float(metres))

    def _sensor(self, obs):
        c = obs.get('constants', {}) if isinstance(obs, dict) else {}
        return (c.get('rgb_px', self.sensor['rgb_px']), c.get('hfov_deg', self.sensor['hfov_deg']),
                c.get('height_m', self.sensor['height_m']))

    def lift(self, x, y, obs=None):
        """(beta, range or None, info) for a click (x, y) in uv01."""
        W, hfov, h = self._sensor(obs or {})
        px, pz = floor_plane(x, y, W, hfov, h)
        info = dict(range_source='floor_plane')
        if self.click['range_source'] == 'g3t_depth':
            g = self.g3t(obs['frames'][-1])
            s, fit = g3t_floor_scale(g['depth'], g['K'], g['up'], h)
            info = dict(range_source='floor_plane', g3t_fit=fit)
            if s is not None:
                Hd, Wd = g['depth'].shape
                d = g['depth'][min(int(y * Hd), Hd - 1), min(int(x * Wd), Wd - 1)]
                if np.isfinite(d) and d > 0:
                    f = focal(W, hfov)
                    pz = s * float(d)
                    px = pz * (x * W - W / 2) / f
                    info = dict(range_source='g3t_depth', g3t_fit=fit, scale=s)
        beta, rng = bearing_range(px, pz)
        return beta, rng, info

    def decide(self, text, obs):
        extra = set(obs) - OBS_KEYS
        if extra:
            raise ValueError(f'Navigation backends take only the schema 8.4 observation; got {sorted(extra)}')
        decision = NT.parse(text, 'click', self.history_frames)
        if decision is None:
            return [], None, dict(error='unparsed')
        if not isinstance(decision, NT.Click):
            prims = NT.primitives(decision)
            stop = decision == 'stop'
            turn = {'turn_left 90': 90.0, 'turn_right 90': -90.0, 'turn_around': 180.0}.get(decision, 0.0)
            return prims, dict(heading_deg=turn, distance_m=0.0, stop=stop), dict(decision=decision)
        beta, rng, info = self.lift(decision.x, decision.y, obs)
        leg = travel(rng, self.click['standoff_m'], self.click['max_leg_m'], self.click['undefined_leg_m'])
        prims = controller(beta, leg, self.click['turn_quantum_deg'], self.click['forward_step_m'])
        walked = prims.count(FORWARD) * self.click['forward_step_m']
        info.update(decision='click', x=decision.x, y=decision.y, bearing_deg=beta, range_m=rng, leg_m=leg)
        return prims, dict(heading_deg=beta, distance_m=walked, stop=False), info
