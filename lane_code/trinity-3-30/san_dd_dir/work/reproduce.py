"""Reproduce the five numbers the san_dd_dir report rests on. Run: /usr/bin/python3 reproduce.py (CPU, read-only, ~30 s)."""
import os, sys, json, sqlite3, ast, re, collections
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import dirparse as P
K = P.K
R2 = P.load('R1', 200); R5 = {r['id']: r for r in P.load('S1', 544)}
away = [r for r in R2 if r['subtype'] == 'away']
# 1. the no-turn clause follows the D opening
d = [r for r in away if r['P']['open'] == 'D']; s = [r for r in away if r['P']['open'] == 'S']
print('1. R0-dev away @200: no-turn clause on %d of %d (E %d, M %d, H %d; %d wrong); D-opened %d of %d carry it; Seen-opened %d of %d' % (
    sum(r['P']['turn'] == 'keep' for r in away), len(away), *[sum(r['P']['turn'] == 'keep' and r['lv'] == lv for r in away) for lv in 'EMH'],
    sum(r['P']['turn'] == 'keep' and r['score'] < 1 for r in away), sum(r['P']['turn'] == 'keep' for r in d), len(d), sum(r['P']['turn'] == 'keep' for r in s), len(s)))
# 2. training: D-skeleton (pool w1g) rows never carry an away clause; Seen rows use a 73-name vocabulary
S = '/scratch/jjyeung/orch_n30/r1_ops6/store/a2_vqa_v7'
F = json.load(open(S + '/FAMILY_INDEX_RANGES.json'))['families']
db = sqlite3.connect('file:' + S + '/vqa/rows.sqlite?mode=ro', uri=True)
AWAY = re.compile(r"away from|opposite direction|my back to|back turned|turned away", re.I)
n = collections.Counter(); V = {'W': set(), 'S': set()}
for t in P.T:
    ids = [i for lo, hi in F[t] for i in range(lo, hi + 1)]
    for k in range(0, len(ids), 200):
        for i, row in db.execute('select i,row from rows where i in (%s)' % ','.join(map(str, ids[k:k + 200]))):
            r = json.loads(row); si = r['student_input']; si = si if isinstance(si, dict) else ast.literal_eval(si)
            g = 'W' if r['pool'] == 'w1g' else 'S'; q = si['question']
            n[(g, bool(AWAY.search(q)))] += 1
            tr = P.triple(q)
            if tr: V[g].update(tr[:3])
print('2. training direction rows: D-skeleton (w1g) with away clause %d of %d; Seen rows with away clause %d of %d; distinct object names Seen %d vs D %d' % (
    n[('W', True)], n[('W', True)] + n[('W', False)], n[('S', True)], n[('S', True)] + n[('S', False)], len(V['S']), len(V['W'])))
# 3. away-hard use of back
ah = [r for r in away if r['lv'] == 'H']; tu = [r for r in ah if r['P']['turn'] == 'half']; nt = [r for r in ah if r['P']['turn'] != 'half']
b = lambda g, k: sum(r[k][0] == 'B' for r in g)
print('3. R0 away-hard back answers %d of %d (truth %d); turned %d of %d (truth %d); no-turn %d of %d (truth %d)' % (
    b(ah, 'prc'), len(ah), b(ah, 'gtc'), b(tu, 'prc'), len(tu), b(tu, 'gtc'), b(nt, 'prc'), len(nt), b(nt, 'gtc')))
# 4. front prior in the stated hard relation (toward frame), pooled over dev-S1, R0 toward, R0 away turned, both twin sets
def fb(rows, flip):
    c = collections.Counter()
    for r in rows:
        g = r['gtc']; f = r['P']['fwd']
        if flip: g = P.OPP[g[0]] + P.OPP[g[1]]
        c[(g[0], f[0])] += 1
    return c
D = P.load('R1', 200, 'dev-S1')
tw = {}
for x in ('away', 'forward'):
    tw[x] = K.facing('R1', 200, x, types=['object_rel_direction_hard'])
    for r in tw[x]: r['P'] = P.parse(r); r['gtc'] = P.code_of_word(P.optword(r, 'gt'), 'H')
c = fb([r for r in D if r['lv'] == 'H'], False) + fb([r for r in R2 if r['lv'] == 'H' and r['subtype'] == 'toward'], False) + fb(tu, True) + fb(tw['away'], True) + fb(tw['forward'], False)
print('4. hard, toward frame: back truths stated front %d of %d; front truths stated back %d of %d' % (c[('B', 'F')], c[('B', 'F')] + c[('B', 'B')], c[('F', 'B')], c[('F', 'B')] + c[('F', 'F')]))
# 5. step 544 (angle) against step 200 (words) on R0 toward items
t = [r for r in R2 if r['subtype'] == 'toward']
print('5. R0 toward: 544 right %d, 200 right %d of %d; disagreements: only 544 right %d, only 200 right %d' % (
    sum(R5[r['id']]['score'] == 1 for r in t), sum(r['score'] == 1 for r in t), len(t),
    sum(R5[r['id']]['score'] == 1 and r['score'] < 1 for r in t), sum(R5[r['id']]['score'] < 1 and r['score'] == 1 for r in t)))
