import sys, re, collections
sys.path.insert(0, '/scratch/jjyeung/orch_n30/swarm_an/kit'); import san_kit as K
def num(x):
    m = re.search(r'-?\d+(?:\.\d+)?', str(x or '')); return float(m.group(0)) if m else None
def rank(v):
    o = sorted(range(len(v)), key=lambda i: v[i]); r = [0.0] * len(v); i = 0
    while i < len(o):
        j = i
        while j + 1 < len(o) and v[o[j + 1]] == v[o[i]]: j += 1
        for k in range(i, j + 1): r[o[k]] = (i + j) / 2.0
        i = j + 1
    return r
def pear(a, b):
    n = len(a); ma = sum(a) / n; mb = sum(b) / n
    return sum((x - ma) * (y - mb) for x, y in zip(a, b)) / (sum((x - ma) ** 2 for x in a) * sum((y - mb) ** 2 for y in b)) ** .5
fac = {'m': 1.0, 'cm': 100.0, 'ft': 1 / .3048, 'in': 1 / .0254}
def unit(q):
    q = q.lower()
    if re.search(r'centimet|\bcm\b', q): return 'cm'
    if re.search(r'\bfeet\b|\bfoot\b|\bft\b', q): return 'ft'
    if re.search(r'\binch', q): return 'in'
    return 'm'
d = K.routed(200, types=['object_abs_distance']); nc = [r for r in d if r['ncalls'] == 0]
a = []; t = []
for r in nc:
    p = num(r['answer']); 
    if p is None: continue
    f = fac[unit(r['question'])]; a.append(p / f); t.append(float(r['gt']) / f)
print('no-call items', len(nc), 'with a numeric answer', len(a), 'Spearman %.2f Pearson %.2f' % (pear(rank(a), rank(t)), pear(a, t)))
for step in (544, 200):
    b = K.routed(step, part='B'); calls = [c for r in b for c in r['calls']]
    print('room part B step', step, 'items', len(b), 'calls', len(calls), 'unserved', sum(1 for c in calls if not c['served']), 'empty response', sum(1 for c in calls if not (c['response'] or '').strip()),
          'finish', dict(collections.Counter(r['finish'] for r in b)), 'score %.2f' % (100 * sum(r['score'] for r in b) / len(b)))
b = K.routed(200, part='B'); sq = [r for r in b if not re.search(r'square f(ee|oo)t|sq\.? ?ft', r['question'].lower())]
low = sum(1 for r in sq if (num(r['answer']) or 0) < float(r['gt'])); big = [r for r in sq if float(r['gt']) >= 60]
print('square-metre items', len(sq), 'answers below truth', low, '| truth >= 60 m2:', len(big), 'MRA %.1f' % (100 * sum(r['score'] for r in big) / len(big)), 'zeros', sum(r['score'] == 0 for r in big))
print('traces stating a number with a unit before </think>:', sum(1 for r in b if re.search(r'\d\s*(m2|m²|square met|sq)', (r['text'] or '').split('</think>')[0])))
ids = {r['id']: r for r in d}
for i in ('vsi590k_164821', 'vsi590k_042690', 'vsi590k_252505'):
    r = ids[i]; tx = re.sub(r'\s+', ' ', r['text'] or '')
    print('---', i, '| gt', r['gt'], '| answer', r['answer'], '| score', r['score'], '| calls', r['ncalls']); print('   ', r['question'][:130]); print('   ', tx[:160], '...', tx[-170:])
