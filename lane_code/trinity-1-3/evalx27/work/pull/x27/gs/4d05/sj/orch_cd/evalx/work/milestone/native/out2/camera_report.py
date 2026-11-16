from collections import defaultdict

import numpy as np

from common import OUT, checked, load
from camera_cohort import FROZEN_COHORT_SHA, TYPES, load_tasks


DRAWS = 10000
SEED = 20261113


def summarize(tasks, arms, shortcuts, draws=DRAWS, seed=SEED):
    columns = ['routed', 'scripted']
    if tasks:
        columns += sorted(shortcuts[tasks[0]['id']]['scores'])
    grouped = defaultdict(list)
    values = []
    for task in tasks:
        key = 'devrows:'+task['id']
        row = [arms[a][key]['scores']['answer'] for a in ('unflagged', 'scripted')]
        row += [shortcuts[task['id']]['scores'][name] for name in columns[2:]]
        values.append(row)
        grouped[task['native']].append(row)
    result = dict(items=len(tasks), captures=len(grouped), interval_method='paired capture-cluster bootstrap',
                  draws=draws, seed=seed, confidence=.95, scores={})
    if not tasks:
        return dict(result, qualification='NOT MEASURABLE: empty diagnostic subset')
    scores = 100*np.array(values).mean(axis=0)
    boot = None
    if len(grouped)>1:
        counts = np.array([len(rows) for _, rows in sorted(grouped.items())])
        sums = np.array([np.array(rows).sum(axis=0) for _, rows in sorted(grouped.items())])
        weights = np.random.default_rng(seed).multinomial(len(counts), np.full(len(counts), 1/len(counts)), size=draws)
        boot = 100*(weights@sums)/(weights@counts)[:, None]
    def interval(value):
        return np.quantile(value, [.025, .975]).tolist() if value is not None else None
    for i, name in enumerate(columns):
        result['scores'][name] = dict(score_pct=float(scores[i]), ci95_pct=interval(boot[:, i] if boot is not None else None))
    result['routed_minus_scripted_pp'] = float(scores[0]-scores[1])
    result['routed_minus_scripted_ci95_pp'] = interval(boot[:, 0]-boot[:, 1] if boot is not None else None)
    gap_index = columns.index('frame_gap')
    for i, arm in enumerate(('routed', 'scripted')):
        result['scores'][arm].update(frame_gap_rule_score_pct=float(scores[gap_index]),
            minus_frame_gap_rule_pp=float(scores[i]-scores[gap_index]),
            minus_frame_gap_rule_ci95_pp=interval(boot[:, i]-boot[:, gap_index] if boot is not None else None))
    if boot is None:
        result['qualification'] = 'Intervals not measurable with fewer than two captures'
    return result


def decorate(report, bundle, inputs):
    if not inputs.get('camera_cohort'):
        return report
    tasks = load_tasks(inputs['camera_cohort'], inputs['frames'])
    shortcut = load(OUT/'CAMERA_SHORTCUTS.json')
    receipt = load(checked(inputs['camera_cohort']))
    if (shortcut.get('schema')!='legs1-camera-shortcuts-v1'
            or shortcut.get('cohort_sha256')!=FROZEN_COHORT_SHA
            or shortcut['tasks']['sha256']!=receipt['tasks']['sha256']
            or set(shortcut['by_id'])!={t['id'] for t in tasks}):
        raise ValueError('Camera shortcut binding differs')
    arms = {name: {r['key']: r for r in rows} for name, rows in bundle['arms'].items()}
    for task in tasks:
        for arm in arms.values():
            row = arm['devrows:'+task['id']]
            if (row['question_type'], row['room'], row['stratum']) != (
                    task['question_type'], task['room'], task['stratum']):
                raise ValueError('Camera diagnostic row differs from its frozen task')
    report['camera_cohort'] = dict(sha256=FROZEN_COHORT_SHA, items=450,
        qualification='Development change-from-parent read; inherited checkpoint exposure is not removed',
        sampling='Fixed answer-stratified hash sample, not the training answer distribution',
        direction_options='A backward, B right, C left, D forward; training uses 84 option lists',
        shortcut_scope=shortcut['scope'], intervals='Capture-clustered, never item-iid or physical-room clustered',
        stop_rule='Overall R1 and script-answered R1 remain authoritative; subsets are diagnostics only')
    for typ in TYPES:
        selected = [t for t in tasks if t['question_type']==typ]
        summarize_subset = lambda ts: summarize(ts, arms, shortcut['by_id'], draws=DRAWS)
        diagnostic = dict(overall=summarize_subset(selected),
            passed_geometry=summarize_subset([t for t in selected
                if not arms['unflagged']['devrows:'+t['id']].get('geometry_refusal')]),
            script_answered=summarize_subset([t for t in selected if not arms['scripted']['devrows:'+t['id']]['no_answer']]))
        if typ=='camera_rotation':
            diagnostic['abs_angle_ge_10_deg'] = summarize_subset([t for t in selected if abs(float(t['answer']))>=10])
            diagnostic['by_selection_stratum'] = {str(s): summarize_subset([t for t in selected if t['selection_stratum']==s])
                                                   for s in sorted({t['selection_stratum'] for t in selected})}
            diagnostic['near_zero'] = dict(abs_angle_lt10_items=sum(abs(float(t['answer']))<10 for t in selected),
                                           exact_zero_items=sum(float(t['answer'])==0 for t in selected),
                                           training_abs_angle_lt10_pct=6.3)
        if typ=='camera_movement_direction':
            diagnostic['by_answer_option'] = {option: summarize_subset([t for t in selected if t['answer']==option.split('.')[0]])
                                                for option in selected[0]['options']}
        report['per_type'][typ]['camera_diagnostics'] = diagnostic
    return report
