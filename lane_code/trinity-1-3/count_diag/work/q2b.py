import json, re, numpy as np, random
from collections import Counter, defaultdict
from cd_load import load, load_on16k, as_num
D, _ = load(); O, _ = load_on16k()
F = json.load(open('Q2_FORMS.json'))
SEED = 20261118
def boot(delta, rooms, draws=10000):
    by = defaultdict(list)
    for d, r in zip(delta, rooms): by[r].append(d)
    R = list(by); S = np.array([sum(by[r]) for r in R]); N = np.array([len(by[r]) for r in R]); K = len(R)
    rng = random.Random(SEED); out = []
    while len(out) < draws:
        c = np.bincount(rng.choices(range(K), k=K), minlength=K); n = c @ N
        if n: out.append((c @ S) / n)
    return np.quantile(out, [0.025, 0.975])
L = []
for s in ['dev-S1', 'R0-dev']:
    A = {x['id']: x for x in F[f'R1m100|{s}']}
    B = D['S544'][s]; R1 = D['R1m100'][s]
    n = len(B)
    def cls(x):
        if x['forced']: return 'runaway (B2048 forced close)'
        if x['pf'] == 'TOTALS': return 'totals form'
        if x['pf'] == 'FS_LIST' and x['ls'] and x['ls']['dup'] > 0: return 'FS list with repeated entry'
        if x['pf'] == 'FS_LIST': return 'FS list, no repeat'
        return 'other form'
    agg = defaultdict(list)
    for i in B:
        agg[cls(A[i])].append(100 * (float(R1[i]['score']) - float(B[i]['score'])))
    L.append(f'\n{s}: R1m100 - S544 decomposed by the R1 trace class (contribution = summed delta / {n} items)')
    tot = 0
    for k, v in sorted(agg.items(), key=lambda t: sum(t[1])):
        L.append(f'  {k:32} n={len(v):>3}  mean delta {np.mean(v):+6.1f}  contribution {sum(v)/n:+6.2f}')
        tot += sum(v) / n
    L.append(f'  total {tot:+.2f}')
    # counterfactual: runaway items scored as S544
    ids = list(B)
    dl = [100 * ((float(B[i]['score']) if A[i]['forced'] else float(R1[i]['score'])) - float(B[i]['score'])) for i in ids]
    lo, hi = boot(dl, [B[i]['room'] for i in ids])
    L.append(f'  counterfactual, runaway items given step 544 score: {np.mean(dl):+.2f} [{lo:+.2f}, {hi:+.2f}]')
    # always-2 reference
    a2 = np.mean([100 * (1.0 if as_num(B[i]['ground_truth']) == 2 else max(0, sum(abs(2 - as_num(B[i]['ground_truth'])) / as_num(B[i]['ground_truth']) < 1 - (0.5 + 0.05 * k) + 1e-9 for k in range(10)) / 10)) for i in ids])
    L.append(f'  reference: answering 2 on every item scores MRA {a2:.2f}')
open('Q2B_REPORT.txt', 'w').write('\n'.join(L) + '\n'); print('\n'.join(L))
