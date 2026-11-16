import argparse
from collections import defaultdict
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import numpy as np


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from direct import A, validate

TYPES = A.R4.CAMERA_TYPES
SEED = 20261113
DRAWS = 10000


def summarize(tasks, arms, draws=DRAWS):
    names = sorted(arms)
    result = dict(items=len(tasks), captures=len({t['native'] for t in tasks}), scores={},
                  interval_method='paired capture-cluster bootstrap; item-weighted mean',
                  draws=draws, seed=SEED)
    if not tasks:
        return dict(result, qualification='NOT MEASURABLE: empty subset')
    groups = defaultdict(list)
    for task in tasks:
        key = 'devrows:'+task['id']
        values = [arms[name][key]['scores']['answer'] for name in names]
        if any(not isinstance(v, (float, int)) or not np.isfinite(v) or not 0<=v<=1 for v in values):
            raise ValueError('Missing or invalid camera score')
        groups[task['native']].append(values)
    counts = np.array([len(rows) for _, rows in sorted(groups.items())])
    sums = np.array([np.array(rows).sum(axis=0) for _, rows in sorted(groups.items())])
    point = 100*sums.sum(axis=0)/counts.sum()
    boot = None
    if len(groups)>1:
        weights = np.random.default_rng(SEED).multinomial(len(groups), np.full(len(groups), 1/len(groups)), size=draws)
        boot = 100*(weights@sums)/(weights@counts)[:, None]
    for i, name in enumerate(names):
        result['scores'][name] = dict(score_pct=float(point[i]),
            ci95_pct=np.quantile(boot[:, i], [.025, .975]).tolist() if boot is not None else None)
    result['minus_f17_pp'] = {}
    if 'f17_ON16k' in names:
        j = names.index('f17_ON16k')
        for i, name in enumerate(names):
            if i != j:
                result['minus_f17_pp'][name] = dict(delta_pp=float(point[i]-point[j]),
                    ci95_pp=np.quantile(boot[:, i]-boot[:, j], [.025, .975]).tolist() if boot is not None else None)
    if boot is None:
        result['qualification'] = 'Intervals unavailable with fewer than two captures'
    return result


def load_merge(path, model, arm):
    cfg = json.loads((Path(path)/'request.json').read_text())
    validate(cfg)
    spec = importlib.util.spec_from_file_location('verified_decision',
        '/scratch/jjyeung/orch_cd/legs1_reads/out/decision.py')
    decision = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(decision)
    value = decision.load_merge(path, arm=arm, expected_model=model)
    return {r['key']: r for r in value['rows']}


def report(cp1, f17):
    _, pins, tasks, _ = A.R4.payload(ROOT/'payload')
    arms = {f'CP1_{arm}': load_merge(cp1, 'cp1m200', arm) for arm in ('ON16k', 'B2048', 'B4096')}
    arms['f17_ON16k'] = load_merge(f17, 'f17', 'ON16k')
    expected = {'devrows:'+t['id'] for t in tasks}
    for name, values in arms.items():
        if set(values) != expected:
            raise ValueError('Camera report membership differs: '+name)
    per_type = {}
    for typ in TYPES:
        selected = [t for t in tasks if t['question_type']==typ]
        result = dict(overall=summarize(selected, arms))
        if typ=='camera_rotation':
            result['abs_angle_ge_10_deg'] = summarize([t for t in selected if abs(float(t['answer']))>=10], arms)
            result['by_selection_stratum'] = {str(s):summarize([t for t in selected if t['selection_stratum']==s], arms)
                for s in sorted({t['selection_stratum'] for t in selected})}
        if typ=='camera_movement_direction':
            result['by_answer_option'] = {option:summarize([t for t in selected if t['answer']==option.split('.')[0]], arms)
                for option in selected[0]['options']}
        per_type[typ] = result
    return dict(schema='devs1-camera-direct-report-v1', cohort_sha256=A.R4.CAMERA_COHORT_SHA256,
        tasks_sha256=pins['TASKS.jsonl'], decision_arm='CP1_B2048 versus f17_ON16k',
        protocol=dict(cp1='32 anchors, each duplicated into 64 input frames; greedy ON16k; derived thinking budgets 2048/4096',
                      f17='32 spread input frames; greedy ON16k'),
        scope='Frozen answer-stratified development cohort; not a benchmark or a training-distribution score',
        direction_options='A backward, B right, C left, D forward; letter and direction are confounded',
        baseline_native_routed='NOT MEASURABLE', overall_diagnostic=summarize(tasks, arms),
        per_type=per_type, source_merges={name:dict(path=str(Path(path).resolve()),
            complete_sha256=A.sha(Path(path)/'MERGE_COMPLETE.json')) for name,path in [('cp1',cp1),('f17',f17)]},
        code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for name in ('cp1', 'f17', 'output'):
        parser.add_argument('--'+name, required=True)
    args = parser.parse_args()
    result = report(args.cp1, args.f17)
    output = Path(args.output)
    with output.open('x') as stream:
        stream.write(json.dumps(result, indent=2, sort_keys=True)+'\n')
    print(output)
