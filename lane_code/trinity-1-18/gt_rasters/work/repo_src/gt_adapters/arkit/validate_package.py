"""Bounded CPU validation with immutable logs, then a generated closure/census manifest."""
from __future__ import annotations
import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from types import SimpleNamespace
import numpy as np
from gt_scene_assets import DATA_ROOT, data_path, pin, read_json, sha, verify, write_json, load_arrays, validate_scene

HERE = Path(__file__).resolve().parent
TASK = DATA_ROOT / 'runtime_control/gt_teacher_r1313'
SCENE = TASK / 'scene104acbf7d2_v1'
REQUIRED_ENV = {'PYTHONDONTWRITEBYTECODE': '1', 'HF_HOME': '/data2/jjyeung/cache/huggingface',
                'HUGGINGFACE_HUB_CACHE': '/data2/jjyeung/cache/huggingface/hub',
                'TORCH_HOME': '/data2/jjyeung/cache/torch', 'PIP_CACHE_DIR': '/data2/jjyeung/cache/pip', 'GP_NATIVE': '1'}


def alignment_validation(output):
    from prepare_gt_scene import inputs, selected_camera_alignment
    from donor_geometry import Renderer
    from gt_training_r1313 import TrainingGrounding
    receipt = validate_scene(read_json(SCENE / 'scene_receipt.json'), load_dense=True)
    provenance = read_json(verify(receipt['source_provenance']))
    for spec in provenance['raw_sources'].values():
        verify(spec, prepared=False)
    frames_path = verify(provenance['source_frames_receipt'])
    raw, frames, vertices, faces, groups, face_ids, basis, diagnostics = inputs(SimpleNamespace(scene=receipt['scene_name'], frames_receipt=frames_path))
    mesh = load_arrays(receipt['instance_mesh'])
    assert np.array_equal(vertices, mesh['vertices_world']) and np.array_equal(faces, mesh['faces'])
    assert np.array_equal(face_ids, mesh['face_instance_ids'])
    official_groups = read_json(verify(receipt['instances']))['segGroups']
    assert len(official_groups) == len(groups) == 176
    for group, adapted in zip(groups, official_groups):
        assert group['label'] == adapted['label']
        for field in ('normalizedAxes', 'centroid'):
            assert group['obb'][field] == adapted['obb'][field]
        assert np.allclose(np.asarray(group['obb']['axesLengths']) / 2, adapted['obb']['axesLengths'])
    assert max(max(d['max_axis_ratio_to_source_axesLengths']) for d in diagnostics if d['max_axis_ratio_to_source_axesLengths']) <= .525
    poses, intrinsics, hw, rows, _ = selected_camera_alignment(raw, frames)
    calibration = load_arrays(receipt['calibration'])
    assert np.array_equal(poses, calibration['camera_poses']) and np.array_equal(intrinsics, calibration['intrinsics'])
    assert list(hw) == calibration['raster_hw'].tolist()
    original_alignment = read_json(verify(receipt['alignment']))
    assert rows == original_alignment['frames']
    provider = TrainingGrounding(receipt)
    render_proofs = []
    for proof in receipt['rendering_proof']:
        verify(proof['side_by_side'])
        arrays = load_arrays(proof['arrays'])
        slot = proof['slot_1based'] - 1
        depth, mask = Renderer._render(vertices, poses[slot].astype(np.float64), intrinsics[slot].astype(np.float64), *hw)
        assert np.array_equal(depth, arrays['depth_z']) and np.array_equal(mask, arrays['valid'])
        rendered = provider._render_instance(receipt['runtime_scene_id'], slot + 1, proof['instance_id'])
        assert rendered is not None and np.array_equal(rendered['mask'], arrays['mask'])
        render_proofs.append({'slot': slot + 1, 'instance_id': proof['instance_id'], 'visible_pixels': int(rendered['mask'].sum()), 'side_by_side': proof['side_by_side']})
    result = {'scene_receipt': pin(SCENE / 'scene_receipt.json'), 'validated_slots': 32,
              'official_instances': len(groups), 'segment_association': basis,
              'all_raw_sources_rehashed': provenance['raw_sources'], 'all_camera_associations': rows,
              'min_raw_vsi_correlation': min(row['raw_to_vsi_correlation'] for row in rows),
              'source_OBB_lengths': 'full_extents_verified_against_mesh', 'provider_OBB_lengths': 'half_extents',
              'source_K_to_VSI': 'one_third', 'target_resize_crop': 'identity640x480',
              'estimated_geometry_used': False, 'CPU_render_proofs_reproduced': render_proofs}
    return write_json(output, result)


def launch_commands(contract):
    package = str(HERE)
    config = str(TASK / ('pilot_' + contract['sha256'][:12] + '.json'))
    exports = '\n'.join('export ' + key + '=' + value for key, value in REQUIRED_ENV.items())
    python = '/data2/jjyeung/envs/planner/bin/python -B'
    bind = (f'{python} {package}/collect.py bind --run-root {DATA_ROOT}/collection_gt_r1313 '
            f'--assets-registry {SCENE}/registry.json --contract {contract["path"]} --contract-sha256 {contract["sha256"]} '
            f'--work-id round__r1313 --agent-id req232-gt-teacher-r1313 --episode-limit 1 --output {config}')
    start = f'{python} {package}/collect.py start --config {config} --workers 1'
    return exports + '\n' + bind + '\n' + start + '\n', config


def validate(args):
    output = data_path(args.output)
    output.mkdir(parents=True, exist_ok=False)
    from audit_package import seal, verify_contract, derivation_checks
    contract = seal(output / 'SOURCE_CONTRACT.json')
    commands = []

    def run(label, arguments):
        log = output / (label + '.log')
        command = [sys.executable, '-B', *arguments]
        started = time.time_ns()
        with log.open('x') as handle:
            process = subprocess.run(command, cwd=HERE, env=dict(os.environ, **REQUIRED_ENV), stdout=handle, stderr=subprocess.STDOUT, timeout=600)
        row = {'label': label, 'argv': command, 'return_code': process.returncode,
               'started_time_ns': started, 'ended_time_ns': time.time_ns(), 'log': pin(log)}
        commands.append(row)
        with (output / 'VALIDATION_LEDGER.jsonl').open('a') as handle:
            handle.write(json.dumps(row, sort_keys=True) + '\n'); handle.flush(); os.fsync(handle.fileno())
        print(json.dumps({'validation': label, 'return_code': process.returncode, 'log': str(log)}), flush=True)
        if process.returncode:
            raise RuntimeError(f'validation failed: {label}; see {log}')

    shared = ['--contract', contract['path'], '--contract-sha256', contract['sha256']]
    run('alignment', [str(HERE / 'validate_package.py'), '--alignment-only', '--output', str(output / 'ALIGNMENT.json')])
    run('unit_tests', ['-m', 'unittest', 'test_gt_tools', 'test_collector', 'test_trace_archive', '-v'])
    run('native_gt_smoke', [str(HERE / 'test_runner_transport.py'), *shared, '--mode', 'gt_tools', '--output', str(output / 'native_gt_smoke')])
    commands_text, config_path = launch_commands(contract)
    script = output / 'PILOT_COMMANDS.sh'
    with script.open('x') as handle:
        handle.write(commands_text)
    status_path = TASK / 'BUILD_STATUS.json'
    status = read_json(status_path)
    status.update(milestone='offline_native_smoke_ready', smoke_ready=True, implementation_review='parent_pending',
                  source_contract=contract, smoke_proof=pin(output / 'native_gt_smoke/PROOF.json'),
                  pilot_commands=pin(script), pilot_config_to_bind=config_path,
                  all_scene_preparation='out_of_scope', paid_inference_calls=0, student_training_runs=0,
                  next='Parent may review the bounded pilot and bind/start its1-question config. Remaining offline negative fixtures run separately; no paid launch by this worker.')
    from pool_harness.atomicfs import replace_json
    replace_json(status_path, status)
    print(json.dumps({'smoke_ready': True, 'pilot_commands': str(script), 'implementation_review': 'parent_pending'}), flush=True)
    if not args.smoke_only:
        run('admission', [str(HERE / 'test_admission.py'), *shared, '--output', str(output / 'admission')])
        for mode in ('zero_answer', 'empty_cap', 'malformed_cap', 'network_error'):
            run('native_' + mode, [str(HERE / 'test_runner_transport.py'), *shared, '--mode', mode, '--output', str(output / ('native_' + mode))])
    final_contract = verify_contract(contract['path'], contract['sha256'])
    donor_proof = derivation_checks()
    from census import LABELS, LABELS_SHA
    if sha(LABELS) != LABELS_SHA:
        raise ValueError('offline grading label authority drift')
    proof_paths = [output / 'ALIGNMENT.json', output / 'native_gt_smoke/PROOF.json']
    if not args.smoke_only:
        proof_paths += [output / 'admission/PROOF.json'] + [output / ('native_' + mode) / 'PROOF.json' for mode in ('zero_answer', 'empty_cap', 'malformed_cap', 'network_error')]
    census = {'schema': 'r1313-offline-validation-closure-v1', 'source_contract': contract,
              'source_root': str(HERE), 'source_files': final_contract['source_files'],
              'runtime_source_files': final_contract['runtime_files'], 'offline_source_files': final_contract['offline_files'],
              'scene_registry': pin(SCENE / 'registry.json'), 'scene_receipt': pin(SCENE / 'scene_receipt.json'),
              'runtime_membership': final_contract['membership'],
              'offline_only_label_authority': {'path': str(LABELS), 'sha256': LABELS_SHA},
              'validation_ledger': pin(output / 'VALIDATION_LEDGER.jsonl'), 'commands': commands,
              'proofs': [pin(path) for path in proof_paths], 'donors_reverified_at_close': donor_proof,
              'pilot_commands': pin(script), 'run_root': str(DATA_ROOT / 'collection_gt_r1313'),
              'smoke_ready': True, 'complete_offline_suite': not args.smoke_only,
              'implementation_review': 'parent_pending', 'paid_calls': 0, 'student_training_runs': 0,
              'accepted_training_traces_claimed': 0, 'fixture_acceptance_is_not_source_question_correctness': True}
    closure = write_json(output / 'CLOSURE_CENSUS.json', census)
    status = read_json(status_path)
    status.update(milestone='offline_validation_complete' if not args.smoke_only else 'offline_native_smoke_ready',
                  validation_closure=closure, complete_offline_suite=not args.smoke_only)
    replace_json(status_path, status)
    print(json.dumps({'closure': closure, 'smoke_ready': True, 'complete_offline_suite': not args.smoke_only}, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--alignment-only', action='store_true')
    parser.add_argument('--smoke-only', action='store_true')
    args = parser.parse_args()
    if any(os.environ.get(key) != value for key, value in REQUIRED_ENV.items()):
        raise ValueError('every Python validation requires the declared cache/no-bytecode/native environment')
    if args.alignment_only:
        print(json.dumps(alignment_validation(args.output)))
    else:
        validate(args)


if __name__ == '__main__':
    main()
