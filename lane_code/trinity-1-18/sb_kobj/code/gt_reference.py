"""Unedited GTSource class from the staged reference; PATCH=10.0 from that file."""
import numpy as np
PATCH=10.0
class GTSource:
    kind = 'gt'

    def __init__(self, path):
        z = np.load(path, allow_pickle=False)
        self.depth, self.inst, self.K, self.c2w, self.valid = z['depth'], z['inst'], z['K'], z['c2w'], z['valid']
        self.ids, self.labels = z['ids'], [str(x) for x in z['labels']]
        self.obb = {int(i): {'centroid': c, 'axesLengths': l, 'normalizedAxes': a}
                    for i, c, l, a in zip(z['ids'], z['obb_centroid'], z['obb_lengths'], z['obb_axes'])}
        self.H, self.W = self.depth.shape[1:]
        self.Kinv = np.linalg.inv(self.K)

    def frame_of(self, k):
        return k

    def has(self, k):
        return bool(self.valid[k - 1])

    def cam(self, k):
        T4 = self.c2w[k - 1]
        return T4[:3, :3], T4[:3, 3]

    def px(self, uv):
        uv = np.asarray(uv, float).reshape(-1, 2)
        return (np.clip((uv[:, 0] / 1000.0 * self.W).astype(int), 0, self.W - 1),
                np.clip((uv[:, 1] / 1000.0 * self.H).astype(int), 0, self.H - 1))

    def lift(self, k, uv, mode='p30'):
        uv = np.asarray(uv, float).reshape(-1, 2)
        D = self.depth[k - 1]
        offs = np.array([(dx, dy) for dx in np.linspace(-PATCH, PATCH, 5) for dy in np.linspace(-PATCH, PATCH, 5)])
        pu = np.clip(uv[:, None, 0] + offs[None, :, 0], 0, 999.9)
        pv = np.clip(uv[:, None, 1] + offs[None, :, 1], 0, 999.9)
        xs, ys = self.px(np.stack([pu.ravel(), pv.ravel()], 1))
        dp = D[ys, xs].reshape(len(uv), -1).astype(float)
        dp[dp <= 0] = np.nan
        with np.errstate(all='ignore'):
            p20, p30, p50, p80 = (np.nanpercentile(dp, q, axis=1) for q in (20, 30, 50, 80))
        spread = (p80 - p20) / np.maximum(p50, 1e-3)
        x, y = self.px(uv)
        dc = D[y, x].astype(float)
        d = p30 if mode == 'p30' else np.where(dc > 0, dc, np.nan)
        pix = np.stack([(x + 0.5), (y + 0.5), np.ones(len(x))], 1)
        Pc = (pix @ self.Kinv.T) * d[:, None]
        R, t = self.cam(k)
        return Pc @ R.T + t, Pc, spread

    def dense(self, k, step=4):
        D = self.depth[k - 1][::step, ::step]
        ys, xs = np.nonzero(D > 0)
        pix = np.stack([(xs * step + 0.5), (ys * step + 0.5), np.ones(len(xs))], 1)
        Pc = (pix @ self.Kinv.T) * D[ys, xs][:, None]
        R, t = self.cam(k)
        return Pc @ R.T + t
