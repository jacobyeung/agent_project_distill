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
BASELINE_AWAY = dict(zip(LEVELS, (38, 20, 6)))
READ_STEPS = (100, 200, 400, 600, 800, 1000)
FINAL_STEP = 1000
PREVIOUS_STEP = {400: 200, 600: 400, 800: 600, FINAL_STEP: 800}
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


def stop_rule(step, f1, f2_fail, away, away544, previous=None):
    """D0_STOP_RULE_20261116 items 1–3; point F2 never enters this decision."""
    if step == 100:
        return dict(verdict=None, reasons=['step 100 gives no verdict'])
    if step == FINAL_STEP:
        decision = 'FAIL' if f2_fail else 'PASS'
        return dict(verdict='FINAL', f2_decision=decision,
                    reasons=['final export: F2 '+decision+'; the leg has ended'])
    reasons = ['F1 '+task+': paired-difference upper bound '+str(value['ci95_pp'][1])+' < 0'
               for task, value in f1.items() if value['ci95_pp'][1] < 0]
    if step == 200:
        for level in LEVELS:
            if away[level] <= away544[level]:
                reasons.append(f'facing {level}: away200={away[level]} <= away544={away544[level]}')
    else:
        below = [level for level in LEVELS if away[level] < previous[level]]
        if len(below) >= 2 and f2_fail:
            for level in below:
                reasons.append(f'facing {level}: away{step}={away[level]} < '
                               f'away{PREVIOUS_STEP[step]}={previous[level]}; '
                               'at least two levels fell and F2 has not passed')
    return dict(verdict='STOP' if reasons else 'CONTINUE',
                reasons=reasons or ['no stop condition met'])


def evaluate(a, b, step, prev=None, strict=True):
    if step not in READ_STEPS:
        raise ValueError('Step must be one of '+str(READ_STEPS))
    index(a, 544); index(b, step)
    keep = lambda rows: [r for r in rows if r['family'] != 'camera']
    a, b = keep(a), keep(b)
    align(a, b)
    if strict:
        inventory = json.loads((Path(__file__).parent/'kit/reader/e193_items.json').read_text())['families']
        for family in ('main', 'away', 'forward'):
            actual = {r['id']: r['task_type'] for r in b if r['family'] == family}
            if actual != inventory[family]['items']:
                raise ValueError('Accepted inventory differs')
    if step in PREVIOUS_STEP:
        if prev is None:
            raise ValueError(f'--prev step {PREVIOUS_STEP[step]} is required for step {step}')
        index(prev, PREVIOUS_STEP[step])
        prev = keep(prev)
        align(b, prev)
    elif prev is not None:
        raise ValueError('--prev is only accepted at steps 400, 600, 800 and the final export')
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
    for level in LEVELS:
        if not math.isclose(base[level]['accuracy_pct'], BASELINE_AWAY[level], rel_tol=0, abs_tol=1e-12):
            raise ValueError('Step-544 away point values must equal 38 / 20 / 6')
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
    means = lambda values: {k: values[k]['accuracy_pct'] for k in LEVELS}
    previous = ({k: accuracy(select(prev, 'away', level=k)) for k in LEVELS}
                if prev is not None else None)
    result['f2']['away_previous'] = previous
    reference = means(previous) if previous is not None else means(base)
    result['facing_comparison'] = dict(reference_step=PREVIOUS_STEP.get(step, 544),
        levels={k: dict(current_pct=means(away)[k], previous_pct=reference[k],
                        below=means(away)[k] < reference[k]) for k in LEVELS})
    result.update(stop_rule(step, f1, f2_fail, means(away), means(base),
                            means(previous) if previous is not None else None))
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--a', required=True, help='Accepted step-544 normalized JSONL')
    p.add_argument('--b', required=True, help='Milestone ITEMS.jsonl')
    p.add_argument('--step', type=int, choices=READ_STEPS, required=True)
    p.add_argument('--prev', help='Previous read ITEMS.jsonl; required at 400/600/800/1000')
    p.add_argument('--output')
    args = p.parse_args()
    result = evaluate(load(args.a), load(args.b), args.step, load(args.prev) if args.prev else None)
    text = json.dumps(result, indent=2, sort_keys=True, allow_nan=False)+'\n'
    if args.output:
        Path(args.output).write_text(text)
    print(text, end='')


if __name__ == '__main__':
    main()
