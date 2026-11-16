"""Frozen ttower scale estimator; preserve exact estimator arithmetic."""
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

