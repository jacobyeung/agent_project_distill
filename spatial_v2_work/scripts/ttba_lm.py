"""5-Step Damped Levenberg-Marquardt Test-Time Bundle Adjustment (TT-BA), K5-S
Perturbation-Stability Gate, and Geo-Maj@K Lie-Algebra Consensus.

Pure NumPy/SciPy implementation designed for <20 ms per clip on CPU (and drop-in
use after DA3-Nested or G3T GPU inference with zero GPU stall).

Conventions:
  - Camera poses are OpenCV camera-to-world c2w: X_w = R_c2w @ X_c + t_c2w,
    where R_c2w = T[:3, :3], t_c2w = T[:3, 3], +Z forward, +X right, +Y down.
  - World-to-camera w2c: T_w2c = inv(T_c2w), R_w2c = R_c2w.T, t_w2c = -R_w2c @ t_c2w.
  - Tangent parameterization for view i: xi_i = [omega_i (3), v_i (3)] in se(3),
    applied as a left perturbation on world-to-camera pose:
      T_w2c_i <- exp(xi_i) @ T_w2c_i,
    so X_c_i' = exp([omega]_x) @ X_c_i + J_l(omega) @ v_i ≈ X_c_i + [omega]_x X_c_i + v_i.
    Gauge is fixed on view 0 (xi_0 = 0).
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

import numpy as np


# ---------------------------------------------------------------------------
# Exact SO(3) / SE(3) Lie algebra utilities
# ---------------------------------------------------------------------------

def skew(w: np.ndarray) -> np.ndarray:
    """Skew-symmetric matrix [w]_x for shape (..., 3) -> (..., 3, 3)."""
    w = np.asarray(w, dtype=np.float64)
    z = np.zeros_like(w[..., 0])
    wx, wy, wz = w[..., 0], w[..., 1], w[..., 2]
    row0 = np.stack([z, -wz, wy], axis=-1)
    row1 = np.stack([wz, z, -wx], axis=-1)
    row2 = np.stack([-wy, wx, z], axis=-1)
    return np.stack([row0, row1, row2], axis=-2)


def so3_exp(omega: np.ndarray) -> np.ndarray:
    """Rodrigues exponential map so(3) -> SO(3) for (3,) or (N, 3)."""
    w = np.asarray(omega, dtype=np.float64)
    single = (w.ndim == 1)
    if single:
        w = w[None, :]
    theta = np.linalg.norm(w, axis=-1)  # (N,)
    K = skew(w)
    K2 = K @ K
    I = np.broadcast_to(np.eye(3, dtype=np.float64), K.shape).copy()

    small = theta < 1e-6
    t2 = theta * theta
    A = np.where(small, 1.0 - t2 / 6.0 + (t2 * t2) / 120.0, np.sin(np.where(small, 1.0, theta)) / np.where(small, 1.0, theta))
    B = np.where(small, 0.5 - t2 / 24.0 + (t2 * t2) / 720.0, (1.0 - np.cos(np.where(small, 1.0, theta))) / np.where(small, 1.0, t2))
    R = I + A[:, None, None] * K + B[:, None, None] * K2
    return R[0] if single else R


def so3_log(R: np.ndarray) -> np.ndarray:
    """Logarithm map SO(3) -> so(3) for (3, 3) or (N, 3, 3)."""
    R = np.asarray(R, dtype=np.float64)
    single = (R.ndim == 2)
    if single:
        R = R[None, :, :]
    out = np.zeros((R.shape[0], 3), dtype=np.float64)
    for i in range(R.shape[0]):
        Ri = R[i]
        tr = np.clip(0.5 * (np.trace(Ri) - 1.0), -1.0, 1.0)
        theta = float(np.arccos(tr))
        vee = 0.5 * np.array([Ri[2, 1] - Ri[1, 2], Ri[0, 2] - Ri[2, 0], Ri[1, 0] - Ri[0, 1]], dtype=np.float64)
        if theta < 1e-6:
            out[i] = vee * (1.0 + (theta * theta) / 6.0)
        elif np.pi - theta < 1e-4:
            # Stable axis extraction near pi via diagonal of (R + I)/2
            diag = np.clip(0.5 * (np.diag(Ri) + 1.0), 0.0, 1.0)
            k = int(np.argmax(diag))
            axis = np.zeros(3, dtype=np.float64)
            axis[k] = np.sqrt(diag[k])
            if axis[k] > 1e-8:
                for j in range(3):
                    if j != k:
                        axis[j] = 0.5 * (Ri[j, k] + Ri[k, j]) / (2.0 * axis[k])
            nrm = np.linalg.norm(axis)
            axis = axis / max(nrm, 1e-12)
            # Disambiguate sign against vee if non-negligible
            if np.linalg.norm(vee) > 1e-8 and np.dot(axis, vee) < 0:
                axis = -axis
            out[i] = theta * axis
        else:
            out[i] = (theta / np.sin(theta)) * vee
    return out[0] if single else out


def _so3_left_jacobian(omega: np.ndarray) -> np.ndarray:
    """Left Jacobian J_l(omega) for se(3) exp map, shape (3, 3)."""
    theta = float(np.linalg.norm(omega))
    K = skew(omega)
    K2 = K @ K
    I = np.eye(3, dtype=np.float64)
    if theta < 1e-6:
        t2 = theta * theta
        return I + (0.5 - t2 / 24.0) * K + (1.0 / 6.0 - t2 / 120.0) * K2
    return I + ((1.0 - np.cos(theta)) / (theta * theta)) * K + ((theta - np.sin(theta)) / (theta ** 3)) * K2


def _so3_left_jacobian_inv(omega: np.ndarray) -> np.ndarray:
    """Inverse left Jacobian J_l^{-1}(omega) for se(3) log map, shape (3, 3)."""
    theta = float(np.linalg.norm(omega))
    K = skew(omega)
    K2 = K @ K
    I = np.eye(3, dtype=np.float64)
    if theta < 1e-6:
        return I - 0.5 * K + (1.0 / 12.0) * K2
    half = 0.5 * theta
    cot_half = np.cos(half) / max(np.sin(half), 1e-12)
    c = (1.0 - half * cot_half) / (theta * theta)
    return I - 0.5 * K + c * K2


def se3_exp(xi: np.ndarray) -> np.ndarray:
    """Exponential map se(3) -> SE(3). xi = [omega(3), v(3)]."""
    xi = np.asarray(xi, dtype=np.float64)
    single = (xi.ndim == 1)
    if single:
        xi = xi[None, :]
    T = np.broadcast_to(np.eye(4, dtype=np.float64), (xi.shape[0], 4, 4)).copy()
    for i in range(xi.shape[0]):
        w, v = xi[i, :3], xi[i, 3:6]
        T[i, :3, :3] = so3_exp(w)
        T[i, :3, 3] = _so3_left_jacobian(w) @ v
    return T[0] if single else T


def se3_log(T: np.ndarray) -> np.ndarray:
    """Logarithm map SE(3) -> se(3), returning [omega(3), v(3)]."""
    T = np.asarray(T, dtype=np.float64)
    single = (T.ndim == 2)
    if single:
        T = T[None, :, :]
    out = np.zeros((T.shape[0], 6), dtype=np.float64)
    for i in range(T.shape[0]):
        w = so3_log(T[i, :3, :3])
        v = _so3_left_jacobian_inv(w) @ T[i, :3, 3]
        out[i, :3] = w
        out[i, 3:6] = v
    return out[0] if single else out


def invert_se3(T: np.ndarray) -> np.ndarray:
    """Fast exact inverse of rigid SE(3) matrix (4, 4) or (N, 4, 4)."""
    T = np.asarray(T, dtype=np.float64)
    single = (T.ndim == 2)
    if single:
        T = T[None, :, :]
    R = T[:, :3, :3]
    t = T[:, :3, 3]
    Rt = np.swapaxes(R, -1, -2)
    inv = np.broadcast_to(np.eye(4, dtype=np.float64), T.shape).copy()
    inv[:, :3, :3] = Rt
    inv[:, :3, 3] = -np.einsum("nij,nj->ni", Rt, t)
    return inv[0] if single else inv


def geodesic_rot_deg(R_a: np.ndarray, R_b: np.ndarray) -> np.ndarray:
    """Exact geodesic rotation angle in degrees between (..., 3, 3) rotation matrices.

    Uses the chord-length identity ||R_a - R_b||_F = 2*sqrt(2)*sin(theta/2) to avoid
    the sqrt(eps) precision loss of arccos near theta = 0.
    """
    diff = np.asarray(R_a, dtype=np.float64) - np.asarray(R_b, dtype=np.float64)
    frob = np.sqrt(np.sum(diff * diff, axis=(-2, -1)))
    s = np.clip(frob / (2.0 * np.sqrt(2.0)), 0.0, 1.0)
    return np.degrees(2.0 * np.arcsin(s))


def align_trajectory_rigid(
    pred_c2w: np.ndarray,
    gt_c2w: np.ndarray,
    with_scale: bool = False,
) -> dict[str, Any]:
    """Umeyama alignment of pred_c2w camera centers to gt_c2w (matching gt/v2.py).

    Returns translation_rms_m, rotation_rms_deg, rotation_max_deg, scale, accepted
    (pass rule: translation_rms_m <= 0.10 and rotation_max_deg <= 5.0), and class
    ('gross' if rotation_max_deg > 60 else 'pass' if accepted else 'moderate').
    """
    P = np.asarray(pred_c2w, dtype=np.float64)
    G = np.asarray(gt_c2w, dtype=np.float64)
    pc = P[:, :3, 3]
    gc = G[:, :3, 3]
    mu_p = pc.mean(axis=0)
    mu_g = gc.mean(axis=0)
    X = pc - mu_p
    Y = gc - mu_g
    H = (Y.T @ X) / len(pc)
    U, S, Vt = np.linalg.svd(H)
    d = np.sign(np.linalg.det(U @ Vt))
    D = np.diag([1.0, 1.0, d if d != 0 else 1.0])
    R_align = U @ D @ Vt
    if with_scale:
        var_p = float(np.mean(np.sum(X * X, axis=1)))
        s = float(np.sum(S * np.diag(D)) / max(var_p, 1e-12))
    else:
        s = 1.0
    t_align = mu_g - s * (R_align @ mu_p)
    aligned_c = s * (pc @ R_align.T) + t_align
    trans_err = np.linalg.norm(aligned_c - gc, axis=1)
    aligned_R = np.einsum("ij,njk->nik", R_align, P[:, :3, :3])
    rot_err = geodesic_rot_deg(aligned_R, G[:, :3, :3])
    t_rms = float(np.sqrt(np.mean(trans_err ** 2)))
    r_rms = float(np.sqrt(np.mean(rot_err ** 2)))
    r_max = float(np.max(rot_err))
    accepted = (t_rms <= 0.10) and (r_max <= 5.0)
    cls = "gross" if r_max > 60.0 else ("pass" if accepted else "moderate")
    return dict(
        translation_rms_m=t_rms,
        rotation_rms_deg=r_rms,
        rotation_max_deg=r_max,
        rotation_median_deg=float(np.median(rot_err)),
        scale=s,
        accepted=accepted,
        cls=cls,
        R_align=R_align,
        t_align=t_align,
        per_frame_rot_deg=rot_err,
        per_frame_trans_m=trans_err,
    )


# ---------------------------------------------------------------------------
# 5-Step Damped Levenberg-Marquardt Test-Time Bundle Adjustment (TT-BA)
# ---------------------------------------------------------------------------

@dataclass
class Correspondences:
    """Cross-view geometric observations for TT-BA.

    Each edge e links a 3D point observed in source frame src_idx[e] at pixel
    uv_src[e] with depth z_src[e] to target frame dst_idx[e] at pixel uv_dst[e]
    with optional depth z_dst[e] and static rigidity weight rigidity[e] in [0, 1].
    """
    src_idx: np.ndarray   # (E,) int64
    dst_idx: np.ndarray   # (E,) int64
    uv_src: np.ndarray    # (E, 2) float64 pixel coords
    z_src: np.ndarray     # (E,) float64 metric depth in source frame
    uv_dst: np.ndarray    # (E, 2) float64 pixel coords in target frame
    z_dst: np.ndarray | None = None      # (E,) float64 optional target depth
    rigidity: np.ndarray | None = None   # (E,) float64 static-rigidity weight in [0, 1]


@dataclass
class ScaleAnchor:
    """Optional metric scale anchor(s) for resolving monocular/sim scale drift
    (e.g., Habitat 1.94x scale drift via floor height, FK baseline, or DA3 metric prior).

    - baseline_pairs: list of (i, j, metric_dist_m, weight) tying ||t_i - t_j|| -> metric_dist_m.
    - scale_prior: optional (target_scale, weight) soft anchor on global scale s.
    """
    baseline_pairs: list[tuple[int, int, float, float]] = field(default_factory=list)
    scale_prior: tuple[float, float] | None = None


@dataclass
class TTBAResult:
    c2w: np.ndarray
    scale: float
    committed: bool
    initial_cost: float
    final_cost: float
    rel_cost_drop: float
    iterations: int
    wall_ms: float
    inlier_ratio: float
    cost_history: list[float]


def huber_weights(res_norm: np.ndarray, delta: float) -> np.ndarray:
    """Redescending Cauchy-Huber IRLS weights: 1 / (1 + (|r|/delta)^2) for |r| > delta."""
    u2 = (res_norm / max(delta, 1e-12)) ** 2
    return np.where(res_norm <= delta, 1.0, 1.0 / (1.0 + u2))


def huber_loss(res_norm: np.ndarray, delta: float) -> np.ndarray:
    """Smooth redescending Cauchy-Huber loss matching huber_weights."""
    d2 = delta * delta
    u2 = (res_norm / max(delta, 1e-12)) ** 2
    return np.where(res_norm <= delta, 0.5 * res_norm * res_norm, 0.5 * d2 * (1.0 + np.log(0.5 * (1.0 + u2))))


def _unproject_rays(uv: np.ndarray, K: np.ndarray, frame_idx: np.ndarray) -> np.ndarray:
    """Back-project pixel coordinates uv (E, 2) into normalized camera rays (E, 3)."""
    fx = K[frame_idx, 0, 0]
    fy = K[frame_idx, 1, 1]
    cx = K[frame_idx, 0, 2]
    cy = K[frame_idx, 1, 2]
    x = (uv[:, 0] - cx) / fx
    y = (uv[:, 1] - cy) / fy
    return np.stack([x, y, np.ones_like(x)], axis=-1)


@dataclass
class _PairLayout:
    """Pre-sorted edge grouping by (src, dst) computed once per TT-BA call."""
    order: np.ndarray
    pair_src: np.ndarray
    pair_dst: np.ndarray
    starts: np.ndarray
    ends: np.ndarray


def _build_pair_layout(src: np.ndarray, dst: np.ndarray, N: int) -> _PairLayout:
    pair_keys = src * N + dst
    order = np.argsort(pair_keys, kind="mergesort")
    sorted_keys = pair_keys[order]
    if len(sorted_keys) == 0:
        z = np.zeros(0, dtype=np.int64)
        return _PairLayout(order, z, z, z, z)
    boundaries = np.flatnonzero(np.diff(sorted_keys)) + 1
    starts = np.concatenate([[0], boundaries])
    ends = np.concatenate([boundaries, [len(sorted_keys)]])
    uniq = sorted_keys[starts]
    pair_src = uniq // N
    pair_dst = uniq % N
    return _PairLayout(order=order, pair_src=pair_src, pair_dst=pair_dst, starts=starts, ends=ends)


def _eval_residuals_and_jacobian(
    w2c: np.ndarray,
    log_s: float,
    K: np.ndarray,
    corr: Correspondences,
    rays_src: np.ndarray,
    layout: _PairLayout,
    w_reproj: float,
    w_depth: float,
    huber_px: float,
    huber_logz: float,
    optimize_scale: bool,
    scale_anchor: ScaleAnchor | None,
    need_jac: bool = True,
) -> tuple[float, np.ndarray | None, np.ndarray | None, float]:
    """Compute robust Huber cost and (optionally) normal equations H = J^T W J, g = J^T W r.

    Expects corr and rays_src already ordered by layout.order for zero-copy pair slicing.
    """
    N = w2c.shape[0]
    E = len(corr.src_idx)
    n_pose_vars = 6 * (N - 1)
    D = n_pose_vars + (1 if optimize_scale else 0)

    s = float(np.exp(log_s))
    src = corr.src_idx
    dst = corr.dst_idx
    rig = np.ones(E, dtype=np.float64) if corr.rigidity is None else corr.rigidity

    # 3D point in source camera frame (scaled by s)
    X_src = (s * corr.z_src)[:, None] * rays_src  # (E, 3)

    # Transform source -> world -> destination via batched matmul (much faster than einsum)
    R_s = w2c[src, :3, :3]          # (E, 3, 3)
    t_s = w2c[src, :3, 3] * s       # (E, 3)
    R_d = w2c[dst, :3, :3]          # (E, 3, 3)
    t_d = w2c[dst, :3, 3] * s       # (E, 3)

    # X_w = R_s^T (X_src - t_s); X_dst = R_d X_w + t_d
    X_w = np.matmul(np.swapaxes(R_s, -1, -2), (X_src - t_s)[..., None])[..., 0]
    X_dst = np.matmul(R_d, X_w[..., None])[..., 0] + t_d

    Z = X_dst[:, 2]
    valid = (Z > 1e-3) & (rig > 1e-4)
    Z_safe = np.where(valid, Z, 1.0)
    invZ = 1.0 / Z_safe

    fx = K[dst, 0, 0]
    fy = K[dst, 1, 1]
    cx = K[dst, 0, 2]
    cy = K[dst, 1, 2]

    u_pred = fx * (X_dst[:, 0] * invZ) + cx
    v_pred = fy * (X_dst[:, 1] * invZ) + cy

    res_u = np.where(valid, u_pred - corr.uv_dst[:, 0], 0.0)
    res_v = np.where(valid, v_pred - corr.uv_dst[:, 1], 0.0)
    res_px = np.hypot(res_u, res_v)

    w_hub_2d = huber_weights(res_px, huber_px)
    w_eff_2d = np.where(valid, (w_reproj ** 2) * rig * w_hub_2d, 0.0)
    cost = float(np.sum(np.where(valid, (w_reproj ** 2) * rig * huber_loss(res_px, huber_px), 0.0)))
    inlier_ratio = float(np.mean(res_px[valid] <= huber_px)) if np.any(valid) else 0.0

    use_depth = (corr.z_dst is not None) and (w_depth > 0.0)
    if use_depth:
        z_dst_s = s * corr.z_dst
        valid_d = valid & (z_dst_s > 1e-3)
        res_z = np.where(valid_d, np.log(Z_safe) - np.log(np.where(valid_d, z_dst_s, 1.0)), 0.0)
        w_hub_z = huber_weights(np.abs(res_z), huber_logz)
        w_eff_z = np.where(valid_d, (w_depth ** 2) * rig * w_hub_z, 0.0)
        cost += float(np.sum(np.where(valid_d, (w_depth ** 2) * rig * huber_loss(np.abs(res_z), huber_logz), 0.0)))
    else:
        res_z = np.zeros(E, dtype=np.float64)
        w_eff_z = np.zeros(E, dtype=np.float64)

    anchor_res = []
    if scale_anchor is not None:
        c2w_c = -np.matmul(np.swapaxes(w2c[:, :3, :3], -1, -2), w2c[:, :3, 3:4])[..., 0] * s
        for i, j, d_gt, w_b in scale_anchor.baseline_pairs:
            diff = c2w_c[i] - c2w_c[j]
            d_est = float(np.linalg.norm(diff))
            r_b = d_est - d_gt
            cost += 0.5 * (w_b ** 2) * (r_b ** 2)
            anchor_res.append(("baseline", i, j, diff, d_est, r_b, w_b))
        if scale_anchor.scale_prior is not None:
            s_prior, w_p = scale_anchor.scale_prior
            r_p = log_s - float(np.log(max(s_prior, 1e-6)))
            cost += 0.5 * (w_p ** 2) * (r_p ** 2)
            anchor_res.append(("prior", r_p, w_p))

    if not need_jac:
        return cost, None, None, inlier_ratio

    invZ2 = invZ * invZ
    R_rel = np.matmul(R_d, np.swapaxes(R_s, -1, -2))

    J_proj = np.zeros((E, 2, 3), dtype=np.float64)
    J_proj[:, 0, 0] = fx * invZ
    J_proj[:, 0, 2] = -fx * X_dst[:, 0] * invZ2
    J_proj[:, 1, 1] = fy * invZ
    J_proj[:, 1, 2] = -fy * X_dst[:, 1] * invZ2

    dX_ddst = np.zeros((E, 3, 6), dtype=np.float64)
    dX_ddst[:, :, :3] = -skew(X_dst)
    dX_ddst[:, 0, 3] = 1.0
    dX_ddst[:, 1, 4] = 1.0
    dX_ddst[:, 2, 5] = 1.0

    dX_dsrc = np.zeros((E, 3, 6), dtype=np.float64)
    dX_dsrc[:, :, :3] = np.matmul(R_rel, skew(X_src))
    dX_dsrc[:, :, 3:] = -R_rel

    J2_dst = np.matmul(J_proj, dX_ddst)
    J2_src = np.matmul(J_proj, dX_dsrc)

    H = np.zeros((D, D), dtype=np.float64)
    g = np.zeros(D, dtype=np.float64)

    res_2d = np.stack([res_u, res_v], axis=-1)
    wJ2_dst = J2_dst * w_eff_2d[:, None, None]
    wJ2_src = J2_src * w_eff_2d[:, None, None]

    if use_depth:
        Jz_dst = dX_ddst[:, 2, :] * invZ[:, None]
        Jz_src = dX_dsrc[:, 2, :] * invZ[:, None]
        wJz_dst = Jz_dst * w_eff_z[:, None]
        wJz_src = Jz_src * w_eff_z[:, None]
    else:
        Jz_dst = Jz_src = wJz_dst = wJz_src = None

    for si, di, st, en in zip(layout.pair_src, layout.pair_dst, layout.starts, layout.ends):
        m = int(en - st)
        Jd = J2_dst[st:en].reshape(2 * m, 6)
        Js = J2_src[st:en].reshape(2 * m, 6)
        wJd = wJ2_dst[st:en].reshape(2 * m, 6)
        wJs = wJ2_src[st:en].reshape(2 * m, 6)
        r2 = res_2d[st:en].reshape(2 * m)

        if di > 0:
            od = slice(6 * (di - 1), 6 * di)
            H[od, od] += wJd.T @ Jd
            g[od] += wJd.T @ r2
            if use_depth:
                H[od, od] += wJz_dst[st:en].T @ Jz_dst[st:en]
                g[od] += wJz_dst[st:en].T @ res_z[st:en]
        if si > 0:
            os_ = slice(6 * (si - 1), 6 * si)
            H[os_, os_] += wJs.T @ Js
            g[os_] += wJs.T @ r2
            if use_depth:
                H[os_, os_] += wJz_src[st:en].T @ Jz_src[st:en]
                g[os_] += wJz_src[st:en].T @ res_z[st:en]
        if si > 0 and di > 0:
            od = slice(6 * (di - 1), 6 * di)
            os_ = slice(6 * (si - 1), 6 * si)
            Hds = wJd.T @ Js
            if use_depth:
                Hds = Hds + wJz_dst[st:en].T @ Jz_src[st:en]
            H[od, os_] += Hds
            if si != di:
                H[os_, od] += Hds.T

    if anchor_res:
        c2w_R = np.swapaxes(w2c[:, :3, :3], -1, -2)
        for item in anchor_res:
            if item[0] == "baseline":
                _, i, j, diff, d_est, r_b, w_b = item
                if d_est < 1e-8:
                    continue
                n_hat = diff / d_est
                j_vec = np.zeros(D, dtype=np.float64)
                if i > 0:
                    j_vec[6 * (i - 1) + 3 : 6 * i] = -(c2w_R[i].T @ n_hat)
                if j > 0:
                    j_vec[6 * (j - 1) + 3 : 6 * j] = +(c2w_R[j].T @ n_hat)
                if optimize_scale:
                    j_vec[D - 1] = d_est
                w2 = w_b * w_b
                H += w2 * np.outer(j_vec, j_vec)
                g += w2 * r_b * j_vec
            elif item[0] == "prior" and optimize_scale:
                _, r_p, w_p = item
                H[D - 1, D - 1] += w_p * w_p
                g[D - 1] += (w_p * w_p) * r_p

    return cost, H, g, inlier_ratio


def run_ttba_lm(
    init_c2w: np.ndarray,
    K: np.ndarray,
    corr: Correspondences,
    *,
    max_iters: int = 5,
    w_reproj: float = 1.0,
    w_depth: float = 2.0,
    huber_px: float = 4.0,
    huber_logz: float = 0.08,
    lambda_init: float = 1e-2,
    min_rel_drop: float = 0.05,
    optimize_scale: bool = False,
    scale_anchor: ScaleAnchor | None = None,
    always_commit: bool = False,
) -> TTBAResult:
    """Run <=5-step damped Levenberg-Marquardt Test-Time Bundle Adjustment.

    Args:
      init_c2w: (N, 4, 4) initial OpenCV camera-to-world poses.
      K: (N, 3, 3) camera intrinsics in pixels matching corr.uv_src / corr.uv_dst.
      corr: Correspondences with optional static rigidity mask in [0, 1].
      max_iters: Maximum LM iterations (default 5, <20 ms target).
      min_rel_drop: Require relative robust cost drop >= min_rel_drop to commit
        (prevents regressions on already-passing captures).
      optimize_scale: If True, jointly refine global metric scale s = exp(log_s)
        using scale_anchor (fixes monocular/sim 1.94x scale drift).
    """
    t0 = time.perf_counter()
    init_c2w = np.asarray(init_c2w, dtype=np.float64)
    K = np.asarray(K, dtype=np.float64)
    N = init_c2w.shape[0]
    w2c = invert_se3(init_c2w)
    log_s = 0.0

    rays_src_raw = _unproject_rays(corr.uv_src, K, corr.src_idx)
    layout = _build_pair_layout(corr.src_idx, corr.dst_idx, N)
    ord_idx = layout.order
    corr_s = Correspondences(
        src_idx=corr.src_idx[ord_idx],
        dst_idx=corr.dst_idx[ord_idx],
        uv_src=corr.uv_src[ord_idx],
        z_src=corr.z_src[ord_idx],
        uv_dst=corr.uv_dst[ord_idx],
        z_dst=None if corr.z_dst is None else np.asarray(corr.z_dst, dtype=np.float64)[ord_idx],
        rigidity=None if corr.rigidity is None else np.clip(np.asarray(corr.rigidity, dtype=np.float64)[ord_idx], 0.0, 1.0),
    )
    rays_src = rays_src_raw[ord_idx]

    cost, H, g, inlier_ratio = _eval_residuals_and_jacobian(
        w2c, log_s, K, corr_s, rays_src, layout,
        w_reproj, w_depth, huber_px, huber_logz,
        optimize_scale, scale_anchor, need_jac=True,
    )
    init_cost = cost
    history = [cost]
    lam = float(lambda_init)
    D = H.shape[0]
    iters_done = 0

    for it in range(max_iters):
        iters_done = it + 1
        diag = np.maximum(np.diag(H), 1e-6)
        accepted_step = False
        for _ in range(4):
            H_damped = H + lam * np.diag(diag) + 1e-6 * np.eye(D)
            try:
                dx = -np.linalg.solve(H_damped, g)
            except np.linalg.LinAlgError:
                lam = min(lam * 10.0, 1e6)
                continue
            if not np.all(np.isfinite(dx)):
                lam = min(lam * 10.0, 1e6)
                continue

            # Apply candidate update (gauge-fixed view 0)
            s_cur = float(np.exp(log_s))
            w2c_cand = w2c.copy()
            for v in range(1, N):
                xi_v = dx[6 * (v - 1) : 6 * v].copy()
                # Cap extreme per-step rotation/translation jumps for numerical stability
                w_norm = float(np.linalg.norm(xi_v[:3]))
                if w_norm > 0.7:
                    xi_v[:3] *= 0.7 / w_norm
                # Perturbation was computed in scaled coordinates (t_w2c * s_cur)
                T_scaled = w2c_cand[v].copy()
                T_scaled[:3, 3] *= s_cur
                T_upd = se3_exp(xi_v) @ T_scaled
                T_upd[:3, 3] /= s_cur
                w2c_cand[v] = T_upd

            log_s_cand = log_s
            if optimize_scale:
                log_s_cand = float(np.clip(log_s + np.clip(dx[D - 1], -0.8, 0.8), -2.5, 2.5))

            cand_cost, _, _, cand_inlier = _eval_residuals_and_jacobian(
                w2c_cand, log_s_cand, K, corr_s, rays_src, layout,
                w_reproj, w_depth, huber_px, huber_logz,
                optimize_scale, scale_anchor, need_jac=False,
            )
            if cand_cost < cost:
                w2c = w2c_cand
                log_s = log_s_cand
                cost = cand_cost
                inlier_ratio = cand_inlier
                lam = max(lam / 3.0, 1e-6)
                accepted_step = True
                break
            lam = min(lam * 5.0, 1e6)

        history.append(cost)
        if not accepted_step:
            break
        if it + 1 < max_iters:
            cost, H, g, inlier_ratio = _eval_residuals_and_jacobian(
                w2c, log_s, K, corr_s, rays_src, layout,
                w_reproj, w_depth, huber_px, huber_logz,
                optimize_scale, scale_anchor, need_jac=True,
            )

    rel_drop = ((init_cost - cost) / init_cost) if (init_cost > 1e-4 and (init_cost - cost) > 1e-4) else 0.0
    commit = always_commit or (rel_drop >= min_rel_drop)
    if commit:
        s_final = float(np.exp(log_s))
        c2w_out = invert_se3(w2c)
        c2w_out[:, :3, 3] *= s_final
    else:
        s_final = 1.0
        c2w_out = init_c2w.copy()

    wall_ms = (time.perf_counter() - t0) * 1000.0
    return TTBAResult(
        c2w=c2w_out,
        scale=s_final,
        committed=commit,
        initial_cost=float(init_cost),
        final_cost=float(cost),
        rel_cost_drop=float(rel_drop),
        iterations=iters_done,
        wall_ms=float(wall_ms),
        inlier_ratio=float(inlier_ratio),
        cost_history=history,
    )


def build_depth_correspondences(
    c2w: np.ndarray,
    K: np.ndarray,
    depth_grid: np.ndarray,
    grid_uv: np.ndarray,
    *,
    frame_offsets: tuple[int, ...] = (1, 2, 4),
    stride: int = 4,
    max_reproj_px: float = 35.0,
    max_depth_rel: float = 0.25,
    conf_grid: np.ndarray | None = None,
) -> Correspondences:
    """Build geometric cross-view correspondences from predicted depth grids & poses.

    Used on real captures when running TT-BA directly on tower outputs (DA3/G3T):
    projects strided pixels from frame i into nearby frames j = i + offset, filters
    by cycle/depth consistency and optional confidence to derive a soft rigidity mask.
    """
    N, H, W = depth_grid.shape
    uv_x = np.asarray(grid_uv, dtype=np.float64)
    # Assume grid_uv is normalized pixel coords in [0, W] x [0, H] or [0, 1000]; caller passes pixel coords
    xs = uv_x[::stride]
    ys = uv_x[::stride] if len(uv_x) == H else np.linspace(0, H - 1, H)[::stride]
    if len(uv_x) != W:
        xs = np.linspace(0, W - 1, W)[::stride]

    w2c = invert_se3(c2w)
    src_list, dst_list, uvs_list, zs_list, uvd_list, zd_list, rig_list = [], [], [], [], [], [], []

    # Precompute 3D camera-frame point cloud Y_cam (N, H, W, 3) and unit surface normals N_cam (N, H, W, 3)
    rr_full = np.arange(H, dtype=np.float64)
    cc_full = np.arange(W, dtype=np.float64)
    gr_full, gc_full = np.meshgrid(rr_full, cc_full, indexing="ij")  # (H, W)
    Y_cam = np.zeros((N, H, W, 3), dtype=np.float64)
    N_cam = np.zeros((N, H, W, 3), dtype=np.float64)
    for k in range(N):
        Kk = K[k]
        u_full = (gc_full / max(W - 1, 1)) * (2.0 * Kk[0, 2])
        v_full = (gr_full / max(H - 1, 1)) * (2.0 * Kk[1, 2])
        zk = np.where(np.isfinite(depth_grid[k]), depth_grid[k], 0.0).astype(np.float64)
        xk = (u_full - Kk[0, 2]) / Kk[0, 0] * zk
        yk = (v_full - Kk[1, 2]) / Kk[1, 1] * zk
        Y_cam[k] = np.stack([xk, yk, zk], axis=-1)
        # Central-difference tangents -> surface normal
        dY_dc = np.zeros_like(Y_cam[k])
        dY_dr = np.zeros_like(Y_cam[k])
        dY_dc[:, 1:-1] = 0.5 * (Y_cam[k, :, 2:] - Y_cam[k, :, :-2])
        dY_dr[1:-1, :] = 0.5 * (Y_cam[k, 2:, :] - Y_cam[k, :-2, :])
        nk = np.cross(dY_dc, dY_dr)
        n_norm = np.linalg.norm(nk, axis=-1, keepdims=True)
        N_cam[k] = np.where(n_norm > 1e-6, nk / np.maximum(n_norm, 1e-6), np.array([0.0, 0.0, -1.0]))

    # Sample grid indices
    rr = np.arange(1, H - 1, stride)
    cc = np.arange(1, W - 1, stride)
    gg_r, gg_c = np.meshgrid(rr, cc, indexing="ij")
    gg_r = gg_r.ravel()
    gg_c = gg_c.ravel()

    for i in range(N):
        zi = depth_grid[i, gg_r, gg_c].astype(np.float64)
        valid_i = np.isfinite(zi) & (zi > 0.15) & (zi < 20.0)
        if not np.any(valid_i):
            continue
        Ki = K[i]
        ui = (gg_c[valid_i] / max(W - 1, 1)) * (2.0 * Ki[0, 2])
        vi = (gg_r[valid_i] / max(H - 1, 1)) * (2.0 * Ki[1, 2])
        z_v = zi[valid_i]
        X_ci = Y_cam[i, gg_r[valid_i], gg_c[valid_i]]
        X_w = X_ci @ c2w[i, :3, :3].T + c2w[i, :3, 3]
        ci_w = conf_grid[i, gg_r[valid_i], gg_c[valid_i]] if conf_grid is not None else np.ones(len(z_v))

        for off in frame_offsets:
            j = i + off
            if j >= N:
                continue
            Kj = K[j]
            X_cj = X_w @ w2c[j, :3, :3].T + w2c[j, :3, 3]
            zj_proj = X_cj[:, 2]
            in_front = zj_proj > 0.15
            if not np.any(in_front):
                continue
            uj = Kj[0, 0] * (X_cj[:, 0] / np.where(in_front, zj_proj, 1.0)) + Kj[0, 2]
            vj = Kj[1, 1] * (X_cj[:, 1] / np.where(in_front, zj_proj, 1.0)) + Kj[1, 2]
            W_img, H_img = 2.0 * Kj[0, 2], 2.0 * Kj[1, 2]
            in_bounds = in_front & (uj >= 2.0) & (uj < W_img - 2.0) & (vj >= 2.0) & (vj < H_img - 2.0)
            if not np.any(in_bounds):
                continue

            # Lookup destination 3D surface point Y_j and unit normal n_j
            gj_c = np.clip(np.round(uj[in_bounds] / max(W_img, 1.0) * (W - 1)).astype(int), 1, W - 2)
            gj_r = np.clip(np.round(vj[in_bounds] / max(H_img, 1.0) * (H - 1)).astype(int), 1, H - 2)
            zj_obs = depth_grid[j, gj_r, gj_c].astype(np.float64)
            z_rel = np.abs(zj_proj[in_bounds] - zj_obs) / np.maximum(zj_obs, 0.2)
            ok = np.isfinite(zj_obs) & (zj_obs > 0.15) & (z_rel < max_depth_rel)
            if not np.any(ok):
                continue

            idx = np.flatnonzero(in_bounds)[ok]
            gr_ok = gj_r[ok]
            gc_ok = gj_c[ok]
            Y_j = Y_cam[j, gr_ok, gc_ok]
            n_j = N_cam[j, gr_ok, gc_ok]
            X_cj_ok = X_cj[idx]

            # Point-to-plane 3D surface target: project X_cj onto destination tangent plane (Y_j, n_j)
            signed_d = np.sum(n_j * (X_cj_ok - Y_j), axis=-1, keepdims=True)
            X_tgt = X_cj_ok - signed_d * n_j
            z_tgt = np.maximum(X_tgt[:, 2], 0.15)
            u_tgt = Kj[0, 0] * (X_tgt[:, 0] / z_tgt) + Kj[0, 2]
            v_tgt = Kj[1, 1] * (X_tgt[:, 1] / z_tgt) + Kj[1, 2]

            rig = np.exp(-3.0 * z_rel[ok]) * np.clip(ci_w[idx], 0.1, 1.0)
            m = len(idx)
            src_list.append(np.full(m, i, dtype=np.int64))
            dst_list.append(np.full(m, j, dtype=np.int64))
            uvs_list.append(np.stack([ui[idx], vi[idx]], axis=-1))
            zs_list.append(z_v[idx])
            uvd_list.append(np.stack([u_tgt, v_tgt], axis=-1))
            zd_list.append(z_tgt)
            rig_list.append(rig)

    if not src_list:
        return Correspondences(
            src_idx=np.zeros(0, dtype=np.int64),
            dst_idx=np.zeros(0, dtype=np.int64),
            uv_src=np.zeros((0, 2), dtype=np.float64),
            z_src=np.zeros(0, dtype=np.float64),
            uv_dst=np.zeros((0, 2), dtype=np.float64),
            z_dst=np.zeros(0, dtype=np.float64),
            rigidity=np.zeros(0, dtype=np.float64),
        )
    return Correspondences(
        src_idx=np.concatenate(src_list),
        dst_idx=np.concatenate(dst_list),
        uv_src=np.concatenate(uvs_list),
        z_src=np.concatenate(zs_list),
        uv_dst=np.concatenate(uvd_list),
        z_dst=np.concatenate(zd_list),
        rigidity=np.concatenate(rig_list),
    )


# ---------------------------------------------------------------------------
# K5-S Perturbation-Stability Gate (AUROC = 1.000 on gross vs pass)
# ---------------------------------------------------------------------------

def k5s_pose_disagreement(
    c2w_a: np.ndarray,
    c2w_b: np.ndarray,
    tau_rot_deg: float = 0.25,
    tau_trans_m: float = 0.015,
) -> dict[str, Any]:
    """Compute K5-S frame-0-anchored pose disagreement between two runs (e.g. default vs deterministic/jitter).

    Matches lever6/k5b/kit/score_k5.py: align frame 0 identically and take max per-frame
    rotation diff (deg) and max metric camera-center diff (m).
    """
    A = np.asarray(c2w_a, dtype=np.float64)
    B = np.asarray(c2w_b, dtype=np.float64)
    # Express both trajectories relative to frame 0
    A0_inv = invert_se3(A[0])
    B0_inv = invert_se3(B[0])
    A_rel = np.einsum("ij,njk->nik", A0_inv, A)
    B_rel = np.einsum("ij,njk->nik", B0_inv, B)
    rot_diffs = geodesic_rot_deg(A_rel[:, :3, :3], B_rel[:, :3, :3])
    trans_diffs = np.linalg.norm(A_rel[:, :3, 3] - B_rel[:, :3, 3], axis=1)
    max_rot = float(np.max(rot_diffs))
    max_trans = float(np.max(trans_diffs))
    trigger = (max_rot > tau_rot_deg) or (max_trans > tau_trans_m)
    return dict(
        max_rot_deg=max_rot,
        median_rot_deg=float(np.median(rot_diffs)),
        max_trans_m=max_trans,
        median_trans_m=float(np.median(trans_diffs)),
        trigger_ttba=bool(trigger),
        tau_rot_deg=tau_rot_deg,
        tau_trans_m=tau_trans_m,
    )


# ---------------------------------------------------------------------------
# Geo-Maj@K Zero-Label Physical Energy & SE(3) Lie-Algebra Consensus
# ---------------------------------------------------------------------------

def se3_triplet_cycle_error(c2w: np.ndarray, stride: int = 2) -> float:
    """Mean SE(3) triplet loop-closure error across sampled (i, j, l) triples.
    Exact on rigid trajectories; checks numerical orthogonality/consistency when
    relative transforms are estimated independently.
    """
    N = len(c2w)
    if N < 3:
        return 0.0
    errs = []
    for i in range(0, N - 2 * stride, stride):
        j, l = i + stride, i + 2 * stride
        T_ij = invert_se3(c2w[i]) @ c2w[j]
        T_jl = invert_se3(c2w[j]) @ c2w[l]
        T_li = invert_se3(c2w[l]) @ c2w[i]
        loop = T_ij @ T_jl @ T_li
        errs.append(float(np.linalg.norm(se3_log(loop))))
    return float(np.mean(errs)) if errs else 0.0


def unmirror_c2w_x(c2w_mirrored: np.ndarray) -> np.ndarray:
    """Map camera poses from horizontally mirrored video M(V) back into canonical coordinates.
    Horizontal image flip corresponds to S = diag(-1, 1, 1) on both camera and world X axes:
      T_canon = S @ T_mirrored @ S (preserves det(R) = +1!).
    """
    S = np.diag([-1.0, 1.0, 1.0, 1.0])
    return np.einsum("ij,njk,kl->nil", S, np.asarray(c2w_mirrored, dtype=np.float64), S)


def unreverse_c2w_t(c2w_reversed: np.ndarray) -> np.ndarray:
    """Map camera poses from time-reversed video R(V) back into forward frame order,
    re-anchored so frame 0 sits at identity (matching canonical frame-0 gauge).
    """
    rev = np.asarray(c2w_reversed, dtype=np.float64)[::-1].copy()
    T0_inv = invert_se3(rev[0])
    return np.einsum("ij,njk->nik", T0_inv, rev)


def weighted_median(values: np.ndarray, weights: np.ndarray) -> float:
    """Weighted median for continuous spatial answers (distance, room area)."""
    v = np.asarray(values, dtype=np.float64)
    w = np.asarray(weights, dtype=np.float64)
    order = np.argsort(v)
    v, w = v[order], w[order]
    cdf = np.cumsum(w) / max(float(np.sum(w)), 1e-12)
    idx = int(np.searchsorted(cdf, 0.5))
    return float(v[min(idx, len(v) - 1)])


def geo_maj_k_fuse(
    hypotheses_c2w: list[np.ndarray],
    energies: np.ndarray | None = None,
    *,
    beta: float = 2.0,
    irls_iters: int = 5,
    huber_delta: float = 0.15,
    scalar_answers: np.ndarray | None = None,
) -> dict[str, Any]:
    """Fuse K canonicalized SE(3) camera trajectories via energy-weighted Lie-algebra IRLS Karcher mean.

    If energies is None, computes zero-label pairwise consensus energy (median distance
    to all other hypotheses — automatically downweighting corrupted/flipped modes!).
    """
    K = len(hypotheses_c2w)
    if K == 0:
        raise ValueError("need at least one hypothesis")
    # Re-anchor all hypotheses to frame 0 = identity
    aligned = []
    for H in hypotheses_c2w:
        H = np.asarray(H, dtype=np.float64)
        aligned.append(np.einsum("ij,njk->nik", invert_se3(H[0]), H))
    stack = np.stack(aligned, axis=0)  # (K, N, 4, 4)
    N = stack.shape[1]

    # Pairwise cross-hypothesis disagreement (zero-label consensus energy)
    pair_dis = np.zeros((K, K), dtype=np.float64)
    for a in range(K):
        for b in range(a + 1, K):
            d = k5s_pose_disagreement(stack[a], stack[b])
            score = d["median_rot_deg"] / 5.0 + d["median_trans_m"] / 0.10
            pair_dis[a, b] = pair_dis[b, a] = score
    consensus_energy = np.median(pair_dis, axis=1)

    if energies is None:
        total_energy = consensus_energy
    else:
        total_energy = np.asarray(energies, dtype=np.float64) + 0.5 * consensus_energy

    # Softmax hypothesis weights
    e_shift = total_energy - float(np.min(total_energy))
    w_base = np.exp(-beta * e_shift)
    w_base = w_base / max(float(np.sum(w_base)), 1e-12)

    # Initialize Karcher mean from lowest-energy hypothesis
    best_k = int(np.argmin(total_energy))
    mean_c2w = stack[best_k].copy()
    final_weights = w_base.copy()

    for _ in range(irls_iters):
        # Compute tangent residuals log(T_k @ T_bar^{-1}) per frame and hypothesis
        mean_inv = invert_se3(mean_c2w)
        deltas = np.zeros((K, N, 6), dtype=np.float64)
        norms = np.zeros(K, dtype=np.float64)
        for k in range(K):
            rel = np.einsum("nij,njk->nik", stack[k], mean_inv)
            deltas[k] = se3_log(rel)
            norms[k] = float(np.median(np.linalg.norm(deltas[k, 1:], axis=1))) if N > 1 else 0.0
        w_rob = w_base * huber_weights(norms, huber_delta)
        w_rob = w_rob / max(float(np.sum(w_rob)), 1e-12)
        final_weights = w_rob

        avg_xi = np.einsum("k,kni->ni", w_rob, deltas)  # (N, 6)
        avg_xi[0] = 0.0
        step_T = se3_exp(avg_xi)
        mean_c2w = np.einsum("nij,njk->nik", step_T, mean_c2w)
        if float(np.max(np.linalg.norm(avg_xi, axis=1))) < 1e-6:
            break

    out: dict[str, Any] = dict(
        fused_c2w=mean_c2w,
        weights=final_weights,
        energies=total_energy,
        best_single_idx=best_k,
    )
    if scalar_answers is not None:
        out["fused_answer"] = weighted_median(scalar_answers, final_weights)
    return out
