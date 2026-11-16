import json, sys, collections, numpy as np
rows = [json.loads(l) for l in open('out_devs1/DEVS1_ROOM.jsonl')]
for sub in ('all', 'm2'):
    R = [r for r in rows if 'mra' in r and (sub == 'all' or r['unit'] == 'm2')]
    cl = sorted({r['room'] for r in R}); ci = np.array([cl.index(r['room']) for r in R]); nc = len(cl)
    rng = np.random.default_rng(20261116); W = np.stack([np.bincount(d, minlength=nc) for d in rng.integers(0, nc, (10000, nc))]).astype(float)
    cnt = np.bincount(ci, minlength=nc)
    def boot(v):
        m = (W @ np.bincount(ci, weights=v, minlength=nc)) / (W @ cnt); return 100*v.mean(), 100*np.percentile(m, 2.5), 100*np.percentile(m, 97.5)
    arms = sorted(R[0]['mra'])
    print(f'## dev-S1 room {sub}: items={len(R)} rooms={nc} missing_tower={sum("error" in r for r in rows)}')
    for a in arms:
        v = np.array([r['mra'].get(a, 0.) for r in R]); m, lo, hi = boot(v)
        ref = a.replace(a.split('+')[0], 'S1', 1); extra = ''
        if ref != a:
            d = boot(v - np.array([r['mra'].get(ref, 0.) for r in R])); extra = f' vs {ref}: {d[0]:+.1f} [{d[1]:+.1f},{d[2]:+.1f}]'
        print(f'{a:14s} {m:5.1f} [{lo:5.1f},{hi:5.1f}]{extra}')
