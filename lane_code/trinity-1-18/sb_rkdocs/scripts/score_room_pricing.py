"""Reference scorer for the room-head pricing (KIT_SPEC_room_pricing.md, section 6).

Usage: use price.py for the single registered R0-dev comparison.
  python score_room_pricing.py --direct  file written by extract_direct.py (labels, the direct answer and its stored score per item)
--pred    one JSON object per line: {"id": item id, "arm": name, "area_m2": float or null,
          "refusal": code or null}; every arm must carry all items of a set it reports on
Scoring: the arm's answer is area_m2 converted to the item's unit (ft2 = m2 * 10.7639104167),
rounded to 2 decimals as the room response prints it; refusals and missing areas score 0.
MRA is the tree's official_mra (ten thresholds 0.50 to 0.95, relative error <= 1 - threshold). Intervals are the
accepted reader scorer's: whole physical rooms resampled 10,000 times with random.Random(17),
ratio estimator, percentile bounds. Python 3.6+, numpy only.
"""
import argparse, json, math, random, sys
from common import sha, BASE
from collections import defaultdict
import numpy as np

FT2 = 10.7639104167


def mra(pred, gt, start=0.5, end=0.95, interval=0.05):
    """Same arithmetic as evalpath/official.py official_mra (sha256 a5d6d79f...), which scores the direct answers."""
    if pred is None or gt is None or not math.isfinite(pred) or not math.isfinite(gt):
        return 0.0
    if gt == 0.0:
        return 1.0 if pred == 0.0 else 0.0
    num_pts = int((end - start) / interval + 2)
    conf = [start + i * (end - start) / (num_pts - 1) for i in range(num_pts)]
    rel_err = abs(pred - gt) / abs(gt)
    return sum(1.0 if rel_err <= (1.0 - c) else 0.0 for c in conf) / len(conf)


def bootstrap(pairs, levels=(0.95,)):
    groups = defaultdict(list)
    for room, value in pairs:
        groups[room].append(float(value))
    grouped = [(sum(groups[k]), len(groups[k])) for k in sorted(groups)]
    rng, samples = random.Random(17), []
    for _ in range(10000):
        draw = rng.choices(grouped, k=len(grouped))
        samples.append(sum(v[0] for v in draw) / sum(v[1] for v in draw))
    out = dict(value=100 * sum(v[0] for v in grouped) / sum(v[1] for v in grouped),
               n=sum(v[1] for v in grouped), rooms=len(grouped))
    for level in levels:
        tail = (1 - level) / 2
        out['ci%g' % (100 * level)] = [100 * float(x) for x in np.quantile(samples, [tail, 1 - tail])]
    return out


def answer(area_m2, unit):
    if area_m2 is None:
        return None
    return round(float(area_m2) * (FT2 if unit == 'ft2' else 1.0), 2)


def describe(rows, key):
    rel = [(r[key] - r['gt']) / r['gt'] for r in rows if r[key] is not None]
    if not rel:
        return dict(answered=0)
    return dict(answered=len(rel), median_rel=float(np.median(rel)), median_abs_rel=float(np.median(np.abs(rel))),
                within10=float(np.mean(np.abs(rel) < .10)), within25=float(np.mean(np.abs(rel) < .25)))


def score(direct_rows, pred_rows, primary, margin, levels=(0.95,)):
    if len({r['id'] for r in direct_rows}) != len(direct_rows):
        raise ValueError('duplicate baseline IDs')
    for r in direct_rows:
        if not math.isfinite(r['direct_mra']) or abs(mra(r['direct'], r['gt'])-r['direct_mra']) > 1e-9:
            raise ValueError('invalid cached baseline score: '+r['id'])
    required={r['id'] for r in direct_rows if r['set']=='R0-dev'}
    if not required or not primary or {p['id'] for p in pred_rows if p['arm']==primary} & required != required:
        raise ValueError('missing primary or primary items')
    for p in pred_rows:
        if not p.get('refusal') and (p.get('area_m2') is None or not math.isfinite(p['area_m2']) or p['area_m2'] < 0):
            raise ValueError('invalid non-refused prediction')
    base = {r['id']: r for r in direct_rows}
    arms = defaultdict(dict)
    for p in pred_rows:
        if p['id'] not in base:
            sys.exit('prediction for an item outside the direct file: ' + p['id'])
        if p['id'] in arms[p['arm']]:
            sys.exit('duplicate prediction %s %s' % (p['arm'], p['id']))
        arms[p['arm']][p['id']] = p
    table = dict(margin=margin, primary=primary, sets={})
    for name in sorted({r['set'] for r in direct_rows}):
        ids = sorted(i for i, r in base.items() if r['set'] == name)
        rows = [base[i] for i in ids]
        direct = bootstrap([(r['room'], r['direct_mra']) for r in rows], levels)
        block = dict(direct=dict(direct, **describe([dict(r, a=r['direct']) for r in rows], 'a')), arms={})
        for arm in sorted(arms):
            have = [i for i in ids if i in arms[arm]]
            if not have:
                continue
            if len(have) != len(ids):
                sys.exit('arm %s covers %d of %d %s items' % (arm, len(have), len(ids), name))
            scored = []
            for r in rows:
                p = arms[arm][r['id']]
                a = None if p.get('refusal') else answer(p.get('area_m2'), r['unit'])
                scored.append(dict(r, a=a, arm_mra=mra(a, r['gt'])))
            rec = bootstrap([(s['room'], s['arm_mra']) for s in scored], levels)
            rec['paired_minus_direct'] = bootstrap([(s['room'], s['arm_mra'] - s['direct_mra']) for s in scored], levels)
            rec['refusals'] = sum(s['a'] is None for s in scored)
            rec.update(describe(scored, 'a'))
            order = sorted(scored, key=lambda s: s['gt'])
            third = len(order) // 3
            rec['by_label_tercile'] = [dict(label_range=[part[0]['gt'], part[-1]['gt']],
                                            arm=100 * float(np.mean([s['arm_mra'] for s in part])),
                                            direct=100 * float(np.mean([s['direct_mra'] for s in part])))
                                       for part in (order[:third], order[third:2 * third], order[2 * third:])]
            block['arms'][arm] = rec
        table['sets'][name] = block
    r0 = table['sets'].get('R0-dev', {})
    if primary and primary in r0.get('arms', {}):
        arm, bar = r0['arms'][primary], r0['direct']['value'] + margin
        lower = arm['paired_minus_direct']['ci%g' % (100 * levels[0])][0]
        table['decision'] = dict(bar=bar, primary_mra=arm['value'], paired_lower=lower,
                                 verdict='PASS' if arm['value'] >= bar and lower > 0 else
                                 'NEAR' if arm['value'] >= bar else 'FAIL')
    return table


def render(table):
    lines = []
    for name, block in table['sets'].items():
        d = block['direct']
        lines.append('## %s (%d items, %d rooms)' % (name, d['n'], d['rooms']))
        lines.append('direct            %6.2f [%6.2f, %6.2f]  median rel %+.3f  median |rel| %.3f' % (
            d['value'], d['ci95'][0], d['ci95'][1], d.get('median_rel', float('nan')), d.get('median_abs_rel', float('nan'))))
        for arm, r in block['arms'].items():
            p = r['paired_minus_direct']
            lines.append('%-17s %6.2f [%6.2f, %6.2f]  minus direct %+6.2f [%+6.2f, %+6.2f]  refusals %d  median rel %+.3f  median |rel| %.3f' % (
                arm, r['value'], r['ci95'][0], r['ci95'][1], p['value'], p['ci95'][0], p['ci95'][1], r['refusals'],
                r.get('median_rel', float('nan')), r.get('median_abs_rel', float('nan'))))
    if 'decision' in table:
        lines.append('DECISION %(verdict)s: primary %(primary_mra).2f against bar %(bar).2f; paired lower bound %(paired_lower)+.2f' % table['decision'])
    return '\n'.join(lines) + '\n'


def self_test(direct_rows):
    assert mra(10, 10) == 1.0 and mra(9.4, 10) == 0.9 and mra(4.9, 10) == 0.0 and mra(None, 10) == 0.0
    assert mra(12.6, 10) == 0.5 and mra(5.1, 10) == 0.1 and mra(float('nan'), 10) == 0.0
    for r in direct_rows:
        assert abs(mra(r['direct'], r['gt']) - r['direct_mra']) < 1e-9, r['id']
    # An arm that repeats the direct answers must reproduce the direct row and a zero paired difference.
    echo = [dict(id=r['id'], arm='echo', area_m2=r['direct'] / (FT2 if r['unit'] == 'ft2' else 1.0), refusal=None)
            for r in direct_rows]
    oracle = [dict(id=r['id'], arm='label', area_m2=r['gt'] / (FT2 if r['unit'] == 'ft2' else 1.0), refusal=None)
              for r in direct_rows]
    refuse = [dict(id=r['id'], arm='refuse', area_m2=None, refusal='room_no_floor_seen') for r in direct_rows]
    t = score(direct_rows, echo + oracle + refuse, 'label', 5)
    for name, block in t['sets'].items():
        e, o, z = block['arms']['echo'], block['arms']['label'], block['arms']['refuse']
        assert abs(e['value'] - block['direct']['value']) < 0.75, (name, e['value'], block['direct']['value'])
        assert abs(o['value'] - 100) < 1e-9 and z['value'] == 0 and z['refusals'] == block['direct']['n']
    assert t['decision']['verdict'] == 'PASS'
    assert score(direct_rows, echo, 'echo', 5)['decision']['verdict'] == 'FAIL'
    print(render(t), end='')
    print('self-test PASS')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--direct', required=True); ap.add_argument('--pred'); ap.add_argument('--primary')
    ap.add_argument('--margin', type=float, default=5.0); ap.add_argument('--out'); ap.add_argument('--self-test', action='store_true')
    a = ap.parse_args()
    if a.pred is not None: raise PermissionError('R0-dev scoring is available only through price.py and its one-look latch')
    if not a.self_test: raise PermissionError('use price.py; only --self-test is public')
    if sha(a.direct) != BASE: raise ValueError('baseline is not the frozen step-200 file')
    direct_rows = json.load(open(a.direct))['rows']
    if a.self_test:
        return self_test(direct_rows)


if __name__ == '__main__':
    main()
