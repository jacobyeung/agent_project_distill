from student_pilot.r2_policy import unsupported_entry
unsupported_entry('step0_runtime_v1/run_cell.py:import')
import argparse
from contextlib import ExitStack
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

from diag_common import ARMS, BULK, CELL, COUNT, LANE, NATIVE, OUT, ROUTE_ROOT, WORK, contract, emit, load_rows, now, object_digest, pin, read_json, verify, write_new
from diag_admission import identity, lock
from diag_worker import validate_terminal


def environment():
    result = dict(os.environ)
    result.update(PYTHONNOUSERSITE='1', PYTHONDONTWRITEBYTECODE='1', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', HF_HUB_DISABLE_TELEMETRY='1', TOKENIZERS_PARALLELISM='false', WANDB_DISABLED='true', OMP_NUM_THREADS='4', MKL_NUM_THREADS='4', CUDA_DEVICE_ORDER='PCI_BUS_ID', CUDA_VISIBLE_DEVICES='')
    for key in ('STUDENT_EVAL_ROOTS', 'STUDENT_ORCHARD', 'STUDENT_TRINITY_EVAL', 'STUDENT_FRAME_ROOT_MAP', 'ORCHARD_MEDIA_ATTESTATION', 'ORCHARD_MEDIA_ATTESTATION_SHA256'):
        result.pop(key, None)
    for key, suffix in (('TMPDIR', 'tmp'), ('XDG_CACHE_HOME', 'xdg'), ('HF_HOME', 'huggingface'), ('HF_HUB_CACHE', 'huggingface/hub'), ('HUGGINGFACE_HUB_CACHE', 'huggingface/hub'), ('TORCH_HOME', 'torch'), ('PIP_CACHE_DIR', 'pip'), ('CUDA_CACHE_PATH', 'cuda'), ('TRITON_CACHE_DIR', 'triton'), ('TORCHINDUCTOR_CACHE_DIR', 'torchinductor'), ('MPLCONFIGDIR', 'matplotlib')):
        directory = OUT / 'runtime' / suffix
        directory.mkdir(parents=True, exist_ok=True)
        result[key] = str(directory)
    return result


def progress(job, frozen):
    ready = read_json(verify(job['route_preflight']))
    values = load_rows(verify(ready['inputs']))
    started = done = errors = 0
    for row in values:
        directory = ROUTE_ROOT / ARMS[0] / 'items' / row['qid']
        start = directory / 'started.json'
        if start.exists():
            record = read_json(start)
            if any(record.get(key) != wanted for key, wanted in {'qid': row['qid'], 'arm': ARMS[0], 'job_sha256': frozen['sha256'], 'input_sha256': object_digest(row['student_input']), 'attempts': 1}.items()):
                raise ValueError('A durable start does not match this frozen cell')
            admission = read_json(verify(record['admission']))
            if admission['job_sha256'] != frozen['sha256'] or admission['process'] != record['worker_process']:
                raise ValueError('A durable start lacks matching admission evidence')
            started += 1
        terminal = directory / 'terminal.json'
        if terminal.exists():
            value = validate_terminal(read_json(terminal), row['qid'], ARMS[0], frozen['sha256'], object_digest(row['student_input']))
            done += 1
            errors += value['status'] != 'OK'
    if not done <= started <= COUNT:
        raise ValueError('Terminal and start census disagree')
    return {'verified_terminals': done, 'expected': COUNT, 'started': started, 'errors': errors, 'missing': COUNT - done, 'active_or_interrupted': started - done}


def run(attempt):
    job, frozen = contract()
    control = OUT / 'control'
    with ExitStack() as stack:
        lock(stack, control / 'supervisor.lock')
        name = 'attempt_' + str(attempt)
        env = environment()
        command = ['bash', '/data3/shared/scripts/vnice/vnice.sh', sys.executable, '-B', '-u', str(WORK / 'diag_worker.py'), '--arm', ARMS[0], '--worker-index', '0', '--attempt', str(attempt)]
        launch = write_new(control / (name + '.launch.json'), {'cell': CELL, 'process': identity(os.getpid()), 'frozen_job': frozen, 'command': command, 'checked_at_utc': now()})
        child = subprocess.Popen(command, cwd=WORK, env=env, stdin=subprocess.DEVNULL, start_new_session=True)
        owned = identity(child.pid)
        write_new(control / (name + '.child.json'), {'process': owned, 'launch': launch, 'frozen_job': frozen})
        before = progress(job, frozen)['verified_terminals']
        last_advance = time.monotonic()
        empty = 0
        try:
            while True:
                try:
                    result = child.wait(timeout=60)
                    break
                except subprocess.TimeoutExpired:
                    if identity(child.pid) != owned:
                        raise ValueError('The evaluation child identity changed')
                    observed = progress(job, frozen)
                    if observed['verified_terminals'] > before:
                        last_advance, empty = time.monotonic(), 0
                    else:
                        empty += 1
                    before = observed['verified_terminals']
                    emit('supervisor_check', child=owned, empty_checks=empty, seconds_since_advance=time.monotonic() - last_advance, **observed)
                    with (control / 'heartbeat.jsonl').open('a') as stream:
                        stream.write(__import__('json').dumps({'at': now(), 'cell': CELL, 'process': owned, **observed}) + '\n')
                    with (LANE / 'out/HEARTBEAT.log').open('a') as stream:
                        stream.write(now() + ' | ' + CELL + ' supervisor: ' + str(observed['verified_terminals']) + '/' + str(COUNT) + ' authenticated terminals.\n')
                    if time.monotonic() - last_advance >= 600:
                        raise RuntimeError('Ten minutes without a terminal; stop only this owned child gracefully')
        finally:
            if child.poll() is None:
                if identity(child.pid) != owned or owned['uid'] != os.getuid():
                    raise ValueError('Child ownership changed; no signal sent')
                os.killpg(child.pid, signal.SIGTERM)
                try:
                    child.wait(timeout=120)
                except subprocess.TimeoutExpired as error:
                    raise RuntimeError('Graceful stop failed; no force-kill attempted') from error
            write_new(control / (name + '.exit.json'), {'returncode': child.returncode, 'child': owned, 'launch': launch, 'finished_at_utc': now()})
        observed = progress(job, frozen)
        if result != 0 or observed['verified_terminals'] != COUNT:
            raise RuntimeError('The cell exited without complete authenticated terminal coverage')
        emit('cell_terminal_coverage_complete', **observed)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('run', 'status'))
    parser.add_argument('--attempt', type=int, default=1)
    args = parser.parse_args()
    if args.attempt < 1:
        raise ValueError('Attempt must be positive')
    if args.action == 'status':
        job, frozen = contract()
        emit('verified_status', **progress(job, frozen))
    else:
        signal.signal(signal.SIGTERM, lambda number, frame: (_ for _ in ()).throw(SystemExit(128 + number)))
        run(args.attempt)


if __name__ == '__main__':
    main()
