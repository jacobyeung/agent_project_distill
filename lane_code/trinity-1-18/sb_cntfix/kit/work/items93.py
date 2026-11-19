"""Lane sb_countdesign: the 93 dev counting items with truth >= 5 (dev-S1 + R0-dev); bars at steps 544 / R1-100 / R1-200. Read-only on sources."""
import sys, json, collections
sys.path.insert(0, '/scratch/jjyeung/orch_n30/san_dd_count/work'); import cnt
K = cnt.K
out = {}
rows_all = {}
for s in ('dev-S1', 'R0-dev'):
    per = {}
    for run, step in cnt.CK:
        for r in K.direct(run, step, s, types=['object_counting']):
            per.setdefault(r['id'], {})[(run, step)] = r
    rows_all[s] = per
def mra(pred, gt):
    try: p = float(pred); g = float(gt)
    except Exception: return 0.0
    if g == 0: return 0.0
    rel = abs(p - g) / g
    return sum(1.0 for t in [0.5 + 0.05 * i for i in range(10)] if rel <= 1 - t + 1e-12) / 10.0
items = []
for s, per in rows_all.items():
    for i, d in per.items():
        r = d.get(('R1', 200)) or list(d.values())[0]
        g = float(r['gt'])
        if g < 5: continue
        it = dict(id=i, set=s, gt=g, room=r['room'], count_kind=r['count_kind'], subtype=r['subtype'], question=r['question'], cats=cnt.cats(r['question']))
        for (run, step), rr in d.items():
            k = '%s_%d' % (run, step)
            it['score_' + k] = rr['score']; it['pred_' + k] = rr['pred']; it['fc_' + k] = rr['forced_close']
        items.append(it)
json.dump(items, open('ITEMS93.json', 'w'), indent=0)
print('n items', len(items), collections.Counter(i['set'] for i in items))
for s in ('dev-S1', 'R0-dev'):
    L = [i for i in items if i['set'] == s]
    print(s, len(L))
    for k in ('S1_544', 'R1_100', 'R1_200'):
        v = [i.get('score_' + k) for i in L]; n = sum(1 for x in v if x is not None)
        print('  ', k, 'n', n, 'mean %.2f' % (100 * sum(x or 0 for x in v) / max(n, 1)), 'forced', sum(1 for i in L if i.get('fc_' + k)))
    print('   truth hist', sorted(collections.Counter(int(i['gt']) for i in L).items()))
    print('   kind', collections.Counter((i['count_kind'], i['subtype']) for i in L))
    print('   ncats', collections.Counter(len(i['cats']) for i in L))
    print('   cats', collections.Counter(c for i in L for c in i['cats']).most_common(40))
# pooled
for k in ('S1_544', 'R1_100', 'R1_200'):
    v = [i.get('score_' + k) or 0 for i in items]; print('pooled', k, '%.2f' % (100 * sum(v) / len(v)))
# constants
for c in (2, 3, 4, 5, 6, 7, 8, 10):
    print('const', c, ' '.join('%s %.1f' % (s, 100 * sum(mra(c, i['gt']) for i in items if i['set'] == s) / sum(1 for i in items if i['set'] == s)) for s in ('dev-S1', 'R0-dev')),
          'pooled %.1f' % (100 * sum(mra(c, i['gt']) for i in items) / len(items)))
# check my mra against stored score
bad = 0; n = 0
for i in items:
    for k in ('R1_200',):
        if i.get('pred_' + k) is not None and i.get('score_' + k) is not None:
            n += 1
            if abs(mra(i['pred_' + k], i['gt']) - i['score_' + k]) > 1e-6: bad += 1
print('mra check: mismatches', bad, 'of', n)
