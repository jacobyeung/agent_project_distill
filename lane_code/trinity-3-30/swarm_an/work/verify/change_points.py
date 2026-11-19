"""Benchmark-point price of each proposed change (counterfactuals). Run with the planner python."""
import sys, re, json, collections
sys.path.insert(0, '/scratch/jjyeung/orch_n30/swarm_an/kit'); sys.path.insert(0, '/scratch/jjyeung/orch_n30/swarm_an/work/verify')
import san_kit as K
STEP = int(sys.argv[1]) if len(sys.argv) > 1 else 200
out = {}
def unit(q):
    q = q.lower()
    if re.search(r'centimet|\bcm\b', q): return 'cm'
    if re.search(r'\bfeet\b|\bfoot\b|\bft\b', q): return 'ft'
    if re.search(r'\binch', q): return 'in'
    return 'm'
def noturn(r):
    t = (r['text'] or '').split('</think>')[0].lstrip()
    return t.startswith('Step 1') and not re.search(r'half turn|flip forward', t)
# ---- direction, R0-dev away leaves
new = K.direct('R1', STEP, 'R0-dev'); old = {r['id']: r for r in K.direct('S1', 544, 'R0-dev')}
print('== direction away, by level: no-turn traces (n, right), turn-writing traces (n, right), expected gain if no-turn items reach the turn-writing accuracy; upper bound = every wrong no-turn item fixed')
d = {}
for lv in ('easy', 'medium', 'hard'):
    rs = [r for r in new if r['type'] == 'object_rel_direction_' + lv and r['subtype'] == 'away']
    nt = [r for r in rs if noturn(r)]; tw = [r for r in rs if not noturn(r)]
    a = sum(r['score'] for r in tw) / len(tw); right = sum(r['score'] for r in nt)
    exp = len(nt) * a - right; ub = len(nt) - right
    d[lv] = dict(items=len(rs), noturn=len(nt), noturn_right=int(right), turn=len(tw), turn_right=int(sum(r['score'] for r in tw)),
                 expected_items=round(exp, 1), upper_items=int(ub), leaf_points_expected=round(100 * exp / len(rs), 2), leaf_points_upper=round(100 * ub / len(rs), 2))
    print(lv, d[lv])
cat_exp = (d['easy']['leaf_points_expected'] + d['hard']['leaf_points_expected']) / 4; cat_ub = (d['easy']['leaf_points_upper'] + d['hard']['leaf_points_upper']) / 4
print('ReVSI direction category points expected %.2f upper %.2f ; ReVSI points expected %.2f upper %.2f' % (cat_exp, cat_ub, cat_exp / 7, cat_ub / 7))
out['direction_clause'] = dict(levels=d, revsi_category_expected=round(cat_exp, 2), revsi_category_upper=round(cat_ub, 2), revsi_points_expected=round(cat_exp / 7, 2), revsi_points_upper=round(cat_ub / 7, 2))
# ---- counting runaways against step 544
print('== counting: force-closed items, loss now and at step 544 (points on the leaf)')
c = {}
for setname, subs in (('dev-S1', [None]), ('R0-dev', ['single', 'multiple'])):
    nw = K.direct('R1', STEP, setname, types=['object_counting']); od = {r['id']: r for r in K.direct('S1', 544, setname, types=['object_counting'])}
    for sub in subs:
        rs = [r for r in nw if sub is None or r['subtype'] == sub]; fc = [r for r in rs if r['forced_close']]
        now = 100 * sum(1 - r['score'] for r in fc) / len(rs); then = 100 * sum(1 - od[r['id']]['score'] for r in fc) / len(rs)
        c[(setname, sub)] = (len(rs), len(fc), now, then)
        print(setname, sub, 'items', len(rs), 'force-closed', len(fc), 'lost now %.2f' % now, 'lost at 544 %.2f' % then, 'gap %.2f' % (now - then))
g_vsi = c[('dev-S1', None)][2] - c[('dev-S1', None)][3]
g_rev = ((c[('R0-dev', 'single')][2] - c[('R0-dev', 'single')][3]) + (c[('R0-dev', 'multiple')][2] - c[('R0-dev', 'multiple')][3])) / 2
ub_vsi = c[('dev-S1', None)][2]; ub_rev = (c[('R0-dev', 'single')][2] + c[('R0-dev', 'multiple')][2]) / 2
print('VSI-Bench counting: back to 544 on runaways +%.2f category = %.2f VSI points; all runaway loss %.2f = %.2f' % (g_vsi, g_vsi / 8, ub_vsi, ub_vsi / 8))
print('ReVSI counting: back to 544 on runaways +%.2f category = %.2f ReVSI points; all runaway loss %.2f = %.2f' % (g_rev, g_rev / 7, ub_rev, ub_rev / 7))
out['counting_runaway'] = dict(vsi_category_back_to_544=round(g_vsi, 2), vsi_points_back_to_544=round(g_vsi / 8, 2), vsi_category_all=round(ub_vsi, 2), vsi_points_all=round(ub_vsi / 8, 2),
                               revsi_category_back_to_544=round(g_rev, 2), revsi_points_back_to_544=round(g_rev / 7, 2), revsi_category_all=round(ub_rev, 2), revsi_points_all=round(ub_rev / 7, 2))
# ---- routed distance, metre items
def mra(p, g):
    if p is None: return 0.0
    g = float(g); e = abs(p - g) / abs(g); return sum(e <= 1 - t / 100 + 1e-12 for t in range(50, 100, 5)) / 10
fac = {'m': 1.0, 'cm': 100.0, 'ft': 1 / .3048, 'in': 1 / .0254}
def gap(r):
    g = [re.search(r'distance ([\d.]+) m', c['response'] or '') for c in r['calls'] if c['family'] == 'gap']; g = [float(x.group(1)) for x in g if x]
    return g[-1] if g else None
try:
    nw = {r['id']: r for r in K.routed(STEP, types=['object_abs_distance'])}; od = {r['id']: r for r in K.routed(544, types=['object_abs_distance'])}
except Exception as e:
    print('no routed read at step', STEP, repr(e)[:80]); json.dump(out, open('/scratch/jjyeung/orch_n30/swarm_an/work/verify/CHANGE_POINTS_m%d.json' % STEP, 'w'), indent=1); sys.exit(0)
print('== routed distance by unit: items, calls, score at 544, score now, only no-call fixed, all call and convert, perfect gap')
dd = {}
for u in ('m', 'cm', 'ft', 'in', 'all'):
    ids = [i for i, r in nw.items() if u == 'all' or unit(r['question']) == u]; n = len(ids)
    t = collections.Counter()
    for i in ids:
        r = nw[i]; f = fac[unit(r['question'])]; g2 = gap(r); g5 = gap(od[i]); gt = r['gt']
        t['calls'] += r['ncalls'] > 0; t['s544'] += od[i]['score']; t['now'] += r['score']
        t['nocall_fixed'] += r['score'] if r['ncalls'] > 0 else (mra(g5 * f, gt) if g5 is not None else r['score'])
        t['faithful'] += mra(g2 * f, gt) if g2 is not None else (mra(g5 * f, gt) if g5 is not None else r['score'])
        t['perfect'] += 1.0 if (g2 is not None or g5 is not None) else r['score']
    dd[u] = dict(items=n, calls=t['calls'], **{k: round(100 * t[k] / n, 2) for k in ('s544', 'now', 'nocall_fixed', 'faithful', 'perfect')})
    print(u, dd[u])
m = dd['m']
print('metre items -> VSI-Bench points (x1/8): calls fixed %+.2f, all call and convert %+.2f, perfect gap %+.2f ; ReVSI (x1/7, proxy): %+.2f, %+.2f, %+.2f' % (
    (m['nocall_fixed'] - m['now']) / 8, (m['faithful'] - m['now']) / 8, (m['perfect'] - m['now']) / 8, (m['nocall_fixed'] - m['now']) / 7, (m['faithful'] - m['now']) / 7, (m['perfect'] - m['now']) / 7))
out['distance'] = dd
json.dump(out, open('/scratch/jjyeung/orch_n30/swarm_an/work/verify/CHANGE_POINTS_m%d.json' % STEP, 'w'), indent=1)
