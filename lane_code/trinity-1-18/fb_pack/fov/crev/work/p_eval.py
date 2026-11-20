"""Probe build3 evaluate() at the bars' boundaries and summaries() against score_400.summarize on fabricated records."""
import importlib.util, json
import numpy as np
spec = importlib.util.spec_from_file_location('sf3', '/scratch/jjyeung/orch_n30/fb_pack/fov/build3/score_fov.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
res = {}


def contrast(points, lo, hi):
    return {'points': points, 'ci95': [lo, hi], 'rooms': 10}


def disp(c, lo, f1, f2):
    return {'combined': {'V1-A': contrast(c, lo, 1), 'V2-A': contrast(c, lo, 1)},
            'folds': [{'name': 'fold1', 'V1-A': contrast(f1, -9, 9), 'V2-A': contrast(f1, -9, 9)},
                      {'name': 'fold2', 'V1-A': contrast(f2, -9, 9), 'V2-A': contrast(f2, -9, 9)}]}


def dist(u1, u2, uc):
    return {'combined': {'V1-A': contrast(0, -9, uc), 'V2-A': contrast(0, -9, uc)},
            'folds': [{'name': 'fold1', 'V1-A': contrast(0, -9, u1), 'V2-A': contrast(0, -9, u1)},
                      {'name': 'fold2', 'V1-A': contrast(0, -9, u2), 'V2-A': contrast(0, -9, u2)}]}


eps = 1e-12
cases = {
    'all_at_boundary_pass': (disp(-0.25, -0.50, -0.50, -0.50), dist(0.0, 0.0, 0.0), True),
    'D1_just_below': (disp(-0.25 - eps, -0.50, -0.5, -0.5), dist(1, 1, 1), False),
    'D2_just_below': (disp(-0.25, -0.50 - eps, -0.5, -0.5), dist(1, 1, 1), False),
    'D3_fold2_below': (disp(0, 0, 0, -0.50 - eps), dist(1, 1, 1), False),
    'H_fold1_below': (disp(0, 0, 0, 0), dist(-eps, 1, 1), False),
    'H_combined_below': (disp(0, 0, 0, 0), dist(1, 1, -eps), False),
}
for name, (d, r, expect) in cases.items():
    crit, choice = m.evaluate(d, r)
    res[name] = {'V2_acceptable': crit['V2']['acceptable'], 'expected': expect, 'ok': crit['V2']['acceptable'] == expect}
# Choice order: make V1 and V2 differ.
good, bad = contrast(0, 0, 1), contrast(-1, -1, 1)
def mix(v1, v2):
    d = {'combined': {'V1-A': v1, 'V2-A': v2}, 'folds': [{'name': n, 'V1-A': contrast(0, -9, 9), 'V2-A': contrast(0, -9, 9)} for n in ('fold1', 'fold2')]}
    return m.evaluate(d, dist(1, 1, 1))[1]
res['choice'] = {'both': mix(good, good), 'V1_only': mix(good, bad), 'V2_only': mix(bad, good), 'neither': mix(bad, bad)}
res['choice_ok'] = res['choice'] == {'both': 'V2', 'V1_only': 'V1', 'V2_only': 'V2', 'neither': 'NONE'}
# summaries() relabels score_400.summarize output; check against a direct call.
s = m.module(m.S1, 'p_eval_s1')
rng = np.random.default_rng(0)
records = []
for k in range(40):
    gt = rng.uniform(.5, 5, 30)
    records.append({'room': f'r{k % 12}', 'gt': gt, 'pred': {'A': gt * rng.uniform(.8, 1.2, 30), 'V1': gt * rng.uniform(.7, 1.3, 30), 'V2': gt * rng.uniform(.9, 1.1, 30)}})
folds = [{'name': 'fold1', 'test_rooms': [f'r{i}' for i in range(6)]}, {'name': 'fold2', 'test_rooms': [f'r{i}' for i in range(6, 12)]}]
mine = m.summaries(s, records, folds)
direct = m.summarize(s, [dict(r, pred={'A': r['pred']['A'], 'B': r['pred']['V1'], 'G': r['pred']['V2']}) for r in records])
res['summaries_relabel_ok'] = (mine['combined']['V1-A'] == direct['B-A'] and mine['combined']['V2-A'] == direct['G-A']
                               and mine['combined']['V2-V1'] == direct['G-B'] and mine['combined']['V2'] == direct['G'])
# Independent recomputation of V2-A combined from pair_scores + interval.
room = {}
for r in records:
    for a in ('A', 'V2'):
        room.setdefault((a, r['room']), []).extend(s.pair_scores(r['pred'][a], r['gt']).tolist())
rooms = sorted({r['room'] for r in records})
vals = [np.mean(room['V2', x]) - np.mean(room['A', x]) for x in rooms]
res['independent_V2-A'] = {'points': float(np.mean(vals)), 'ci95': s.interval(vals)}
res['independent_matches'] = abs(res['independent_V2-A']['points'] - mine['combined']['V2-A']['points']) < 1e-12 and \
    res['independent_V2-A']['ci95'] == mine['combined']['V2-A']['ci95']
print(json.dumps(res, indent=1))
