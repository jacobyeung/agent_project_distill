"""Lane sb_countdesign, CPU pilot on K1: training-free price of fixed-math counting from SAM 3 per-frame proposals (teacher pass, floor 0.2, cap 10)
and G3T x own-scale geometry. Truth T = distinct GT instances of the name visible (>= 20 px at the 320x240 raster) in >= 1 of the 32 anchors.
Estimators: per-frame maximum; greedy 3D merge (the tree's merge3d rule with a radius parameter); scale-free merge; identity oracles.
Run: /scratch/jjyeung/envs/planner_local_v1/bin/python k1_price.py   (writes K1_PRICE.json)"""
import json, gzip, collections, itertools, sys
import numpy as np
pairs = json.load(gzip.open('K1_PAIRS.json.gz'))
meta = json.load(open('K1_LIFT_META.json')); A = np.load('K1_LIFT.npz')['rows']
capix = {c['capture']: i for i, c in enumerate(meta['captures'])}; nameix = {n: i for i, n in enumerate(meta['names'])}
key = A[:, 0].astype(np.int64) * 100000 + A[:, 1].astype(np.int64)
order = np.lexsort((A[:, 3], A[:, 2], key)); A = A[order]; key = key[order]
uk, start = np.unique(key, return_index=True); end = list(start[1:]) + [len(key)]
rows_of = {int(k): (int(s), int(e)) for k, s, e in zip(uk, start, end)}
THETA = [0.5 + 0.05 * i for i in range(10)]
def mra(p, g):
    rel = abs(float(p) - g) / g
    return sum(1.0 for t in THETA if rel <= 1 - t) / 10.0
def tbin(T): return str(T) if T <= 4 else '5+'
P = []
for p in pairs:
    if p['capture'] not in capix or p['T'] < 1: continue
    kk = capix[p['capture']] * 100000 + nameix.get(p['name'], -1)
    s, e = rows_of.get(kk, (0, 0))
    P.append(dict(p=p, a=A[s:e], T=p['T'], split=p['split'], ds=p['capture'].split('/')[0]))
print('pairs priced', len(P), 'T>=5', sum(1 for x in P if x['T'] >= 5), collections.Counter((x['split'], tbin(x['T'])) for x in P))

def nstar(a, t):
    if not len(a): return 0
    m = a[a[:, 4] >= t]
    return int(max(collections.Counter(m[:, 2].astype(int)).values(), default=0))
def greedy(a, t, r, s=1, rel=None, thi=None):
    """merge3d rule: frames in order; a detection joins the nearest cluster whose mean lies within the radius and that holds no
    detection of the same frame; else it starts a cluster. rel: radius = max(r, rel * extent of the detection). Returns clusters."""
    cl = []
    for d in a:
        if d[4] < t: continue
        p = d[12:15].astype(float); k = int(d[2]); ext = float(np.linalg.norm(d[15:18]))
        rad = r if rel is None else max(r, rel * ext)
        best = None
        for c in cl:
            dist = float(np.linalg.norm(c['sum'] / c['n'] - p))
            if dist < rad and k not in c['fr'] and (best is None or dist < best[0]): best = (dist, c)
        if best: c = best[1]; c['sum'] += p; c['n'] += 1; c['fr'].add(k); c['j'] = max(c['j'], float(d[4]))
        else: cl.append(dict(sum=p.copy(), n=1, fr={k}, j=float(d[4])))
    return [c for c in cl if c['n'] >= s or (thi is not None and c['j'] >= thi)]
def oracle_pos(a): return len(set(a[a[:, 6] == 1][:, 7].astype(int))) if len(a) else 0
def oracle_any(a):
    if not len(a): return 0
    m = a[(a[:, 8] == 1) & (a[:, 9] >= 0.25)]
    return len(set(m[:, 7].astype(int)))
EST = {'const2': lambda a: 2, 'oracle_pos_ids': oracle_pos, 'oracle_named_ids_iou25': oracle_any}
for t in (0.2, 0.35, 0.5): EST['nstar_t%.2f' % t] = (lambda a, t=t: nstar(a, t))
for t in (0.2, 0.35, 0.5):
    for r in (0.3, 0.45, 0.6, 0.8, 1.0, 1.5):
        for s in (1, 2):
            EST['merge_t%.2f_r%.2f_s%d' % (t, r, s)] = (lambda a, t=t, r=r, s=s: len(greedy(a, t, r, s)))
    for rel in (0.5, 0.75, 1.0):
        for s in (1, 2):
            EST['relmerge_t%.2f_rel%.2f_s%d' % (t, rel, s)] = (lambda a, t=t, rel=rel, s=s: len(greedy(a, t, 0.3, s, rel=rel)))
    EST['merge_t%.2f_r0.60_s2_or_j0.7' % t] = (lambda a, t=t: len(greedy(a, t, 0.6, 2, thi=0.7)))
    EST['merge_t%.2f_r0.80_s2_or_j0.7' % t] = (lambda a, t=t: len(greedy(a, t, 0.8, 2, thi=0.7)))
res = {}
for name, f in EST.items():
    est = [f(x['a']) for x in P]
    d = {}
    for split in ('train', 'heldout', 'all'):
        for b in ('1', '2', '3', '4', '5+', 'all'):
            ix = [i for i, x in enumerate(P) if (split == 'all' or x['split'] == split) and (b == 'all' or tbin(x['T']) == b)]
            if not ix: continue
            sc = [mra(est[i], P[i]['T']) for i in ix]
            d['%s|%s' % (split, b)] = dict(n=len(ix), mra=round(100 * float(np.mean(sc)), 2),
                                            under=sum(1 for i in ix if est[i] < P[i]['T']), over=sum(1 for i in ix if est[i] > P[i]['T']),
                                            ratio_med=round(float(np.median([est[i] / P[i]['T'] for i in ix])), 2),
                                            ge4=sum(1 for i in ix if est[i] >= 4))
    res[name] = dict(bins=d, est=est)
def bal(d, split): return float(np.mean([d['%s|%s' % (split, b)]['mra'] for b in ('2', '3', '4', '5+')]))
names = sorted(res, key=lambda n: -res[n]['bins']['train|5+']['mra'])
print('\n== top by train 5+ MRA ==')
for n in names[:14]:
    d = res[n]['bins']; print('%-34s' % n, ' '.join('%s %.1f' % (b, d['train|' + b]['mra']) for b in ('1', '2', '3', '4', '5+')), '| heldout', ' '.join('%s %.1f' % (b, d['heldout|' + b]['mra']) for b in ('1', '2', '3', '4', '5+')))
print('\n== top by train balanced (2,3,4,5+) ==')
names2 = sorted(res, key=lambda n: -bal(res[n]['bins'], 'train'))
for n in names2[:14]:
    d = res[n]['bins']; print('%-34s bal %.1f' % (n, bal(d, 'train')), ' '.join('%s %.1f' % (b, d['train|' + b]['mra']) for b in ('1', '2', '3', '4', '5+')), '| heldout bal %.1f' % bal(d, 'heldout'), ' '.join('%s %.1f' % (b, d['heldout|' + b]['mra']) for b in ('1', '2', '3', '4', '5+')))
print('\n== references ==')
for n in ('const2', 'oracle_pos_ids', 'oracle_named_ids_iou25', 'nstar_t0.20', 'nstar_t0.35', 'nstar_t0.50', 'merge_t0.20_r1.50_s1', 'merge_t0.50_r1.50_s1'):
    d = res[n]['bins']; print('%-34s' % n, ' '.join('%s %.1f' % (b, d['all|' + b]['mra']) for b in ('1', '2', '3', '4', '5+')), '| 5+ under/over %d/%d ratio %.2f' % (d['all|5+']['under'], d['all|5+']['over'], d['all|5+']['ratio_med']))
json.dump(dict(n_pairs=len(P), pairs=[dict(capture=x['p']['capture'], name=x['p']['name'], T=x['T'], split=x['split']) for x in P],
               results={n: dict(bins=res[n]['bins'], est=[int(v) for v in res[n]['est']]) for n in res}), open('K1_PRICE.json', 'w'))
