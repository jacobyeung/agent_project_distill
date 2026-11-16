import argparse
import copy
import hashlib
import json
import math
import re
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

from . import compact_counted_v1 as compact


IDENTITY_FIELDS = ('qid', 'dataset', 'scene', 'question_type')
ANSWERONLY_SHA256 = 'fc668c74e909bafabb2541519924ab2e67b6313df046841daae58e630529847a'
RGB_FIELDS = {'question', 'options', 'frames', 'frame_indices', 'timestamps', 'fps', 'total_num_frames'}
SEMANTIC_STATUS = 'historical_control_not_recertified'


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def checked_bytes(pin):
    path = compact.safe_path(pin['path'])
    payload = path.read_bytes()
    require(compact.sha256_bytes(payload) == pin['sha256'], f'sha256_mismatch: {path}')
    return payload


def checked_json(pin):
    return compact.decode_json(checked_bytes(pin))


def identities(entries):
    result = {}
    for entry in entries:
        qid = compact.safe_qid(entry['qid'])
        require(qid not in result, f'duplicate_qid: {qid}')
        require(all(isinstance(entry.get(key), str) and entry[key] for key in IDENTITY_FIELDS),
                f'identity_schema: {qid}')
        result[qid] = entry
    return result


def scene_group(dataset, scene):
    dataset = 'scannetpp' if dataset == 'scannetppv2' else dataset
    match = re.fullmatch(r'(scene\d{4})_\d{2}', scene) if dataset == 'scannet' else None
    return f'{dataset}/{match.group(1) if match else scene}'


def normalized_groups(groups):
    return {scene_group(*group.split('/', 1)) for group in groups}


def validate_membership(subset, entries, split, forbidden_qids=(), forbidden_groups=()):
    require(subset.get('schema') == 'iteration-training-subset-v1' and subset.get('pool_id') == 'armc_v1c'
            and subset.get('seed') == 20260923, 'membership_contract')
    qids = subset['qids']
    require(len(qids) == subset['n'] and len(qids) == len(set(qids)), 'membership_qids')
    require([row['qid'] for row in subset['records']] == qids, 'membership_record_order')
    by_qid = identities(entries)
    train, heldout = set(split['train_candidate_qids']), set(split['heldout_qids'])
    train_groups = normalized_groups(split['train_group_ids'])
    heldout_groups = normalized_groups(split['heldout_group_ids'])
    for record in subset['records']:
        qid = record['qid']
        require(qid in by_qid, f'missing_selected_qid: {qid}')
        entry = by_qid[qid]
        require({key: entry[key] for key in IDENTITY_FIELDS} == record, f'membership_identity: {qid}')
        require(qid not in heldout, f'heldout_qid: {qid}')
        require(qid in train, f'not_published_train: {qid}')
        require(qid not in forbidden_qids, f'evaluation_qid: {qid}')
        group = scene_group(entry['dataset'], entry['scene'])
        require(group not in heldout_groups, f'heldout_scene: {qid}')
        require(group in train_groups, f'not_published_train_scene: {qid}')
        require(group not in forbidden_groups, f'evaluation_scene: {qid}: {group}')
    require(not train_groups & heldout_groups, 'split_scene_sides_conflict')
    return by_qid


def validate_output_membership(subset, entries):
    require([entry['qid'] for entry in entries] == subset['qids'], 'output_membership')
    by_qid = identities(entries)
    require([{key: by_qid[qid][key] for key in IDENTITY_FIELDS} for qid in subset['qids']]
            == subset['records'], 'output_identity')


def validate_rgb(inputs):
    require(isinstance(inputs, dict) and set(inputs) == RGB_FIELDS, 'rgb_schema')
    require(isinstance(inputs['question'], str) and inputs['question']
            and isinstance(inputs['options'], list)
            and all(isinstance(option, str) for option in inputs['options']), 'rgb_schema')
    for key in ('frames', 'frame_indices', 'timestamps'):
        require(isinstance(inputs[key], list) and len(inputs[key]) == 32, 'rgb_schema')
    require(all(isinstance(frame, dict) and set(frame) == {'path', 'sha256'} for frame in inputs['frames']),
            'rgb_schema')
    indices, timestamps = inputs['frame_indices'], inputs['timestamps']
    require(all(type(index) is int and index >= 0 for index in indices)
            and indices == sorted(set(indices)), 'rgb_schema')
    require(all(type(value) in (int, float) and math.isfinite(value) and value >= 0 for value in timestamps)
            and timestamps == sorted(set(timestamps)), 'rgb_schema')
    require(type(inputs['total_num_frames']) is int and inputs['total_num_frames'] > max(indices)
            and type(inputs['fps']) in (int, float) and math.isfinite(inputs['fps']) and inputs['fps'] > 0,
            'rgb_schema')


def validate_pair(entry, row, target_bytes, reference_entry, reference_row, reference_bytes, count_tokens):
    qid = entry['qid']
    for row_key, entry_key in compact.ROW_ALIGNED_FIELDS:
        require(row.get(row_key) == entry.get(entry_key), f'row_identity: {qid}: {row_key}')
        require(reference_row.get(row_key) == reference_entry.get(entry_key),
                f'row_identity: reference: {qid}: {row_key}')
    for key in IDENTITY_FIELDS + ('answer', 'source_index_sha256', 'generation_commit', 'validation_commit'):
        require(entry.get(key) == reference_entry.get(key), f'reference_identity: {qid}: {key}')
    answer, target = entry['answer'], row['target']
    require(isinstance(answer, str) and answer and answer == answer.strip() and '\n' not in answer
            and '\r' not in answer, f'answer_schema: {qid}')
    require(isinstance(target, str) and target, f'target_schema: {qid}')
    require(target_bytes in (target.encode('utf-8'), (target + '\n').encode('utf-8')),
            f'target_row_bytes: {qid}')
    require(target.count(compact.MARKER) == 1, f'closing_marker: {qid}')
    require(target.endswith('\n' + compact.MARKER + '\n' + answer)
            and target.splitlines()[-2:] == [compact.MARKER, answer], f'terminal_answer: {qid}')
    require(reference_row['target'] == answer
            and reference_bytes in (answer.encode('utf-8'), (answer + '\n').encode('utf-8')),
            f'reference_answer: {qid}')
    require(row['student_input'] == reference_row['student_input'], f'student_input_changed: {qid}')
    validate_rgb(row['student_input'])
    require(entry.get('tier_i', {}).get('all_deterministic_checks_satisfied') is True,
            f'source_admission: {qid}')
    tokens = count_tokens(target)
    require(type(tokens) is int and tokens > 0, f'target_token_count: {qid}')
    require(tokens <= compact.MAX_TOKENS, f'target_token_limit: {qid}: {tokens}')
    return {
        'target_tokens': tokens, 'answer_tokens': count_tokens(answer),
        'target_utf8_bytes': len(target.encode('utf-8')),
        'student_input_sha256': compact.digest_json(row['student_input']),
        'semantic_status': SEMANTIC_STATUS, 'claims_new_derivation': False,
        'inherited_text_flags': {
            'derivation_section': bool(re.search(r'^Derivations \([1-9]\d*\)$', target, re.MULTILINE)),
            'unspecified_numeric_meaning': 'no more specific geometric interpretation is asserted' in target,
            'radialized_xy_centres': 'from the world origin in the world X-Y plane' in target,
            'visibility_lists': 'recorded visible frames are' in target,
        },
    }


def copied_entry(entry, row_bytes, target_bytes, output):
    root = Path(output) / 'targets' / compact.safe_qid(entry['qid'])
    return {**entry, 'row_path': str(root / 'row.json'), 'row_sha256': compact.sha256_bytes(row_bytes),
            'target_path': str(root / 'target.txt'), 'sha256': compact.sha256_bytes(target_bytes)}


def copy_entry(entry, row_bytes, target_bytes, output):
    result = copied_entry(entry, row_bytes, target_bytes, output)
    compact.save(result['row_path'], row_bytes)
    compact.save(result['target_path'], target_bytes)
    return result


def bundle(entry):
    row_bytes = checked_bytes({'path': entry['row_path'], 'sha256': entry['row_sha256']})
    target_bytes = checked_bytes({'path': entry['target_path'], 'sha256': entry['sha256']})
    return compact.decode_json(row_bytes), row_bytes, target_bytes


def frame_check(pin, cache):
    key = (pin['path'], pin['sha256'])
    if key not in cache:
        digest = hashlib.sha256()
        with compact.safe_path(pin['path']).open('rb') as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b''):
                digest.update(chunk)
        require(digest.hexdigest() == pin['sha256'], f'frame_sha256: {pin["path"]}')
        cache.add(key)


def evaluation_exclusions(paths):
    qids, groups, pins = set(), set(), []
    expected = {'vsibench_answerable500': (200, 500), 'vstibench_repr450_v2': (150, 450)}
    seen = set()
    for path in paths:
        subset = compact.load_json(path)
        benchmark = subset['benchmark']
        require(benchmark in expected and benchmark not in seen, 'evaluation_subset_benchmark')
        seen.add(benchmark)
        n, full_n = expected[benchmark]
        require(subset['schema'] == 'iteration-evaluation-subset-v1' and subset['seed'] == 20260923
                and subset['n'] == n and len(subset['qids']) == n
                and len(set(subset['qids'])) == n, 'evaluation_subset_contract')
        manifest = checked_json(subset['benchmark_manifest'])
        inputs_pin = manifest['inputs']
        rows = [compact.decode_json(line) for line in checked_bytes(inputs_pin).splitlines() if line.strip()]
        full_qids = [row['qid'] for row in rows]
        require(manifest['benchmark'] == benchmark and len(full_qids) == full_n
                and len(set(full_qids)) == full_n and full_qids == manifest['ordered_ids']
                and set(subset['qids']) <= set(full_qids), 'evaluation_manifest_membership')
        qids.update(full_qids)
        for row in rows:
            dataset, separator, scene = row['video_id'].partition(':')
            require(bool(separator), 'evaluation_scene_identity')
            groups.add(scene_group(dataset, scene))
        pins.extend([compact.binding(path), subset['benchmark_manifest'], inputs_pin])
    require(seen == set(expected), 'both_evaluation_subsets_required')
    return qids, groups, pins


def load_contract(args):
    subset = compact.load_json(args.membership)
    require(subset['n'] == 1000, 'membership_must_be_1000')
    inputs = subset['inputs']
    require(compact.binding(args.source_index) == inputs['pool_index'], 'source_index_binding')
    source = compact.load_jsonl(args.source_index)
    require(len(source) == 3431, 'source_pool_size')
    published = checked_json(inputs['published_split'])
    protocol = checked_json(inputs['answeronly_protocol'])
    checked_bytes(inputs['derivation_receipt'])
    split = protocol['split']
    require(split['inherited_from'] == inputs['published_split'] and split['hashed_group_count'] == 0,
            'published_split_inheritance')
    require(set(split['train_group_ids']) <= set(published['train_group_ids'])
            and set(split['heldout_group_ids']) <= set(published['heldout_group_ids']), 'published_scene_sides')
    reference_pin = compact.binding(args.answeronly_index)
    require(reference_pin['sha256'] == ANSWERONLY_SHA256, 'answeronly_source_index_binding')
    reference = identities(compact.load_jsonl(args.answeronly_index))
    require(set(reference) == set(identities(source)), 'answeronly_pool_membership')
    forbidden_qids, forbidden_groups, evaluation_pins = evaluation_exclusions(args.eval_subset)
    by_qid = validate_membership(subset, source, split, forbidden_qids, forbidden_groups)
    pins = {'membership': compact.binding(args.membership), 'source_index': inputs['pool_index'],
            'answeronly_index': reference_pin, 'published_split': inputs['published_split'],
            'answeronly_protocol': inputs['answeronly_protocol'], 'evaluation': evaluation_pins}
    restricted = copy.deepcopy(published)
    restricted.update(schema='provisional-whole-scene-split-v1', train_candidate_qids=subset['qids'],
                      source_split=inputs['published_split'], source_membership=pins['membership'])
    return subset, by_qid, reference, restricted, pins


def percentile(values, fraction):
    values = sorted(values)
    if not values:
        return None
    position = fraction * (len(values) - 1)
    low, high = math.floor(position), math.ceil(position)
    return values[low] + (values[high] - values[low]) * (position - low)


def summary(audit, refused, attempted):
    by_family = defaultdict(list)
    for row in audit:
        by_family[row['question_type']].append(row['target_tokens'])
    tokens = [row['target_tokens'] for row in audit]
    return {
        'passed': not refused and len(audit) == attempted, 'attempted': attempted, 'admitted': len(audit),
        'refused': len(refused), 'refusal_reasons': dict(Counter(row['reason'].split(':', 1)[0] for row in refused)),
        'target_tokens': {'p50': percentile(tokens, .5), 'p95': percentile(tokens, .95),
                          'max': max(tokens, default=None), 'total': sum(tokens)},
        'per_family': {kind: {'rows': len(values), 'p50': percentile(values, .5),
                             'p95': percentile(values, .95), 'max': max(values)}
                       for kind, values in sorted(by_family.items())},
        'semantic_status': SEMANTIC_STATUS, 'claims_new_derivation': False,
        'inherited_text_flags': dict(Counter(key for row in audit for key, value in row['inherited_text_flags'].items() if value)),
        'copied_rows_fraction': 1.0 if audit else 0.0, 'gemini_calls': 0, 'gemini_tokens': 0,
        'full_sequence_and_eos_admission': 'required_from_unchanged_harness_stage_2',
    }


def jsonl(rows):
    return b''.join((json.dumps(row, sort_keys=True, ensure_ascii=False, allow_nan=False) + '\n').encode('utf-8')
                    for row in rows)


def provenance():
    root = Path(__file__).resolve().parents[2]
    status = subprocess.check_output(['git', '-C', str(root), 'status', '--short'], text=True)
    require(not status.strip(), 'renderer_checkout_dirty')
    commit = subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip()
    return {'commit': commit, 'module': compact.binding(__file__), 'helpers': compact.binding(compact.__file__)}


def run(args):
    output = compact.safe_path(args.output)
    subset, source, reference, split, pins = load_contract(args)
    count_tokens, tokenizer_pins = compact.tokenizer_counter(args.tokenizer)
    build = {'schema': 'literal-compact-control-v1', 'inputs': pins, 'code': provenance(),
             'tokenizer': tokenizer_pins, 'max_target_tokens': compact.MAX_TOKENS,
             'semantic_status': SEMANTIC_STATUS, 'new_derivations_allowed': False}
    verify = args.command == 'verify'
    if verify:
        require(compact.load_json(output / 'BUILD.json') == build, 'build_provenance_changed')
        entries = compact.load_jsonl(output / 'candidate_index.jsonl')
        validate_output_membership(subset, entries)
        output_entries = {entry['qid']: entry for entry in entries}
    else:
        compact.save(output / 'BUILD.json', build)
    admitted, audit, refused, frames = [], [], [], set()
    for index, qid in enumerate(subset['qids'], 1):
        entry, baseline = source[qid], reference[qid]
        try:
            row, row_bytes, target_bytes = bundle(entry)
            reference_row, _, reference_bytes = bundle(baseline)
            details = validate_pair(entry, row, target_bytes, baseline, reference_row, reference_bytes, count_tokens)
            for frame in row['student_input']['frames']:
                frame_check(frame, frames)
            if verify:
                copied = output_entries[qid]
                require(copied == copied_entry(entry, row_bytes, target_bytes, output), f'copied_index_changed: {qid}')
                _, copied_row_bytes, copied_target_bytes = bundle(copied)
                require(copied_row_bytes == row_bytes and copied_target_bytes == target_bytes,
                        f'copied_bytes_changed: {qid}')
            else:
                copied = copy_entry(entry, row_bytes, target_bytes, output)
            admitted.append(copied)
            audit.append({'qid': qid, 'question_type': entry['question_type'],
                          'source_row': {'path': entry['row_path'], 'sha256': entry['row_sha256']},
                          'source_target': {'path': entry['target_path'], 'sha256': entry['sha256']},
                          'reference_row': {'path': baseline['row_path'], 'sha256': baseline['row_sha256']},
                          'copied_row': {'path': copied['row_path'], 'sha256': copied['row_sha256']},
                          'copied_target': {'path': copied['target_path'], 'sha256': copied['sha256']},
                          'physical_scene_group': scene_group(entry['dataset'], entry['scene']), **details})
        except (ValueError, OSError, KeyError, compact.Deferral) as error:
            refused.append({'qid': qid, 'reason': str(error)})
        if index % 100 == 0:
            print(json.dumps({'checked': index, 'admitted': len(admitted), 'refused': len(refused)}), flush=True)
    result = summary(audit, refused, len(subset['qids']))
    result['unique_frame_files_verified'] = len(frames)
    if result['passed']:
        validate_output_membership(subset, admitted)
    if verify:
        require(not refused, f'verification_refusals: {refused[:3]}')
        require((output / 'COPY_AUDIT.jsonl').read_bytes() == jsonl(audit), 'audit_replay_changed')
        require(compact.load_json(output / 'ADMISSION.json') == result, 'admission_replay_changed')
        require(compact.load_json(output / 'split_trainer.json') == split, 'split_replay_changed')
        compact.save(output / 'VERIFICATION.json', {'passed': True, 'rows': len(admitted),
                     'candidate_index': compact.binding(output / 'candidate_index.jsonl'),
                     'admission': compact.binding(output / 'ADMISSION.json'), 'build': compact.binding(output / 'BUILD.json')})
    else:
        compact.save(output / 'COPY_AUDIT.jsonl', jsonl(audit))
        compact.save(output / 'REFUSALS.jsonl', jsonl(refused))
        compact.save(output / 'ADMISSION.json', result)
        compact.save(output / 'split_trainer.json', split)
        if result['passed']:
            compact.save(output / 'candidate_index.jsonl', jsonl(admitted))
    print(json.dumps(result, indent=2), flush=True)
    return 0 if result['passed'] else 1


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=('build', 'verify'))
    parser.add_argument('--membership', type=Path, required=True)
    parser.add_argument('--source-index', type=Path, required=True)
    parser.add_argument('--answeronly-index', type=Path, required=True)
    parser.add_argument('--eval-subset', type=Path, action='append', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--tokenizer', type=Path, default=compact.TOKENIZER)
    return run(parser.parse_args(argv))


if __name__ == '__main__':
    raise SystemExit(main())
