"""Validate ARKit timing against the sealed reader before publishing any manifest.

Metadata only by default. --check-phases performs heavy local reads and requires
explicit operator approval. No model inference, downloads, or source edits occur.
Run with the local sam3_capretry_native_v1 Python and -B.
"""
import argparse
import copy
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import statistics
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent
BASE = ROOT.parent
SOURCE = Path('/scratch/jjyeung/orch_cd/k1_ops/work')
FINALIZER = BASE / 'codex_finalize_v2/finalize_k1.py'
MANIFEST_SHA = 'c3bbc378d659567c37dbb8aa12e5ab5f54fe23e40c2bd2dc198ab3d62d372380'
RATES_SHA = '36ae882f936ebc7a7d1a7651b5c53056c07d39ff552b2368a5c1e8068568d422'
KEYS = ('fps', 'timestamps', 'total_num_frames')
RATE_TOLERANCE = 0.005
PATHS = {
    'manifest': BASE / 'codex_finalize_v2/K1_MANIFEST.finalized.json',
    'wa': BASE / 'WA_OUT.jsonl',
    'plan': SOURCE / 'D3_FETCH_PLAN.json',
    'tokens': SOURCE / 'CANON_TOKENS.jsonl',
    'rates': BASE / 'kit07ca49df/k/frame_rates.json',
}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_bundle():
    bundle = {'pins': {}}
    for name, path in PATHS.items():
        raw = path.read_bytes()
        bundle['pins'][name] = {'path': str(path), 'sha256': sha(raw)}
        bundle[name] = ([json.loads(line) for line in raw.splitlines() if line.strip()]
                        if path.suffix == '.jsonl' else json.loads(raw))
    require(bundle['pins']['manifest']['sha256'] == MANIFEST_SHA, 'Input manifest hash differs')
    require(bundle['pins']['rates']['sha256'] == RATES_SHA, 'Sealed rate hash differs')
    require(bundle['rates']['schema'] == 's1-fps-authority-v1', 'Rate schema differs')
    return bundle


def first_tokens(rows):
    result = {}
    for row in rows:
        result.setdefault(row['canonical'], row['s'])
    return result


def indexed(rows, key):
    result = {}
    for row in rows:
        value = key(row)
        require(value not in result, 'Duplicate key: ' + str(value))
        result[value] = row
    return result


def pair_rates(points):
    require(len(points) >= 2, 'Too few timing samples')
    values = []
    for (i, t), (j, u) in zip(points, points[1:]):
        require(j > i and math.isfinite(t) and math.isfinite(u) and u > t,
                'Timing samples must increase strictly')
        values.append((j-i)/(u-t))
    return values


def nominal_rate(points):
    observed = statistics.median(pair_rates(points))
    nominal = round(observed)
    require(nominal > 0 and abs(observed/nominal - 1) <= RATE_TOLERANCE,
            'Median rate is not within 0.5% of a positive integer: ' + repr(observed))
    return float(nominal), observed


def intervals(points, fps):
    """Separate deliberately sparse samples from elapsed time beyond index spacing.

    An excess > 1.5 periods flags a possible timeline gap. With sparse receipts,
    this cannot identify absent archive members or localize a gap within a span.
    """
    pair_rates(points)
    result = []
    for (i, t), (j, u) in zip(points, points[1:]):
        elapsed = u-t
        excess = elapsed-(j-i)/fps
        result.append({'left_index': i, 'right_index': j,
                       'left_source_ts': t, 'right_source_ts': u,
                       'elapsed_s': elapsed, 'expected_elapsed_s': (j-i)/fps,
                       'implied_fps': (j-i)/elapsed, 'excess_s': excess,
                       'sample_spacing_over_1_5_periods': elapsed > 1.5/fps,
                       'missing_interval_over_1_5_periods': excess > 1.5/fps})
    return result


def derive(capture, wa, plan):
    require(not wa.get('error') and not wa.get('errors') and wa.get('misses') == [],
            'WA receipt reports failure')
    frames = indexed(wa['frames'], lambda row: row[0])
    need = indexed(plan['need'], lambda row: row[0])
    dense = [row['index'] for row in capture['dense_frames']]
    anchors = capture['anchor_indices']
    require(len(dense) == 64 and dense == sorted(set(dense)), 'Expected 64 ordered dense indices')
    require(len(anchors) == 32 and anchors == sorted(set(anchors)), 'Expected 32 ordered anchors')
    require(set(dense) == set(frames) == set(need), 'Dense, receipt and plan indices differ')
    require([dense[slot] for slot in capture['anchor_slots']] == anchors, 'Anchor slots differ')
    require(type(wa['n_members']) is int and wa['n_members'] > 1, 'Invalid archive count')
    require(math.isfinite(wa['first_ts']) and math.isfinite(wa['last_ts'])
            and wa['last_ts'] > wa['first_ts'], 'Invalid archive time span')
    for i in dense:
        row, requested = frames[i], need[i]
        require(len(row) == 6 and len(requested) == 3, 'Malformed timing row')
        require(wa['first_ts'] <= row[5] <= wa['last_ts'], 'Sample outside archive span')
        require(math.isfinite(row[4]) and abs((row[5]-requested[1])*1000-row[4]) <= 0.0011,
                'WA dt_ms disagrees with requested/source timestamps')
        require(abs(row[5]-requested[1]) <= (0.002 if requested[2] else 0.0105)+1e-6,
                'WA source timestamp exceeds fetch tolerance')
    point_sets = {
        'plan_dense': [(i, need[i][1]) for i in dense],
        'wa_dense': [(i, frames[i][5]) for i in dense],
        'plan_anchors': [(i, need[i][1]) for i in anchors],
        'wa_anchors': [(i, frames[i][5]) for i in anchors],
    }
    estimates = {name: nominal_rate(points) for name, points in point_sets.items()}
    require(len({v[0] for v in estimates.values()}) == 1, 'Anchor/dense/plan/WA rates disagree')
    fps = estimates['plan_dense'][0]
    # The reader uses this ordinal lower bound when its plan lacks raw_n.
    # n_members counts the separate archive grid and is never substituted here.
    timing = {'fps': fps, 'timestamps': [i/fps for i in anchors],
              'total_num_frames': max(anchors)+1}
    spans = {name: intervals(points, fps) for name, points in point_sets.items()}
    diagnostics = {
        'median_implied_fps': {name: value[1] for name, value in estimates.items()},
        'archive_n_members': wa['n_members'], 'archive_first_ts': wa['first_ts'],
        'archive_last_ts': wa['last_ts'],
        'archive_average_member_fps': (wa['n_members']-1)/(wa['last_ts']-wa['first_ts']),
        'total_num_frames_lower_bound': True,
        'anchor_indices': anchors,
        'anchor_source_timestamps': [frames[i][5] for i in anchors],
        'intervals': spans,
        'gaps': {name: [span for span in values if span['missing_interval_over_1_5_periods']]
                 for name, values in spans.items()},
        'receipt_pixel_hashes_differ_from_manifest': sum(
            frames[row['index']][1] != row['sha256'] for row in capture['dense_frames']),
        'gap_scope': 'Sparse-sample excess elapsed time; complete archive gaps are not observable.',
    }
    return timing, diagnostics


def evaluate(bundle, reader):
    captures = bundle['manifest']['captures']
    tokens = first_tokens(bundle['tokens'])
    wa = indexed(bundle['wa'], lambda row: row['s'])
    arkit = [c for c in captures if c['canonical'].startswith('arkitscenes/')]
    require(len(arkit) == 162, 'Expected 162 ARKit captures')
    require(len({tokens[c['canonical']] for c in arkit}) == 162, 'ARKit tokens are not unique')
    require(set(wa) == {tokens[c['canonical']] for c in arkit}, 'WA token coverage differs')
    rates = bundle['rates']
    covered = [c for c in arkit if 'd3/'+tokens[c['canonical']] in rates['by_scene']]
    uncovered = [c for c in arkit if c not in covered]
    require(len(covered) == 87 and len(uncovered) == 75, 'Expected coverage 87/75')
    report = {'passed': False, 'rule': 'median adjacent index/time slope; nearest positive integer within 0.5% in all four sample sets',
              'count_rule': 'Reader ordinal lower bound max(anchor_indices)+1; not archive n_members',
              'sources': bundle['pins'], 'agreement': [], 'uncovered': [], 'failures': []}
    candidates = {}
    for capture in covered:
        canonical = capture['canonical']
        token = tokens[canonical]
        row = {'canonical': canonical, 'token': token, 'agrees': False}
        try:
            require('d3/'+token not in rates.get('missing_arkit_scenes', []), 'Conflicting sealed coverage')
            expected, proof = reader.resolve_timing(capture, token, rates['by_scene']['d3/'+token],
                                                     None, None, authority=rates)
            row.update(expected=expected, expected_reader_proof=proof)
            candidate, diagnostics = derive(capture, wa[token], bundle['plan'][token])
            row.update(derived=candidate, diagnostics=diagnostics)
            row['field_agreement'] = {key: candidate[key] == expected[key] for key in KEYS}
            row['agrees'] = all(row['field_agreement'].values())
            if not row['agrees']:
                row['error'] = 'Exact sealed-reader timing comparison failed'
            else:
                checked, _ = reader.resolve_timing(capture, token, candidate['fps'], None,
                                                   candidate['fps'], authority=rates)
                require(checked == candidate, 'Reader changes derived timing')
                candidates[canonical] = candidate
        except (ValueError, TypeError, KeyError, IndexError) as error:
            row.update(agrees=False, error=str(error))
        report['agreement'].append(row)
        if not row['agrees']:
            report['failures'].append({'canonical': canonical, 'error': row['error']})
    # Gate precedes every uncovered derivation and every manifest construction/write.
    if report['failures']:
        return None, report
    for capture in uncovered:
        canonical = capture['canonical']
        token = tokens[canonical]
        row = {'canonical': canonical, 'token': token, 'reader_passed': False}
        try:
            candidate, diagnostics = derive(capture, wa[token], bundle['plan'][token])
            checked, proof = reader.resolve_timing(capture, token, candidate['fps'], None, candidate['fps'])
            require(checked == candidate, 'Reader changes derived timing')
            row.update(derived=candidate, diagnostics=diagnostics, reader_proof=proof, reader_passed=True)
            candidates[canonical] = candidate
        except (ValueError, TypeError, KeyError, IndexError) as error:
            row['error'] = str(error)
            report['failures'].append({'canonical': canonical, 'error': str(error)})
        report['uncovered'].append(row)
    if report['failures']:
        return None, report
    result = copy.deepcopy(bundle['manifest'])
    covered_names = {c['canonical'] for c in covered}
    sources = {}
    for capture in result['captures']:
        canonical = capture['canonical']
        if canonical in candidates:
            capture['model_row']['student_input'].update(candidates[canonical])
            sources[canonical] = ('frame_rates_07ca49df' if canonical in covered_names
                                  else 'derived_wa_validated')
        else:
            sources[canonical] = 'd12_mp4'
    # Keep existing capture keys byte-equivalent, including legacy timing_source.
    # The authoritative timing_source map is top-level to avoid extra digest edits.
    final = result['k1_finalize']
    final['schema'] = 'k1-finalize-arkit-timing-v1'
    final['input'] = bundle['pins']['manifest']
    final['timing'] = {
        'timing_source': sources,
        'source_counts': {name: list(sources.values()).count(name) for name in
                          ('d12_mp4', 'frame_rates_07ca49df', 'derived_wa_validated')},
        'arkit': {'applied': True, 'required': 162, 'covered': 87, 'derived': 75,
                  'exact_agreements': 87, 'missing': [], 'total_num_frames_lower_bound': True},
        'sources': bundle['pins'], 'rule': report['rule'], 'count_rule': report['count_rule'],
        'legacy_capture_timing_source': 'Preserved input field; use this top-level timing_source map.',
        'validation_scope': 'Reader metadata only; no pixel rehash or proof of full archive continuity.',
        'second_reader_required_before_own_run': True,
        'failures': {},
    }
    final['timing']['builder'] = {'path': str(Path(__file__).resolve()),
                                  'sha256': sha(Path(__file__).read_bytes())}
    final['timing']['reader_adapter'] = {'path': str(FINALIZER), 'sha256': sha(FINALIZER.read_bytes())}
    validate_changes(bundle['manifest'], result)
    report['passed'] = True
    return result, report


def validate_changes(before, after):
    normalized = copy.deepcopy(after)
    for old, new in zip(before['captures'], normalized['captures']):
        if old['canonical'].startswith('arkitscenes/'):
            for key in KEYS:
                new['model_row']['student_input'][key] = old['model_row']['student_input'][key]
        require(new == old, 'Unexpected capture edit: ' + old['canonical'])
    normalized['k1_finalize'] = before['k1_finalize']
    require(normalized == before, 'Unexpected top-level edit')


def write_new(path, value):
    path = Path(path).absolute()
    require(path.parent.resolve() == ROOT, 'Output must be directly inside codex_arkit_timing')
    raw = value.encode() if isinstance(value, str) else (json.dumps(value, indent=2, allow_nan=False)+'\n').encode()
    with path.open('xb') as stream:
        stream.write(raw)
    return {'path': str(path), 'sha256': sha(raw)}


def publish(bundle, reader, output):
    result, report = evaluate(bundle, reader)
    if result is not None:
        report['output'] = write_new(output, result)
    return report


def agreement_tsv(report):
    lines = ['canonical\ttoken\tfps_equal\ttimestamps_equal\tcount_equal\tsealed_fps\tderived_fps\tsealed_count\tderived_count\tresult']
    for row in report['agreement']:
        eq, ex, de = row.get('field_agreement', {}), row.get('expected', {}), row.get('derived', {})
        values = [row['canonical'], row['token'], *(eq.get(k, False) for k in KEYS),
                  ex.get('fps'), de.get('fps'), ex.get('total_num_frames'), de.get('total_num_frames'),
                  'PASS' if row['agrees'] else row.get('error', 'FAIL')]
        lines.append('\t'.join(map(str, values)))
    return '\n'.join(lines)+'\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check-phases', type=Path, help='Approved heavy I/O only: unchanged own/tower_sam checks')
    args = parser.parse_args()
    os.environ['CUDA_VISIBLE_DEVICES'] = ''
    reader = load_module('k1_timing_reader_adapter', FINALIZER)
    if args.check_phases:
        require(args.check_phases.resolve().parent == ROOT, 'Check only this build output')
        manifest = json.loads(args.check_phases.read_bytes())
        results = reader.check_phases(manifest, ('own', 'tower_sam'))
        write_new(ROOT/'PHASE_CHECKS.json', results)
        return
    report = publish(load_bundle(), reader, ROOT/'K1_MANIFEST.arkit_timing.json')
    write_new(ROOT/'TIMING_VALIDATION.json', report)
    write_new(ROOT/'AGREEMENT_87.tsv', agreement_tsv(report))
    write_new(ROOT/'DERIVED_75.json', report['uncovered'])
    print(json.dumps({'passed': report['passed'], 'agreements': sum(r['agrees'] for r in report['agreement']),
                      'uncovered_checked': len(report['uncovered']), 'failures': report['failures'],
                      'output': report.get('output')}, indent=2))
    if not report['passed']:
        raise SystemExit(2)


if __name__ == '__main__':
    main()
