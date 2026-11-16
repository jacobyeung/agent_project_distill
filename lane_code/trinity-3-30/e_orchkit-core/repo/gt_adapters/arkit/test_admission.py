"""Persistent admission/census fixtures using real donor leases and the real episode pool."""
from __future__ import annotations
import argparse
import copy
import json
import os
import shutil
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from gt_scene_assets import DATA_ROOT, read_json, sha, write_json
from audit_package import HERE, verify_contract
from collect import load_config, coord_guard, objects, initialize, validate_config
from coordination import cmd_complete, do_claim, cmd_heartbeat, agent_id
from test_runner_transport import fixture_config

TASK = DATA_ROOT / 'runtime_control/gt_teacher_r1313'


def refused(call, label):
    try:
        call()
    except (ValueError, RuntimeError, KeyError, OSError, SystemExit):
        return label
    raise AssertionError('admission accepted ' + label)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--contract', type=Path, required=True)
    parser.add_argument('--contract-sha256', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    config, coord = fixture_config(args.output, args.contract, args.contract_sha256)
    cases = []
    live_path = Path('/data2/jjyeung/agent_project/.coord/LEASES/round__r1313.lock/lease.json')
    live = read_json(live_path)
    if live.get('work_id') != 'round__r1313' or live.get('agent_id') != 'req232-gt-teacher-r1313':
        raise ValueError('assigned shared lease identity differs from the brief')
    live_age = (datetime.now(timezone.utc) - datetime.fromisoformat(live['last_heartbeat'])).total_seconds()
    all_ready = dict(config, episode_limit=0)
    target, queue, pending = objects(all_ready)
    assert len(queue.catalog.episodes) == 297 and pending == 49703
    initialize(target, 2)
    first = queue.claim_next('owner', 0)
    assert first.episode is not None
    second = queue.claim_next('other', 1)
    assert second.episode is not None and second.episode != first.episode
    cases.append('exclusive_real_episode_claims')
    foreign = dict(config, agent_id='foreign-fixture-owner')
    cases.append(refused(lambda: coord_guard(foreign), 'foreign_collection_lease'))
    original_owner = agent_id()
    os.environ['AGENT_ID'] = 'foreign-fixture-owner'
    cases.append(refused(lambda: cmd_heartbeat(coord, SimpleNamespace(work_id=config['work_id'], status=None, note=None)), 'foreign_heartbeat'))
    os.environ['AGENT_ID'] = original_owner
    path = Path(coord.lease_dir(config['work_id'])) / 'lease.json'
    import coordination
    lease = read_json(path)
    old = dict(lease, last_heartbeat=(datetime.now(timezone.utc) - timedelta(hours=1)).isoformat())
    coordination.write_json(str(path), old)
    cases.append(refused(lambda: coord_guard(config), 'stale_collection_lease'))
    cmd_heartbeat(coord, SimpleNamespace(work_id=config['work_id'], status=None, note=None))
    cases.append(refused(lambda: load_config(config['_config_path'], service=True), 'fixture_config_paid_launch'))
    cases.append(refused(lambda: validate_config(dict(config, mode='production')), 'production_fixture_coord_root'))
    cases.append(refused(lambda: validate_config(dict(config, run_root='/tmp/forbidden')), 'output_outside_DATA'))
    cases.append(refused(lambda: objects(dict(config, budget=32768)), 'unselected_32k'))
    cases.append(refused(lambda: validate_config(dict(config, assets_registry_sha256='0' * 64)), 'registry_digest_drift'))
    contract = read_json(args.contract)
    corrupt = copy.deepcopy(contract)
    corrupt['source_files'].pop('gt_tool_bindings.py')
    corrupt['runtime_files'].remove('gt_tool_bindings.py')
    corrupt_path = args.output / 'symmetric_corruption_contract.json'
    write_json(corrupt_path, corrupt)
    cases.append(refused(lambda: verify_contract(corrupt_path, sha(corrupt_path)), 'symmetric_source_census_corruption'))
    copy_root = args.output / 'source_drift_fixture'
    shutil.copytree(HERE, copy_root)
    with (copy_root / 'gt_tool_bindings.py').open('a') as handle:
        handle.write('\nDRIFT_FIXTURE = True\n')
    cases.append(refused(lambda: verify_contract(args.contract, args.contract_sha256, root=copy_root), 'runtime_source_drift'))
    from training_assets import teacher_rows, bind_runtime_row
    row = next(r for r in teacher_rows() if r['scene_name'] == '104acbf7d2' and r['dataset'] == 'scannetppv2')
    receipt = read_json(first.episode.payload['scene_receipt']['path'])
    bound = bind_runtime_row(row, receipt)
    assert bound['question'] == row['question'] and bound.get('options') == row.get('options')
    assert bound['scene_name'] == 'scannetppv2__104acbf7d2' and bound['source_scene_name'] == '104acbf7d2'
    cases.append('source_question_preserved_and_scene_qualified')
    from transport_admission import is_rate_limit_error
    assert is_rate_limit_error({'status': 'error', 'http_status': 429})
    assert not is_rate_limit_error({'status': 'ok', 'duration': '429.8s'})
    cases.append('typed429_not_elapsed_duration')
    cmd_complete(coord, SimpleNamespace(work_id=config['work_id'], result=str(args.output / 'PROOF.json')))
    assert do_claim(coord, config['work_id'], {}) == (False, 'already-completed')
    cases.append('lease_terminal_prevents_reclaim')
    value = {'fixture_only': True, 'checks_passed': cases, 'first_scene_questions': 297,
             'membership_questions': 50000, 'pending_asset_questions': pending,
             'shared_coord_read_only': {'path': str(live_path), 'sha256_at_read': sha(live_path),
                 'agent_id': live['agent_id'], 'status': live['status'], 'heartbeat_age_seconds_at_read': live_age},
             'no_deletion': True, 'paid_calls': 0}
    spec = write_json(args.output / 'PROOF.json', value)
    print(json.dumps({'proof': spec, 'passed_checks': len(cases)}, indent=2))


if __name__ == '__main__':
    main()
