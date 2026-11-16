"""Run the first three pinned ScanNet scenes once and record every terminal outcome."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from gt_scene_assets import data_path, pin, read_json, verify, write_json, validate_scene
from scannet_contract import verify_contract

HERE = Path(__file__).resolve().parent


def run_child(command, log, env, timeout=3600):
    with log.open('x') as f:
        try:
            run = subprocess.run(command, env=env, cwd=HERE, stdout=f, stderr=subprocess.STDOUT, timeout=timeout)
            return run.returncode, None
        except subprocess.TimeoutExpired:
            return 124, f'preparer exceeded {timeout} seconds; subprocess terminated and reaped'
        except OSError as error:
            return 125, str(error)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--contract', type=Path, required=True)
    parser.add_argument('--contract-sha256', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    contract = verify_contract(args.contract, args.contract_sha256)
    output = data_path(args.output); output.mkdir(parents=True, exist_ok=True)
    rows = [r for r in read_json(contract['plan']['path'])['scenes'] if r['dataset'] == 'scannet'][:3]
    if len(rows) != 3:
        raise ValueError('pinned plan lacks three ScanNet scenes')
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', CUDA_VISIBLE_DEVICES='',
        HF_HOME='/data2/jjyeung/cache/huggingface', HUGGINGFACE_HUB_CACHE='/data2/jjyeung/cache/huggingface/hub',
        TORCH_HOME='/data2/jjyeung/cache/torch', PIP_CACHE_DIR='/data2/jjyeung/cache/pip',
        OMP_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2', MKL_NUM_THREADS='2', OPENCV_FOR_THREADS_NUM='2')
    results = []
    for row in rows:
        target = output / row['scene']
        command = [sys.executable, '-B', str(HERE / 'prepare_gt_scene.py'), 'prepare',
            '--scene', row['scene'], '--frames-receipt', row['frames_receipt']['path'],
            '--frames-receipt-sha256', row['frames_receipt']['sha256'],
            '--contract', str(args.contract), '--contract-sha256', args.contract_sha256, '--output', str(target)]
        started = time.time_ns(); log = output / (row['scene'] + '.log')
        return_code, driver_error = run_child(command, log, env)
        result = {'scene': row['scene'], 'return_code': return_code, 'argv': command,
            'started_time_ns': started, 'ended_time_ns': time.time_ns(), 'log': pin(log),
            'frames_receipt': row['frames_receipt']}
        receipt_path = target / ('REFUSAL_RECEIPT.json' if return_code else 'VALIDATION_RECEIPT.json')
        if driver_error or not receipt_path.is_file():
            receipt_path = output / (row['scene'] + '_DRIVER_REFUSAL.json')
            write_json(receipt_path, {'schema': 'r1313-scannet-driver-refusal-v1',
                'stage': 'preparer_process', 'status': 'refused', 'collector_admission': False,
                'error': driver_error or 'preparer terminated without a terminal receipt',
                'return_code': return_code, 'log': result['log'], 'scene': row['scene']})
            if not return_code:
                return_code = 126
                result['return_code'] = return_code
        result['receipt'] = pin(receipt_path)
        if return_code == 0:
            receipt = validate_scene(read_json(target / 'scene_receipt.json'), load_dense=True)
            alignment = read_json(verify(receipt['alignment']))
            result.update(status='validated_not_admitted', validated_slots=32,
                min_correlation=min(r['raw_to_vsi_correlation'] for r in alignment['frames']),
                max_reprojection_px=max(r['max_reprojection_px'] for r in alignment['render_audits']))
        else:
            refusal = read_json(receipt_path)
            result.update(status='refused', stage=refusal['stage'], error=refusal['error'])
        results.append(result)
        with (output / 'COMMAND_LEDGER.jsonl').open('a') as f:
            f.write(json.dumps(result, sort_keys=True) + '\n'); f.flush(); os.fsync(f.fileno())
        print(json.dumps(result), flush=True)
    verify_contract(args.contract, args.contract_sha256)
    report = write_json(output / 'RESULTS.json', {'schema': 'r1313-scannet-validation-summary-v1',
        'contract': pin(args.contract), 'selection': 'first_three_scannet_entries_in_pinned_PLAN_no_replacement',
        'scenes': results, 'collector_admissions': 0, 'paid_api_calls': 0, 'gpu_runs': 0})
    print(json.dumps(report), flush=True)


if __name__ == '__main__':
    main()
