# Q4: usage path after the response: conversion lines recomputed, departures, and not-seen handling (both steps).
import sys; sys.path.insert(0, '/scratch/jjyeung/orch_n30/san_dd_dist/work'); from dist_items import *
from collections import Counter
d = load(); R = build(d)
for step in (544, 200):
    xs = [x for (s, i), x in sorted(R.items()) if s == step and x['called']]
    lines = [(x, c) for x in xs for c in x['conv']]
    bad = []
    for x, (u, gw, fw, yw) in lines:
        gw, fw, yw = float(gw), float(fw), float(yw)
        e = dict(g_eq_gap=x['gap'] is not None and abs(gw - x['gap']) <= 0.005, factor_ok=abs(fw / x['F'] - 1) < 1e-3,
                 arith_ok=abs(yw - gw * fw) <= max(0.011, 5e-4 * abs(yw)), ans_eq=x['ans'] is not None and abs(x['ans'] - yw) <= 0.011)
        if not all(e.values()): bad.append((x['id'], x['unit'], x['gap'], gw, fw, yw, x['ans'], x['score'], [k for k, v in e.items() if not v]))
    print('== step %d: "Converting to" lines %d on %d items; lines failing a check %d' % (step, len(lines), len(set(x['id'] for x, _ in lines)), len(bad)))
    for b in bad: print('   ', b)
    fac = Counter(c[2] for x, c in lines); print('   factors written', dict(fac))
    # departures from gap x F (1% tolerance) among callers with numeric gap
    dep = [x for x in xs if x['gap'] is not None and usage(x) != 'follows']
    kinds = Counter((x['unit'], usage(x)) for x in dep)
    print('   departures (answer != gap x F within 1%%): %d of %d -> %s' % (len(dep), sum(x['gap'] is not None for x in xs), dict(kinds)))
    for x in dep:
        if usage(x) != 'metres': print('     other:', x['id'], x['unit'], 'gap', x['gap'], 'ans', x['ans'], 'gt', x['gt'], 'score', x['score'], '|', x['post'].split('</think>')[0].strip().replace('\n', ' | ')[-200:])
    # strict departures within 1% (approximate conversions)
    strict = [x for x in xs if x['gap'] is not None and usage(x) == 'follows' and abs(x['ans'] - x['gap'] * x['F']) > max(0.011, 5e-4 * abs(x['gap'] * x['F']))]
    print('   approximate conversions (within 1%% but not exact): %d %s' % (len(strict), [(x['id'][-6:], x['unit'], x['gap'], x['ans']) for x in strict]))
    # not seen
    ns = [x for x in xs if any(g['not_seen'] for g in x['grounds']) or x['gap'] is None]
    print('   items with a not-seen ground or no numeric gap: %d' % len(ns))
    for x in ns:
        gr = '; '.join('%s:%s' % (g['obj'], 'NOT SEEN' if g['not_seen'] else 'ok') for g in x['grounds'])
        print('     ', x['id'], x['unit'], 'gt', x['gt'], 'ans', x['ans'], 'score', x['score'], '|', gr, '| gap resp:', x['gapresp'], '|', x['post'].split('</think>')[0].strip().replace('\n', ' | ')[-230:])
