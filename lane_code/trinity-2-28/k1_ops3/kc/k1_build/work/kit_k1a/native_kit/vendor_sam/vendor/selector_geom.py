import math
import numpy as np

class GeomTower:
    def __init__(self, path):
        import programs as PR
        self.h = PR.load_heads(path)
        assert self.h.grid is not None
        ys, xs = np.mgrid[0:H, 0:W]
        self.u, self.v = (xs + .5) / W * 1000, (ys + .5) / H * 1000
        self.frames = list(range(1, 33))
        self._d = {}

    def depth(self, k):
        if k not in self._d:
            self._d[k] = self.h._depth(k-1, self.u.ravel(), self.v.ravel()).reshape(H, W).astype(np.float32)
        return self._d[k]

    def rays(self, k):
        fh, fw = self.h.fov[k-1]
        return np.stack([(self.u/500-1)*math.tan(fw/2), (self.v/500-1)*math.tan(fh/2), np.ones_like(self.u)], -1)

    def cam(self, k):
        return self.h.cam(k)

    def project(self, k, P):
        R, t = self.cam(k)
        Pc = (P - t) @ R
        z = Pc[:, 2]
        fh, fw = self.h.fov[k-1]
        u = 500*(Pc[:, 0]/np.maximum(z, 1e-6)/math.tan(fw/2)+1)
        v = 500*(Pc[:, 1]/np.maximum(z, 1e-6)/math.tan(fh/2)+1)
        return u/1000*W - .5, v/1000*H - .5, z

def lift(geom, k, m, mode=None):
    """World points of mask m on frame k (stride-2 grid as prog_v2.Fused), optional erosion / depth-edge drop."""
    if mode in ('e1', 'e2'):
        er = ndimage.binary_erosion(m, ndimage.generate_binary_structure(2, 1), iterations=int(mode[1]))
        m = er if er.sum() >= 8 else m
    D = geom.depth(k)
    if mode == 'edge':
        keep = m & ~edge_mask(D)
        m = keep if keep.sum() >= 8 else m
    if mode == 'dc':
        m = depth_consistent(m, D)
    sub = m[::STEP, ::STEP] & (D[::STEP, ::STEP] > 0)
    if sub.sum() < 3:
        return None
    d = D[::STEP, ::STEP][sub]
    R, t = geom.cam(k)
    return (geom.rays(k)[::STEP, ::STEP][sub] * d[:, None]) @ R.T + t

def union(parts, p):
    """One instance from accepted candidates: per frame the union of members (candidate order by p)."""
    fr = {}
    for cid, masks in sorted(parts, key=lambda t: -p[t[0]]):
        for k, m in masks.items():
            fr[k] = fr[k] | m if k in fr else m
    return fr
