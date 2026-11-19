"""ScaleHead: predicts the per-clip log metric scale of the frozen G3T tower output.

Everything between the input tensors and the output is fixed math (rotations, unprojection,
quantiles, logs, means, norms) or a parameter/buffer in the state dict. Gravity comes from the
tower's own anchor poses (mean camera up axis, the G1 rule); no GT enters the forward pass.

Inputs (batch first, one clip per batch element):
  depth_grid      [B, 32, 51, 51]     tower depth on the 51x51 canvas grid
  depth_conf_grid [B, 32, 51, 51]     tower depth confidence
  points_grid     [B, 32, 51, 51, 3]  tower point map (origin-camera frame)
  anchor_pose     [B, 32, 9]          raw_pose[anchor_slots]: t(3), quaternion xyzw(4), fov_h, fov_w
  grid_uv         [51] or [B, 51]     canvas coordinates in [0, 1000] (default linspace(0, 1000, 51))
  own_depth_grid  optional [B, 32, 51, 51] metric depth from the student's own depth phase (socket)
Output: log scale [B]; metric depth = exp(log_scale) * depth_grid.
"""
import hashlib
import json
from pathlib import Path

import torch
from torch import nn

FLOOR_LEVELS = (0.01, 0.02, 0.05, 0.10, 0.25)
HEIGHT_LEVELS = (0.50, 0.75, 0.90, 0.95)
DEPTH_LEVELS = (0.10, 0.25, 0.50, 0.75, 0.90)
RADIUS_LEVELS = (0.50, 0.90, 0.99)
EPS = 1e-6
FEATURE_NAMES = (
    [f'log_floor_dist_q{int(q * 100):02d}' for q in FLOOR_LEVELS]
    + [f'log_height_above_q01_q{int(q * 100):02d}' for q in HEIGHT_LEVELS]
    + ['log_span_q01_q99']
    + [f'log_depth_conf_q{int(q * 100):02d}' for q in DEPTH_LEVELS]
    + [f'log_depth_all_q{int(q * 100):02d}' for q in (0.10, 0.50, 0.90)]
    + [f'log_horiz_radius_q{int(q * 100):02d}' for q in RADIUS_LEVELS]
    + ['log_cam_step_mean', 'log_cam_extent_max', 'log_tan_half_fov_h', 'log_tan_half_fov_w',
       'mean_log_conf', 'log_median_conf',
       'log_pointmap_to_depth_ratio', 'log_pointmap_floor_dist_q01'])
N_FEATURES = len(FEATURE_NAMES)


def quat_xyzw_to_matrix(q):
    q = q / q.norm(dim=-1, keepdim=True)
    x, y, z, w = q.unbind(-1)
    return torch.stack([
        1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w),
        2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w),
        2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)], -1).reshape(*q.shape[:-1], 3, 3)


def _q(values, levels):
    return torch.quantile(values, torch.tensor(levels, dtype=values.dtype))


def clip_features(depth, conf, points, pose, grid_uv):
    """Fixed-math features of one clip (float64). Returns ([N_FEATURES], aux dict)."""
    depth, conf, points, pose, grid_uv = (t.double() for t in (depth, conf, points, pose, grid_uv))
    # raw_pose encodes E_k = inv(C_k) C_0: camera-to-reference rotation is R_rel^T, centre -R^T t.
    R = quat_xyzw_to_matrix(pose[:, 3:7]).transpose(-1, -2)            # [32,3,3] camera -> ref
    centres = -(R @ pose[:, :3, None])[..., 0]                          # [32,3]
    up = (-R[:, :, 1]).mean(0)                                          # G1: mean camera up axis
    up = up / up.norm()
    tan_h, tan_w = torch.tan(pose[:, 7] / 2), torch.tan(pose[:, 8] / 2)
    u = (grid_uv / 1000 - 0.5) * 2                                      # columns -> x
    rx = u[None, None, :] * tan_w[:, None, None]
    ry = u[None, :, None] * tan_h[:, None, None]
    rays = torch.stack(torch.broadcast_tensors(rx, ry, torch.ones_like(rx * ry)), -1)  # [32,51,51,3]
    world = torch.einsum('kij,kabj->kabi', R, rays * depth[..., None]) + centres[:, None, None, :]
    valid = torch.isfinite(depth) & (depth > 0) & torch.isfinite(world).all(-1)
    finite_conf = torch.isfinite(conf)
    conf_thr = torch.quantile(conf[finite_conf], 0.5)
    confident = valid & finite_conf & (conf > conf_thr)

    z = (world[valid] @ up)
    zc = centres @ up
    cam_h = torch.quantile(zc, 0.5)
    zq = _q(z, FLOOR_LEVELS + HEIGHT_LEVELS + (0.99,))
    floor_q, height_q, z99 = zq[:len(FLOOR_LEVELS)], zq[len(FLOOR_LEVELS):-1], zq[-1]
    floor_dist = torch.log((cam_h - floor_q).clamp_min(EPS))
    heights = torch.log((height_q - floor_q[0]).clamp_min(EPS))
    span = torch.log((z99 - floor_q[0]).clamp_min(EPS))
    dconf = torch.log(_q(depth[confident], DEPTH_LEVELS))
    dall = torch.log(_q(depth[valid], (0.10, 0.50, 0.90)))
    pv = world[valid]
    horiz = pv - (pv @ up)[:, None] * up[None]
    hc = horiz.mean(0)
    radius = torch.log(_q((horiz - hc).norm(dim=-1), RADIUS_LEVELS).clamp_min(EPS))
    step = torch.log((centres[1:] - centres[:-1]).norm(dim=-1).mean().clamp_min(EPS))
    extent = torch.log((centres - centres.mean(0)).norm(dim=-1).max().clamp_min(EPS))
    lconf = torch.log(conf[finite_conf].clamp_min(EPS))
    pts = points.double()
    pmask = confident & torch.isfinite(pts).all(-1)
    ratio = torch.log(((pts - centres[:, None, None, :]).norm(dim=-1)[pmask]).clamp_min(EPS)
                      / (world - centres[:, None, None, :]).norm(dim=-1)[pmask].clamp_min(EPS)).median()
    zp = pts[torch.isfinite(pts).all(-1)] @ up
    pfloor = torch.log((cam_h - torch.quantile(zp, 0.01)).clamp_min(EPS))
    feats = torch.cat([floor_dist, heights, span[None], dconf, dall, radius,
                       torch.stack([step, extent, torch.log(tan_h).mean(), torch.log(tan_w).mean(),
                                    lconf.mean(), lconf.median(), ratio, pfloor])])
    aux = dict(h_raw=float(cam_h - floor_q[0]), span=float(z99 - floor_q[0]), confident=confident)
    return feats, aux


class ScaleHead(nn.Module):
    """Standardise fixed-math clip features, then a small MLP (hidden=0 means linear) -> log scale."""

    def __init__(self, hidden=0):
        super().__init__()
        self.hidden = hidden
        self.register_buffer('feat_mean', torch.zeros(N_FEATURES, dtype=torch.float64))
        self.register_buffer('feat_std', torch.ones(N_FEATURES, dtype=torch.float64))
        if hidden:
            self.net = nn.Sequential(nn.Linear(N_FEATURES, hidden), nn.Tanh(), nn.Linear(hidden, 1))
        else:
            self.net = nn.Linear(N_FEATURES, 1)
        self.net.double()
        # Own-depth socket: blends toward median(log own/g3t) on confident grid points. Untrained
        # until K1's own phase exists; at 0 it leaves the prediction unchanged.
        self.own_gate = nn.Parameter(torch.zeros((), dtype=torch.float64))

    @staticmethod
    def features(depth_grid, depth_conf_grid, points_grid, anchor_pose, grid_uv=None):
        B = depth_grid.shape[0]
        if grid_uv is None:
            grid_uv = torch.linspace(0, 1000, depth_grid.shape[-1], dtype=torch.float64)
        grid_uv = torch.as_tensor(grid_uv)
        if grid_uv.dim() == 1:
            grid_uv = grid_uv[None].expand(B, -1)
        out, aux = [], []
        for b in range(B):
            f, a = clip_features(depth_grid[b], depth_conf_grid[b], points_grid[b], anchor_pose[b], grid_uv[b])
            out.append(f)
            aux.append(a)
        return torch.stack(out), aux

    def from_features(self, feats):
        x = (feats.double() - self.feat_mean) / self.feat_std
        return self.net(x)[..., 0]

    def forward(self, depth_grid, depth_conf_grid, points_grid, anchor_pose, grid_uv=None, own_depth_grid=None):
        feats, aux = self.features(depth_grid, depth_conf_grid, points_grid, anchor_pose, grid_uv)
        log_scale = self.from_features(feats)
        if own_depth_grid is not None:
            own = []
            for b in range(depth_grid.shape[0]):
                m = aux[b]['confident'] & torch.isfinite(own_depth_grid[b]) & (own_depth_grid[b] > 0)
                own.append(torch.log(own_depth_grid[b].double()[m] / depth_grid[b].double()[m]).median())
            log_scale = log_scale + self.own_gate * (torch.stack(own) - log_scale)
        return log_scale


def prepare_inputs(tower_npz):
    """Load one K1 tower.npz into batch-of-one tensors for ScaleHead.forward."""
    import numpy as np
    with np.load(tower_npz, allow_pickle=False) as z:
        pose = z['raw_pose'][z['anchor_slots']]
        return dict(depth_grid=torch.from_numpy(z['depth_grid'])[None],
                    depth_conf_grid=torch.from_numpy(z['depth_conf_grid'])[None],
                    points_grid=torch.from_numpy(z['points_grid'])[None],
                    anchor_pose=torch.from_numpy(pose)[None],
                    grid_uv=torch.from_numpy(z['grid_uv']))


def file_sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_head(directory, expected_sha256=None):
    """Load scale_head.safetensors + scale_head.json; refuse on a sha256 mismatch."""
    from safetensors.torch import load_file
    directory = Path(directory)
    weights = directory / 'scale_head.safetensors'
    meta = json.loads((directory / 'scale_head.json').read_text())
    expected = expected_sha256 or meta['weights_sha256']
    actual = file_sha256(weights)
    if actual != expected:
        raise ValueError(f'scale head sha256 mismatch: expected {expected}, got {actual}')
    head = ScaleHead(hidden=meta['config']['hidden'])
    head.load_state_dict(load_file(str(weights)))
    head.eval()
    return head
