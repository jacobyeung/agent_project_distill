"""Paired room-bootstrap metrics and the registered milestone stop rules.

Scores are fractions; all displayed accuracies and intervals are percentages.
The exact r5 room bootstrap is called with B first to obtain B minus A.
"""
import argparse
import json
import math
from pathlib import Path
from room_bootstrap import paired

LEVELS = ('easy', 'medium', 'hard')
THRESHOLDS = dict(zip(LEVELS, (54, 40, 36)))
# The two comparative variants are information only, outside registered F1.
F1_TYPES = ('route_planning', 'object_counting',
            'object_rel_direction_easy', 'object_rel_direction_medium',
            'object_rel_direction_hard', 'object_rel_distance',
            'object_size_estimation')
F1_INFORMATION_TYPES = ('relative_count', 'relative_size_object')


def load(path):
    with Path(path).open() as stream:
        return [json.loads(line) for line in stream if line.strip()]


def index(rows, step=None):
    result = {}
    for r in rows:
        if r['family'] not in ('main','away','forward','camera'):
            raise ValueError('Unknown family')
        key = (r['family'], r['id'])
        if key in result:
            raise ValueError('Duplicate item')
        if (r['budget'] != 2048 or not isinstance(r['score'], (float, int))
                or not math.isfinite(r['score']) or not 0 <= r['score'] <= 1
                or not r['room'] or not r['scene']):
            raise ValueError('Invalid B2048 record')
        if step is not None and r['step'] != step:
            raise ValueError('Wrong step')
        result[key] = r
    return result


def align(a, b):
    aa, bb = index(a), index(b)
    if not aa or aa.keys() != bb.keys():
        raise ValueError('Paired membership differs')
    for key, x in aa.items():
        y = bb[key]
        for field in ('task_type', 'level', 'room', 'scene', 'scoring_basis', 'pair_id', 'count_kind'):
            if x.get(field) != y.get(field):
                raise ValueError('Paired metadata differs: '+field)
    return aa, bb


def bootstrap(a, b=None):
    if not a:
        raise ValueError('Missing required task or level')
    def convert(rows):
        return [dict(key=r['family']+':'+r['id'], room=r['room'], stratum=r['scoring_basis'],
                     question_type=r['task_type'], scores=dict(value=r['score'])) for r in rows]
    zero = [dict(r, score=0) for r in a]
    return paired(convert(a), convert(zero if b is None else b), 'value', replicates=10000, seed=17)


def accuracy(rows):
    out = bootstrap(rows)
    out['accuracy_pct'] = out.pop('delta_pp')
    out['ci95_pct'] = out.pop('ci95_pp')
    return out


def twins(rows):
    aa, ff = {}, {}
    for r in rows:
        if r['family'] not in ('away', 'forward'):
            continue
        target = aa if r['family'] == 'away' else ff
        pair = r['pair_id']
        if not pair or pair in target or r['level'] not in LEVELS:
            raise ValueError('Invalid twin pairing')
        target[pair] = r
    if not aa or aa.keys() != ff.keys():
        raise ValueError('Missing twin')
    for key, a in aa.items():
        if any(a[k] != ff[key][k] for k in ('level', 'room', 'scene')):
            raise ValueError('Twin metadata differs')
    # Missing answers are reported separately; only parsed answers count alike.
    alike = sum(a['answer_content'] is not None and a['answer_content'] == ff[k]['answer_content'] for k, a in aa.items())
    return dict(pairs=len(aa), alike_pairs=alike, alike_pct=100*alike/len(aa),
                unparsed_pairs=sum(a['answer_content'] is None or ff[k]['answer_content'] is None for k, a in aa.items()))


def stop_rule(f1_fail, f2_fail, away200, away100, away544):
    if f1_fail:
        return 'STOP'
    if not f2_fail:
        return 'CONTINUE'
    if away100 is None:
        raise ValueError('Step-100 results are required for the trend exception')
    rising = sum(away200[k] > away100[k] for k in LEVELS) >= 2
    above = all(away200[k] > away544[k] for k in LEVELS)
    return 'CONTINUE_TO_400' if rising and above else 'STOP'


def evaluate(a, b, step, m100=None, strict=True):
    if step not in (100, 200, 400):
        raise ValueError('Step must be 100, 200 or 400')
    index(a, 544); index(b, step)
    keep = lambda rows: [r for r in rows if r['family'] != 'camera']
    a, b = keep(a), keep(b)
    if m100 is not None:
        m100 = keep(m100)
    align(a, b)
    if strict:
        inventory = json.loads((Path(__file__).parent/'kit/reader/e193_items.json').read_text())['families']
        for family in ('main', 'away', 'forward'):
            actual = {r['id']: r['task_type'] for r in b if r['family'] == family}
            if actual != inventory[family]['items']:
                raise ValueError('Accepted inventory differs')
    if m100 is not None:
        index(m100, 100); align(a, m100)
    def select(rows, family='main', task=None, level=None):
        return [r for r in rows if r['family'] == family and (task is None or r['task_type'] == task)
                and (level is None or r['level'] == level)]
    f1 = {t: bootstrap(select(b, task=t), select(a, task=t)) for t in F1_TYPES}
    for value in f1.values():
        value['fail'] = value['ci95_pp'][1] < 0
    information = {t: bootstrap(select(b, task=t), select(a, task=t))
                   for t in F1_INFORMATION_TYPES}
    away = {level: accuracy(select(b, 'away', level=level)) for level in LEVELS}
    base = {level: accuracy(select(a, 'away', level=level)) for level in LEVELS}
    for level, value in away.items():
        value.update(threshold_pct=THRESHOLDS[level], fail=value['ci95_pct'][0] <= THRESHOLDS[level],
                     point_estimate_fail=value['accuracy_pct'] < THRESHOLDS[level])
    pairs, base_pairs = twins(b), twins(a)
    toward = bootstrap(select(b, 'forward'), select(a, 'forward'))
    toward['fail'] = toward['ci95_pp'][1] < 0
    f1_fail = any(x['fail'] for x in f1.values())
    f2_fail = any(x['fail'] for x in away.values()) or pairs['alike_pct'] > 20 or toward['fail']
    point_fail = any(x['point_estimate_fail'] for x in away.values()) or pairs['alike_pct'] > 20 or toward['fail']
    guards = {}
    for kind, constant, threshold in (('total', 7, 46.30), ('single', 2, 61.87)):
        chosen = [r for r in b if r['family'] == 'main' and r.get('count_kind') == kind]
        guards[kind] = dict(constant=constant, constant_accuracy_pct=threshold, items=len(chosen),
            accuracy_pct=100*sum(r['score'] for r in chosen)/len(chosen) if chosen else None,
            status='AVAILABLE' if chosen else 'UNAVAILABLE_ON_ACCEPTED_INVENTORY')
        guards[kind]['passes'] = ((guards[kind]['accuracy_pct'] > threshold if kind == 'total'
                                  else guards[kind]['accuracy_pct'] >= threshold) if chosen else None)
    result = dict(step=step, budget=2048, bootstrap_draws=10000, seed=17, f1=f1, f1_fail=f1_fail,
        f1_information_only=information,
        f2=dict(away=away, away544=base, pairs=pairs, pairs544=base_pairs, toward_delta=toward),
        f2_verdict_reading='TRACE_RULING_2.7_LOWER_BOUND',
        f2_point_estimate_information_only=dict(fail=point_fail),
        f2_fail=f2_fail, guards=guards, f3_f4='NOT_EVALUATED_BY_DIRECT_READ; NON_STOPPING')
    if step == 200:
        means = lambda values: {k: values[k]['accuracy_pct'] for k in LEVELS}
        earlier = {k: accuracy(select(m100, 'away', level=k)) for k in LEVELS} if m100 is not None else None
        result['f2']['away100'] = earlier
        result['verdict'] = stop_rule(f1_fail, f2_fail, means(away), means(earlier) if earlier else None, means(base))
        result['f2_point_estimate_information_only']['verdict'] = stop_rule(
            f1_fail, point_fail, means(away), means(earlier) if earlier else None, means(base))
    elif step == 400:
        result['verdict'] = 'STOP' if f2_fail else 'CONTINUE'
        result['f2_point_estimate_information_only']['verdict'] = 'STOP' if point_fail else 'CONTINUE'
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--a', required=True, help='Accepted step-544 normalized JSONL')
    p.add_argument('--b', required=True, help='Milestone ITEMS.jsonl')
    p.add_argument('--step', type=int, choices=(100, 200, 400), required=True)
    p.add_argument('--m100', help='Step-100 ITEMS.jsonl for the trend exception')
    p.add_argument('--output')
    args = p.parse_args()
    result = evaluate(load(args.a), load(args.b), args.step, load(args.m100) if args.m100 else None)
    text = json.dumps(result, indent=2, sort_keys=True, allow_nan=False)+'\n'
    if args.output:
        Path(args.output).write_text(text)
    print(text, end='')


if __name__ == '__main__':
    main()
