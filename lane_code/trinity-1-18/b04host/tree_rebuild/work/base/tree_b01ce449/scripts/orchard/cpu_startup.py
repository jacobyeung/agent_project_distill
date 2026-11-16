import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

from student_pilot.common import startup_event

REPO = Path(__file__).resolve().parents[2]
LABEL = 'ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW'


def cpu_environment():
    if (any(os.environ.get(name, '') not in ('', 'N/A', '(null)')
            for name in ('SLURM_JOB_GPUS', 'SLURM_STEP_GPUS'))
            or os.environ.get('SLURM_GPUS_ON_NODE', '') not in ('', '0', 'N/A', '(null)')):
        raise ValueError('Prepare startup in a CPU allocation, before reserving GPUs')
    return {**os.environ, 'CUDA_VISIBLE_DEVICES': '', 'PYTHONDONTWRITEBYTECODE': '1'}


def require_clean_checkout():
    expected = os.environ['TRAINER_COMMIT']
    head = subprocess.check_output(['git', '-C', str(REPO), 'rev-parse', 'HEAD'], text=True).strip()
    dirty = subprocess.check_output(['git', '-C', str(REPO), 'status', '--porcelain', '--untracked-files=normal'], text=True).strip()
    if not re.fullmatch(r'[0-9a-f]{40}', expected) or head != expected or dirty:
        raise ValueError('CPU preparation requires the clean GPU deployment commit')


def run(command, env):
    startup_event(command[5] + '_begin')
    subprocess.run(command, env=env, cwd=REPO, check=True)
    startup_event(command[5] + '_end')


def prepare(frozen, student, world_size, label=LABEL, scratch_root=None, shared_frames=False):
    env = cpu_environment()
    if shared_frames:
        from student_pilot.startup_receipt import require_cpu
        require_cpu()
    if type(world_size) is not int or world_size not in (*range(2, 9), 16, 24, 32, 40, 48, 56, 64):
        raise ValueError('Use a supported training world size')
    if student not in ('onethinker', 'qwen35', 'qwen36_27b'):
        raise ValueError('Use a registered student')
    frozen = Path(frozen).resolve()
    inputs = [frozen / name for name in ('config.json', 'launch_identity.json', 'protocol.json', 'training.json')]
    receipt = frozen / 'training.json.source_receipt.json'
    request, marker = frozen / 'request.json', frozen / 'cpu_startup.json'
    if not all(path.is_file() for path in inputs) or any(path.exists() for path in (request, marker)):
        raise ValueError('Require frozen CPU inputs and new request/readiness paths')
    require_clean_checkout()
    cli = [sys.executable, '-B', '-m', 'student_pilot.cli', 'diagnostic']
    shared = ['--provisional-diagnostic', label]
    if scratch_root is not None:
        shared += ['--scratch-root', str(scratch_root)]
    if not receipt.exists():
        run([*cli, 'seal-source', '--manifest', str(inputs[3]), '--output', str(receipt), *shared], env)
    run([*cli, 'lease-request-ddp', '--manifest', str(inputs[3]), '--protocol', str(inputs[2]),
         '--student', student, '--world-size', str(world_size), '--output', str(request), *shared], env)
    startup = None
    if shared_frames:
        from student_pilot.startup_receipt import prepare as prepare_startup
        startup_event('shared_startup_prepare_begin')
        startup = prepare_startup(frozen, student, world_size, label)
        startup_event('shared_startup_prepare_end')
    pins = []
    extra = [frozen / 'startup_receipt.json', frozen / 'shared_frames.json'] if startup is not None else []
    for path in [*inputs, receipt, request, *extra]:
        digest = hashlib.sha256()
        with path.open('rb') as stream:
            for block in iter(lambda: stream.read(8 * 1024 * 1024), b''):
                digest.update(block)
        pins.append({'path': str(path), 'sha256': digest.hexdigest(), 'size_bytes': path.stat().st_size})
    result = {'status': 'CPU_STARTUP_PREPARED', 'gpu_admission': False, 'trainer_commit': os.environ['TRAINER_COMMIT'],
              'student': student, 'world_size': world_size, 'provisional_diagnostic': label, 'inputs': pins}
    if startup is not None:
        result.update(startup_receipt=startup, gpu_environment={'STUDENT_STARTUP_RECEIPT': startup['path'],
                      'STUDENT_STARTUP_RECEIPT_SHA256': startup['sha256']})
    with marker.open('x') as stream:
        json.dump(result, stream, sort_keys=True, indent=2)
        stream.write('\n')
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--frozen', required=True, type=Path)
    parser.add_argument('--student', required=True, choices=('onethinker', 'qwen35', 'qwen36_27b'))
    parser.add_argument('--world-size', required=True, type=int)
    parser.add_argument('--provisional-diagnostic', default=LABEL)
    parser.add_argument('--scratch-root', type=Path)
    parser.add_argument('--shared-frames', action='store_true')
    args = parser.parse_args()
    print(json.dumps(prepare(args.frozen, args.student, args.world_size, args.provisional_diagnostic,
                             args.scratch_root, args.shared_frames), sort_keys=True))


if __name__ == '__main__':
    main()
