import sys, os
sys.path.insert(0, '/scratch/jjyeung/orch_n30/gt_rasters/work/proof_arkit')
from arkit_cr import *
ID, SRC = sys.argv[1], sys.argv[2]
X = float(sys.argv[3]) if len(sys.argv) > 3 else 0.0365
r = np.load(f'/scratch/jjyeung/orch_cd/dose_pool/out/arkit_gt/gt/{ID}.npz')
D, I, Kr, C = r['depth'], r['inst'], r['K'], r['c2w']
ds = sorted(glob.glob(f'{SRC}/{ID}_frames/lowres_depth/*.png'), key=ts)
pc = sorted(glob.glob(f'{SRC}/{ID}_frames/lowres_wide_intrinsics/*.pincam'), key=ts)
T, AA, TT = load_traj(f'{SRC}/{ID}_frames/lowres_wide.traj')
ann = json.load(open(f'{SRC}/{ID}_3dod_annotation.json'))['data']
cen = np.array([o['segments']['obbAligned']['centroid'] for o in ann]); L = np.array([o['segments']['obbAligned']['axesLengths'] for o in ann])
A = np.array([o['segments']['obbAligned']['normalizedAxes'] for o in ann]).reshape(-1, 3, 3)
print('labels eq', [o['label'] for o in ann] == r['labels'].tolist(), 'cen eq', np.array_equal(cen, r['obb_centroid']), np.array_equal(L, r['obb_lengths']), np.array_equal(A.reshape(-1, 9), r['obb_axes']))
floor = (cen[:, 2] - L[:, 2] / 2).min(); vol = np.prod(L, 1)
yi = np.floor(np.arange(240) * 192 / 240).astype(int); xi = np.floor(np.arange(320) * 256 / 320).astype(int)
tot = 0
for f in range(32):
    png = np.array(Image.open(ds[f])); w, h, fx, fy, cx, cy = np.loadtxt(pc[f])
    i = np.argmin(np.abs(T - ts(ds[f]))); dt = T[i] - ts(ds[f])
    c = c2w_of(AA[i], TT[i], 'scipy')
    dep = (png[np.ix_(yi, xi)] / 1000.0).astype(np.float32)
    K = np.diag([1.25, 1.25, 1]) @ np.array([[fx, 0, cx], [0, fy, cy], [0, 0, 1]])
    d = png.astype(np.float64) / 1000.0
    v, u = np.mgrid[0:192, 0:256].astype(np.float64)
    P = np.stack([(u + .5 - cx) / fx * d, (v + .5 - cy) / fy * d, d, np.ones_like(d)], -1).reshape(-1, 4) @ C[f].astype(np.float64).T
    P = P[:, :3]
    out = np.full(len(P), -1, np.int32)
    for k in np.argsort(vol)[::-1]:
        out[(np.abs((P - cen[k]) @ A[k].T) <= L[k] / 2 + 0.03).all(1)] = k
    out[P[:, 2] < floor + X] = -1; out[d.reshape(-1) <= 0] = -1
    inst = out.reshape(192, 256)[np.ix_(yi, xi)]
    zero = not (D[f] > 0).any()
    if zero: inst[:] = -1; dep[:] = 0
    mis = int((inst != I[f]).sum()); tot += mis
    print(f, 'dt %+.5f' % dt, 'zero' if zero else '', 'depth_eq', np.array_equal(dep, D[f]), 'c2w_eq', np.array_equal(c.astype(np.float32), C[f]),
          'K_eq', np.array_equal(K, r['K_frames'][f]), 'inst_mis', mis)
print('total inst mismatches', tot, 'K==K_frames[0]', np.array_equal(Kr, r['K_frames'][0]))
