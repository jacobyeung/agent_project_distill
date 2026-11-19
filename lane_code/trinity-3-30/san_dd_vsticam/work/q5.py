# Q5 (what training gave), Q6 scene stats on rows, Q7 dev wording, and the near/far column for Q1
import sys, json, re
sys.path.insert(0, '/scratch/jjyeung/orch_n30/san_dd_vsticam/work'); from common import *
D = dev(); by = {(d['id'], d['step']): d for d in D}
Q = json.load(open(T + '/q1_rules.json'))
print('== Q5 flips and letters')
for t in CAM + (NF,):
    ids = [d['id'] for d in D if d['step'] == 200 and d['type'] == t]
    c = Counter()
    for i in ids:
        a, b = by[(i, 544)]['score'] == 1, by[(i, 200)]['score'] == 1
        c[('544 right' if a else '544 wrong') + ' -> ' + ('200 right' if b else '200 wrong')] += 1
    L = lambda s, f: dict(sorted(Counter(by[(i, s)][f] for i in ids).items()))
    print(t[-2:], dict(c), '| truth', L(200, 'gt'), '| 544', L(544, 'pred'), '| 200', L(200, 'pred'))
print('== Q5 accuracy split by shortcuts (shortcut gives truth / none does)')
for name, S in (('last+large', ['last', 'large']), ('all six (step-200 statements)', ['last', 'first', 'early', 'neark', 'large', 'room'])):
    for t in CAM:
        c = Counter()
        for d in D:
            if d['type'] != t or d['step'] != 200: continue
            v = Q['%s|200' % d['id']]; tr = v['t']
            sc = any(v['r'][n][0] == tr for n in S)
            for s in (544, 200):
                c[(s, sc, 'n')] += 1; c[(s, sc, 'right')] += by[(d['id'], s)]['score'] == 1
        print(name, t[-2:], ' '.join('%d %s: %d/%d' % (s, 'shortcut' if sc else 'no-shortcut', c[(s, sc, 'right')], c[(s, sc, 'n')]) for s in (544, 200) for sc in (True, False)))
vals = Counter(); zero = 0; n = 0
for d in D:
    if d['step'] == 544 and d['type'] in CAM:
        n += 1; zero += any(x == 0 for x in d['dist'].values())
        for x in d['dist'].values(): vals[x] += 1
print('== 544 stated distances: items', n, 'items with a 0.0 m', zero, 'most common values', vals.most_common(8), 'distinct', len(vals))
print('== Q1 near/far column (step 200 and 544): rule -> predicted relation; =model / =truth of 150')
for s in (200, 544):
    c = Counter(); rooms = defaultdict(list)
    for d in D:
        if d['step'] == s: rooms[d['room']].append(d)
    for d in D:
        if d['step'] != s or d['type'] != NF: continue
        x, y = d['subj'], d['ref']; fs = by[(d['id'], 200)]['fs']
        near = {'last': d['opts'][-1].split()[-1] if False else None}
        def rel(nearer): return 'Near' if nearer == x else 'Far'
        m = d['opts'][ord(d['pred']) - 65] if d['pred'] in ('A', 'B') else None; tr = d['opts'][ord(d['gt']) - 65]
        picks = {'last option': d['opts'][-1], 'first option': d['opts'][0]}
        if x in fs and y in fs and fs[x] != fs[y]: picks['earlier first-seen is nearer'] = rel(x if fs[x] < fs[y] else y)
        if x in fs and y in fs and abs(fs[x] - d['k']) != abs(fs[y] - d['k']): picks['first-seen nearer k is nearer'] = rel(x if abs(fs[x] - d['k']) < abs(fs[y] - d['k']) else y)
        sx, sy = size(x)[0], size(y)[0]
        if sx and sy and sx != sy: picks['larger is nearer'] = rel(x if sx > sy else y)
        picks['subject is Near'] = 'Near'
        for nm, p in picks.items():
            c[(nm, 'n')] += 1; c[(nm, 'model')] += p == m; c[(nm, 'truth')] += p == tr
    print(s, ' ; '.join('%s %d/%d/%d' % (nm, c[(nm, 'n')], c[(nm, 'model')], c[(nm, 'truth')]) for nm in sorted(set(k[0] for k in c))))
print('== Q6 rows per scene (all four families) and distinct k')
R = rows(); sc = defaultdict(list)
for f in R:
    for r in R[f]: sc[r['canonical']].append(r)
cam_sc = {s: [r for r in v if r['qt'] in CAM] for s, v in sc.items()}
nr = sorted(len(v) for v in cam_sc.values() if v); nk = sorted(len(set(r['k'] for r in v)) for v in cam_sc.values() if v)
print('scenes with camera rows', len(nr), 'camera rows per scene median', nr[len(nr) // 2], 'max', nr[-1], '| distinct k per scene median', nk[len(nk) // 2], 'max', nk[-1], '| share of scenes with >=4 distinct k %.2f' % (sum(x >= 4 for x in nk) / len(nk)))
ch = Counter()
for s, v in cam_sc.items():
    for i in range(len(v)):
        for j in range(i + 1, len(v)):
            a, b = v[i], v[j]
            if a['k'] == b['k']: continue
            ia = {x['id']: g for x, g in zip(a['inst'], a['gv'])}; ib = {x['id']: g for x, g in zip(b['inst'], b['gv'])}
            sh = [z for z in ia if z in ib]
            if len(sh) < 2: continue
            ta = min(sh, key=lambda z: ia[z]); tb = min(sh, key=lambda z: ib[z])
            ch['row pairs sharing >=2 objects'] += 1; ch['nearest shared object changes'] += ta != tb
print(dict(ch))
print('== Q7 dev names')
names = Counter(); plural = set(); shared = []; dup = 0
GEN = {'object', 'item', 'box', 'bag', 'container', 'cabinet', 'shelf', 'table', 'chair', 'door', 'window', 'light', 'picture', 'plant', 'machine', 'panel', 'board', 'stand', 'rack', 'holder', 'cover', 'frame', 'cord', 'cable', 'switch', 'sign', 'paper', 'papers', 'clothes', 'stuff'}
gen = Counter()
for d in D:
    if d['step'] != 200: continue
    c = d['opts'] if d['type'] in CAM else [d['subj'], d['ref']]
    if len(set(c)) < len(c): dup += 1
    for o in c:
        names[o] += 1
        if o.endswith('s') and not o.endswith(('ss', 'us', 'is')): plural.add(o)
        if o in GEN: gen[o] += 1
    for a in c:
        for b in c:
            if a != b and (re.search(r'\b%s\b' % re.escape(a), b)): shared.append((d['id'][:6], d['type'][-2:], a, b))
print('items with a repeated name', dup, '| plural-looking names', len(plural), sorted(plural)[:40])
print('generic names (my list) item-mentions', sum(gen.values()), gen.most_common(12))
print('name contained in another candidate of the same item', len(shared), shared[:12])
