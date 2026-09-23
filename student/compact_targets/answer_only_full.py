import argparse
import json
import math
import subprocess
import sys
from pathlib import Path

from tools.provenance import provenance
from . import compact_control as control
from . import compact_counted_v1 as compact
from . import design_common as common


PIN_FIELDS = {'row_path', 'row_sha256', 'target_path', 'sha256'}
BENCHMARKS = {'vsibench_full', 'vstibench_full', 'revsi_full'}


def answer_text(entry):
    value = entry.get('answer')
    control.require(isinstance(value, (str, int, float)) and not isinstance(value, bool), 'answer_type')
    control.require(not isinstance(value, float) or math.isfinite(value), 'answer_finite')
    answer = str(value)
    control.require(bool(answer) and answer == answer.strip() and '\n' not in answer and '\r' not in answer,
                    'bare_answer_schema')
    return answer


def line_bytes(row):
    return (json.dumps(row, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False) + '\n').encode()


def unique_rows(payload):
    rows = [compact.decode_json(line) for line in payload.splitlines() if line.strip()]
    control.require(all(isinstance(row, dict) and isinstance(row.get('qid'), str) for row in rows), 'row_identity')
    control.require(len({row['qid'] for row in rows}) == len(rows), 'duplicate_qid')
    return rows


def benchmark_exclusions(blocking):
    control.require(set(blocking) == BENCHMARKS, 'full_benchmark_sources')
    qids, groups = set(), set()
    for pin in blocking.values():
        rows = control.checked_json(pin)
        control.require(isinstance(rows, list) and len(rows) == pin['rows'], 'benchmark_rows')
        for row in rows:
            qids.add(str(row['id']))
            dataset = row.get('revsi_source_corpus', row['dataset'])
            groups.add(control.scene_group(dataset, row['scene_name']))
    return qids, groups


def partition(rows, heldout, split, entries, expected_train):
    train_ids = [row['qid'] for row in rows]
    heldout_ids = [row['qid'] for row in heldout]
    control.require(len(train_ids) == expected_train and len(set(train_ids)) == expected_train, 'training_count')
    control.require(len(set(heldout_ids)) == len(heldout_ids), 'heldout_duplicates')
    control.require(not set(train_ids) & set(heldout_ids), 'heldout_in_train')
    control.require(set(split['train_qids']) == set(train_ids), 'published_train_membership')
    control.require(set(split['heldout_qids']) == set(heldout_ids), 'published_heldout_membership')
    control.require(len(split['train_qids']) == len(train_ids) and len(split['heldout_qids']) == len(heldout_ids),
                    'published_split_counts')
    index = control.identities(entries)
    control.require(set(index) == set(train_ids) | set(heldout_ids), 'candidate_pool_membership')
    train_groups = {control.scene_group(row['dataset'], row['scene']) for row in rows}
    heldout_groups = {control.scene_group(row['dataset'], row['scene']) for row in heldout}
    control.require(not train_groups & heldout_groups, 'heldout_scene_in_train')
    published_heldout = control.normalized_groups(split['all_heldout_groups'])
    control.require(not train_groups & published_heldout, 'published_heldout_scene_in_train')
    return index, set(train_ids), train_groups


def stage(source_mix, source_layout, output_mix, output_layout, expected_train, code):
    source_mix, source_layout, output_mix, output_layout = map(Path, (source_mix, source_layout, output_mix, output_layout))
    control.require(output_mix != output_layout and not any(out == src or out.is_relative_to(src)
                    for out in (output_mix, output_layout) for src in (source_mix, source_layout)), 'output_source_overlap')
    manifest = compact.load_json(source_mix / 'MANIFEST.json')
    materialization = compact.load_json(source_layout / 'MATERIALIZATION.json')
    payloads = {name: control.checked_bytes(manifest['artifacts'][name])
                for name in ('train.jsonl', 'heldout.jsonl', 'split.json')}
    rows, heldout = unique_rows(payloads['train.jsonl']), unique_rows(payloads['heldout.jsonl'])
    split = compact.decode_json(payloads['split.json'])
    source_index = control.checked_bytes(materialization['artifacts']['candidate_index.jsonl'])
    entries = unique_rows(source_index)
    control.require(control.checked_bytes(materialization['artifacts']['split.json']) == payloads['split.json'],
                    'source_split_byte_identity')
    index, train_ids, train_groups = partition(rows, heldout, split, entries, expected_train)
    forbidden_qids, forbidden_groups = benchmark_exclusions(manifest['benchmark_blocking'])
    control.require(not train_ids & forbidden_qids and not train_groups & forbidden_groups, 'benchmark_training_overlap')
    raw_by_id = {row['qid']: row for row in rows + heldout}
    split_trainer = compact.load_json(source_mix / 'split_trainer.json')
    control.require(set(split_trainer['train_candidate_qids']) == train_ids, 'native_split_train_membership')
    control.require(set(split_trainer['heldout_qids']) == {row['qid'] for row in heldout},
                    'native_split_heldout_membership')
    inputs = {'schema': 'answer-only-full-build-inputs-v1', 'source_mix': compact.binding(source_mix / 'MANIFEST.json'),
              'source_layout': compact.binding(source_layout / 'MATERIALIZATION.json'),
              'source_index': materialization['artifacts']['candidate_index.jsonl'],
              'source_split': manifest['artifacts']['split.json'],
              'source_native_split': compact.binding(source_mix / 'split_trainer.json'),
              'output_mix': str(output_mix), 'output_layout': str(output_layout), 'expected_train': expected_train,
              'code': code}
    for output in (output_mix, output_layout):
        control.require(not output.exists() or (output / 'BUILD_INPUTS.json').is_file(), 'unowned_output_exists')
        compact.save(output / 'BUILD_INPUTS.json', inputs)
    new_entries, audits = [], []
    for entry in entries:
        row, row_bytes, target_bytes = control.bundle(entry)
        source_row = raw_by_id[entry['qid']]
        control.require(all(row[key] == source_row[key] for key in ('qid', 'dataset', 'scene', 'category', 'student_input')),
                        f'raw_layout_input_identity: {entry["qid"]}')
        control.require(row['target'] == source_row['target'], f'raw_layout_target_identity: {entry["qid"]}')
        answer = answer_text(entry)
        if entry['qid'] in train_ids:
            row_bytes = compact.canonical_bytes({**row, 'target': answer})
            target_bytes = (answer + '\n').encode()
        new_entry = control.copy_entry(entry, row_bytes, target_bytes, output_layout)
        control.require({k: v for k, v in new_entry.items() if k not in PIN_FIELDS}
                        == {k: v for k, v in entry.items() if k not in PIN_FIELDS}, 'index_metadata_changed')
        new_entries.append(new_entry)
        audits.append({'qid': entry['qid'], 'training': entry['qid'] in train_ids,
                       'source_row': {'path': entry['row_path'], 'sha256': entry['row_sha256']},
                       'source_target': {'path': entry['target_path'], 'sha256': entry['sha256']},
                       'output_row': {'path': new_entry['row_path'], 'sha256': new_entry['row_sha256']},
                       'output_target': {'path': new_entry['target_path'], 'sha256': new_entry['sha256']}})
    train_payload = b''.join(line_bytes({**row, 'target': answer_text(index[row['qid']])}) for row in rows)
    mix_artifacts = {'train.jsonl': compact.save(output_mix / 'train.jsonl', train_payload),
                     'heldout.jsonl': compact.save(output_mix / 'heldout.jsonl', payloads['heldout.jsonl'])}
    layout_artifacts = {'candidate_index.jsonl': compact.save(output_layout / 'candidate_index.jsonl',
                                                             b''.join(line_bytes(row) for row in new_entries))}
    for output, artifacts in ((output_mix, mix_artifacts), (output_layout, layout_artifacts)):
        artifacts['split.json'] = compact.save(output / 'split.json', payloads['split.json'])
        artifacts['split_trainer.json'] = compact.save(output / 'split_trainer.json',
                                                      control.checked_bytes(inputs['source_native_split']))
    audit_pin = compact.save(output_layout / 'ROW_AUDIT.jsonl', b''.join(line_bytes(row) for row in audits))
    control.require([row['qid'] for row in new_entries] == [row['qid'] for row in entries], 'candidate_order_changed')
    control.require([row['qid'] for row in unique_rows(train_payload)] == [row['qid'] for row in rows],
                    'training_order_changed')
    report = {'schema': 'answer-only-full-stage-v1', 'inputs': inputs, 'mix_artifacts': mix_artifacts,
              'layout_artifacts': layout_artifacts, 'row_audit': audit_pin, 'benchmark_sources': manifest['benchmark_blocking'],
              'counts': {'train': len(rows), 'heldout': len(heldout), 'candidate_index': len(entries),
                         'answer_only_targets': len(rows), 'heldout_targets_unchanged': len(heldout),
                         'heldout_in_train': 0, 'benchmark_training_overlap': 0},
              'training_qids': [row['qid'] for row in rows],
              'candidate_qid_order_sha256': compact.digest_json([row['qid'] for row in entries]),
              'source_non_target_fields_preserved': True, 'heldout_bytes_preserved': True}
    layout_artifacts['MATERIALIZATION.json'] = compact.save(output_layout / 'MATERIALIZATION.json', {
        'schema': 'answer-only-full-candidate-layout-v1', 'artifacts': dict(layout_artifacts),
        'counts': report['counts'], 'source_materialization': inputs['source_layout'],
        'source_mix': str(output_mix), 'row_audit': audit_pin, 'code': code,
        'target_transform': 'Bare indexed answer for training; unchanged heldout context',
        'gpu_training_admission_claimed': False})
    compact.save(output_layout / 'STAGED.json', report)
    return report


def validate_native(report, trainer):
    trainer = Path(trainer).resolve()
    head = subprocess.check_output(['git', '-C', str(trainer), 'rev-parse', 'HEAD'], text=True).strip()
    control.require(head == common.TRAINER_COMMIT, 'native_trainer_commit')
    sys.path.insert(0, str(trainer))
    from student_pilot import batches, provisional
    import torch
    control.require(Path(provisional.__file__).resolve().is_relative_to(trainer), 'native_loader_import_path')
    layout = Path(report['inputs']['output_layout'])
    loaded = provisional.load_provisional_candidates(layout / 'candidate_index.jsonl', common.LABEL)
    inherited = provisional.split_candidates(loaded, common.LABEL,
                                             inherited_from=report['layout_artifacts']['split_trainer.json'])['split']
    expected = set(report['training_qids'])
    control.require(set(inherited['train_candidate_qids']) == expected, 'native_loader_train_membership')
    control.require(len(loaded) == report['counts']['candidate_index'], 'native_loader_candidate_count')
    control.require(not expected & set(inherited['heldout_qids']), 'native_loader_heldout_overlap')
    processor = batches.load_processor('onethinker')
    tokenizer, counts = processor.tokenizer, []
    for row in loaded:
        if row['qid'] not in expected:
            continue
        control.require(row['target'] == str(row['answer']), 'native_answer_byte_identity')
        prompt, suffix = batches.training_text(processor, row['student_input']['question'],
                                               row['student_input']['options'], row['target'])
        prefix_ids = tokenizer.encode(prompt, add_special_tokens=False)
        suffix_ids = tokenizer.encode(suffix, add_special_tokens=False)
        control.require(bool(suffix_ids) and suffix_ids[-1] == tokenizer.eos_token_id, 'native_assistant_eos')
        control.require(tokenizer.decode(prefix_ids + suffix_ids, skip_special_tokens=False) == prompt + suffix,
                        'native_assistant_roundtrip')
        ids = torch.tensor([prefix_ids + suffix_ids], dtype=torch.long)
        labels = batches.assistant_labels(ids, torch.ones_like(ids), len(prefix_ids), len(suffix_ids))
        control.require(int((labels != -100).sum()) == len(suffix_ids) and labels[0, -1].item() == tokenizer.eos_token_id,
                        'native_eos_supervision')
        counts.append(len(suffix_ids))
    control.require(len(counts) == len(expected), 'native_training_acceptance_count')
    return {'schema': 'answer-only-native-loader-check-v1', 'passed': True, 'trainer_commit': head,
            'native_candidates_accepted': len(loaded), 'training_rows_accepted': len(counts),
            'heldout_context_rows': len(loaded) - len(counts), 'heldout_in_train': 0,
            'native_assistant_eos_verified': len(counts), 'assistant_tokens_including_eos': sum(counts),
            'max_assistant_tokens_including_eos': max(counts), 'input_frame_hashes_checked_by_native_loader': True,
            'full_sequence_retokenization_claimed': False, 'gpu_training_admission_claimed': False,
            'validation_scope': 'Native candidate loader, inherited split, native assistant boundary, and EOS loss mask; no GPU use'}


def main():
    parser = argparse.ArgumentParser()
    for name in ('source-mix', 'source-layout', 'output-mix', 'output-layout'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--expected-train', type=int, default=7684)
    parser.add_argument('--trainer', type=Path, default=common.TRAINER)
    args = parser.parse_args()
    code = provenance(args.source_mix / 'MANIFEST.json')
    control.require(not code['dirty'], 'dirty_transformer_checkout')
    code['module'] = compact.binding(Path(__file__).resolve())
    report = stage(args.source_mix.resolve(), args.source_layout.resolve(), args.output_mix.resolve(),
                   args.output_layout.resolve(), args.expected_train, code)
    validation = validate_native(report, args.trainer)
    validation_pin = compact.save(args.output_layout / 'NATIVE_ADMISSION.json', validation)
    manifest = {**report, 'schema': 'answer-only-full-mix-v1', 'native_validation': validation_pin,
                'heldout_policy': 'Preserve heldout bytes as protocol context; convert only the inherited training membership',
                'transformation': 'Replace row.target with the exact indexed answer; target.txt is answer plus one newline'}
    mix_manifest = {**manifest, 'artifacts': report['mix_artifacts']}
    layout_manifest = {**manifest, 'artifacts': report['layout_artifacts']}
    mix_pin = compact.save(args.output_mix / 'MANIFEST.json', mix_manifest)
    layout_pin = compact.save(args.output_layout / 'MANIFEST.json', layout_manifest)
    print(json.dumps({'ready': True, 'mix_manifest': mix_pin, 'layout_manifest': layout_pin,
                      'counts': report['counts'], 'native_validation': validation_pin}, sort_keys=True), flush=True)


if __name__ == '__main__':
    main()
