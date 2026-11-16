"""Camera math shared by the provider, the click lift and the synthetic scenes (schema 0).

- Camera frame: OpenCV axes (x right, y down, z forward), origin at the optical centre, for the image as the policy
  sees it. MuJoCo cameras (x right, y up, looking along -z): R_opencv = R_mujoco @ diag(1, -1, -1).
- Continuous pixels: column i covers [i, i + 1), centre i + 0.5; K maps camera points to these coordinates.
- uv01: u = x / W, v = y / H. In frame iff 0 <= u < 1 and 0 <= v < 1.
- Depth is the optical-axis z, not the ray length.
- T_a_b maps points in frame b to frame a.
- Mask erosion and dilation by k pixels use a 3 x 3 square element applied k times (Chebyshev distance k).
"""
import math

import numpy as np
from scipy import ndimage

MUJOCO_TO_OPENCV = np.diag([1.0, -1.0, -1.0])


def intrinsics_from_fov(width, height, fovy_deg=None, fovx_deg=None):
    """Pinhole K with square pixels from a vertical (MuJoCo) or horizontal (Habitat) field of view."""
    if (fovy_deg is None) == (fovx_deg is None):
        raise ValueError('Give exactly one of fovy_deg and fovx_deg')
    if fovy_deg is not None:
        f = height / (2 * math.tan(math.radians(fovy_deg) / 2))
    else:
        f = width / (2 * math.tan(math.radians(fovx_deg) / 2))
    return np.array([[f, 0, width / 2], [0, f, height / 2], [0, 0, 1]], dtype=np.float64)


def rigid(R=None, t=None):
    T = np.eye(4)
    if R is not None:
        T[:3, :3] = R
    if t is not None:
        T[:3, 3] = t
    return T


def inv(T):
    T = np.asarray(T, dtype=np.float64)
    out = np.eye(4)
    out[:3, :3] = T[:3, :3].T
    out[:3, 3] = -T[:3, :3].T @ T[:3, 3]
    return out


def apply(T, X):
    X = np.asarray(X, dtype=np.float64)
    return X @ np.asarray(T)[:3, :3].T + np.asarray(T)[:3, 3]


def axis_angle_to_matrix(aa):
    """Rodrigues."""
    aa = np.asarray(aa, dtype=np.float64)
    theta = float(np.linalg.norm(aa))
    if theta < 1e-12:
        return np.eye(3)
    k = aa / theta
    Kx = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
    return np.eye(3) + math.sin(theta) * Kx + (1 - math.cos(theta)) * Kx @ Kx


def matrix_to_axis_angle(R):
    R = np.asarray(R, dtype=np.float64)
    angle = math.acos(min(1.0, max(-1.0, (np.trace(R) - 1) / 2)))
    if angle < 1e-9:
        return np.zeros(3)
    if math.pi - angle < 1e-6:
        _, V = np.linalg.eigh((R + np.eye(3)) / 2)
        return V[:, -1] * angle
    axis = np.array([R[2, 1] - R[1, 2], R[0, 2] - R[2, 0], R[1, 0] - R[0, 1]]) / (2 * math.sin(angle))
    return axis * angle


def look_at(eye, target, up=(0., 0., 1.)):
    """T_world_cam for an OpenCV camera at eye looking at target, with image-up towards `up`."""
    eye, target, up = (np.asarray(v, dtype=np.float64) for v in (eye, target, up))
    z = target - eye
    z /= np.linalg.norm(z)
    x = np.cross(z, up)
    if np.linalg.norm(x) < 1e-9:
        x = np.cross(z, np.array([0., 1., 0.]))
    x /= np.linalg.norm(x)
    y = np.cross(z, x)
    return rigid(np.column_stack((x, y, z)), eye)


def unproject_pixels(rows, cols, z, K):
    """Integer pixel indices and optical-axis depth -> camera points [N, 3] (depth * K^-1 [u, v, 1] at centres)."""
    rows, cols, z = (np.asarray(a, dtype=np.float64).reshape(-1) for a in (rows, cols, z))
    x = ((cols + 0.5) - K[0, 2]) / K[0, 0]
    y = ((rows + 0.5) - K[1, 2]) / K[1, 1]
    return np.column_stack((x * z, y * z, z))


def project(X, K, width, height):
    """Camera points [N, 3] -> (uv01 [N, 2], z [N]); uv is nan where z <= 0."""
    X = np.asarray(X, dtype=np.float64).reshape(-1, 3)
    z = X[:, 2]
    with np.errstate(divide='ignore', invalid='ignore'):
        u = (K[0, 0] * X[:, 0] / z + K[0, 2]) / width
        v = (K[1, 1] * X[:, 1] / z + K[1, 2]) / height
    uv = np.column_stack((u, v))
    uv[z <= 0] = np.nan
    return uv, z


def record_uv(X, K, width, height, behind=0.01):
    """Schema 5.2 uv field of one point: uv01 clipped to [-1, 2]; (-1, -1) when z <= `behind` (G3T units)."""
    X = np.asarray(X, dtype=np.float64).reshape(3)
    if X[2] <= behind:
        return [-1.0, -1.0]
    uv, _ = project(X[None], K, width, height)
    return np.clip(uv[0], -1.0, 2.0).tolist()


def in_frame(uv):
    return bool(np.isfinite(uv).all() and 0 <= uv[0] < 1 and 0 <= uv[1] < 1)


def erode(mask, px):
    mask = np.asarray(mask, dtype=bool)
    return ndimage.binary_erosion(mask, structure=np.ones((3, 3)), iterations=px) if px > 0 else mask


def dilate(mask, px):
    mask = np.asarray(mask, dtype=bool)
    return ndimage.binary_dilation(mask, structure=np.ones((3, 3)), iterations=px) if px > 0 else mask


def mask_contains(mask, uv):
    """Does the pixel holding continuous uv01 lie in the mask (False when out of frame)?"""
    if not in_frame(uv):
        return False
    h, w = mask.shape
    return bool(mask[int(math.floor(uv[1] * h)), int(math.floor(uv[0] * w))])


def principal_extents(P):
    """p2-p98 extents along the principal axes of P, largest first (no floor; the caller floors in metres)."""
    P = np.asarray(P, dtype=np.float64)
    Q = P - P.mean(0)
    _, _, Vt = np.linalg.svd(Q, full_matrices=False)
    proj = Q @ Vt.T
    lo, hi = np.percentile(proj, 2, axis=0), np.percentile(proj, 98, axis=0)
    return np.sort(hi - lo)[::-1]


def lift_mask(mask, depth, conf, K, erode_px=2, min_pixels=20):
    """Schema 6.3 step 6 in one view: erode the mask, keep pixels with finite positive depth and confidence above the
    view's median confidence (conf None: GT depth, every finite pixel is confident). Returns (X = per-axis median [3],
    raw extents [3], points [N, 3], n) in depth units, or None with fewer than min_pixels pixels."""
    depth = np.asarray(depth, dtype=np.float64)
    if depth.shape != mask.shape or (conf is not None and np.shape(conf) != mask.shape):
        raise ValueError('Mask, depth and confidence differ in size')
    keep = erode(mask, erode_px) & np.isfinite(depth) & (depth > 0)
    if conf is not None:
        conf = np.asarray(conf, dtype=np.float64)
        finite_conf = conf[np.isfinite(conf)]
        median = float(np.median(finite_conf)) if finite_conf.size else math.inf
        keep &= np.isfinite(conf) & (conf > median)
    rows, cols = np.nonzero(keep)
    if len(rows) < min_pixels:
        return None
    P = unproject_pixels(rows, cols, depth[rows, cols], K)
    return np.median(P, axis=0), principal_extents(P), P, len(rows)
