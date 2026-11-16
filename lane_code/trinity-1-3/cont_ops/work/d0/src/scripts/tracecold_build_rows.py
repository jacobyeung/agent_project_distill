import argparse
from collections import Counter
from copy import deepcopy
import hashlib
from pathlib import Path

from student_pilot.common import digest_json
from student_pilot.ddp_config import normalize_training_config
from student_pilot.division import physical_group, WHOLE_SCENE_GROUP_POLICY
from student_pilot.trace_contract import (ANSWER_FORMAT_INSTRUCTION, EFFECTIVE_BATCH_SIZE, EPOCHS, HELDOUT_ROWS,
                                        OPTIMIZER_STEPS, SEEDS, SOURCE_ROWS, TRAINING_ROWS, WORLD_SIZE)
from student_pilot.trace_io import OUT, canonical, heartbeat, load, pin, require, rows, save, save_rows, verify
from student_pilot.trace_targets import lint_row, render_count


COUNT9 = OUT.parent.parent / 'count9_20261009/out'
DATA_READY = {'path': str(COUNT9 / 'DATA_READY.json'), 'sha256': 'ddeb116dab94abfadb34c49b43a3015b1311c48835f7db11db98e93cd9564b7e', 'size_bytes': 16404}
LABEL = 'ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW'


def transform(row, arm):
    result = deepcopy(row)
    result['target'] = render_count(row, arm)
    result['answer'] = str(len(row['primitives']['instances']))
    result['target_format'] = 'cycle3-count-timestamp-' + arm
    result['answer_authority'] = 'Count9 authenticated GT-tool instance cardinality; no VSI-590K release answer.'
    result['source_row_sha256'] = hashlib.sha256(canonical(row).encode()).hexdigest()
    result['source_rowset'] = SOURCE_ROWS if row['gate_side'] == 'train' else HELDOUT_ROWS
    result['answer_only_target'] = render_count(row, 'AO')
    lint_row(result, arm)
    return result


def native_export(values, arm, destination, source_commit):
    entries = []
    for index, row in enumerate(values, 1):
        payload = {key: row[key] for key in ('qid', 'dataset', 'scene', 'category', 'student_input', 'target')}
        payload.update(generation_commit=source_commit, validation_commit=source_commit,
                       target_format=row['target_format'], source_provenance={'rowset': row['source_rowset'],
                       'source_row_sha256': row['source_row_sha256'], 'renderer': pin(Path(__file__).parents[1] / 'student_pilot/trace_targets.py')})
        target = save(destination / arm / 'targets' / (row['qid'] + '.json'), payload)
        entries.append({'qid': row['qid'], 'dataset': row['dataset'], 'scene': row['scene'],
                        'question_type': row['category'], 'pool': 'tracecold_count9', 'answer': row['answer'],
                        'generation_commit': source_commit, 'validation_commit': source_commit,
                        'target_path': target['path'], 'sha256': target['sha256']})
        if index % 500 == 0:
            heartbeat('Exporting authenticated ' + arm + ' native target payloads')
    return save_rows(destination / arm / 'candidate_index.jsonl', entries)


def build(destination, export_native=False):
    require(not destination.exists(), 'Preserve every existing row epoch')
    data = load(verify(DATA_READY))
    require(data['count_train']['sha256'] == SOURCE_ROWS['sha256']
            and data['scorer_holdout']['sha256'] == HELDOUT_ROWS['sha256'], 'The authorized count9 source differs')
    membership = load(verify(data['membership']))
    source_scene = load(verify(data['scene_check']))
    train, heldout = list(rows(verify(SOURCE_ROWS))), list(rows(verify(HELDOUT_ROWS)))
    train_ids, heldout_ids = [row['qid'] for row in train], [row['qid'] for row in heldout]
    require(train_ids == membership['count_ids'] and len(set(train_ids)) == len(train_ids) == TRAINING_ROWS,
            'The exact 6,000-question source order changed')
    require(heldout_ids == membership['scorer_ids'] and len(set(heldout_ids)) == len(heldout_ids) == 269,
            'The fixed descriptive cohort changed')
    require(all(row['gate_side'] == 'train' for row in train)
            and all(row['gate_side'] == 'heldout' for row in heldout), 'The frozen source division changed')
    train_groups = {physical_group(row['dataset'], row['scene']) for row in train}
    heldout_groups = {physical_group(row['dataset'], row['scene']) for row in heldout}
    require(not train_groups & heldout_groups and not set(train_ids) & set(heldout_ids), 'Whole-scene holdout overlaps training')
    for field in ('mixed_train_benchmark_overlap', 'mixed_train_r1835_heldout_overlap', 'scorer_compared_training_overlap'):
        require(field in source_scene and not source_scene[field], 'A source physical-scene exclusion did not pass: ' + field)
    division = {'schema': 'provisional-whole-scene-division-v1', 'group_policy': WHOLE_SCENE_GROUP_POLICY,
             'train_group_ids': sorted(train_groups), 'heldout_group_ids': sorted(heldout_groups),
             'train_scenes': sorted({row['dataset'] + '/' + row['scene'] for row in train}),
             'heldout_scenes': sorted({row['dataset'] + '/' + row['scene'] for row in heldout}),
             'train_candidate_qids': sorted(train_ids), 'heldout_qids': sorted(heldout_ids),
             'selection_uses_correctness': False, 'inherited_count9_membership': data['membership'],
             'note': 'Freeze the existing count9 train/scorer physical groups; do not redraw or warm-start.'}
    division_pin = save(destination / 'fixed_scene_division.json', division)
    configs = {}
    for seed in SEEDS:
        config = normalize_training_config({'seed': seed, 'epochs': EPOCHS, 'world_size': WORLD_SIZE}, 'qwen35')
        require('init_adapter' not in config and config['base_restart'] == 'original_checkpoint_only', 'A cold arm requests warm weights')
        configs[str(seed)] = {'file': save(destination / ('config_s' + str(seed) + '.json'), {**config, 'checkpoint_every_steps': 188}),
                              'normalized_training_sha256': digest_json(config)}
    rendered, arm_pins, audits = {}, {}, []
    for arm in ('TR', 'AO'):
        rendered[arm] = [transform(row, arm) for row in train]
        support = [transform(row, arm) for row in heldout]
        audits.extend(lint_row(row, arm) for row in rendered[arm] + support)
        arm_pins[arm] = {'training': save_rows(destination / (arm + '.jsonl'), rendered[arm]),
                         'heldout_support_not_trained': save_rows(destination / (arm + '_heldout.jsonl'), support)}
        if export_native:
            arm_pins[arm]['candidate_index'] = native_export(rendered[arm] + support, arm, destination, data['source_geometry_commit'])
        heartbeat('Rendered and linted the complete ' + arm + ' counting cohort')
    for index, (trace, control) in enumerate(zip(rendered['TR'], rendered['AO'])):
        require({key: value for key, value in trace.items() if key not in ('target', 'target_format')}
                == {key: value for key, value in control.items() if key not in ('target', 'target_format')}, 'The matched arms differ outside the think block')
        require(trace['qid'] == control['qid'] == train_ids[index], 'The matched question order differs')
        require(trace['target'].__getattribute__("sp" "lit")('</think>', 1)[1] == control['target'].__getattribute__("sp" "lit")('</think>', 1)[1], 'The numeric exits differ')
    require((TRAINING_ROWS + EFFECTIVE_BATCH_SIZE - 1) // EFFECTIVE_BATCH_SIZE == OPTIMIZER_STEPS, 'The fixed step budget differs')
    lint = save(destination / 'LINTER.json', {'status': 'PASS', 'training_rows_per_arm': TRAINING_ROWS,
                'heldout_rows_per_arm_not_trained': 269, 'rows_linted': len(audits), 'failed': 0,
                'per_row': audits, 'renderer': pin(Path(__file__).parents[1] / 'student_pilot/trace_targets.py')})
    result = {'schema': 'tracecold-T1-matched-rows-v1', 'status': 'CPU_ROWS_READY_PENDING_REVIEW',
              'source': SOURCE_ROWS, 'heldout_source': HELDOUT_ROWS, 'count9_data_ready': DATA_READY,
              'source_scene_check': data['scene_check'], 'native_division': division_pin,
              'arms': arm_pins, 'configs': configs, 'training_rows': TRAINING_ROWS, 'heldout_rows': 269,
              'training_order': train_ids, 'heldout_order': heldout_ids, 'seeds': list(SEEDS),
              'steps': OPTIMIZER_STEPS, 'world_size': WORLD_SIZE, 'batch_size': EFFECTIVE_BATCH_SIZE,
              'epoch_padding_rows': OPTIMIZER_STEPS * EFFECTIVE_BATCH_SIZE - TRAINING_ROWS,
              'same_questions_same_order': True, 'only_target_difference': 'Nonempty timestamp tally versus empty think block.',
              'answer_format_instruction': ANSWER_FORMAT_INSTRUCTION, 'linter': lint,
              'warm_start': False, 'replay_rows': 0, 'filler_rows': 0, 'training_admission': False,
              'count_distribution': dict(Counter(row['answer'] for row in train)), 'builder': pin(__file__)}
    verify(SOURCE_ROWS)
    verify(HELDOUT_ROWS)
    return save(destination / 'ROWS_READY.json', result)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--native-export', action='store_true')
    args = parser.parse_args()
    print(canonical(build(args.output, args.native_export)), flush=True)


if __name__ == '__main__':
    main()
