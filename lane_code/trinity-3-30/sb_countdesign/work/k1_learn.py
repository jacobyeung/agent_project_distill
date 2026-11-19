"""Lane sb_countdesign, CPU pilot on K1: (1) fixed-math estimators by dataset; (2) a learned count from tool statistics
(gradient boosting on per-(capture,name) summaries of SAM 3 proposals and 3D merges), fitted on K1 train, read on K1 held-out.
Run: /scratch/jjyeung/envs/planner_local_v1/bin/python k1_learn.py"""
import json, gzip, collections
import numpy as np
exec(open('k1_price.py').read().split("EST = {")[0])   # loaders, P, mra, tbin, nstar, greedy, oracles
def feats(a):
    f = []
    for t in (0.2, 0.35, 0.5, 0.7):
        m = a[a[:, 4] >= t] if len(a) else a
        per = collections.Counter(m[:, 2].astype(int)) if len(m) else {}
        v = sorted(per.values(), reverse=True) + [0] * 3
        f += [len(m), len(per), v[0], v[1], v[2], (np.mean(list(per.values())) if per else 0.0)]
    for t in (0.35, 0.5):
        for r in (0.3, 0.6, 1.0, 1.5):
            cl = greedy(a, t, r, 1) if len(a) else []
            f += [len(cl), sum(1 for c in cl if c['n'] >= 2), sum(1 for c in cl if c['n'] >= 3)]
    if len(a):
        f += [float(a[:, 4].max()), float(a[:, 4].mean()), float(np.median(np.linalg.norm(a[:, 15:18], axis=1))), float(np.median(a[:, 18])), float(np.median(a[:, 11]))]
    else: f += [0, 0, 0, 0, 0]
    return f
X = np.array([feats(x['a']) for x in P], float); y = np.array([x['T'] for x in P], float)
tr = np.array([x['split'] == 'train' for x in P]); he = ~tr
ds = np.array([x['ds'] for x in P])
print('X', X.shape, 'train', tr.sum(), 'heldout', he.sum())
from sklearn.ensemble import GradientBoostingRegressor
def report(tag, est, mask):
    out = []
    for b in ('1', '2', '3', '4', '5+', 'all'):
        ix = [i for i in np.flatnonzero(mask) if b == 'all' or tbin(P[i]['T']) == b]
        out.append('%s %.1f (n %d)' % (b, 100 * np.mean([mra(est[i], P[i]['T']) for i in ix]), len(ix)))
    print('%-30s' % tag, ' | '.join(out))
res = {}
for loss, name in (('squared_error', 'gbr_logT'), ('absolute_error', 'gbr_logT_l1')):
    g = GradientBoostingRegressor(loss=loss, n_estimators=300, max_depth=3, learning_rate=0.05, subsample=0.8, random_state=0)
    g.fit(X[tr], np.log(y[tr]))
    est = np.maximum(1, np.rint(np.exp(g.predict(X)))).astype(int)
    res[name] = est
    report(name + ' train', est, tr); report(name + ' heldout', est, he)
# fit with weights that favour large sets (inverse bin frequency)
w = np.array([1.0 / sum(1 for x in P if x['split'] == 'train' and tbin(x['T']) == tbin(p['T'])) for p in P])
g = GradientBoostingRegressor(n_estimators=300, max_depth=3, learning_rate=0.05, subsample=0.8, random_state=0)
g.fit(X[tr], np.log(y[tr]), sample_weight=w[tr]); est = np.maximum(1, np.rint(np.exp(g.predict(X)))).astype(int); res['gbr_logT_balanced'] = est
report('gbr_balanced train', est, tr); report('gbr_balanced heldout', est, he)
# room-grouped cross-validation on train+heldout for a tighter 5+ estimate (grouped by capture)
caps = np.array([x['p']['capture'] for x in P]); ucap = sorted(set(caps)); rng = np.random.default_rng(20261119); perm = rng.permutation(len(ucap)); fold = {ucap[j]: i % 5 for i, j in enumerate(perm)}
cv = np.zeros(len(P), int)
for f in range(5):
    te = np.array([fold[c] == f for c in caps])
    g = GradientBoostingRegressor(n_estimators=300, max_depth=3, learning_rate=0.05, subsample=0.8, random_state=0)
    g.fit(X[~te], np.log(y[~te]), sample_weight=w[~te]); cv[te] = np.maximum(1, np.rint(np.exp(g.predict(X[te]))))
res['gbr_balanced_cv5'] = cv
report('gbr_balanced 5-fold capture CV', cv, np.ones(len(P), bool))
for d in ('arkitscenes', 'scannet', 'scannetpp'):
    report('  cv5 ' + d, cv, ds == d)
# fixed-math references by dataset
ref = {'nstar_t0.50': [nstar(x['a'], 0.5) for x in P], 'nstar_t0.35': [nstar(x['a'], 0.35) for x in P],
       'merge_t0.50_r1.50_s2': [len(greedy(x['a'], 0.5, 1.5, 2)) for x in P], 'oracle_named_ids_iou25': [oracle_any(x['a']) for x in P], 'oracle_pos_ids': [oracle_pos(x['a']) for x in P]}
for n, est in ref.items():
    report(n + ' all', est, np.ones(len(P), bool))
    for d in ('arkitscenes', 'scannet', 'scannetpp'): report('  ' + n + ' ' + d, est, ds == d)
json.dump({k: [int(v) for v in e] for k, e in {**res, **ref}.items()}, open('K1_LEARN_EST.json', 'w'))
imp = sorted(zip(g.feature_importances_, range(X.shape[1])), reverse=True)[:8]; print('top features (index)', [(round(a, 3), b) for a, b in imp])
