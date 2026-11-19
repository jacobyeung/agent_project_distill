"""Lane sb_countdesign: does the model's own answer or runaway separate large sets (truth >= 5) from small ones? All 535 dev counting items. CPU, read-only."""
import sys, json, collections
sys.path.insert(0, '/scratch/jjyeung/orch_n30/san_dd_count/work'); import cnt
K = cnt.K
def num(p):
    try: return float(p)
    except Exception: return None
out = {}
for s in ('dev-S1', 'R0-dev'):
    per = {}
    for run, step in cnt.CK:
        for r in K.direct(run, step, s, types=['object_counting']): per.setdefault(r['id'], {})['%s_%d' % (run, step)] = r
    rooms = set(v['R1_200']['room'] for v in per.values() if float(v['R1_200']['gt']) >= 5)
    print(s, 'items', len(per), 'truth>=5', sum(1 for v in per.values() if float(v['R1_200']['gt']) >= 5), 'in rooms', len(rooms))
    for k in ('S1_544', 'R1_200'):
        for thr in (4, 5):
            big = [v for v in per.values() if float(v[k]['gt']) >= 5]; small = [v for v in per.values() if float(v[k]['gt']) <= 3]; mid = [v for v in per.values() if float(v[k]['gt']) == 4]
            f = lambda v: (num(v[k]['pred']) is not None and num(v[k]['pred']) >= thr) or bool(v[k]['forced_close'])
            tp = sum(f(v) for v in big); fp = sum(f(v) for v in small); mp = sum(f(v) for v in mid)
            print('  %s: "answer >= %d or runaway" fires on %d of %d truth>=5, %d of %d truth 4, %d of %d truth<=3' % (k, thr, tp, len(big), mp, len(mid), fp, len(small)))
            out['%s|%s|%d' % (s, k, thr)] = dict(big=[tp, len(big)], four=[mp, len(mid)], small=[fp, len(small)])
    # signed error at truth>=5 for step 544 (count-first form): ratio pred/gt
    import statistics
    r = [num(v['S1_544']['pred']) / float(v['S1_544']['gt']) for v in per.values() if float(v['S1_544']['gt']) >= 5 and num(v['S1_544']['pred'])]
    print('  step 544 pred/truth at truth>=5: median %.2f, under %d, over %d, exact %d of %d' % (statistics.median(r), sum(x < 1 for x in r), sum(x > 1 for x in r), sum(x == 1 for x in r), len(r)))
    r = [num(v['R1_200']['pred']) / float(v['R1_200']['gt']) for v in per.values() if float(v['R1_200']['gt']) >= 5 and num(v['R1_200']['pred']) and not v['R1_200']['forced_close']]
    print('  step 200 (not runaway) pred/truth at truth>=5: median %.2f, under %d, over %d of %d' % (statistics.median(r), sum(x < 1 for x in r), sum(x > 1 for x in r), len(r)))
json.dump(out, open('GATE_CUE.json', 'w'), indent=1)
