# Q1: what the stated order rests on (dev VSTI camera-object items, steps 200 and 544)
import sys, json, itertools, random
sys.path.insert(0, '/scratch/jjyeung/orch_n30/san_dd_vsticam/work'); from common import *
D = dev()
by = {(d['id'], d['step']): d for d in D}
def model_prefs(d):
    """pairwise (nearer, farther) statements of the model on item d"""
    if d['type'] == NF:
        if d['step'] == 200 and d['rel']: return [d['rel']]
        if d['step'] == 544 and d['pred'] in 'AB':
            lab = d['opts'][ord(d['pred']) - 65]
            return [(d['subj'], d['ref'])] if lab == 'Near' else [(d['ref'], d['subj'])]
        return []
    if d['step'] == 200: o = d['order'] or []
    else: o = sorted(d['dist'], key=lambda x: d['dist'][x])
    return [(o[i], o[j]) for i in range(len(o)) for j in range(i + 1, len(o))]
rooms = defaultdict(list)
for d in D: rooms[(d['room'], d['step'])].append(d)
def ans(d): return d['opts'][ord(d['pred']) - 65] if d['pred'] and d['pred'] in 'ABCD'[:len(d['opts'])] else None
def truth(d): return d['opts'][ord(d['gt']) - 65]
def rules(d):
    c = d['opts']; out = {}
    out['last'] = (c[-1], True); out['first'] = (c[0], True)
    fs = by[(d['id'], 200)]['fs']
    out['early'] = argbest(c, lambda x: fs.get(x))
    out['neark'] = argbest(c, lambda x: abs(fs[x] - d['k']) if x in fs else None)
    out['large'] = argbest(c, lambda x: size(x)[0], reverse=True)
    prefs = [p for e in rooms[(d['room'], d['step'])] if e['id'] != d['id'] for p in model_prefs(e)]
    w, u, n = copeland(c, prefs); out['room'] = (w, u)
    if d['step'] == 544:
        w2, u2 = argbest(c, lambda x: d['dist'].get(x)); out['dist544'] = (w2, u2)
    return out
res = {}
for d in D:
    if d['type'] not in CAM: continue
    res[(d['id'], d['step'])] = dict(r=rules(d), a=ans(d), t=truth(d), type=d['type'], score=d['score'])
names = ['last', 'first', 'early', 'neark', 'large', 'room']
print('rule | step | type | covered | =model | =truth   (ties broken by option order; room abstains without shared pairs)')
for step in (200, 544):
    for t in CAM:
        its = [v for (i, s), v in res.items() if s == step and v['type'] == t]
        line = []
        for n in names:
            cov = [v for v in its if v['r'][n][0] is not None]
            line.append('%s %d/%d/%d' % (n, len(cov), sum(v['r'][n][0] == v['a'] for v in cov), sum(v['r'][n][0] == v['t'] for v in cov)))
        print(step, t[-2:], 'acc', sum(v['score'] for v in its), '|', ' ; '.join(line))
# large: v7-only coverage
for t in CAM:
    its = [v for (i, s), v in res.items() if s == 200 and v['type'] == t]
    ids = [i for (i, s), v in res.items() if s == 200 and v['type'] == t]
    v7 = [v for i, v in zip(ids, its) if all(size(x, False)[0] is not None for x in by[(i, 200)]['opts'])]
    print('large v7-only', t[-2:], len(v7), sum(v['r']['large'][0] == v['a'] for v in v7), sum(v['r']['large'][0] == v['t'] for v in v7))
# decision lists: rules abstain when not unique (except last/first)
def pick(v, n):
    w, u = v['r'][n]
    if n in ('last', 'first'): return w
    return w if (w is not None and u) else None
def dl_pred(v, order):
    for n in order:
        p = pick(v, n)
        if p is not None: return p, n
    return None, None
for step in (200, 544):
    its = [v for (i, s), v in res.items() if s == step]
    pool = ['early', 'neark', 'large', 'room', 'last', 'first'] if step == 200 else ['dist544', 'early', 'neark', 'large', 'room', 'last', 'first']
    best = []
    for L in range(1, 5):
        for order in itertools.permutations(pool, L):
            if order[-1] not in ('last', 'first'): continue
            h = sum(dl_pred(v, order)[0] == v['a'] for v in its)
            best.append((h, order))
    best.sort(reverse=True)
    print('step', step, 'best decision lists (hits of %d):' % len(its), best[:4])
    # split-half check of the top list chosen on even items only
    ev = its[0::2]; od = its[1::2]
    bb = max(((sum(dl_pred(v, o)[0] == v['a'] for v in ev), o) for _, o in best), key=lambda x: x[0])
    print('  fit on even half', bb, 'scored on odd half', sum(dl_pred(v, bb[1])[0] == v['a'] for v in od), 'of', len(od))
    o = best[0][1]
    for t in CAM:
        sub = [v for v in its if v['type'] == t]
        print('  per type', t[-2:], sum(dl_pred(v, o)[0] == v['a'] for v in sub), 'of', len(sub), 'rule use', Counter(dl_pred(v, o)[1] for v in sub))
json.dump({'%s|%d' % k: dict(r={n: list(x) for n, x in v['r'].items()}, a=v['a'], t=v['t'], type=v['type'], score=v['score']) for k, v in res.items()},
          open(T + '/q1_rules.json', 'w'))
