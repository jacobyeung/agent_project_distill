"""Double bootstrap for the pooled harm rule of leg R1 (method of card_fix a3_power.py / a3_power2.py, both sets).
Noise model: paired items of a later read (default D0 m200) against step 544 on dev-S1 (main) and R0-dev (a7).
Outer loop: one pseudo-read = whole rooms drawn with replacement inside each set (72 dev-S1, 98 R0-dev).
  cnull  centred: the observed paired differences minus their set-and-type mean (true difference 0, D0's own noise);
  xnull  exchange: the two arms exchanged inside each drawn room with probability 1/2 (true difference 0);
  f95, f2, f43  on the exchange null, each later-arm item score set to 0 with probability L/(100 x mean score), L = 9.5, 2, 4.3.
Inner loop: the rule's own interval on each pseudo-read, INN joint draws (rooms resampled inside each set), np.quantile linear.
usage: pr_sim.py SEED OUTER INNER [ARM]"""
import sys, json
import numpy as np
SEED, OUT, INN = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3])
ARM = sys.argv[4] if len(sys.argv) > 4 else 'D0m200'
Z = np.load('PAIRS.npz')
META = json.load(open('PAIRS_META.json'))
a = META['arms'].index(ARM)
rng = np.random.default_rng(SEED)
LEV = np.array([1 - 0.025 / 8, 1 - 0.025 / 32, 1 - 0.025 / 7, 1 - 0.025 / 28, 0.975])
MLEV = np.array([0.975, 1 - 0.00625])
SLEV = np.array([1 - 0.025 / 7, 1 - 0.025 / 28, 0.975])
LOSS = (0.095, 0.02, 0.043)


def prep(ds, local):
    ty = np.array([local.index(t) for t in Z[ds + '_type']])
    rm = Z[ds + '_room']
    sa = Z[ds + '_score'][:, 0]
    sb = Z[ds + '_score'][:, a]
    K = int(rm.max()) + 1
    items = [np.flatnonzero(rm == k) for k in range(K)]
    sizes = np.array([len(x) for x in items])
    delta = np.array([(sb - sa)[ty == t].mean() for t in range(7)])
    pm = np.array([(sa[ty == t].mean() + sb[ty == t].mean()) / 2 for t in range(7)])
    return dict(ty=ty, sa=sa, sb=sb, K=K, items=items, sizes=sizes, delta=delta, pm=pm,
                n=np.array([(ty == t).sum() for t in range(7)]))


# global type order: 0-5 shared, 6 route planning (dev-S1 only), 7 appearance order (R0-dev only)
S = prep('S', [0, 1, 2, 3, 4, 5, 6])
R = prep('R', [0, 1, 2, 3, 4, 5, 7])
W = {'item': S['n'][:6] / (S['n'][:6] + R['n'][:6]), 'equal': np.full(6, 0.5)}


def counts(k):
    idx = rng.integers(0, k, size=(INN, k))
    idx += np.arange(INN)[:, None] * k
    return np.bincount(idx.ravel(), minlength=INN * k).reshape(INN, k).astype(np.float64)


def pseudo(D):
    K = D['K']
    pick = rng.integers(0, K, size=K)
    swap = rng.random(K) < 0.5
    idx = np.concatenate([D['items'][r] for r in pick])
    cl = np.repeat(np.arange(K), D['sizes'][pick])
    t = D['ty'][idx]
    sa = D['sa'][idx]
    sb = D['sb'][idx]
    x = np.where(swap[cl], sb, sa)
    y = np.where(swap[cl], sa, sb)
    u = rng.random(len(idx))
    key = cl * 7 + t

    def agg(w):
        return np.bincount(key, weights=w, minlength=K * 7).reshape(K, 7)

    sc = [agg(sb - sa - D['delta'][t]), agg(y - x)] + [agg(np.where(u < L / D['pm'][t], 0.0, y) - x) for L in LOSS]
    return np.stack(sc, 0), agg(np.ones(len(idx)))            # (5,K,7), (K,7)


COMBO = ((0, 0), (1, 1), (2, 2), (2, 1), (1, 2), (3, 3), (2, 4))            # (dev-S1 scenario, R0-dev scenario)


def mean_scen(P):                                            # P: (...,7 combos,8 types) -> (...,24)
    base = P[..., 1, :].sum(-1)
    out = [P[..., 0, :].mean(-1), base / 8]
    out += [(base - P[..., 1, t] + P[..., 2, t]) / 8 for t in range(8)]
    out += [P[..., 5, :].mean(-1), (base - P[..., 1, 5] + P[..., 6, 5]) / 8]
    out += [(base - P[..., 1, t] + P[..., 3, t]) / 8 for t in range(6)]
    out += [(base - P[..., 1, t] + P[..., 4, t]) / 8 for t in range(6)]
    return np.stack(out, -1)


V = ('item', 'equal', 'unstrat')
ub = np.zeros((OUT, 3, 7, 8, 5))
est = np.zeros((OUT, 3, 7, 8))
mub = np.zeros((OUT, 3, 24, 2))
mest = np.zeros((OUT, 3, 24))
sub = np.zeros((OUT, 4, 7, 3))
sest = np.zeros((OUT, 4, 7))
smub = np.zeros((OUT, 10, 2))
smest = np.zeros((OUT, 10))
KS, KR = S['K'], R['K']
for o in range(OUT):
    SS, NS = pseudo(S)
    SR, NR = pseudo(R)
    MS = counts(KS)
    MR = counts(KR)
    dS = MS @ NS
    dR = MR @ NR
    nS = (MS @ SS.transpose(1, 0, 2).reshape(KS, 35)).reshape(INN, 5, 7)
    nR = (MR @ SR.transpose(1, 0, 2).reshape(KR, 35)).reshape(INN, 5, 7)
    DS = nS / dS[:, None, :]
    DR = nR / dR[:, None, :]
    eS = SS.sum(1) / NS.sum(0)
    eR = SR.sum(1) / NR.sum(0)                                # (5,7)
    MU = counts(KS + KR)
    uS = MU[:, :KS]
    uR = MU[:, KS:]
    udS = uS @ NS
    udR = uR @ NR
    unS = (uS @ SS.transpose(1, 0, 2).reshape(KS, 35)).reshape(INN, 5, 7)
    unR = (uR @ SR.transpose(1, 0, 2).reshape(KR, 35)).reshape(INN, 5, 7)
    for v, name in enumerate(V):
        P = np.zeros((INN, 7, 8))
        E = np.zeros((7, 8))
        for c, (i, j) in enumerate(COMBO):
            if name == 'unstrat':
                P[:, c, :6] = (unS[:, i, :6] + unR[:, j, :6]) / (udS[:, :6] + udR[:, :6])
                P[:, c, 6] = unS[:, i, 6] / udS[:, 6]
                P[:, c, 7] = unR[:, j, 6] / udR[:, 6]
                E[c, :6] = (SS[i, :, :6].sum(0) + SR[j, :, :6].sum(0)) / (NS[:, :6].sum(0) + NR[:, :6].sum(0))
            else:
                w = W[name]
                P[:, c, :6] = w * DS[:, i, :6] + (1 - w) * DR[:, j, :6]
                P[:, c, 6] = DS[:, i, 6]
                P[:, c, 7] = DR[:, j, 6]
                E[c, :6] = w * eS[i, :6] + (1 - w) * eR[j, :6]
            E[c, 6] = eS[i, 6]
            E[c, 7] = eR[j, 6]
        ub[o, v] = np.moveaxis(np.quantile(P, LEV, axis=0), 0, -1)
        est[o, v] = E
        mub[o, v] = np.quantile(mean_scen(P), MLEV, axis=0).T
        mest[o, v] = mean_scen(E)
    # the card's dev-S1 rule on the same pseudo-read: per-type interval over the rooms that hold the type, mean of seven jointly
    for t in range(7):
        keep = NS[:, t] > 0
        Mt = counts(int(keep.sum()))
        q = (Mt @ SS[:4][:, keep, t].T) / (Mt @ NS[keep, t])[:, None]
        sub[o, :, t, :] = np.quantile(q, SLEV, axis=0).T
    sest[o] = eS[:4]
    b = DS[:, 1, :].sum(1)
    ms = [DS[:, 0, :].mean(1), b / 7] + [(b - DS[:, 1, t] + DS[:, 2, t]) / 7 for t in range(7)] + [DS[:, 3, :].mean(1)]
    smub[o] = np.quantile(np.stack(ms, 1), MLEV, axis=0).T
    be = eS[1].sum()
    smest[o] = np.array([eS[0].mean(), be / 7] + [(be - eS[1, t] + eS[2, t]) / 7 for t in range(7)] + [eS[3].mean()])
np.savez('sim_%s_seed%d.npz' % (ARM, SEED), ub=ub, est=est, mub=mub, mest=mest, sub=sub, sest=sest, smub=smub, smest=smest,
         W_item=W['item'], pmS=S['pm'], pmR=R['pm'], deltaS=S['delta'], deltaR=R['delta'], INN=INN, KS=KS, KR=KR)
print('done', ARM, SEED, OUT, INN)
