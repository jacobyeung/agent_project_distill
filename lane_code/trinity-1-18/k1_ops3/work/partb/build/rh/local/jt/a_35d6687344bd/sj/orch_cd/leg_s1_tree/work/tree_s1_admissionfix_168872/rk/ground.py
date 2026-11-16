"""Grounding interface backed only by an MDG mask export."""
from functools import lru_cache
import os
import sys

import numpy as np
from scipy import ndimage


@lru_cache(maxsize=1)
def mdg():
    sys.path.insert(0, os.environ.get('RK_MDG_ROOT', '/scratch/jjyeung/orch_cd/mdg_next/work/c1mix_mdg_ro'))
    from student_pilot import mdg_eval
    return mdg_eval


class MaskGround:
    def __init__(self, npz, tau=None):
        self.names, self.values, self.audit = mdg().read_npz(npz)
        self.by_name = {mdg().label(n): i for i, n in enumerate(self.names)}
        self.tau = float(self.audit['tau'] if tau is None else tau)
        if not 0 <= self.tau <= 1:
            raise ValueError('tau must be in [0,1]')
        self.geo = None
        self.cache = {}

    def index(self, obj):
        try:
            return self.by_name.get(mdg().label(obj))
        except ValueError:
            return None

    def vis(self, obj, k):
        q = self.index(obj)
        if q is None or not 1 <= k <= 32:
            return False, 0.0
        mask = self.values['mask'][q, k-1]
        area = float(mask.mean())
        return bool(self.values['prob'][q, k-1] >= self.tau and area > 0), area

    def pixels(self, obj, k, limit=None):
        key = (obj, k)
        if key not in self.cache:
            if not self.vis(obj, k)[0]:
                return np.empty((0, 2))
            mask = self.values['mask'][self.index(obj), k-1]
            eroded = ndimage.binary_erosion(mask, structure=np.ones((3, 3)), iterations=1)
            rows, cols = np.nonzero(eroded)
            h, w = mask.shape
            uv = np.column_stack(((cols+.5)/w*1000, (rows+.5)/h*1000))
            self.cache[key] = uv[((uv >= 20) & (uv <= 980)).all(1)]
        return self.cache[key]

    def lifted(self, obj, k):
        uv = self.pixels(obj, k)
        if not len(uv):
            return uv, np.empty((0, 3))
        P, Pc, spread = self.geo.lift(k, uv, mode='center')
        edge = np.minimum(uv, 1000-uv).min(1)
        ok = (np.isfinite(P).all(1) & np.isfinite(Pc).all(1) & (Pc[:, 2] > 0)
              & np.isfinite(spread) & (spread <= np.where(edge <= 40, .10, .25)))
        return uv[ok], P[ok]

    def get(self, obj, k, kind, other=None):
        if not self.vis(obj, k)[0]:
            return None if kind == 'box' else []
        q = self.index(obj)
        if kind in ('point', 'all'):
            return [self.values['uv'][q, k-1].astype(float).tolist()]
        if kind == 'box':
            mask = self.values['mask'][q, k-1]
            rows, cols = np.nonzero(mask)
            h, w = mask.shape
            return [cols.min()/w*1000, rows.min()/h*1000,
                    (cols.max()+1)/w*1000, (rows.max()+1)/h*1000]
        if kind == 'mask':
            return self.pixels(obj, k).tolist()
        if kind in ('edge', 'ends'):
            if self.geo is None:
                raise ValueError('Bind MaskGround.geo before requesting lifted edges')
            uv, P = self.lifted(obj, k)
            if not len(P):
                return []
            if kind == 'ends':
                from scipy.spatial.distance import cdist
                i, j = np.unravel_index(np.argmax(cdist(P, P)), (len(P), len(P)))
                return uv[[i, j]].tolist()
            _, Q = self.lifted(other, k)
            if not len(P) or not len(Q):
                return []
            from scipy.spatial import cKDTree
            return uv[np.argsort(cKDTree(Q).query(P)[0], kind='stable')[:3]].tolist()
        raise ValueError('Unknown grounding kind: '+kind)
