#!/usr/bin/env python3
"""CPU-only ledger of existing captures. Run with the approved isolated Python."""
import os
for _key in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[_key] = '1'
os.environ['CUDA_VISIBLE_DEVICES'] = ''
import argparse
import ast
from collections import Counter
import gzip
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import random
import re
import statistics
from typing import Optional
import numpy as np

ROOT = Path(__file__).resolve().parent
BASE = Path('/scratch/jjyeung/orch_n30')
CAP = BASE / 'cont_ops24_c/cap'
CODE = BASE / 'cont_ops24_c/gbuild'
ITEMS = BASE / 'grd_funnel1/kit/rerun2/items544.json'
CORPUS = ROOT / 'in/corpus'
READS = {
    200: ('673bc60f_s200_R0dev_D580_173243', '673bc60f_s200_devS1R0_direct_a8102c3207b'),
    400: ('6ed2c7aa_s400_R0dev_D580_173241', '6ed2c7aa_s400_devS1R0_direct_a59a7bff4c4'),
}
SEED, DRAWS = 20261120, 10000
STAGES = ['S0', 'S1', 'S2', 'S3', 'S4', 'S5', 'no-GT', 'censored']
DATASETS = ['all', 'arkitscenes', 'scannet', 'scannetppv2', 'ScanNet+ScanNet++']
INPUT_HASHES = {}


def pin(path):
    path = Path(path).resolve()
    if not str(path).startswith('/scratch/'):
        raise ValueError('Only local scratch inputs are permitted')
    if str(path) not in INPUT_HASHES:
        with path.open('rb') as f:
            INPUT_HASHES[str(path)] = hashlib.file_digest(f, 'sha256').hexdigest()
    return path


def read(path):
    return json.loads(pin(path).read_text())


def stream(path):
    with gzip.open(pin(path), 'rt') as f:
        for line in f:
            yield json.loads(line)


def source_function(path, name, namespace):
    node = next(n for n in ast.parse(pin(path).read_text()).body
                if isinstance(n, ast.FunctionDef) and n.name == name)
    exec(compile(ast.Module([node], type_ignores=[]), str(path), 'exec'), namespace)
    return namespace[name]


# Extract only these pure functions; importing the original modules loads models.
official_mra = source_function(CODE / 'work/payload/tree/evalpath/official.py',
                               'official_mra', {'math': math, 'Optional': Optional})
unit_factor = source_function(CODE / 'work/payload/h1eval/scorers.py', 'unit_factor', {'re': re})
names = source_function(CODE / 'kit2/kit/analyze.py', 'names', {'re': re})


def gap_prediction(calls, question):
    values = []
    for c in calls:
        if c['call'].startswith('<gap ') and c.get('served'):
            match = re.fullmatch(r'distance ([0-9]+(?:\.[0-9]+)?) m', c.get('response') or '')
            if match:
                values.append(float(match[1]))
    return values[-1] * unit_factor(question) if values else None


class Bootstrap:
    """Resample physical rooms; reuse draws across paired arms and subsets."""
    def __init__(self, rows):
        self.rooms = sorted({r['room'] for r in rows})
        self.lookup = {r: i for i, r in enumerate(self.rooms)}
        self.draws = np.zeros((DRAWS, len(self.rooms)), dtype=np.int16)
        rng = random.Random(SEED)
        for draw in self.draws:
            for _ in self.rooms:
                draw[self.lookup[rng.choice(self.rooms)]] += 1

    def samples(self, rows, key):
        n = np.zeros(len(self.rooms))
        total = n.copy()
        for r in rows:
            if r.get(key) is not None:
                i = self.lookup[r['room']]
                n[i] += 1
                total[i] += r[key]
        dn = self.draws @ n
        values = np.divide(self.draws @ total, dn, out=np.full(DRAWS, np.nan), where=dn > 0)
        return values

    @staticmethod
    def summary(mean, values, n, rooms):
        valid = values[np.isfinite(values)]
        return dict(mean=mean, ci95=np.percentile(valid, [2.5, 97.5]).tolist() if len(valid) else None,
                    n=n, rooms=rooms, defined_draws=len(valid), undefined_draws=DRAWS-len(valid))

    def metric(self, rows, key):
        rr = [r for r in rows if r.get(key) is not None]
        return self.summary(statistics.mean(r[key] for r in rr) if rr else None,
                            self.samples(rr, key), len(rr), len({r['room'] for r in rr}))

    def contrast(self, a, b, key):
        return self.summary(statistics.mean(r[key] for r in a)-statistics.mean(r[key] for r in b)
                            if a and b else None, self.samples(a, key)-self.samples(b, key),
                            [len(a), len(b)], [len({r['room'] for r in a}), len({r['room'] for r in b})])


def subset(rows, ds):
    return [r for r in rows if ds == 'all' or r['dataset'] == ds or
            (ds == 'ScanNet+ScanNet++' and r['dataset'] in ('scannet', 'scannetppv2'))]


def capture_rows():
    refs = {r['item_id']: r for r in read(ITEMS)['items']}
    point = read(CAP / 'score_t1/SCORE_POINT_T1.json')
    dense = read(CAP / 'score_t1/SCORE_DENSE_T1.json')
    funnel = read(CAP / 'score_t1/FUNNEL_T1.json')
    dm = {r['item_id']: r for r in dense['rows']}
    rows = []
    for p in point['rows']:
        ref, d = refs[p['item_id']], dm[p['item_id']]
        assert p['baseline'] == p['T1'] == d['T1'] == d['baseline']
        truth = float(p['truth']['scored'])
        assert truth == float(ref['task']['released_answer'])
        factor = unit_factor(ref['task']['question'])
        rows.append(dict(item_id=p['item_id'], room=p['room'], dataset=ref['task']['dataset'],
                         pair_class=sorted(names(ref['task']['question'])), truth=truth,
                         truth_m=truth/factor, factor=factor, T1=p['T1'], T2=p['points'], dense64=d['dense64']))
    lookup = {r['item_id']: r for r in rows}
    counts = {}
    for file, arm in [('t1.gz', 'T1'), ('t2.gz', 'T2'), ('dense.gz', 'dense64')]:
        seen = set()
        for r in stream(CAP / file):
            if r['pass_index'] != 0:
                continue
            item = lookup[r['item_id']]
            assert r['item_id'] not in seen
            seen.add(r['item_id'])
            pred = gap_prediction(r['calls'], refs[r['item_id']]['task']['question'])
            score = 100*official_mra(pred, item['truth'])
            assert abs(score-item[arm]) < 1e-9, (r['item_id'], arm, score, item[arm])
            item[arm+'_prediction'] = pred
        assert seen == set(lookup)
        counts[arm] = len(seen)
    for arm, field in [('t1', 'T1'), ('points', 'T2'), ('dense64', 'dense64')]:
        for r in funnel['items'][arm]:
            item = lookup[r['item_id']]
            assert r['score'] == item[field] and r['room'] == item['room']
            item[field+'_stage'] = r['stage']
    assert len(rows) == 150 and abs(statistics.mean(r['T1'] for r in rows)-58.6) < 1e-9
    return rows, funnel, counts


def fit_constants(rows):
    """Median in metres, excluding the entire test room from both fit levels."""
    pooled = statistics.median(r['truth_m'] for r in rows)
    for r in rows:
        train = [q for q in rows if q['room'] != r['room']]
        same = [q for q in train if q['pair_class'] == r['pair_class']]
        global_m = statistics.median(q['truth_m'] for q in train)
        class_m = statistics.median(q['truth_m'] for q in same) if same else global_m
        r.update(class_train_n=len(same), class_train_rooms=len({q['room'] for q in same}),
                 class_fallback=not same, global_train_n=len(train),
                 global_train_rooms=len({q['room'] for q in train}),
                 class_constant_m=class_m, global_constant_m=global_m, pooled_constant_m=pooled)
        for key, pred in [('class_loro', class_m), ('global_loro', global_m), ('global_pooled', pooled)]:
            r[key] = 100*official_mra(pred*r['factor'], r['truth'])
            r['T1_minus_'+key] = r['T1']-r[key]
    return pooled


def analyze_captures(rows, funnel):
    boot = Bootstrap(rows)
    pooled = fit_constants(rows)
    tables, stages, constants = {}, {}, {}
    for r in rows:
        r['T2_minus_T1'] = r['T2']-r['T1']
        r['dense64_minus_T1'] = r['dense64']-r['T1']
    for ds in DATASETS:
        rr = subset(rows, ds)
        tables[ds] = {key: boot.metric(rr, key) for key in
                      ('T1', 'T2', 'dense64', 'T2_minus_T1', 'dense64_minus_T1')}
        constants[ds] = {key: boot.metric(rr, key) for key in
                         ('class_loro', 'global_loro', 'global_pooled', 'T1_minus_class_loro',
                          'T1_minus_global_loro', 'T1_minus_global_pooled')}
        stages[ds] = {}
        for arm, field in [('t1', 'T1'), ('points', 'T2'), ('dense64', 'dense64')]:
            oo = [dict(o, dataset=o['capture'].split('/')[0]) for o in funnel['objects'][arm]]
            stages[ds][field] = {}
            for stage in STAGES:
                cell = boot.metric([r for r in rr if r[field+'_stage'] == stage], field)
                cell['objects'] = sum(o['stage'] == stage for o in subset(oo, ds))
                stages[ds][field][stage] = cell
    contrast = {k: boot.contrast(subset(rows, 'arkitscenes'), subset(rows, 'ScanNet+ScanNet++'), k)
                for k in ('T1', 'T2', 'dense64', 'T2_minus_T1', 'dense64_minus_T1')}
    return dict(dataset_tables=tables, dataset_hypothesis_contrasts=contrast, funnel=stages,
                funnel_definitions=funnel['definitions'], constants=constants,
                constant_fit=dict(estimator='median distance in metres; unordered exact lower-case object-name pair',
                    unseen_class='other-room global median', global_pooled_m=pooled,
                    global_pooled_warning='Descriptive in-sample median; sees evaluation labels. Not cross-fitted.',
                    classes=len({tuple(r['pair_class']) for r in rows}),
                    class_supported_items=sum(not r['class_fallback'] for r in rows),
                    fallback_items=sum(r['class_fallback'] for r in rows),
                    ci_scope='Room bootstrap of fixed out-of-room predictions; no bootstrap refit.'),
                rooms=boot.rooms, rows=rows)


def corpus_scorer():
    path = pin(CORPUS / 'tool/corpus_score.py')
    spec = importlib.util.spec_from_file_location('r6_corpus_score', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_corpus():
    with pin(CORPUS / 'INDEX.jsonl').open() as f:
        index = {r['read_id']: r for r in map(json.loads, f)}
    module = corpus_scorer()
    checks, reads = {}, {}
    for ids in READS.values():
        for rid in ids:
            path = pin(CORPUS / 'reads' / (rid+'.jsonl.gz'))
            assert INPUT_HASHES[str(path)] == index[rid]['output']['sha256']
            result = module.collect(path)
            checks[rid] = {}
            for arm, entry in result['arms'].items():
                actual, expected = entry['overall'], index[rid]['arm_stats'][arm]
                assert actual['items'] == expected['items'] and actual['scored'] == expected['scored']
                assert abs(actual['mean_score']-expected['mean_score']) < 1e-12
                checks[rid][arm] = dict(actual=actual, expected=expected, match=True)
            compact = []
            for r in stream(path):
                task = r['raw'].get('input') or {}
                arm = r['arms'].get('tower', {})
                calls = arm.get('tool_calls') or []
                ground = [c for c in calls if c.get('served') and c.get('kind') == 'ground']
                gap = gap_prediction(calls, r['question']) if calls else None
                compact.append(dict(item_id=r['item_id'], room=r['room'], family=r['family'],
                    type=r['question_type'], truth=r['truth']['scored'], unit=r['truth']['units'],
                    twin_id=task.get('twin_id'), pair=task.get('gt', {}).get('pair'),
                    truth_m=task.get('gt', {}).get('distance_m'),
                    template=bool(task) and not r['item_id'].endswith('_ho'),
                    wording_id=task.get('heldout_wording_id'),
                    scores={a: v['score']*100 if v['score'] is not None else None for a,v in r['arms'].items()},
                    called=bool(calls), not_seen=any('not seen' in (c.get('response') or '').lower() for c in calls),
                    box_returned=len(ground) == 2 and all(re.search(r'\nB\d+: f1 centre ', c.get('response') or '') for c in ground),
                    numeric_gap=gap is not None,
                    null_would_win=any(c.get('stage1', {}).get('null_would_win', False) for c in ground),
                    gap_score=100*official_mra(gap, float(r['truth']['scored'])) if task else None,
                    gate_fields=sorted({k for c in calls for k in c if 'gate' in k or 'fallback' in k})))
            reads[rid] = compact
    metadata = {}
    for step, (rid, _) in READS.items():
        manifest = index[rid]['raw_metadata']['inputs/items/dist580.json']
        assert set(manifest['sets']['R0-dev']) == {r['item_id'] for r in reads[rid]}
        metadata[str(step)] = {k: v for k,v in manifest.items() if k != 'sets'}
    return reads, checks, metadata


def twin_subset(rows, unit):
    if unit == 'all':
        return rows
    if unit == 'm+ft':
        return [r for r in rows if r['twin_unit'] in ('m', 'ft')]
    return [r for r in rows if r['twin_unit'] == unit]


def analyze_twins(reads):
    output = {}
    for step, (rid, did) in READS.items():
        routed, direct = reads[rid], reads[did]
        lookup = {r['item_id']: r for r in routed}
        boot = Bootstrap(routed)
        dd = {r['item_id']: r for r in direct if r['type'] == 'object_abs_distance'}
        pairs, cross = [], []
        for r in routed:
            if not r['template']:
                continue
            t = lookup[r['twin_id']]
            assert t['twin_id'] == r['item_id'] and r['room'] == t['room']
            assert r['truth_m'] == t['truth_m'] and r['pair'] == t['pair'] and r['unit'] == 'm'
            row = dict(template_id=r['item_id'], twin_id=t['item_id'], room=r['room'], twin_unit=t['unit'],
                       template=r['scores']['tower'], twin=t['scores']['tower'],
                       template_called=r['called'], twin_called=t['called'],
                       template_minus_twin=r['scores']['tower']-t['scores']['tower'])
            pairs.append(row)
            if r['called'] == t['called']:
                continue
            route, plain = (r,t) if r['called'] else (t,r)
            sc, dc = route['scores']['tower'], plain['scores']['tower']
            gates = dict(box_returned=bool(route['box_returned']),
                         numeric_gap=route['numeric_gap'], not_seen_fallback=not route['not_seen'],
                         selector_null_fallback=not route['null_would_win'])
            q = dict(row, routed_id=route['item_id'], direct_id=plain['item_id'],
                     routed_unit=route['unit'], direct_unit=plain['unit'], routed=sc, direct=dc,
                     routed_minus_direct=sc-dc, gates=gates)
            for name, use_route in gates.items():
                q['gate_'+name] = sc if use_route else dc
                q['gain_'+name] = q['gate_'+name]-sc
            cross.append(q)
        assert len(pairs) == 290
        gates = ('box_returned', 'numeric_gap', 'not_seen_fallback', 'selector_null_fallback')
        tables, pair_tables = {}, {}
        for unit in ('m', 'ft', 'm+ft', 'in', 'cm', 'all'):
            rr = twin_subset(cross, unit)
            tables[unit] = {key: boot.metric(rr, key) for key in
                           ('routed', 'direct', 'routed_minus_direct')}
            tables[unit]['gates'] = {g: dict(score=boot.metric(rr, 'gate_'+g),
                gain_over_always_route=boot.metric(rr, 'gain_'+g),
                fallback_pairs=sum(not r['gates'][g] for r in rr)) for g in gates}
            pp = twin_subset(pairs, unit)
            pair_tables[unit] = {k: boot.metric(pp, k) for k in ('template', 'twin', 'template_minus_twin')}
        coverage = dict(routed_items=len(routed), routed_rooms=len(boot.rooms), template_items=290,
            reworded_twins=290, units=dict(Counter(r['unit'] for r in routed)),
            twin_units=dict(Counter(r['twin_unit'] for r in pairs)),
            direct_items=len(direct), direct_distance_items=len(dd),
            exact_distance_overlap=len(set(lookup)&set(dd)),
            direct_question_types=dict(Counter(r['type'] for r in direct)),
            discordant_route_pairs=len(cross), numeric_gap_vs_direct_pairs=sum(r['gates']['numeric_gap'] for r in cross),
            both_called_pairs=sum(r['template_called'] and r['twin_called'] for r in pairs),
            no_tool_pairs=sum(not r['template_called'] and not r['twin_called'] for r in pairs),
            template_not_seen=sum(r['not_seen'] for r in routed if r['template']),
            recorded_explicit_gate_fields=sorted({k for r in routed for k in r['gate_fields']}))
        item_tables = {u: boot.metric([dict(r, score=r['scores']['tower']) for r in routed
                      if u == 'all' or r['unit'] == u or (u == 'm+ft' and r['unit'] in ('m','ft'))], 'score')
                      for u in ('m','ft','m+ft','in','cm','all')}
        output[str(step)] = dict(coverage=coverage, named_direct_comparison=dict(status='unidentified',
            reason='Named direct read has no distance items; no same-item route/direct scores or fallback scores.',
            routed_minus_direct=None, gates=None), routed_item_scores=item_tables,
            all_twin_pairs=pair_tables, observational_route_direct_twins=tables,
            pair_rows=pairs, observational_pair_rows=cross, rooms=boot.rooms)
    return output


def verdicts(twins):
    observational = {}
    for unit in ('m','ft','m+ft','in','cm','all'):
        deltas = {s: twins[s]['observational_route_direct_twins'][unit]['routed_minus_direct']['mean'] for s in ('200','400')}
        gains = [(s,g,v['gain_over_always_route']['mean']) for s in ('200','400')
                 for g,v in twins[s]['observational_route_direct_twins'][unit]['gates'].items()]
        hits = [dict(step=s,gate=g,gain=v) for s,g,v in gains if v is not None and v >= 2]
        below = deltas['400'] is not None and deltas['400'] < -3
        observational[unit] = dict(deltas=deltas, gate_ge2=hits, step400_below_minus3=below,
            retain_condition=all(v is not None and v >= 0 for v in deltas.values()) and not hits,
            parser_review_numeric_trigger=bool(hits) or below,
            interpretation='Observational twins differ in wording/units; not a forced-direct same-item comparison.')
    primary_units = ('m', 'ft', 'm+ft', 'all')
    primary_retain = all(observational[u]['retain_condition'] for u in primary_units)
    trigger_units = [u for u, v in observational.items() if v['parser_review_numeric_trigger']]
    return dict(registered=dict(
        evidence='D580 reciprocal twins with one called answer and one no-call answer; observational.',
        primary_scopes=list(primary_units), twin_proxy_retain_condition=primary_retain,
        route_retention_verdict='Unresolved: the required same-item gate comparison is unavailable.',
        route_table='distance routed with not-seen fallback; camera routed; room direct',
        same_item_gate_ge2=None,
        primary_twin_proxy_gate_ge2=any(observational[u]['gate_ge2'] for u in primary_units),
        primary_step400_below_minus3=any(observational[u]['step400_below_minus3'] for u in primary_units),
        any_unit_twin_proxy_gate_ge2=any(v['gate_ge2'] for v in observational.values()),
        any_unit_step400_below_minus3=any(v['step400_below_minus3'] for v in observational.values()),
        parser_trigger_units=trigger_units,
        forced_direct_diagnostic='Triggered on the centimetre stratum only; 20-minute diagnostic not run.',
        parser_review='Eligible on the centimetre stratum only; no review spent in this CPU ledger.',
        caution='No pooled/metre/foot numerical trigger. Centimetres are an additional observed unit stratum. Twin gate gains are sensitivity estimates, not the requested same-item test.'),
        observational=observational, dataset_splits='Hypotheses only; need fresh items.')


def fmt(cell):
    if cell['mean'] is None:
        return 'NA'
    lo,hi = cell['ci95']
    return f"{cell['mean']:.1f} [{lo:.1f}, {hi:.1f}]"


def table(headers, rows):
    return ['| '+' | '.join(headers)+' |', '| '+' | '.join(['---']*len(headers))+' |'] + [
        '| '+' | '.join(map(str,r))+' |' for r in rows]


def report(result):
    cap, twins, v = result['captures'], result['twins'], result['verdicts']
    lines = ['# LEDGER R6',
        'Route-retention verdict: unresolved because same-item gate scores are unavailable. The twin proxy meets the retain rule for metres, feet, their pool, and all units; it does not validate a policy change.',
        'Centimetre twins cross the step-400 <−3 trigger: the 20-minute forced-direct diagnostic is triggered for this stratum, not run; parser review is eligible, not spent. Their gate proxy also exceeds +2, but the required same-item gate trigger is unidentified.',
        'D580 supplies observational route/direct twins; wording and units differ, so their differences do not identify the effect of routing.',
        'Scores are MRA points (0–100). Intervals use 10,000 paired physical-room draws, seed 20261120, item weighting; all subsets reuse population draws. Undefined draws are recorded in JSON.',
        'Dataset splits are hypotheses. Cells show mean [95% interval].']
    lines += table(['Dataset (items/rooms)','T1','T2 points','Dense64','T2−T1','Dense−T1'], [
        [f"{ds} ({t['T1']['n']}/{t['T1']['rooms']})"]+[fmt(t[k]) for k in ('T1','T2','dense64','T2_minus_T1','dense64_minus_T1')]
        for ds,t in cap['dataset_tables'].items()])
    lines += ['Constants use unordered object-name pairs and medians in metres. Both LORO fits exclude every label in the test room; bootstrap intervals condition on fitted predictions.']
    fit = cap['constant_fit']
    lines += [f"There are {fit['classes']} classes; {fit['class_supported_items']} items have other-room class support and {fit['fallback_items']} use the other-room global median. The pooled median is {fit['global_pooled_m']:.4f} m and is an in-sample descriptive reference."]
    t = cap['constants']['all']
    lines += table(['Constant on 150','MRA','Served 58.6 − constant'], [[name,fmt(t[key]),fmt(t['T1_minus_'+key])]
        for name,key in [('Class median, LORO','class_loro'),('Global median, LORO','global_loro'),('Global median, pooled (in-sample)','global_pooled')]])
    lines += ['T1 first-failure stages: n; mean [95% interval]. S0 invisible, S1 no matching proposal, S2 wrong selection, S3 <3 matched frames, S4 misplaced, S5 passed.']
    lines += table(['Stage','ARKit','ScanNet','ScanNet++','ScanNet+ScanNet++'], [[s]+[
        f"{cap['funnel'][ds]['T1'][s]['n']}; {fmt(cap['funnel'][ds]['T1'][s])}" for ds in DATASETS[1:]] for s in STAGES])
    lines += ['No item reaches S4/S5; missing GT and censored items remain in all-score denominators. All-arm stage counts, object counts, split contrasts, and per-item evidence are in JSON.',
        'Observational twin ledger: the template asks metres; its direct, reworded twin uses the listed unit. “m+ft” pools metre and foot twins; “all” also includes inches and centimetres.']
    lines += table(['Step/unit','Pairs','Route','Direct twin','Route−direct'], [[s+'/'+u,
        t['routed']['n'],fmt(t['routed']),fmt(t['direct']),fmt(t['routed_minus_direct'])]
        for s in ('200','400') for u in ('m','ft','m+ft','all','in','cm')
        for t in [twins[s]['observational_route_direct_twins'][u]]])
    lines += ['Gates use the same observational pairs: retain the routed answer when the condition passes; otherwise substitute the direct twin. Scores and gains are not same-item counterfactuals.']
    lines += table(['Step/gate (all units)','Fallback pairs','Gate MRA','Gate−always-route'], [[s+'/'+g,
        t['fallback_pairs'],fmt(t['score']),fmt(t['gain_over_always_route'])]
        for s in ('200','400') for g in ('box_returned','not_seen_fallback','selector_null_fallback')
        for t in [twins[s]['observational_route_direct_twins']['all']['gates'][g]]])
    lines += [f"Centimetre box/not-seen gate gains: 200 {fmt(twins['200']['observational_route_direct_twins']['cm']['gates']['box_returned']['gain_over_always_route'])}; 400 {fmt(twins['400']['observational_route_direct_twins']['cm']['gates']['box_returned']['gain_over_always_route'])}.",
        'The numeric-gap gate equals the box gate here; per-unit gate tables are in JSON. Selector-null is a recorded diagnostic, not an active refusal policy.',
        'Mechanical twin-proxy readings (point-estimate thresholds; same-item gate verdict remains unidentified):']
    for u in ('m','ft','m+ft','all'):
        o = v['observational'][u]
        lines.append(f"{u}: retain condition={o['retain_condition']}; gate ≥2={bool(o['gate_ge2'])}; step-400 <−3={o['step400_below_minus3']}; numeric parser trigger={o['parser_review_numeric_trigger']}.")
    lines += [f"Coverage: each D580 read has 290 reciprocal pairs/580 items/98 rooms: 363 m, 73 ft, 72 in, 72 cm. Route/direct pairs are {twins['200']['coverage']['discordant_route_pairs']} at 200 and {twins['400']['coverage']['discordant_route_pairs']} at 400; the plan's 82 twin pairs are not reproduced.",
        'At step 400, 82 is the number of template items with a “not seen” response, not the number of route/direct pairs.',
        'Validation: raw-gap scoring reproduces all 450 T1/T2/dense scores and T1=58.6; the supplied corpus scorer reproduces every INDEX arm mean of all four reads; read-file hashes match INDEX.',
        'Deviations: both named direct reads have 3,120 items but zero distance items, so no independent same-item replication is possible. Gates substitute the observed direct twin. No model/job rerun or forbidden resource was used.']
    assert len(lines) <= 70, len(lines)
    return '\n'.join(lines)+'\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=ROOT/'out')
    args = parser.parse_args()
    out = args.out.resolve()
    if not out.is_relative_to(ROOT):
        parser.error('Output must remain inside r6')
    pin(ROOT/'in/PLAN_RANK6.md')
    rows, funnel, capture_checks = capture_rows()
    captures = analyze_captures(rows, funnel)
    reads, checks, metadata = load_corpus()
    twins = analyze_twins(reads)
    result = dict(schema='ledger-r6-v1', bootstrap=dict(seed=SEED, draws=DRAWS, interval=95,
        unit='physical room', estimator='item-weighted', pairing='same room draws for all arms and subgroups'),
        captures=captures, twins=twins, d580_metadata=metadata, verdicts=verdicts(twins),
        validation=dict(served150=58.6, capture_scores_reproduced=capture_checks, corpus=checks),
        provenance=dict(inputs=INPUT_HASHES, corpus_scoring='Supplied corpus_score.collect; stored scores, no text rescoring.',
            capture_scoring='Pure official_mra and unit_factor extracted from pinned source; last served numeric gap; missing gap scores zero.',
            mra='Mean relative accuracy at confidence 0.50,0.55,...,0.95 (10 inclusive thresholds); zero target requires exact zero.'),
        limitations=['No distance items in the named direct reads.',
            'Observational twins differ in wording and often units; route selection is not randomized.',
            'No forced-route counterfactual for no-call items; always-route means the observed called arm on discordant pairs only.',
            'Class median falls back to the training-room global median for unseen classes.',
            'Funnel stages are reused from the existing audit; censored/no-GT are not successful stages.',
            'Step-544 corpus segments are reference inputs only; step-544 findings use the 150 capture items.'])
    rendered = report(result)
    out.mkdir(parents=True, exist_ok=True)
    (out/'LEDGER.json').write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    (out/'REPORT_R6.md').write_text(rendered)
    paths = [ROOT/'ledger.py', ROOT/'test_ledger.py', out/'LEDGER.json', out/'REPORT_R6.md']
    if (out/'TEST.log').is_file():
        paths.append(out/'TEST.log')
    sums = []
    for path in paths:
        with path.open('rb') as f:
            sums.append(hashlib.file_digest(f,'sha256').hexdigest()+'  '+str(path.relative_to(ROOT)))
    (out/'SHA256SUMS').write_text('\n'.join(sums)+'\n')
    print(rendered)


if __name__ == '__main__':
    main()
