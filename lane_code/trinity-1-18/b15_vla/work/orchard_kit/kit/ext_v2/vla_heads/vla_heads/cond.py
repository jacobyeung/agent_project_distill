"""Spatial conditioning: tensor contracts, the where encoder and the G3T token projector.

`cond` selects what the head sees besides the LM states:
- none: nothing (the pure backbone swap, arm B1);
- spatial_readouts: the where-provider's entity records (arm U1), as vectors only (no cond tokens);
- g3t_tokens: one projected G3T camera token per view (cond tokens);
- both: the where vectors plus cond tokens: G3T tokens and, when the batch carries pose9, the
  camera / depth readout tokens.

Raw inputs travel in `batch['cond']`, a dict:

where (vla_where's provider, `WhereOutput.vector` / `.mask`; schema 5.2): E = 2 rows, index 0 the
target (the object the robot moves), 1 the place (where it goes):
- where      [B, 2, 18] float: 0 presence (max over the two views); 1 valid; 2-3 uv_agent and 4-5
              uv_wrist (uv01 projection of the reported point, clipped to [-1, 2], (-1, -1) behind
              the camera); 6-8 X_wrist (m, wrist camera at t, OpenCV axes); 9-11 reach_base (m, the
              point minus the end-effector position in robot base axes); 12-14 size (m, p2-p98
              principal extents, largest first); 15-17 scale_source one-hot [proprio_handeye,
              vc_ratio, metric_test]. valid = 0 -> the whole row is zero. valid = 1 with an unknown
              metric scale -> cols 0-5 filled, 6-17 zero (all-zero one-hot = scale unknown).
- where_mask [B, 2] bool, optional (default: valid > 0.5); the encoder ANDs it with valid.
- withheld   [B] bool, optional: chunks whose where input is withheld (evaluation `withheld`
              condition, or a loader that applied `withheld_draw` itself); applies in every mode.
- episode    list of B str and t [B] (or list of int): with them, training draws the dropout per
              chunk as `withheld_draw(episode, t, where_seed, where_dropout)` (schema 5.5).
A withheld chunk zeroes both rows and sets where_mask False; where_mask = valid AND NOT withheld.

G3T (student_pilot.g3t_online FEATURE 'cam_l23_2048_pose9_disagreement1_v1'):
- g3t_cam    [B, V, 2058]: layer-23 frame and global camera tokens (2 x 1024), then G3T pose9 relative
              to frame 0 (translation divided by the mean camera radius over frames 1..V-1, quaternion
              xyzw, FoV h w rad), then one scalar that g3t_online.disagreement computes: the absolute
              yaw |atan2(f_x, f_z)| of the local camera's forward axis (not a local-versus-global
              disagreement, despite the feature name)
- g3t_patch  [B, V, H, W, 2048], optional, read only when g3t_patch_grid > 0 (pooled to g x g per view)
- g3t_mask   [B, V] bool, optional

Optional readout tokens under both (student_pilot.head_api / carrier_c1.readout / TowerState):
- pose9 [B, V, 9] (t m, quaternion xyzw, FoV h w rad) with pose_mask [B, V]; gravity_up [B, 3] and
  step_scale [B, 1]; depth_grid [B, V, Gh, Gw] m (pooled to readout_depth_grid^2 log depths) or
  point_depth [B, V, Kp] at point_uv [B, V, Kp, 2]; depth_mask [B, V].

Every projection that writes a cond token ends in a zero-initialised layer, and the heads add cond
through zero-initialised maps, so a cond arm's step-0 prediction equals the no-cond arm's
(design record 5.4). These modules are built under a forked RNG, so adding them does not change
any other parameter's initial value under the same seed.
"""
import contextlib
import hashlib

import torch
from torch import nn
from torch.nn import functional as F

from .layers import mlp, zero_


@contextlib.contextmanager
def rng_neutral():
    """Build modules without consuming the global RNG stream (cond arms keep the no-cond arm's init)."""
    with torch.random.fork_rng(devices=[]):
        yield


def withheld_draw(episode, t, seed=17, p=0.2):
    """Schema 5.5: chunk (episode, t) is withheld iff int(sha256(f"{seed}:{episode}:{t}")[:8], 16) / 16**8 < p."""
    u = int(hashlib.sha256(f'{seed}:{episode}:{int(t)}'.encode()).hexdigest()[:8], 16) / 16 ** 8
    return u < p


def where_features(where, where_mask=None, withheld=None):
    """Where records [B, E, 18] -> (features [B, E, 18] float32, mask [B, E]).
    mask = valid (col 1 > 0.5) AND where_mask (if given) AND NOT withheld [B] (if given); rows
    outside the mask are zeroed."""
    if where.ndim != 3 or where.shape[-1] != 18:
        raise ValueError(f'where must be [B, E, 18], got {tuple(where.shape)}')
    w = where.float()
    mask = w[..., 1] > 0.5
    if where_mask is not None:
        mask = mask & where_mask.bool().to(w.device)
    if withheld is not None:
        withheld = torch.as_tensor(withheld, dtype=torch.bool, device=w.device).reshape(-1)
        if withheld.shape[0] != w.shape[0]:
            raise ValueError('withheld must be [B]')
        mask = mask & ~withheld[:, None]
    return w * mask[..., None], mask


def _mask(raw, key, shape, device):
    value = raw.get(key)
    return torch.ones(shape, dtype=torch.bool, device=device) if value is None else value.bool().to(device)


class G3TProjector(nn.Module):
    def __init__(self, cfg):
        super().__init__()
        self.cfg = cfg
        d = cfg.cond_dim
        self.cam = nn.Sequential(nn.LayerNorm(cfg.g3t_cam_dim), zero_(nn.Linear(cfg.g3t_cam_dim, d)))
        self.view = zero_(nn.Embedding(cfg.max_views, d))
        if cfg.g3t_patch_grid:
            self.patch = nn.Sequential(nn.LayerNorm(cfg.g3t_patch_dim), zero_(nn.Linear(cfg.g3t_patch_dim, d)))
            self.cell = zero_(nn.Embedding(cfg.g3t_patch_grid ** 2, d))

    def forward(self, raw):
        cam = raw.get('g3t_cam')
        if cam is None:
            raise ValueError('cond g3t_tokens needs g3t_cam [B, V, 2058]')
        b, v, c = cam.shape
        if c != self.cfg.g3t_cam_dim or v > self.cfg.max_views:
            raise ValueError(f'g3t_cam must be [B, V<={self.cfg.max_views}, {self.cfg.g3t_cam_dim}], got {tuple(cam.shape)}')
        dtype, device = self.cam[1].weight.dtype, cam.device
        views = self.view(torch.arange(v, device=device))
        mask = _mask(raw, 'g3t_mask', (b, v), device)
        tokens, masks = [self.cam(cam.to(dtype)) + views], [mask]
        patch = raw.get('g3t_patch')
        if self.cfg.g3t_patch_grid and patch is not None:
            if patch.ndim != 5 or patch.shape[:2] != (b, v) or patch.shape[-1] != self.cfg.g3t_patch_dim:
                raise ValueError(f'g3t_patch must be [B, V, H, W, {self.cfg.g3t_patch_dim}]')
            g = self.cfg.g3t_patch_grid
            pooled = F.adaptive_avg_pool2d(patch.flatten(0, 1).permute(0, 3, 1, 2).float(), g)
            pooled = pooled.permute(0, 2, 3, 1).reshape(b, v, g * g, -1).to(dtype)
            p = self.patch(pooled) + views[:, None] + self.cell.weight[None]
            tokens.append(p.reshape(b, v * g * g, -1))
            masks.append(mask[:, :, None].expand(-1, -1, g * g).reshape(b, -1))
        return torch.cat(tokens, 1), torch.cat(masks, 1)


class ReadoutProjector(nn.Module):
    """Optional camera / depth readout tokens (read only when the batch carries pose9)."""

    def __init__(self, cfg):
        super().__init__()
        self.cfg = cfg
        h, d, g = cfg.readout_hidden, cfg.cond_dim, cfg.readout_depth_grid
        self.pose = nn.Sequential(nn.LayerNorm(12), mlp([12, h, d], zero_last=True))
        self.gravity = mlp([4, h, d], zero_last=True)
        self.depth = nn.Sequential(nn.LayerNorm(g * g + 2), mlp([g * g + 2, h, d], zero_last=True))
        self.point = mlp([3, h, d], zero_last=True)
        self.view = zero_(nn.Embedding(cfg.max_views, d))
        self.kind = zero_(nn.Embedding(3, d))

    @staticmethod
    def pose_features(pose9):
        t, q, fov = pose9[..., :3], pose9[..., 3:7], pose9[..., 7:9]
        q = F.normalize(q, dim=-1)
        q = torch.where(q[..., 3:4] < 0, -q, q)  # q and -q are one rotation: keep w >= 0
        dist = t.norm(dim=-1, keepdim=True)
        return torch.cat([t, torch.log1p(dist), q, fov, fov.cos()], -1)

    def forward(self, raw):
        pose9 = raw['pose9']
        b, v, _ = pose9.shape
        if pose9.shape[-1] != 9 or v > self.cfg.max_views:
            raise ValueError(f'pose9 must be [B, V<={self.cfg.max_views}, 9]')
        dtype, device = self.view.weight.dtype, pose9.device
        views = self.view(torch.arange(v, device=device))
        tokens = [self.pose(self.pose_features(pose9.float()).to(dtype)) + views + self.kind.weight[0]]
        masks = [_mask(raw, 'pose_mask', (b, v), device)]
        grav, scale = raw.get('gravity_up'), raw.get('step_scale')
        if grav is not None or scale is not None:
            grav = pose9.new_zeros(b, 3) if grav is None else grav.float()
            scale = pose9.new_ones(b, 1) if scale is None else scale.float().reshape(b, 1)
            g = torch.cat([F.normalize(grav, dim=-1), torch.log(scale.clamp(min=1e-3))], -1)
            tokens.append((self.gravity(g.to(dtype)) + self.kind.weight[1])[:, None])
            masks.append(torch.ones(b, 1, dtype=torch.bool, device=device))
        depth = self.depth_tokens(raw, b, v, dtype)
        if depth is not None:
            tokens.append(depth + views + self.kind.weight[2])
            masks.append(_mask(raw, 'depth_mask', (b, v), device))
        return torch.cat(tokens, 1), torch.cat(masks, 1)

    def depth_tokens(self, raw, b, v, dtype):
        g = self.cfg.readout_depth_grid
        if raw.get('depth_grid') is not None:
            grid = raw['depth_grid'].float()
            if grid.ndim != 4 or grid.shape[:2] != (b, v):
                raise ValueError('depth_grid must be [B, V, Gh, Gw] metres')
            logd = torch.log(grid.clamp(min=1e-3)).flatten(0, 1)[:, None]
            pooled = F.adaptive_avg_pool2d(logd, g).reshape(b, v, g * g)
            stats = torch.stack([pooled.mean(-1), pooled.std(-1, unbiased=False)], -1)
            return self.depth(torch.cat([pooled - stats[..., :1], stats], -1).to(dtype))
        if raw.get('point_depth') is not None:
            d, uv = raw['point_depth'].float(), raw['point_uv'].float()
            if d.shape[:2] != (b, v) or uv.shape != (*d.shape, 2):
                raise ValueError('point_depth [B, V, Kp] needs point_uv [B, V, Kp, 2]')
            f = torch.cat([uv / 500 - 1, torch.log(d.clamp(min=1e-3))[..., None]], -1)
            return self.point(f.to(dtype)).mean(2)
        return None


class CondProjector(nn.Module):
    """raw cond dict -> dict(tokens [B, N, cond_dim] | None, mask, where [B, E, 18] | None, where_mask)."""

    def withheld(self, raw, training):
        """[B] bool or None: an explicit raw['withheld'], else (training only) the sha256 draw."""
        if raw.get('withheld') is not None:
            return raw['withheld']
        if not training or self.cfg.where_dropout <= 0:
            return None
        if raw.get('episode') is None or raw.get('t') is None:
            raise ValueError('Training with where_dropout > 0 needs cond["episode"] and cond["t"] '
                             '(or cond["withheld"]) for the sha256 draw')
        ts = raw['t'].tolist() if torch.is_tensor(raw['t']) else list(raw['t'])
        return torch.tensor([withheld_draw(e, t, self.cfg.where_seed, self.cfg.where_dropout)
                             for e, t in zip(raw['episode'], ts)], dtype=torch.bool)

    def __init__(self, cfg):
        super().__init__()
        self.cfg = cfg
        with rng_neutral():
            self.g3t = G3TProjector(cfg) if cfg.cond in ('g3t_tokens', 'both') else None
            # Schema 1: cond tokens exist under g3t_tokens and both only, so readout tokens join `both`.
            self.readout = ReadoutProjector(cfg) if cfg.cond == 'both' else None

    def forward(self, raw, training=False):
        out = dict(tokens=None, mask=None, where=None, where_mask=None)
        if self.cfg.cond == 'none':
            return out
        if raw is None:
            raise ValueError(f'cond={self.cfg.cond} needs batch["cond"]')
        parts = []
        if self.g3t is not None:
            parts.append(self.g3t(raw))
        if self.cfg.cond in ('spatial_readouts', 'both') and self.cfg.where_vector:
            if 'where' not in raw:
                raise ValueError(f'cond={self.cfg.cond} needs cond["where"] [B, 2, 18]')
            where, mask = where_features(raw['where'], raw.get('where_mask'), self.withheld(raw, training))
            if where.shape[1] != self.cfg.where_entities:
                raise ValueError(f'where must hold {self.cfg.where_entities} entities')
            out.update(where=where, where_mask=mask)
        if self.readout is not None and raw.get('pose9') is not None:
            parts.append(self.readout(raw))
        if parts:
            out.update(tokens=torch.cat([t for t, _ in parts], 1), mask=torch.cat([m for _, m in parts], 1))
        return out
