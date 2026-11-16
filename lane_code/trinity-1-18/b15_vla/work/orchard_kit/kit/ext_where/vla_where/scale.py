"""Metric scale `proprio_handeye` (schema 6.4) and the hand-eye constant T_eef<-wrist (schema 6.5).

Metric wrist-camera centres: c(k) = p_eef(k) + R_eef(k) t_he, exact under rotation. For each history view h with
||c(t) - c(h)|| >= min_motion_m, r_h = ||c(t) - c(h)|| / ||C_G3T(view 0) - C_G3T(h)||. s = median(r_h), valid iff at
least one r_h exists and max(r) / min(r) - 1 <= max_ratio_spread. (The per-entity range rule, the reported point at most
max_range_m from the wrist camera, lives in the provider.) Nothing carries over between chunks.
"""
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from . import geometry as G


@dataclass(frozen=True)
class HandEye:
    """T_eef<-wrist: R_he (wrist camera axes, OpenCV, into the end-effector frame) and t_he (metres, eef frame)."""
    R: np.ndarray
    t: np.ndarray
    sha256: str = 'unpinned'

    @classmethod
    def load(cls, path, sha256=None):
        raw = Path(path).read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        if sha256 is not None and digest != sha256:
            raise ValueError(f'Hand-eye pin differs: {digest} != {sha256}')
        d = json.loads(raw)
        if d.get('schema') == 'vla_schema_v1/hand_eye':
            return cls(np.asarray(d['R_he'], dtype=np.float64), np.asarray(d['t_he'], dtype=np.float64), digest)
        if d.get('schema') == 'vla_schema_v1' and 'T_eef_cam' in d:      # vla_libero's fit (conformance/hand_eye.json)
            T = np.asarray(d['T_eef_cam'], dtype=np.float64)
            return cls(T[:3, :3], T[:3, 3], digest)
        raise ValueError('Unknown hand-eye schema')

    def T(self):
        return G.rigid(self.R, self.t)


def eef_pose(proprio):
    """T_base<-eef from raw proprio (position 0:3, axis-angle 3:6)."""
    p = np.asarray(proprio, dtype=np.float64)
    return G.rigid(G.axis_angle_to_matrix(p[3:6]), p[0:3])


def wrist_pose(proprio, hand_eye):
    """T_base<-wrist = T_base<-eef T_eef<-wrist."""
    return eef_pose(proprio) @ hand_eye.T()


def centre(proprio, hand_eye):
    p = np.asarray(proprio, dtype=np.float64)
    return p[0:3] + G.axis_angle_to_matrix(p[3:6]) @ hand_eye.t


def reach_base(X_wrist, proprio, hand_eye):
    """The point minus the end-effector position, in base axes: R_eef (R_he X_wrist + t_he)."""
    R_eef = G.axis_angle_to_matrix(np.asarray(proprio, dtype=np.float64)[3:6])
    return R_eef @ (hand_eye.R @ np.asarray(X_wrist, dtype=np.float64) + hand_eye.t)


def proprio_handeye(proprio_t, history, g3t_centres, hand_eye, *, min_motion_m=0.02, max_ratio_spread=0.2):
    """history: {step: proprio} of the G3T history views; g3t_centres: {step: C_G3T(h) in view 0's gauge}.
    Returns (s or None, info)."""
    c_t = centre(proprio_t, hand_eye)
    ratios, info = {}, dict(moved={}, skipped=[])
    for h, p in history.items():
        metric = float(np.linalg.norm(c_t - centre(p, hand_eye)))
        model = float(np.linalg.norm(np.asarray(g3t_centres[h], dtype=np.float64)))
        info['moved'][h] = metric
        if not np.isfinite(metric) or metric < min_motion_m or not np.isfinite(model) or model <= 1e-12:
            info['skipped'].append(h)
            continue
        ratios[h] = metric / model
    info['ratios'] = ratios
    if not ratios:
        info['why'] = 'no_motion'
        return None, info
    r = np.array(list(ratios.values()))
    info['spread'] = float(r.max() / r.min() - 1)
    if info['spread'] > max_ratio_spread:
        info['why'] = 'spread'
        return None, info
    return float(np.median(r)), info


def fit_hand_eye(T_base_eef, T_base_wrist):
    """Least-squares T_eef<-wrist from paired poses (replayed demo states): R by the Kabsch/Procrustes mean of
    R_eef^T R_wrist, t by the mean of R_eef^T (c_wrist - p_eef). Returns (R_he, t_he, residual dict)."""
    A = np.asarray(T_base_eef, dtype=np.float64)
    B = np.asarray(T_base_wrist, dtype=np.float64)
    rel = np.einsum('nji,njk->nik', A[:, :3, :3], B[:, :3, :3])
    U, _, Vt = np.linalg.svd(rel.sum(0))
    R = U @ np.diag([1, 1, np.linalg.det(U @ Vt)]) @ Vt
    ts = np.einsum('nji,nj->ni', A[:, :3, :3], B[:, :3, 3] - A[:, :3, 3])
    t = ts.mean(0)
    pred = np.einsum('nij,j->ni', A[:, :3, :3], t) + A[:, :3, 3]
    pos = np.linalg.norm(pred - B[:, :3, 3], axis=1)
    ang = [np.degrees(np.linalg.norm(G.matrix_to_axis_angle(R.T @ r))) for r in rel]
    return R, t, dict(n=len(A), max_pos_m=float(pos.max()), max_rot_deg=float(max(ang)),
                      ok=bool(pos.max() < 1e-3 and max(ang) < 0.1))


def write_hand_eye(path, R, t, residual, source):
    """Store the fitted constant as JSON; returns its sha256 (the pin that enters configs and cache keys)."""
    text = json.dumps(dict(schema='vla_schema_v1/hand_eye', R_he=np.asarray(R).tolist(), t_he=np.asarray(t).tolist(),
                           residual=residual, source=source), sort_keys=True, indent=1) + '\n'
    Path(path).write_text(text)
    return hashlib.sha256(text.encode()).hexdigest()
