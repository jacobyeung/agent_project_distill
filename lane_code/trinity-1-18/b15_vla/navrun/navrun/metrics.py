"""VLN-CE measures and an independent implementation of FastDTW radius 1."""
import math
import numpy as np
from scipy.spatial.distance import cdist

def _dtw(x, y, window=None):
    n, m = len(x), len(y)
    if not n or not m:
        return (0.0 if n == m else math.inf), []
    distances = cdist(x, y, metric='euclidean')
    cells = ((i, j) for i in range(n) for j in range(m)) if window is None else window
    d = {(-1, -1): (0., -1, -1)}
    for i, j in cells:
        prev = min(((d.get((a, b), (math.inf,))[0], a, b) for a, b in
                    ((i-1, j), (i, j-1), (i-1, j-1))), key=lambda v: v[0])
        d[i, j] = (distances[i, j] + prev[0], prev[1], prev[2])
    if (n-1, m-1) not in d:
        raise ValueError('DTW window does not reach the endpoint')
    path, i, j = [], n-1, m-1
    while i >= 0 or j >= 0:
        path.append((i, j))
        _, i, j = d[i, j]
    return float(d[n-1, m-1][0]), path[::-1]

def exact_dtw(x, y):
    return _dtw(np.asarray(x, float), np.asarray(y, float))[0]

def _fast(x, y, radius):
    if len(x) < radius + 2 or len(y) < radius + 2:
        return _dtw(x, y)
    small_x = (x[:len(x)//2*2:2] + x[1:len(x)//2*2:2]) / 2
    small_y = (y[:len(y)//2*2:2] + y[1:len(y)//2*2:2]) / 2
    _, path = _fast(small_x, small_y, radius)
    coarse = {(i+a, j+b) for i, j in path for a in range(-radius, radius+1)
              for b in range(-radius, radius+1)}
    window = {(2*i+a, 2*j+b) for i, j in coarse for a in (0, 1) for b in (0, 1)
              if 0 <= 2*i+a < len(x) and 0 <= 2*j+b < len(y)}
    return _dtw(x, y, sorted(window))

def fast_dtw(x, y, radius=1):
    if radius < 0:
        raise ValueError('Negative FastDTW radius')
    return _fast(np.asarray(x, float), np.asarray(y, float), radius)[0]

def deduplicate_path(path):
    """VLN-CE's DTW measure records a point only when agent position changes."""
    out = []
    for p in path:
        if not out or not np.array_equal(p, out[-1]):
            out.append(np.asarray(p, float))
    return out

def metrics(path, reference, distances, shortest, stopped, radius=3.0, dtw='fast'):
    if not path or len(distances) != len(path):
        raise ValueError('Need one goal distance per path state')
    tl = float(np.linalg.norm(np.diff(np.asarray(path), axis=0), axis=1).sum())
    ne = float(distances[-1])
    sr = float(stopped and ne < radius)
    osr = float(min(distances) < radius)
    spl = (shortest / max(shortest, tl) if shortest > 0 else float(tl == 0)) if sr else 0.0
    prediction = deduplicate_path(path)
    reference = deduplicate_path(reference)
    ndtw = math.exp(-(fast_dtw if dtw == 'fast' else exact_dtw)(prediction, reference) / (len(reference) * radius)) if reference else None
    return dict(NE=ne if math.isfinite(ne) else None, SR=sr, SPL=spl, OSR=osr, TL=tl,
                nDTW=ndtw, SDTW=None if ndtw is None else sr * ndtw)

def aggregate(results):
    keys = ('NE', 'SR', 'SPL', 'OSR', 'TL', 'nDTW', 'SDTW')
    return dict(n=len(results), **{k: float(np.mean([r[k] for r in results if r.get(k) is not None]))
                                 if any(r.get(k) is not None for r in results) else None for k in keys})
