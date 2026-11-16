"""Ground-truth visibility per (capture, category) from instance rasters at the row's own 32 pins.
Rule (rows_a2 calibration, work/fs/calib.py): instance visible in pin f when its raster pixel share >= FLOOR."""
import json, os, re, glob, collections
import numpy as np
FLOOR = 0.002
DENY = {'wall', 'floor', 'ceiling', 'object', 'objects', 'remove', 'split', 'unknown', 'otherfurniture', 'otherstructure',
        'otherprop', 'stuff', 'item', 'items', 'thing', 'things', 'structure', 'beam', 'pipe', 'pipes', 'cable', 'cables',
        'wire', 'wires', 'decoration', 'misc', 'other'}
def norm(s): return re.sub(r'\s+', ' ', str(s).strip().lower().replace('_', ' '))
def load_raster(path):
    z = np.load(path); inst = z['inst']; n = inst.shape[1] * inst.shape[2]
    share = collections.defaultdict(dict); cent = collections.defaultdict(dict)
    W = inst.shape[2]
    for f in range(inst.shape[0]):
        a = inst[f]; u, c = np.unique(a, return_counts=True)
        for i, cc in zip(u, c):
            if i >= 0:
                share[int(i)][f + 1] = cc / n
        if len(u):
            # mean column of each instance in this frame (for the horizontal region word)
            cols = np.broadcast_to(np.arange(W), a.shape)
            s = np.bincount((a + 1).ravel(), weights=cols.ravel(), minlength=int(a.max()) + 2)
            k = np.bincount((a + 1).ravel(), minlength=int(a.max()) + 2)
            for i in u:
                if i >= 0: cent[int(i)][f + 1] = float(s[i + 1] / k[i + 1] / W)
    labels = {int(i): norm(l) for i, l in zip(z['ids'], z['labels'])}
    return dict(share=share, cent=cent, labels=labels, fi=[int(x) for x in z['frame_indices']], shape=list(inst.shape),
                valid=[bool(x) for x in z['valid']] if 'valid' in z.files else None)
def first_seen(rs, iid, floor=FLOOR):
    v = [f for f, s in rs['share'].get(iid, {}).items() if s >= floor]
    return min(v) if v else None
def categories(rs):
    by = collections.defaultdict(list)
    for i, l in rs['labels'].items(): by[l].append(i)
    return by
def ambiguous(cat, labels):
    """another label in the scene shares the head noun (office chair / chair) or is a plural variant"""
    for l in labels:
        if l == cat: continue
        if l.endswith(' ' + cat) or cat.endswith(' ' + l) or l in (cat + 's', cat + 'es') or cat in (l + 's', l + 'es'):
            return l
    return None
