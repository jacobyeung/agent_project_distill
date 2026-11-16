"""Independent numpy lifting on real GT vs the module through ground_rows' production GT path."""
import json, sys, math
import numpy as np
sys.path.insert(0, '/scratch/jjyeung/orch_cd/ground_rows/work/derivgen')
from derivgen import ground_v312_io as io
from derivgen.ground_v312 import load_backend
from derivgen.calculator import PrintedPointRegistry
programs, MaskGround, Scene = io.reference('/scratch/jjyeung/orch_cd/mdg_next/work/rkit')
import os
backend = load_backend(os.environ.get('BACKEND', str(__import__('pathlib').Path(__file__).resolve().parents[1] / 'student_pilot/ground_lifting.py')))
M = json.load(open('/scratch/jjyeung/orch_cd/ground_rows/work/inputs/routing356_scenes.json'))
STRUCT = ('wall','floor','ceiling','object','remove','REMOVE','split')
from pathlib import Path
selected_scenes = [s for s in M if M[s]['canonical'].startswith('scannet/')][:1] + [s for s in M if M[s]['canonical'].startswith('scannetppv2/')][:2]
missing = [M[s]['gt']['path'] for s in selected_scenes if not Path(M[s]['gt']['path']).exists()]
if missing:
    print(json.dumps(dict(status='PENDING-INPUT', paths=missing)))
    raise SystemExit(2)


def erode(m):
    p = np.pad(m, 1, constant_values=False); out = np.ones_like(m)
    H, W = m.shape
    for dy in range(3):
        for dx in range(3): out &= p[dy:dy+H, dx:dx+W]
    return out

def my_lift(z, k, mask):
    H, W = z['depth'].shape[1:]
    D = z['depth'][k-1].astype(float); K = z['K_frames'][k-1]; Ki = np.linalg.inv(K)
    r, c = np.nonzero(erode(mask)); h, w = mask.shape
    u = (c+.5)/w*1000; v = (r+.5)/h*1000
    keep = (u>=20)&(u<=980)&(v>=20)&(v<=980); u, v = u[keep], v[keep]
    def pix(uu, vv):
        return (np.clip((uu/1000*W).astype(int),0,W-1), np.clip((vv/1000*H).astype(int),0,H-1))
    x, y = pix(u, v); d = D[y, x]
    off = np.linspace(-10,10,5)
    dx, dy = np.meshgrid(off, off, indexing='ij'); dx, dy = dx.ravel(), dy.ravel()
    px_, py_ = pix(np.clip(u[:,None]+dx[None],0,999.9).ravel(), np.clip(v[:,None]+dy[None],0,999.9).ravel())
    patch = D[py_, px_].reshape(len(u), 25)
    patch[patch<=0] = np.nan
    with np.errstate(all='ignore'):
        p20, p50, p80 = (np.nanpercentile(patch, q, axis=1) for q in (20,50,80))
    spread = (p80-p20)/np.maximum(p50,1e-3)
    ray = np.stack([x+.5, y+.5, np.ones(len(x))],1) @ Ki.T
    Pc = ray*d[:,None]
    T = z['c2w'][k-1]; Pw = Pc @ T[:3,:3].T + T[:3,3]
    edge = np.minimum(np.minimum(u,1000-u), np.minimum(v,1000-v))
    ok = (d>0)&np.isfinite(spread)&(spread <= np.where(edge<=40,.10,.25))&(Pc[:,2]>0)
    return Pw[ok], Pc[ok], spread[ok]

def level(z):
    R1, t1 = z['c2w'][0][:3,:3], z['c2w'][0][:3,3]
    hd = R1[:,2].copy(); hd[2] = 0; hd /= np.linalg.norm(hd)
    up = np.array([0,0,1.]); right = np.array([hd[1], -hd[0], 0.])  # heading x up, written out
    return right, up, hd, t1

def min_rect(xy):
    from scipy.spatial import ConvexHull
    hull = xy[ConvexHull(xy).vertices]; best = None
    for i in range(len(hull)):
        e = hull[(i+1)%len(hull)]-hull[i]; n = np.linalg.norm(e)
        if n < 1e-9: continue
        e = e/n; f = np.array([-e[1], e[0]])
        a, b = xy@e, xy@f; ext = (a.max()-a.min(), b.max()-b.min())
        if best is None or ext[0]*ext[1] < best[0]: best = (ext[0]*ext[1], ext)
    return best[1]

def brute_gap(A, B):
    best = np.inf
    for i in range(0, len(A), 2000):
        d = np.sqrt(((A[i:i+2000,None,:]-B[None,:,:])**2).sum(-1)).min(); best = min(best, d)
    return best

def mine(z, masks, prob):
    right, up, hd, t1 = level(z)
    frames, areas, pts = [], {}, {}
    for k in range(1, 33):
        if prob[k-1] < .5 or not masks[k-1].any() or not z['valid'][k-1]: continue
        areas[k] = masks[k-1].mean()
        Pw, Pc, s = my_lift(z, k, masks[k-1])
        if len(Pw): frames.append(k); pts[k] = (Pw, s)
    if not frames: return None
    best = sorted(frames, key=lambda k: (-areas[k], k))[0]
    Pw, s = pts[best]
    Wl = np.stack([(Pw-t1)@right, (Pw-t1)@hd, (Pw-t1)@up], 1)    # frame-1 level world (x right, y heading, z up)
    c = np.median(Wl, 0)
    cn = t1 + c[0]*right + c[1]*hd + c[2]*up                     # back to native world
    T = z['c2w'][best-1]; cam = T[:3,:3].T @ (cn - T[:3,3]); cam[1] *= -1
    f1 = np.array([c[0], c[2], c[1]])
    ext = sorted(min_rect(Wl[:, :2]), reverse=True)
    z0, z1 = np.percentile(Wl[:,2], (2, 98))
    return dict(frames=frames, best=best, camera=cam, f1=f1, size=[*ext, max(z1-z0,.02)], spread=float(np.median(s)),
                pts={k: np.stack([(P-t1)@right, (P-t1)@hd, (P-t1)@up],1) for k, (P, _) in pts.items()}, areas=areas,
                visible=sorted(areas))

def fmt(x): t = f'{x:.2f}'; return '0.00' if t == '-0.00' else t
out = []
scenes = [s for s in M if M[s]['canonical'].startswith('scannet/')][:1] + [s for s in M if M[s]['canonical'].startswith('scannetppv2/')][:2]
for s in scenes:
    e = M[s]; z = dict(np.load(e['gt']['path'], allow_pickle=False))
    clip = io.GTClip(e['gt']['path'], e['frame_indices'], programs, MaskGround)
    labels = [str(l) for l in z['labels']]
    cands = [(int((z['inst']==i).sum()), int(i), l) for i, l in zip(z['ids'], labels)
             if labels.count(l) == 1 and not any(w in l.lower() for w in ('wall','floor','ceiling','remove','object'))]
    cands = sorted(cands, reverse=True)[:2]
    res = {}
    for area, iid, name in cands:
        if len(set(programs.T.match_labels(name, clip.geo.labels))) != 1 or sum(l in programs.T.match_labels(name, clip.geo.labels) for l in clip.geo.labels) != 1:
            print('skip multi-match', name); continue
        masks, prob = clip.masks(name)
        mod = backend.lift_object(name, masks, prob, clip.geo, tau=.5)
        text = backend.render_ground(mod, PrintedPointRegistry())
        my = mine(z, masks, prob)
        res[name] = (mod, my)
        # obb half/full: GT points of this instance over all valid frames along obb axes
        allP = []
        for k in range(1,33):
            if not z['valid'][k-1]: continue
            yy, xx = np.nonzero(z['inst'][k-1]==iid); d = z['depth'][k-1][yy, xx].astype(float); g = d>0
            Pc = (np.stack([xx[g]+.5, yy[g]+.5, np.ones(g.sum())],1) @ np.linalg.inv(z['K_frames'][k-1]).T)*d[g,None]
            T = z['c2w'][k-1]; allP.append(Pc@T[:3,:3].T+T[:3,3])
        allP = np.concatenate(allP); j = list(z['ids']).index(iid)
        ax = np.asarray(z['obb_axes'][j]).reshape(3,3); q = (allP - z['obb_centroid'][j]) @ ax.T
        ext = np.percentile(q, 99, 0) - np.percentile(q, 1, 0)
        out.append(dict(scene=s, canonical=e['canonical'], name=name, module_text=text,
            module=dict(frames=mod['frames'], best=mod.get('best'), camera=mod.get('camera'), f1=mod.get('f1'), size=mod.get('size'), spread=mod.get('spread')),
            mine=None if my is None else dict(frames=my['frames'], best=my['best'], camera=my['camera'].tolist(), f1=my['f1'].tolist(), size=my['size'], spread=my['spread']),
            mine_text=None if my is None else f"cam{my['best']} ({', '.join(map(fmt,my['camera']))}) m; f1 ({', '.join(map(fmt,my['f1']))}) m; spread {fmt(my['spread'])} | size {' x '.join(map(fmt,my['size']))} m",
            K_frame_differs_from_K=bool(not np.allclose(z['K_frames'][(my or {'best':1})['best']-1], z['K'])),
            obb_lengths=np.asarray(z['obb_lengths'][j]).round(3).tolist(), gt_point_extent_on_obb_axes_p1_p99=ext.round(3).tolist()))
    names = list(res)
    if len(names) == 2:
        a, b = res[names[0]][0], res[names[1]][0]
        audit = []
        g = backend.gap_objects(a, b, audit=audit)
        ma, mb = res[names[0]][1], res[names[1]][1]
        common = sorted(set(ma['visible']) & set(mb['visible']), key=lambda k: (-min(ma['areas'][k], mb['areas'][k]), k))
        pairs = [(k,k) for k in common] + sorted([(i,j) for i in ma['visible'] for j in mb['visible'] if (i,j) not in {(k,k) for k in common}], key=lambda p:(abs(p[0]-p[1]),*p))
        mg = None
        for i, j in pairs:
            if i in ma['pts'] and j in mb['pts']: mg = (brute_gap(ma['pts'][i], mb['pts'][j]), [i, j]); break
        out.append(dict(scene=s, gap=[names[0], names[1]], module=g, module_frames=audit[0]['frames'] if audit else None,
                        mine=None if mg is None else mg[0], mine_frames=None if mg is None else mg[1]))
print(json.dumps(out, indent=1, default=float))
bad = []
for r in out:
    if 'gap' in r:
        if r['module'] is None or r['mine'] is None or abs(r['module']-r['mine']) > 1e-6 or r['module_frames'] != r['mine_frames']: bad.append(('gap', r['scene']))
    else:
        lines = r['module_text'].split('\n')
        expected_first = r['name'] + ': frames ' + ','.join(map(str, r['mine']['frames'])) + f" (best {r['mine']['best']})" if r['mine'] is not None else None
        if lines[0] != expected_first: bad.append(('first_line', r['scene']))
        if r['mine'] is None or len(lines) != 3 or r['module']['frames'] != r['mine']['frames'] or r['module']['best'] != r['mine']['best'] \
           or lines[1].split(': ',1)[1] != r['mine_text'].split(' | ')[0] or lines[2] != r['mine_text'].split(' | ')[1]:
            bad.append((r['name'], r['scene']))
print('HANDCHECK', 'PASS' if not bad else 'FAIL', bad, file=sys.stderr)

if bad:
    raise SystemExit(1)
assert len(out) == 9, 'Expected six real objects and three gaps'
