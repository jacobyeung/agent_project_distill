"""Lane sb_countdesign: K1 summary table for the record (frozen rules), with capture-bootstrap intervals at truth >= 5 and the share of pairs the
tool would call "large" (estimate >= 4) by truth bin. Run: /scratch/jjyeung/envs/planner_local_v1/bin/python k1_final.py  (writes K1_FINAL.json)"""
import json, gzip, collections
import numpy as np
exec(open('k1_price.py').read().split("EST = {")[0])
N = np.load('K1_NMS.npz')['rows']
keepd = {(int(r[0]), int(r[1]), int(r[2]), int(r[3])): int(r[4]) for r in N}
for x in P: x['keep'] = np.array([bool(keepd[(int(d[0]), int(d[1]), int(d[2]), int(d[3]))]) for d in x['a']], bool) if len(x['a']) else np.zeros(0, bool)
def nmax(a, t):
    m = a[a[:, 4] >= t] if len(a) else a
    return max(collections.Counter(m[:, 2].astype(int)).values(), default=0) if len(m) else 0
L = json.load(open('K1_LMERGE.json')); LE = json.load(open('K1_LEARN_EST.json'))
rules = {'N_max_t0.35_nms (kit primary)': [nmax(x['a'][x['keep']], 0.35) for x in P], 'N_max_t0.50_nms': [nmax(x['a'][x['keep']], 0.5) for x in P], 'N_max_t0.50_raw': [nmax(x['a'], 0.5) for x in P],
         'M_merge3d_1.5m_t0.50 (tree rule, radius 1.5 m)': [len(greedy(x['a'], 0.5, 1.5, 1)) for x in P], 'M_merge3d_1.5m_t0.50_support2': [len(greedy(x['a'], 0.5, 1.5, 2)) for x in P],
         'M_merge3d_0.6m_t0.50_support2': [len(greedy(x['a'], 0.5, 0.6, 2)) for x in P],
         'L_learned_accept_merge_theta0.8_tau0.5': L['theta0.8_tau0.5']['est'], 'C_learned_count_from_summaries_cv5': LE['gbr_balanced_cv5'],
         'O_identity_oracle_iou25': [oracle_any(x['a']) for x in P], 'O_identity_oracle_POS': [oracle_pos(x['a']) for x in P]}
caps = np.array([x['p']['capture'] for x in P]); rng = np.random.default_rng(20261119)
def boot(est, ix):
    sc = np.array([mra(est[i], P[i]['T']) for i in ix]); cp = caps[ix]; u = sorted(set(cp)); groups = [np.flatnonzero(cp == c) for c in u]; vals = []
    for _ in range(4000):
        pick = rng.integers(0, len(groups), len(groups)); s = np.concatenate([groups[g] for g in pick]); vals.append(sc[s].mean())
    return 100 * sc.mean(), 100 * np.percentile(vals, 2.5), 100 * np.percentile(vals, 97.5)
out = {}
for name, est in rules.items():
    d = {}
    for b in ('1', '2', '3', '4', '5+'):
        ix = [i for i, x in enumerate(P) if tbin(x['T']) == b]
        d[b] = dict(n=len(ix), mra=round(100 * float(np.mean([mra(est[i], P[i]['T']) for i in ix])), 1), share_est_ge4=round(float(np.mean([est[i] >= 4 for i in ix])), 3),
                    over=round(float(np.mean([est[i] > P[i]['T'] for i in ix])), 3), under=round(float(np.mean([est[i] < P[i]['T'] for i in ix])), 3))
    for tag, sel in (('all', lambda x: True), ('train', lambda x: x['split'] == 'train'), ('heldout', lambda x: x['split'] == 'heldout'), ('arkitscenes', lambda x: x['ds'] == 'arkitscenes'), ('scannet', lambda x: x['ds'] == 'scannet'), ('scannetpp', lambda x: x['ds'] == 'scannetpp')):
        ix = np.array([i for i, x in enumerate(P) if x['T'] >= 5 and sel(x)])
        m, lo, hi = boot(est, ix); d['5+|' + tag] = dict(n=len(ix), mra=round(m, 1), lo=round(lo, 1), hi=round(hi, 1))
    big = [i for i, x in enumerate(P) if x['T'] >= 5]; d['5+_ratio_med'] = round(float(np.median([est[i] / P[i]['T'] for i in big])), 2)
    out[name] = d
    print('%-48s' % name, ' '.join('%s %.1f' % (b, d[b]['mra']) for b in ('1', '2', '3', '4', '5+')), '| 5+ all %.1f [%.1f, %.1f] train %.1f heldout %.1f [%.1f, %.1f] ark %.1f sn %.1f spp %.1f [%.1f, %.1f]' % (
        d['5+|all']['mra'], d['5+|all']['lo'], d['5+|all']['hi'], d['5+|train']['mra'], d['5+|heldout']['mra'], d['5+|heldout']['lo'], d['5+|heldout']['hi'], d['5+|arkitscenes']['mra'], d['5+|scannet']['mra'], d['5+|scannetpp']['mra'], d['5+|scannetpp']['lo'], d['5+|scannetpp']['hi']),
          '| est>=4 share', ' '.join('%.2f' % d[b]['share_est_ge4'] for b in ('1', '2', '3', '4', '5+')), '| ratio %.2f under %.2f over %.2f' % (d['5+_ratio_med'], d['5+']['under'], d['5+']['over']))
Th = collections.Counter(min(x['T'], 13) for x in P if x['T'] >= 5); print('T hist 5+', sorted(Th.items()))
out['_meta'] = dict(pairs=len(P), captures=len(set(caps)), pairs_5plus=len([1 for x in P if x['T'] >= 5]), captures_5plus=len(set(x['p']['capture'] for x in P if x['T'] >= 5)),
                    by_split={s: sum(1 for x in P if x['T'] >= 5 and x['split'] == s) for s in ('train', 'heldout')}, by_dataset={d: sum(1 for x in P if x['T'] >= 5 and x['ds'] == d) for d in ('arkitscenes', 'scannet', 'scannetpp')},
                    T_median_5plus=float(np.median([x['T'] for x in P if x['T'] >= 5])))
print(out['_meta'])
json.dump(out, open('K1_FINAL.json', 'w'), indent=1)
