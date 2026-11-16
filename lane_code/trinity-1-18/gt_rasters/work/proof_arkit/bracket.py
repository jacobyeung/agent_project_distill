import sys
sys.argv += [] 
exec(open('/scratch/jjyeung/orch_n30/gt_rasters/work/proof_arkit/arkit_test.py').read().split("tot = 0")[0])
lo, hi = -np.inf, np.inf; allz = []
per_box = {}
for f in range(32):
    if not (D[f] > 0).any(): continue
    png = np.array(Image.open(ds[f])); w, h, fx, fy, cx, cy = np.loadtxt(pc[f])
    d = png.astype(np.float64) / 1000.0
    v, u = np.mgrid[0:192, 0:256].astype(np.float64)
    P = (np.stack([(u + .5 - cx) / fx * d, (v + .5 - cy) / fy * d, d, np.ones_like(d)], -1).reshape(-1, 4) @ C[f].astype(np.float64).T)[:, :3]
    allz.append(P[d.reshape(-1) > 0, 2])
    out = np.full(len(P), -1, np.int32)
    for k in np.argsort(vol)[::-1]:
        out[(np.abs((P - cen[k]) @ A[k].T) <= L[k] / 2 + 0.03).all(1)] = k
    out[d.reshape(-1) <= 0] = -1
    a = out.reshape(192, 256)[np.ix_(yi, xi)]; Pz = P[:, 2].reshape(192, 256)[np.ix_(yi, xi)]
    agree_nonfloor = (a >= 0) & (I[f] < 0)
    exc = agree_nonfloor; inc = (a >= 0) & (I[f] >= 0) & (a == I[f])
    if exc.any():
        for k in np.unique(a[exc]):
            m = exc & (a == k); per_box.setdefault(int(k), [-np.inf, np.inf]); per_box[int(k)][0] = max(per_box[int(k)][0], Pz[m].max())
        lo = max(lo, Pz[exc].max())
    if inc.any():
        for k in np.unique(a[inc]):
            m = inc & (a == k); per_box.setdefault(int(k), [-np.inf, np.inf]); per_box[int(k)][1] = min(per_box[int(k)][1], Pz[m].min())
        hi = min(hi, Pz[inc].min())
z = np.concatenate(allz)
print(ID, 'box floor', floor, 'global bracket excluded<=%.5f included>=%.5f' % (lo - floor, hi - floor))
for k, (a_, b_) in sorted(per_box.items()):
    print('  box', k, ann[k]['label'], 'bottom-floor %.4f' % (cen[k, 2] - L[k, 2] / 2 - floor), 'excl max %.4f incl min %.4f' % (a_ - floor, b_ - floor))
for q in [1, 2, 5, 10]: print('  pct', q, '%.4f' % (np.percentile(z, q) - floor))
