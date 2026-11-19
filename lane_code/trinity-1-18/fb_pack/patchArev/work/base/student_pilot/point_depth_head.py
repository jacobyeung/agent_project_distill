"""Point-depth head: metric depth at continuous [0, 1000] x [0, 1000] points of each temporal group.

The design follows the depth-VLM recipe (DepthVLM, DepthEvidence, MVUCF) on Qwen3.5:

1. Inputs per row, never pooled: three intermediate ViT block outputs at the native patch grid
   [T, 2Hm, 2Wm, D_vit] (reordered from the processor's 2x2 merge-unit order with the row's real
   video_grid_thw) and the final-norm LLM states at the row's visual tokens [T, Hm, Wm, D_llm].
2. Fusion: per-stream LayerNorm + linear projection to d. The ViT streams form a fine map; the LLM
   stream plus the 2x2-pooled fine map form a coarse map, FiLM-modulated by the group's predicted
   field of view (detached, from the pose head).
3. Cross-frame attention on the coarse map: alternating attention within each group and across every
   group's tokens (VGGT's frame/global pattern), with 2D sin-cos positions and a learned group embedding.
4. The context is upsampled to the fine grid, added to the ViT map and refined by two 3x3 convolutions.
5. Point queries sample the fine map bilinearly (grid_sample, align_corners=False: [0, 1000] spans the
   image edges, pixel centres at (i + 0.5) / W * 1000) with central finite differences and the sub-cell
   phase; absolute image position is not an input (MVUCF), so depth must come from the features.
6. Readout: an MLP with Softplus, depth = min_depth + softplus(raw), clamped to [min_depth, max_depth].
Loss: SILog (lambda 0.5) + metric log-L1 and inverse-depth Smooth-L1 + within-frame pairwise log-depth terms.
"""
import math
import re

import torch
from torch import nn
from torch.nn import functional as F

POINT_DEPTH_DEFAULTS = {
    'weight': 0.0,
    'weight_silog': 1.0,
    'weight_metric': 0.5,
    'weight_grad': 0.5,
    'silog_lambda': 0.5,
    'smooth_l1_beta': 0.1,
    'd_proj': 256,
    'mlp_hidden': 256,
    'num_heads': 8,
    'context_depth': 2,
    # 1-based ViT block indices; [9, 17, 25] are the outputs of 0-based blocks 8, 16 and 24, the
    # intermediate layers DepthVLM taps on Qwen3-VL's 27-block ViT (its deepstack indexes).
    'vit_layers': [9, 17, 25],
    'min_depth_m': 0.05,
    'max_depth_m': 25.0,
    'num_points_per_frame': 64,
}


def _finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def normalize_point_depth(value):
    if value is None:
        return None
    if not isinstance(value, dict) or set(value) - POINT_DEPTH_DEFAULTS.keys():
        raise ValueError('Unknown point_depth configuration')
    cfg = {**POINT_DEPTH_DEFAULTS, **value}
    for key in ('weight', 'weight_silog', 'weight_metric', 'weight_grad', 'silog_lambda',
                'smooth_l1_beta', 'min_depth_m', 'max_depth_m'):
        if not _finite(cfg[key]) or cfg[key] < 0:
            raise ValueError('Invalid point_depth setting: ' + key)
    if cfg['silog_lambda'] > 1.0 or cfg['smooth_l1_beta'] <= 0:
        raise ValueError('Invalid point_depth silog_lambda or smooth_l1_beta')
    if cfg['min_depth_m'] <= 0 or cfg['max_depth_m'] <= cfg['min_depth_m']:
        raise ValueError('Invalid point_depth depth bounds')
    for key, low, high in (('d_proj', 16, 2048), ('mlp_hidden', 16, 4096), ('num_heads', 1, 64),
                           ('context_depth', 1, 8), ('num_points_per_frame', 1, 4096)):
        if type(cfg[key]) is not int or not low <= cfg[key] <= high:
            raise ValueError('Invalid point_depth setting: ' + key)
    if cfg['d_proj'] % cfg['num_heads'] or cfg['d_proj'] % 4:
        raise ValueError('point_depth d_proj must be divisible by num_heads and by 4')
    vit_layers = cfg['vit_layers']
    if (not isinstance(vit_layers, list) or len(vit_layers) != 3
            or any(type(k) is not int or not 1 <= k <= 64 for k in vit_layers)
            or vit_layers != sorted(set(vit_layers))):
        raise ValueError('point_depth vit_layers must be 3 increasing 1-based ViT block indices')
    return cfg


def point_depth_enabled(cfg):
    return bool(cfg and cfg.get('weight', 0.0) > 0.0)


def sincos_2d(height, width, dim, device):
    """[H*W, dim] sin-cos embedding of normalized cell centres ((i + 0.5) / H, (j + 0.5) / W)."""
    quarter = dim // 4
    freqs = torch.exp(torch.arange(quarter, device=device, dtype=torch.float32) * (-math.log(1000.0) / max(1, quarter)))
    ys = (torch.arange(height, device=device, dtype=torch.float32) + 0.5) / height
    xs = (torch.arange(width, device=device, dtype=torch.float32) + 0.5) / width
    grid_y, grid_x = torch.meshgrid(ys, xs, indexing='ij')
    angles_y = 2 * math.pi * grid_y.reshape(-1, 1) * freqs * 16
    angles_x = 2 * math.pi * grid_x.reshape(-1, 1) * freqs * 16
    return torch.cat((angles_y.sin(), angles_y.cos(), angles_x.sin(), angles_x.cos()), dim=-1)


class AttentionBlock(nn.Module):
    """Pre-norm bidirectional self-attention block with LayerScale."""

    def __init__(self, dim, heads, mlp_ratio=4, init_values=0.01):
        super().__init__()
        self.heads = heads
        self.norm1, self.qkv, self.proj = nn.LayerNorm(dim), nn.Linear(dim, 3 * dim), nn.Linear(dim, dim)
        self.norm2 = nn.LayerNorm(dim)
        self.mlp = nn.Sequential(nn.Linear(dim, mlp_ratio * dim), nn.GELU(), nn.Linear(mlp_ratio * dim, dim))
        self.ls1 = nn.Parameter(torch.full((dim,), float(init_values)))
        self.ls2 = nn.Parameter(torch.full((dim,), float(init_values)))

    def forward(self, x):
        batch, length, dim = x.shape
        q, k, v = self.qkv(self.norm1(x)).view(batch, length, 3, self.heads, dim // self.heads).permute(2, 0, 3, 1, 4)
        attended = F.scaled_dot_product_attention(q, k, v, is_causal=False)
        x = x + self.ls1 * self.proj(attended.transpose(1, 2).reshape(batch, length, dim))
        return x + self.ls2 * self.mlp(self.norm2(x))


class CrossFrameBlock(nn.Module):
    """Attention within each temporal group, then across all groups' tokens (VGGT alternating attention)."""

    def __init__(self, dim, heads):
        super().__init__()
        self.frame = AttentionBlock(dim, heads)
        self.global_attention = AttentionBlock(dim, heads)

    def forward(self, tokens):
        groups, cells, dim = tokens.shape
        tokens = self.frame(tokens)
        return self.global_attention(tokens.reshape(1, groups * cells, dim)).reshape(groups, cells, dim)


class PointDepthHead(nn.Module):
    """Fused ViT + LLM visual features, cross-frame attention and continuous point queries (one row at a time)."""

    def __init__(self, llm_dim, settings, vit_dim):
        super().__init__()
        self.settings = normalize_point_depth(settings)
        if vit_dim is None:
            raise ValueError('The point-depth head needs the vision tower width')
        self.llm_dim, self.vit_dim = int(llm_dim), int(vit_dim)
        d = self.d_proj = self.settings['d_proj']
        self.min_depth_m = float(self.settings['min_depth_m'])
        self.max_depth_m = float(self.settings['max_depth_m'])
        self.vit_norms = nn.ModuleList([nn.LayerNorm(self.vit_dim) for _ in range(3)])
        self.vit_projs = nn.ModuleList([nn.Linear(self.vit_dim, d) for _ in range(3)])
        self.llm_norm = nn.LayerNorm(self.llm_dim)
        self.llm_proj = nn.Linear(self.llm_dim, d)
        self.group_embed = nn.Parameter(torch.zeros(16, d))
        # FiLM from [tan(fov_w/2), tan(fov_h/2), fov_w, fov_h]; zero-initialized output keeps identity at start.
        self.fov_film = nn.Sequential(nn.Linear(4, d), nn.SiLU(), nn.Linear(d, 2 * d))
        self.context = nn.ModuleList([CrossFrameBlock(d, self.settings['num_heads'])
                                      for _ in range(self.settings['context_depth'])])
        self.context_norm = nn.LayerNorm(d)
        groups = 8 if d % 8 == 0 else 1
        self.refine = nn.Sequential(nn.Conv2d(d, d, 3, padding=1), nn.GroupNorm(groups, d), nn.GELU(),
                                    nn.Conv2d(d, d, 3, padding=1))
        hidden = self.settings['mlp_hidden']
        self.point_mlp = nn.Sequential(nn.Linear(3 * d + 4, hidden), nn.GELU(), nn.Linear(hidden, hidden), nn.GELU(),
                                       nn.Linear(hidden, 1))
        self._init_weights()

    def _init_weights(self):
        for module in self.modules():
            if isinstance(module, (nn.Linear, nn.Conv2d)):
                nn.init.trunc_normal_(module.weight, std=0.02)
                if module.bias is not None:
                    nn.init.zeros_(module.bias)
            elif isinstance(module, (nn.LayerNorm, nn.GroupNorm)) and module.weight is not None:
                nn.init.ones_(module.weight)
                nn.init.zeros_(module.bias)
        nn.init.trunc_normal_(self.group_embed, std=0.02)
        nn.init.zeros_(self.fov_film[-1].weight)
        nn.init.zeros_(self.fov_film[-1].bias)
        with torch.no_grad():
            # Initial prediction near 2 m: min_depth + softplus(b) = 2.
            self.point_mlp[-1].bias.fill_(math.log(math.expm1(max(2.0 - self.min_depth_m, 0.1))))

    def encode(self, llm_grid, vit_grids, fov_hw):
        """One row: llm_grid [T, Hm, Wm, D_llm], vit_grids 3 x [T, 2Hm, 2Wm, D_vit], fov_hw [T, 2] -> [T, d, 2Hm, 2Wm]."""
        if llm_grid.ndim != 4 or llm_grid.shape[-1] != self.llm_dim:
            raise ValueError(f'Expected LLM visual grid [T, Hm, Wm, {self.llm_dim}], got {tuple(llm_grid.shape)}')
        groups, height, width, _ = llm_grid.shape
        if groups > self.group_embed.shape[0]:
            raise ValueError('More temporal groups than the head supports')
        if len(vit_grids) != 3 or any(v.shape != (groups, 2 * height, 2 * width, self.vit_dim) for v in vit_grids):
            raise ValueError('ViT grids must be three [T, 2Hm, 2Wm, D_vit] maps aligned with the LLM grid')
        if fov_hw.shape != (groups, 2):
            raise ValueError('Expected one predicted field of view per temporal group')
        fine = sum(proj(norm(grid.float())) for norm, proj, grid in zip(self.vit_norms, self.vit_projs, vit_grids))
        fine = fine.permute(0, 3, 1, 2)  # [T, d, 2Hm, 2Wm]
        coarse = self.llm_proj(self.llm_norm(llm_grid.float())) + F.avg_pool2d(fine, 2).permute(0, 2, 3, 1)
        fov = fov_hw.float().clamp(0.1, math.pi - 0.1)
        film = self.fov_film(torch.stack((torch.tan(fov[:, 1] / 2), torch.tan(fov[:, 0] / 2), fov[:, 1], fov[:, 0]), dim=-1))
        gamma, beta = film.chunk(2, dim=-1)
        coarse = coarse * (1 + gamma[:, None, None, :]) + beta[:, None, None, :]
        tokens = coarse.reshape(groups, height * width, self.d_proj)
        tokens = tokens + sincos_2d(height, width, self.d_proj, tokens.device)[None] + self.group_embed[:groups, None, :]
        for block in self.context:
            tokens = block(tokens)
        context = self.context_norm(tokens).reshape(groups, height, width, self.d_proj).permute(0, 3, 1, 2)
        fine = fine + F.interpolate(context, size=fine.shape[-2:], mode='bilinear', align_corners=False)
        return fine + self.refine(fine)

    def query(self, feature_map, uv_0_1000):
        """feature_map [T, d, H, W], uv_0_1000 [T, K, 2] ((0, 0) top-left) -> metric depth [T, K]."""
        groups, dim, height, width = feature_map.shape
        uv = uv_0_1000.float()
        if uv.ndim != 3 or uv.shape[0] != groups or uv.shape[-1] != 2:
            raise ValueError(f'Expected point queries [T, K, 2], got {tuple(uv.shape)}')
        if not torch.isfinite(uv).all() or torch.any(uv < 0) or torch.any(uv > 1000):
            raise ValueError('Point queries must lie in [0, 1000] x [0, 1000]')
        points = uv.shape[1]
        sampled = sample_points(feature_map, uv)
        centre = sampled[:, :, 0]
        grad_x = 0.5 * (sampled[:, :, 1] - sampled[:, :, 2])
        grad_y = 0.5 * (sampled[:, :, 3] - sampled[:, :, 4])
        # Sub-cell phase of the query on the fine grid (cell centres at integer + 0.5).
        phase_x = uv[..., 0] / 1000.0 * width - 0.5
        phase_y = uv[..., 1] / 1000.0 * height - 0.5
        phase = torch.stack((torch.sin(2 * math.pi * phase_x), torch.cos(2 * math.pi * phase_x),
                             torch.sin(2 * math.pi * phase_y), torch.cos(2 * math.pi * phase_y)), dim=-1)
        raw = self.point_mlp(torch.cat((centre, grad_x, grad_y, phase), dim=-1)).squeeze(-1)
        depth = self.min_depth_m + F.softplus(raw)
        if depth.shape != (groups, points):
            raise ValueError('Point-depth readout shape mismatch')
        return depth.clamp(max=self.max_depth_m)

    def forward(self, llm_grid, vit_grids, fov_hw, uv_0_1000):
        feature_map = self.encode(llm_grid, vit_grids, fov_hw)
        return feature_map if uv_0_1000 is None else self.query(feature_map, uv_0_1000)

    def row_loss(self, pred_depth, gt_depth, mask):
        """One row's loss: SILog + metric log-L1 and inverse-depth Smooth-L1 + within-frame pairwise log-depth."""
        if pred_depth.shape != gt_depth.shape or pred_depth.shape != mask.shape or pred_depth.ndim != 2:
            raise ValueError(f'Point-depth loss shape mismatch: {tuple(pred_depth.shape)} vs {tuple(gt_depth.shape)}')
        pred = pred_depth.float().clamp(min=self.min_depth_m, max=self.max_depth_m)
        gt = gt_depth.float()
        valid = mask.bool() & torch.isfinite(gt) & (gt >= self.min_depth_m) & (gt <= self.max_depth_m)
        if not valid.any():
            raise ValueError('A depth-supervised row has no valid depth label')
        safe_gt = torch.where(valid, gt, pred.detach())
        diff = torch.where(valid, torch.log(pred) - torch.log(safe_gt), torch.zeros_like(pred))
        count = valid.sum().float()
        mean_sq, mean = (diff ** 2).sum() / count, diff.sum() / count
        silog = torch.sqrt((mean_sq - self.settings['silog_lambda'] * mean ** 2).clamp_min(0) + 1e-6) - 1e-3
        inverse = F.smooth_l1_loss(1.0 / pred, 1.0 / safe_gt, beta=self.settings['smooth_l1_beta'], reduction='none')
        metric = diff.abs().sum() / count + torch.where(valid, inverse, torch.zeros_like(inverse)).sum() / count
        pair_terms, pair_count = pred.new_zeros(()), pred.new_zeros(())
        for stride in (1, 2):
            if diff.shape[1] > stride:
                both = valid[:, stride:] & valid[:, :-stride]
                pair_terms = pair_terms + ((diff[:, stride:] - diff[:, :-stride]).abs() * both).sum()
                pair_count = pair_count + both.sum()
        pairs = pair_terms / pair_count.clamp_min(1)
        return (self.settings['weight_silog'] * silog + self.settings['weight_metric'] * metric
                + self.settings['weight_grad'] * pairs)


def sample_points(feature_map, uv_0_1000):
    """Bilinear samples [T, K, 5, d] at each point and its +-1-cell neighbours in x and y.

    [0, 1000] spans the image edges: x maps to grid_sample's u = x / 500 - 1 with align_corners=False,
    so the centre of fine cell (i, j) of an H x W map sits at ((j + 0.5) / W * 1000, (i + 0.5) / H * 1000)."""
    groups, _, height, width = feature_map.shape
    uv = uv_0_1000.float()
    x, y = uv[..., 0] / 500.0 - 1.0, uv[..., 1] / 500.0 - 1.0
    dx, dy = 2.0 / width, 2.0 / height
    offsets = torch.tensor([[0, 0], [dx, 0], [-dx, 0], [0, dy], [0, -dy]], device=uv.device, dtype=uv.dtype)
    grid = torch.stack((x, y), dim=-1)[:, :, None, :] + offsets
    sampled = F.grid_sample(feature_map, grid, mode='bilinear', padding_mode='border', align_corners=False)
    return sampled.permute(0, 2, 3, 1)


def vit_blocks(module):
    """Zero-based ViT block index -> module, preferring the inner module under FSDP wrapping."""
    found = {}
    for name, child in module.named_modules():
        match = re.search(r'visual\.blocks\.(\d+)(\._fsdp_wrapped_module)?$', name)
        if match and (match.group(2) or int(match.group(1)) not in found):
            found[int(match.group(1))] = child
    return found


def vit_layer_hooks(module, vit_layer_indices, store):
    """Forward hooks keeping the first output of each requested 1-based ViT block; raises if one is absent."""
    blocks = vit_blocks(module)
    handles = []
    for k in vit_layer_indices:
        if k - 1 not in blocks:
            raise ValueError(f'ViT block {k} (1-based) does not exist for the point-depth head')

        def hook(layer, args, output, k=k):
            if k not in store:
                store[k] = output[0] if isinstance(output, tuple) else output
        handles.append(blocks[k - 1].register_forward_hook(hook))
    return handles


def vit_grids_by_row(raw_tokens, video_grid_thw, merge_size):
    """Separate the ViT's packed tokens per video and restore each one's spatial layout.

    The processor flattens every video's patches as [t, h / m, w / m, m, m] (each m x m merge
    unit contiguous). This returns, per row, [t, h, w, D] in raster order, so cell (i, j) covers
    image rows [i, i + 1) / h and columns [j, j + 1) / w. Raises on any count mismatch."""
    grids = video_grid_thw.tolist()
    sizes = [t * h * w for t, h, w in grids]
    if raw_tokens.ndim != 2 or raw_tokens.shape[0] != sum(sizes):
        raise ValueError(f'ViT token count {tuple(raw_tokens.shape)} differs from video_grid_thw total {sum(sizes)}')
    result = []
    starts = [sum(sizes[:i]) for i in range(len(sizes))]
    for (t, h, w), start, size in zip(grids, starts, sizes):
        chunk = raw_tokens[start:start + size]
        if h % merge_size or w % merge_size:
            raise ValueError('ViT grid is not divisible by the spatial merge size')
        dim = chunk.shape[-1]
        units = chunk.reshape(t, h // merge_size, w // merge_size, merge_size, merge_size, dim)
        result.append(units.permute(0, 1, 3, 2, 4, 5).reshape(t, h, w, dim))
    return result
