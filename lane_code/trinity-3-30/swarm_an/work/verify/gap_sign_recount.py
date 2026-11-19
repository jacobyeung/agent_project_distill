import sys, re
sys.path.insert(0, '/scratch/jjyeung/orch_n30/swarm_an/kit'); import san_kit as K
fac = {'m': 1.0, 'cm': 100.0, 'ft': 1 / .3048, 'in': 1 / .0254}
def unit(q):
    q = q.lower()
    if re.search(r'centimet|\bcm\b', q): return 'cm'
    if re.search(r'\bfeet\b|\bfoot\b|\bft\b', q): return 'ft'
    if re.search(r'\binch', q): return 'in'
    return 'm'
def mra(p, g): return sum(abs(p - g) / g <= 1 - t / 100 + 1e-12 for t in range(50, 100, 5)) / 10
def gap(r):
    g = [re.search(r'distance ([\d.]+) m', c['response'] or '') for c in r['calls'] if c['family'] == 'gap']; g = [float(x.group(1)) for x in g if x]
    return g[-1] if g else None
def nfr(r):
    out = []
    for c in r['calls']:
        m = re.search(r'frames ([\d,]+)', c['response'] or '')
        if c['family'] != 'gap' and m: out.append(len(m.group(1).split(',')))
    return min(out) if len(out) >= 2 else None
S = {s: {r['id']: r for r in K.routed(s, types=['object_abs_distance'])} for s in (544, 200)}
same = n = 0
for i, r in S[200].items():
    a, b = gap(r), gap(S[544][i])
    if a is None or b is None: continue
    t = float(r['gt']) / fac[unit(r['question'])]; n += 1; same += ((a - t) * (b - t) > 0)
print('shared numeric gaps', n, 'same sign of error', same)
for s in (544, 200):
    lo = []; hi = []
    for r in S[s].values():
        g = gap(r); k = nfr(r)
        if g is None or k is None: continue
        (lo if k < 3 else hi).append(mra(g, float(r['gt']) / fac[unit(r['question'])]))
    print(s, 'rarer object grounded in <3 frames: n %d MRA %.1f | >=3: n %d MRA %.1f | if the low group matched the high group: %+.1f points on 150 items' % (len(lo), 100 * sum(lo) / len(lo), len(hi), 100 * sum(hi) / len(hi), len(lo) * (sum(hi) / len(hi) - sum(lo) / len(lo)) * 100 / 150))
