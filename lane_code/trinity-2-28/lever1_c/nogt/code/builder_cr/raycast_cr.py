"""Clean-room first-hit raster of a triangle mesh (CPU, numpy, float64).

For each pixel centre (x + off, y + off) the ray K^-1 [u, v, 1] is intersected
with every triangle whose projected bounding box covers it; the smallest
camera-z hit wins. Returns z-depth (or ray length) and face index (-1 unhit).
"""
import numpy as np


def first_hits(vertices, faces, c2w, K, hw, off=0.5, near=1e-6, mode="z", chunk=200000):
    H, W = hw
    c2w = np.asarray(c2w, np.float64)
    w2c = np.linalg.inv(c2w)
    v = np.asarray(vertices, np.float64) @ w2c[:3, :3].T + w2c[:3, 3]
    tri = v[faces]                                  # F,3,3 camera coords
    z = tri[..., 2]
    keep = (z > near).all(1)
    idx = np.nonzero(keep)[0]
    tri = tri[idx]
    fx, fy, cx, cy = K[0, 0], K[1, 1], K[0, 2], K[1, 2]
    px = fx * tri[..., 0] / tri[..., 2] + cx - off  # continuous coords whose integer = pixel index
    py = fy * tri[..., 1] / tri[..., 2] + cy - off
    x0 = np.clip(np.ceil(px.min(1)), 0, W).astype(np.int64)
    x1 = np.clip(np.floor(px.max(1)), -1, W - 1).astype(np.int64)
    y0 = np.clip(np.ceil(py.min(1)), 0, H).astype(np.int64)
    y1 = np.clip(np.floor(py.max(1)), -1, H - 1).astype(np.int64)
    nx = x1 - x0 + 1
    ny = y1 - y0 + 1
    ok = (nx > 0) & (ny > 0)
    idx, tri, x0, y0, nx, ny = idx[ok], tri[ok], x0[ok], y0[ok], nx[ok], ny[ok]
    best = np.full(H * W, np.inf)
    face = np.full(H * W, -1, np.int64)
    area = nx * ny
    order = np.argsort(area)
    start = 0
    cum = np.cumsum(area[order])
    while start < len(order):
        stop = int(np.searchsorted(cum, (cum[start - 1] if start else 0) + chunk, side="right"))
        stop = max(stop, start + 1)
        sel = order[start:stop]
        start = stop
        a = area[sel]
        rep = np.repeat(np.arange(len(sel)), a)
        local = np.arange(rep.size) - np.repeat(np.cumsum(a) - a, a)
        t = sel[rep]
        xs = x0[t] + local % nx[t]
        ys = y0[t] + local // nx[t]
        d = np.stack([(xs + off - cx) / fx, (ys + off - cy) / fy, np.ones(xs.size)], 1)
        p0, p1, p2 = tri[t, 0], tri[t, 1], tri[t, 2]
        e1, e2 = p1 - p0, p2 - p0
        pv = np.cross(d, e2)
        det = (e1 * pv).sum(1)
        good = np.abs(det) > 1e-18
        inv = np.where(good, 1.0 / np.where(good, det, 1.0), 0.0)
        tv = -p0
        uu = (tv * pv).sum(1) * inv
        qv = np.cross(tv, e1)
        vv = (d * qv).sum(1) * inv
        tt = (e2 * qv).sum(1) * inv
        hit = good & (uu >= 0) & (vv >= 0) & (uu + vv <= 1) & (tt > 0)
        if not hit.any():
            continue
        pix = (ys * W + xs)[hit]
        dep = tt[hit] if mode == "z" else (tt * np.linalg.norm(d, axis=1))[hit]
        fid = idx[t[hit]]
        o = np.lexsort((fid, dep, pix))
        pix, dep, fid = pix[o], dep[o], fid[o]
        first = np.r_[True, pix[1:] != pix[:-1]]
        pix, dep, fid = pix[first], dep[first], fid[first]
        better = dep < best[pix]
        best[pix[better]] = dep[better]
        face[pix[better]] = fid[better]
    best = best.reshape(H, W)
    return np.where(np.isfinite(best), best, np.inf), face.reshape(H, W)
