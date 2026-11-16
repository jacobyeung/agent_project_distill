"""Per-dimension min-max normalisation (`minmax_subset_v1`, schema 7).

Statistics are the per-dimension min and max over the training subset (StarVLA's
`Libero4in1DataConfig` statistic), saved as JSON {kind, min, max, count, subset_sha}. The first
len(min) dimensions are normalised, y = 2 (x - min) / (max - min) - 1, and decoded as
x = (y + 1) / 2 (max - min) + min; later dimensions pass through unchanged (the action's gripper g,
dim 6, which is not normalised). Dimensions with max == min map to 0 and decode to min.

- Actions: min and max hold dims 0-5; training values lie inside [-1, 1], so normalize does not clip
  and the round trip is exact there. At evaluation `denormalize` clips the predicted y to [-1, 1]
  first (clip=True, the default).
- Proprio (8-D: eef position 3, eef axis-angle 3, gripper joints 2): all 8 dims; the evaluator calls
  normalize(x, clip=True).
"""
import json
from pathlib import Path

import numpy as np
import torch

KIND = 'minmax_subset_v1'


class Normalizer:
    def __init__(self, min, max, count=None, subset_sha=None):
        self.min = np.asarray(min, dtype=np.float64)
        self.max = np.asarray(max, dtype=np.float64)
        self.count, self.subset_sha = count, subset_sha
        if self.min.shape != self.max.shape or self.min.ndim != 1 or np.any(self.max < self.min):
            raise ValueError('min and max must be 1-D with max >= min')

    @classmethod
    def fit(cls, data, dims=None, subset_sha=None):
        """data [..., A] (array or tensor; the training subset only) -> statistics of the first `dims`
        dimensions (default all)."""
        x = np.asarray(data.detach().cpu() if torch.is_tensor(data) else data, dtype=np.float64)
        x = x.reshape(-1, x.shape[-1])[:, :dims]
        return cls(x.min(0), x.max(0), len(x), subset_sha)

    @property
    def dim(self):
        return len(self.min)

    def _apply(self, x, fn):
        """Compute in float64 numpy; tensors come back with their own dtype and device (no gradient)."""
        if torch.is_tensor(x):
            return torch.as_tensor(fn(x.detach().cpu().double().numpy()), dtype=x.dtype, device=x.device)
        return fn(np.asarray(x, dtype=np.float64))

    def _split(self, v):
        if v.shape[-1] < self.dim:
            raise ValueError(f'expected at least {self.dim} dims, got {v.shape[-1]}')
        return v[..., :self.dim], v[..., self.dim:]

    def normalize(self, x, clip=False):
        flat = self.max == self.min
        span = np.where(flat, 1.0, self.max - self.min)

        def fn(v):
            head, tail = self._split(v)
            y = np.where(flat, 0.0, 2 * (head - self.min) / span - 1)
            return np.concatenate([np.clip(y, -1, 1) if clip else y, tail], -1)
        return self._apply(x, fn)

    def denormalize(self, y, clip=True):
        flat = self.max == self.min
        span = np.where(flat, 1.0, self.max - self.min)

        def fn(v):
            head, tail = self._split(v)
            head = np.clip(head, -1, 1) if clip else head
            return np.concatenate([np.where(flat, self.min, (head + 1) / 2 * span + self.min), tail], -1)
        return self._apply(y, fn)

    def to_dict(self):
        return dict(kind=KIND, min=self.min.tolist(), max=self.max.tolist(), count=self.count, subset_sha=self.subset_sha)

    @classmethod
    def from_dict(cls, d):
        if d.get('kind') != KIND:
            raise ValueError(f'Normalizer kind must be {KIND}, got {d.get("kind")!r}')
        return cls(d['min'], d['max'], d.get('count'), d.get('subset_sha'))

    def save(self, path):
        Path(path).write_text(json.dumps(self.to_dict(), indent=2) + '\n')

    @classmethod
    def load(cls, path):
        return cls.from_dict(json.loads(Path(path).read_text()))
