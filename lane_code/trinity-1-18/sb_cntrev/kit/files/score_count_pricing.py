#!/usr/bin/env python3
"""Reference scorer of the count pricing kit (lane sb_countdesign, 2026-11-19). CPU only, numpy only.

Fixed math (arm N, the per-frame maximum):
  for one (capture, category): in each of the 32 frame slots take the SAM 3 instances with joint_score >= T_JOINT, in decreasing
  joint_score; drop an instance whose mask (subsampled [::2, ::2]) has IoU > NMS_IOU with a kept one or whose overlap with a kept one
  exceeds NMS_CONTAIN of the smaller mask; the frame count is the number kept; the tool count is the maximum over the 32 slots.
  An item's tool count is the sum over its categories. A missing capture or category scores as tool count 0 (a refusal counts as 0).
Composites with the direct answers stored in the item file (step 544 = count-first form; R1 step 200 = first-seen list):
  R1 replace-if-large: tool count if tool count >= LARGE else the direct answer;  R2 floor: max(direct answer, tool count).
Metric: VSI-Bench MRA with the official comparison (no tolerance), as the stored direct scores use.
Verdict on the large items (truth >= 5) of the items scored, arm N, a missing capture or category counted as 0:
  PASS  N >= direct step 544 + 5 and the room-bootstrap 95% lower bound of N - direct step 544 is above 0;
  NEAR  not PASS, N >= direct R1 step 200 + 5 and the lower bound of N - direct R1 step 200 is above 0;  FAIL otherwise.
  +INFORMATIVE is appended when N is also at or above the best constant answer (5, 6 or 7, chosen on the same items) and the rank
  correlation of the tool count with the truth inside these items is at least 0.5.

Modes:
  --selftest                         bars from the item file and a synthetic fixture
  --k1 LABELS TEACHER [--captures K1_LIFT_META.json]   K1 reproduction (truth from lane b05_owngrd's labels)
  --items ITEMS --teacher ROOT[,ROOT2] --out OUT.json [--set R0-dev|dev-S1]   the dev read (--set when only one set was run)
"""
import argparse, collections, gzip, json, os, random, sys
import numpy as np

T_JOINT, NMS_IOU, NMS_CONTAIN, LARGE = 0.35, 0.5, 0.8, 4
THETA = [0.5 + 0.05 * i for i in range(10)]
SEED, DRAWS = 20261119, 10000

def mra(pred, truth):
    try: p = float(pred)
    except (TypeError, ValueError): return 0.0
    rel = abs(p - float(truth)) / float(truth)
    return sum(1.0 for t in THETA if rel <= 1 - t) / 10.0

def rle_decode(r):
    h, w = r['size']; counts = r['counts']
    if sum(counts) != h * w: raise ValueError('invalid RLE')
    return np.repeat(np.arange(len(counts)) % 2, counts).astype(bool).reshape((h, w), order='F')

def frame_count(instances):
    ins = sorted((i for i in instances if i['joint_score'] >= T_JOINT), key=lambda i: -i['joint_score'])
    kept = []
    for i in ins:
        m = rle_decode(i['mask'])[::2, ::2]; a = int(m.sum())
        if a == 0: continue
        ok = True
        for k, b in kept:
            inter = int((m & k).sum())
            if inter and (inter / float(a + b - inter) > NMS_IOU or inter / float(min(a, b)) > NMS_CONTAIN): ok = False; break
        if ok: kept.append((m, a))
    return len(kept)

def tool_count(teacher, category):
    """Returns (count, best_slot, per_slot list) or None when the category was not prompted."""
    per = []
    for slot in sorted(teacher['frames'], key=int):
        ph = teacher['frames'][slot]['phrases'].get(category)
        if ph is None: return None
        per.append(frame_count(ph['instances']))
    if len(per) != 32: raise ValueError('expected 32 frame slots, got %d' % len(per))
    best = int(np.argmax(per))
    return per[best], best, per

def load_teacher(root, scene):
    """root: one output folder of run_count_teacher.py, or several separated by commas (the first that holds the scene wins)."""
    for r in root.split(','):
        p = os.path.join(r, scene.replace('/', '__'), 'teacher.json.gz')
        if os.path.isfile(p): return json.load(gzip.open(p))
    return None

def spearman(x, y):
    def rank(v):
        v = np.asarray(v, float); o = np.argsort(v, kind='mergesort'); r = np.empty(len(v)); r[o] = np.arange(len(v), dtype=float)
        for u in np.unique(v):
            m = v == u; r[m] = r[m].mean()
        return r
    if len(x) < 3: return None
    rx, ry = rank(x), rank(y)
    if rx.std() == 0 or ry.std() == 0: return None
    return float(np.corrcoef(rx, ry)[0, 1])

CONSTANTS = (5, 6, 7)

def boot(vals_by_room, draws=DRAWS, seed=SEED):
    rooms = sorted(vals_by_room); rng = random.Random(seed); out = []
    for _ in range(draws):
        s = [v for r in rng.choices(rooms, k=len(rooms)) for v in vals_by_room[r]]
        out.append(sum(s) / len(s))
    out.sort(); return out[int(0.025 * draws)], out[int(0.975 * draws)]

def summarize(items, est, tag):
    """items: list of dicts with truth, room, set, direct; est: {id: tool count}."""
    res = {}
    def arm_scores(sel):
        arms = collections.OrderedDict()
        arms['N_tool'] = {x['id']: mra(est[x['id']], x['truth']) for x in sel}
        for k in ('S1_544', 'R1_200'):
            arms['direct_' + k] = {x['id']: float(x['direct'][k]['score']) for x in sel}
            def num(x):
                try: return float(x['direct'][k]['pred'])
                except (TypeError, ValueError): return 0.0
            arms['R1_replace_if_large_' + k] = {x['id']: mra(est[x['id']] if est[x['id']] >= LARGE else num(x), x['truth']) for x in sel}
            arms['R2_floor_' + k] = {x['id']: mra(max(num(x), est[x['id']]), x['truth']) for x in sel}
        return arms
    groups = collections.OrderedDict()
    groups['large_all'] = [x for x in items if x['truth'] >= 5]
    for s in sorted(set(x['set'] for x in items)): groups['large_' + s] = [x for x in items if x['truth'] >= 5 and x['set'] == s]
    groups['every_item'] = list(items)
    for s in sorted(set(x['set'] for x in items)): groups['every_' + s] = [x for x in items if x['set'] == s]
    for b in (2, 3, 4): groups['truth_%d' % b] = [x for x in items if x['truth'] == b]
    for g, sel in groups.items():
        if not sel: continue
        arms = arm_scores(sel); d = dict(n=len(sel), rooms=len(set(x['room'] for x in sel)))
        for a, sc in arms.items():
            d[a] = round(100 * sum(sc.values()) / len(sc), 2)
        for a in ('N_tool', 'R1_replace_if_large_S1_544', 'R1_replace_if_large_R1_200', 'R2_floor_S1_544', 'R2_floor_R1_200'):
            for ref in ('direct_S1_544', 'direct_R1_200'):
                by = collections.defaultdict(list)
                for x in sel: by[x['room']].append(100 * (arms[a][x['id']] - arms[ref][x['id']]))
                lo, hi = boot(by); d['%s_minus_%s' % (a, ref)] = [round(d[a] - d[ref], 2), round(lo, 2), round(hi, 2)]
        d['tool_ge_large'] = sum(1 for x in sel if est[x['id']] >= LARGE); d['tool_zero'] = sum(1 for x in sel if est[x['id']] == 0)
        for c in CONSTANTS: d['const_%d' % c] = round(100 * sum(mra(c, x['truth']) for x in sel) / len(sel), 2)
        d['best_const'] = max(d['const_%d' % c] for c in CONSTANTS)
        rho = spearman([est[x['id']] for x in sel], [x['truth'] for x in sel]); d['spearman_tool_truth'] = None if rho is None else round(rho, 3)
        d['tool_under'] = sum(1 for x in sel if est[x['id']] < x['truth']); d['tool_over'] = sum(1 for x in sel if est[x['id']] > x['truth'])
        res[g] = d
    return res

def verdict(res):
    g = res.get('large_all');
    if not g: return 'NO_ITEMS'
    n, d544, d200 = g['N_tool'], g['direct_S1_544'], g['direct_R1_200']
    lo544 = g['N_tool_minus_direct_S1_544'][1]; lo200 = g['N_tool_minus_direct_R1_200'][1]
    base = 'PASS' if (n >= d544 + 5 and lo544 > 0) else ('NEAR' if (n >= d200 + 5 and lo200 > 0) else 'FAIL')
    rho = g.get('spearman_tool_truth')
    informative = n >= g['best_const'] and rho is not None and rho >= 0.5
    return base + ('+INFORMATIVE' if informative else '')

def dev_read(items_path, root, out, only_set=None):
    items = [json.loads(l) for l in open(items_path)] if items_path.endswith('.jsonl') else json.load(open(items_path))
    if only_set: items = [x for x in items if x['set'] == only_set]
    est = {}; detail = {}; cache = {}
    for x in items:
        if x['scene'] not in cache: cache[x['scene']] = load_teacher(root, x['scene'])
        t = cache[x['scene']]; tot = 0; parts = []
        for c in x['categories']:
            r = tool_count(t, c) if t is not None else None
            parts.append(dict(category=c, count=None if r is None else r[0], best_slot=None if r is None else r[1], per_slot=None if r is None else r[2]))
            tot += 0 if r is None else r[0]
        est[x['id']] = tot; detail[x['id']] = parts
    have = [x for x in items if cache[x['scene']] is not None]
    res = dict(constants=dict(T_JOINT=T_JOINT, NMS_IOU=NMS_IOU, NMS_CONTAIN=NMS_CONTAIN, LARGE=LARGE, SEED=SEED, DRAWS=DRAWS),
               only_set=only_set, coverage=dict(items=len(items), with_teacher=len(have), missing_scenes=sorted(set(x['scene'] for x in items if cache[x['scene']] is None))[:50]),
               every_item_counted_refusals_as_zero=summarize(items, est, 'all'), only_items_with_teacher_output=summarize(have, est, 'have') if have else {})
    res['verdict_primary'] = verdict(res['every_item_counted_refusals_as_zero'])
    res['per_item'] = {i: dict(tool=est[i], parts=detail[i]) for i in est}
    json.dump(res, open(out, 'w'), indent=1)
    g = res['every_item_counted_refusals_as_zero'].get('large_all', {})
    print('coverage', res['coverage']['with_teacher'], 'of', res['coverage']['items'], '| large items: tool', g.get('N_tool'), 'direct 544', g.get('direct_S1_544'), 'direct 200', g.get('direct_R1_200'), 'best constant', g.get('best_const'), 'rank correlation', g.get('spearman_tool_truth'), '| verdict', res['verdict_primary'])

def k1(labels, teacher, captures_meta=None):
    keep = None
    if captures_meta: keep = set(c['capture'] for c in json.load(open(captures_meta))['captures'])
    sc = collections.defaultdict(list)
    for fn in sorted(os.listdir(labels)):
        if not fn.endswith('.labels.json.gz'): continue
        lab = json.load(gzip.open(os.path.join(labels, fn)))
        if keep is not None and lab['canonical'] not in keep: continue
        t = json.load(gzip.open(os.path.join(teacher, fn[:-len('.labels.json.gz')], 'teacher.json.gz')))
        for name, role in lab['roles'].items():
            if role != 'gt': continue
            vis = set()
            for k in range(32):
                f = lab['frames'][str(k)].get(name)
                if f: vis |= set(f['gt_visible'])
            if not vis: continue
            r = tool_count(t, name); c = 0 if r is None else r[0]
            sc[str(len(vis)) if len(vis) <= 4 else '5+'].append(mra(c, len(vis)))
    print('K1 arm N (per-frame maximum, joint >= %.2f, duplicate suppression):' % T_JOINT, ' '.join('truth %s: %.1f (n %d)' % (b, 100 * np.mean(sc[b]), len(sc[b])) for b in ('1', '2', '3', '4', '5+')))

def selftest(items_path):
    assert mra(4, 5) == 0.6 and mra(5, 5) == 1.0 and mra(2, 5) == 0.0 and mra(6, 5) == 0.6, 'MRA rule'
    def rle(m):
        f = m.reshape(-1, order='F').astype(np.uint8); counts = []; cur = 0; run = 0
        for v in f:
            if v == cur: run += 1
            else: counts.append(run); cur = v; run = 1
        counts.append(run); return dict(size=list(m.shape), counts=counts)
    def box(x0, y0, x1, y1):
        m = np.zeros((64, 64), bool); m[y0:y1, x0:x1] = True; return m
    a, b, c = box(0, 0, 20, 20), box(30, 30, 50, 50), box(2, 2, 18, 18)
    assert (rle_decode(rle(a)) == a).all()
    fr = lambda ms: dict(phrases=dict(chair=dict(instances=[dict(joint_score=s, mask=rle(m)) for m, s in ms])))
    frames = {str(k): fr([]) for k in range(32)}
    frames['3'] = fr([(a, 0.9), (b, 0.8), (c, 0.7)])      # c lies inside a: a duplicate
    frames['7'] = fr([(a, 0.9), (b, 0.3)])                # b under the joint floor
    t = dict(frames=frames)
    r = tool_count(t, 'chair'); assert r[0] == 2 and r[1] == 3 and r[2][7] == 1, r
    assert abs(spearman([1, 2, 3, 4], [2, 4, 6, 9]) - 1.0) < 1e-9 and spearman([1, 1, 1], [1, 2, 3]) is None
    assert tool_count(t, 'table') is None
    if items_path:
        items = [json.loads(l) for l in open(items_path)]
        est = {x['id']: 0 for x in items}; res = summarize(items, est, 'x')
        g = res['large_all']; print('bars from the item file: large items n %d, direct step 544 %.2f, direct R1 step 200 %.2f' % (g['n'], g['direct_S1_544'], g['direct_R1_200']))
        for s in ('dev-S1', 'R0-dev'):
            g = res['large_' + s]; print('   %s: n %d, %.2f, %.2f' % (s, g['n'], g['direct_S1_544'], g['direct_R1_200']))
        assert res['large_all']['n'] == 93 and abs(res['large_all']['direct_S1_544'] - 28.82) < 0.01 and abs(res['large_all']['direct_R1_200'] - 15.05) < 0.01
        assert verdict(res) == 'FAIL'
        assert abs(res['large_all']['best_const'] - 58.17) < 0.02, res['large_all']['best_const']
    print('selftest OK')

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--selftest', action='store_true'); ap.add_argument('--items'); ap.add_argument('--teacher'); ap.add_argument('--out')
    ap.add_argument('--k1', nargs=2, metavar=('LABELS', 'TEACHER')); ap.add_argument('--captures')
    ap.add_argument('--set', choices=['R0-dev', 'dev-S1'], help='restrict the dev read to one set (use when only that set was run)')
    a = ap.parse_args()
    if a.selftest: selftest(a.items)
    elif a.k1: k1(a.k1[0], a.k1[1], a.captures)
    else: dev_read(a.items, a.teacher, a.out, a.set)
