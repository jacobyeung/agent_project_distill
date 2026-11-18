"""Family-wise false-stop probability over successive looks of one leg, for the pooled rule and the card's dev-S1 rule.
Null: the four real reads of each item (step 544, D0 m100, D0 m200, H1-1 m100) are exchangeable.  One pseudo-leg draws
whole rooms with replacement inside each set and, inside each drawn room, permutes the four reads at random; the first is
the baseline and the other three are looks 1 to 3 (they share the baseline and the items, as R1's looks will).
Each look is scored with the rule's own interval (INN joint draws).  usage: pr_looks.py SEED OUTER INNER"""
import sys, json
import numpy as np
SEED, OUT, INN = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3])
Z = np.load('PAIRS.npz')
rng = np.random.default_rng(SEED)
LEV = np.array([1 - 0.025 / 8, 1 - 0.025 / 32])
SLEV = np.array([1 - 0.025 / 7, 1 - 0.025 / 28])
MLEV = np.array([0.975, 1 - 0.00625])


def prep(ds, local):
    ty = np.array([local.index(t) for t in Z[ds + '_type']])
    rm = Z[ds + '_room']
    K = int(rm.max()) + 1
    items = [np.flatnonzero(rm == k) for k in range(K)]
    return dict(ty=ty, sc=Z[ds + '_score'], K=K, items=items, sizes=np.array([len(x) for x in items]),
                n=np.array([(ty == t).sum() for t in range(7)]))


S = prep('S', [0, 1, 2, 3, 4, 5, 6])
R = prep('R', [0, 1, 2, 3, 4, 5, 7])
w = S['n'][:6] / (S['n'][:6] + R['n'][:6])


def counts(k):
    idx = rng.integers(0, k, size=(INN, k))
    idx += np.arange(INN)[:, None] * k
    return np.bincount(idx.ravel(), minlength=INN * k).reshape(INN, k).astype(np.float64)


def pseudo(D):
    K = D['K']
    pick = rng.integers(0, K, size=K)
    perm = np.argsort(rng.random((K, 4)), axis=1)
    idx = np.concatenate([D['items'][r] for r in pick])
    cl = np.repeat(np.arange(K), D['sizes'][pick])
    t = D['ty'][idx]
    X = np.take_along_axis(D['sc'][idx], perm[cl], axis=1)
    key = cl * 7 + t
    Sd = np.stack([np.bincount(key, weights=X[:, j] - X[:, 0], minlength=K * 7).reshape(K, 7) for j in (1, 2, 3)], 0)
    return Sd, np.bincount(key, minlength=K * 7).reshape(K, 7).astype(np.float64)


KS, KR = S['K'], R['K']
ub = np.zeros((OUT, 3, 8, 2))
mub = np.zeros((OUT, 3, 2))
sub = np.zeros((OUT, 3, 7, 2))
smub = np.zeros((OUT, 3, 2))
for o in range(OUT):
    SS, NS = pseudo(S)
    SR, NR = pseudo(R)
    MS, MR = counts(KS), counts(KR)
    DS = (MS @ SS.transpose(1, 0, 2).reshape(KS, 21)).reshape(INN, 3, 7) / (MS @ NS)[:, None, :]
    DR = (MR @ SR.transpose(1, 0, 2).reshape(KR, 21)).reshape(INN, 3, 7) / (MR @ NR)[:, None, :]
    P = np.concatenate([w * DS[:, :, :6] + (1 - w) * DR[:, :, :6], DS[:, :, 6:7], DR[:, :, 6:7]], 2)      # (INN,3,8)
    ub[o] = np.moveaxis(np.quantile(P, LEV, axis=0), 0, -1)
    mub[o] = np.quantile(P.mean(2), MLEV, axis=0).T
    for t in range(7):
        keep = NS[:, t] > 0
        Mt = counts(int(keep.sum()))
        q = (Mt @ SS[:, keep, t].T) / (Mt @ NS[keep, t])[:, None]
        sub[o, :, t, :] = np.quantile(q, SLEV, axis=0).T
    smub[o] = np.quantile(DS.mean(2), MLEV, axis=0).T
np.savez('looks_seed%d.npz' % SEED, ub=ub, mub=mub, sub=sub, smub=smub)
print('done', SEED, OUT, INN)
