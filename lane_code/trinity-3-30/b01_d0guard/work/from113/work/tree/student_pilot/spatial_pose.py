"""Version-one pose frontend: 64 spatial cells, then frame/global attention twice.

The bottleneck is at most 256 channels, independent of the existing pose trunk.
No frame index is embedded: only the origin group differs from the other groups.
"""
import math

import torch
from torch import nn
from torch.nn import functional as F


TOKEN_BUDGET = 64


def pool_shape(height, width):
    """Near-isotropic downsample within the budget, without upsampling."""
    scale = min(1., math.sqrt(TOKEN_BUDGET / (height * width)))
    return max(1, int(height * scale)), max(1, int(width * scale))


def pool_grid(grid):
    # [groups, height, width, channels]. Pool in the encoder dtype before casting
    # the small result; never allocate a full-resolution FP32 copy of the raster.
    if grid.ndim != 4 or min(grid.shape) < 1:
        raise ValueError('Spatial pose requires a nonempty raster grid')
    shape = pool_shape(*grid.shape[1:3])
    # Extremely thin grids still have a fixed upper bound.
    shape = tuple(min(TOKEN_BUDGET, n) for n in shape)
    return F.adaptive_avg_pool2d(grid.permute(0, 3, 1, 2), shape).permute(0, 2, 3, 1).float()


def positions_2d(height, width, dim, device):
    y, x = torch.meshgrid(torch.linspace(-1, 1, height, device=device),
                          torch.linspace(-1, 1, width, device=device), indexing='ij')
    frequency = torch.arange(1, dim // 4 + 1, device=device) * (math.pi / 2)
    phase = torch.stack((x, y), -1).reshape(-1, 2, 1) * frequency
    return torch.cat((phase.sin(), phase.cos()), -1).flatten(1)


class SpatialPose(nn.Module):
    def __init__(self, hidden_size, embed_dim):
        super().__init__()
        # Imported here to keep CameraSupervision's optional import acyclic.
        from .camera_head import Block
        dim = min(256, embed_dim)
        # The camera schema allows widths not divisible by four.
        dim = max(16, dim // 4 * 4)
        self.width = dim
        self.project = nn.Linear(hidden_size, dim)
        self.camera_tokens = nn.Parameter(torch.randn(2, dim) * .02)
        self.blocks = nn.ModuleList([Block(dim, 4, init_values=1.) for _ in range(4)])
        self.norm = nn.LayerNorm(dim)
        self.output = nn.Linear(dim, hidden_size)

    def forward(self, grids, groups, key_mask=None):
        if grids is None or len(grids) == 0:
            raise ValueError('spatial_tokens_v1 requires captured ViT grids')
        outputs, buckets = [None] * len(grids), {}
        for row, grid in enumerate(grids):
            grid = pool_grid(grid)
            n, height, width, _ = grid.shape
            if n > groups:
                raise ValueError('Spatial groups exceed camera positions')
            buckets.setdefault(tuple(grid.shape), []).append((row, grid))
        for shape, entries in buckets.items():
            rows = [row for row, _ in entries]
            grid = torch.stack([grid for _, grid in entries])
            n, height, width, _ = shape
            batch = len(rows)
            spatial = self.project(grid.flatten(2, 3))
            spatial = spatial + positions_2d(height, width, self.width, grid.device)[None, None]
            cam = self.camera_tokens[(torch.arange(n, device=grid.device) > 0).long()]
            tokens = torch.cat((cam[None, :, None].expand(batch, -1, -1, -1), spatial), 2)
            length = tokens.shape[2]
            valid = None if key_mask is None else key_mask[rows, :n]
            for index, block in enumerate(self.blocks):
                if index % 2 == 0:
                    tokens = block(tokens.reshape(batch * n, length, self.width)).reshape(batch, n, length, self.width)
                else:
                    mask = None if valid is None else valid[:, :, None].expand(batch, n, length).reshape(batch, -1)
                    tokens = block(tokens.reshape(batch, n * length, self.width), mask).reshape(batch, n, length, self.width)
            cameras = self.output(self.norm(tokens[:, :, 0]))
            for i, row in enumerate(rows):
                outputs[row] = F.pad(cameras[i], (0, 0, 0, groups - n))
        return torch.stack(outputs)
