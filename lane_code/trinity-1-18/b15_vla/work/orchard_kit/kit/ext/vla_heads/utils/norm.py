"""Per-dimension normalisation (design record 5.5): the 1st and 99th percentiles of the training
subset map to [-1, 1] with clipping; saved as JSON {q01, q99, count, subset_sha}. The evaluator
de-normalises with the same file. `skip` dimensions (the gripper) keep their raw values and sign.

LIBERO convention: a 7-D delta end-effector action (xyz, axis-angle, gripper) with gripper -1 = open,
+1 = close, and an 8-D state (eef position 3, axis-angle 3, gripper joint positions 2).
"""
import json
from pathlib import Path

import numpy as np
import torch


class Normalizer:
    """Per-dimension affine map of the [q_low, q_high] percentile range onto [-1, 1] with clipping.

    `skip` lists dimensions left untouched (for example a gripper already in {-1, +1}).
    Dimensions with q_high == q_low map to 0 and decode to q_low.
    """

    def __init__(self, low, high, skip=(), q=(1.0, 99.0), count=None, subset_sha=None):
        self.count, self.subset_sha = count, subset_sha
        self.low = np.asarray(low, dtype=np.float64)
        self.high = np.asarray(high, dtype=np.float64)
        self.skip = sorted(int(i) for i in skip)
        self.q = tuple(float(v) for v in q)
        if self.low.shape != self.high.shape or self.low.ndim != 1 or np.any(self.high < self.low):
            raise ValueError('low and high must be 1-D with high >= low')

    @classmethod
    def fit(cls, data, skip=(), q=(1.0, 99.0), subset_sha=None):
        """data [..., A] (array or tensor; the training subset only) -> Normalizer from its q[0] and
        q[1] percentiles."""
        x = np.asarray(data.detach().cpu() if torch.is_tensor(data) else data, dtype=np.float64)
        x = x.reshape(-1, x.shape[-1])
        return cls(np.percentile(x, q[0], axis=0), np.percentile(x, q[1], axis=0), skip, q, len(x), subset_sha)

    @property
    def dim(self):
        return len(self.low)

    def _apply(self, x, fn):
        """Compute in float64 numpy; tensors come back with their own dtype and device (no gradient)."""
        if torch.is_tensor(x):
            return torch.as_tensor(fn(x.detach().cpu().double().numpy()), dtype=x.dtype, device=x.device)
        return fn(np.asarray(x, dtype=np.float64))

    def _parts(self):
        flat = self.high == self.low
        span = np.where(flat, 1.0, self.high - self.low)
        keep = np.zeros(self.dim, dtype=bool)
        keep[self.skip] = True
        return span, keep, flat

    def normalize(self, x):
        span, keep, flat = self._parts()
        def fn(v):
            y = np.where(flat, 0.0, np.clip(2 * (v - self.low) / span - 1, -1, 1))
            return np.where(keep, v, y)
        return self._apply(x, fn)

    def denormalize(self, y):
        span, keep, flat = self._parts()
        def fn(v):
            x = np.where(flat, self.low, (v + 1) / 2 * span + self.low)
            return np.where(keep, v, x)
        return self._apply(y, fn)

    def to_dict(self):
        return dict(kind='percentile_minmax_v1', q=list(self.q), q01=self.low.tolist(), q99=self.high.tolist(),
                    skip=self.skip, count=self.count, subset_sha=self.subset_sha)

    @classmethod
    def from_dict(cls, d):
        if d.get('kind') != 'percentile_minmax_v1':
            raise ValueError('Unknown normalizer kind')
        return cls(d['q01'], d['q99'], d['skip'], d['q'], d.get('count'), d.get('subset_sha'))

    def save(self, path):
        Path(path).write_text(json.dumps(self.to_dict(), indent=2) + '\n')

    @classmethod
    def load(cls, path):
        return cls.from_dict(json.loads(Path(path).read_text()))
