"""Build and verify a scene-disjoint answer-only superset of a pinned corpus."""
import argparse
from collections import Counter
import json
import math
from pathlib import Path
import random
import re
import subprocess
import sys
import time

from . import answer_only_full as inherited
from . import compact_control as control
from . import compact_counted_v1 as compact
from . import answer_fullpool_sources as source

S = Path('/data2/jjyeung/agent_project_data/student_diagnostic_pilot_20260918')
D = Path('/data2/jjyeung/agent_project_data/vsi_distill_training_20260917')
P = Path('/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918')
OUT0 = S / 'mix_v25_roomfix_answeronly_20260923'
ROOT_A = P / 'claude_v25_uncapped_render_20260923T0030Z/work/combined_sources_r3_r4'
TRAINER = P / 'claude_onethinker_v241_launch_20260921T0015Z/work_checkout_b084aaf'
SPLIT_SHA = '5dcd3cdc3c816625e0f579797f1c61adb2f9c97cf3373bcee3589ddd9414cd19'
NATIVE_SPLIT_SHA = 'eec29d981c5c30b6217c72938bfbb1c0cbd13842ff651767a2c657125092cb27'
LABELS_SHA = '86226945ccc192c197b992b776c4376a6a66e881230272ed1dba07ad442f41a8'
A_MEMBERS_SHA = 'fd5703e9d5a6474ea1c9010cc91bf76ca5644f11b5e284399db5056eebfe984c'
A_LABELS_SHA = '50ef9cc160f1f6e22a64a0f922d22fb999df2c25809009b022ac0a62af55cd79'
MEMBERS_SHA = '018162ec3c6109a4d9e818eaee6c60077f654ae348f0fc67c6af2eaa67be16f8'
ROOM_SHA = '025355ea328c0f1f73ba997fd52070a1f487248acd1fb9d8ac727886b319d231'
SAMPLE_SEED = 20260923
require = control.require


def trainer_modules(path):
    head = subprocess.check_output(['git', '-C', str(path), 'rev-parse', 'HEAD'], text=True).strip()
    require(head == inherited.common.TRAINER_COMMIT, 'trainer_commit_changed')
    sys.path.insert(0, str(path))
    from student_pilot import split, provisional
    require(Path(split.__file__).resolve().is_relative_to(path), 'trainer_import_path')
    return split, provisional


def progress(out, step, done='', next_step=''):
    out.mkdir(parents=True, exist_ok=True)
    with (out / 'HEARTBEAT.md').open('a') as stream:
        stream.write(f'{source.utc()} | {step}\n')
    (out / 'PROGRESS.md').write_text(f'done: {done}\ndoing: {step}\nnext: {next_step}\nblockers: None.\n')
    print(f'{source.utc()} | {step}', flush=True)


def write_lines(path, rows):
    with Path(path).open('wb') as stream:
        for row in rows:
            stream.write(inherited.line_bytes(row))


def checked_authority(path, expected):
    binding = source.pin(path)
    require(binding['sha256'] == expected, f'authority_hash_mismatch: {path}')
    return binding


def read_base(mix, layout, limit, expected_train):
    manifest = source.read_json(mix / 'MANIFEST.json')
    base = {}
    for side in ('train', 'heldout'):
        payload = control.checked_bytes(manifest['artifacts'][side + '.jsonl'])
        lines = [line for line in payload.splitlines(keepends=True) if line.strip()]
        rows = inherited.unique_rows(payload)
        if side == 'train':
            require(len(rows) == expected_train, 'OUT0_training_count')
        base[side] = [(row, line) for row, line in zip(rows, lines)][:limit or None]
    materialization = source.read_json(layout / 'MATERIALIZATION.json')
    index = inherited.unique_rows(control.checked_bytes(materialization['artifacts']['candidate_index.jsonl']))
    return base, control.identities(index), manifest


def native_answer(row, mode):
    final = row['native_answer_archive']
    match = re.fullmatch(r'<ANSWER>(.*?)</ANSWER>', final['native_answer_block'], re.I | re.S)
    require(bool(match), 'native_answer_block_schema')
    answer = inherited.answer_text({'answer': match[1].strip()})
    target = answer if mode == 'bare' else '<answer>' + match[1] + '</answer>'
    require(final['target'] == '<answer>' + match[1] + '</answer>', 'native_archive_transform_drift')
    return answer, target


def benchmark_groups(manifest):
    return inherited.benchmark_exclusions(manifest['benchmark_sources'])


def emit_splits(rows, base_record, mix, layout, trainer_split, base_pin, split_pin):
    derived = trainer_split.make_inherited_split(rows, rows, base_record,
        seed=base_record['seed'], heldout_fraction=base_record['heldout_fraction_of_groups'])
    # Keep named groups and exact scenes even when a bounded dry run has no rows there.
    for key in ('train_group_ids', 'heldout_group_ids', 'train_scenes', 'heldout_scenes'):
        derived[key] = sorted(set(derived[key]) | set(base_record[key]))
    record = {**derived, 'schema': 'provisional-inherited-scene-split-v1',
              'inherited_from': base_pin, 'source_split': split_pin,
              'provisional_diagnostic': inherited.common.LABEL,
              'benchmark_improvement_claim': False, 'score_nomination_allowed': False,
              'benchmark_trained_diagnostic': True, 'infrastructure_only': False}
    record['provenance'] = {'config_sha256': compact.digest_json(record)}
    train_ids = set(derived['train_candidate_qids'])
    published = {'schema': 'answer-fullpool-inherited-scene-split-v1',
                 'seed': record['seed'], 'validation_fraction': record['heldout_fraction_of_groups'],
                 'parent_split': split_pin, 'inherited_split': base_pin,
                 'train_qids': [r['qid'] for r in rows if r['qid'] in train_ids],
                 'heldout_qids': [r['qid'] for r in rows if r['qid'] not in train_ids],
                 'all_heldout_groups': record['heldout_group_ids'],
                 'train_scenes': record['train_scenes'], 'heldout_scenes': record['heldout_scenes'],
                 'hashed_group_ids': record['hashed_group_ids'],
                 'new_scene_rule': 'b084aaf make_inherited_split; student-scene-split-v1, seed 17, fraction 0.1'}
    for output in (mix, layout):
        source.write_json(output / 'split.json', published)
        source.write_json(output / 'split_trainer.json', record)
    return record


def inventory(root):
    # Only the newly created output tree is enumerated, never collector archives.
    return {str(path.relative_to(root)): source.pin(path)
            for path in sorted(root.rglob('*')) if path.is_file() and path != root / 'MANIFEST.json'}


def build(args):
    start = time.monotonic()
    mix, layout, out = args.output_mix.resolve(), args.output_layout.resolve(), args.out.resolve()
    protected = [args.source_mix.resolve(), args.source_layout.resolve(), args.root_a.resolve(),
                 args.root_a_run.resolve(), args.root_b_run.resolve(), Path('/home/jjyeung/agent_project_distill')]
    for output in (mix, layout, out):
        require(not any(output == p or output.is_relative_to(p) or p.is_relative_to(output) for p in protected),
                'output_source_overlap')
    require(mix != layout and not mix.is_relative_to(layout) and not layout.is_relative_to(mix), 'output_overlap')
    require(not mix.exists() and not layout.exists(), 'output_exists_use_new_directory')
    require(not out.is_relative_to(mix) and not out.is_relative_to(layout), 'audit_inside_output')
    progress(out, 'Freeze source inputs and terminal list')
    snapshot = source.snapshot_terminals(args.root_b_run, args.limit, out / 'ROOTB_SNAPSHOT.json')
    split_pin = checked_authority(args.source_mix / 'split.json', args.split_sha)
    native_pin = checked_authority(args.source_mix / 'split_trainer.json', args.native_split_sha)
    trainer_split, provisional = trainer_modules(args.trainer.resolve())
    base_record = provisional.load_inherited_record(native_pin)
    require(base_record['seed'] == 17 and base_record['heldout_fraction_of_groups'] == 0.1, 'split_hash_rule')
    base, old_index, base_manifest = read_base(args.source_mix, args.source_layout, args.limit, args.expected_train)
    inputs = {'schema': 'answer-fullpool-inputs-v1', 'source_mix': str(args.source_mix.resolve()),
              'source_layout': str(args.source_layout.resolve()), 'expected_out0_train': args.expected_train,
              'source_manifest': source.pin(args.source_mix / 'MANIFEST.json'),
              'source_materialization': source.pin(args.source_layout / 'MATERIALIZATION.json'),
              'source_split': split_pin, 'source_native_split': native_pin,
              'root_a_accepted': source.pin(args.root_a / 'ACCEPTED_combined_r3_r4.json'),
              'root_a_index': source.pin(args.root_a / 'candidate_index.jsonl'),
              'root_a_run': str(args.root_a_run.resolve()), 'root_b_run': str(args.root_b_run.resolve()),
              'root_a_members': checked_authority(args.root_a_members, args.root_a_members_sha),
              'root_a_labels': checked_authority(args.root_a_labels, args.root_a_labels_sha),
              'members': checked_authority(args.members, args.members_sha),
              'labels': checked_authority(args.labels, args.labels_sha),
              'room_labels': {'path': str(args.room_labels.resolve()), 'sha256': args.room_sha},
              'limit_per_root_and_out0_side': args.limit, 'target_format': args.target_format,
              'benchmark_sources': base_manifest['benchmark_sources'], 'sample_seed': SAMPLE_SEED,
              'trainer': str(args.trainer.resolve()), 'trainer_commit': inherited.common.TRAINER_COMMIT,
              'commit': subprocess.check_output(['git', '-C', str(source.REPO), 'rev-parse', 'HEAD'], text=True).strip(),
              'code': {str(p.relative_to(source.REPO)): source.pin(p) for p in sorted(
                  list(Path(__file__).parent.glob('answer*.py')) +
                  [Path(__file__).with_name(n) for n in ('compact_control.py', 'compact_counted_v1.py', 'design_common.py')] +
                  list((source.REPO / 'collector').glob('*.py')) +
                  [source.REPO / 'tools/gtmeasure/room_labels.py', source.REPO / 'tools/gtmeasure/formats.py'])}}
    for directory in (mix, layout):
        directory.mkdir(parents=True)
        source.write_json(directory / 'BUILD_INPUTS.json', inputs)
    source.write_json(out / 'BUILD_INPUTS.json', inputs)
    config_sha = compact.digest_json(inputs)
    members = {r['id']: r for r in source.read_jsonl(args.members)}
    gold = {r['id']: r['ground_truth'] for r in source.read_jsonl(args.labels)}
    a_members = {r['id']: r for r in source.read_jsonl(args.root_a_members)}
    a_gold = {r['id']: r['ground_truth'] for r in source.read_jsonl(args.root_a_labels)}
    accepted = source.read_json(args.root_a / 'ACCEPTED_combined_r3_r4.json')
    require(len({r['id'] for r in accepted}) == len(accepted), 'root_a_duplicate_decision')
    require(len(accepted) == args.expected_root_a, 'root_a_census_count')
    candidates = {r['qid']: r for r in source.read_jsonl(args.root_a / 'candidate_index.jsonl')}
    forbidden_qids, forbidden_groups = benchmark_groups(base_manifest)
    frames = source.Frames()
    rows, entries, origins, lines, seen, audits, dropped = [], [], {}, {}, set(), [], []
    all_out0 = set(old_index)
    drops_handle = (out / 'DROPPED_ROWS.jsonl').open('wb')
    last_heartbeat = time.monotonic()

    def heartbeat(step):
        nonlocal last_heartbeat
        if time.monotonic() - last_heartbeat > 25:
            progress(out, step, f'{len(rows)} rows retained; {len(dropped)} source rows excluded')
            last_heartbeat = time.monotonic()

    def drop(qid, root, reason, detail=''):
        record = {'qid': qid, 'root': root, 'reason': reason, 'detail': detail}
        dropped.append(record)
        drops_handle.write(inherited.line_bytes(record))
        drops_handle.flush()

    def add(row, entry, root, row_bytes=None, target_bytes=None, line=None):
        qid = row['qid']
        require(qid not in seen, 'duplicate_output_qid')
        frames.row(row)
        entry = control.copy_entry(entry, row_bytes or compact.canonical_bytes(row),
                                   target_bytes or (row['target'] + '\n').encode(), layout)
        rows.append(row)
        entries.append(entry)
        origins[qid] = root
        lines[qid] = line or inherited.line_bytes(row)
        seen.add(qid)
        heartbeat('Validate frames and materialize retained rows')

    progress(out, 'Carry OUT0 row and target bytes')
    for side in ('train', 'heldout'):
        for row, line in base[side]:
            entry = old_index[row['qid']]
            layout_row, row_bytes, target_bytes = control.bundle(entry)
            require(layout_row == row, 'OUT0_mix_layout_identity')
            if side == 'train':
                require(row['target'] == inherited.answer_text(entry), 'OUT0_bare_answer_contract')
            add(row, entry, 'OUT0-carried', row_bytes, target_bytes, line)
    progress(out, 'Read corrected same-scene room labels')
    labels = source.room_labels(args.room_labels, args.room_sha)

    def ingest_decision(decision, root, payload=None):
        qid = decision['id']
        heartbeat('Ingest strict accepted teacher rows')
        if not all(decision.get(k) is True for k in ('accepted', 'answer_correct', 'mechanically_complete', 'has_perceptual_evidence')):
            drop(qid, root, 'strict_not_accepted', decision.get('reason', 'missing strict acceptance'))
            return
        if qid in seen or qid in all_out0:
            drop(qid, root, 'duplicate', 'OUT0 or prior retained source wins')
            return
        try:
            root_members, root_gold = (a_members, a_gold) if root == 'root-A-new' else (members, gold)
            entry = candidates.get(qid) if root == 'root-A-new' else None
            if entry and 'row_path' in entry and not entry.get('ingestion_refusal'):
                row = control.checked_json({'path': entry['row_path'], 'sha256': entry['row_sha256']})
                require(row['sources']['raw'] == {'path': decision['trace_path'], 'sha256': decision['trace_sha256']},
                        'stage1_trace_pin_mismatch')
            else:
                run_root = args.root_a_run if root == 'root-A-new' else args.root_b_run
                if payload is None:
                    path = source.ingest.allowed_path(decision['trace_path'], run_root, decision['trace_path'])
                    payload = path.read_bytes()
                row = source.fresh_row(decision, payload, run_root, frames, inputs['commit'], config_sha)
                entry = None
            source.check_membership(row, root_members[qid])
            require(row['qid'] == qid, 'source_qid_mismatch')
            if qid in forbidden_qids or control.scene_group(row['dataset'], row['scene']) in forbidden_groups:
                drop(qid, root, 'benchmark_overlap')
                return
            answer, target = native_answer(row, args.target_format)
            correct, rule = source.census.grade(root_members[qid], root_gold[qid], answer)
            require(correct, 'ground_truth_mismatch: ' + rule)
            room_evidence = None
            if row['category'] == 'room_size_estimation':
                try:
                    room_evidence = source.check_room(row, answer, labels)
                except (ValueError, KeyError) as error:
                    drop(qid, root, 'room_label_mismatch', str(error))
                    return
            row = {**row, 'target': target}
            if entry:
                require(str(entry['answer']) == answer, 'indexed_native_answer_mismatch')
            else:
                entry = {'qid': qid, 'dataset': row['dataset'], 'scene': row['scene'],
                         'question_type': row['category'], 'pool': 'clean_vsi590k', 'answer': answer,
                         'generation_commit': inputs['commit'], 'validation_commit': inputs['commit'],
                         'config_sha256': config_sha, 'postprocess': source.ingest.SCHEMA}
            add(row, entry, root)
            audits.append({'qid': qid, 'root': root, 'strict_decision': decision,
                           'ground_truth_rule': rule, 'room_label': room_evidence,
                           'source_row': {'path': entry['row_path'], 'sha256': entry['row_sha256']} if 'row_path' in entry else None,
                           'target_transform': args.target_format})
        except source.FrameError as error:
            drop(qid, root, error.reason, str(error))
        except (ValueError, KeyError, TypeError, OSError) as error:
            drop(qid, root, 'ingest_refusal', str(error))

    progress(out, 'Ingest bounded or complete root A')
    for decision in sorted(accepted, key=lambda r: r['id'])[:args.limit or None]:
        ingest_decision(decision, 'root-A-new')
    progress(out, 'Census frozen root B terminals serially')
    for decision, payload in source.root_b_decisions(snapshot, members, gold):
        snapshot['decisions'].append(decision)
        ingest_decision(decision, 'root-B-new', payload)
        if len(snapshot['decisions']) % 25 == 0:
            source.write_json(out / 'ROOTB_SNAPSHOT.json', snapshot)
    snapshot['completed_at'] = source.utc()
    source.write_json(out / 'ROOTB_SNAPSHOT.json', snapshot)
    drops_handle.close()
    # One audit line per qid, with all source occurrences retained for accounting.
    grouped_drops = {}
    for item in dropped:
        grouped_drops.setdefault(item['qid'], {**item, 'occurrences': []})['occurrences'].append(item)
    write_lines(out / 'DROPPED_ROWS.jsonl', grouped_drops.values())
    progress(out, 'Emit inherited splits and manifests')
    record = emit_splits(rows, base_record, mix, layout, trainer_split, native_pin, split_pin)
    train_ids = set(record['train_candidate_qids'])
    partition = {side: [r for r in rows if (r['qid'] in train_ids) == (side == 'train')]
                 for side in ('train', 'heldout')}
    for side, side_rows in partition.items():
        with (mix / (side + '.jsonl')).open('wb') as stream:
            for row in side_rows:
                stream.write(lines[row['qid']])
    write_lines(layout / 'candidate_index.jsonl', entries)
    write_lines(layout / 'ROW_AUDIT.jsonl', audits)
    write_lines(layout / 'ROW_ORIGINS.jsonl', [{'qid': r['qid'], 'root': origins[r['qid']]} for r in rows])
    # This is a diagnostic data package, not an assertion that model/tokenizer tests ran.
    source.write_json(layout / 'NATIVE_ADMISSION.json', {'passed': True,
        'scope': 'Pinned b084aaf split functions; candidate/row identity, RGB schema, all frame hashes',
        'native_candidate_loader_verified_by_verify': False, 'gpu_training_admission_claimed': False})
    source.write_json(layout / 'MATERIALIZATION.json', {'schema': 'answer-fullpool-candidate-layout-v1',
        'artifacts': {name: source.pin(layout / name) for name in ('candidate_index.jsonl', 'split.json', 'split_trainer.json')},
        'source_mix': str(mix), 'target_transform': args.target_format,
        'gpu_training_admission_claimed': False})
    source.write_json(layout / 'STAGED.json', {'counts': {s: len(r) for s, r in partition.items()},
                                             'source_mix': str(mix), 'inputs': source.pin(layout / 'BUILD_INPUTS.json')})
    counts = {side: {'total': len(side_rows),
                    'by_root': {root: sum(origins[r['qid']] == root for r in side_rows)
                                for root in ('OUT0-carried', 'root-A-new', 'root-B-new')},
                    'by_question_type': dict(Counter(r['category'] for r in side_rows))}
              for side, side_rows in partition.items()}
    drops = dict(Counter(r['reason'] for r in grouped_drops.values()))
    for reason in ('duplicate', 'holdout', 'missing_frames', 'room_label_mismatch', 'ingest_refusal', 'other'):
        drops.setdefault(reason, 0)
    sample = random.Random(SAMPLE_SEED).sample(partition['train'], min(30, len(partition['train'])))
    write_lines(out / 'SAMPLE_30.jsonl', [{'qid': r['qid'], 'root': origins[r['qid']], 'category': r['category'],
        'question': r['student_input']['question'], 'target': r['target'], 'scene': r['dataset'] + '/' + r['scene'],
        'split_side': 'train', 'sample_seed': SAMPLE_SEED} for r in sample])
    manifest_pins = {}
    for name, root in (('mix', mix), ('trainer', layout)):
        source.write_json(root / 'MANIFEST.json', {'schema': 'answer-fullpool-manifest-v1',
            'artifacts': inventory(root), 'counts': counts,
            'manifest_self_hash': 'Stored externally in BUILD_SUMMARY.json; self hashing is not defined',
            'audit_artifacts': {n: source.pin(out / n) for n in ('SAMPLE_30.jsonl', 'DROPPED_ROWS.jsonl', 'ROOTB_SNAPSHOT.json')}})
        manifest_pins[name] = source.pin(root / 'MANIFEST.json')
    known_scenes = set(base_record['train_scenes']) | set(base_record['heldout_scenes'])
    new_scenes = {r['dataset'] + '/' + r['scene'] for r in rows} - known_scenes
    summary = {'status': 'built_pending_verify', 'dry_run': bool(args.limit), 'counts': counts,
        'dropped_by_reason': drops, 'dropped_source_occurrences_by_reason': dict(Counter(r['reason'] for r in dropped)),
        'dropped_unique_qids': len(grouped_drops), 'dropped_by_root': dict(Counter(r['root'] for r in dropped)),
        'heldout_routed_not_dropped': len(partition['heldout']), 'holdout_scene_count': len(record['heldout_scenes']),
        'holdout_scenes_with_rows': len({(r['dataset'], r['scene']) for r in partition['heldout']}),
        'new_exact_scene_count': len(new_scenes), 'newly_hashed_group_count': record['hashed_group_count'],
        'newly_hashed_scene_count': sum(trainer_split.physical_group(*scene.split('/', 1)) in record['hashed_group_ids'] for scene in new_scenes),
        'root_b_snapshot_terminals': snapshot['terminal_count'], 'root_b_censused_questions': len(snapshot['decisions']),
        'root_b_strict_accepted': sum(d['accepted'] for d in snapshot['decisions']),
        'root_a_strict_accepted_authority': len(accepted), 'root_a_considered': min(args.limit or len(accepted), len(accepted)),
        'all_frames_verified': True, 'unique_frame_files': len(frames.checked), 'frame_bytes_read': frames.bytes_read,
        'superset_full_out0_checked': not bool(args.limit), 'manifest': manifest_pins,
        'optimizer_steps_one_epoch_effective_batch32': math.ceil(len(partition['train']) / 32),
        'optimizer_steps_floor_if_dropping_last_batch': len(partition['train']) // 32,
        'sample_seed': SAMPLE_SEED, 'commit': inputs['commit'], 'elapsed_seconds': time.monotonic() - start,
        'commands': {'build': [sys.executable, '-B', '-m', 'student.compact_targets.answer_fullpool', *sys.argv[1:]],
                     'verify': [sys.executable, '-B', '-m', 'student.compact_targets.answer_fullpool', 'verify',
                                '--output-mix', str(mix), '--output-layout', str(layout), '--out', str(out)]}}
    source.write_json(out / 'BUILD_SUMMARY.json', summary)
    render_report(out, summary)
    progress(out, 'Build complete; verification remains', f'{len(train_ids)} train; {len(rows)-len(train_ids)} heldout', 'Run verify')
    return summary


def render_report(out, summary):
    import shlex
    text = [f"Status: {summary['status']}; dry run: {summary['dry_run']}.",
            f"Counts: {json.dumps(summary['counts'], sort_keys=True)}",
            f"Dropped source rows: {json.dumps(summary['dropped_by_reason'], sort_keys=True)}",
            'Heldout rows are routed to heldout.jsonl, not discarded; holdout drop count is zero.',
            f"Holdout scenes: {summary['holdout_scene_count']}; newly hashed scenes: {summary['newly_hashed_scene_count']}; groups: {summary['newly_hashed_group_count']}.",
            f"Root B: {summary['root_b_censused_questions']} questions censused; {summary['root_b_strict_accepted']} strict accepted.",
            f"Manifest SHA-256: {json.dumps(summary['manifest'], sort_keys=True)}",
            f"One epoch at effective batch 32: {summary['optimizer_steps_one_epoch_effective_batch32']} optimizer steps (retain partial final batch).",
            f"Code commit: {summary['commit']}.",
            f"Sample seed: {summary['sample_seed']}; elapsed build seconds: {summary['elapsed_seconds']:.1f}.",
            'Build: ' + shlex.join(summary['commands']['build']),
            'Verify: ' + shlex.join(summary['commands']['verify']),
            'The numeric census accepts at most 5% error; room rows additionally require exact corrected-label agreement.',
            'No GPU, paid API, training, or collector writes were used.']
    (out / 'REPORT.md').write_text('\n'.join(text) + '\n')


def verify(args):
    mix, layout, out = args.output_mix.resolve(), args.output_layout.resolve(), args.out.resolve()
    progress(out, 'Verify manifests and inherited scene assignments')
    summary_pin_record = source.read_json(out / 'BUILD_SUMMARY.json')
    for name, root in (('mix', mix), ('trainer', layout)):
        require(source.sha(root / 'MANIFEST.json') == summary_pin_record['manifest'][name]['sha256'],
                'manifest_digest_mismatch')
        manifest = source.read_json(root / 'MANIFEST.json')
        require(set(manifest['artifacts']) == set(inventory_names(root)), 'manifest_inventory_mismatch')
        for name, binding in manifest['artifacts'].items():
            require(binding['path'] == str(root / name), 'manifest_path_mismatch')
            require(source.sha(root / name) == binding['sha256'], 'manifest_hash_mismatch: ' + name)
        for binding in manifest['audit_artifacts'].values():
            require(source.sha(binding['path']) == binding['sha256'], 'audit_artifact_hash_mismatch')
    inputs = source.read_json(mix / 'BUILD_INPUTS.json')
    require(inputs == source.read_json(layout / 'BUILD_INPUTS.json'), 'layout_build_inputs_identity')
    for key in ('source_manifest', 'source_materialization'):
        checked_authority(inputs[key]['path'], inputs[key]['sha256'])
    base_split = inputs['source_native_split']
    checked_authority(base_split['path'], base_split['sha256'])
    checked_authority(inputs['source_split']['path'], inputs['source_split']['sha256'])
    trainer_split, provisional = trainer_modules(Path(inputs['trainer']))
    old_record = provisional.load_inherited_record(base_split)
    record = provisional.load_inherited_record(source.pin(mix / 'split_trainer.json'))
    train = list(source.read_jsonl(mix / 'train.jsonl'))
    heldout = list(source.read_jsonl(mix / 'heldout.jsonl'))
    rows = train + heldout
    if not inputs['limit_per_root_and_out0_side']:
        require(len(train) > inputs['expected_out0_train'], 'not_a_strict_training_superset')
    ids = {r['qid'] for r in rows}
    require(len(ids) == len(rows), 'duplicate_output_qids')
    derived = trainer_split.make_inherited_split(rows, rows, old_record,
        seed=old_record['seed'], heldout_fraction=old_record['heldout_fraction_of_groups'])
    for key, side_rows in (('train_candidate_qids', train), ('heldout_qids', heldout)):
        require(sorted(r['qid'] for r in side_rows) == derived[key] == record[key], 'split_membership_mismatch')
    old_sides = trainer_split.published_group_sides(old_record)
    new_sides = trainer_split.published_group_sides(record)
    require(all(new_sides.get(g) == side for g, side in old_sides.items()), 'split_inheritance_changed')
    for key in ('train_scenes', 'heldout_scenes'):
        require(set(old_record[key]) <= set(record[key]), 'inherited_exact_scene_missing')
    heldout_groups = set(record['heldout_group_ids'])
    require(not {trainer_split.physical_group(r['dataset'], r['scene']) for r in train} & heldout_groups,
            'holdout_scene_in_train')
    forbidden_qids, forbidden_groups = inherited.benchmark_exclusions(inputs['benchmark_sources'])
    require(not {r['qid'] for r in train} & forbidden_qids, 'benchmark_qid_in_train')
    require(not {control.scene_group(r['dataset'], r['scene']) for r in train} & forbidden_groups,
            'benchmark_scene_in_train')
    for side in ('train', 'heldout'):
        output_lines = {compact.decode_json(line)['qid']: line for line in (mix / (side + '.jsonl')).read_bytes().splitlines(keepends=True) if line.strip()}
        source_lines = [line for line in (Path(inputs['source_mix']) / (side + '.jsonl')).read_bytes().splitlines(keepends=True) if line.strip()]
        if side == 'train':
            require(len(source_lines) == inputs['expected_out0_train'], 'OUT0_training_count')
        for line in source_lines[:inputs['limit_per_root_and_out0_side'] or None]:
            require(output_lines.get(compact.decode_json(line)['qid']) == line, 'OUT0_superset_byte_identity')
    by_id = {r['qid']: r for r in rows}
    entries = list(source.read_jsonl(layout / 'candidate_index.jsonl'))
    require({r['qid'] for r in entries} == ids and len(entries) == len(rows), 'candidate_membership_mismatch')
    old_materialization = source.read_json(inputs['source_materialization']['path'])
    old_entries = control.identities(inherited.unique_rows(control.checked_bytes(
        old_materialization['artifacts']['candidate_index.jsonl'])))
    for entry in entries:
        row, row_bytes, target = control.bundle(entry)
        require(row == by_id[entry['qid']], 'mix_trainer_row_identity')
        if entry['qid'] in old_entries:
            _, old_row_bytes, old_target = control.bundle(old_entries[entry['qid']])
            require((row_bytes, target) == (old_row_bytes, old_target), 'OUT0_layout_byte_identity')
        require(target in (row['target'].encode(), (row['target'] + '\n').encode()), 'trainer_target_identity')
        for row_key, entry_key in (('qid', 'qid'), ('dataset', 'dataset'), ('scene', 'scene'), ('category', 'question_type')):
            require(row[row_key] == entry[entry_key], 'candidate_identity_mismatch')
        for key in ('generation_commit', 'validation_commit'):
            require(bool(re.fullmatch(r'[0-9a-f]{40}', entry[key])) and row.get(key, entry[key]) == entry[key],
                    'candidate_commit_mismatch')
        provisional.validate_rgb(row['student_input'])
    for name in ('split.json', 'split_trainer.json'):
        require((mix / name).read_bytes() == (layout / name).read_bytes(), 'layout_split_identity')
    published = source.read_json(mix / 'split.json')
    require(published['train_qids'] == [r['qid'] for r in train] and published['heldout_qids'] == [r['qid'] for r in heldout], 'mix_split_identity')
    frames = source.Frames()
    sample = random.Random(SAMPLE_SEED).sample(rows, min(args.frame_sample, len(rows)))
    for row in sample:
        frames.row(row)
    if args.native_loader:
        progress(out, 'Run pinned native candidate loader on CPU')
        loaded = provisional.load_provisional_candidates(layout / 'candidate_index.jsonl', inherited.common.LABEL)
        require(len(loaded) == len(rows), 'native_loader_count')
        replay = provisional.split_candidates(loaded, inherited.common.LABEL,
            inherited_from=source.pin(layout / 'split_trainer.json'))['split']
        require(replay['train_candidate_qids'] == sorted(r['qid'] for r in train), 'native_loader_split')
    result = {'passed': True, 'train': len(train), 'heldout': len(heldout),
              'out0_full_superset': not bool(inputs['limit_per_root_and_out0_side']),
              'out0_selected_bytes_preserved': True, 'holdout_in_train': 0,
              'inherited_groups_stable': len(old_sides), 'frame_sample_rows': len(sample),
              'frame_sample_unique_files': len(frames.checked), 'native_loader_passed': args.native_loader}
    source.write_json(out / 'VERIFICATION.json', result)
    summary = source.read_json(out / 'BUILD_SUMMARY.json')
    summary.update(status='verified', verification=result)
    source.write_json(out / 'BUILD_SUMMARY.json', summary)
    render_report(out, summary)
    progress(out, 'Verification passed', f"{len(train)} train; {len(heldout)} heldout", 'Orchestrator may review package')
    print(json.dumps(result, sort_keys=True), flush=True)
    return result


def inventory_names(root):
    return [str(p.relative_to(root)) for p in root.rglob('*') if p.is_file() and p != root / 'MANIFEST.json']


def parser():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    build_parser = sub.add_parser('build')
    verify_parser = sub.add_parser('verify')
    for p in (build_parser, verify_parser):
        for name in ('output-mix', 'output-layout', 'out'):
            p.add_argument('--' + name, type=Path, required=True)
    for name, default in (
        ('source-mix', OUT0), ('source-layout', Path(str(OUT0) + '_trainer')),
        ('root-a', ROOT_A), ('root-a-run', D / 'collection_gt_r1313'),
        ('root-b-run', D / 'collection_gt_r1316'), ('trainer', TRAINER),
        ('root-a-members', D / 'membership/v2/train50k_scene_reuse_answer_free.jsonl'),
        ('root-a-labels', D / 'offline_labels/v2/train50k_scene_reuse_labels.jsonl'),
        ('members', D / 'membership/v3/train105k_scannet_family_answer_free.jsonl'),
        ('labels', D / 'offline_labels/v3/train105k_scannet_family_labels.jsonl'),
        ('room-labels', D / 'source/vsi_590k.jsonl')):
        build_parser.add_argument('--' + name, type=Path, default=default)
    for name, default in (('split-sha', SPLIT_SHA), ('native-split-sha', NATIVE_SPLIT_SHA),
                          ('root-a-members-sha', A_MEMBERS_SHA), ('root-a-labels-sha', A_LABELS_SHA),
                          ('members-sha', MEMBERS_SHA), ('labels-sha', LABELS_SHA), ('room-sha', ROOM_SHA)):
        build_parser.add_argument('--' + name, default=default)
    build_parser.add_argument('--limit', type=int, default=0, help='Bound each teacher root and each OUT0 side; zero means full superset')
    build_parser.add_argument('--expected-train', type=int, default=7684)
    build_parser.add_argument('--expected-root-a', type=int, default=20139)
    build_parser.add_argument('--target-format', choices=('bare', 'native-block'), default='bare')
    verify_parser.add_argument('--frame-sample', type=int, default=30)
    verify_parser.add_argument('--native-loader', action='store_true', help='Also run b084aaf CPU loader, which hashes every frame')
    return parser


def main():
    args = parser().parse_args()
    require(getattr(args, 'limit', 0) >= 0, 'negative_limit')
    try:
        (build if args.command == 'build' else verify)(args)
    except Exception as error:
        args.out.mkdir(parents=True, exist_ok=True)
        source.write_json(args.out / 'FAILURE.json', {'command': args.command, 'error': repr(error), 'timestamp': source.utc()})
        (args.out / 'REPORT.md').write_text(f'{args.command} failed: {error}\nPartial artifacts remain in place. No deletion or collector mutation occurred.\n')
        raise


if __name__ == '__main__':
    main()
