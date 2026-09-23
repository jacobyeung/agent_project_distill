import argparse
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

from .blocking import scene_key
from .io import canonical, pin, read_json, read_jsonl, source_commit
from .split import group_id
from .swarm import LABEL, evaluation_authority, require, verify_set, write_new


def validate_membership(entries, expected_split, protocol, training, forbidden_qids, blocked_groups):
    qids = [entry['qid'] for entry in entries]
    expected = set(qids)
    split = protocol['split']
    require(len(expected) == len(qids) and expected == set(expected_split['train_candidate_qids']), 'bridge_candidate_membership')
    require(set(split['train_candidate_qids']) == expected
            and set(split['heldout_qids']) == set(expected_split['heldout_qids'])
            and split['hashed_group_count'] == 0, 'bridge_inherited_split')
    require(not training['pre_evaluation_drops'] and training['training_ready'] is True, 'bridge_training_drops')
    require(len(training['rows']) == len(qids) and {row['qid'] for row in training['rows']} == expected, 'bridge_training_membership')
    heldout = set(split['heldout_qids'])
    heldout_groups = set(split['heldout_group_ids'])
    for entry in entries:
        source_qid = entry.get('h5_source_qid', entry['qid'])
        require(entry['qid'] not in heldout and source_qid not in heldout, 'bridge_heldout_qid')
        require(entry['qid'] not in forbidden_qids and source_qid not in forbidden_qids, 'bridge_evaluation_qid')
        require(group_id(entry['dataset'], entry['scene']) not in heldout_groups, 'bridge_heldout_scene')
        require(scene_key(entry['dataset'], entry['scene']) not in blocked_groups, 'bridge_evaluation_scene')
    return {'training_rows': len(qids), 'heldout_context_rows': len(heldout), 'heldout_in_train': 0,
            'evaluation_subset_qids_in_train': 0, 'hashed_group_count': 0, 'token_limit_drops': 0}


def same_or_new(path, value):
    if path.exists():
        require(read_json(path) == value, 'bridge_existing_receipt_differs')
        return pin(path)
    return write_new(path, value)


def check_ready(args):
    commit = source_commit()
    dataset, run = args.dataset.resolve(), args.run.resolve()
    require(run.is_relative_to('/data2') and dataset.is_relative_to('/data2'), 'bridge_owned_data_root')
    checked = verify_set(dataset)
    require(checked['verdict'] == 'PASS', 'bridge_dataset_admission')
    config = read_json(dataset / 'CONFIG.json')
    layout = read_json(args.layout_audit)
    require(layout['verdict'] == 'PASS' and layout['r12_length_policy_pass'] is True
            and Path(layout['directory']).resolve() == dataset, 'bridge_layout_audit')
    require(args.handcheck.is_file() and args.handcheck.stat().st_size > 0, 'bridge_handcheck_missing')
    trainer = Path(config['trainer_root'])
    actual_commit = subprocess.check_output(['git', '-C', str(trainer), 'rev-parse', 'HEAD'], text=True).strip()
    status = subprocess.check_output(['git', '-C', str(trainer), '--no-optional-locks', 'status', '--porcelain'], text=True)
    require(actual_commit == config['trainer_commit'] and not status.strip(), 'bridge_trainer_pin')
    sys.path.insert(0, str(trainer))
    from student_pilot.provisional_data import load_protocol, load_training
    from student_pilot.ddp_admission import checked_request

    frozen = run / 'frozen'
    protocol = load_protocol(frozen / 'protocol.json', LABEL, student='onethinker')
    training = load_training(frozen / 'training.json', LABEL)
    request = checked_request(frozen / 'train_request.json', LABEL)
    recipe = read_json(run / 'training_config.json')
    require(recipe == read_json(args.reference_recipe) and recipe['world_size'] == 2
            and recipe['effective_batch_size'] == 32 and recipe['epochs'] == 3 and recipe['seed'] == 17,
            'bridge_reference_recipe')
    require(len(request['ranks']) == 2, 'bridge_world_size')
    entries = list(read_jsonl(dataset / 'candidate_index.jsonl'))
    forbidden, blocked, evaluation_pin = evaluation_authority(config['eval_qids'], config['eval_qids_sha256'])
    counts = validate_membership(entries, read_json(dataset / 'split_trainer.json'), protocol, training, forbidden, blocked)
    require(training['counts']['target_tokens_including_eos'] == layout['native_target_tokens_including_eos']['total'],
            'bridge_native_token_accounting')
    files = [dataset / 'MANIFEST.json', dataset / 'candidate_index.jsonl', dataset / 'split_trainer.json',
             args.layout_audit, args.handcheck, run / 'training_config.json', args.reference_recipe,
             frozen / 'protocol.json', frozen / 'training.json', frozen / 'train_request.json']
    record = {'schema': 'h05-native-cpu-ready-v1', 'status': 'READY_FOR_SUPERVISOR_NOT_GPU_ADMISSION',
              'bridge_commit': commit, 'bridge_source': pin(__file__), 'trainer_commit': actual_commit,
              'dataset': str(dataset), 'run': str(run), 'evaluation': evaluation_pin, 'counts': counts,
              'native_counts': training['counts'], 'inputs': [pin(path) for path in files],
              'native_work_ids': [rank['work_id'] for rank in request['ranks']],
              'no_gpu_probe_or_coordination_mutation': True, 'score_nomination_allowed': False}
    return record, same_or_new(run / ('NATIVE_CPU_READY_' + commit[:12] + '.json'), record)


def bind_harness(args):
    record, ready_pin = check_ready(args)
    require(args.harness and args.harness_commit and args.train_host and args.train_cards and args.eval_cards,
            'bridge_harness_placement_required')
    harness = args.harness.resolve()
    actual = subprocess.check_output(['git', '-C', str(harness), 'rev-parse', 'HEAD'], text=True).strip()
    status = subprocess.check_output(['git', '-C', str(harness), '--no-optional-locks', 'status', '--porcelain'], text=True)
    require(actual == args.harness_commit and not status.strip(), 'bridge_harness_pin')
    sys.path.insert(0, str(harness))
    from student.iteration_harness.cli import configuration
    from student.iteration_harness.io import once, stage

    run = args.run.resolve()
    options = SimpleNamespace(name=run.name, pool_id='h05_gtmeasure_augmentation' if record['counts']['training_rows'] == 2000 else 'h05_gtmeasure_only',
                              n=record['counts']['training_rows'], seed=20260923, lane=run.parents[1],
                              candidate_index=args.dataset.resolve() / 'candidate_index.jsonl',
                              train_host=args.train_host, train_cards=args.train_cards, eval_cards=args.eval_cards,
                              full=False, dry_run=True)
    target, config = configuration(options)
    require(target == run and len(config['train_cards']) == 2, 'bridge_harness_run_identity')
    config.update(pool_adapter=ready_pin, fixed_evaluation_authority=record['evaluation'])
    once(run / 'CONFIG.json', config)
    with stage(run, 2, {'configuration': pin(run / 'CONFIG.json'), 'native_cpu_ready': ready_pin,
                        'pool_adapter': pin(__file__), 'pool_adapter_commit': record['bridge_commit']}) as result:
        if result is not None:
            result.update(outputs=record['inputs'], training_ready=True, cpu_only=True,
                          training_rows=record['counts']['training_rows'], heldout_context_rows=record['counts']['heldout_context_rows'],
                          trainonly_index=str(args.dataset.resolve() / 'candidate_index.jsonl'),
                          protocol=str(run / 'frozen/protocol.json'), training_manifest=str(run / 'frozen/training.json'),
                          leakage=record['counts'], protocol_context_is_not_a_training_layout=True,
                          pool_contract='R4 authorized GT-only or GT plus frozen common A0; no training/scoring implementation changed')
    return {'status': 'HARNESS_STAGE_3_READY_NO_GPU_STARTED', 'run': str(run), 'config': pin(run / 'CONFIG.json'),
            'stage_2': pin(run / 'STAGE_2.json'), 'train_command': ['bash', str(harness / 'student/iteration_harness/stage_3.sh'), '--run', str(run)],
            'evaluation_gate': 'Use only a harness path bound to the recorded D/EVAL_QIDS authority; legacy auto-subset preparation is not authorized.'}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('check', 'bind'))
    parser.add_argument('--dataset', type=Path, required=True)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--layout-audit', type=Path, required=True)
    parser.add_argument('--handcheck', type=Path, required=True)
    parser.add_argument('--reference-recipe', type=Path, required=True)
    parser.add_argument('--harness', type=Path)
    parser.add_argument('--harness-commit')
    parser.add_argument('--train-host')
    parser.add_argument('--train-cards')
    parser.add_argument('--eval-cards', nargs='+')
    args = parser.parse_args()
    result = check_ready(args)[0] if args.action == 'check' else bind_harness(args)
    print(canonical(result), flush=True)


if __name__ == '__main__':
    main()
