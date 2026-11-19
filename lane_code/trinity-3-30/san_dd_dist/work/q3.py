# Q3: what triggers the no-call direct template at step 200; do no-call answers use the frames?
import sys, json; sys.path.insert(0, '/scratch/jjyeung/orch_n30/san_dd_dist/work'); from dist_items import *
from collections import Counter, defaultdict
import numpy as np
d = load(); R = build(d); ids = sorted(i for (s, i) in R if s == 200)
X = {i: R[(200, i)] for i in ids}; Y = {i: R[(544, i)] for i in ids}
# 1. same objects (same room, same pair) asked twice
grp = defaultdict(list)
for i, x in X.items(): grp[(x['room'], frozenset(o.lower() for o in x['objs']))].append(x)
multi = [v for v in grp.values() if len(v) > 1]
print('object pairs asked more than once (same room):', len(multi), 'items', sum(len(v) for v in multi))
for v in multi:
    print('  ', v[0]['room'], sorted(v[0]['objs']), [(x['unit'], 'CALL' if x['called'] else 'none', x['tmpl'][:38]) for x in v])
# by object pair ignoring room
grp2 = defaultdict(list)
for i, x in X.items(): grp2[frozenset(o.lower() for o in x['objs'])].append(x)
mixed = [v for v in grp2.values() if len(v) > 1 and len(set(x['called'] for x in v)) > 1]
print('object pairs (any room) with mixed call status:', len(mixed))
for v in mixed[:8]: print('  ', sorted(v[0]['objs']), [(x['unit'], 'CALL' if x['called'] else 'none', x['tmpl'][:30], x['room'][-9:]) for x in v])
# wording x unit call table for wordings with >=5 items
print('wording x unit: calls/items at step 200')
T = Counter(x['tmpl'] for x in X.values())
for t, n in T.most_common():
    if n < 5: continue
    c = {u: '%d/%d' % (sum(x['called'] for x in X.values() if x['tmpl'] == t and x['unit'] == u), sum(1 for x in X.values() if x['tmpl'] == t and x['unit'] == u)) for u in ('m', 'ft', 'in', 'cm')}
    print('  %-62s %s' % (t[:62], c))
# 2. logistic-style comparison: within-wording unit effect, within-unit wording effect (simple stratified counts)
nc = [x for x in X.values() if not x['called']]; cl = [x for x in X.values() if x['called']]
print('no-call by unit', Counter(x['unit'] for x in nc), 'of', Counter(x['unit'] for x in X.values()))
print('no-call rooms', len(set(x['room'] for x in nc)), 'of', len(set(x['room'] for x in X.values())), 'rooms; rooms with both forms', len(set(x['room'] for x in nc) & set(x['room'] for x in cl)))
oc = Counter(o.lower() for x in nc for o in x['objs']); oa = Counter(o.lower() for x in X.values() for o in x['objs'])
print('objects most often in no-call items (no-call/all):', [(o, oc[o], oa[o]) for o, _ in oc.most_common(12)])
# 3. forms
forms = {'first seen in frame': r'first seen in frame', 'candidates ordered nearest to farthest': r'ordered nearest to farthest', 'nearest-to-farthest order': r'nearest-to-farthest order',
         'find the X and the Y, then': r'Step 1: find the [^,.]+ and the [^,.]+, then', 'qualitative (no number before </think>)': None}
for k, p in forms.items():
    if p: print('form %-42s %d of %d' % (k, sum(bool(re.search(p, x['text'])) for x in nc), len(nc)))
think = lambda x: x['text'].split('</think>')[0]
print('no number in think block', sum(not re.search(r'\d+\.?\d*\s*(?:m|meters?|metres?|cm|centimeters?|in|inch|inches|ft|feet|foot)\b', think(x)) for x in nc))
# 4. answers vs truth (metres), no-call items
a = np.array([x['ans'] / x['F'] for x in nc]); t = np.array([x['gt_m'] for x in nc])
g5 = np.array([Y[x['id']]['gap'] if Y[x['id']]['gap'] is not None else np.nan for x in nc])
def rk(v): return np.argsort(np.argsort(v))
ok = ~np.isnan(g5)
print('no-call n', len(nc), 'pearson(ans_m, truth_m) %.3f spearman %.3f log-pearson %.3f' % (np.corrcoef(a, t)[0, 1], np.corrcoef(rk(a), rk(t))[0, 1], np.corrcoef(np.log(a), np.log(t))[0, 1]))
print('  same items, 544 head gap: n %d pearson %.3f spearman %.3f' % (ok.sum(), np.corrcoef(g5[ok], t[ok])[0, 1], np.corrcoef(rk(g5[ok]), rk(t[ok]))[0, 1]))
print('  ans_m: distinct %d, median %.2f, IQR %.2f-%.2f; truth_m median %.2f IQR %.2f-%.2f' % (len(set(np.round(a, 2))), np.median(a), *np.percentile(a, [25, 75]), np.median(t), *np.percentile(t, [25, 75])))
mr = lambda p: 100 * np.mean([mra(pp, tt) for pp, tt in zip(p, t)])
best_c = max(np.arange(0.1, 6.0, 0.01), key=lambda c: mr(np.full(len(t), c)))
print('  MRA (metres) no-call answers %.1f; best constant %.2f m scores %.1f; own median constant %.1f; 544 gap on same items %.1f (n %d)' % (mr(a), best_c, mr(np.full(len(t), best_c)), mr(np.full(len(t), np.median(a))), 100 * np.mean([mra(g, tt) for g, tt in zip(g5[ok], t[ok])]), ok.sum()))
# residual check: does the answer carry information beyond a constant? rank-correlation of answer with truth within unit
for u in ('m', 'ft', 'in', 'cm'):
    s = [x for x in nc if x['unit'] == u]
    if len(s) > 4:
        aa = np.array([x['ans'] / x['F'] for x in s]); tt = np.array([x['gt_m'] for x in s])
        print('  unit %s n %d spearman %.2f' % (u, len(s), np.corrcoef(rk(aa), rk(tt))[0, 1]))
# 5. frame claims vs step-544 ground frames
allf = [f for x in Y.values() for g in x['grounds'] for f in g['frames']]
print('ground frame range at 544: min %d max %d' % (min(allf), max(allf)))
hit = first = tot = 0; chance = []
for x in nc:
    gm = {g['obj'].lower(): g for g in Y[x['id']]['grounds'] if g['frames']}
    for o, f in re.findall(r'find the ([^,.]+?), first seen in frame (\d+)', x['text']):
        g = gm.get(o.strip().lower())
        if not g: continue
        tot += 1; f = int(f); hit += f in g['frames']; first += f == min(g['frames']); chance.append(len(g['frames']) / 32.0)
print('frame claims in no-call traces matched to a 544 ground: %d; claimed frame in the ground frame list %d; equals first listed frame %d; chance of a random frame in list %.2f' % (tot, hit, first, np.mean(chance) if chance else 0))
