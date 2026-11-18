"""Pseudo-reads scored through the executable's own statistics path (pooled_harm_rule_v2.decide: random.Random seed
20261118, 10,000 accepted draws, rejection of draws missing a type, unrounded bounds), to compare with the archived
pr_sim.py figures (NumPy generator, no rejection).  Pseudo-reads come from pr_sim.py's generator (D0 m200 pairs; whole
rooms drawn with replacement inside each set, arms exchanged per drawn room; flips set a later-arm item to 0 with
probability L / mean score).  Scenarios: unchanged model (exchange), (a) size loss dev-S1 -9.5 and R0-dev -4.3 (flips),
(c) uniform -2 on every type (flips).  usage: sim_exec.py SEED OUTER OUT.npz [null]  (null: the unchanged model only)"""
import sys
import numpy as np
import pooled_harm_rule_v2 as RULE
SEED, OUT = int(sys.argv[1]), int(sys.argv[2])
NULL_ONLY = len(sys.argv) > 4 and sys.argv[4] == 'null'
Z = np.load('PAIRS.npz')
gen = np.random.default_rng(SEED)
LOSS = (0.095, 0.02, 0.043)


def prep(ds, local):
    ty = np.array([local.index(t) for t in Z[ds + '_type']])
    room_ix, sa, sb = Z[ds + '_room'], Z[ds + '_score'][:, 0], Z[ds + '_score'][:, 1]
    K = int(room_ix.max()) + 1
    items = [np.flatnonzero(room_ix == k) for k in range(K)]
    pm = np.array([(sa[ty == t].mean() + sb[ty == t].mean()) / 2 for t in range(7)])
    return dict(ty=ty, sa=sa, sb=sb, K=K, items=items, sizes=np.array([len(x) for x in items]), pm=pm)


SET_S, SET_R = prep('S', [0, 1, 2, 3, 4, 5, 6]), prep('R', [0, 1, 2, 3, 4, 5, 7])


def pseudo(D):
    """pr_sim.py pseudo(): sums (4,K,7) for [exchange, flips 9.5, flips 2, flips 4.3] and item counts (K,7)."""
    K = D['K']
    pick = gen.integers(0, K, size=K)
    swap = gen.random(K) < 0.5
    idx = np.concatenate([D['items'][r] for r in pick])
    cl = np.repeat(np.arange(K), D['sizes'][pick])
    t = D['ty'][idx]
    x = np.where(swap[cl], D['sb'][idx], D['sa'][idx])
    y = np.where(swap[cl], D['sa'][idx], D['sb'][idx])
    u = gen.random(len(idx))
    key = cl * 7 + t
    agg = lambda w: np.bincount(key, weights=w, minlength=K * 7).reshape(K, 7)
    return np.stack([agg(y - x)] + [agg(np.where(u < L / D['pm'][t], 0.0, y) - x) for L in LOSS], 0), agg(np.ones(len(idx)))


def data(sS, nS, sR, nR):
    mk = lambda s, n, types: dict(S=s, N=n, SZ=np.zeros((len(n), 2)), NZ=np.ones((len(n), 2)), K=len(n), types=types,
                                  base_pct=[0.0] * 7, rooms_per_type=[int((n[:, k] > 0).sum()) for k in range(7)])
    return dict(S=mk(sS, nS, tuple(RULE.N_ITEMS['S'])), R=mk(sR, nR, tuple(RULE.N_ITEMS['R'])))


res = np.zeros((OUT, 3, 2, 3), dtype=bool)        # pseudo-read, scenario, look (200, later), (stop, H1, H2)
red = np.zeros((OUT, 3), dtype=int)
for o in range(OUT):
    sS, nS = pseudo(SET_S)
    sR, nR = pseudo(SET_R)
    a_S, a_R = sS[0].copy(), sR[0].copy()
    a_S[:, 5], a_R[:, 5] = sS[1][:, 5], sR[3][:, 5]
    for c, (x, y) in enumerate(((sS[0], sR[0]), (a_S, a_R), (sS[2], sR[2]))[:1 if NULL_ONLY else 3]):
        for l, step in enumerate((200, 400)):
            d = RULE.decide(data(x, nS, y, nR), step)
            res[o, c, l] = (d['stop'], bool(d['H1']), d['H2'])
            red[o, c] = d['redrawn']
np.savez(sys.argv[3], res=res, redrawn=red)
print('done', SEED, OUT)
