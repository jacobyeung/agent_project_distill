import argparse
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import random
import re
import sys
import threading
import time

from tools.provenance import provenance
from . import answer_fullpool as full
from . import traceev_extract as extract

source = full.source
control = full.control
compact = full.compact
require = control.require
BASE_INDEX_SHA = 'b0658afc8c5a7439277985e59a13429d31b64dcbfb1f7f2087e49bb753456446'
BASE_SPLIT_SHA = '46d0d91058623f5031b2f548afb14bcc26c2cb3e44664b48edba767fdfdf7f70'
BASE_TRAIN = 25164
BASE_HELDOUT = 4235
SEED = 20260925
REPO = Path(__file__).resolve().parents[2]
MERGE_MAP = Path('/home/jjyeung/agent_project_distill/agent/scratch/devin_lanes/traceev_b2r_20260925/inputs/vsi_merge_map.json')


class Progress:
    def __init__(self, audit, heartbeat=None):
        self.audit = Path(audit)
        self.heartbeat = Path(heartbeat) if heartbeat else None
        self.message = 'Starting trace evidence operation'
        self.stop = threading.Event()
        self.thread = threading.Thread(target=self.loop, daemon=True)

    def emit(self):
        line = f'{source.utc()} | {self.message}\n'
        with (self.audit / 'HEARTBEAT.log').open('a') as stream:
            stream.write(line)
        if self.heartbeat:
            with self.heartbeat.open('a') as stream:
                stream.write(line)
        print(line.rstrip(), flush=True)

    def step(self, message):
        self.message = message
        self.emit()

    def loop(self):
        while not self.stop.wait(120):
            self.emit()

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *_):
        self.stop.set()
        self.thread.join()


def io_map(function, items, workers):
    require(1 <= workers <= 64, 'io_workers_must_be_1_to_64')
    with ThreadPoolExecutor(max_workers=workers) as pool:
        yield from pool.map(function, items)


def inventory(root, workers):
    names = sorted(full.inventory_names(root))
    return dict(io_map(lambda name: (name, source.pin(root / name)), names, workers))


def carry_bundle(item, base, layout, side):
    row, line = item
    entry = base['index'][row['qid']]
    layout_row, row_bytes, target_bytes = control.bundle(entry)
    require(layout_row == row, 'base_mix_layout_identity')
    require(target_bytes in (row['target'].encode(), (row['target'] + '\n').encode()), 'base_target_identity')
    base['provisional'].validate_rgb(row['student_input'])
    copied = control.copy_entry(entry, row_bytes, target_bytes, layout)
    origin = {'qid': row['qid'], 'root': 'v3-carried', 'side': side,
              'source_row': {'path': entry['row_path'], 'sha256': entry['row_sha256']},
              'source_target': {'path': entry['target_path'], 'sha256': entry['sha256']}}
    return row, line, copied, origin


def materialize_evidence(fact, inputs, layout):
    row = packed_evidence(fact, inputs)
    return row, evidence_entry(row, layout)


def load_base(mix, layout, trainer):
    index_pin = full.checked_authority(layout / 'candidate_index.jsonl', BASE_INDEX_SHA)
    split_pin = full.checked_authority(layout / 'split_trainer.json', BASE_SPLIT_SHA)
    require(source.sha(mix / 'split_trainer.json') == BASE_SPLIT_SHA, 'base_split_layout_identity')
    splitter, provisional = full.trainer_modules(trainer)
    record = provisional.load_inherited_record(split_pin)
    base, index, manifest = full.read_base(mix, layout, 0, BASE_TRAIN)
    require(len(base['heldout']) == BASE_HELDOUT, 'base_heldout_count')
    rows = {row['qid']: row for side in base.values() for row, _ in side}
    require(len(rows) == BASE_TRAIN + BASE_HELDOUT and set(rows) == set(index), 'base_membership')
    for side, key in (('train', 'train_candidate_qids'), ('heldout', 'heldout_qids')):
        require(sorted(row['qid'] for row, _ in base[side]) == sorted(record[key]), 'base_split_membership')
    require(not control.normalized_groups(record['train_group_ids']) &
            control.normalized_groups(record['heldout_group_ids']), 'base_heldout_group_overlap')
    base_inputs = control.checked_json(manifest['artifacts']['BUILD_INPUTS.json'])
    forbidden = full.benchmark_groups(base_inputs)
    pins = {'manifest': source.pin(mix / 'MANIFEST.json'),
            'materialization': source.pin(layout / 'MATERIALIZATION.json'),
            'candidate_index': index_pin, 'split_trainer': split_pin,
            'split': source.pin(mix / 'split.json'), 'inputs': source.pin(mix / 'BUILD_INPUTS.json')}
    require(source.read_json(pins['materialization']['path'])['artifacts']['candidate_index.jsonl'] == index_pin,
            'base_candidate_binding')
    return {'base': base, 'rows': rows, 'index': index, 'record': record, 'pins': pins,
            'benchmark_sources': base_inputs['benchmark_sources'], 'forbidden': forbidden,
            'splitter': splitter, 'provisional': provisional}


def exclusions(path, base):
    requested = [] if path is None else [line.strip() for line in Path(path).read_text().splitlines() if line.strip()]
    require(len(requested) == len(set(requested)), 'duplicate_base_exclusion')
    require(set(requested) <= set(base['rows']), 'unknown_base_exclusion')
    train = set(base['record']['train_candidate_qids'])
    records = [{'qid': qid, 'label': base['rows'][qid]['target'], 'index_answer': base['index'][qid]['answer'],
                'side': 'train' if qid in train else 'heldout', 'excluded': qid in train,
                'dataset': base['rows'][qid]['dataset'], 'scene': base['rows'][qid]['scene']}
               for qid in requested]
    return {qid for qid in requested if qid in train}, records


def counting_catalog(base):
    catalog = defaultdict(list)
    for qid, entry in base['index'].items():
        if entry['question_type'] == 'object_counting':
            row = base['rows'][qid]
            selected = {key: entry[key] for key in ('qid', 'dataset', 'scene', 'question_type', 'row_path', 'row_sha256')}
            catalog[(row['dataset'], row['scene'])].append({'entry': selected,
                'question': row['student_input']['question'], 'label': row['target'],
                'frames_sha256': extract.digest(row['student_input']['frames'])})
    return catalog


def evidence_rows(path, base, progress):
    rows = list(source.read_jsonl(path))
    record = base['record']
    train, heldout = set(record['train_candidate_qids']), set(record['heldout_qids'])
    train_groups = control.normalized_groups(record['train_group_ids'])
    heldout_groups = control.normalized_groups(record['heldout_group_ids'])
    train_scenes, heldout_scenes = set(record['train_scenes']), set(record['heldout_scenes'])
    forbidden_qids, forbidden_groups = base['forbidden']
    base_frames = {(frame['path'], frame['sha256']) for row in base['rows'].values() for frame in row['student_input']['frames']}
    catalog = counting_catalog(base)
    seen_ids, seen_facts = set(base['rows']), set()
    for i, row in enumerate(rows):
        qid, kind = row['qid'], row['question_type']
        compact.safe_qid(qid)
        require(qid not in seen_ids, 'duplicate_evidence_qid')
        seen_ids.add(qid)
        group = control.scene_group(row['dataset'], row['scene'])
        scene = row['dataset'] + '/' + row['scene']
        require(group not in heldout_groups and scene not in heldout_scenes, 'evidence_heldout_scene')
        require(qid not in forbidden_qids and group not in forbidden_groups, 'evidence_benchmark_overlap')
        require(group in train_groups and scene in train_scenes, 'evidence_not_v3_train_scene')
        require(kind in extract.KINDS and row['supports'] == extract.SUPPORTS[kind], 'evidence_kind_contract')
        require(bool(re.fullmatch(r'[0-9a-f]{40}', row['extractor_commit'])), 'extractor_commit_contract')
        extract.validate_text(row['question'], row['target'])
        gt = row['evidence']['gt']
        expected_question, expected_target = extract.render(kind, gt['labels'], gt['values_unrounded'])
        require((row['question'], row['target']) == (expected_question, expected_target), 'evidence_template_target')
        if kind in ('traceev_size', 'traceev_abs_distance'):
            number = r'\d+\.\d{2}'
            pattern = number if kind == 'traceev_abs_distance' else number + r', ' + number + r', ' + number
            require(bool(re.fullmatch(pattern, row['target'])), 'evidence_two_decimals')
        control.validate_rgb(row['student_input'])
        require(row['student_input']['question'] == row['question'] and row['student_input']['options'] == [],
                'evidence_student_input_question')
        require(all((frame['path'], frame['sha256']) in base_frames for frame in row['student_input']['frames']),
                'evidence_new_frame')
        source_qids = row['source_qids']
        require(isinstance(source_qids, list) and source_qids and len(set(source_qids)) == len(source_qids), 'source_qids_contract')
        traces = set()
        for source_qid in source_qids:
            require(source_qid not in heldout, 'evidence_heldout_source')
            require(source_qid in train and source_qid not in forbidden_qids, 'evidence_source_not_train')
            original = base['rows'][source_qid]
            require((row['dataset'], row['scene']) == (original['dataset'], original['scene']), 'evidence_source_scene')
            require(row['student_input'] == {**original['student_input'], 'question': row['question'], 'options': []},
                    'evidence_student_input_changed')
            pin = base['index'][source_qid].get('strict_accepted_trace') or original.get('sources', {}).get('raw')
            require(bool(pin), 'evidence_source_trace_missing')
            traces.add((pin['path'], pin['sha256']))
        require(traces == {(pin['path'], pin['sha256']) for pin in row['source_traces']}, 'evidence_trace_bindings')
        frame_sha = extract.digest(row['student_input']['frames'])
        identity = gt['labels'][0] if kind.startswith('traceev_frames_') else sorted(gt['instance_ids'])
        fact = [frame_sha, kind, identity]
        require(row['fact_key'] == fact and row['evidence']['selected_frames_sha256'] == frame_sha, 'evidence_fact_key')
        digest = extract.digest(fact)
        require(digest not in seen_facts, 'duplicate_evidence_fact')
        seen_facts.add(digest)
        require(qid == f"traceev__{row['scene']}__{kind}__{digest[:12]}", 'evidence_qid_digest')
        require(row['evidence']['v3_index_sha256'] == BASE_INDEX_SHA and
                row['evidence']['v3_split_sha256'] == BASE_SPLIT_SHA, 'evidence_base_pins')
        owner = row['evidence']['source_entry']['qid']
        require(owner in source_qids, 'evidence_owner')
        original_entry = base['index'][owner]
        for key in ('qid', 'dataset', 'scene', 'question_type', 'row_path', 'row_sha256'):
            require(row['evidence']['source_entry'][key] == original_entry[key], 'evidence_source_entry')
        checks, checked_entries = [], []
        if kind == 'traceev_count_list':
            checks, checked_entries = extract.count_label_checks(original_entry, base['rows'][owner], gt['labels'][0],
                gt['values_unrounded']['count'], catalog[(row['dataset'], row['scene'])])
        require(row.get('label_check') == (checks[0] if checks else None), 'evidence_label_check')
        require(row['evidence'].get('label_checks', []) == checks and
                row['evidence'].get('counting_entries', []) == checked_entries, 'evidence_label_check_coverage')
        if i % 1000 == 0:
            progress.step(f'Validated {i + 1} evidence rows against v3')
    return rows, base_frames


def filter_merge_groups(rows, merge_pin):
    pairs = control.checked_json(merge_pin)
    require(isinstance(pairs, list) and all(isinstance(pair, list) and len(pair) == 2 and
            all(isinstance(label, str) and label == label.lower().strip() and label for label in pair) for pair in pairs),
            'merge_map_schema')
    groups = {}
    for parent, child in pairs:
        merged = {parent, child} | groups.get(parent, set()) | groups.get(child, set())
        for label in merged:
            groups[label] = merged
    cached, retained, dropped = {}, [], []
    for row in rows:
        gt = row['evidence']['gt']
        pin = gt['assets']['instances']
        key = (pin['path'], pin['sha256'])
        if key not in cached:
            instances = control.checked_json(pin)
            require(isinstance(instances.get('segGroups'), list), 'instances_segGroups_schema')
            cached[key] = {group['label'].strip().lower() for group in instances['segGroups']}
        labels = cached[key]
        siblings = {label: sorted((groups.get(label, set()) - {label}) & labels) for label in gt['labels']}
        siblings = {label: values for label, values in siblings.items() if values}
        if siblings:
            dropped.append({'qid': row['qid'], 'question_type': row['question_type'], 'dataset': row['dataset'],
                'scene': row['scene'], 'reason': 'vsi_merge_group_sibling', 'siblings': siblings, 'instances': pin})
        else:
            retained.append(row)
    return retained, dropped


def packed_evidence(row, inputs):
    return {**row, 'category': row['question_type'], 'generation_commit': inputs['provenance']['repo_commit'],
            'validation_commit': inputs['provenance']['repo_commit'], 'config_sha256': inputs['provenance']['config_sha256'],
            'target_provenance': {'source': 'traceev_gt_tool_evidence', 'evidence_rows': inputs['evidence'],
                                  'extractor_commit': row['extractor_commit']}}


def evidence_entry(row, layout):
    qid = compact.safe_qid(row['qid'])
    shard = hashlib.sha256(qid.encode()).hexdigest()[:2]
    root = layout / 'targets_traceev' / shard / qid
    root.mkdir(parents=True, exist_ok=False)
    row_bytes, target_bytes = compact.canonical_bytes(row), (row['target'] + '\n').encode()
    (root / 'row.json').write_bytes(row_bytes)
    (root / 'target.txt').write_bytes(target_bytes)
    return {'qid': qid, 'dataset': row['dataset'], 'scene': row['scene'], 'question_type': row['category'],
            'pool': 'traceev_gt_tool_evidence', 'answer': row['target'],
            'generation_commit': row['generation_commit'], 'validation_commit': row['validation_commit'],
            'config_sha256': row['config_sha256'], 'row_path': str(root / 'row.json'),
            'row_sha256': compact.sha256_bytes(row_bytes), 'target_path': str(root / 'target.txt'),
            'sha256': compact.sha256_bytes(target_bytes)}


def composition(partition, evidence, excluded, base, extraction_summary, evidence_drops):
    evidence_ids = {row['qid'] for row in evidence}
    counts = {side: {'total': len(rows), 'carried_rows': sum(row['qid'] not in evidence_ids for row in rows),
                    'evidence_rows': sum(row['qid'] in evidence_ids for row in rows),
                    'by_question_type': dict(sorted(Counter(row['category'] for row in rows).items()))}
              for side, rows in partition.items()}
    types = sorted({row['category'] for row in base['rows'].values()} | set(extract.KINDS))
    return {**counts, 'by_type': {kind: {side: counts[side]['by_question_type'].get(kind, 0)
                                      for side in partition} for kind in types},
            'evidence_by_supported_type': dict(sorted(Counter(support for row in evidence for support in row['supports']).items())),
            'label_checks': extract.label_check_summary(evidence),
            'base_exclusions': {'excluded_train': sum(row['excluded'] for row in excluded),
                                'listed_heldout_preserved': sum(not row['excluded'] for row in excluded),
                                'by_dataset': dict(Counter(row['dataset'] for row in excluded if row['excluded']))},
            'trace_gt_agreement': extraction_summary.get('agreements', {}),
            'trace_gt_agreement_scope': 'Extractor-wide authenticated summary; agreement does not filter rows',
            'evidence_rows': len(evidence), 'base_rows': len(base['rows']),
            'evidence_rows_before_merge_filter': len(evidence) + len(evidence_drops),
            'evidence_drops': {'vsi_merge_group_sibling': len(evidence_drops)},
            'evidence_drops_by_kind': dict(sorted(Counter(row['question_type'] for row in evidence_drops).items()))}


def composition_text(value):
    lines = ['# Trace-evidence set composition', '',
             f"The set contains {value['train']['total']:,} training rows and {value['heldout']['total']:,} unchanged heldout rows.",
             f"The builder added {value['evidence_rows']:,} evidence rows and excluded {value['base_exclusions']['excluded_train']:,} listed v3 training rows.",
             f"It preserved {value['base_exclusions']['listed_heldout_preserved']:,} listed heldout rows.", '',
             '| Question type | Train | Heldout |', '|---|---:|---:|']
    lines += [f"| {kind} | {counts['train']} | {counts['heldout']} |" for kind, counts in value['by_type'].items()]
    lines += ['', '| Supported task | Evidence rows |', '|---|---:|']
    lines += [f'| {kind} | {count} |' for kind, count in value['evidence_by_supported_type'].items()]
    lines += ['', 'Multi-support rows count toward each supported task. Grounding is an auxiliary task.', '',
              '| Dataset | Compared count rows | Disagreements | Disagreement percent |', '|---|---:|---:|---:|']
    lines += [f"| {dataset} | {counts.get('compared_rows', 0)} | {counts.get('disagreement_rows', 0)} | {counts['disagreement_percent']:.2f} |"
              for dataset, counts in value['label_checks'].items()]
    lines += ['', 'GT-derived counts remain targets when v3 labels disagree. Count-one disagreements are exempt from the count-one cap.',
              '', '| Evidence kind | VSI merge-group sibling drops |', '|---|---:|']
    lines += [f'| {kind} | {count} |' for kind, count in value['evidence_drops_by_kind'].items()]
    lines += ['', f"The merge-label filter dropped {value['evidence_drops']['vsi_merge_group_sibling']} rows after authenticating their GT instance assets.",
              '', '## Trace and GT agreement', '', value['trace_gt_agreement_scope'] + '.',
              json.dumps(value['trace_gt_agreement'], sort_keys=True), '']
    return '\n'.join(lines)


def check_outputs(args):
    outputs = [args.output_mix.resolve(), args.output_layout.resolve(), args.audit.resolve()]
    protected = [args.base_mix.resolve(), args.base_layout.resolve(), REPO, Path('/home/jjyeung/agent_project_distill')]
    for path in outputs:
        require(path.is_relative_to('/data2'), 'output_must_be_under_data2')
        require(not path.exists(), 'output_exists_use_new_directory: ' + str(path))
        require(not any(path == other or path.is_relative_to(other) or other.is_relative_to(path) for other in protected),
                'output_source_overlap')
    for i, path in enumerate(outputs):
        require(not any(path == other or path.is_relative_to(other) or other.is_relative_to(path) for other in outputs[i + 1:]),
                'output_overlap')
    return outputs


def build(args):
    started = time.monotonic()
    require(1 <= args.io_workers <= 64, 'io_workers_must_be_1_to_64')
    mix, layout, audit = check_outputs(args)
    audit.mkdir(parents=True)
    config = {'base_mix': str(args.base_mix.resolve()), 'base_layout': str(args.base_layout.resolve()),
              'evidence': source.pin(args.evidence), 'output_mix': str(mix), 'output_layout': str(layout),
              'merge_map': source.pin(args.merge_map),
              'exclude_base_qids': source.pin(args.exclude_base_qids) if args.exclude_base_qids else None,
              'trainer': str(args.trainer.resolve()), 'sample_seed': SEED, 'io_workers': args.io_workers}
    source.write_json(audit / 'CONFIG.json', config)
    code = provenance(audit / 'CONFIG.json')
    require(not code['dirty'], 'dirty_tree_commit_before_build')
    with Progress(audit, args.heartbeat) as progress:
        progress.step('Authenticate v3 inputs and inherited scene split')
        base = load_base(args.base_mix.resolve(), args.base_layout.resolve(), args.trainer.resolve())
        excluded_ids, excluded = exclusions(args.exclude_base_qids, base)
        facts, _ = evidence_rows(args.evidence, base, progress)
        require(source.pin(args.evidence) == config['evidence'], 'evidence_changed_during_read')
        summary_path = args.evidence.parent / 'SUMMARY.json'
        extraction_summary = source.read_json(summary_path) if summary_path.is_file() else {}
        if extraction_summary:
            require(extraction_summary['sha256'] == config['evidence']['sha256'] and extraction_summary['rows'] == len(facts),
                    'extractor_summary_binding')
        source_evidence_rows = len(facts)
        facts, evidence_drops = filter_merge_groups(facts, config['merge_map'])
        full.write_lines(audit / 'EVIDENCE_DROPS.jsonl', evidence_drops)
        inputs = {'schema': 'traceev-build-inputs-v1', **config, 'provenance': code, 'base': base['pins'],
                  'benchmark_sources': base['benchmark_sources'], 'trainer_commit': full.inherited.common.TRAINER_COMMIT,
                  'extractor_summary': source.pin(summary_path) if extraction_summary else None,
                  'code': {str(path.relative_to(REPO)): source.pin(path) for path in
                           (Path(__file__), Path(extract.__file__), Path(full.__file__), Path(source.__file__),
                            Path(control.__file__), Path(compact.__file__), Path(full.inherited.__file__), REPO / 'tools/provenance.py')}}
        for root in (mix, layout):
            root.mkdir(parents=True)
            source.write_json(root / 'BUILD_INPUTS.json', inputs)
        source.write_json(audit / 'BUILD_INPUTS.json', inputs)
        full.write_lines(audit / 'BASE_EXCLUSIONS.jsonl', excluded)
        entries, rows, origins = [], [], []
        partition = {'train': [], 'heldout': []}
        progress.step('Carry authenticated v3 row and target bytes')
        for side in partition:
            selected = (item for item in base['base'][side] if item[0]['qid'] not in excluded_ids)
            with (mix / (side + '.jsonl')).open('wb') as stream:
                for row, line, entry, origin in io_map(
                        lambda item: carry_bundle(item, base, layout, side), selected, args.io_workers):
                    entries.append(entry)
                    rows.append(row)
                    partition[side].append(row)
                    origins.append(origin)
                    stream.write(line)
                    if len(rows) % 2000 == 0:
                        progress.step(f'Carried {len(rows)} v3 rows byte identically')
        progress.step('Materialize sharded evidence rows on training side')
        with (mix / 'train.jsonl').open('ab') as stream:
            for i, (row, entry) in enumerate(io_map(
                    lambda fact: materialize_evidence(fact, inputs, layout), facts, args.io_workers), 1):
                entries.append(entry)
                rows.append(row)
                partition['train'].append(row)
                origins.append({'qid': row['qid'], 'root': 'traceev_gt_tool_evidence', 'side': 'train',
                                'source_qids': row['source_qids'], 'evidence_rows': config['evidence']})
                stream.write(full.inherited.line_bytes(row))
                if i % 2000 == 0:
                    progress.step(f'Materialized {i} sharded evidence rows')
        require(BASE_TRAIN + BASE_HELDOUT - len(excluded_ids) < 40000, 'base_directory_entry_limit')
        shards = Counter(hashlib.sha256(row['qid'].encode()).hexdigest()[:2] for row in facts)
        require(all(count < 40000 for count in shards.values()), 'evidence_directory_entry_limit')
        split = full.emit_splits(rows, base['record'], mix, layout, base['splitter'], base['pins']['split_trainer'], base['pins']['split'])
        require(split['heldout_group_ids'] == base['record']['heldout_group_ids'] and
                split['heldout_qids'] == base['record']['heldout_qids'], 'heldout_inheritance_changed')
        require(not split['hashed_group_ids'], 'new_evidence_scene_group')
        full.write_lines(layout / 'candidate_index.jsonl', entries)
        full.write_lines(layout / 'ROW_ORIGINS.jsonl', origins)
        comp = composition(partition, facts, excluded, base, extraction_summary, evidence_drops)
        for root in (mix, layout):
            source.write_json(root / 'COMPOSITION.json', comp)
            (root / 'COMPOSITION.md').write_text(composition_text(comp))
        source.write_json(layout / 'MATERIALIZATION.json', {'schema': 'traceev-candidate-layout-v1',
            'artifacts': {name: source.pin(layout / name) for name in ('candidate_index.jsonl', 'split.json', 'split_trainer.json')},
            'source_mix': str(mix), 'target_transform': 'Unchanged v3 bytes plus bare GT-tool evidence targets',
            'gpu_training_admission_claimed': False})
        source.write_json(layout / 'STAGED.json', {'counts': {side: len(items) for side, items in partition.items()},
            'source_mix': str(mix), 'inputs': source.pin(layout / 'BUILD_INPUTS.json')})
        source.write_json(layout / 'NATIVE_ADMISSION.json', {'passed': False,
            'scope': 'Build complete; separate VERIFICATION.json is the verification authority',
            'native_candidate_loader_verified_by_verify': False, 'gpu_training_admission_claimed': False,
            'verification_path': str(audit / 'VERIFICATION.json')})
        progress.step('Seal mix and trainer manifests')
        manifests = {}
        for name, root in (('mix', mix), ('trainer', layout)):
            source.write_json(root / 'MANIFEST.json', {'schema': 'traceev-manifest-v1',
                'artifacts': inventory(root, args.io_workers), 'counts': {side: comp[side] for side in partition},
                'audit_artifacts': {'BASE_EXCLUSIONS.jsonl': source.pin(audit / 'BASE_EXCLUSIONS.jsonl'),
                                    'EVIDENCE_DROPS.jsonl': source.pin(audit / 'EVIDENCE_DROPS.jsonl'),
                                    'CONFIG.json': source.pin(audit / 'CONFIG.json')},
                'manifest_self_hash': 'Stored externally in BUILD_SUMMARY.json'})
            manifests[name] = source.pin(root / 'MANIFEST.json')
        require(provenance(audit / 'CONFIG.json') == code, 'build_code_or_config_changed')
        require(source.pin(args.evidence) == config['evidence'], 'evidence_changed_during_build')
        summary = {'status': 'built_pending_verify', 'commit': code['repo_commit'], 'provenance': code,
            'output_mix': str(mix), 'output_layout': str(layout), 'manifest': manifests,
            'candidate_index': source.pin(layout / 'candidate_index.jsonl'), 'candidate_rows': len(rows),
            'split_trainer': source.pin(layout / 'split_trainer.json'), 'evidence': config['evidence'],
            'evidence_rows': len(facts), 'source_evidence_rows': source_evidence_rows,
            'evidence_drops': comp['evidence_drops'], 'base_exclusions': comp['base_exclusions'],
            'counts': {side: comp[side] for side in partition}, 'elapsed_seconds': time.monotonic() - started}
        source.write_json(audit / 'BUILD_SUMMARY.json', summary)
        progress.step(f'Built {len(rows)} rows; verification remains')
        return summary


def replay_evidence(row):
    return extract.replay(row)


def verify(args):
    mix, layout, audit = args.output_mix.resolve(), args.output_layout.resolve(), args.audit.resolve()
    require(1 <= args.io_workers <= 64, 'io_workers_must_be_1_to_64')
    require(audit.is_dir(), 'audit_directory_missing')
    report = audit / args.verification_name
    result = {'passed': False, 'status': 'running', 'started_utc': source.utc(), 'checks': {}, 'sample_seed': SEED}
    current = 'manifests'

    def checked(name, **details):
        result['checks'][name] = {'passed': True, **details}
        source.write_json(report, result)

    source.write_json(report, result)
    try:
        with Progress(audit, args.heartbeat) as progress:
            progress.step('Verify sealed manifests and original input pins')
            summary = source.read_json(audit / 'BUILD_SUMMARY.json')
            require(summary['output_mix'] == str(mix) and summary['output_layout'] == str(layout), 'summary_output_identity')
            for name, root in (('mix', mix), ('trainer', layout)):
                require(source.pin(root / 'MANIFEST.json') == summary['manifest'][name], 'manifest_digest_mismatch')
                manifest = source.read_json(root / 'MANIFEST.json')
                require(set(manifest['artifacts']) == set(full.inventory_names(root)), 'manifest_inventory_mismatch')
                def authenticate_artifact(item):
                    relative, pin = item
                    require(pin['path'] == str(root / relative), 'manifest_path_mismatch')
                    require(source.sha(root / relative) == pin['sha256'], 'manifest_hash_mismatch: ' + relative)

                list(io_map(authenticate_artifact, manifest['artifacts'].items(), args.io_workers))
                for pin in manifest['audit_artifacts'].values():
                    full.checked_authority(pin['path'], pin['sha256'])
            checked('manifests')
            current = 'input_pins'
            inputs = source.read_json(mix / 'BUILD_INPUTS.json')
            require(inputs == source.read_json(layout / 'BUILD_INPUTS.json') == source.read_json(audit / 'BUILD_INPUTS.json'),
                    'build_inputs_identity')
            for pin in [*inputs['base'].values(), inputs['evidence'], inputs['merge_map']]:
                full.checked_authority(pin['path'], pin['sha256'])
            for key in ('exclude_base_qids', 'extractor_summary'):
                if inputs[key]:
                    full.checked_authority(inputs[key]['path'], inputs[key]['sha256'])
            require(source.sha(audit / 'CONFIG.json') == inputs['provenance']['config_sha256'] and
                    inputs['provenance'] == summary['provenance'] and not inputs['provenance']['dirty'], 'build_provenance')
            base = load_base(Path(inputs['base_mix']), Path(inputs['base_layout']), Path(inputs['trainer']))
            require(base['pins'] == inputs['base'] and base['benchmark_sources'] == inputs['benchmark_sources'], 'base_input_bindings')
            excluded_ids, excluded = exclusions(inputs['exclude_base_qids']['path'] if inputs['exclude_base_qids'] else None, base)
            require(list(source.read_jsonl(audit / 'BASE_EXCLUSIONS.jsonl')) == excluded, 'base_exclusions_audit')
            checked('input_pins', excluded_train=len(excluded_ids), listed_heldout_preserved=sum(not r['excluded'] for r in excluded))
            current = 'evidence_admission'
            facts, base_frames = evidence_rows(Path(inputs['evidence']['path']), base, progress)
            checked('evidence_admission', rows=len(facts), leakage_checked=len(facts), templates_checked=len(facts),
                    two_decimal_numeric_targets=True, one_based_frame_numbers=True, duplicate_facts=0)
            current = 'vsi_merge_group_sibling'
            source_evidence_rows = len(facts)
            facts, evidence_drops = filter_merge_groups(facts, inputs['merge_map'])
            require(list(source.read_jsonl(audit / 'EVIDENCE_DROPS.jsonl')) == evidence_drops, 'merge_group_drop_audit')
            by_fact = {row['qid']: row for row in facts}
            checked('vsi_merge_group_sibling', source_rows=source_evidence_rows, retained_rows=len(facts),
                    dropped_rows=len(evidence_drops), by_kind=dict(Counter(row['question_type'] for row in evidence_drops)))
            current = 'base_mix_bytes'
            partition, lines = {}, {}
            for side in ('train', 'heldout'):
                payload = (mix / (side + '.jsonl')).read_bytes()
                partition[side] = full.inherited.unique_rows(payload)
                lines[side] = {compact.decode_json(line)['qid']: line for line in payload.splitlines(keepends=True) if line.strip()}
                expected = {row['qid']: line for row, line in base['base'][side] if row['qid'] not in excluded_ids}
                for qid, line in expected.items():
                    require(lines[side].get(qid) == line, 'base_mix_bytes_changed: ' + qid)
                require(set(lines[side]) == set(expected) | (set(by_fact) if side == 'train' else set()), 'output_side_membership')
            rows = partition['train'] + partition['heldout']
            by_id = {row['qid']: row for row in rows}
            require(len(by_id) == len(rows), 'duplicate_output_qid')
            checked('base_mix_bytes', carried=BASE_TRAIN + BASE_HELDOUT - len(excluded_ids), excluded=len(excluded_ids))
            current = 'scene_disjointness'
            split = base['provisional'].load_inherited_record(source.pin(layout / 'split_trainer.json'))
            for key in ('train_group_ids', 'heldout_group_ids', 'train_scenes', 'heldout_scenes'):
                require(split[key] == base['record'][key], 'inherited_scene_sets_changed: ' + key)
            require(split['heldout_qids'] == base['record']['heldout_qids'] and not split['hashed_group_ids'], 'heldout_membership_changed')
            derived = base['splitter'].make_inherited_split(rows, rows, base['record'],
                seed=base['record']['seed'], heldout_fraction=base['record']['heldout_fraction_of_groups'])
            for side, key in (('train', 'train_candidate_qids'), ('heldout', 'heldout_qids')):
                require(sorted(row['qid'] for row in partition[side]) == split[key] == derived[key], 'split_membership')
            forbidden_qids, forbidden_groups = base['forbidden']
            require(not {row['qid'] for row in partition['train']} & forbidden_qids and
                    not {control.scene_group(row['dataset'], row['scene']) for row in partition['train']} & forbidden_groups,
                    'benchmark_train_overlap')
            for name in ('split.json', 'split_trainer.json'):
                require((mix / name).read_bytes() == (layout / name).read_bytes(), 'layout_split_identity')
            published = source.read_json(mix / 'split.json')
            require(published['train_qids'] == [row['qid'] for row in partition['train']] and
                    published['heldout_qids'] == [row['qid'] for row in partition['heldout']], 'published_split_identity')
            checked('scene_disjointness', heldout_groups=len(split['heldout_group_ids']), evidence_train_only=True,
                    benchmark_overlap=0, new_scene_groups=0)
            current = 'base_carried_bytes'
            progress.step('Verify every carried bundle and candidate identity')
            entries = list(source.read_jsonl(layout / 'candidate_index.jsonl'))
            require(set(control.identities(entries)) == set(by_id), 'candidate_membership')
            require(source.pin(layout / 'candidate_index.jsonl') == summary['candidate_index'] and
                    source.pin(layout / 'split_trainer.json') == summary['split_trainer'], 'summary_artifact_pins')
            def authenticate_candidate(entry):
                qid = entry['qid']
                row, row_bytes, target = control.bundle(entry)
                require(row == by_id[qid], 'mix_layout_row_identity')
                require(target in (row['target'].encode(), (row['target'] + '\n').encode()), 'target_row_identity')
                for row_key, entry_key in (('qid', 'qid'), ('dataset', 'dataset'), ('scene', 'scene'), ('category', 'question_type')):
                    require(row[row_key] == entry[entry_key], 'candidate_identity')
                for key in ('generation_commit', 'validation_commit'):
                    require(bool(re.fullmatch(r'[0-9a-f]{40}', entry[key])) and row.get(key, entry[key]) == entry[key], 'candidate_commit')
                base['provisional'].validate_rgb(row['student_input'])
                if qid in base['index']:
                    old = base['index'][qid]
                    _, original_bytes, original_target = control.bundle(old)
                    require((row_bytes, target) == (original_bytes, original_target), 'base_carried_bytes_changed')
                    require(entry == control.copied_entry(old, original_bytes, original_target, layout), 'base_index_metadata_changed')
                else:
                    require(row == packed_evidence(by_fact[qid], inputs), 'evidence_row_provenance')
                    shard = hashlib.sha256(qid.encode()).hexdigest()[:2]
                    require(Path(entry['row_path']) == layout / 'targets_traceev' / shard / qid / 'row.json' and
                            Path(entry['target_path']) == layout / 'targets_traceev' / shard / qid / 'target.txt', 'evidence_layout')
                if str(entry['answer']) != row['target']:
                    return {'qid': qid, 'side': 'train' if qid in lines['train'] else 'heldout',
                            'base_carried': qid in base['index']}

            mismatch = []
            for i, different in enumerate(io_map(authenticate_candidate, entries, args.io_workers)):
                if different:
                    mismatch.append(different)
                if i % 2000 == 0:
                    progress.step(f'Authenticated {i + 1} candidate bundles')
            checked('base_carried_bytes', carried=BASE_TRAIN + BASE_HELDOUT - len(excluded_ids))
            exempt = {row['qid'] for row in mismatch if row['side'] == 'heldout' and row['base_carried']}
            mismatch = [row for row in mismatch if row['qid'] not in exempt]
            result['checks']['index_target_equality'] = {'passed': not mismatch, 'rows': len(entries),
                'mismatch_count': len(mismatch), 'mismatches': mismatch,
                'exempt_heldout_count': len(exempt), 'exempt_heldout_qids': sorted(exempt),
                'exemption_requires_v3_bytes_and_index_identity': True}
            source.write_json(report, result)
            current = 'composition_and_origins'
            expected_origins = []
            for row in rows:
                qid = row['qid']
                if qid in base['index']:
                    entry = base['index'][qid]
                    expected_origins.append({'qid': qid, 'root': 'v3-carried', 'side': 'train' if qid in lines['train'] else 'heldout',
                        'source_row': {'path': entry['row_path'], 'sha256': entry['row_sha256']},
                        'source_target': {'path': entry['target_path'], 'sha256': entry['sha256']}})
                else:
                    expected_origins.append({'qid': qid, 'root': 'traceev_gt_tool_evidence', 'side': 'train',
                        'source_qids': by_fact[qid]['source_qids'], 'evidence_rows': inputs['evidence']})
            actual_origins = list(source.read_jsonl(layout / 'ROW_ORIGINS.jsonl'))
            require(len(actual_origins) == len(rows) and {r['qid']: r for r in actual_origins} ==
                    {r['qid']: r for r in expected_origins}, 'origin_membership')
            extraction_summary = source.read_json(inputs['extractor_summary']['path']) if inputs['extractor_summary'] else {}
            comp = composition(partition, facts, excluded, base, extraction_summary, evidence_drops)
            for root in (mix, layout):
                require(source.read_json(root / 'COMPOSITION.json') == comp and
                        (root / 'COMPOSITION.md').read_text() == composition_text(comp), 'composition_mismatch')
            require(summary['counts'] == {side: comp[side] for side in partition} and summary['candidate_rows'] == len(rows) and
                    summary['evidence_rows'] == len(facts) and summary['source_evidence_rows'] == source_evidence_rows and
                    summary['evidence_drops'] == comp['evidence_drops'] and
                    summary['base_exclusions'] == comp['base_exclusions'], 'summary_counts')
            materialization = source.read_json(layout / 'MATERIALIZATION.json')
            require(materialization['artifacts'] == {name: source.pin(layout / name)
                    for name in ('candidate_index.jsonl', 'split.json', 'split_trainer.json')}, 'materialization_pins')
            checked('composition_and_origins', rows=len(rows), label_checks=comp['label_checks'])
            current = 'frames'
            frame_sample = random.Random(SEED).sample(facts, min(args.frame_sample, len(facts)))
            frames = source.Frames()
            for row in frame_sample:
                frames.row(row)
            checked('frames', all_evidence_frames_in_v3=True, v3_unique_frames=len(base_frames),
                    sampled_rows=len(frame_sample), sampled_unique_files=len(frames.checked), new_frame_files=0)
            current = 'replay_sample'
            sample = random.Random(SEED).sample(facts, min(args.replay_sample, len(facts)))
            for i, row in enumerate(sample):
                progress.step(f'Replay evidence fact {i + 1} of {len(sample)}')
                require(replay_evidence(row) == row['target'], 'evidence_replay_mismatch: ' + row['qid'])
                result['checks']['replay_sample'] = {'passed': False, 'state': 'running', 'completed': i + 1, 'rows': len(sample)}
                source.write_json(report, result)
            checked('replay_sample', rows=len(sample), qids=[row['qid'] for row in sample])
            current = 'native_loader'
            if args.native_loader:
                progress.step('Pinned native candidate loader remains running on CPU')
                result['checks']['native_loader'] = {'passed': False, 'state': 'running'}
                source.write_json(report, result)
                loaded = base['provisional'].load_provisional_candidates(layout / 'candidate_index.jsonl', full.inherited.common.LABEL)
                require(len(loaded) == len(rows), 'native_loader_count')
                replay = base['provisional'].split_candidates(loaded, full.inherited.common.LABEL,
                    inherited_from=source.pin(layout / 'split_trainer.json'))['split']
                require(replay['train_candidate_qids'] == split['train_candidate_qids'] and
                        replay['heldout_qids'] == split['heldout_qids'], 'native_loader_split')
                checked('native_loader', state='passed', rows=len(loaded), trainer_commit=inputs['trainer_commit'])
            else:
                result['checks']['native_loader'] = {'passed': None, 'state': 'not_requested'}
            current = 'index_target_equality'
            require(not mismatch, f'index_target_equality: {len(mismatch)} rows differ; carried targets and index answers remain unchanged')
            result.update(passed=True, status='verified', train=len(partition['train']), heldout=len(partition['heldout']),
                          evidence_rows=len(facts), finished_utc=source.utc())
            source.write_json(report, result)
            progress.step('Verification passed for the assembled trace evidence set')
            return result
    except Exception as error:
        result.update(passed=False, status='failed', failed_check=current,
                      error=f'{type(error).__name__}: {error}', finished_utc=source.utc())
        result['checks'].setdefault(current, {})['passed'] = False
        source.write_json(report, result)
        raise


def transfer(args):
    mix, layout, audit = args.output_mix.resolve(), args.output_layout.resolve(), args.audit.resolve()
    output = args.output_xfer.resolve()
    require(output.is_relative_to('/data2') and not output.exists(), 'transfer_output_exists_or_outside_data2')
    require(not any(output == root or output.is_relative_to(root) or root.is_relative_to(output)
                    for root in (mix, layout)), 'transfer_output_overlap')
    summary = source.read_json(audit / 'BUILD_SUMMARY.json')
    paths = []
    for name, root in (('mix', mix), ('trainer', layout)):
        require(source.pin(root / 'MANIFEST.json') == summary['manifest'][name], 'transfer_manifest_pin')
        manifest = source.read_json(root / 'MANIFEST.json')
        require(set(manifest['artifacts']) == set(full.inventory_names(root)), 'transfer_inventory')
        paths += [root / name for name in [*manifest['artifacts'], 'MANIFEST.json']]
    inputs = source.read_json(mix / 'BUILD_INPUTS.json')
    full.checked_authority(inputs['evidence']['path'], inputs['evidence']['sha256'])
    base_manifest = control.checked_json(inputs['base']['manifest'])
    base_frames = set()
    for side in ('train', 'heldout'):
        pin = base_manifest['artifacts'][side + '.jsonl']
        full.checked_authority(pin['path'], pin['sha256'])
        for row in source.read_jsonl(pin['path']):
            base_frames.update((frame['path'], frame['sha256']) for frame in row['student_input']['frames'])
    evidence_frames = {(frame['path'], frame['sha256']) for row in source.read_jsonl(inputs['evidence']['path'])
                       for frame in row['student_input']['frames']}
    new_frames = {Path(path) for path, _ in evidence_frames - base_frames}
    output.mkdir(parents=True)
    lists = {}
    for kind, files in (('set', paths), ('frames', new_frames)):
        names = sorted(str(Path(path).relative_to('/data2')) for path in files)
        require(len(names) == len(set(names)), 'transfer_duplicate_path')
        lists[kind] = []
        for i in range(8):
            part = output / f'{kind}.part{i:02d}'
            selected = names[i::8]
            part.write_text(''.join(name + '\n' for name in selected))
            lists[kind].append({**source.pin(part), 'files': len(selected)})
    script = '''#!/bin/bash
set -uo pipefail
ROOT=/lustre/fsw/portfolios/av/users/jyeung/split
CA=$ROOT/distill/orch
D=$ROOT/distill/traceev
X=__XFER_SOURCE__
mkdir -p "$D/lists" "$D/logs" "$CA/data2root" || exit 1
rsync -a -e "ssh -F $ROOT/cache/ssh_trinity_config" "tri-login:$X/" "$D/lists/" || exit 1
pids=()
for kind in set frames; do
  for i in 00 01 02 03 04 05 06 07; do
    (
      log="$D/logs/pull_${kind}_$i.log"
      rsync -a --files-from="$D/lists/$kind.part$i" -e "ssh -F $ROOT/cache/ssh_trinity_config" tri-login:/data2/ "$CA/data2root/" > "$log" 2>&1
      rc=$?
      printf '%s rc=%s\\n' "$(date -u +%FT%TZ)" "$rc" >> "$log"
      exit "$rc"
    ) &
    pids+=("$!")
  done
done
failed=0
for pid in "${pids[@]}"; do
  wait "$pid" || failed=1
done
if (( failed != 0 )); then exit 1; fi
printf 'ALL DONE %s\\n' "$(date -u +%FT%TZ)" > "$D/logs/pull_traceev.done"
'''
    import shlex
    script_path = output / 'pull_traceev.sh'
    script_path.write_text(script.replace('__XFER_SOURCE__', shlex.quote(str(output))))
    result = {'output': str(output), 'lists': lists, 'set_files': len(paths), 'new_frame_files': len(new_frames),
              'pull_script': source.pin(script_path), 'pull_executed': False,
              'candidate_index': summary['candidate_index'], 'split_trainer': summary['split_trainer']}
    source.write_json(audit / 'TRANSFER_SUMMARY.json', result)
    return result


def parser():
    parser = argparse.ArgumentParser(description='Assemble and verify v3 plus GT trace-evidence training rows')
    commands = parser.add_subparsers(dest='command', required=True)
    build_parser = commands.add_parser('build')
    verify_parser = commands.add_parser('verify')
    transfer_parser = commands.add_parser('transfer')
    for command in (build_parser, verify_parser, transfer_parser):
        for name in ('output-mix', 'output-layout', 'audit'):
            command.add_argument('--' + name, type=Path, required=True)
        command.add_argument('--heartbeat', type=Path, default=os.environ.get('TRACEEV_HEARTBEAT'))
    for command in (build_parser, verify_parser):
        command.add_argument('--io-workers', type=int, default=32)
    for name in ('base-mix', 'base-layout', 'evidence'):
        build_parser.add_argument('--' + name, type=Path, required=True)
    build_parser.add_argument('--exclude-base-qids', type=Path)
    build_parser.add_argument('--merge-map', type=Path, default=MERGE_MAP)
    build_parser.add_argument('--trainer', type=Path, default=full.TRAINER)
    verify_parser.add_argument('--replay-sample', type=int, default=200)
    verify_parser.add_argument('--frame-sample', type=int, default=30)
    verify_parser.add_argument('--native-loader', action='store_true')
    verify_parser.add_argument('--verification-name', choices=('VERIFICATION.json', 'NATIVE_VERIFICATION.json'),
                               default='VERIFICATION.json')
    transfer_parser.add_argument('--output-xfer', type=Path, required=True)
    return parser


def main():
    args = parser().parse_args()
    try:
        require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CUDA_VISIBLE_DEVICES_must_be_empty')
        if args.command == 'verify':
            require(args.replay_sample > 0 and args.frame_sample > 0, 'verification_samples_must_be_positive')
        result = {'build': build, 'verify': verify, 'transfer': transfer}[args.command](args)
        print(json.dumps(result, sort_keys=True), flush=True)
        return 0
    except Exception as error:
        print(f'traceev {args.command} refused: {type(error).__name__}: {error}', file=sys.stderr, flush=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
