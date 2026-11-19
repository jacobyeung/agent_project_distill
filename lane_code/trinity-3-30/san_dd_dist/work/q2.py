# Q2: counterfactual prices on the scored truth (row gt), both steps.
import sys, json; sys.path.insert(0, '/scratch/jjyeung/orch_n30/san_dd_dist/work'); from dist_items import *
from collections import Counter
d = load(); R = build(d); ids = sorted(i for (s, i) in R if s == 200)
same = sum(R[(200, i)]['calls'] == R[(544, i)]['calls'] for i in ids if R[(200, i)]['called'] and R[(544, i)]['called'])
both = sum(R[(200, i)]['called'] and R[(544, i)]['called'] for i in ids)
exp544 = sum(R[(544, i)]['calls'] == expected_calls(R[(544, i)]['q'], 'object_abs_distance') for i in ids if R[(544, i)]['called'])
print('call strings identical on shared callers: %d of %d; step-544 calls equal expected_calls: %d of %d' % (same, both, exp544, sum(R[(544, i)]['called'] for i in ids)))
def price(step, rule):
    other = 544 if step == 200 else 200; tot = 0.0; ch = Counter()
    for i in ids:
        x = R[(step, i)]; y = R[(other, i)]; s0 = x['score']; s1 = s0
        if rule in ('a', 'a0', 'd'):
            g = x['gap'] if x['called'] else (y['gap'] if y['called'] else None)
            if rule == 'd' and x['called']: g = None
            if g is not None: s1 = mra(round(g * x['F'], 2), x['gt'])
            elif rule == 'a0' and (x['called'] or not y['called'] or y['gap'] is None): s1 = 0.0
        elif rule == 'b':
            s1 = mra(round(round(x['gt_m'], 2) * x['F'], 2), x['gt'])
        elif rule == 'b_obs':  # perfect head, observed usage: callers keep their answer/gap multiplier; no-call items keep their answer
            if x['called']:
                gp = round(x['gt_m'], 2); u = usage(x)
                mult = x['F'] if u == 'follows' else (1.0 if u == 'metres' else (x['ans'] / x['gap'] if x['gap'] and x['ans'] is not None else None))
                s1 = mra(gp * mult, x['gt']) if mult is not None else s0
        elif rule == 'b_call':  # perfect head and observed usage for callers; no-call items call and convert right with a perfect gap
            if x['called']: s1 = price_item_bobs(x)
            else: s1 = mra(round(round(x['gt_m'], 2) * x['F'], 2), x['gt'])
        elif rule == 'c':
            if x['unit'] == 'cm' and x['called'] and usage(x) == 'metres': s1 = mra(round(x['gap'] * 100, 2), x['gt'])
        elif rule == 'e':  # only caller usage fixed (every caller with a numeric gap answers gap x F)
            if x['called'] and x['gap'] is not None: s1 = mra(round(x['gap'] * x['F'], 2), x['gt'])
        tot += s1; ch['changed'] += s1 != s0; ch['up'] += s1 > s0; ch['down'] += s1 < s0
        ch['gain'] += s1 - s0
    return round(100 * tot / len(ids), 2), dict(changed=ch['changed'], up=ch['up'], down=ch['down'], gain_pts=round(100 * ch['gain'] / len(ids), 2))
def price_item_bobs(x):
    gp = round(x['gt_m'], 2); u = usage(x)
    mult = x['F'] if u == 'follows' else (1.0 if u == 'metres' else (x['ans'] / x['gap'] if x['gap'] and x['ans'] is not None else None))
    return mra(gp * mult, x['gt']) if mult is not None else x['score']
res = {}
for step in (200, 544):
    obs = round(100 * sum(R[(step, i)]['score'] for i in ids) / len(ids), 2)
    res[step] = dict(observed=obs)
    print('== step', step, 'observed', obs)
    for rule, name in [('a', 'a: all call, own gap x F (no-call -> other step gap; no numeric gap -> keep answer)'),
                       ('a0', 'a0: as a, items without any numeric gap score 0'),
                       ('b', 'b: perfect gap (truth in m, 2 dp) x F, all items'),
                       ('b_obs', "b': perfect gap, observed usage; no-call keep answer"),
                       ('b_call', "b'': perfect gap, observed usage for callers; no-call call+convert"),
                       ('c', 'c: only cm metre-answers converted'), ('d', 'd: only no-call items fixed (other step gap x F)'),
                       ('e', 'e: only caller usage fixed (gap x F)')]:
        m, ch = price(step, rule); res[step][rule] = dict(mra=m, **ch); print('  %-90s %6.2f %s' % (name, m, ch))
# overlap check at 200: c + d + e(other than c) vs a
json.dump(res, open('/scratch/jjyeung/orch_n30/san_dd_dist/work/q2_prices.json', 'w'), indent=1)
# per-unit decomposition at 200 for (a), (c), (d)
for step in (200, 544):
    for u in ('m', 'ft', 'in', 'cm'):
        xs = [R[(step, i)] for i in ids if R[(step, i)]['unit'] == u]
        def cf(x, mode):
            other = R[(544 if step == 200 else 200, x['id'])]
            if mode == 'a':
                g = x['gap'] if x['called'] else (other['gap'] if other['called'] else None)
                return mra(round(g * x['F'], 2), x['gt']) if g is not None else x['score']
            if mode == 'd':
                if x['called']: return x['score']
                g = other['gap'] if other['called'] else None
                return mra(round(g * x['F'], 2), x['gt']) if g is not None else x['score']
            if mode == 'e':
                return mra(round(x['gap'] * x['F'], 2), x['gt']) if x['called'] and x['gap'] is not None else x['score']
        n = len(xs); f = lambda v: round(100 * v / n, 1)
        print(step, u, n, 'obs', f(sum(x['score'] for x in xs)), 'a', f(sum(cf(x, 'a') for x in xs)), 'd', f(sum(cf(x, 'd') for x in xs)), 'e', f(sum(cf(x, 'e') for x in xs)))
