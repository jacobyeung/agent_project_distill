"""K1 held-out price of the reader's box lifting (GT instance masks, E3 geometry, S4 and SO scales, G1 gravity).

Arms per scale s in (S4, SO), gravity G1, all on the reader's tree (tree_b01ce449):
  s+G1+dep    deployed E3 path (harness.distance: ground_lifting + Session default box policy)
  s+G1+plain  the reader: lift_plain (every mask pixel) + MinAreaBoxProvider (e2e_reader.grounding)
  s+G1+best   lift_plain restricted to the best frame (largest mask area); no constant
  s+G1+besthull  hull, then the best surviving frame only
  s+G1+bestspread  best frame, points with depth-stencil spread <= the frame's median spread
  s+G1+bestotsu    best frame, larger cluster of an exact 1-D two-means split of camera depth
  s+G1+hull   lift_plain, then each point is kept when, over the other frames where the object is visible
              and the point projects into the image in front of the camera, it falls inside the mask at
              least as often as outside (majority vote; points with no such frame are kept)
Usage (inside the harness copy, run.sh environment): python -B lift_price.py READER_ROOT SPLIT [k n]
A geometry the tree refuses (GeometryError) refuses every arm of that capture alike.
"""
import json, sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parent
READER = Path(sys.argv[1]).resolve()
TREE_B04 = READER.parent / 'tree_rebuild/work/base/tree_b01ce449'
SPLIT = sys.argv[2]
assert SPLIT in ('train', 'heldout')
k, n = (int(sys.argv[3]), int(sys.argv[4])) if len(sys.argv) > 4 else (0, 1)
TAG = sys.argv[5] if len(sys.argv) > 5 else 'v2'
ONLY = sys.argv[6].split(',') if len(sys.argv) > 6 else None
src = (HERE / 'harness.py').read_text()
old = "TREE = Path('/scratch/jjyeung/orch_cd/leg_s1_tree/work/tree_s1_admissionfix_168872')"
assert src.count(old) == 1
src = src.replace(old, f"TREE = Path('{TREE_B04}')")
old_root = "assert ROOT == Path('/scratch/jjyeung/orch_n30/b04_e2ehook_sh/harness')"
assert src.count(old_root) == 1
src = src.replace(old_root, f"assert ROOT == Path('{HERE}')")
import types
H = types.ModuleType('e3h'); H.__file__ = str(HERE / 'harness.py')
sys.modules['e3h'] = H
exec(compile(src, str(HERE / 'harness.py'), 'exec'), H.__dict__)
sys.path.insert(1, str(READER))
from e2e_reader.grounding import lift_plain, MinAreaBoxProvider, mask_pixels
from trace_format.ground_v313 import Session
from student_pilot import ground_lifting


def lift_best(name, masks, geometry):
    r = lift_plain(name, masks, geometry)
    if r['seen']:
        b = r['best']
        r = dict(r, frames=[b], points={str(b): r['points'][str(b)]})
    return r


def project(geometry, j, P):
    R, t = geometry.cam(j)
    Pc = (P - t) @ R
    h = Pc @ geometry.K[j - 1].T @ np.linalg.inv(geometry.A[j - 1]).T
    with np.errstate(divide='ignore', invalid='ignore'):
        uv = h[:, :2] / h[:, 2:3]
    return uv, Pc[:, 2] > 0


def lift_hull(name, masks, geometry):
    r = lift_plain(name, masks, geometry)
    if not r['seen']:
        return r
    masks = np.asarray(masks, bool)
    Hm, Wm = masks.shape[1:]
    pts, frames = {}, []
    for f in r['frames']:
        P = np.asarray(r['points'][str(f)], float)
        inside = np.zeros(len(P), int); outside = np.zeros(len(P), int)
        for j in r['visible']:
            if j == f:
                continue
            uv, front = project(geometry, j, P)
            ok = front & np.isfinite(uv).all(1) & (uv[:, 0] >= 0) & (uv[:, 0] < 1000) & (uv[:, 1] >= 0) & (uv[:, 1] < 1000)
            col = np.clip((uv[ok, 0] / 1000 * Wm).astype(int), 0, Wm - 1); row = np.clip((uv[ok, 1] / 1000 * Hm).astype(int), 0, Hm - 1)
            hit = masks[j - 1][row, col]
            idx = np.nonzero(ok)[0]
            inside[idx] += hit; outside[idx] += ~hit
        keep = inside >= outside
        if keep.any():
            frames.append(f); pts[str(f)] = P[keep].tolist()
    if not frames:
        return dict(r, seen=False, frames=[], points={})
    best = min(frames, key=lambda q: (-r['areas'][str(q)], q))
    return dict(r, frames=frames, points=pts, best=best)


def lift_besthull(name, masks, geometry):
    r = lift_hull(name, masks, geometry)
    if r['seen']:
        b = r['best']
        r = dict(r, frames=[b], points={str(b): r['points'][str(b)]})
    return r


def _best_points(name, masks, geometry):
    r = lift_best(name, masks, geometry)
    if not r['seen']:
        return r, None, None
    b = r['best']
    uv = mask_pixels(np.asarray(masks, bool)[b - 1])
    P, Pc, spread = (np.asarray(x, np.float64) for x in geometry.lift(b, uv, mode='center'))
    ok = np.isfinite(P).all(1) & np.isfinite(Pc).all(1) & (Pc[:, 2] > 0)
    return r, (P[ok], Pc[ok, 2], spread[ok]), b


def _keep(r, b, P):
    if len(P) < 4:
        return dict(r, seen=False, frames=[], points={})
    return dict(r, frames=[b], points={str(b): P.tolist()})


def lift_bestspread(name, masks, geometry):
    """Best frame; keep points whose 5x5 depth-stencil spread is at most the frame's median spread."""
    r, x, b = _best_points(name, masks, geometry)
    if x is None:
        return r
    P, z, sp = x
    return _keep(r, b, P[sp <= np.median(sp)])


def lift_bestotsu(name, masks, geometry):
    """Best frame; two-means on camera depth (exact 1-D split minimising within-cluster variance); keep the larger cluster."""
    r, x, b = _best_points(name, masks, geometry)
    if x is None:
        return r
    P, z, sp = x
    o = np.argsort(z); zs = z[o]; n = len(zs)
    if n < 8:
        return _keep(r, b, P)
    c = np.cumsum(zs); c2 = np.cumsum(zs * zs)
    i = np.arange(1, n)
    left = c2[:-1] - c[:-1] ** 2 / i
    right = (c2[-1] - c2[:-1]) - (c[-1] - c[:-1]) ** 2 / (n - i)
    cut = int(np.argmin(left + right)) + 1
    keep = o[:cut] if cut >= n - cut else o[cut:]
    return _keep(r, b, P[np.sort(keep)])


LIFTS = dict(plain=lift_plain, best=lift_best, hull=lift_hull, besthull=lift_besthull,
             bestspread=lift_bestspread, bestotsu=lift_bestotsu)
try:
    from e2e_reader.grounding import lift_bestspread as _shipped
    LIFTS['shipped'] = _shipped  # the reader's own lifting, for the port check (train only)
except ImportError:
    pass


def reader_distance(row, geo, gt, lift):
    def socket(name):
        iid = row.get('gt_instances', {}).get(name)
        if iid is None:
            return []
        masks = gt['inst'] == iid
        masks[~gt['valid'].astype(bool)] = False
        return [dict(instance_id=str(iid), masks=masks)]

    class S(Session):
        def __init__(self):
            super().__init__(ground_lifting, geo, None, instances=lambda name: (), program_version='3.14',
                             multi_instance=True, geometry_mode='sensor', box_provider=MinAreaBoxProvider())

        def _instances(self, name):
            out = []
            for e in socket(name):
                li = lift(name, e['masks'], self.geometry)
                if li['seen']:
                    out.append(dict(li, instance_id=e['instance_id'], first=min(li['frames'])))
            return sorted(out, key=lambda q: (q['first'], q['instance_id']))
    s = S()
    a, b = row['operands']
    s.execute(f'<ground obj="{a}" mode="box">'); s.execute(f'<ground obj="{b}" mode="box">')
    resp = s.execute(f'<gap a="{a}" b="{b}" rule="box_grid_5cm">')
    import re
    m = re.fullmatch(r'distance ([0-9]+\.[0-9]{2}) m', resp)
    return (float(m[1]), None) if m else (None, resp)


fits = json.load(open(H.OUT / 'FITS.json'))
cs, cache, inv = H.inventory()
ho = [c for c in cs if c['k1_split'] == SPLIT][k::n]
dest = HERE / ('out_lift_' + SPLIT + '_' + TAG)
dest.mkdir(exist_ok=True)
for c in ho:
    if not any(r['type'] == 'object_abs_distance' for r in c['rows']):
        continue
    gt, tw, hw = H.load_capture(c, cache[H.digest(c)], True)
    f = H.features(c, tw, gt, hw, 'specified')
    sv = H.scales(f, fits)
    rows = []
    for s in ('S4', 'SO'):
        arm = s + '+G1'
        if not np.isfinite(sv[s]):
            continue
        try:
            geo = H.geometry_npz(c, tw, hw, f['gravity']['G1'], sv[s], arm)
        except ValueError as exc:
            code = type(exc).__name__ + ':' + str(exc)
            for row in c['rows']:
                if row['type'] == 'object_abs_distance':
                    for name in ('dep',) + tuple(q for q in LIFTS if not ONLY or q in ONLY):
                        rows.append(H.item(c, row, arm + '+' + name, (None, code)))
            continue
        cache_l = {}
        for row in c['rows']:
            if row['type'] != 'object_abs_distance':
                continue
            rows.append(H.item(c, row, arm + '+dep', H.attempt(lambda: H.distance(row, geo, gt, 'predicted', cache_l))))
            for name, fn in LIFTS.items():
                if ONLY and name not in ONLY:
                    continue
                rows.append(H.item(c, row, arm + '+' + name, H.attempt(lambda: reader_distance(row, geo, gt, fn))))
    H.dump(dest / (c['canonical'].replace('/', '__') + '.json'), dict(scales={k: sv[k] for k in ('S4', 'SO')}, items=rows))
    print(c['canonical'], len(rows), flush=True)
print('SHARD_DONE', flush=True)
