"""Relative size (protected outcome): export vs step 544 on dev-S1 (main), paired by item, room bootstrap 10,000 draws,
seed 20261118; percentile intervals at 95% and at the H1 level 1-0.05/8 (registered rule, step 200).
usage: relsize.py --x <fetched/x> [--level 0.99375]"""
import argparse, json, random, collections
BASE = '/scratch/jjyeung/orch_n30/evalx27/work/pull/x27/res/e193/merged/main/results/budget_2048/0/items_leg_m544_main.jsonl'
a = argparse.ArgumentParser(); a.add_argument('--x', required=True); a.add_argument('--level', type=float, default=1 - 0.05 / 8); a = a.parse_args()
rd = lambda p: {r['id']: r for r in map(json.loads, open(p)) if r.get('question_type') == 'relative_size_object'}
b, e = rd(BASE), rd(a.x + '/main/a0/results/budget_2048/0/items_a0.jsonl')
ids = sorted(e); assert ids and all(i in b for i in ids)
by = collections.defaultdict(list)
for i in ids: by[b[i]['room']].append(float(e[i]['score']) - float(b[i]['score']))
rooms = sorted(by); rng = random.Random(20261118); ms = []
for _ in range(10000):
    s = c = 0
    for _ in rooms:
        v = by[rooms[rng.randrange(len(rooms))]]; s += sum(v); c += len(v)
    ms.append(100.0 * s / c)
ms.sort(); q = lambda p: ms[min(len(ms) - 1, max(0, int(p * len(ms))))]
m = 100.0 * sum(sum(v) for v in by.values()) / len(ids)
L = a.level
out = dict(items=len(ids), rooms=len(rooms), base=round(100 * sum(float(b[i]['score']) for i in ids) / len(ids), 2),
           export=round(100 * sum(float(e[i]['score']) for i in ids) / len(ids), 2), delta=round(m, 2),
           ci95=[round(q(0.025), 2), round(q(0.975), 2)], level=L, ci_level=[round(q((1 - L) / 2), 2), round(q((1 + L) / 2), 2)])
out['holds'] = out['ci_level'][1] < 0
print(json.dumps(out))
