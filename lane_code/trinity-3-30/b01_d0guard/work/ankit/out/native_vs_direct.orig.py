#!/usr/bin/env python3
"""Paired dev-S1 analysis. Standard library only; no model inference or network.

Use --plumbing for fixtures; --subset KEYS.json is always PLUMBING.
All paths written by this program must remain inside the build directory.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path
import random
import re
import sys

BUILD = Path('/scratch/jjyeung/orch_n30/native_r2/builds/03_analysis')
ROOT = BUILD.parents[1]
META = ROOT / 'work/meta/sj/orch_cd'
DEFAULT_TASKS = META / 'legs1_reads/work/vendor/r3/TASKS.jsonl'
DEFAULT_FRAMES = DEFAULT_TASKS.with_name('FRAMES.json')
DEFAULT_CAMERA = META / 'legs1_routed/out2/CAMERA_TASKS.jsonl'
DEFAULT_DIRECT = ROOT / 'work/direct/DIRECT_B2048_COMPACT.json'
ARMS = ('unflagged', 'scripted')
TYPES = ('object_abs_distance', 'room_size_estimation', 'camera_displacement',
         'camera_movement_direction', 'camera_rotation')
ALIASES = {'absolute_distance_object': TYPES[0], 'absolute_size_room': TYPES[1]}
EXPECTED = dict(zip(TYPES, (150, 36, 150, 150, 150)))
CAVEAT = ('training responses came from ground-truth instances; the wider candidate universe '
          'changes candidate competition; tools print metric units only while 107 of 150 '
          'distance and 7 of 36 room items ask other units; no training row shows a failed '
          'ground; routing rows hold no ARKitScenes scenes in a 400-row sample; the reviewed '
          'guard refuses 1 capture (2 distance items) where the sealed guard refused 11')


class Refusal(ValueError):
    """The inputs do not support an admitted paired comparison."""


def require(condition, message):
    if not condition:
        raise Refusal(message)


def read(path):
    with Path(path).open() as stream:
        return json.load(stream)


def jsonl(path):
    with Path(path).open() as stream:
        return [json.loads(line) for line in stream if line.strip()]


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def write(path, value):
    path = Path(path).resolve()
    require(path.is_relative_to(BUILD), 'Output must be inside ' + str(BUILD))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n')


def family(row):
    return ALIASES.get(row['question_type'], row['question_type'])


def label(row):
    return 'released_answer' if row['stratum'] == 'primary' else 'answer'


def index(rows, source, selected=None):
    result = {}
    for row in rows:
        key = row['key']
        if selected is not None and key not in selected:
            continue
        require(key not in result, f'Duplicate key in {source}: {key}')
        result[key] = row
    return result


def pct(values):
    return 100 * sum(values) / len(values) if values else None


def close(actual, expected, context):
    if isinstance(expected, dict):
        require(isinstance(actual, dict) and set(actual) >= set(expected), context + ': missing fields')
        for k, v in expected.items():
            close(actual[k], v, context + '/' + k)
    elif isinstance(expected, (int, float)) and not isinstance(expected, bool):
        require(isinstance(actual, (int, float)) and math.isfinite(actual)
                and math.isclose(actual, expected, rel_tol=1e-10, abs_tol=1e-8), context + ': disagreement')
    else:
        require(actual == expected, context + ': disagreement')


def question_unit(question):
    # Matches the bound reader_policy.question_unit; the last named length unit wins.
    matches = re.findall(r'\b(square\s+)?(millimeters?|millimetres?|centimeters?|centimetres?|'
                         r'meters?|metres?|inches|inch|feet|foot)\b', question, re.I)
    if not matches:
        return dict(unit='unknown', metric=None, meter_based=None)
    square, value = matches[-1]
    value = value.lower().replace('metre', 'meter')
    unit = ('millimeters' if value.startswith('millimeter') else
            'centimeters' if value.startswith('centimeter') else
            'meters' if value.startswith('meter') else
            'inches' if value in ('inch', 'inches') else 'feet')
    return dict(unit=('square ' if square else '') + unit,
                metric=unit in ('millimeters', 'centimeters', 'meters'), meter_based=unit == 'meters')


def metadata(tasks, frames, camera, keys):
    """Derive rooms from metadata, before consulting any direct/native room value."""
    task_index = {}
    capture_map = {}
    for source, rows in ((str(tasks), jsonl(tasks)), (str(camera), jsonl(camera))):
        for row in rows:
            key = row.get('key', 'devrows:' + row['id'])
            if key not in keys:
                continue
            require(key not in task_index, 'Duplicate metadata key: ' + key)
            task_index[key] = row
            cap, room = row['native'], row['room']
            group, capture_id = cap.split('/', 1)
            require(group in ('d1', 'd2', 'd3'), 'Unknown capture group: ' + cap)
            expected_dataset = {'d1': 'scannet', 'd2': 'scannetppv2', 'd3': 'arkitscenes'}[group]
            require(row['dataset'] == expected_dataset, 'Dataset disagreement: ' + cap)
            require(row['scene'] == expected_dataset + '/' + capture_id, 'Scene disagreement: ' + cap)
            if group == 'd1':
                require(re.fullmatch(r'scene\d+_\d+', capture_id) is not None, 'Invalid rescan: ' + cap)
                require(room == group + '/' + capture_id.rsplit('_', 1)[0], 'Rescan room disagreement: ' + cap)
            elif group == 'd2':
                require(room == cap, 'Single scan room disagreement: ' + cap)
            else:
                require(re.fullmatch(r'd3/venue\d+', room) is not None, 'Missing venue metadata: ' + cap)
            entry = dict(room=room, group=group, scene=row['scene'], dataset=row['dataset'], sources=[source])
            if cap in capture_map:
                require(all(capture_map[cap][x] == entry[x] for x in ('room', 'scene', 'dataset')),
                        'Metadata room disagreement: ' + cap)
                if source not in capture_map[cap]['sources']:
                    capture_map[cap]['sources'].append(source)
            else:
                capture_map[cap] = entry
    require(set(task_index) == set(keys), 'Metadata lacks selected keys')
    seen = set()
    for row in read(frames)['captures']:
        cap = row['native']
        if cap not in capture_map:
            continue
        require(cap not in seen, 'Duplicate FRAMES capture: ' + cap)
        seen.add(cap)
        require(row['scene'] == capture_map[cap]['scene'], 'FRAMES scene disagreement: ' + cap)
        for field in ('room', 'dataset'):
            if field in row:
                require(row[field] == capture_map[cap][field], 'FRAMES ' + field + ' disagreement: ' + cap)
        capture_map[cap]['sources'].append(str(frames))
    require(seen == set(capture_map), 'FRAMES lacks selected captures')
    summary = {g: dict(captures=sum(v['group'] == g for v in capture_map.values()),
                       rooms=len({v['room'] for v in capture_map.values() if v['group'] == g}))
               for g in ('d1', 'd2', 'd3')}
    return task_index, dict(captures=capture_map, summary=summary,
                           method='d1 scene prefix; d2 scan identity; d3 venue from TASKS.room; FRAMES.scene cross-check')


def bootstrap(rows, draws=10000, seed=20261115):
    """Paired, unstratified physical-room percentile bootstrap, item-weighted."""
    require(draws >= 10000, 'At least 10000 bootstrap draws are required')
    if not rows:
        return {a: None for a in ARMS}
    by_room = defaultdict(lambda: [0, 0.0, 0.0])
    for room, native, scripted, direct in rows:
        acc = by_room[room]
        acc[0] += 1
        acc[1] += native - direct
        acc[2] += scripted - direct
    clusters = [by_room[r] for r in sorted(by_room)]
    rnd = random.Random(seed)
    values = [[], []]
    for _ in range(draws):
        chosen = rnd.choices(clusters, k=len(clusters))
        denominator = sum(c[0] for c in chosen)
        for j in (0, 1):
            values[j].append(100 * sum(c[j + 1] for c in chosen) / denominator)
    def quantile(xs, p):
        xs.sort()
        position = (len(xs) - 1) * p
        lo = int(position)
        return xs[lo] + (xs[min(lo + 1, len(xs) - 1)] - xs[lo]) * (position - lo)
    return {a: [quantile(values[j], .025), quantile(values[j], .975)] for j, a in enumerate(ARMS)}


def native_score(row):
    return row['scores'][label(row)]


def counts(keys, arms, direct, tasks, refused):
    result = {}
    for arm, rows in arms.items():
        rs = [rows[k] for k in keys]
        model_rows = [r for r in rs if tasks[r['key']]['native'] not in refused]
        result[arm] = dict(items=len(rs), geometry_refused_items=len(rs) - len(model_rows),
            geometry_refused_captures=len({tasks[r['key']]['native'] for r in rs} & refused),
            capped=sum(bool(r['capped']) for r in rs),
            no_answer=sum(bool(r['no_answer']) for r in model_rows),
            no_answer_including_geometry=sum(bool(r['no_answer']) for r in rs),
            program_refusals=sum(r.get('decode', {}).get('finish') == 'program_refusal' for r in rs),
            call_errors=sum(r['call_errors'] for r in rs),
            call_error_items=sum(bool(r['call_errors']) for r in rs),
            version_errors=sum(r['version_errors'] for r in rs),
            budget_truncated_call_items=sum(bool(r['budget_truncated_calls']) for r in rs))
    result['direct'] = dict(items=len(keys), capped=sum(bool(direct[k]['hit_token_cap']) for k in keys),
                            parse_failed=sum(bool(direct[k]['parse_failed']) for k in keys))
    return result


def call_rates(keys, arms):
    result = {}
    for typ in TYPES:
        rs = [arms['unflagged'][k] for k in keys if family(arms['unflagged'][k]) == typ]
        if not rs:
            continue
        decoded = [r for r in rs if not r.get('geometry_refusal')]
        calls = sum(bool(r['called']) for r in rs)
        result[typ] = dict(items=len(rs), call_rate_denominator_items=len(decoded),
                          call_rate_decoded_items_pct=100 * calls / len(decoded) if decoded else None,
                          call_rate_all_items_pct=100 * calls / len(rs))
    return result


def units(keys, arms, direct):
    """R1-compatible summaries plus all-arm exact-unit summaries."""
    original, extended = {}, {}
    predicates = dict(all=lambda u: True, metric=lambda u: u['metric'] is True,
        nonmetric=lambda u: u['metric'] is False, meter_based=lambda u: u['meter_based'] is True,
        other_units=lambda u: u['meter_based'] is False, unknown=lambda u: u['metric'] is None)
    for typ in TYPES:
        ks = [k for k in keys if family(arms['unflagged'][k]) == typ]
        if not ks and typ not in TYPES[:2]:
            continue
        def summary(selected):
            passed = [k for k in selected if not arms['unflagged'][k].get('geometry_refusal')]
            def scores(group):
                return {**{a: pct([native_score(arms[a][k]) for k in group]) for a in ARMS},
                        'direct': pct([direct[k]['score'] for k in group])}
            return dict(items=len(passed), all_items=len(selected), geometry_refused_items=len(selected)-len(passed),
                        scores_pct=scores(passed), all_item_scores_pct=scores(selected))
        groups = {name: summary([k for k in ks if pred(arms['unflagged'][k]['question_unit'])])
                  for name, pred in predicates.items()}
        exact = sorted({arms['unflagged'][k]['question_unit']['unit'] for k in ks})
        extended[typ] = dict(groups=groups, exact_units={u: summary([k for k in ks
                              if arms['unflagged'][k]['question_unit']['unit'] == u]) for u in exact})
        if typ in TYPES[:2]:
            original[typ] = {name: {**v,
                'scores_pct': {a: v['scores_pct'][a] for a in ARMS},
                'all_item_scores_pct': {a: v['all_item_scores_pct'][a] for a in ARMS}}
                for name, v in groups.items()}
            for name, refused in (('exact_units', False), ('geometry_refused_exact_units', True)):
                original[typ][name] = dict(Counter(arms['unflagged'][k]['question_unit']['unit'] for k in ks
                    if bool(arms['unflagged'][k].get('geometry_refusal')) == refused))
    return original, extended


def analyze(bundle, admission, direct_rows, task_rows, room_map, subset=False, plumbing=False,
            draws=10000, seed=20261115):
    require(bundle.get('schema') == 'legs1-r1-nomdg-v1', 'Unexpected bundle schema')
    keys = bundle['expected_keys']
    require(len(keys) == len(set(keys)), 'Duplicate expected key')
    require(bool(keys), 'Empty cohort')
    keyset = set(keys)
    arms = {a: index(bundle['arms'][a], a, keyset if subset else None) for a in ARMS}
    for a in ARMS:
        require(set(arms[a]) == keyset, 'Missing or unexpected key in ' + a)
    # Full mode validates duplicates across the whole accepted direct file.
    direct = index(direct_rows, 'direct', keyset if subset else None)
    require(keyset <= set(direct), 'Direct read lacks expected keys')
    if not subset:
        for row in direct.values():
            capture = row.get('native')
            if capture in room_map['captures']:
                require(row['room'] == room_map['captures'][capture]['room'],
                        'Direct room-map disagreement: ' + row['key'])
    direct = {k: direct[k] for k in keys}
    require(set(task_rows) == keyset, 'Metadata selection differs')
    type_counts = Counter(family(arms['unflagged'][k]) for k in keys)
    require(set(type_counts) <= set(TYPES), 'Unexpected question type')
    if not subset:
        require(type_counts == EXPECTED, 'Full cohort type denominators differ')
        require({g: v['captures'] for g, v in room_map['summary'].items()} == {'d1':29, 'd2':25, 'd3':30},
                'Full cohort capture denominators differ')
    report = admission['report']
    guard = report['gravity_guard_report']['dev-S1']
    refused_all = set(guard['reviewed_refused'])
    require(len(refused_all) == len(guard['reviewed_refused']), 'Duplicate guard refusal capture')
    require(refused_all <= set(guard['captures']), 'Guard refuses an unknown capture')
    for name in ('sealed_refused', 'reviewed_only_refused'):
        if name in guard:
            require(len(set(guard[name])) == len(guard[name]), 'Duplicate guard capture: ' + name)
            require(guard[name + '_count'] == len(guard[name]), 'Guard count disagreement: ' + name)
            require(set(guard[name]) <= set(guard['captures']), 'Guard list outside capture census: ' + name)
    if 'sealed_refused' in guard and 'reviewed_only_refused' in guard:
        require(set(guard['reviewed_only_refused']) == refused_all - set(guard['sealed_refused']),
                'Reviewed-only guard list disagreement')
    captures = set(room_map['captures'])
    refused = refused_all & captures
    if not subset:
        require(set(guard['captures']) == captures, 'Guard capture census disagreement')
        require(guard['capture_count'] == len(captures), 'Guard capture count disagreement')
    require(guard['reviewed_refused_count'] == len(refused_all), 'Guard refusal count disagreement')
    comparison = report.get('geometry_refusal_comparison')
    if comparison and 'full_refused' in comparison:
        require(set(comparison['full_refused']) & captures == refused, 'Guard comparison disagreement')
    label_counts = Counter()
    label_keys = defaultdict(list)
    for key in keys:
        task, dr = task_rows[key], direct[key]
        cap, room = task['native'], room_map['captures'][task['native']]['room']
        require(dr['native'] == cap and dr['room'] == room, 'Direct room-map disagreement: ' + key)
        require(dr['id'] == task['id'], 'Direct identity disagreement: ' + key)
        require(dr.get('budget') == 2048, 'Direct budget disagreement: ' + key)
        require(dr['stratum'] == task['stratum'] and family(dr) == family(task), 'Direct task disagreement: ' + key)
        authority = label(task)
        require(task.get('ground_truth') is not None and task.get(authority) is not None,
                'Missing label evidence: ' + key)
        require(str(task['ground_truth']).strip() == str(task[authority]).strip(), 'Label pairing disagreement: ' + key)
        require(task['scorer'] in ('official_vsi_mra', 'official_exact_match'), 'Unrecognized scorer: ' + key)
        if task['stratum'] == 'primary':
            require(task['scorer'] == 'official_vsi_mra', 'Primary scorer disagreement: ' + key)
        label_counts[authority] += 1
        label_keys[authority].append(key)
        unit = question_unit(task['question'])
        for a in ARMS:
            row = arms[a][key]
            require(row.get('arm', a) == a, 'Native arm identity disagreement: ' + key)
            if bundle.get('artifact_sha256'):
                require(row.get('checkpoint_sha256') == bundle['artifact_sha256'],
                        'Native checkpoint disagreement: ' + key)
            require(row['room'] == room, 'Native room-map disagreement: ' + key)
            require(row['stratum'] == task['stratum'] and family(row) == family(task), 'Native task disagreement: ' + key)
            require(row['question_unit'] == unit, 'Question unit disagreement: ' + key)
            ref = row.get('geometry_refusal')
            require(bool(ref) == (cap in refused), 'Geometry refusal set disagreement: ' + key)
            if ref:
                require(ref.get('capture') == cap, 'Geometry refusal capture disagreement: ' + key)
                require(native_score(row) == 0 and not row['called'] and row['no_answer'],
                        'Geometry refusal must score zero without decoding: ' + key)
            val = native_score(row)
            require(isinstance(val, (int, float)) and math.isfinite(val) and 0 <= val <= 1,
                    'Invalid native score: ' + key)
            if row['capped'] or row['no_answer']:
                require(val == 0, 'Capped/unparsed native answer has nonzero recorded score: ' + key)
        val = dr['score']
        require(isinstance(val, (int, float)) and math.isfinite(val) and 0 <= val <= 1, 'Invalid direct score: ' + key)
        if dr['hit_token_cap'] or dr['parse_failed']:
            require(val == 0, 'Capped/unparsed direct answer has nonzero recorded score: ' + key)
    rates = call_rates(keys, arms)
    for typ, rate in rates.items():
        close(report['per_type'][typ], rate, 'Admission call rate/' + typ)
        selected = [k for k in keys if family(arms['unflagged'][k]) == typ]
        geometry_count = sum(bool(arms['unflagged'][k].get('geometry_refusal')) for k in selected)
        checks = dict(geometry_refused_items=geometry_count, call_rate_excluded_geometry_items=geometry_count,
                      call_errors=sum(arms[a][k]['call_errors'] for a in ARMS for k in selected),
                      version_errors=sum(arms[a][k]['version_errors'] for a in ARMS for k in selected))
        for name, expected in checks.items():
            if name in report['per_type'][typ]:
                close(report['per_type'][typ][name], expected, 'Admission counter/' + typ + '/' + name)
    original_units, extended_units = units(keys, arms, direct)
    close(bundle['unit_scores'], original_units, 'Bundle unit_scores')
    if 'unit_scores' in report:
        close(report['unit_scores'], original_units, 'Admission unit_scores')
    counted = counts(keys, arms, direct, task_rows, refused)
    if 'geometry_refused_items' in report:
        close(report['geometry_refused_items'], counted['unflagged']['geometry_refused_items'],
              'Admission geometry refused items')
    if 'program_refusals' in report:
        p = report['program_refusals']
        close(p['total'], counted['unflagged']['program_refusals'], 'Admission program refusals')
        if 'per_family' in p:
            for typ in TYPES:
                n = sum(family(arms['unflagged'][k]) == typ and
                        arms['unflagged'][k].get('decode', {}).get('finish') == 'program_refusal' for k in keys)
                close(p['per_family'].get(typ, 0), n, 'Program refusals/' + typ)
    groups = {'all': keys}
    groups.update({t: [k for k in keys if family(arms['unflagged'][k]) == t] for t in TYPES})
    groups['camera_all'] = [k for k in keys if family(arms['unflagged'][k]) in TYPES[2:]]
    groups.update({g: [k for k in keys if task_rows[k]['native'].startswith(g + '/')] for g in ('d1','d2','d3')})
    for g in ('d1', 'd2', 'd3'):
        for t in (*TYPES, 'camera_all'):
            groups[g + '/' + t] = [k for k in groups[t] if k in set(groups[g])]
    output_groups = {}
    for name, group in groups.items():
        output_groups[name] = {}
        for selection in ('all_items', 'passed_geometry'):
            selected = group if selection == 'all_items' else [k for k in group if task_rows[k]['native'] not in refused]
            rows = [(task_rows[k]['room'], native_score(arms['unflagged'][k]),
                     native_score(arms['scripted'][k]), direct[k]['score']) for k in selected]
            intervals = bootstrap(rows, draws, seed)
            means = {a: pct([native_score(arms[a][k]) for k in selected]) for a in ARMS}
            direct_mean = pct([direct[k]['score'] for k in selected])
            output_groups[name][selection] = dict(items=len(selected), rooms=len({r[0] for r in rows}),
                native_pct=means['unflagged'], scripted_pct=means['scripted'], direct_pct=direct_mean,
                differences={a: dict(points=means[a] - direct_mean if selected else None,
                                     paired95_rooms=intervals[a]) for a in ARMS},
                counts=counts(selected, arms, direct, task_rows, refused))
    unit_check = {t: dict(other_units=extended_units[t]['groups']['other_units']['all_items'],
                         items=extended_units[t]['groups']['all']['all_items']) for t in TYPES[:2]}
    unit_check['matches_brief_full_counts'] = (unit_check[TYPES[0]] == dict(other_units=107, items=150)
                                              and unit_check[TYPES[1]] == dict(other_units=7, items=36))
    all_result = output_groups['all']['all_items']
    mode = 'PLUMBING — not model scores' if plumbing or subset or bundle.get('synthetic') else 'REAL_FULL_READ — pending independent analysis review'
    return dict(schema='native-vs-direct-devs1-v1', mode=mode, items=len(keys),
        method=dict(name='paired physical-room percentile bootstrap', draws=draws, seed=seed,
                    confidence=.95, quantile='linear interpolation at (draws - 1) * p',
                    weighting='sample rooms with replacement; sum item differences / sampled item count',
                    paired='same room sample for both native arms and direct; groups resampled separately',
                    caveat='Marginal intervals; no multiple-comparison adjustment; descriptive dev-S1 comparison'),
        room_map_summary=room_map['summary'], label_pairing=dict(status='PASS', counts=dict(label_counts), keys=dict(label_keys),
                    rule='primary: ground_truth == released_answer; otherwise ground_truth == answer',
                    evidence='Metadata labels, scorer and item identity checked; compact direct file does not contain raw labels or predictions'),
        unit_check=unit_check, r1_call_rates_recomputed=rates,
        r1_call_rates_reported={t:{k:report['per_type'][t][k] for k in rates[t]} for t in rates},
        r1_call_rate_definition='R1 decoded denominator excludes geometry refusals only; program refusals remain included',
        counts=counted, groups=output_groups, unit_scores_reported=bundle['unit_scores'],
        unit_scores_recomputed=original_units, unit_scores_with_direct=extended_units,
        unit_definition='other_units means not meter_based, including centimeters; unknown units remain separate',
        gravity_guard_report=report['gravity_guard_report'], geometry_refusal_comparison=comparison,
        program_refusals_reported=report.get('program_refusals'),
        conclusion=None if mode.startswith('PLUMBING') else dict(
            native_point_estimate_above_direct=all_result['differences']['unflagged']['points'] > 0,
            native_interval_excludes_zero_above=all_result['differences']['unflagged']['paired95_rooms'][0] > 0,
            headline_authorized=False, reason='Independent review required by F1 before any headline'),
        caveat_exact=CAVEAT,
        not_checked=['Original direct return archive, raw direct predictions, checkpoint byte identity, and scorer execution',
                     'Training-instance, candidate-universe, failed-ground and routing-sample caveats are supplied context, not re-audited',
                     'Gravity estimates and guard mathematics were not rerun; guard reports, capture lists and item flags were cross-checked',
                     'Independent analysis review and full-run job admission are outside this program'])


def markdown(result, output_path):
    source = str(output_path / 'NATIVE_VS_DIRECT.json')
    lines = [result['mode'], '', 'Every value in the following tables is sourced from `' + source + '`.', '',
             'Intervals resample physical rooms with replacement, retain all paired items, and recompute the item-weighted difference. '
             f"The report uses {result['method']['draws']} draws, fixed seed {result['method']['seed']}, and linear-interpolated percentile endpoints. "
             'Input paths/hashes are in the source JSON. Empty groups are NA.', '',
             '| Group | Selection | Items | Rooms | Native % | Scripted % | Direct % | Native − direct pp [95% CI] | Scripted − direct pp [95% CI] |',
             '|---|---|---:|---:|---:|---:|---:|---|---|']
    def f(x):
        return 'NA' if x is None else f'{x:.3f}'
    for group, selections in result['groups'].items():
        for selection, row in selections.items():
            diffs = []
            for a in ARMS:
                d = row['differences'][a]
                diffs.append('NA' if d['points'] is None else f"{d['points']:+.3f} [{d['paired95_rooms'][0]:+.3f}, {d['paired95_rooms'][1]:+.3f}]")
            lines.append(f"| {group} | {selection} | {row['items']} | {row['rooms']} | {f(row['native_pct'])} | {f(row['scripted_pct'])} | {f(row['direct_pct'])} | {' | '.join(diffs)} |")
    lines += ['', 'Counts use the same source JSON. No-answer counts exclude geometry refusals; all-item counts remain intact.', '',
              '| Arm | Items | Refused items | Refused captures | Capped | No answer | Program refusals | Call errors | Budget-truncated call items | Parse failed |',
              '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for a, c in result['counts'].items():
        fields = ('items','geometry_refused_items','geometry_refused_captures','capped','no_answer','program_refusals','call_errors','budget_truncated_call_items','parse_failed')
        lines.append('| ' + a + ' | ' + ' | '.join(str(c.get(x, 'NA')) for x in fields) + ' |')
    lines += ['', 'R1 call rates below match the admission report. Program refusals remain in the R1 decoded denominator.', '',
              '| Type | All items | Decoded items | Call rate decoded % | Call rate all % |', '|---|---:|---:|---:|---:|']
    for t, c in result['r1_call_rates_recomputed'].items():
        lines.append(f"| {t} | {c['items']} | {c['call_rate_denominator_items']} | {f(c['call_rate_decoded_items_pct'])} | {f(c['call_rate_all_items_pct'])} |")
    lines += ['', 'Unit groups use question_unit checked against the metadata question. Other units means not metre-based; centimeters are metric and other units. '
              'Passed-geometry unit counts exclude refused items. Direct uses the identical key groups.', '',
              '| Type | Unit group | Selection | Items | Native % | Scripted % | Direct % |', '|---|---|---|---:|---:|---:|---:|']
    for t, categories in result['unit_scores_with_direct'].items():
        for category, groups in categories.items():
            for name, c in groups.items():
                for selection, count, field in (('all_items','all_items','all_item_scores_pct'),('passed_geometry','items','scores_pct')):
                    lines.append(f"| {t} | {category}/{name} | {selection} | {c[count]} | {f(c[field]['unflagged'])} | {f(c[field]['scripted'])} | {f(c[field]['direct'])} |")
    lines += ['', 'Label pairing: ' + result['label_pairing']['rule'] + '. ' + result['label_pairing']['evidence'] + '.', '',
              'Observed unit counts (source: `' + source + '`): ' + json.dumps(result['unit_check'], sort_keys=True), '',
              'Required caveat, reproduced verbatim from `' + str(BUILD / 'BRIEF.md') + '`:', '', '> ' + CAVEAT, '',
              'The caveat describes the full cohort; subset outputs do not verify its full-cohort counts.', '',
              'Not checked:', ''] + ['- ' + s + '.' for s in result['not_checked']]
    lines += ['', 'Input provenance:', ''] + ['- `' + v['path'] + '` (sha256 `' + v['sha256'] + '`).' for v in result['sources'].values()]
    return '\n'.join(lines) + '\n'


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle', type=Path, required=True)
    parser.add_argument('--admission', type=Path, required=True)
    parser.add_argument('--direct', type=Path, default=DEFAULT_DIRECT)
    parser.add_argument('--tasks', type=Path, default=DEFAULT_TASKS)
    parser.add_argument('--frames', type=Path, default=DEFAULT_FRAMES)
    parser.add_argument('--camera-tasks', type=Path, default=DEFAULT_CAMERA)
    parser.add_argument('--output', type=Path, default=BUILD / 'out')
    parser.add_argument('--subset', type=Path, help='JSON key list; restrict inputs and label output PLUMBING')
    parser.add_argument('--plumbing', action='store_true')
    parser.add_argument('--draws', type=int, default=10000)
    parser.add_argument('--seed', type=int, default=20261115)
    args = parser.parse_args(argv)
    try:
        require(args.output.resolve().is_relative_to(BUILD), 'Output directory outside build')
        bundle = read(args.bundle)
        if args.subset:
            selected = read(args.subset)
            require(isinstance(selected, list) and len(selected) == len(set(selected)), 'Invalid subset keys')
            require(set(selected) <= set(bundle['expected_keys']), 'Subset keys outside bundle')
            bundle['expected_keys'] = selected
        tasks, room_map = metadata(args.tasks, args.frames, args.camera_tasks, set(bundle['expected_keys']))
        result = analyze(bundle, read(args.admission), read(args.direct), tasks, room_map,
                         subset=bool(args.subset), plumbing=args.plumbing, draws=args.draws, seed=args.seed)
        sources = {name: dict(path=str(path.resolve()), sha256=sha256(path)) for name, path in
                   (('bundle', args.bundle), ('admission', args.admission), ('direct', args.direct),
                    ('tasks', args.tasks), ('frames', args.frames), ('camera_tasks', args.camera_tasks),
                    ('script', Path(__file__)))}
        if args.subset:
            sources['subset'] = dict(path=str(args.subset.resolve()), sha256=sha256(args.subset))
        for name, path in (('brief', BUILD / 'BRIEF.md'), ('orchestrator', BUILD / 'in/20261115T2358Z_ORCH_GO_full.md'),
                           ('review', BUILD / 'in/REVIEW_VERDICT_C8R.md')):
            sources[name] = dict(path=str(path), sha256=sha256(path))
        result['sources'] = sources
        room_map.update(mode=result['mode'], sources=sources)
        write(args.output / 'ROOM_MAP.json', room_map)
        write(args.output / 'NATIVE_VS_DIRECT.json', result)
        (args.output / 'NATIVE_VS_DIRECT.md').write_text(markdown(result, args.output.resolve()))
        print(json.dumps(dict(status='PASS', mode=result['mode'], output=str(args.output / 'NATIVE_VS_DIRECT.json'))))
        return 0
    except (Refusal, KeyError, TypeError, OSError, ValueError) as exc:
        print('REFUSED: ' + str(exc), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
