import sys, re, collections
sys.path.insert(0, '/scratch/jjyeung/orch_n30/swarm_an/kit'); import san_kit as K
rows = K.direct('R1', 200, 'R0-dev', types=['obj_appearance_order'])
r = rows[0]; print(r['question'][:260]); print(r['options']); print('gt', r['gt'], 'pred', r['pred']); print(r['text'][:520]); print('======')
def opt_orders(r): return {o[0]: [x.strip().lower() for x in o.split('.', 1)[1].split(',')] for o in r['options']}
dep = right_dep = inopt = 0; pairs = collections.Counter(); n = 0
for r in rows:
    th = (r['text'] or '').split('</think>')[0]; oo = opt_orders(r); truth = oo[str(r['gt']).strip()[0]]
    cand = None
    for line in reversed(th.splitlines()):
        low = line.lower()
        pos = sorted((low.rfind(x), x) for x in truth)
        if all(p >= 0 for p, _ in pos) and ('order' in low or 'then' in low or 'first' in low):
            cand = [x for _, x in pos]; break
    if cand is None: continue
    n += 1
    pl = str(r['pred']).strip()[:1]; chosen = oo.get(pl)
    if chosen != cand:
        dep += 1; right_dep += r['score'] >= 1; inopt += cand in oo.values()
    for a in range(3):
        i, j = truth[a], truth[a + 1]
        pairs[(a, cand.index(i) < cand.index(j))] += 1
print('parsed', n, 'of', len(rows), '| answer differs from written order', dep, 'right among them', right_dep, 'written order is some option', inopt)
print('adjacent true pairs kept in the written order (pair index: kept, reversed):', [(a, pairs[(a, True)], pairs[(a, False)]) for a in range(3)])
