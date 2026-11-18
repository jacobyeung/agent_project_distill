"""Pooled harm rule of leg R1: reference implementation (H1 on eight direct types over dev-S1 and R0-dev, H2 on their mean).

One decision per boundary (steps 200, 400, 600, 800), an R1 export against step 544 (artifact 1d6eeb28), paired by item.
  set S = dev-S1, family `main`  : 1,050 items, 72 physical rooms, baseline A544.jsonl (sha256 8347cd84...)
  set R = R0-dev, family `a7`    : 1,781 items, 98 physical rooms, baseline ITEMS.jsonl of Orchard 171197 (a05c2318...)
Per type t and set d: D[d,t] = mean over the set's items of (score of the export - score of step 544).
Statistic of a type both sets hold: P[t] = w[t] * D[S,t] + (1 - w[t]) * D[R,t], with w[t] = n[S,t] / (n[S,t] + n[R,t])
  (every item counts once; the weights are fixed by the registered item sets).
Route planning exists on dev-S1 only: P = D[S,route].  Appearance order exists on R0-dev only: P = D[R,appearance].
Bootstrap: 10,000 joint draws, seed 20261118, random.Random; each draw takes 72 dev-S1 rooms with replacement, then
  98 R0-dev rooms with replacement (rooms in sorted key order, rng.choices on the index range), recomputes every D, every P
  and the unweighted mean of the eight P from the same draw.  A draw in which a set holds no item of some type is redrawn.
Intervals: percentile, linear interpolation (numpy.quantile default), two-sided.
  H1 fires when the interval of some type lies wholly below zero: level 1 - 0.05/8 at step 200, 1 - 0.05/32 later.
  H2 fires when the interval of the mean of the eight lies wholly below zero: level 0.95 at step 200, 0.9875 later.
Nominal bound for an unchanged model: 0.025 + 0.025 at step 200, 0.00625 + 0.00625 at each later look, 0.0875 over four.
Printed beside the rule and stopping nothing: each set's own difference with its 95% interval, and a mark when one set's
interval lies wholly below zero while the pooled test of that type is silent (a loss confined to one set).

usage: pooled_harm_rule.py --step STEP --read ITEMS.jsonl [ITEMS.jsonl ...] --output OUT.json [--calibration]
`--calibration` skips the check that the read's step equals --step (for reads of other legs); such output decides nothing."""
import argparse, collections, hashlib, json, math, random, sys
import numpy as np

C = '/scratch/jjyeung/orch_n30/cont_ops/work'
BASE = dict(
    S=dict(name='dev-S1', family='main', path=C + '/d0/readk/evidence/A544.jsonl',
           sha256='8347cd843f47fe637e770e47544ad49b03e60909e5312260a305319150edb8be',
           items_sha256='22ad2765e8e9a69b7395ff98ff578aaa2fb36d454f5ed4cf47f6b935166412a4', items=1050, rooms=72),
    R=dict(name='R0-dev', family='a7', path=C + '/h1read/kit/build/adff67f7ae9/fetched/x/ITEMS.jsonl',
           sha256='a05c2318e038d6e19c368c309d8cba2cd31047fc6fd7ef124a7b8ac943565233',
           items_sha256='630cd8691a2c36ce5c7f6d58e8d7fcbfff1c01521105b926f2f82c8d16e73e71', items=1781, rooms=98))
ROOM_LIST_SHA256 = '3440f7cfa19d2b70c05d38b949809e33fa90b770bf1ee9c17737fa78abde7e07'
SHARED = ('object_counting', 'object_rel_direction_easy', 'object_rel_direction_medium', 'object_rel_direction_hard',
          'object_rel_distance', 'object_size_estimation')
TYPES = SHARED + ('route_planning', 'obj_appearance_order')          # route: dev-S1 only; appearance: R0-dev only
N_ITEMS = dict(S=dict(zip(SHARED + ('route_planning',), (150,) * 7)),
               R=dict(zip(SHARED + ('obj_appearance_order',), (385, 192, 194, 192, 279, 293, 246))))
SEED, DRAWS = 20261118, 10000
LEVELS = {200: (1 - 0.05 / 8, 0.95), 400: (1 - 0.05 / 32, 0.9875), 600: (1 - 0.05 / 32, 0.9875), 800: (1 - 0.05 / 32, 0.9875)}
META = ('task_type', 'room', 'scene', 'scoring_basis', 'level', 'pair_id', 'count_kind')


def sha(path):
    return hashlib.sha256(open(path, 'rb').read()).hexdigest()


def load(paths, family, types):
    rows = {}
    for p in paths:
        for line in open(p):
            if not line.strip():
                continue
            r = json.loads(line)
            if r.get('family') != family or r.get('task_type') not in types:
                continue
            if r['id'] in rows:
                raise SystemExit('duplicate item %s in family %s' % (r['id'], family))
            s = r.get('score')
            if r.get('budget') != 2048 or type(s) not in (int, float) or not math.isfinite(s) or not 0 <= s <= 1:
                raise SystemExit('invalid scored item %s' % r['id'])
            rows[r['id']] = r
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--step', type=int, choices=sorted(LEVELS), required=True)
    ap.add_argument('--read', nargs='+', required=True)
    ap.add_argument('--output', required=True)
    ap.add_argument('--calibration', action='store_true')
    ap.add_argument('--base-s1', default=BASE['S']['path'])
    ap.add_argument('--base-r0', default=BASE['R']['path'])
    a = ap.parse_args()
    BASE['S']['path'], BASE['R']['path'] = a.base_s1, a.base_r0
    data, room_keys = {}, []
    for d in 'SR':
        b = BASE[d]
        if sha(b['path']) != b['sha256']:
            raise SystemExit('%s baseline is not the registered step-544 read' % b['name'])
        types = tuple(N_ITEMS[d])
        base = load([b['path']], b['family'], types)
        ids = sorted(base)
        key = ''.join('%s\t%s\t%s\n' % (i, base[i]['room'], base[i]['task_type']) for i in ids)
        if hashlib.sha256(key.encode()).hexdigest() != b['items_sha256'] or len(ids) != b['items']:
            raise SystemExit('%s item set differs from the registered one' % b['name'])
        if any(r['step'] != 544 for r in base.values()):
            raise SystemExit('%s baseline is not step 544' % b['name'])
        read = load(a.read, b['family'], types)
        if set(read) != set(ids):
            raise SystemExit('%s: item keys differ (read only %d, baseline only %d)' % (b['name'], len(set(read) - set(ids)), len(set(ids) - set(read))))
        for i in ids:
            for f in META:
                if base[i].get(f) != read[i].get(f):
                    raise SystemExit('%s: paired metadata differs on %s (%s)' % (b['name'], i, f))
        steps = sorted({read[i]['step'] for i in ids})
        if steps != [a.step] and not a.calibration:
            raise SystemExit('%s: read is of step %s, not %d' % (b['name'], steps, a.step))
        rooms = sorted({base[i]['room'] for i in ids})
        if len(rooms) != b['rooms']:
            raise SystemExit('%s room count differs' % b['name'])
        room_keys += [('devS1:' if d == 'S' else 'R0dev:') + r for r in rooms]
        ri = {r: k for k, r in enumerate(rooms)}
        S = np.zeros((len(rooms), len(types)))
        N = np.zeros((len(rooms), len(types)))
        for i in ids:
            t = types.index(base[i]['task_type'])
            S[ri[base[i]['room']], t] += float(read[i]['score']) - float(base[i]['score'])
            N[ri[base[i]['room']], t] += 1
        if [int(x) for x in N.sum(0)] != [N_ITEMS[d][t] for t in types]:
            raise SystemExit('%s per-type item counts differ' % b['name'])
        data[d] = dict(S=S, N=N, K=len(rooms), types=types, steps=steps,
                       base_pct=[100 * sum(float(base[i]['score']) for i in ids if base[i]['task_type'] == t) / N_ITEMS[d][t] for t in types],
                       rooms_per_type=[int((N[:, k] > 0).sum()) for k in range(len(types))])
    if hashlib.sha256(('\n'.join(room_keys) + '\n').encode()).hexdigest() != ROOM_LIST_SHA256:
        raise SystemExit('room list differs from the registered one')
    w = np.array([N_ITEMS['S'][t] / (N_ITEMS['S'][t] + N_ITEMS['R'][t]) for t in SHARED])

    def stat(dS, dR):                       # dS, dR: per-type differences of each set (7,) -> eight P and their mean
        p = np.concatenate([w * dS[:6] + (1 - w) * dR[:6], dS[6:7], dR[6:7]])
        return p

    KS, KR = data['S']['K'], data['R']['K']
    rng = random.Random(SEED)
    P = np.zeros((DRAWS, 8))
    DS = np.zeros((DRAWS, 7))
    DR = np.zeros((DRAWS, 7))
    redrawn = b = 0
    while b < DRAWS:
        cS = np.bincount(rng.choices(range(KS), k=KS), minlength=KS)
        cR = np.bincount(rng.choices(range(KR), k=KR), minlength=KR)
        nS, nR = cS @ data['S']['N'], cR @ data['R']['N']
        if (nS == 0).any() or (nR == 0).any():
            redrawn += 1
            continue
        DS[b], DR[b] = (cS @ data['S']['S']) / nS, (cR @ data['R']['S']) / nR
        P[b] = stat(DS[b], DR[b])
        b += 1
    dS = data['S']['S'].sum(0) / data['S']['N'].sum(0)
    dR = data['R']['S'].sum(0) / data['R']['N'].sum(0)
    p = stat(dS, dR)
    L1, L2 = LEVELS[a.step]

    def ci(x, level):
        lo, hi = np.quantile(x, [(1 - level) / 2, (1 + level) / 2])
        return [round(100 * float(lo), 3), round(100 * float(hi), 3)]

    types = []
    for t, name in enumerate(TYPES):
        iS = data['S']['types'].index(name) if name in data['S']['types'] else None
        iR = data['R']['types'].index(name) if name in data['R']['types'] else None
        row = dict(type=name, weight_dev_s1=round(float(w[t]), 6) if t < 6 else (1.0 if iS is not None else 0.0),
                   pooled_delta_pp=round(100 * float(p[t]), 3), interval_pp=ci(P[:, t], L1), ci95_pp=ci(P[:, t], 0.95))
        row['fires'] = row['interval_pp'][1] < 0
        for d, i, D, dd in (('dev_s1', iS, DS, dS), ('r0_dev', iR, DR, dR)):
            if i is not None:
                k = 'S' if d == 'dev_s1' else 'R'
                row[d] = dict(items=N_ITEMS[k][name], rooms=data[k]['rooms_per_type'][i], step544_pct=round(data[k]['base_pct'][i], 2),
                              delta_pp=round(100 * float(dd[i]), 3), ci95_pp_printed_only=ci(D[:, i], 0.95))
        types.append(row)
    mean = dict(delta_pp=round(100 * float(p.mean()), 3), interval_pp=ci(P.mean(1), L2), ci95_pp=ci(P.mean(1), 0.95))
    mean['fires'] = mean['interval_pp'][1] < 0
    h1 = [r['type'] for r in types if r['fires']]
    # printed mark, stops nothing: one set's own 95% interval lies wholly below zero while the pooled test of the type is silent
    marks = ['%s on %s: %+.2f %s' % (r['type'], BASE[k]['name'], r[d]['delta_pp'], r[d]['ci95_pp_printed_only'])
             for r in types if not r['fires'] for d, k in (('dev_s1', 'S'), ('r0_dev', 'R'))
             if d in r and r[d]['ci95_pp_printed_only'][1] < 0]
    out = dict(rule='R1 pooled harm rule v1', set_confined_loss_marks_printed_only=marks, step=a.step, calibration=a.calibration, read_steps=dict(dev_s1=data['S']['steps'], r0_dev=data['R']['steps']),
               levels=dict(H1=L1, H2=L2), seed=SEED, draws=DRAWS, redrawn=redrawn,
               baselines={BASE[d]['name']: dict(path=BASE[d]['path'], sha256=BASE[d]['sha256'], items_sha256=BASE[d]['items_sha256']) for d in 'SR'},
               room_list_sha256=ROOM_LIST_SHA256, reads={q: sha(q) for q in a.read}, script_sha256=sha(sys.argv[0]),
               types=types, mean_of_eight=mean, H1_fires_on=h1, H2_fires=mean['fires'],
               verdict=('STOP' if (h1 or mean['fires']) else 'SILENT') if not a.calibration else
                       ('would STOP' if (h1 or mean['fires']) else 'would stay SILENT') + ' (calibration read, decides nothing)')
    json.dump(out, open(a.output, 'w'), indent=1)
    print('%-30s %7s %7s %8s  %-20s %s' % ('type', 'dev-S1', 'R0-dev', 'pooled', 'interval at H1 level', 'fires'))
    for r in types:
        print('%-30s %7s %7s %+8.2f  [%+7.2f, %+7.2f]   %s' % (
            r['type'], '%+.2f' % r['dev_s1']['delta_pp'] if 'dev_s1' in r else '-', '%+.2f' % r['r0_dev']['delta_pp'] if 'r0_dev' in r else '-',
            r['pooled_delta_pp'], r['interval_pp'][0], r['interval_pp'][1], 'FIRES' if r['fires'] else ''))
    print('%-30s %7s %7s %+8.2f  [%+7.2f, %+7.2f]   %s' % ('mean of eight (H2 level)', '', '', mean['delta_pp'], mean['interval_pp'][0], mean['interval_pp'][1], 'FIRES' if mean['fires'] else ''))
    for m in marks:
        print('mark (printed, stops nothing): loss on one set only,', m)
    print('verdict:', out['verdict'])


if __name__ == '__main__':
    main()
