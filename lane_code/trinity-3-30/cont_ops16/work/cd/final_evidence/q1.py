import json, re, random, statistics as st
import numpy as np
from collections import Counter, defaultdict
from cd_load import load, as_num, mra

D, SHAS = load()
SEED, DRAWS = 20261118, 10000
EXPORTS = ['S544', 'D0m100', 'H1m100', 'R1m100', 'D0m200']
SETS = ['dev-S1', 'R0-dev']

def cat_of(q):
    m = re.search(r'(?:many|count of|number of|how many)\s+(.*?)\(s\)', q, re.I)
    return m.group(1).strip().lower() if m else '?'

def kind(q):
    return 'multiple' if re.search(r'\(s\)\s+and\s+', q) else 'single'

def tbin(g):
    g = int(g)
    return str(g) if g <= 5 else ('6-9' if g <= 9 else ('10-14' if g <= 14 else '15+'))

PBINS = ['nonnum', '0', '1', '2', '3', '4', '5', '6-9', '10-14', '15+']
def pbin(p):
    if p is None: return 'nonnum'
    if p != int(p): return 'nonnum'
    p = int(p)
    if p <= 5: return str(p)
    return '6-9' if p <= 9 else ('10-14' if p <= 14 else '15+')
TBINS = ['2', '3', '4', '5', '6-9', '10-14', '15+']

def item_view(r):
    gt = as_num(r['ground_truth']); p = as_num(r['extracted_answer'])
    resp = (r['response_text'] or '').strip()
    return dict(id=r['id'], room=r['room'], gt=gt, p=p, score=float(r['score']), resp=resp,
                exact=(p is not None and gt is not None and abs(p - gt) < 1e-9),
                nonnum=p is None, nonint=(p is not None and p != int(p)),
                unit=bool(re.search(r'[A-Za-z]', resp)), cap=bool(r['hit_token_cap']), forced=bool(r['forced_close']),
                unclosed=bool(r['stopped_unclosed']), out=int(r['output_tokens'] or 0), think=int(r['think_tokens'] or 0),
                cat=cat_of(r['question']), kind=kind(r['question']), ds=r['dataset'], tb=tbin(gt), pb=pbin(p), gen=r['raw_generation'] or '')

V = {ex: {s: {i: item_view(r) for i, r in D[ex][s].items()} for s in D[ex]} for ex in D}

def boot(delta, rooms, seed=SEED, draws=DRAWS):
    """room bootstrap of the item-weighted mean of per-item deltas: resample the subset's rooms with replacement."""
    by = defaultdict(list)
    for d, r in zip(delta, rooms): by[r].append(d)
    R = list(by); S = np.array([sum(by[r]) for r in R]); N = np.array([len(by[r]) for r in R])
    rng = random.Random(seed); out = []
    K = len(R)
    while len(out) < draws:
        c = np.bincount(rng.choices(range(K), k=K), minlength=K)
        n = c @ N
        if n == 0: continue
        out.append((c @ S) / n)
    lo, hi = np.quantile(out, [0.025, 0.975])
    return float(np.mean(delta)), float(lo), float(hi), len(delta), K

def summ(items):
    n = len(items)
    num = [x for x in items if not x['nonnum']]
    err = [x['p'] - x['gt'] for x in num]
    rel = [(x['p'] - x['gt']) / x['gt'] for x in num]
    return dict(n=n, mra=100 * sum(x['score'] for x in items) / n,
                exact=100 * sum(x['exact'] for x in items) / n, exact_k=sum(x['exact'] for x in items),
                over=sum(1 for e in err if e > 0), under=sum(1 for e in err if e < 0),
                mean_err=float(np.mean(err)) if err else None, median_err=float(np.median(err)) if err else None,
                mean_rel_err=float(np.mean(rel)) if rel else None,
                nonnum=sum(x['nonnum'] for x in items), nonint=sum(x['nonint'] for x in items), unit=sum(x['unit'] for x in items),
                cap=sum(x['cap'] for x in items), forced=sum(x['forced'] for x in items), unclosed=sum(x['unclosed'] for x in items),
                out_mean=float(np.mean([x['out'] for x in items])), out_median=float(np.median([x['out'] for x in items])),
                out_p90=float(np.quantile([x['out'] for x in items], 0.9)))

res = {'sources_sha256': SHAS, 'summary': {}, 'by_true': {}, 'confusion': {}, 'paired': {}, 'by_kind': {}, 'by_ds': {}, 'by_cat': {}}
for s in SETS:
    for ex in EXPORTS:
        if s not in V[ex]: continue
        items = list(V[ex][s].values())
        res['summary'][f'{ex}|{s}'] = summ(items)
        bt = {}
        for b in TBINS:
            it = [x for x in items if x['tb'] == b]
            if it: bt[b] = dict(n=len(it), mra=100 * sum(x['score'] for x in it) / len(it), exact=sum(x['exact'] for x in it),
                                 mean_pred=float(np.mean([x['p'] for x in it if x['p'] is not None])) if any(x['p'] is not None for x in it) else None,
                                 over=sum(1 for x in it if x['p'] is not None and x['p'] > x['gt']), under=sum(1 for x in it if x['p'] is not None and x['p'] < x['gt']))
        res['by_true'][f'{ex}|{s}'] = bt
        cm = {b: Counter(x['pb'] for x in items if x['tb'] == b) for b in TBINS}
        res['confusion'][f'{ex}|{s}'] = {b: [cm[b].get(p, 0) for p in PBINS] for b in TBINS}
        for k in ['single', 'multiple']:
            it = [x for x in items if x['kind'] == k]
            if it: res['by_kind'][f'{ex}|{s}|{k}'] = summ(it)
# paired comparisons
PAIRS = [('R1m100', 'S544'), ('D0m100', 'S544'), ('H1m100', 'S544'), ('R1m100', 'D0m100'), ('R1m100', 'H1m100'), ('D0m200', 'S544')]
def groups(s, base):
    g = {'all': lambda x: True}
    for b in TBINS: g[f'true={b}'] = (lambda b: lambda x: x['tb'] == b)(b)
    g['true=2'] = lambda x: x['tb'] == '2'
    g['true>=3'] = lambda x: x['gt'] >= 3
    g['true>=6'] = lambda x: x['gt'] >= 6
    g['single'] = lambda x: x['kind'] == 'single'
    g['multiple'] = lambda x: x['kind'] == 'multiple'
    for ds in sorted({x['ds'] for x in base.values() if x['ds']}): g[f'ds={ds}'] = (lambda ds: lambda x: x['ds'] == ds)(ds)
    return g
for s in SETS:
    for a, b in PAIRS:
        if s not in V[a] or s not in V[b]: continue
        A, B = V[a][s], V[b][s]
        G = groups(s, B)
        for gname, f in G.items():
            ids = [i for i in B if f(B[i])]
            if not ids: continue
            dl = [100 * (A[i]['score'] - B[i]['score']) for i in ids]
            ex_dl = [100 * (int(A[i]['exact']) - int(B[i]['exact'])) for i in ids]
            m, lo, hi, n, k = boot(dl, [B[i]['room'] for i in ids])
            me, loe, hie, _, _ = boot(ex_dl, [B[i]['room'] for i in ids])
            res['paired'][f'{a}-{b}|{s}|{gname}'] = dict(n=n, rooms=k, mra_delta=m, ci=[lo, hi], exact_delta=me, exact_ci=[loe, hie])
# class-level (pooled across sets) for R1 vs S544
for s in SETS:
    A, B = V['R1m100'][s], V['S544'][s]
    cc = defaultdict(list)
    for i in B: cc[B[i]['cat']].append(100 * (A[i]['score'] - B[i]['score']))
    res['by_cat'][s] = sorted([(c, len(v), float(np.mean(v)), float(np.sum(v)) / 100) for c, v in cc.items()], key=lambda t: t[3])
json.dump(res, open('Q1_RESULTS.json', 'w'), indent=1)

# text report
L = []
L.append('Counting items at the scored budget B2048. MRA in points (x100). exact = pred == GT.')
for s in SETS:
    L.append(f'\n== {s}')
    L.append(f"{'export':8} {'n':>4} {'MRA':>6} {'exact':>9} {'over':>5} {'under':>5} {'meanErr':>8} {'medErr':>6} {'relErr':>7} {'nonnum':>6} {'nonint':>6} {'unit':>4} {'cap':>4} {'forced':>6} {'outMean':>7} {'outMed':>6} {'outP90':>6}")
    for ex in EXPORTS:
        k = f'{ex}|{s}'
        if k not in res['summary']: continue
        r = res['summary'][k]
        L.append(f"{ex:8} {r['n']:>4} {r['mra']:6.2f} {r['exact']:5.1f}({r['exact_k']:>3}) {r['over']:>5} {r['under']:>5} {r['mean_err']:8.2f} {r['median_err']:6.1f} {r['mean_rel_err']:7.3f} {r['nonnum']:>6} {r['nonint']:>6} {r['unit']:>4} {r['cap']:>4} {r['forced']:>6} {r['out_mean']:7.1f} {r['out_median']:6.0f} {r['out_p90']:6.0f}")
    L.append('  by true count: n | MRA | exact | mean pred | over/under')
    for b in TBINS:
        row = [f'  true={b:5}']
        for ex in EXPORTS:
            k = f'{ex}|{s}'
            if k in res['by_true'] and b in res['by_true'][k]:
                t = res['by_true'][k][b]
                row.append(f"{ex}: n{t['n']} {t['mra']:5.1f} ex{t['exact']} mp{t['mean_pred'] if t['mean_pred'] is None else round(t['mean_pred'],2)} o{t['over']}/u{t['under']}")
        L.append(' | '.join(row))
for s in SETS:
    for ex in EXPORTS:
        k = f'{ex}|{s}'
        if k not in res['confusion']: continue
        L.append(f'\nconfusion {ex} {s} (rows true, cols pred {PBINS})')
        for b in TBINS:
            L.append(f'  true {b:6}: ' + ' '.join(f'{v:4d}' for v in res['confusion'][k][b]))
L.append('\nPaired deltas (A - B), points, room bootstrap 10,000 draws seed 20261118, 95% percentile CI; n items / rooms')
for k, v in res['paired'].items():
    L.append(f"  {k:40} n={v['n']:>3}/{v['rooms']:>2}  MRA {v['mra_delta']:+6.2f} [{v['ci'][0]:+6.2f},{v['ci'][1]:+6.2f}]  exact {v['exact_delta']:+6.2f} [{v['exact_ci'][0]:+6.2f},{v['exact_ci'][1]:+6.2f}]")
L.append('\nR1m100 - S544 by object class (largest summed losses first): class, n, mean delta, summed delta in item-units')
for s in SETS:
    L.append(f'  {s}: ' + '; '.join(f'{c} n{n} {m:+.1f} sum{su:+.2f}' for c, n, m, su in res['by_cat'][s][:12]))
open('Q1_REPORT.txt', 'w').write('\n'.join(L) + '\n')
print('\n'.join(L))
