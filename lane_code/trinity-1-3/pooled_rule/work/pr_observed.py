"""The three real later reads (D0 m200, D0 m100, H1-1 m100) against step 544 under the card's dev-S1 rule and under the
pooled rule, with 200,000 bootstrap draws (numpy) to remove the tool's Monte Carlo noise from the comparison; and the
correlation between two looks of one leg (D0 m100 and m200) under one joint room bootstrap."""
import json
import numpy as np
Z = np.load('PAIRS.npz')
META = json.load(open('PAIRS_META.json'))
ARMS = META['arms']
rng = np.random.default_rng(20261118)
REP, CH = 200000, 20000
TS = ('counting', 'direction_easy', 'direction_medium', 'direction_hard', 'rel_distance', 'object_size', 'route_planning')
T8 = TS[:6] + ('route_planning (dev-S1 only)', 'appearance_order (R0-dev only)')


def table(ds, local):
    ty = np.array([local.index(t) for t in Z[ds + '_type']])
    rm = Z[ds + '_room']
    K = int(rm.max()) + 1
    N = np.zeros((K, 7))
    np.add.at(N, (rm, ty), 1)
    S = {}
    for a, arm in enumerate(ARMS[1:], 1):
        d = Z[ds + '_score'][:, a] - Z[ds + '_score'][:, 0]
        s = np.zeros((K, 7))
        np.add.at(s, (rm, ty), d)
        S[arm] = s
    return S, N, K


SS, NS, KS = table('S', [0, 1, 2, 3, 4, 5, 6])
SR, NR, KR = table('R', [0, 1, 2, 3, 4, 5, 7])
w = NS.sum(0)[:6] / (NS.sum(0)[:6] + NR.sum(0)[:6])


def counts(k, reps):
    idx = rng.integers(0, k, size=(reps, k))
    idx += np.arange(reps)[:, None] * k
    return np.bincount(idx.ravel(), minlength=reps * k).reshape(reps, k).astype(np.float64)


def q(x, level):
    return [round(float(v), 2) for v in 100 * np.quantile(x, [(1 - level) / 2, (1 + level) / 2])]


out = {}
# imperial / metric split of dev-S1 object size
imp = Z['S_imperial']
for arm in ARMS[1:]:
    a = ARMS.index(arm)
    r = {}
    # card's dev-S1 rule
    dev = {}
    for t in range(7):
        keep = NS[:, t] > 0
        x = np.concatenate([(M @ SS[arm][keep, t]) / (M @ NS[keep, t]) for M in (counts(int(keep.sum()), CH) for _ in range(REP // CH))])
        dev[TS[t]] = dict(delta=round(100 * SS[arm][:, t].sum() / NS[:, t].sum(), 2), rooms=int(keep.sum()), se=round(float(100 * x.std()), 2),
                          ci_step200=q(x, 1 - 0.05 / 7), ci_later=q(x, 1 - 0.05 / 28), ci95=q(x, 0.95))
    PS, PR = [], []
    for _ in range(REP // CH):
        MS, MR = counts(KS, CH), counts(KR, CH)
        PS.append((MS @ SS[arm]) / (MS @ NS))
        PR.append((MR @ SR[arm]) / (MR @ NR))
    PS, PR = np.concatenate(PS), np.concatenate(PR)
    m7 = PS.mean(1)
    dev['mean_of_seven'] = dict(delta=round(float(100 * (SS[arm].sum(0) / NS.sum(0)).mean()), 2), se=round(float(100 * m7.std()), 2),
                                ci_step200=q(m7, 0.95), ci_later=q(m7, 0.9875))
    dev['fires_step200'] = [k for k, v in dev.items() if isinstance(v, dict) and v['ci_step200'][1] < 0]
    dev['fires_later'] = [k for k, v in dev.items() if isinstance(v, dict) and v['ci_later'][1] < 0]
    r['devS1_rule'] = dev
    for name, ww in (('pooled_item', w), ('pooled_equal', np.full(6, 0.5))):
        P = np.concatenate([ww * PS[:, :6] + (1 - ww) * PR[:, :6], PS[:, 6:7], PR[:, 6:7]], 1)
        dS, dR = SS[arm].sum(0) / NS.sum(0), SR[arm].sum(0) / NR.sum(0)
        p = np.concatenate([ww * dS[:6] + (1 - ww) * dR[:6], dS[6:7], dR[6:7]])
        pool = {}
        for t in range(8):
            pool[T8[t]] = dict(delta=round(float(100 * p[t]), 2), se=round(float(100 * P[:, t].std()), 2),
                               ci_step200=q(P[:, t], 1 - 0.05 / 8), ci_later=q(P[:, t], 1 - 0.05 / 32), ci95=q(P[:, t], 0.95))
        m8 = P.mean(1)
        pool['mean_of_eight'] = dict(delta=round(float(100 * p.mean()), 2), se=round(float(100 * m8.std()), 2), ci_step200=q(m8, 0.95), ci_later=q(m8, 0.9875))
        pool['fires_step200'] = [k for k, v in pool.items() if isinstance(v, dict) and v['ci_step200'][1] < 0]
        pool['fires_later'] = [k for k, v in pool.items() if isinstance(v, dict) and v['ci_later'][1] < 0]
        r[name] = pool
    r['per_set'] = dict(devS1={TS[t]: [round(float(100 * SS[arm][:, t].sum() / NS[:, t].sum()), 2), round(float(100 * PS[:, t].std()), 2)] for t in range(7)},
                        R0dev={(TS[:6] + ('appearance_order',))[t]: [round(float(100 * SR[arm][:, t].sum() / NR[:, t].sum()), 2), round(float(100 * PR[:, t].std()), 2)] for t in range(7)})
    d = Z['S_score'][:, a] - Z['S_score'][:, 0]
    r['devS1_size_split'] = dict(metric=[int((imp == 0).sum()), round(float(100 * d[imp == 0].mean()), 2)], imperial=[int((imp == 1).sum()), round(float(100 * d[imp == 1].mean()), 2)])
    out[arm] = r
# correlation between two looks of one leg: D0 m100 and D0 m200 under the same room draws
PS1, PS2, PR1, PR2 = [], [], [], []
for _ in range(5):
    MS, MR = counts(KS, CH), counts(KR, CH)
    PS1.append((MS @ SS['D0m100']) / (MS @ NS)); PS2.append((MS @ SS['D0m200']) / (MS @ NS))
    PR1.append((MR @ SR['D0m100']) / (MR @ NR)); PR2.append((MR @ SR['D0m200']) / (MR @ NR))
PS1, PS2, PR1, PR2 = [np.concatenate(x) for x in (PS1, PS2, PR1, PR2)]
P1 = np.concatenate([w * PS1[:, :6] + (1 - w) * PR1[:, :6], PS1[:, 6:7], PR1[:, 6:7]], 1)
P2 = np.concatenate([w * PS2[:, :6] + (1 - w) * PR2[:, :6], PS2[:, 6:7], PR2[:, 6:7]], 1)
out['look_correlation_D0_m100_m200'] = dict(per_type={T8[t]: round(float(np.corrcoef(P1[:, t], P2[:, t])[0, 1]), 3) for t in range(8)},
                                            mean_of_eight=round(float(np.corrcoef(P1.mean(1), P2.mean(1))[0, 1]), 3),
                                            devS1_per_type={TS[t]: round(float(np.corrcoef(PS1[:, t], PS2[:, t])[0, 1]), 3) for t in range(7)})
out['item_weights_devS1'] = [round(float(x), 4) for x in w]
out['draws'] = REP
json.dump(out, open('OBSERVED_READS.json', 'w'), indent=1)
for arm in ARMS[1:]:
    r = out[arm]
    print('==', arm, '| dev-S1 size split (items, delta):', r['devS1_size_split'])
    print('  dev-S1 rule fires: step-200 level', r['devS1_rule']['fires_step200'], '| later level', r['devS1_rule']['fires_later'],
          '| size', r['devS1_rule']['object_size'])
    for nm in ('pooled_item', 'pooled_equal'):
        print(' ', nm, 'fires: step-200 level', r[nm]['fires_step200'], '| later level', r[nm]['fires_later'], '| size', r[nm]['object_size'],
              '| mean', r[nm]['mean_of_eight'])
    print('  pooled_item se per type', [r['pooled_item'][t]['se'] for t in T8], '| dev-S1 rule se', [r['devS1_rule'][t]['se'] for t in TS])
print('look correlation', out['look_correlation_D0_m100_m200'])
