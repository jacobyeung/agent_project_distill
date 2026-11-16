"""Compare score_and_aggregate_orchard.official_mra (surviving, 0bb536ca) with the authority
agent/evaluation/scoring.mean_relative_accuracy (f67703ea) on a grid; then the parse and aggregation layers."""
import itertools, json, math, sys
import numpy as np
sys.path.insert(0, '.')
import auth_scoring as A
import score_and_aggregate_orchard as S
out = {}
# 1. thresholds
n = (0.95 - 0.5) / 0.05 + 2
ta = np.linspace(0.5, 0.95, int(n)); ts = [0.5 + i * (0.95 - 0.5) / (int(n) - 1) for i in range(int(n))]
out['thresholds'] = dict(n_raw=n, n=int(n), authority=ta.tolist(), surviving=ts,
                         bitwise_equal=[float(a) == b for a, b in zip(ta, ts)], one_minus_authority=[1 - float(a) for a in ta], one_minus_surviving=[1 - b for b in ts])
# 2. grid
tg = [0.0, -0.0, -1.0, -2.5, 1e-9, 0.3, 1.0, 2.5, 3.0, 7.0, 100.0, 1e6, math.inf, -math.inf, math.nan, None]
base = [0.0, -0.0, -1.0, -2.5, 1e-9, 0.3, 1.0, 2.5, 3.0, 7.0, 100.0, 1e6, math.inf, -math.inf, math.nan, None]
preds = set()
for t in [x for x in tg if isinstance(x, float) and math.isfinite(x)]:
    for k in range(0, 21):  # boundary values pred = t*(1 +- 0.05k)
        preds.add(t * (1 + 0.05 * k)); preds.add(t * (1 - 0.05 * k))
        preds.add(t + abs(t) * 0.05 * k); preds.add(t - abs(t) * 0.05 * k)
        preds.add(float(np.nextafter(t * (1 + 0.05 * k), math.inf))); preds.add(float(np.nextafter(t * (1 + 0.05 * k), -math.inf)))
grid_p = base + sorted(preds)
rows = []; diffs = []
for p, t in itertools.product(grid_p, tg):
    a = A.mean_relative_accuracy(p, t, 0.5, 0.95, 0.05)
    s = S.official_mra(p, t, 0.5, 0.95, 0.05)
    rows.append((p, t, a, s))
    if not (a == s): diffs.append((p, t, a, s))
def cls(p, t):
    if p is None or t is None: return 'none'
    if math.isfinite(t) and t < 0: return 'target_negative'
    if not (math.isfinite(p) and math.isfinite(t)): return 'nonfinite'
    if t == 0: return 'target_zero'
    if t < 0: return 'target_negative'
    return 'target_positive_finite'
from collections import Counter
out['grid'] = dict(n_pairs=len(rows), n_diff=len(diffs),
                   pairs_by_class=dict(Counter(cls(p, t) for p, t, _, _ in rows)),
                   diff_by_class=dict(Counter(cls(p, t) for p, t, _, _ in diffs)),
                   diff_examples={c: [d for d in diffs if cls(d[0], d[1]) == c][:6] for c in set(cls(d[0], d[1]) for d in diffs)})
# 3. random positive-target sweep incl. exact ties
rng = np.random.default_rng(17); nd = 0; N = 200000
for _ in range(N):
    t = float(rng.choice([rng.uniform(0.01, 20), round(rng.uniform(0.1, 20), 1), float(rng.integers(1, 30))]))
    p = float(rng.choice([rng.uniform(0, 40), round(t * (1 + 0.05 * rng.integers(-20, 21)), 2), t * (1 + 0.05 * rng.integers(-20, 21))]))
    nd += A.mean_relative_accuracy(p, t, .5, .95, .05) != S.official_mra(p, t, .5, .95, .05)
out['random_positive'] = dict(n=N, n_diff=int(nd))
# 4. parse layer: authority to_float vs surviving official_to_float vs k1_report float()
def k1(x):
    try: return float(x)
    except Exception as e: return 'raises ' + type(e).__name__
inp = [None, '', '3', '3.5', '-2', '0', 'abc', '3.5 m', '<ANSWER>4.2</ANSWER>', 'about 3 or 4', 'nan', 'inf', '1e3', True, 2, 2.5]
out['parse'] = [dict(input=repr(x), authority_to_float=A.to_float(x), surviving_official_to_float=S.official_to_float(x) if isinstance(x, str) or x is None else S.official_to_float(x), k1_float=k1(x) if x is not None else 'None passed through') for x in inp]
# 5. aggregation on a synthetic record set (VSI types only, all three directions present, and a set missing 'hard')
def agg_cmp(types_scores):
    recs = []; srecs = []
    for i, (qt, sc) in enumerate(types_scores):
        key = 'accuracy' if qt in A.MCA_QUESTION_TYPES else 'MRA'
        recs.append({'type': qt, key: sc})
    a = A.aggregate_records(recs)
    by = {}
    for qt, sc in types_scores: by.setdefault(qt, []).append(sc)
    o = {f'{q}_accuracy': sum(v) / len(v) for q, v in by.items()}
    k = ['object_rel_direction_easy_accuracy', 'object_rel_direction_medium_accuracy', 'object_rel_direction_hard_accuracy']
    if all(x in o for x in k): o['object_rel_direction_accuracy'] = (o.pop(k[0]) + o.pop(k[1]) + o.pop(k[2])) / 3.0
    o['overall'] = sum(o.values()) / len(o)
    return dict(authority_overall=a['overall'], surviving_overall=o['overall'], equal=a['overall'] == o['overall'],
                abs_diff=abs(a['overall'] - o['overall']))
vsi = ['object_rel_direction_easy', 'object_rel_direction_medium', 'object_rel_direction_hard', 'object_rel_distance',
       'route_planning', 'obj_appearance_order', 'object_abs_distance', 'object_counting', 'object_size_estimation', 'room_size_estimation']
rs = [(q, float(rng.choice([0.0, 1.0])) if q in A.MCA_QUESTION_TYPES else float(rng.choice(np.linspace(0, 1, 11)))) for q in vsi for _ in range(37)]
out['aggregate_full'] = agg_cmp(rs)
out['aggregate_missing_hard'] = agg_cmp([r for r in rs if r[0] != 'object_rel_direction_hard'])
thr = [.50,.55,.60,.65,.70,.75,.80,.85,.90,.95]; nk = 0; tot = 0; ex = []
for g in np.round(rng.uniform(0.2, 12, 3000), 2).tolist() + rng.uniform(0.2, 12, 3000).tolist():
    for t in thr:
        for c in (g * t, g * (2 - t)):
            for g2 in (g,):
                tot += 1; a = A.mean_relative_accuracy(c, g2, .5, .95, .05); b = S.official_mra(c, g2, .5, .95, .05)
                if a != b: nk += 1; ex.append((c, g2, a, b)) if len(ex) < 5 else None
out['k1_endpoint_constants'] = dict(n=tot, n_diff=nk, examples=ex)
json.dump(out, open('COMPARE.json', 'w'), indent=1, default=str)
print(json.dumps({k: v for k, v in out.items() if k != 'parse'}, default=str)[:4000])
for r in out['parse']: print(r)
