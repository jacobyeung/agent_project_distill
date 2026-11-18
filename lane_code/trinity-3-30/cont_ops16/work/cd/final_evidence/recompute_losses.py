#!/usr/bin/env python3
"""Recompute the counting losses and the runaway decomposition from RUNAWAY_BY_ITEM.tsv alone (lane count_diag).
Room bootstrap: resample the compared items' rooms with replacement (random.Random(20261118).choices), 10,000 draws,
statistic = summed item deltas / items in the drawn rooms, 95% percentile interval (numpy.quantile)."""
import csv, json, random, sys
from collections import defaultdict
import numpy as np

P = sys.argv[1] if len(sys.argv) > 1 else 'RUNAWAY_BY_ITEM.tsv'
items = list(csv.DictReader(open(P), delimiter='\t'))
by = defaultdict(dict)
for it in items:
    by[(it['export'], it['set'])][it['item_id']] = it


def boot(delta, rooms, seed=20261118, draws=10000):
    g = defaultdict(list)
    for dv, room in zip(delta, rooms):
        g[room].append(dv)
    keys = list(g)
    S = np.array([sum(g[k]) for k in keys])
    N = np.array([len(g[k]) for k in keys])
    K = len(keys)
    rng = random.Random(seed)
    out = []
    while len(out) < draws:
        c = np.bincount(rng.choices(range(K), k=K), minlength=K)
        n = c @ N
        if n:
            out.append((c @ S) / n)
    lo, hi = np.quantile(out, [0.025, 0.975])
    return [round(float(np.mean(delta)), 2), round(float(lo), 2), round(float(hi), 2), len(delta), K]


def delta(it):
    return 100 * (float(it['score_b2048']) - float(it['score_step544_b2048']))


res = {'runaways': {}, 'deltas_vs_step544 [mean, lo, hi, items, rooms]': {}, 'R1_decomposition': {},
       'R1_counterfactual_runaways_as_step544 [mean, lo, hi, items, rooms]': {}}
for (ex, s), d in sorted(by.items()):
    single = [it for it in d.values() if it['multi_category'] == '0']
    multi = [it for it in d.values() if it['multi_category'] == '1']
    res['runaways']['%s|%s' % (ex, s)] = dict(
        items=len(d),
        single='%d/%d' % (sum(it['forced_close_b2048'] == '1' for it in single), len(single)),
        multi='%d/%d' % (sum(it['forced_close_b2048'] == '1' for it in multi), len(multi)),
        cap16k=sum(it['cap16k'] == '1' for it in d.values()),
        mean_score=round(100 * float(np.mean([float(it['score_b2048']) for it in d.values()])), 2))
    if ex == 'S544':
        continue
    ids = sorted(d)
    res['deltas_vs_step544 [mean, lo, hi, items, rooms]']['%s|%s' % (ex, s)] = boot([delta(d[i]) for i in ids], [d[i]['room'] for i in ids])
    if ex == 'R1m100':
        n = len(ids)
        run = [i for i in ids if d[i]['forced_close_b2048'] == '1']
        rest = [i for i in ids if d[i]['forced_close_b2048'] != '1']
        res['R1_decomposition'][s] = dict(runaway_items=len(run), runaway_contribution=round(sum(delta(d[i]) for i in run) / n, 2),
                                          other_items=len(rest), other_contribution=round(sum(delta(d[i]) for i in rest) / n, 2))
        cf = [0.0 if d[i]['forced_close_b2048'] == '1' else delta(d[i]) for i in ids]
        res['R1_counterfactual_runaways_as_step544 [mean, lo, hi, items, rooms]'][s] = boot(cf, [d[i]['room'] for i in ids])
json.dump(res, open('LOSS_RECOMPUTE.json', 'w'), indent=1)
print(json.dumps(res, indent=1))
