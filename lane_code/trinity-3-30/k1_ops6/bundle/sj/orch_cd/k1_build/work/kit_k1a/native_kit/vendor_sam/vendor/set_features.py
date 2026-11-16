import numpy as np

def iou(a, b):
    i = np.logical_and(a, b).sum()
    return float(i/np.logical_or(a, b).sum()) if i else 0.

def match_ids(gms, preds):
    """Greedy one-to-one IoU > 0.5; gms = [(gid, mask)] -> matched gids."""
    pairs = sorted(((iou(g, p), gi, j) for gi, g in gms for j, p in enumerate(preds)), reverse=True)
    ug, up = set(), set()
    for v, gi, j in pairs:
        if v > .5 and gi not in ug and j not in up:
            ug.add(gi)
            up.add(j)
    return sorted(ug)

def set_features(out, g):
    peaks = np.array([r['features']['peak'] for r in out])
    order = (-peaks).argsort(kind='stable')
    rank = np.empty(len(out))
    rank[order] = np.arange(len(out))
    for r, rk in zip(out, rank):
        f = r['features']
        f['n_cands_name'] = float(len(out))
        f['peak_rank'] = float(rk)
        f['peak_rank_frac'] = float(rk/max(len(out)-1, 1))
        f['peak_rel'] = float(f['peak']/max(peaks.max(), 1e-6))
        f['coverage'] = float(f['n_members']/max(f['reproj_vis'], 1))
        f['log_members'] = float(np.log1p(f['n_members']))
