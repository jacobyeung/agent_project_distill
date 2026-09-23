import argparse
from collections import Counter, defaultdict
import copy
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
import json
from pathlib import Path
import re
import time

from .blocking import benchmark_blocking, scene_key
from .conventions import FAMILIES
from .formats import TYPE_FAMILY, format_value
from .io import canonical, digest, pin, read_json, read_jsonl, sha, source_commit, verify_pin
from .split import ARM_C_SHA256, group_id, load_split
from .targets import MARKER, render_target, validate_student_input, validate_target


LABEL = 'ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW'
GROUP_POLICY = ('ScanNet sceneNNNN scan suffixes share a group; other datasets use the supplied scene identity '
                'because no repeat-scan mapping is supplied. Heldout includes the canonical closure of selected physical groups.')
SAFE_QID = re.compile(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,159}')


class AdmissionError(ValueError):
    pass


def require(condition, reason):
    if not condition:
        raise AdmissionError(reason)


@dataclass
class Guard:
    train_qids: set
    heldout_qids: set
    train_groups: set
    heldout_groups: set
    forbidden_qids: set
    blocked_groups: set

    def check(self, row, side='train'):
        require(side in ('train', 'heldout'), 'unknown_split_side')
        require(not self.train_qids & self.heldout_qids, 'published_qid_overlap')
        require(not self.train_groups & self.heldout_groups, 'published_scene_overlap')
        qid = row.get('qid')
        require(isinstance(qid, str) and SAFE_QID.fullmatch(qid), 'unsafe_qid')
        require(qid not in self.forbidden_qids, 'benchmark_qid')
        require(scene_key(row['dataset'], row['scene']) not in self.blocked_groups, 'benchmark_scene')
        qids = self.train_qids if side == 'train' else self.heldout_qids
        groups = self.train_groups if side == 'train' else self.heldout_groups
        require(qid in qids, 'unpublished_or_wrong_side_qid')
        require(group_id(row['dataset'], row['scene']) in groups, 'unpublished_or_wrong_side_scene')
        try:
            validate_student_input(row['student_input'])
        except (KeyError, TypeError, ValueError) as error:
            raise AdmissionError('rgb_schema: ' + str(error)) from error


def check_gt(row, guard, *, side='train', max_bytes=4096, max_observations=32, conventions=None):
    guard.check(row, side)
    require(row.get('source') == 'gtmeasure_v1' and row['qid'].startswith('gtmeasure_'), 'foreign_gt_source')
    require(TYPE_FAMILY.get(row.get('source_question_type')) == row.get('family'), 'gt_family')
    target, answer = row['target'], row['ground_truth']['answer']
    observations, derivations = row['observations'], row['derivations']
    try:
        expected = render_target(observations, answer, derivations)
    except (KeyError, TypeError, ValueError) as error:
        raise AdmissionError('source_target: ' + str(error)) from error
    require(target == expected, 'source_target_bytes')
    require(len(target.encode()) <= max_bytes and len(observations) <= max_observations, 'target_length')
    require(target.count(MARKER) == 1 and target.endswith(MARKER + '\n' + answer), 'terminal_answer')
    validate_target(target)
    measurements = row['ground_truth']['measurements']
    require(measurements and all(Decimal(str(m['value_si'])).is_finite() and Decimal(str(m['value_si'])) >= 0
                                 for m in measurements), 'invalid_measurement')
    require(sorted({iid for m in measurements for iid in m['object_ids']}) == row['object_ids'], 'measurement_object_ids')
    kind = row['source_question_type']
    if conventions is not None:
        rounding_kind = 'absolute_distance_object' if kind == 'relative_distance_object' else kind
        for measurement in measurements:
            require(format_value(measurement['value_si'], rounding_kind, measurement['units'], conventions)
                    == measurement['rounded_value'], 'measurement_rounding')
    derivation = 'measured-scalar-no-derivation'
    if kind == 'relative_distance_object':
        options = row['student_input']['options']
        lettered = re.findall(r'^([A-D])\. ([^\n]+)$', row['student_input']['question'], re.MULTILINE)
        require(len(measurements) == len(options) == 4 and len(set(options)) == 4
                and [value for _, value in lettered] == options
                and [letter for letter, _ in lettered] == list('ABCD')
                and [m.get('label') for m in measurements] == options, 'mc_options')
        displayed = [Decimal(m['rounded_value']) for m in measurements]
        require(all(value.is_finite() and value >= 0 for value in displayed), 'mc_values')
        require(displayed.count(min(displayed)) == 1, 'mc_tie')
        best = displayed.index(min(displayed))
        require(answer == lettered[best][0], 'mc_answer')
        require(derivations == [f'The {options[best]} has the smallest distance, so the answer is {answer}.'], 'mc_derivation')
        reference = None
        for line, measurement in zip(observations[-4:], measurements):
            match = re.fullmatch(r'The closest-point distance from the (.+) to the nearest (.+) is ([0-9.]+) meters\.', line)
            require(match is not None and match[2] == measurement['label']
                    and match[3] == measurement['rounded_value'] and measurement['units'] == 'meters', 'mc_observation')
            reference = reference or match[1]
            require(match[1] == reference, 'mc_reference')
        derivation = 'unique-displayed-minimum'
    else:
        require(not derivations, 'unsupported_derivation')
        require(len(measurements) == 1 and measurements[0]['rounded_value'] == answer, 'scalar_answer_bytes')
        measurement = measurements[0]
        if kind == 'absolute_count':
            roster = [re.fullmatch(r'The (.+) instance (\d+) has center \([^)]+\) meters in the camera0 frame\.', line)
                      for line in observations[:-1]]
            require(roster and all(match is not None for match in roster), 'count_roster_shape')
            ids = [int(match[2]) for match in roster]
            labels = {match[1] for match in roster}
            require(len(labels) == 1 and len(set(ids)) == len(ids) and sorted(ids) == row['object_ids']
                    and str(len(ids)) == answer, 'count_roster')
            require(observations[-1] == f'The scene contains {answer} distinct {next(iter(labels))} instances.', 'count_statement')
            derivation = 'distinct-instance-count'
        else:
            units = re.escape(measurement['units'])
            number = re.escape(answer)
            patterns = {
                'absolute_size_object': rf'The longest dimension of the .+ is {number} {units}\.',
                'absolute_distance_object': rf'The closest-point distance between the .+ and the .+ is {number} {units}\.',
                'absolute_size_room': rf'The floor area is {number} {units}\.',
                'camera_obj_abs_dist': rf'In frame {row["frame_index"]}, the closest point of the .+ is {number} {units} from the camera\.',
            }
            require(kind in patterns and re.fullmatch(patterns[kind], observations[-1]), 'scalar_observation')
            if kind == 'camera_obj_abs_dist':
                require(type(row['frame_index']) is int and 1 <= row['frame_index'] <= 32, 'camera_frame')
    return {'answer': answer, 'target_bytes': len(target.encode()), 'observations': len(observations),
            'derivation': derivation, 'end_cue': MARKER, 'side': side, 'copied_target_bytes': True}


def check_answeronly(row, entry, target_bytes, guard, *, side='train'):
    guard.check(row, side)
    answer = str(entry['answer'])
    require(row['target'] == answer and target_bytes in (answer.encode(), (answer + '\n').encode())
            and '\n' not in answer and '\r' not in answer and len(answer.encode()) <= 64, 'answeronly_bytes')
    require(row['qid'] == entry['qid'], 'answeronly_identity')
    return {'answer': answer, 'target_bytes': len(target_bytes), 'end_cue': 'trainer-eos', 'side': side,
            'copied_target_bytes': True, 'derivation': 'none'}


def select_balanced(rows, size=1000, seed=20260923):
    require(type(size) is int and size > 0 and size % len(FAMILIES) == 0, 'balanced_size')
    require(len({row['qid'] for row in rows}) == len(rows), 'duplicate_gt_qid')
    groups = defaultdict(list)
    for row in rows:
        require(row['family'] in FAMILIES, 'selection_family')
        groups[row['family']].append(row)
    chosen = []
    for family in sorted(FAMILIES):
        require(len(groups[family]) >= size // len(FAMILIES), 'insufficient_family:' + family)
        ranked = sorted(groups[family], key=lambda row: (digest([seed, 'h05-gt-v2', row['qid']]), row['qid']))
        chosen.extend(ranked[:size // len(FAMILIES)])
    return sorted(chosen, key=lambda row: row['qid'])


def verify_frames(rows):
    seen = {}
    for row in rows:
        for frame in row['student_input']['frames']:
            path, expected = frame['path'], frame['sha256']
            require(path not in seen or seen[path] == expected, 'frame_pin_conflict')
            if path not in seen:
                require(Path(path).is_file() and sha(path) == expected, 'frame_hash:' + path)
                seen[path] = expected
    return {'unique_frames': len(seen), 'frame_pins_sha256': digest(seen)}


def mapped_row(source, commit, config_sha, source_index_sha, answer_entry=None):
    result = copy.deepcopy(source)
    result['materialization'] = {'commit': commit, 'config_sha256': config_sha,
                                 'source_index_sha256': source_index_sha, 'source_row_sha256': digest(source)}
    if answer_entry is None:
        result.update(answer=source['ground_truth']['answer'], pool='gtmeasure_v2', validation_commit=commit)
    return result


def write_new(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = data if isinstance(data, bytes) else (json.dumps(data, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + '\n').encode()
    with path.open('xb') as handle:
        handle.write(payload)
    return pin(path)


def materialize_row(root, source, commit, config_sha, source_index_sha, answer_entry=None, answer_bytes=None):
    qid = source['qid']
    require(isinstance(qid, str) and SAFE_QID.fullmatch(qid), 'unsafe_qid')
    row = mapped_row(source, commit, config_sha, source_index_sha, answer_entry)
    output = Path(root) / 'targets' / qid
    target_bytes = source['target'].encode() if answer_entry is None else answer_bytes
    require(isinstance(target_bytes, bytes), 'missing_answeronly_bytes')
    target_pin = write_new(output / 'target.txt', target_bytes)
    row_pin = write_new(output / 'row.json', row)
    entry = copy.deepcopy(answer_entry) if answer_entry is not None else {
        'qid': qid, 'dataset': row['dataset'], 'scene': row['scene'], 'question_type': row['category'],
        'pool': row['pool'], 'answer': row['answer'], 'generation_commit': row['generation_commit'],
        'validation_commit': commit, 'source_index_sha256': source_index_sha,
    }
    entry.update(target_path=target_pin['path'], sha256=target_pin['sha256'], row_path=row_pin['path'],
                 row_sha256=row_pin['sha256'], materialization_commit=commit, render_config_sha256=config_sha)
    return entry


def check_rendered(source, entry, commit, config_sha, source_index_sha, answer_entry=None, answer_bytes=None):
    row_path = verify_pin({'path': entry['row_path'], 'sha256': entry['row_sha256']})
    target_path = verify_pin({'path': entry['target_path'], 'sha256': entry['sha256']})
    expected = mapped_row(source, commit, config_sha, source_index_sha, answer_entry)
    require(read_json(row_path) == expected, 'rendered_fidelity')
    require(target_path.read_bytes() == (source['target'].encode() if answer_entry is None else answer_bytes), 'rendered_target_bytes')
    require(entry['qid'] == source['qid'] and entry['scene'] == source['scene']
            and entry['question_type'] == source['category'] and entry['dataset'] == source['dataset'], 'rendered_identity')
    require(entry['answer'] == (source['ground_truth']['answer'] if answer_entry is None else answer_entry['answer']), 'rendered_answer')
    require(entry['generation_commit'] == (source['generation_commit'] if answer_entry is None else answer_entry['generation_commit'])
            and entry['validation_commit'] == (commit if answer_entry is None else answer_entry['validation_commit'])
            and entry['materialization_commit'] == commit and entry['render_config_sha256'] == config_sha, 'rendered_provenance')
    if answer_entry is None:
        require(entry['pool'] == 'gtmeasure_v2' and entry['source_index_sha256'] == source_index_sha, 'rendered_source_metadata')
    else:
        copied = {key: value for key, value in answer_entry.items() if key not in ('target_path', 'sha256', 'row_path', 'row_sha256')}
        require(all(entry.get(key) == value for key, value in copied.items()), 'rendered_source_metadata')


def make_trainer_split(train, heldout, source_pins, commit, config_sha):
    train_qids, heldout_qids = {row['qid'] for row in train}, {row['qid'] for row in heldout}
    train_groups = {group_id(row['dataset'], row['scene']) for row in train}
    heldout_groups = {group_id(row['dataset'], row['scene']) for row in heldout}
    require(len(train_qids) == len(train) and len(heldout_qids) == len(heldout)
            and not train_qids & heldout_qids and not train_groups & heldout_groups, 'split_overlap')
    return {
        'schema': 'provisional-whole-scene-split-v1', 'seed': 17, 'heldout_fraction_of_groups': 0.1,
        'group_policy': GROUP_POLICY, 'selection_uses_correctness': False,
        'donor_group_count': len(train_groups | heldout_groups),
        'donor_scene_count': len({(row['dataset'], row['scene']) for row in [*train, *heldout]}),
        'train_candidate_qids': sorted(train_qids), 'heldout_qids': sorted(heldout_qids),
        'train_group_ids': sorted(train_groups), 'heldout_group_ids': sorted(heldout_groups),
        'train_scenes': sorted({row['dataset'] + '/' + row['scene'] for row in train}),
        'heldout_scenes': sorted({row['dataset'] + '/' + row['scene'] for row in heldout}),
        'source_splits': source_pins, 'renderer_commit': commit, 'render_config_sha256': config_sha,
        'provisional_diagnostic': LABEL, 'result_status': 'diagnostic, provisional',
        'benchmark_trained_diagnostic': True, 'benchmark_improvement_claim': False,
        'score_nomination_allowed': False, 'infrastructure_only': False,
    }


def index_bytes(entries):
    return ''.join(canonical(entry) + '\n' for entry in entries).encode()


def load_inputs(config):
    from .mix import measurement_rows

    directory = Path(config['gt_dir'])
    sides, manifest, split, source_pins = measurement_rows(directory)
    require(manifest['config']['structure'] == 'v2', 'source_not_v2')
    conventions = read_json(directory / 'CONVENTIONS.json')
    require(digest(conventions) == manifest['config']['conventions_sha256'], 'conventions_digest')
    policy = load_split(directory / 'split.json')
    policy.assert_train(sides['train'])
    require(all(policy.side(row['dataset'], row['scene']) == 'heldout' for row in sides['heldout']), 'gt_heldout_side')
    membership = read_json(config['membership'])
    require(membership.get('pool_id') == 'armc_v1c' and membership['n'] == 1000
            and len(membership['qids']) == len(set(membership['qids'])) == 1000, 'harness_membership')
    inherited_pin = membership['inputs']['published_split']
    require(inherited_pin['sha256'] == ARM_C_SHA256 and split['inherited_split']['sha256'] == ARM_C_SHA256, 'split_authority')
    inherited = read_json(verify_pin(inherited_pin))
    require(set(membership['qids']) <= set(inherited['train_candidate_qids']), 'harness_heldout_qid')
    answer_index = pin(config['answer_index'])
    require(answer_index['sha256'] == config['answer_index_sha256'], 'answer_index_digest')
    entries = list(read_jsonl(config['answer_index']))
    by_qid = {entry['qid']: entry for entry in entries}
    require(len(by_qid) == len(entries) == 3431, 'answeronly_source_census')
    evaluation, blocked = benchmark_blocking(manifest['benchmark_blocking'])
    forbidden = set()
    for info in evaluation.values():
        for row in read_json(info['path']):
            forbidden.update(str(row[key]) for key in ('id', 'qid', 'question_id') if key in row)
    for path, benchmark, n in zip(config['eval_subsets'], ('vsibench_answerable500', 'vstibench_repr450_v2'), (200, 150)):
        subset = read_json(path)
        require(subset['benchmark'] == benchmark and subset['n'] == n
                and len(set(subset['qids'])) == n, 'evaluation_subset')
        forbidden.update(map(str, subset['qids']))
        source_pins.append(pin(path))
    guard = Guard(
        set(split['train_qids']) | set(inherited['train_candidate_qids']),
        set(split['heldout_qids']) | set(inherited['heldout_qids']),
        {group for group, side in policy.known.items() if side == 'train'},
        {group for group, side in policy.known.items() if side == 'heldout'}, forbidden, blocked,
    )
    answer_rows = {}
    for qid in sorted(set(membership['qids']) | set(inherited['heldout_qids'])):
        require(qid in by_qid and qid.startswith('vsi590k_'), 'answeronly_membership')
        entry = by_qid[qid]
        row_spec = {'path': entry['row_path'], 'sha256': entry['row_sha256']}
        target_spec = {'path': entry['target_path'], 'sha256': entry['sha256']}
        row = read_json(verify_pin(row_spec))
        payload = verify_pin(target_spec).read_bytes()
        require(all(row[field] == entry[key] for field, key in (('qid', 'qid'), ('scene', 'scene'), ('category', 'question_type')))
                and row['dataset'] == entry.get('dataset', row['dataset']), 'answeronly_index_identity')
        check_answeronly(row, entry, payload, guard, side='train' if qid in membership['qids'] else 'heldout')
        answer_rows[qid] = (row, entry, payload)
    source_pins += [pin(config['membership']), answer_index, pin(inherited_pin['path'])]
    return {'sides': sides, 'gt_manifest': manifest, 'gt_split': split, 'conventions': conventions,
            'guard': guard, 'membership': membership, 'answer_rows': answer_rows, 'inherited': inherited,
            'source_pins': source_pins, 'source_splits': [pin(directory / 'split.json'), pin(inherited_pin['path'])]}


def admit_and_select(inputs, config):
    admitted, refused, checks = [], [], {}
    for row in inputs['sides']['train']:
        try:
            check = check_gt(row, inputs['guard'], max_bytes=config['max_bytes'],
                             max_observations=config['max_observations'], conventions=inputs['conventions'])
        except (AdmissionError, ValueError, KeyError, TypeError, IndexError) as error:
            refused.append({'qid': row.get('qid'), 'family': row.get('family'), 'reason': str(error)})
            continue
        admitted.append(row)
        checks[row['qid']] = check
    selected = select_balanced(admitted, size=config['size'], seed=config['seed'])
    return selected, refused, checks, len(admitted)


def source_for(qid, inputs):
    if qid in inputs['answer_rows']:
        row, entry, payload = inputs['answer_rows'][qid]
        return row, entry, payload, inputs['answer_index_sha256']
    row = inputs['gt_by_qid'][qid]
    side = 'train' if qid in inputs['gt_train_qids'] else 'heldout'
    return row, None, None, inputs['gt_manifest']['artifacts'][side + '.jsonl']['sha256']


def attach_sources(inputs, config):
    inputs['answer_index_sha256'] = config['answer_index_sha256']
    inputs['gt_by_qid'] = {row['qid']: row for side in inputs['sides'].values() for row in side}
    inputs['gt_train_qids'] = set(inputs['gt_split']['train_qids'])


def build(config, output, inputs, selected, refused, checks, admitted_count, commit):
    started = time.monotonic()
    output = Path(output).resolve()
    require(output.is_relative_to(Path(config['output_root']).resolve()) and output != Path(config['output_root']).resolve(), 'output_scope')
    require(not output.exists(), 'output_exists')
    train = list(selected)
    heldout = list(inputs['sides']['heldout'])
    if config['variant'] == 'v02_gt1000_ao1000':
        train += [inputs['answer_rows'][qid][0] for qid in inputs['membership']['qids']]
        heldout += [inputs['answer_rows'][qid][0] for qid in inputs['inherited']['heldout_qids']]
    train.sort(key=lambda row: row['qid'])
    heldout.sort(key=lambda row: row['qid'])
    for row in heldout:
        if row['qid'].startswith('gtmeasure_'):
            check_gt(row, inputs['guard'], side='heldout', max_bytes=1000000, max_observations=100000,
                     conventions=inputs['conventions'])
    config = {**config, 'renderer_commit': commit, 'source_pins': inputs['source_pins']}
    config_sha = digest(config)
    frames = verify_frames([*train, *heldout])
    split = make_trainer_split(train, heldout, inputs['source_splits'], commit, config_sha)
    output.mkdir(parents=True, exist_ok=False)
    train_entries, heldout_entries = [], []
    for rows, root, entries in ((train, output, train_entries), (heldout, output / 'heldout_context', heldout_entries)):
        for row in rows:
            source, entry, payload, source_sha = source_for(row['qid'], inputs)
            entries.append(materialize_row(root, source, commit, config_sha, source_sha, entry, payload))
    artifacts = [write_new(output / 'CONFIG.json', config),
                 write_new(output / 'candidate_index.jsonl', index_bytes(train_entries)),
                 write_new(output / 'heldout_context/candidate_index.jsonl', index_bytes(heldout_entries)),
                 write_new(output / 'protocol_context/candidate_index.jsonl', index_bytes(sorted(train_entries + heldout_entries, key=lambda e: e['qid']))),
                 write_new(output / 'split_trainer.json', split),
                 write_new(output / 'REFUSALS.json', refused),
                 write_new(output / 'GT_MEMBERSHIP.json', {'qids': [row['qid'] for row in selected], 'seed': config['seed'],
                                                          'by_family': dict(Counter(row['family'] for row in selected)),
                                                          'algorithm': 'equal-family-sha256-among-admitted-v1'})]
    duplicate_inputs = Counter(digest(row['student_input']) for row in train)
    targets_by_input = defaultdict(set)
    for row in train:
        targets_by_input[digest(row['student_input'])].add(str(source_for(row['qid'], inputs)[1]['answer'])
                                                        if row['qid'] in inputs['answer_rows'] else row['ground_truth']['answer'])
    require(all(len(answers) == 1 for answers in targets_by_input.values()), 'conflicting_identical_inputs')
    manifest = {
        'schema': 'swarm-h05-trainer-set-v1', 'variant': config['variant'], 'renderer_commit': commit,
        'config_sha256': config_sha, 'created_utc': datetime.now(timezone.utc).isoformat(),
        'source_rows_attempted': len(inputs['sides']['train']), 'source_rows_admitted': admitted_count,
        'source_rows_refused': len(refused), 'refusal_reasons': dict(Counter(row['reason'] for row in refused)),
        'training_rows': len(train), 'gt_training_rows': len(selected), 'answeronly_training_rows': len(train) - len(selected),
        'heldout_context_rows': len(heldout), 'heldout_context_is_not_training': True,
        'gt_by_family': dict(Counter(row['family'] for row in selected)),
        'selected_derivation_checks': dict(Counter(checks[row['qid']]['derivation'] for row in selected)),
        'max_gt_target_bytes': max(len(row['target'].encode()) for row in selected),
        'duplicate_input_groups': sum(count > 1 for count in duplicate_inputs.values()),
        'frames': frames, 'artifacts': artifacts, 'gemini': {'calls': 0, 'input_tokens': 0, 'output_tokens': 0},
        'elapsed_seconds': time.monotonic() - started, 'independent_admission_review': 'pending',
        'comparison_scope': 'count-matched, not qid-matched' if len(train) == len(selected) else 'augmentation; not compute-matched',
        'score_nomination_allowed': False,
    }
    write_new(output / 'MANIFEST.json', manifest)
    print(canonical({'output': str(output), **{key: manifest[key] for key in ('training_rows', 'gt_by_family', 'source_rows_refused', 'heldout_context_rows')}}), flush=True)
    return manifest


def verify_set(directory):
    directory = Path(directory).resolve()
    manifest = read_json(directory / 'MANIFEST.json')
    for spec in manifest['artifacts']:
        verify_pin(spec)
    config = read_json(directory / 'CONFIG.json')
    require(digest(config) == manifest['config_sha256'], 'config_digest')
    for spec in config['source_pins']:
        verify_pin(spec)
    inputs = load_inputs(config)
    attach_sources(inputs, config)
    selected, refused, checks, admitted_count = admit_and_select(inputs, config)
    expected_train = {row['qid'] for row in selected}
    expected_heldout = set(inputs['gt_split']['heldout_qids'])
    if config['variant'] == 'v02_gt1000_ao1000':
        expected_train.update(inputs['membership']['qids'])
        expected_heldout.update(inputs['inherited']['heldout_qids'])
    train = list(read_jsonl(directory / 'candidate_index.jsonl'))
    heldout = list(read_jsonl(directory / 'heldout_context/candidate_index.jsonl'))
    require(len(train) == len(expected_train) and {e['qid'] for e in train} == expected_train, 'training_membership')
    require(len(heldout) == len(expected_heldout) and {e['qid'] for e in heldout} == expected_heldout, 'heldout_membership')
    require(read_json(directory / 'REFUSALS.json') == refused and manifest['source_rows_admitted'] == admitted_count, 'admission_census')
    require(list(read_jsonl(directory / 'protocol_context/candidate_index.jsonl')) == sorted(train + heldout, key=lambda e: e['qid']), 'protocol_context')
    rows = {'train': [], 'heldout': []}
    for side, entries in (('train', train), ('heldout', heldout)):
        for entry in entries:
            source, answer_entry, answer_bytes, source_sha = source_for(entry['qid'], inputs)
            check_rendered(source, entry, manifest['renderer_commit'], manifest['config_sha256'], source_sha, answer_entry, answer_bytes)
            rows[side].append(source)
    split = make_trainer_split(rows['train'], rows['heldout'], inputs['source_splits'], manifest['renderer_commit'], manifest['config_sha256'])
    require(read_json(directory / 'split_trainer.json') == split, 'split_replay')
    require(verify_frames(rows['train'] + rows['heldout']) == manifest['frames'], 'frames_replay')
    return {'verdict': 'PASS', 'training_rows': len(train), 'heldout_context_rows': len(heldout),
            'heldout_in_train': len(expected_train & expected_heldout), 'manifest': pin(directory / 'MANIFEST.json'),
            'independent_admission_review': manifest['independent_admission_review'], 'gemini': manifest['gemini']}


def main():
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest='command', required=True)
    render = commands.add_parser('render')
    render.add_argument('--gt-dir', required=True)
    render.add_argument('--answer-index', required=True)
    render.add_argument('--answer-index-sha256', required=True)
    render.add_argument('--membership', required=True)
    render.add_argument('--eval-subsets', nargs=2, required=True)
    render.add_argument('--output-root', required=True)
    render.add_argument('--size', type=int, default=1000)
    render.add_argument('--seed', type=int, default=20260923)
    render.add_argument('--max-bytes', type=int, default=4096)
    render.add_argument('--max-observations', type=int, default=32)
    render.add_argument('--variant', choices=('v01_gt1000', 'v02_gt1000_ao1000', 'both'), default='both')
    verify = commands.add_parser('verify')
    verify.add_argument('--directory', required=True)
    args = parser.parse_args()
    if args.command == 'verify':
        print(canonical(verify_set(args.directory)))
        return
    config = vars(args).copy()
    config.pop('command')
    require(Path(config['output_root']).resolve().is_relative_to('/data2'), 'output_must_be_on_data2')
    commit = source_commit()
    inputs = load_inputs(config)
    attach_sources(inputs, config)
    selected, refused, checks, admitted = admit_and_select(inputs, config)
    variants = ('v01_gt1000', 'v02_gt1000_ao1000') if config['variant'] == 'both' else (config['variant'],)
    for variant in variants:
        build({**config, 'variant': variant}, Path(config['output_root']) / variant,
              inputs, selected, refused, checks, admitted, commit)


if __name__ == '__main__':
    main()
