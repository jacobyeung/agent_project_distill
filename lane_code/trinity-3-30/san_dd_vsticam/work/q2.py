# Q2: a fixed order of the room against the camera's position (dev at step 200, and store-v7 rows)
import sys, json, random
sys.path.insert(0, '/scratch/jjyeung/orch_n30/san_dd_vsticam/work'); from common import *
def band(dk): return '1-3' if dk <= 3 else ('4-8' if dk <= 8 else ('9-16' if dk <= 16 else '17-31'))
BANDS = ['1-3', '4-8', '9-16', '17-31']
D = dev()
def dev_statements(step):
    """per room: list of (k, x, y, model_x_nearer or None, truth_x_nearer or None, item id, type)"""
    S = defaultdict(list)
    for d in D:
        if d['step'] != step or d['type'] not in CAM + (NF,): continue
        if d['type'] == NF:
            x, y = sorted([d['subj'], d['ref']])
            if step == 200: m = d['rel'][0] == x if d['rel'] else None
            else: m = None if d['pred'] not in ('A', 'B') else ((d['opts'][ord(d['pred']) - 65] == 'Near') == (d['subj'] == x))
            tn = d['opts'][ord(d['gt']) - 65] == 'Near'
            S[d['room']].append((d['k'], x, y, m, tn == (d['subj'] == x), d['id'], 'nf'))
            continue
        order = d['order'] if step == 200 else sorted(d['dist'], key=lambda z: d['dist'][z])
        rank = {o: i for i, o in enumerate(order)}; t = d['opts'][ord(d['gt']) - 65]
        c = d['opts']
        for i in range(len(c)):
            for j in range(i + 1, len(c)):
                x, y = sorted([c[i], c[j]])
                tr = (True if t == x else (False if t == y else None))
                S[d['room']].append((d['k'], x, y, rank[x] < rank[y] if x in rank and y in rank else None, tr, d['id'], d['type'][-2:]))
    return S
for step in (200, 544):
    S = dev_statements(step)
    mc = defaultdict(Counter); tc = defaultdict(Counter); both = Counter(); npairs = Counter()
    for room, st in S.items():
        g = defaultdict(list)
        for s in st: g[(s[1], s[2])].append(s)
        for pair, ss in g.items():
            if len(set(s[0] for s in ss)) < 2: continue
            npairs['pairs'] += 1
            ms = set(s[3] for s in ss if s[3] is not None); npairs['model same at every k'] += len(ms) == 1
            ts = set(s[4] for s in ss if s[4] is not None)
            if len(set(s[0] for s in ss if s[4] is not None)) >= 2: npairs['truth known at >=2 k'] += 1; npairs['truth same at every k'] += len(ts) == 1
            for a in range(len(ss)):
                for b in range(a + 1, len(ss)):
                    A, B = ss[a], ss[b]
                    if A[0] == B[0]: continue
                    bd = band(abs(A[0] - B[0]))
                    if A[3] is not None and B[3] is not None: mc[bd][A[3] == B[3]] += 1
                    if A[4] is not None and B[4] is not None:
                        tc[bd][A[4] == B[4]] += 1
                        if A[3] is not None and B[3] is not None: both[(bd, 'truth flips' if A[4] != B[4] else 'truth same', 'model flips' if A[3] != B[3] else 'model same')] += 1
    print('DEV step', step, dict(npairs))
    for bd in BANDS: print('  dk', bd, 'model same/changed', mc[bd][True], mc[bd][False], '| truth same/changed', tc[bd][True], tc[bd][False])
    print('  cross (statement pairs with truth known):', sorted(both.items()))
# (b) training rows
R = rows(); drop = dropped()
allrows = [r for fam in R for r in R[fam]]
def row_prefs(r):
    """(nearer_id, farther_id) by instance id from geometry; ids are (canonical, instance id)"""
    ids = [(r['canonical'], x['id']) for x in r['inst']]; g = r['gv']
    return [((ids[i], ids[j]) if g[i] < g[j] else (ids[j], ids[i])) for i in range(len(ids)) for j in range(i + 1, len(ids)) if g[i] != g[j]]
sc = defaultdict(list)
for r in allrows: sc[r['canonical']].append(r)
tcount = defaultdict(Counter); pairs_any = Counter()
for scn, rs in sc.items():
    g = defaultdict(list)
    for r in rs:
        for a, b in row_prefs(r):
            key = tuple(sorted([a, b])); g[key].append((r['k'], a == key[0], r['qt']))
    for key, ss in g.items():
        if len(set(s[0] for s in ss)) < 2: continue
        pairs_any['pairs at >=2 k'] += 1; pairs_any['nearer changes at some k'] += len(set(s[1] for s in ss)) > 1
        for a in range(len(ss)):
            for b in range(a + 1, len(ss)):
                if ss[a][0] != ss[b][0]: tcount[band(abs(ss[a][0] - ss[b][0]))][ss[a][1] == ss[b][1]] += 1
print('ROWS: scenes', len(sc), dict(pairs_any))
for bd in BANDS:
    c = tcount[bd]; n = c[True] + c[False]
    print('  dk', bd, 'statement pairs', n, 'nearer changes', c[False], '(%.1f%%)' % (100 * c[False] / max(n, 1)))
# (c) fixed order per scene, leave one out, on camera rows
cnt = Counter()
for fam in CAM:
    for r in R[fam]:
        ids = [(r['canonical'], x['id']) for x in r['inst']]; win = ids[0]
        prefs = [p for o in sc[r['canonical']] if o['qid'] != r['qid'] for p in row_prefs(o)]
        w, u, n = copeland(ids, prefs)
        covered = set(i for p in prefs for i in p if i in ids)
        cnt[(fam[-2:], 'rows')] += 1
        if n: cnt[(fam[-2:], 'with sibling info')] += 1
        if covered == set(ids): cnt[(fam[-2:], 'all candidates covered')] += 1
        if w is not None:
            cnt[(fam[-2:], 'fixed-order hits (info rows)')] += (w == win)
            if covered == set(ids): cnt[(fam[-2:], 'hits among all-covered')] += (w == win)
        # expected score with chance fallback
        cnt[(fam[-2:], 'expected score x1000')] += 1000 * ((w == win) if w is not None else 1 / len(ids))
for k in sorted(cnt): print(' ', k, cnt[k])
