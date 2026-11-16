import numpy as np
def estimate(depth, confidence, vc):
    d, c, v = (np.asarray(x, float) for x in (depth, confidence, vc))
    if d.shape != c.shape or d.shape != v.shape:
        raise ValueError('Depth/confidence/V-C grids must match')
    finite = c[np.isfinite(c)]
    if not len(finite):
        raise ValueError('No finite confidence')
    threshold = float(np.percentile(finite, 50))
    selected = np.isfinite(c) & (c > threshold) & np.isfinite(d) & (d > 0) & np.isfinite(v) & (v > .1) & (v < 10)
    if not selected.any():
        raise ValueError('No eligible scale points (confidence must be strictly above median)')
    return float(np.median(v[selected] / d[selected])), selected, threshold

def assert_identity(raw):
    raw = np.asarray(raw)
    if raw.ndim != 2 or raw.shape[1] != 9 or not np.isfinite(raw).all():
        raise ValueError('Invalid pose codes')
    if not np.allclose(raw[0, :3], 0, atol=2e-5) or not np.allclose(raw[0, 3:6], 0, atol=2e-5) or not np.isclose(abs(raw[0, 6]), 1, atol=2e-5):
        raise ValueError('Frame 1 must be identity in raw E_k coordinates')
    if not np.allclose(np.linalg.norm(raw[:, 3:7], axis=1), 1, atol=1e-3):
        raise ValueError('Non-unit quaternion')
    if np.any(raw[:, 7:] <= 0) or np.any(raw[:, 7:] >= np.pi):
        raise ValueError('FoV outside (0,pi)')
