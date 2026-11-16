"""Aggregate per-capture JSON into arm tables: mean MRA x100, room-bootstrap 95% CI, paired diffs."""
import sys, json, glob, collections, numpy as np
src, split = sys.argv[1], sys.argv[2]
fits = json.load(open(sys.argv[3])) if len(sys.argv) > 3 and sys.argv[3] != '-' else None
refs = sys.argv[4].split(',') if len(sys.argv) > 4 else ['S1+G1']
rows = []
for p in sorted(glob.glob(src + '/*.json')):
    d = json.load(open(p))
    rows += [r for r in d.get('items', []) if r['split'] == split] if isinstance(d, dict) else []


def mra(pred, gt):
    if pred is None:
        return 0.
    return float(np.mean([abs(pred - gt) / abs(gt) < 1 - t for t in np.arange(.5, .96, .05)]))


if fits and fits.get('R2'):
    extra = []
    for r in rows:
        if r['type'] == 'room_size_estimation' and r['arm'].endswith('+R0') and not r['arm'].startswith('GT+'):
            k = (fits['R2'].get(r['arm'][:-3]) or {}).get('k')
            q = dict(r, arm=r['arm'][:-3] + '+R2')
            q['pred'] = None if (k is None or r['pred'] is None) else r['pred'] * k
            q['mra'] = mra(q['pred'], r['gt'])
            extra.append(q)
    rows += extra
rng = np.random.default_rng(20261116)


def ref_for(a, ref, typ):
    if typ == 'object_abs_distance':
        return ref
    return ref + '+' + a.split('+')[-1]


for typ in ('object_abs_distance', 'room_size_estimation'):
    by = collections.defaultdict(dict)
    for r in rows:
        if r['type'] == typ:
            by[r['arm']][r['row_id']] = r
    if not by:
        continue
    arms = sorted(by)
    base = by[arms[0]]
    clusters = sorted({r['room'] for r in base.values()})
    cidx = {name: i for i, name in enumerate(clusters)}
    ids = sorted(base)
    cl = np.array([cidx[base[i]['room']] for i in ids])
    nc = len(clusters)
    draws = rng.integers(0, nc, size=(10000, nc))
    W = np.stack([np.bincount(d, minlength=nc) for d in draws]).astype(float)
    cnt = np.bincount(cl, minlength=nc)

    def boot(v):
        s = np.bincount(cl, weights=v, minlength=nc)
        m = (W @ s) / (W @ cnt)
        return 100 * v.mean(), 100 * np.percentile(m, 2.5), 100 * np.percentile(m, 97.5)

    print(f'## {typ} split={split} items={len(ids)} rooms={nc} datasets={dict(collections.Counter(base[i]["dataset"] for i in ids))}')
    vals = {a: np.array([by[a][i]['mra'] if i in by[a] else 0. for i in ids]) for a in arms}
    refu = {a: sum(1 for i in ids if i in by[a] and by[a][i]['refusal_code']) for a in arms}
    for a in arms:
        m, lo, hi = boot(vals[a])
        line = f'{a:14s} {m:6.1f} [{lo:5.1f},{hi:5.1f}] ref={refu[a]}'
        for ref in refs:
            rr = ref_for(a, ref, typ)
            if rr in vals and rr != a:
                d, dlo, dhi = boot(vals[a] - vals[rr])
                line += f' | vs {rr}: {d:+5.1f} [{dlo:+5.1f},{dhi:+5.1f}]'
        print(line)
